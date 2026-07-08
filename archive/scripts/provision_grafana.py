#!/usr/bin/env python3
"""Provision Grafana Cloud with the ETF Analytics dashboard.

Run this script once after creating your Grafana account, or re-run it
whenever you want to update the dashboard definition. It is idempotent —
running it multiple times is safe.

Required environment variables
-------------------------------
GRAFANA_URL     Base URL of your Grafana instance
                e.g. https://yourname.grafana.net
GRAFANA_API_KEY Service account token with Admin role
                Grafana → Administration → Service accounts → Add token
DATABASE_URL    Supabase Session Pooler connection string (same secret used
                by GitHub Actions for the daily pipeline)

Usage
-----
    export GRAFANA_URL=https://yourname.grafana.net
    export GRAFANA_API_KEY=glsa_...
    export DATABASE_URL=postgresql://postgres.xxx:pass@aws-0-xxx.pooler.supabase.com:5432/postgres
    python scripts/provision_grafana.py
"""

from __future__ import annotations

import json
import os
import sys
from urllib.parse import urlparse

import requests

GRAFANA_URL = os.environ.get("GRAFANA_URL", "").rstrip("/")
GRAFANA_API_KEY = os.environ.get("GRAFANA_API_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

DATASOURCE_NAME = "ETF Analytics"
DASHBOARD_UID = "etf-analytics-v1"
DASHBOARD_TITLE = "ETF Analytics Dashboard"
GRAFANA_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "grafana", "etf_dashboard.json")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
        "Content-Type": "application/json",
    }


def _get(path: str) -> requests.Response:
    r = requests.get(f"{GRAFANA_URL}{path}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r


def _post(path: str, payload: dict) -> requests.Response:
    r = requests.post(f"{GRAFANA_URL}{path}", headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r


def _put(path: str, payload: dict) -> requests.Response:
    r = requests.put(f"{GRAFANA_URL}{path}", headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r


# ---------------------------------------------------------------------------
# Data source
# ---------------------------------------------------------------------------

def get_or_create_datasource() -> str:
    """Return the UID of the ETF Analytics PostgreSQL data source, creating it if needed."""
    existing = {ds["name"]: ds for ds in _get("/api/datasources").json()}

    if DATASOURCE_NAME in existing:
        uid = existing[DATASOURCE_NAME]["uid"]
        print(f"✅  Data source '{DATASOURCE_NAME}' already exists  (uid: {uid})")
        return uid

    if not DATABASE_URL:
        print(
            "⚠️   DATABASE_URL is not set. Create the data source manually:\n"
            "     Grafana → Connections → Add data source → PostgreSQL\n"
            f"    Name it exactly: {DATASOURCE_NAME!r}"
        )
        sys.exit(1)

    parsed = urlparse(DATABASE_URL)
    payload = {
        "name": DATASOURCE_NAME,
        "type": "grafana-postgresql-datasource",
        "access": "proxy",
        "url": f"{parsed.hostname}:{parsed.port or 5432}",
        "user": parsed.username,
        "database": parsed.path.lstrip("/"),
        "secureJsonData": {"password": parsed.password},
        "jsonData": {
            "sslmode": "require",
            "postgresVersion": 1600,
            "timescaledb": False,
        },
        "isDefault": True,
    }
    uid = _post("/api/datasources", payload).json()["datasource"]["uid"]
    print(f"✅  Created data source '{DATASOURCE_NAME}'  (uid: {uid})")
    return uid


# ---------------------------------------------------------------------------
# Dashboard builder
# ---------------------------------------------------------------------------

def _ds_ref(uid: str) -> dict:
    return {"type": "grafana-postgresql-datasource", "uid": uid}


def _sql_target(sql: str, ref_id: str = "A", fmt: str = "table") -> dict:
    return {"rawSql": sql.strip(), "format": fmt, "refId": ref_id}


def build_dashboard(ds_uid: str) -> dict:
    """Return the full Grafana dashboard definition as a Python dict."""
    ds = _ds_ref(ds_uid)
    panels: list[dict] = []
    pid = 1
    y = 0

    # ── Row 1: KPI stat cards — one per ETF ──────────────────────────────────
    etfs = ["VOO", "VTI", "QQQ", "VUAA.L", "CNDX.L"]
    widths = [5, 5, 5, 5, 4]   # sums to 24
    x = 0
    for i, (ticker, w) in enumerate(zip(etfs, widths)):
        panels.append({
            "id": pid, "type": "stat",
            "title": ticker,
            "gridPos": {"x": x, "y": y, "w": w, "h": 5},
            "datasource": ds,
            "targets": [_sql_target(
                f"SELECT latest_close_eur AS \"Price (EUR)\", "
                f"daily_change_eur_pct AS \"Daily Δ%\" "
                f"FROM mart_52week_metrics WHERE ticker = '{ticker}'",
                fmt="table"
            )],
            "options": {
                "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                "orientation": "vertical",
                "colorMode": "background",
                "graphMode": "none",
                "textMode": "auto",
            },
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "green", "value": 0},
                        ],
                    },
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "Price (EUR)"},
                        "properties": [{"id": "unit", "value": "currencyEUR"}],
                    },
                    {
                        "matcher": {"id": "byName", "options": "Daily Δ%"},
                        "properties": [{"id": "unit", "value": "percent"}],
                    },
                ],
            },
        })
        pid += 1
        x += w
    y += 5

    # ── Row 2: Price History time series ─────────────────────────────────────
    price_sql = """
SELECT
  date::timestamp AS time,
  MAX(CASE WHEN ticker = 'VOO'    THEN close_eur END) AS "VOO",
  MAX(CASE WHEN ticker = 'VTI'    THEN close_eur END) AS "VTI",
  MAX(CASE WHEN ticker = 'QQQ'    THEN close_eur END) AS "QQQ",
  MAX(CASE WHEN ticker = 'VUAA.L' THEN close_eur END) AS "VUAA.L",
  MAX(CASE WHEN ticker = 'CNDX.L' THEN close_eur END) AS "CNDX.L"
FROM mart_price_history
WHERE date >= $__timeFrom()::date AND date <= $__timeTo()::date
GROUP BY date
ORDER BY date
"""
    panels.append({
        "id": pid, "type": "timeseries",
        "title": "Price History — EUR (use time picker to zoom)",
        "gridPos": {"x": 0, "y": y, "w": 24, "h": 12},
        "datasource": ds,
        "targets": [_sql_target(price_sql, fmt="time_series")],
        "fieldConfig": {
            "defaults": {
                "unit": "currencyEUR",
                "custom": {"lineWidth": 2, "fillOpacity": 5, "spanNulls": True},
            },
            "overrides": [],
        },
        "options": {
            "tooltip": {"mode": "multi", "sort": "none"},
            "legend": {
                "displayMode": "table",
                "placement": "bottom",
                "calcs": ["lastNotNull", "min", "max"],
            },
        },
    })
    pid += 1
    y += 12

    # ── Row 3: 52-Week Metrics table ─────────────────────────────────────────
    metrics_sql = """
SELECT
  ticker                 AS "Ticker",
  etf_name               AS "ETF Name",
  latest_close_eur       AS "Price (EUR)",
  daily_change_eur_pct   AS "Daily Δ%",
  high_52week            AS "52w High",
  low_52week             AS "52w Low",
  pct_below_52w_high     AS "% Below High",
  pct_above_52w_low      AS "% Above Low",
  latest_price_date      AS "Last Updated"
FROM mart_52week_metrics
ORDER BY ticker
"""
    panels.append({
        "id": pid, "type": "table",
        "title": "52-Week Metrics",
        "gridPos": {"x": 0, "y": y, "w": 24, "h": 8},
        "datasource": ds,
        "targets": [_sql_target(metrics_sql)],
        "fieldConfig": {
            "defaults": {"custom": {"align": "auto", "inspect": False}},
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Price (EUR)"},
                    "properties": [{"id": "unit", "value": "currencyEUR"}],
                },
                {
                    "matcher": {"id": "byName", "options": "Daily Δ%"},
                    "properties": [
                        {"id": "unit", "value": "percent"},
                        {"id": "custom.displayMode", "value": "color-text"},
                        {
                            "id": "thresholds",
                            "value": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "red", "value": None},
                                    {"color": "green", "value": 0},
                                ],
                            },
                        },
                    ],
                },
                {
                    "matcher": {"id": "byName", "options": "% Below High"},
                    "properties": [
                        {"id": "unit", "value": "percent"},
                        {"id": "custom.displayMode", "value": "color-background"},
                        {
                            "id": "thresholds",
                            "value": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 5},
                                    {"color": "red", "value": 15},
                                ],
                            },
                        },
                    ],
                },
            ],
        },
        "options": {"footer": {"show": False}, "sortBy": []},
    })
    pid += 1
    y += 8

    # ── Row 4: Entry Thresholds table ────────────────────────────────────────
    threshold_sql = """
SELECT
  ticker                                              AS "Ticker",
  pct_below                                           AS "% Below 52w High",
  threshold_price                                     AS "Threshold Price",
  latest_close                                        AS "Current Price",
  gap_to_threshold_pct                                AS "Gap to Threshold %",
  CASE WHEN is_at_or_below_threshold THEN '🟢 Signal' ELSE '⬜ Not Yet' END AS "Buy Signal"
FROM mart_entry_thresholds
ORDER BY ticker, pct_below
"""
    panels.append({
        "id": pid, "type": "table",
        "title": "Entry Point Thresholds (5 – 30% below 52w High)",
        "gridPos": {"x": 0, "y": y, "w": 24, "h": 12},
        "datasource": ds,
        "targets": [_sql_target(threshold_sql)],
        "fieldConfig": {
            "defaults": {"custom": {"align": "auto"}},
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "% Below 52w High"},
                    "properties": [{"id": "unit", "value": "percent"}],
                },
                {
                    "matcher": {"id": "byName", "options": "Gap to Threshold %"},
                    "properties": [
                        {"id": "unit", "value": "percent"},
                        {"id": "custom.displayMode", "value": "color-text"},
                        {
                            "id": "thresholds",
                            "value": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 0},
                                ],
                            },
                        },
                    ],
                },
            ],
        },
        "options": {"footer": {"show": False}},
    })

    return {
        "title": DASHBOARD_TITLE,
        "uid": DASHBOARD_UID,
        "tags": ["etf", "finance", "dbt", "portfolio"],
        "schemaVersion": 38,
        "version": 1,
        "refresh": "1h",
        "time": {"from": "now-1y", "to": "now"},
        "timepicker": {},
        "panels": panels,
        "annotations": {"list": []},
        "templating": {"list": []},
        "links": [],
        "graphTooltip": 1,
        "fiscalYearStartMonth": 0,
        "liveNow": False,
    }


# ---------------------------------------------------------------------------
# Push to Grafana
# ---------------------------------------------------------------------------

def push_dashboard(dashboard: dict) -> str:
    result = _post(
        "/api/dashboards/db",
        {
            "dashboard": dashboard,
            "overwrite": True,
            "message": "Provisioned by scripts/provision_grafana.py",
        },
    ).json()
    return f"{GRAFANA_URL}{result.get('url', '/dashboards')}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if not GRAFANA_URL or not GRAFANA_API_KEY:
        print("❌  Set GRAFANA_URL and GRAFANA_API_KEY before running this script.")
        print("    See analytics/docs/grafana_setup.md for instructions.")
        sys.exit(1)

    print(f"🔗  Grafana: {GRAFANA_URL}\n")

    ds_uid = get_or_create_datasource()
    dashboard = build_dashboard(ds_uid)

    # Save JSON copy to grafana/ for version control + manual import
    os.makedirs(os.path.dirname(os.path.abspath(GRAFANA_JSON_PATH)), exist_ok=True)
    with open(GRAFANA_JSON_PATH, "w") as f:
        json.dump(dashboard, f, indent=2)
    print(f"💾  Dashboard JSON → grafana/etf_dashboard.json")

    url = push_dashboard(dashboard)
    print(f"✅  Dashboard live → {url}")
    print("\nDone. GitHub Actions will keep your data fresh every weekday night.")


if __name__ == "__main__":
    main()
