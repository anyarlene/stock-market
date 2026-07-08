# Grafana Cloud Setup — ETF Analytics Dashboard

> **⚠️ SUPERSEDED** by `stock-market-v2-reporting-layer.md` (v3 DuckDB-only roadmap).
> Grafana is retired as the reporting layer; this document is kept for historical reference only.

**Goal:** live dashboard at a permanent URL, always on, cost-free, no server to manage.

**Time needed:** ~15 minutes (one time only).

---

## Step 1 — Get your Grafana API token (2 min)

1. Log in at [grafana.com](https://grafana.com)
2. Go to **Administration → Service accounts**
3. Click **Add service account** → name it `etf-pipeline` → role **Admin**
4. Click **Add service account token** → copy the token (starts with `glsa_...`)

Keep this token safe — you need it in Steps 2 and 3.

---

## Step 2 — Add GitHub secrets (2 min)

Go to your GitHub repo → **Settings → Secrets and variables → Actions** → add:

| Secret name | Value |
|---|---|
| `GRAFANA_URL` | Your Grafana instance URL, e.g. `https://yourname.grafana.net` |
| `GRAFANA_API_KEY` | The token you copied in Step 1 |

Your `DATABASE_URL` secret is already set from the Supabase setup.

---

## Step 3 — Run the provisioning script (1 min)

The script creates the PostgreSQL data source and builds the full dashboard automatically.

**Option A — via GitHub Actions (recommended, no local install needed):**

Go to your repo → **Actions → Production Market Data Automation** → **Run workflow**.

The workflow already includes an optional Grafana step — it runs automatically when
`GRAFANA_URL` and `GRAFANA_API_KEY` are set.

**Option B — locally:**

```bash
pip install requests
export GRAFANA_URL=https://yourname.grafana.net
export GRAFANA_API_KEY=glsa_...
export DATABASE_URL=postgresql://postgres.xxx:pass@aws-0-xxx.pooler.supabase.com:5432/postgres

python scripts/provision_grafana.py
```

---

## Step 4 — Open your dashboard

The script prints the dashboard URL at the end. It looks like:

```
https://yourname.grafana.net/d/etf-analytics-v1/etf-analytics-dashboard
```

Bookmark it. That URL is permanent and always shows the latest data.

---

## What the dashboard includes

| Panel | Type | Data source |
|---|---|---|
| ETF KPI cards (price + daily Δ%) | Stat | `mart_52week_metrics` |
| Price history (all ETFs, EUR) | Time series | `mart_price_history` |
| 52-Week metrics summary | Table | `mart_52week_metrics` |
| Entry point thresholds (5–30%) | Table | `mart_entry_thresholds` |

---

## Daily routine after setup

GitHub Actions updates Supabase every weekday at 21:15 UTC (Berlin time).
Open your Grafana URL any time — data is always from the previous evening.

**Nothing to run. Nothing to start. Just open the URL.**

---

## Troubleshooting

**"Data source not found" error in the script**
→ The script creates it automatically using `DATABASE_URL`. Make sure the secret is the Supabase Session Pooler URL (starts with `aws-0-...`).

**Dashboard shows "No data"**
→ Go to Grafana → Connections → your data source → Test connection.
→ Make sure the GitHub Actions pipeline has run at least once successfully.

**Dashboard URL changed**
→ It won't — the UID `etf-analytics-v1` is fixed in the script. The URL is always the same.
