# ETF Analytics — End-to-End Data Engineering Pipeline

A cost-free, fully cloud-run Data Engineering project tracking 5 ETFs (VOO, VTI, QQQ, VUAA.L, CNDX.L).
It runs a complete **ELT** pipeline — from raw market data to a public dashboard — with no database
server and no local machine involvement.

> **Live dashboard:** _add your Streamlit Community Cloud URL here_
>
> **Design & roadmap:** [`analytics/docs/stock-market-v2-reporting-layer.md`](analytics/docs/stock-market-v2-reporting-layer.md) is the single source of truth for the architecture direction.

---

## Architecture

```
                    SINGLE ENVIRONMENT — FULLY CLOUD-RUN
┌──────────────────────────────────────────────────────────────────────┐
│  GitHub Actions — one workflow, daily schedule (Mon–Fri 21:15 UTC)     │
│  + workflow_dispatch for manual runs                                   │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  ┌────────────┐      │
│  │ Extract&Load │→ │  Transform   │→ │ Quality │→ │  Publish   │      │
│  │ yfinance →   │  │  dbt run     │  │dbt test │  │ warehouse. │      │
│  │ DuckDB file  │  │              │  │         │  │ duckdb →   │      │
│  │ (Python)     │  │              │  │         │  │ GH Release │      │
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

This is **ELT**, not ETL: Python **E**xtracts from Yahoo Finance and **L**oads raw rows into DuckDB;
dbt then **T**ransforms them into the marts the dashboard reads.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| **Extract & Load** | Python + `yfinance` | Fetch OHLCV + FX rates → raw DuckDB tables |
| **Warehouse** | DuckDB (single file) | `warehouse.duckdb` — no server, built by the pipeline |
| **Transform** | dbt Core + `dbt-duckdb` | Staging → Intermediate → Mart models |
| **Orchestration / CI** | GitHub Actions | Daily pipeline + tests on every push/PR |
| **Data distribution** | GitHub Releases | `warehouse.duckdb` published under the `latest-data` tag |
| **Dashboard** | Streamlit + Plotly | Public dashboard on Streamlit Community Cloud |

No component has a server, a trial period, or usage-based billing.

---

## Tracked ETFs

| Ticker | Name | Exchange | Currency |
|---|---|---|---|
| VOO | Vanguard S&P 500 ETF | NYSE | USD |
| VTI | Vanguard Total Stock Market ETF | NYSE | USD |
| QQQ | Invesco QQQ Trust | NASDAQ | USD |
| VUAA.L | Vanguard S&P 500 UCITS ETF | LSE | USD |
| CNDX.L | iShares NASDAQ 100 UCITS ETF | LSE | GBP |

---

## dbt Data Models

```
dbt/models/
├── staging/                    materialized as VIEWS
│   ├── sources.yml             raw source definitions + freshness SLA
│   ├── stg_etf_data.sql        clean OHLCV joined with ETF metadata
│   └── stg_currency_rates.sql  validated historical FX rates
│
├── intermediate/               materialized as VIEWS
│   └── int_etf_eur.sql         guarantees EUR columns on every row
│
└── marts/                      materialized as TABLES
    ├── mart_price_history.sql   daily OHLCV + EUR + daily Δ% + 7-day MA
    ├── mart_52week_metrics.sql  52w high/low + distance from high/low
    └── mart_entry_thresholds.sql 5–30% entry levels (long format)
```

---

## Local Development — Quick Start

No database server or Docker required — the warehouse is a single DuckDB file.

```bash
# 1. Install dependencies (Python 3.12 recommended)
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Build the warehouse: extract + load + fetch (needs internet — hits Yahoo Finance)
#    Creates ./warehouse.duckdb, loads reference symbols, fetches OHLCV + FX rates.
PYTHONPATH=. .venv/bin/python analytics/enhanced_workflow.py --step full
#    Use --step incremental for a daily top-up once data exists.

# 3. Transform + test (run from the dbt/ directory)
cd dbt
../.venv/bin/dbt deps
../.venv/bin/dbt run  --profiles-dir .
../.venv/bin/dbt test --profiles-dir .
cd ..

# 4. Run the dashboard locally (reads ./warehouse.duckdb)
.venv/bin/pip install -r dashboard/requirements.txt
.venv/bin/streamlit run dashboard/app.py     # http://localhost:8501
```

**DuckDB path:** the ETL (run from the repo root) and dbt (run from `dbt/`, using
`../warehouse.duckdb`) resolve to the same repo-root `warehouse.duckdb`. Override with an
**absolute** `DUCKDB_PATH` if needed.

---

## Production — Zero Daily Work

| Concern | How |
|---|---|
| Daily pipeline | GitHub Actions (`.github/workflows/production_automation.yml`), Mon–Fri 21:15 UTC + manual `workflow_dispatch` |
| Data storage | `warehouse.duckdb` published as the `latest-data` GitHub Release asset (overwritten each run) |
| Dashboard | Streamlit Community Cloud, `dashboard/app.py`, auto-downloads the Release asset |

The pipeline uses the built-in `GITHUB_TOKEN` (workflow has `contents: write`) — no extra secrets.
After a one-time Streamlit Cloud deploy, the dashboard refreshes daily on its own.

---

## Project Structure

```
stock-market/
├── analytics/
│   ├── enhanced_workflow.py        ETL orchestrator (used by GitHub Actions)
│   ├── database/                   schema (DuckDB), DB manager, symbol loader, init
│   ├── etl/                        enhanced_market_data_fetcher (yfinance)
│   ├── utils/                      currency converter, validators
│   ├── database_diagnostic.py      warehouse status report
│   └── docs/
│       ├── stock-market-v2-reporting-layer.md   architecture roadmap (source of truth)
│       └── assets/                 dashboard mockup
│
├── dbt/
│   ├── dbt_project.yml             project config (staging/int = view, marts = table)
│   ├── profiles.yml                single DuckDB target
│   └── models/                     staging, intermediate, marts (+ schema docs)
│
├── dashboard/
│   ├── app.py                      Streamlit dashboard (reads DuckDB marts)
│   ├── requirements.txt            Streamlit Cloud dependencies
│   └── .streamlit/config.toml      dark theme
│
├── .github/workflows/
│   ├── production_automation.yml   daily ELT + dbt + publish DuckDB Release asset
│   └── test_automation.yml         CI health check on every push/PR
│
├── archive/                        retired code/infra/docs (not part of the running system)
├── requirements.txt                pipeline Python dependencies
└── .env.example                    optional DUCKDB_PATH override
```

Historical/retired material (Airflow, Metabase, Grafana, the old Chart.js website, and superseded
setup guides) lives under [`archive/`](archive/) and is intentionally not part of the running system.

---

## Adding a New ETF

```bash
# 1. Add a row to analytics/database/reference/symbols.csv
# 2. Rebuild the warehouse and models
PYTHONPATH=. .venv/bin/python analytics/enhanced_workflow.py --step full
cd dbt && ../.venv/bin/dbt run --profiles-dir . && ../.venv/bin/dbt test --profiles-dir .
```
