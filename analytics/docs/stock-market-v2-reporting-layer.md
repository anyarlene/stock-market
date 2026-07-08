# Stock-Market v2 — Reporting Layer (Streamlit + DuckDB)

> **Status:** Approved direction — pending implementation
> **Supersedes:** `stock-market-v1.md` (Metabase plan). That plan was never fully implemented;
> production had already diverged to Grafana Cloud. This document is the single source of truth
> for the reporting layer going forward.
> **Goal:** A clean, cost-free, publicly accessible dashboard, visually matching
> `assets/etf-dashboard-mockup.png`, without adding a hosted database server or another
> partially-adopted visualization tool.

---

## 1. Why this supersedes v1

The project has accumulated visualization approaches over time without formally retiring the
previous one:

| Order | Tool | Status before this doc |
|---|---|---|
| 1 | Chart.js + GitHub Pages | Planned for archive in v1, never fully removed |
| 2 | Metabase (OSS, Docker) | Planned in v1, not what's actually running in prod |
| 3 | Grafana Cloud | Actually running in production today (per root `README.md`) |
| 4 | Streamlit (this doc) | New, final direction |

This churn — not the database choice — was the main risk to keeping the project clean. This
document exists to make Streamlit the **one** dashboard going forward and explicitly retire
the rest, rather than adding a fifth tool alongside the others.

---

## 2. What changes and why

| Layer | Current | New |
|---|---|---|
| Production warehouse | PostgreSQL on Supabase (hosted, free tier) | **DuckDB file**, built by the pipeline, no server |
| Local dev warehouse | PostgreSQL (Docker) | **Unchanged** — stays PostgreSQL in Docker |
| dbt | Single target: `postgres` | **Two targets:** `dev` (postgres, local) and `prod` (duckdb, file-based) |
| Orchestration (local) | Airflow (Docker) | **Unchanged** — stays functional, only the `visualize` task changes |
| Orchestration (prod) | GitHub Actions (no Airflow) | **Unchanged** in structure, `visualize` step replaced |
| Dashboard | Grafana Cloud (public dashboards, restricted/read-only mode) | **Streamlit app**, full custom design, genuinely public |
| Hosting for dashboard | Grafana Cloud | **Streamlit Community Cloud** (free forever, non-commercial use) |
| Static website | GitHub Pages (Chart.js, partially archived already) | **Archived** — Streamlit URL becomes the single public front door |

### Why DuckDB instead of keeping Supabase for production

- The dataset is small and low-write (5 ETFs, daily batch updates) — this is not a workload that
  needs an always-on multi-user relational server.
- Supabase's free tier **auto-pauses after ~7 days of inactivity** — an operational risk with no
  upside for this use case.
- DuckDB removes connection strings, server credentials, networking, and pause/wake failure modes
  entirely. The pipeline produces a file; the dashboard reads a file.
- `dbt-duckdb` uses the same dbt models (staging → intermediate → marts) with only the target
  changed — no rewrite of SQL logic.

### Why Airflow and local Postgres are explicitly kept

- Airflow remains valuable for demonstrating/exercising real orchestration (DAGs, retries,
  dependencies) in local development.
- Local Postgres (Docker) is not a cost or stability concern — it never leaves your machine.
- Only the **production data path** and the **visualize** step change. Nothing about local
  development changes except one Airflow task's implementation.

---

## 3. New architecture

```
                    LOCAL DEVELOPMENT (unchanged)
┌───────────────────────────────────────────────────────────────┐
│  Apache Airflow (Docker) → PostgreSQL (Docker) → dbt (dev)      │
│  DAG: etf_market_data_pipeline                                  │
└───────────────────────────────────────────────────────────────┘

                    PRODUCTION (changed)
┌────────────────────────────────────────────────────────────────────┐
│  GitHub Actions (daily, Mon–Fri 21:15 UTC)                           │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  ┌──────────┐      │
│  │ Extract&Load │→ │  Transform   │→ │ Quality │→ │ Publish  │      │
│  │ (yfinance →  │  │  dbt run     │  │ dbt test│  │ artifact │      │
│  │  local .db   │  │  --target=   │  │ + source│  │ (DuckDB  │      │
│  │  file)       │  │  duckdb      │  │freshness│  │  file)   │      │
│  └──────────────┘  └──────────────┘  └─────────┘  └────┬─────┘      │
└────────────────────────────────────────────────────────┼───────────┘
                                                          │
                                                          ▼
                              GitHub Release asset (tag: latest-data)
                              warehouse.duckdb, overwritten daily
                                                          │
                                                          ▼
                        ┌─────────────────────────────────────┐
                        │  Streamlit app (Streamlit Cloud)     │
                        │  downloads + caches warehouse.duckdb │
                        │  renders ETF Analytics Dashboard     │
                        │  Public URL, no login required       │
                        └─────────────────────────────────────┘
```

---

## 4. dbt changes

Add a second target to `dbt/profiles.yml`:

```yaml
etf_analytics:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DB_HOST', 'localhost') }}"
      # ... existing local config, unchanged ...
    prod:
      type: duckdb
      path: "{{ env_var('DUCKDB_PATH', 'warehouse.duckdb') }}"
      threads: 4
```

- `dbt run --profiles-dir . --target dev` → local Postgres (Airflow/dev workflow, unchanged)
- `dbt run --profiles-dir . --target prod` → builds `warehouse.duckdb` (used in GitHub Actions)

**Known risk to validate during implementation:** dbt models must stay ANSI-SQL-compatible across
both adapters. A few functions (date arithmetic, string functions) can differ slightly between
Postgres and DuckDB — each mart model should be tested against both targets before this is
considered done.

Add `dbt-duckdb` and `duckdb` to `requirements.txt`.

---

## 5. Airflow DAG changes

Only the final stage changes:

| Stage | Before | After |
|---|---|---|
| `extract_load` | Unchanged | Unchanged |
| `transform` | Unchanged | Unchanged |
| `quality` | Unchanged | Unchanged |
| `visualize` | `provision_grafana` (Grafana REST API) | `publish_duckdb_artifact` (builds `--target duckdb`, no external API needed for local runs; local runs can skip publishing) |

The DAG keeps its 4-stage shape. Locally, the last stage can simply confirm the DuckDB file built
successfully — publishing to a GitHub Release is a production-only concern, handled in GitHub
Actions, not required for local Airflow runs.

---

## 6. Production GitHub Actions changes (`production_automation.yml`)

Add steps after the existing `dbt run`:

- `dbt run --profiles-dir dbt --target prod` (builds `warehouse.duckdb`)
- `dbt test --profiles-dir dbt --target prod`
- Publish `warehouse.duckdb` as a GitHub Release asset under a fixed tag (e.g. `latest-data`),
  overwriting the previous asset each run (use `gh release upload --clobber` or equivalent action)

Remove: the Supabase `DATABASE_URL` write step and the Grafana provisioning step for production
runs (kept only if you want to dual-run during a transition period — see Section 8).

---

## 7. Streamlit dashboard design

Reads `warehouse.duckdb` (downloaded from the GitHub Release URL, cached with `st.cache_data`, TTL
matched to the daily pipeline schedule so it refreshes once/day without re-downloading on every
visitor).

Mapped directly from `assets/etf-dashboard-mockup.png`:

| Mockup panel | Streamlit / Plotly implementation |
|---|---|
| Dark theme | `.streamlit/config.toml` — dark base + custom accent colors |
| 5 KPI cards (ticker, price, % change, sparkline) | `st.columns(5)` + `st.metric()` per ETF + small Plotly sparkline |
| Price history chart, 1M/3M/1Y/2Y/ALL buttons | Plotly `go.Figure` with native `rangeselector` buttons |
| Entry point thresholds (horizontal bars) | Plotly horizontal bar chart, one bar per threshold level |
| 52-week summary table | `st.dataframe()` with conditional red/green formatting |

Data source: `mart_price_history`, `mart_52week_metrics`, `mart_entry_thresholds` — same marts
already defined in `dbt/models/marts/`, unchanged.

---

## 8. What gets archived

| Item | Action |
|---|---|
| Grafana Cloud dashboard + provisioning | Archive. Keep `analytics/docs/grafana_setup.md` but mark superseded at the top of the file |
| `docker-compose.prod.yml` (Oracle Cloud VM, Metabase) | Archive — no VM/Metabase needed once Streamlit Cloud hosts the dashboard |
| Supabase production database | Archive — production data now lives in the published DuckDB file, not a hosted DB |
| `website/` (GitHub Pages, Chart.js, investment planner) | Archive fully — Streamlit's public URL becomes the single front door. Update root `README.md` to link to it |
| `.github/workflows/deploy-website.yml` | Remove or archive alongside `website/` |
| `stock-market-v1.md` | Mark superseded at the top, keep for history, do not delete |

---

## 9. What is explicitly NOT changed

- Local Docker Compose (`docker-compose.yml`): PostgreSQL + Metabase for local dev — unchanged
  (Metabase can stay as a local exploration tool if useful; it's just not the production dashboard)
- Airflow DAG structure and local dev workflow — unchanged except the final stage's implementation
- `dbt/models/` staging and intermediate layers — unchanged
- Data extraction (yfinance) logic — unchanged

---

## 10. Cost and stability summary

| Component | Cost | Notes |
|---|---|---|
| GitHub Actions | Free | Public repo — unlimited minutes |
| DuckDB file build | Free | No server, no hosting |
| GitHub Release (data storage) | Free | Well within GitHub's storage limits for a small file |
| Streamlit Community Cloud | Free forever | Non-commercial use, ~1GB RAM, sleeps after ~12h idle |
| Local Postgres/Airflow/Metabase | Free | Docker, local machine only |

No component in this design has a trial period, a renewal requirement, or a usage-based billing risk.

---

## 11. Implementation checklist

### Phase A — dbt DuckDB target
- [ ] Add `prod` target (DuckDB) to `dbt/profiles.yml`
- [ ] Add `dbt-duckdb`, `duckdb` to `requirements.txt`
- [ ] Run all mart models against `--target prod` locally, fix any dialect-specific SQL

### Phase B — Production pipeline
- [ ] Update `production_automation.yml`: build DuckDB file, run tests, publish as Release asset
- [ ] Remove Supabase `DATABASE_URL` write and Grafana provisioning from the production workflow

### Phase C — Airflow
- [ ] Replace `provision_grafana` task with `publish_duckdb_artifact` (or a local-only build
      confirmation step) in `airflow/dags/etf_pipeline.py`

### Phase D — Streamlit app
- [ ] New `dashboard/` folder: `app.py`, `requirements.txt`, `.streamlit/config.toml`
- [ ] Implement KPI cards, price history chart, threshold bars, summary table per Section 7
- [ ] Deploy via Streamlit Community Cloud, connect to this GitHub repo

### Phase E — Archive
- [ ] Move `website/`, `docker-compose.prod.yml` to an `archive/` folder (or a clearly marked git
      tag/branch) — do not silently delete history
- [ ] Add "Superseded by `stock-market-v2-reporting-layer.md`" banner to `stock-market-v1.md`
- [ ] Add "Superseded" banner to `grafana_setup.md`
- [ ] Update root `README.md`: architecture diagram, tech stack table, and the public dashboard
      link now point to Streamlit
