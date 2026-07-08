# Metabase Setup Guide

> **⚠️ SUPERSEDED** by `stock-market-v2-reporting-layer.md` (v3 DuckDB-only roadmap).
> Metabase is retired as the production dashboard; this document is kept for historical reference only.

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

## 7. Stop the local stack

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop and delete all data (full reset)
```

---

---

# Production Setup — Dashboard from anywhere, zero daily work

> **Goal:** open a URL in any browser → see today's data. No local Docker. No manual runs.
>
> **Stack:** Supabase (database) + Oracle Cloud free VM (Metabase) + GitHub Actions (daily data update)

---

## Step 1 — Supabase (free PostgreSQL, always-on)

1. Go to [supabase.com](https://supabase.com) → **Start for free** → create a project
2. Choose a region close to you, set a strong DB password
3. Go to **Project Settings → Database → Connection string → URI**
4. Copy the connection string — it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
5. Keep it safe — you will use it in steps 2 and 3

### Initialize the database on Supabase (one time only)

Run these commands locally with your Supabase `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"

cd analytics
PYTHONPATH=.. python database/init_db.py
PYTHONPATH=.. python database/load_symbols.py
cd ..

# Run a full data fetch to populate the database
PYTHONPATH=. python analytics/enhanced_workflow.py --step full

# Run dbt to create the mart tables
cd dbt && dbt run --profiles-dir . && cd ..
```

After this, the data is in Supabase and refreshes automatically every weekday via GitHub Actions.

---

## Step 2 — GitHub Actions (daily automatic updates)

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Name: `DATABASE_URL`
4. Value: your Supabase connection string from Step 1
5. Click **Add secret**

That's it. GitHub Actions will now run the ETL + dbt every weekday at 10:15 PM Berlin time, writing fresh data to Supabase automatically.

---

## Step 3 — Oracle Cloud free VM (Metabase, always-on)

### 3a. Create the VM

1. Go to [cloud.oracle.com](https://cloud.oracle.com) → **Start for free** (no credit card billing for Always Free resources)
2. After signup, go to **Compute → Instances → Create Instance**
3. Change shape: click **Change Shape** → **Ampere** → select `VM.Standard.A1.Flex`
   - Set **OCPUs: 2**, **Memory: 12 GB** (well within the Always Free quota)
4. Choose **Ubuntu 22.04** as the image
5. Download the SSH key when prompted (you will need it to connect)
6. Click **Create**

### 3b. Open the firewall for port 3000

**In the Oracle Cloud console:**

1. Go to your instance → **Subnet** → **Security List**
2. Add an **Ingress Rule**:
   - Source CIDR: `0.0.0.0/0`
   - Destination port: `3000`
   - Protocol: TCP

**On the VM itself** (after SSH in):

```bash
sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT
sudo netfilter-persistent save
```

### 3c. Install Docker on the VM

SSH into your VM:

```bash
ssh -i <your-key.pem> ubuntu@<your-oracle-ip>
```

Then install Docker:

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker ubuntu
# log out and back in for group change to take effect
exit
ssh -i <your-key.pem> ubuntu@<your-oracle-ip>
```

### 3d. Deploy Metabase

```bash
# Clone the repo
git clone https://github.com/anyarlene/stock-market.git
cd stock-market

# Start Metabase (production compose — no local PostgreSQL)
docker compose -f docker-compose.prod.yml up -d

# Check it is running
docker compose -f docker-compose.prod.yml ps
```

Metabase will be available at:
```
http://<your-oracle-ip>:3000
```

Metabase starts in about 2 minutes the first time (JVM warmup).

---

## Step 4 — Connect Metabase to Supabase (one time only)

1. Open `http://<your-oracle-ip>:3000` in your browser
2. Complete the setup wizard (create admin account)
3. Choose **I'll add my data later**
4. Go to **Admin → Databases → Add a database**

| Field | Value |
|---|---|
| Database type | PostgreSQL |
| Display name | ETF Analytics |
| Host | `db.[YOUR-PROJECT-REF].supabase.co` |
| Port | `5432` |
| Database name | `postgres` |
| Username | `postgres` |
| Password | your Supabase DB password |
| SSL | Required |

5. Click **Save** — Metabase syncs the schema (~1 minute)

---

## Step 5 — Build the dashboard with Cursor AI (one time only)

Enable the MCP server on your Oracle VM Metabase:

1. Go to **Admin → AI → MCP** → toggle ON
2. Enable **Cursor and VS Code**
3. MCP endpoint: `http://<your-oracle-ip>:3000/api/metabase-mcp`

Add to Cursor settings (Settings → MCP Servers):

```json
{
  "mcpServers": {
    "metabase": {
      "url": "http://<your-oracle-ip>:3000/api/metabase-mcp",
      "transport": "streamable-http"
    }
  }
}
```

Use the starter prompt from [Step 6 of the local guide](#6-build-the-dashboard-with-cursor-ai) to build the dashboard.

---

## Daily routine after setup

| What happens | When | Your involvement |
|---|---|---|
| ETL fetch + dbt run | Every weekday at 10:15 PM Berlin time | None — automatic |
| Dashboard shows fresh data | Every morning | Open URL, read, close |
| Dashboard improvements | Whenever you want | Prompt Cursor, done |

**You never need to run anything manually.**
