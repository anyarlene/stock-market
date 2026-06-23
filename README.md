# ETF Analytics — End-to-End Data Engineering Pipeline

A production-style Data Engineering project tracking 5 ETFs (VOO, VTI, QQQ, VUAA.L, CNDX.L).
Demonstrates a complete, automated ELT pipeline from raw market data to live dashboards.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION                               │
│                                                                      │
│   Apache Airflow  ──────────────────────────────────────────────    │
│   (local Docker)       DAG: etf_market_data_pipeline                │
│                                                                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────┐  │
│   │ Extract&Load │→ │  Transform   │→ │   Quality    │→ │ Viz   │  │
│   │              │  │              │  │              │  │       │  │
│   │ init_db      │  │ dbt staging  │  │ dbt test     │  │ sync  │  │
│   │ load_symbols │  │ dbt interm.  │  │ dbt source   │  │ Meta- │  │
│   │ fetch_data   │  │ dbt marts    │  │   freshness  │  │ base  │  │
│   └──────────────┘  └──────────────┘  └──────────────┘  └───────┘  │
└───────────┬─────────────────┬────────────────────────────────┬──────┘
            │                 │                                │
            ▼                 ▼                                ▼
  ┌──────────────────┐  ┌───────────────────────┐  ┌──────────────────┐
  │   Yahoo Finance  │  │      PostgreSQL        │  │    Metabase      │
  │   (yfinance)     │  │  (Supabase free tier)  │  │ (Oracle Cloud    │
  │                  │  │                        │  │  Always Free VM) │
  │  OHLCV prices    │  │  Raw tables  (Python)  │  │                  │
  │  FX rates        │  │  Mart tables (dbt)     │  │  Live dashboard  │
  └──────────────────┘  └───────────────────────┘  │  auto-refreshed  │
                                                    └──────────────────┘

  GitHub Actions → daily schedule (production, no Airflow server needed)
```

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| **Orchestration** | Apache Airflow 2.9 | DAG scheduling, task dependencies, retries |
| **Extract & Load** | Python + yfinance | Incremental fetch from Yahoo Finance → PostgreSQL |
| **Transform** | dbt Core 1.8 | Staging → Intermediate → Mart models |
| **Warehouse** | PostgreSQL 16 | Single source of truth (Supabase in production) |
| **Visualization** | Grafana Cloud (free) | Always-on dashboards, no server needed |
| **CI / CD** | GitHub Actions | Tests on every PR; daily pipeline run in production |
| **Infrastructure** | Docker Compose | Local dev (Airflow + PostgreSQL + Metabase) |

---

## Pipeline — What Happens Every Weekday Night

```
21:15 UTC  Airflow scheduler triggers etf_market_data_pipeline
           │
           ├── extract_load
           │    ├── init_database      ensure schema is current (idempotent)
           │    ├── load_symbols       reload ETF reference data from CSV
           │    └── fetch_market_data  incremental OHLCV fetch from Yahoo Finance
           │
           ├── transform              (runs only if extract_load succeeds)
           │    ├── dbt_run_staging        stg_etf_data, stg_currency_rates
           │    ├── dbt_run_intermediate   int_etf_eur  (EUR fallback logic)
           │    └── dbt_run_marts          mart_price_history
           │                               mart_52week_metrics
           │                               mart_entry_thresholds
           │
           ├── quality                (test + freshness run in parallel)
           │    ├── dbt_test               schema tests: not_null, unique
           │    └── dbt_source_freshness   SLA: warn >12 h, error >24 h
           │
           └── visualize              (skipped when GRAFANA_URL not set)
                └── provision_grafana  Grafana dashboard provisioning via REST API
```

---

## dbt Data Models

```
dbt/models/
├── staging/                    materialized as VIEWS
│   ├── sources.yml             raw source definitions + freshness SLA
│   ├── schema.yml              staging model + column documentation
│   ├── stg_etf_data.sql        clean OHLCV joined with ETF metadata
│   └── stg_currency_rates.sql  validated historical FX rates
│
├── intermediate/               materialized as VIEWS
│   └── int_etf_eur.sql         guarantees EUR columns on every row
│                               (ETL value → same-day rate → latest rate)
│
└── marts/                      materialized as TABLES (for fast Metabase queries)
    ├── schema.yml              full column documentation for all marts
    ├── mart_price_history.sql  daily OHLCV + EUR + daily Δ% + 7-day MA
    ├── mart_52week_metrics.sql latest 52w high/low + distance from high/low
    └── mart_entry_thresholds.sql 5–30% entry levels (long format, 30 rows total)
```

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

## Local Development — Quick Start

**Requirements:** Docker Desktop

```bash
# 1. Clone and configure
git clone https://github.com/anyarlene/stock-market.git
cd stock-market
cp .env.example .env                      # edit DB creds if needed

# 2. Start PostgreSQL + Metabase
docker compose up -d

# 3. Start Airflow (builds custom image with dbt + psycopg2)
cd airflow
cp env.example .env                       # edit DATABASE_URL if needed
docker compose up -d --build
cd ..

# 4. Open Airflow at http://localhost:8080  (admin / admin)
#    Unpause the  etf_market_data_pipeline  DAG and trigger a run.

# 5. Open Metabase at http://localhost:3000
#    Connect it to PostgreSQL (host: host.docker.internal, port: 5432)
#    Build the dashboard — see analytics/docs/metabase_setup.md
```

### Run dbt manually (without Airflow)

```bash
pip install -r requirements.txt
cp .env.example .env && source .env       # or set DATABASE_URL in your shell

cd dbt
dbt deps                                  # install dbt_utils
dbt run --profiles-dir .                  # build all models
dbt test --profiles-dir .                 # run all tests
dbt source freshness --profiles-dir .     # check SLA compliance
dbt docs generate --profiles-dir .        # generate data catalog
dbt docs serve --profiles-dir .           # serve at http://localhost:8080
```

---

## Production — Zero Daily Work

| Service | Provider | Cost |
|---|---|---|
| PostgreSQL | [Supabase](https://supabase.com) free tier | Free |
| Daily pipeline | GitHub Actions (schedule trigger) | Free |
| Dashboard | [Grafana Cloud](https://grafana.com) free tier | Free |

**After one-time setup:** open your permanent Grafana URL from any device.
Data refreshes every weekday night automatically. Nothing to run or start.

Required GitHub secrets: `DATABASE_URL`, `GRAFANA_URL`, `GRAFANA_API_KEY`

→ Full setup guide: `analytics/docs/grafana_setup.md`

---

## Project Structure

```
stock-market/
├── airflow/
│   ├── Dockerfile                  custom image with dbt + psycopg2
│   ├── docker-compose.yaml         Airflow stack (scheduler, webserver, triggerer)
│   ├── env.example                 Airflow env vars template
│   ├── requirements.txt            Airflow extra packages
│   └── dags/
│       ├── etf_pipeline.py         ★ main showcase DAG (ELT + dbt + Metabase)
│       └── market_data_update.py   legacy DAG (kept for reference)
│
├── analytics/
│   ├── enhanced_workflow.py        ETL orchestrator (used by Airflow DAG)
│   ├── database/                   schema, DB manager, symbol loader
│   ├── etl/                        fetcher, currency converter
│   ├── utils/                      FX converter, validators
│   └── docs/                       setup guides, Metabase MCP guide
│
├── dbt/
│   ├── dbt_project.yml             project config (staging/int = view, marts = table)
│   ├── profiles.yml                connection via env vars
│   ├── packages.yml                dbt_utils
│   └── models/
│       ├── staging/                sources.yml (with freshness), stg_* models
│       ├── intermediate/           int_etf_eur
│       └── marts/                  mart_price_history, mart_52week_metrics,
│                                   mart_entry_thresholds  (+ full schema docs)
│
├── .github/workflows/
│   ├── production_automation.yml   daily ETL + dbt (Mon–Fri 21:15 UTC)
│   ├── test_automation.yml         CI on every PR (PostgreSQL service container)
│   └── deploy-website.yml          static landing page → GitHub Pages
│
├── docker-compose.yml              local: PostgreSQL + Metabase
├── docker-compose.prod.yml         production: Metabase only (DB on Supabase)
├── .env.example                    environment variable template
└── requirements.txt                Python dependencies
```

---

## Documentation

| File | Topic |
|---|---|
| `analytics/docs/grafana_setup.md` | Grafana Cloud setup (15 min, no card needed) |
| `analytics/docs/stock-market-v1.md` | v1 architecture decisions |
| `analytics/docs/airflow_setup.md` | Airflow local setup guide |

---

## Adding a New ETF

```bash
# 1. Add a row to analytics/database/reference/symbols.csv
# 2. Reload symbols
python analytics/database/load_symbols.py

# 3. Fetch historical data
PYTHONPATH=. python analytics/enhanced_workflow.py --step full

# 4. Rebuild dbt models
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .

# 5. Sync Metabase (Admin → Databases → Sync schema)
```
