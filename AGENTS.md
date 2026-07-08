# AGENTS.md

## Cursor Cloud specific instructions

This repo is an ETF data-engineering pipeline: **Python ETL (yfinance) → DuckDB (single file) → dbt → Streamlit dashboard**. The design/roadmap is `analytics/docs/stock-market-v2-reporting-layer.md`. Airflow, Metabase, Grafana, the Chart.js `website/`, legacy ETL scripts, and superseded setup docs have been retired to `archive/` and are NOT part of the running system.

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

### Streamlit dashboard (`dashboard/`)
- Run locally from `dashboard/`: `/workspace/.venv/bin/streamlit run app.py` (install its deps with `pip install -r dashboard/requirements.txt` if needed). It reads marts from the DuckDB warehouse.
- Data resolution order: `$DUCKDB_PATH` → a local `warehouse.duckdb` in the repo (dev) → the published `latest-data` GitHub Release asset (`$WAREHOUSE_URL`). So locally it "just works" if `warehouse.duckdb` exists; in production (Streamlit Community Cloud) it downloads the Release asset.
- `dashboard/` has its own `requirements.txt` for Streamlit Cloud; it is separate from the pipeline's root `requirements.txt`.

### Tests / lint
- CI health check (see `.github/workflows/test_automation.yml`): `PYTHONPATH=. .venv/bin/python analytics/test_enhanced_workflow.py`. No DB server needed — it creates/uses the DuckDB file.
- Lint tools are installed (`black`, `isort`, `flake8`) but the existing codebase is NOT formatted to their defaults, so they report many pre-existing style findings — that is expected, not a regression.

### Notes / caveats
- `dbt source freshness --profiles-dir .` only computes for the `etf_data` source (it has a `loaded_at_field`); the other sources have none and error by design on the DuckDB adapter.
- `production_automation.yml` runs the full pipeline daily and publishes `warehouse.duckdb` as the `latest-data` GitHub Release asset (built-in `GITHUB_TOKEN`, `contents: write`); the Streamlit app downloads that asset. It only runs on schedule or manual `workflow_dispatch`.
- (Historical, archived) `archive/analytics/etl/data_exporter.py` used SQLite-only syntax — do not resurrect it as-is; the DuckDB/Streamlit path replaces it.
