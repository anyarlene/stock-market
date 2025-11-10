from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = Path("/opt/airflow/project")
ANALYTICS_DIR = PROJECT_ROOT / "analytics"
PYTHONPATH = str(PROJECT_ROOT)

default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="market_data_incremental_update",
    description="Fetches and processes daily market data from Yahoo Finance.",
    default_args=default_args,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule="15 21 * * 1-5",
    catchup=False,
    tags=["market-data", "yfinance", "sqlite"],
) as dag:

    env = {
        "PYTHONPATH": PYTHONPATH,
    }

    initialize_database = BashOperator(
        task_id="initialize_database",
        bash_command=(
            f"cd {ANALYTICS_DIR} && "
            "python database/init_db.py && "
            "python database/load_symbols.py"
        ),
        env=env,
    )

    run_incremental_update = BashOperator(
        task_id="run_incremental_update",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python analytics/enhanced_workflow.py --step incremental"
        ),
        env=env,
    )

    show_results = BashOperator(
        task_id="show_results",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python analytics/database_diagnostic.py"
        ),
        env=env,
    )

    initialize_database >> run_incremental_update >> show_results

