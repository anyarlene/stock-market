"""ETF Market Data Pipeline
============================

A production-style ELT pipeline for ETF analytics.

Pipeline stages
---------------
1. **Extract & Load**  — fetch OHLCV prices and FX rates from Yahoo Finance
                          and upsert them into PostgreSQL.
2. **Transform**       — run dbt models in layer order:
                          staging → intermediate → marts.
3. **Quality**         — run dbt tests and check source freshness in parallel.
4. **Visualize**       — trigger Metabase to resync schema so new mart tables
                          are immediately visible in dashboards (optional; skipped
                          when METABASE_URL Airflow Variable is not set).

Schedule : Mon–Fri at 21:15 UTC
Data source : Yahoo Finance (yfinance)
Warehouse   : PostgreSQL (Supabase in production, local Docker in dev)
Transform   : dbt Core
Dashboards  : Metabase OSS
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

# ---------------------------------------------------------------------------
# Paths — the whole repo is mounted at /opt/airflow/project
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path("/opt/airflow/project")
DBT_DIR = PROJECT_ROOT / "dbt"

# ---------------------------------------------------------------------------
# Default task arguments
# ---------------------------------------------------------------------------
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ---------------------------------------------------------------------------
# Helpers used by PythonOperators
# ---------------------------------------------------------------------------

def _init_database() -> None:
    """Ensure all PostgreSQL tables exist (idempotent)."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from analytics.database.db_manager import DatabaseManager

    db = DatabaseManager()
    db.initialize_database()


def _load_symbols() -> None:
    """Reload ETF symbols from the CSV reference file."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from analytics.database.load_symbols import load_symbols

    csv_path = str(PROJECT_ROOT / "analytics" / "database" / "reference" / "symbols.csv")
    load_symbols(csv_path)


def _fetch_market_data() -> dict:
    """Incrementally fetch OHLCV data from Yahoo Finance and upsert into PostgreSQL.

    Returns the run summary dict for downstream logging via XCom.
    Raises RuntimeError when the overall fetch fails so Airflow marks the
    task as failed and triggers the retry policy.
    """
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from analytics.etl.enhanced_market_data_fetcher import EnhancedMarketDataFetcher

    fetcher = EnhancedMarketDataFetcher()
    results = fetcher.run_incremental_update()

    if not results.get("overall_success"):
        raise RuntimeError(f"Market data fetch reported failure: {results}")

    return results


def _should_sync_metabase() -> bool:
    """Return True when the METABASE_URL Airflow Variable is configured.

    Used as a ShortCircuitOperator gate so the visualize task group is
    silently skipped in environments where Metabase is not set up yet.
    """
    try:
        url = Variable.get("METABASE_URL", default_var="")
        return bool(url.strip())
    except Exception:
        return False


def _sync_metabase() -> None:
    """Trigger Metabase to resync its ETF database connection.

    Requires two Airflow Variables to be set:
      - METABASE_URL   : base URL of your Metabase instance
                         e.g. http://<oracle-ip>:3000
      - METABASE_API_KEY : admin API key created in Metabase Admin → API Keys

    On success Metabase picks up any new/renamed dbt mart tables within
    about a minute, keeping dashboards always current.
    """
    import requests

    metabase_url = Variable.get("METABASE_URL").rstrip("/")
    api_key = Variable.get("METABASE_API_KEY")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    # Discover the ETF analytics database inside Metabase
    resp = requests.get(f"{metabase_url}/api/database", headers=headers, timeout=30)
    resp.raise_for_status()
    databases = resp.json().get("data", [])

    etf_db = next(
        (d for d in databases if "etf" in d.get("name", "").lower()),
        None,
    )
    if etf_db is None:
        raise RuntimeError(
            "No ETF database found in Metabase. "
            "Connect it first via Admin → Databases → Add a database."
        )

    db_id = etf_db["id"]

    # Trigger schema resync (picks up new tables / columns from dbt marts)
    requests.post(f"{metabase_url}/api/database/{db_id}/sync_schema", headers=headers, timeout=30)
    # Rescan field values (keeps filter dropdowns fresh)
    requests.post(f"{metabase_url}/api/database/{db_id}/rescan_values", headers=headers, timeout=30)

    print(f"✅  Triggered Metabase sync for database id={db_id} ({etf_db['name']})")


# ---------------------------------------------------------------------------
# Build env dict for BashOperators that run dbt
# ---------------------------------------------------------------------------
def _dbt_env() -> dict[str, str]:
    """Assemble env vars for dbt, sourced from the Airflow process environment."""
    keys = ["DATABASE_URL", "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_SSLMODE"]
    env = {k: os.environ.get(k, "") for k in keys}
    # Keep the system PATH so dbt binary is found
    env["PATH"] = os.environ.get("PATH", "/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin")
    return env


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="etf_market_data_pipeline",
    description="ELT: Yahoo Finance → PostgreSQL → dbt → Metabase",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="15 21 * * 1-5",
    catchup=False,
    max_active_runs=1,
    tags=["etf", "yfinance", "dbt", "postgresql", "metabase"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start")

    # ── 1. Extract & Load ───────────────────────────────────────────────────
    with TaskGroup("extract_load", tooltip="Ingest ETF data from Yahoo Finance into PostgreSQL") as tg_el:

        init_db = PythonOperator(
            task_id="init_database",
            python_callable=_init_database,
            doc_md="Create PostgreSQL tables from schema.sql (idempotent).",
        )

        load_sym = PythonOperator(
            task_id="load_symbols",
            python_callable=_load_symbols,
            doc_md="Reload ETF symbols from analytics/database/reference/symbols.csv.",
        )

        fetch = PythonOperator(
            task_id="fetch_market_data",
            python_callable=_fetch_market_data,
            doc_md=(
                "Incrementally fetch OHLCV + FX rates from Yahoo Finance. "
                "Only pulls dates newer than the latest record in PostgreSQL."
            ),
        )

        init_db >> load_sym >> fetch

    # ── 2. Transform ────────────────────────────────────────────────────────
    with TaskGroup("transform", tooltip="dbt: staging → intermediate → marts") as tg_transform:

        dbt_deps = BashOperator(
            task_id="dbt_deps",
            bash_command=f"cd {DBT_DIR} && dbt deps --profiles-dir .",
            env=_dbt_env(),
            doc_md="Install dbt packages declared in packages.yml.",
        )

        dbt_staging = BashOperator(
            task_id="dbt_run_staging",
            bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir . --select staging",
            env=_dbt_env(),
            doc_md="Materialize staging views: clean + join raw tables.",
        )

        dbt_intermediate = BashOperator(
            task_id="dbt_run_intermediate",
            bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir . --select intermediate",
            env=_dbt_env(),
            doc_md="Materialize intermediate views: EUR conversion with fallback logic.",
        )

        dbt_marts = BashOperator(
            task_id="dbt_run_marts",
            bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir . --select marts",
            env=_dbt_env(),
            doc_md=(
                "Materialize mart tables consumed by Metabase: "
                "mart_price_history, mart_52week_metrics, mart_entry_thresholds."
            ),
        )

        dbt_deps >> dbt_staging >> dbt_intermediate >> dbt_marts

    # ── 3. Quality ──────────────────────────────────────────────────────────
    with TaskGroup("quality", tooltip="dbt tests + source freshness (run in parallel)") as tg_quality:

        dbt_test = BashOperator(
            task_id="dbt_test",
            bash_command=f"cd {DBT_DIR} && dbt test --profiles-dir .",
            env=_dbt_env(),
            doc_md="Run all dbt schema tests (not_null, unique, custom).",
        )

        dbt_freshness = BashOperator(
            task_id="dbt_source_freshness",
            bash_command=f"cd {DBT_DIR} && dbt source freshness --profiles-dir .",
            env=_dbt_env(),
            doc_md="Assert that raw source tables received data within the SLA window.",
        )
        # dbt_test and dbt_freshness run in parallel (no dependency between them)

    # ── 4. Visualize (optional) ─────────────────────────────────────────────
    with TaskGroup("visualize", tooltip="Refresh Metabase (skipped when METABASE_URL is not set)") as tg_viz:

        check_metabase = ShortCircuitOperator(
            task_id="check_metabase_configured",
            python_callable=_should_sync_metabase,
            doc_md="Skip the sync task when METABASE_URL Airflow Variable is not configured.",
        )

        sync_mb = PythonOperator(
            task_id="sync_metabase",
            python_callable=_sync_metabase,
            doc_md=(
                "Trigger Metabase schema resync so new dbt mart tables appear "
                "in dashboards immediately. Requires METABASE_URL and "
                "METABASE_API_KEY Airflow Variables."
            ),
        )

        check_metabase >> sync_mb

    # ── End (runs regardless of quality outcome to always mark pipeline done)
    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # ── Wire task groups ────────────────────────────────────────────────────
    start >> tg_el >> tg_transform >> tg_quality >> tg_viz >> end
