# AGENTS.md

## Cursor Cloud specific instructions

This repo is an ETF data-engineering pipeline: **Python ETL (yfinance) → PostgreSQL → dbt** (marts consumed downstream). Reporting is mid-migration: the v3 roadmap (`analytics/docs/stock-market-v2-reporting-layer.md`) is moving to a DuckDB file + Streamlit dashboard. Airflow, Metabase, Grafana, the Chart.js `website/`, and legacy ETL scripts have been retired to `archive/` (Phase 0) and are NOT part of the running system.

### Environment layout
- Python deps live in a virtualenv at `.venv` (created by the startup update script). Run tools with `.venv/bin/python`, `.venv/bin/dbt`, etc., or `source .venv/bin/activate`.
- `black` is pinned to `24.10.0` on purpose: the latest `black` requires `pathspec>=1.0`, which conflicts with `dbt-core` (`pathspec<0.13`). Do not bump it without resolving that conflict.
- Copy env vars before running anything: `cp .env.example .env` then `set -a && . ./.env && set +a`. Defaults point at the local Postgres below.

### PostgreSQL (must be started manually each session)
- PostgreSQL 16 is installed system-wide but is NOT auto-started on VM boot. Start it with:
  `sudo pg_ctlcluster 16 main start`
- The `etf_user` role (password `etf_pass`) and `etf_db` database already exist in the persisted cluster; connect with `PGPASSWORD=etf_pass psql -h localhost -U etf_user -d etf_db`.
- If starting fresh, recreate them as the `postgres` superuser (role `etf_user` LOGIN PASSWORD `etf_pass`, then `createdb -O etf_user etf_db`).

### Running the pipeline (end-to-end)
1. Init schema + load reference symbols: `PYTHONPATH=. .venv/bin/python analytics/database/load_symbols.py`
2. Fetch market data (needs internet; hits Yahoo Finance): `PYTHONPATH=. .venv/bin/python analytics/enhanced_workflow.py --step fetch`
3. Build dbt models (run from `dbt/`, always pass `--profiles-dir .`): `dbt deps`, then `dbt run --profiles-dir .`, `dbt test --profiles-dir .`.

Note: `enhanced_workflow.py` now supports only `--step full|incremental|fetch` (the `currency`/`export` steps were archived with `analytics/etl/currency_converter_etl.py` and `data_exporter.py`). The old Chart.js site is at `archive/website/` for reference; the replacement Streamlit dashboard is not built yet (Phase 3).

### Tests / lint
- CI health check (see `.github/workflows/test_automation.yml`): `PYTHONPATH=. .venv/bin/python analytics/test_enhanced_workflow.py` (needs Postgres running).
- Lint tools are installed (`black`, `isort`, `flake8`) but the existing codebase is NOT formatted to their defaults, so they report many pre-existing style findings — that is expected, not a regression.

### Known pre-existing bugs (do NOT assume these are environment issues)
- `analytics/etl/enhanced_market_data_fetcher.calculate_and_store_metrics` raises `unsupported operand type(s) for *: 'decimal.Decimal' and 'float'` because Postgres returns `DECIMAL` columns as `Decimal`. Raw OHLCV price rows are still inserted before this fails, but the `fifty_two_week_metrics` / `decrease_thresholds` tables stay empty, so `mart_52week_metrics` and `mart_entry_thresholds` build with 0 rows (`mart_price_history` is unaffected).
- `dbt source freshness --profiles-dir .` only succeeds for the `etf_data` source; the others have no `loaded_at_field` and error out by design on the Postgres adapter.
- (Historical, now archived) `archive/analytics/etl/data_exporter.py` uses SQLite-only syntax against a Postgres DB — do not resurrect it as-is; the DuckDB/Streamlit path replaces it.
