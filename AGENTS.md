# AGENTS.md

## Cursor Cloud specific instructions

This repo is an ETF data-engineering pipeline: **Python ETL (yfinance) → DuckDB (single file) → dbt** (marts consumed downstream). Reporting is mid-migration per the v3 roadmap (`analytics/docs/stock-market-v2-reporting-layer.md`): the reporting layer will be a Streamlit dashboard reading the DuckDB file. Airflow, Metabase, Grafana, the Chart.js `website/`, and legacy ETL scripts have been retired to `archive/` and are NOT part of the running system.

### Environment layout
- Python deps live in a virtualenv at `.venv` (created by the startup update script). Run tools with `.venv/bin/python`, `.venv/bin/dbt`, etc., or `source .venv/bin/activate`.
- `black` is pinned to `24.10.0` on purpose: the latest `black` requires `pathspec>=1.0`, which conflicts with `dbt-core` (`pathspec<0.13`). Do not bump it without resolving that conflict.
- No database server is required (Phase 1 migrated off PostgreSQL). The warehouse is a single DuckDB file at `warehouse.duckdb` in the repo root, created by the pipeline. `.env` is optional; only set `DUCKDB_PATH` (absolute path) if you want a non-default location — the ETL and dbt must point at the same file.

### DuckDB path gotcha
- The ETL runs from the repo root, so it defaults to `./warehouse.duckdb`. dbt runs from `dbt/`, so its profile defaults to `../warehouse.duckdb` — both resolve to the same repo-root file. If you override `DUCKDB_PATH`, use an absolute path or the two will diverge.
- DuckDB allows only one read-write connection to the file at a time. Don't run the ETL and dbt concurrently against the same file (the workflow runs them sequentially).

### Running the pipeline (end-to-end)
1. Full ETL (creates schema, loads symbols, fetches from Yahoo Finance — needs internet): `PYTHONPATH=. .venv/bin/python analytics/enhanced_workflow.py --step full`. Use `--step incremental` afterwards for daily top-ups. `--step full|incremental|fetch` are the only options; note `load_symbols.py` alone does NOT create the schema, so a fresh DB must be initialized via `--step full` (or `analytics/database/init_db.py`) first.
2. Build dbt models (run from `dbt/`, always pass `--profiles-dir .`): `dbt deps`, then `dbt run --profiles-dir .`, `dbt test --profiles-dir .`. All 6 models build and the 41 data tests pass, including `mart_52week_metrics` and `mart_entry_thresholds` (now populated).

### Tests / lint
- CI health check (see `.github/workflows/test_automation.yml`): `PYTHONPATH=. .venv/bin/python analytics/test_enhanced_workflow.py`. No DB server needed — it creates/uses the DuckDB file.
- Lint tools are installed (`black`, `isort`, `flake8`) but the existing codebase is NOT formatted to their defaults, so they report many pre-existing style findings — that is expected, not a regression.

### Notes / caveats
- `dbt source freshness --profiles-dir .` only computes for the `etf_data` source (it has a `loaded_at_field`); the other sources have none and error by design on the DuckDB adapter.
- The GitHub Actions workflows (`production_automation.yml`, `test_automation.yml`) still assume PostgreSQL and are pending the Phase 2 rewrite; they are inconsistent with the DuckDB pipeline until then.
- (Historical, archived) `archive/analytics/etl/data_exporter.py` used SQLite-only syntax — do not resurrect it as-is; the DuckDB/Streamlit path replaces it.
