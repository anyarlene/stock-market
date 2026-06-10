# Metabase Setup Guide

This guide covers everything needed to start Metabase, connect it to PostgreSQL, and use Cursor's AI agent to build the ETF dashboard automatically.

---

## Prerequisites

- Docker Desktop installed and running
- Project cloned locally
- `.env` file created from `.env.example`

---

## 1. Start the stack

```bash
# Copy env file (first time only)
cp .env.example .env

# Start PostgreSQL + Metabase
docker compose up -d

# Verify both containers are running
docker compose ps
```

PostgreSQL is available at `localhost:5432`.
Metabase UI is available at `http://localhost:3000`.

---

## 2. Run the ETL pipeline

```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize DB schema and load symbols
cd analytics
PYTHONPATH=.. python database/init_db.py
PYTHONPATH=.. python database/load_symbols.py
cd ..

# Fetch market data and calculate metrics
PYTHONPATH=. python analytics/enhanced_workflow.py --step full

# Run dbt transformations (creates mart_ tables)
cd dbt
dbt run --profiles-dir .
cd ..
```

After this step, the following tables are available in PostgreSQL:

| Table | Description |
|---|---|
| `mart_price_history` | Daily OHLCV + EUR prices for all ETFs |
| `mart_52week_metrics` | Latest 52-week high/low + current price per ETF |
| `mart_entry_thresholds` | Entry point levels (5–30% below 52-week high) |

---

## 3. First-time Metabase configuration

1. Open `http://localhost:3000`
2. Complete the setup wizard (create admin account)
3. When asked about your data, choose **I'll add my data later**

### Connect Metabase to PostgreSQL

Go to **Admin > Databases > Add a database** and fill in:

| Field | Value |
|---|---|
| Database type | PostgreSQL |
| Display name | ETF Analytics |
| Host | `host.docker.internal` (Mac/Windows) or `postgres` (Linux Docker network) |
| Port | `5432` |
| Database name | `etf_db` |
| Username | `etf_user` |
| Password | `etf_pass` |

Click **Save** and wait for the metadata sync to complete (~1 minute).

---

## 4. Enable the MCP server (for AI dashboard build)

Go to **Admin > AI > MCP** and:
1. Toggle **MCP server** ON
2. Enable **Cursor and VS Code** under Supported clients
3. Note your MCP endpoint: `http://localhost:3000/api/metabase-mcp`

---

## 5. Connect Cursor to Metabase MCP

Add the MCP server to Cursor settings (Settings > MCP Servers):

```json
{
  "mcpServers": {
    "metabase": {
      "url": "http://localhost:3000/api/metabase-mcp",
      "transport": "streamable-http"
    }
  }
}
```

Or via terminal:

```bash
claude mcp add --transport http metabase http://localhost:3000/api/metabase-mcp
```

Metabase will prompt you to approve the OAuth connection in your browser.

---

## 6. Build the dashboard with Cursor AI

Open Cursor and use the Agent chat. The agent has access to your Metabase instance and can read your table schemas directly.

### Starter prompt

```
Using the Metabase MCP tools, build an ETF analytics dashboard called "ETF Analytics".

The database has these tables:
- mart_price_history (ticker, date, open, high, low, close, close_eur, daily_change_eur_pct, volume)
- mart_52week_metrics (ticker, etf_name, high_52week, low_52week, latest_close_eur, pct_below_52w_high)
- mart_entry_thresholds (ticker, pct_below, threshold_price, is_at_or_below_threshold)

ETFs tracked: VOO, VTI, QQQ, VUAA.L, CNDX.L

Build the following cards and arrange them in a grid dashboard:
1. KPI card for each ETF showing latest close_eur and daily_change_eur_pct
2. Multi-line chart: close_eur over time for all ETFs (from mart_price_history), with a date filter
3. Summary table: ticker, etf_name, latest_close_eur, high_52week, low_52week, pct_below_52w_high
4. Bar chart: threshold_price by pct_below for each ticker (from mart_entry_thresholds),
   colored by is_at_or_below_threshold
```

### Iteration

After the first build, review the dashboard in `http://localhost:3000` and refine:

```
Update the price history chart to add a time range filter parameter
with options: 1 month, 3 months, 1 year, all time.
```

```
Add a ticker filter parameter to the dashboard so I can isolate one ETF at a time.
```

---

## 7. Persistent production database (optional)

For the GitHub Actions workflow to update data daily, the PostgreSQL database must be accessible from the internet. Free hosted options:

| Provider | Free tier | Notes |
|---|---|---|
| [Supabase](https://supabase.com) | 500 MB, always-on | Best option for this project |
| [Neon](https://neon.tech) | 0.5 GB, serverless | Slightly slower cold starts |

Steps:
1. Create a free PostgreSQL instance on Supabase or Neon
2. Run the schema init and symbol load once against that DB
3. Add `DATABASE_URL` to **GitHub repository secrets** (Settings > Secrets > Actions)
4. The daily workflow will then fetch, transform, and dbt-run against the hosted DB
5. Point Metabase at the same hosted DB connection string

---

## 8. Stop the stack

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop and delete all data (full reset)
```
