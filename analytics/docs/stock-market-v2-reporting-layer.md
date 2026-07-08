# Stock-Market — Final Roadmap: Cleanup + Reporting Layer (v3, DuckDB-only)

> **Status:** Approved direction — pending implementation
> **Supersedes:** `stock-market-v1.md` (Metabase plan) AND the first version of this file
> (dual Postgres+DuckDB design). This is the single, final source of truth.
> **Goal:** A clean, single-environment, cost-free project that runs entirely in the cloud
> with zero local intervention, ending in a public dashboard matching
> `assets/etf-dashboard-mockup.png`.

---

## 0. Decision flagged for review

**Airflow is recommended for full retirement, not just a modified task.** Reasoning:

- Airflow has never run in production here — the README already states production uses
  GitHub Actions "no Airflow server needed."
- Airflow only runs if you manually start Docker Desktop and the containers — this directly
  conflicts with "the project should run in the cloud without needing my intervention."
- Keeping it means two parallel definitions of the same pipeline (the Airflow DAG and the
  GitHub Actions workflow) — the exact kind of redundant setup this cleanup is meant to remove.

If you want to keep Airflow purely as a portfolio artifact demonstrating orchestration skills,
that's reasonable — but it should live in `archive/` clearly marked "not part of the running
system," not in the active project structure. This document assumes full retirement unless
you say otherwise.

---

## 1. Constraints for this design

- Single environment — no dev/test/prod separation (solo developer)
- No redundant tools — one database technology, one orchestrator, one dashboard tool
- Zero local intervention required to keep the project running
- Fully cost-free, indefinitely
- End state: a public dashboard URL, matching the target mockup design

---

## 2. Audit of current repo state (grounded in what actually exists today)

### Already known-obsolete per the project's own README

The README's "What dbt replaces" table already documents these as superseded — they were
never removed from the repo:

| File | Superseded by |
|---|---|
| `analytics/etl/currency_converter_etl.py` | `dbt/models/intermediate/int_etf_eur.sql` |
| `analytics/etl/data_exporter.py` (metric calc) | `dbt/models/marts/mart_52week_metrics.sql` |
| `analytics/etl/data_exporter.py` (thresholds) | `dbt/models/marts/mart_entry_thresholds.sql` |

### Additional dead/duplicate code found in this audit

| File | Issue |
|---|---|
| `server_automation.py` (repo root) | v0 script: writes to SQLite, `git commit`s the DB file. Fully superseded by `production_automation.yml` (which uses Postgres/GitHub Actions, no git-committed DB) |
| `.github/workflows/test_daily_update.yml` | Same v0 SQLite-commit pattern, runs on a stale `automation-daily-update` branch. Duplicate of `production_automation.yml` |
| `analytics/etl/market_data_fetcher.py` | Superseded by `analytics/etl/enhanced_market_data_fetcher.py` (the one actually used by `enhanced_workflow.py`) |
| `analytics/workflow.py` | Superseded by `analytics/enhanced_workflow.py` (the one actually used in all current workflows) |
| `analytics/daily_automation.py` | Old automation entry point, not referenced by current GitHub Actions workflows |
| `scripts/provision_grafana.py`, `scripts/oracle-cloud-init.yml` | Tied to Grafana/Oracle VM production dashboard — retired with this doc |
| `analytics/docs/grafana_setup.md`, `metabase_setup.md`, `oracle-vm-setup.md` | Document retired infrastructure |

### Confirmed still in active use — keep, adapt to DuckDB

| File | Role |
|---|---|
| `analytics/enhanced_workflow.py` | Main ETL orchestrator, called by GitHub Actions |
| `analytics/etl/enhanced_market_data_fetcher.py` | yfinance fetch logic |
| `analytics/utils/currency_converter.py`, `validators.py` | Shared helpers used during extraction |
| `analytics/database_diagnostic.py` | Status reporting, called by `production_automation.yml` — needs its Postgres queries adapted to DuckDB |
| `analytics/test_enhanced_workflow.py` | Test suite, called by `test_automation.yml` |
| `dbt/models/` (staging, intermediate, marts) | Core transformation logic — unchanged in content, only the target changes |
| `airflow/`, `docker-compose.yml`, `docker-compose.prod.yml` | Retired per Section 0 |

*(Docs not fully audited here — `architecture.md`, `automation_setup.md`, `how_to_run_scripts.md`,
`setup.md`, `currency_conversion.md` — review each for overlap with the README during Phase 4
and consolidate or archive as needed.)*

---

## 3. Final target architecture

```
                    SINGLE ENVIRONMENT — FULLY CLOUD-RUN
┌──────────────────────────────────────────────────────────────────────┐
│  GitHub Actions — one workflow, daily schedule (Mon–Fri 21:15 UTC)     │
│  + workflow_dispatch for manual runs                                   │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  ┌────────────┐      │
│  │ Extract&Load │→ │  Transform   │→ │ Quality │→ │  Publish   │      │
│  │ yfinance →   │  │  dbt run     │  │dbt test │  │ warehouse. │      │
│  │ local .duckdb│  │ (duckdb only)│  │+freshness│ │ duckdb →   │      │
│  │ file         │  │              │  │         │  │ GH Release │      │
│  └──────────────┘  └──────────────┘  └─────────┘  └─────┬──────┘      │
└──────────────────────────────────────────────────────────────┼───────┘
                                                                │
                                                                ▼
                              GitHub Release asset (tag: latest-data)
                              warehouse.duckdb, overwritten daily
                                                                │
                                                                ▼
                              ┌───────────────────────────────┐
                              │ Streamlit app (Streamlit Cloud)│
                              │ downloads + caches the file    │
                              │ ETF Analytics Dashboard        │
                              │ Public URL, no login           │
                              └───────────────────────────────┘
```

**No local machine involvement at any point** — GitHub Actions runs the pipeline, Streamlit
Cloud auto-redeploys from `git push` and serves the dashboard.

Optional local development (not required to run the project, purely a convenience for editing):
`pip install -r requirements.txt && dbt run` — DuckDB needs no Docker, no server, just a
local file. This is simpler than the old Postgres-in-Docker workflow, not an added burden.

---

## 4. Phase 0 — Cleanup (before adding anything new)

- [ ] Delete or move to `archive/`: `server_automation.py`, `analytics/workflow.py`,
      `analytics/daily_automation.py`, `analytics/etl/market_data_fetcher.py`,
      `analytics/etl/currency_converter_etl.py`, `analytics/etl/data_exporter.py`
- [ ] Delete `.github/workflows/test_daily_update.yml`
- [ ] Move `airflow/`, `docker-compose.yml`, `docker-compose.prod.yml` to `archive/`
- [ ] Move `scripts/provision_grafana.py`, `scripts/oracle-cloud-init.yml` to `archive/`
- [ ] Move `website/` (Chart.js, investment planner) to `archive/`
- [ ] Delete `.github/workflows/deploy-website.yml`
- [ ] Add "Superseded" banners to `stock-market-v1.md`, `grafana_setup.md`, `metabase_setup.md`,
      `oracle-vm-setup.md`
- [ ] Review `architecture.md`, `automation_setup.md`, `how_to_run_scripts.md`, `setup.md` for
      overlap with README; consolidate or archive

## 5. Phase 1 — dbt on DuckDB only

- [ ] Update `dbt/profiles.yml` to a single `duckdb` target (remove postgres target entirely)
- [ ] Replace `psycopg2-binary`, `dbt-postgres` with `duckdb`, `dbt-duckdb` in `requirements.txt`
- [ ] Run all mart models against DuckDB, fix any dialect-specific SQL
- [ ] Adapt `analytics/database_diagnostic.py` to query DuckDB instead of Postgres

## 6. Phase 2 — One GitHub Actions workflow

- [ ] Replace `production_automation.yml` with a single workflow: extract → dbt run → dbt test →
      publish `warehouse.duckdb` as a GitHub Release asset (`gh release upload --clobber`)
- [ ] Remove `DATABASE_URL`/Supabase parsing and the Grafana provisioning step
- [ ] Simplify `test_automation.yml`: remove the Postgres service container (no longer needed —
      tests run against an ephemeral local DuckDB file)

## 7. Phase 3 — Streamlit dashboard

- [ ] New `dashboard/app.py` + `.streamlit/config.toml` (dark theme)
- [ ] Downloads `warehouse.duckdb` from the GitHub Release URL, cached via `st.cache_data`
- [ ] KPI cards, price history chart (Plotly `rangeselector`), threshold bars, summary table —
      per the mockup, reading `mart_price_history`, `mart_52week_metrics`, `mart_entry_thresholds`
- [ ] Deploy via Streamlit Community Cloud, connected to this repo, auto-redeploy on push

## 8. Phase 4 — Documentation

- [ ] Update root `README.md`: architecture diagram, tech stack table, dashboard link
- [ ] Consolidate `analytics/docs/` — one clear doc per remaining concern, delete/archive the rest

---

## 9. Cost and stability summary

| Component | Cost | Runs where |
|---|---|---|
| GitHub Actions | Free | Cloud |
| DuckDB build | Free | Inside the GitHub Actions run |
| GitHub Release storage | Free | Cloud |
| Streamlit Community Cloud | Free forever (non-commercial use) | Cloud |

No server, no database service, no VM, nothing requiring your machine to be on.

---

## 10. Definition of done

- [ ] `main` branch has no references to Postgres, Supabase, Grafana, Metabase-in-production,
      or Airflow-in-production
- [ ] One GitHub Actions workflow runs the entire pipeline daily, unattended
- [ ] A public Streamlit URL displays the ETF Analytics Dashboard, matching the mockup design,
      viewable by anyone with no login
- [ ] You can delete this repo from your local machine entirely and the live dashboard keeps
      updating daily without any action from you

---

*Documentation written for review. Implementation begins only after approval.*
