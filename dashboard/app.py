"""
ETF Analytics Dashboard (Streamlit) — "imbuto"

Reads the DuckDB warehouse produced by the pipeline (mart_price_history,
mart_52week_metrics, mart_entry_thresholds, mart_fx_rates) and renders the
dashboard from analytics/docs/assets/etf-dashboard-mockup.png.

Data source resolution (first match wins):
  1. $DUCKDB_PATH (if the file exists)
  2. a local warehouse.duckdb in the repo (dev convenience)
  3. the published GitHub Release asset ($WAREHOUSE_URL, tag `latest-data`)

Currency: values are converted via EUR as a pivot (triangulation) so any of
EUR / USD / GBP can be displayed for every ETF.
"""

import os
import tempfile
from datetime import timedelta

import duckdb
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RELEASE_URL = os.environ.get(
    "WAREHOUSE_URL",
    "https://github.com/anyarlene/imbuto/releases/download/latest-data/warehouse.duckdb",
)
DATA_TTL = 6 * 3600  # refresh cached data every 6h (pipeline runs daily)

ORDER = ["VOO", "VTI", "QQQ", "VUAA.L", "CNDX.L"]
COLORS = {
    "VOO": "#3b82f6",
    "VTI": "#a855f7",
    "QQQ": "#22d3ee",
    "VUAA.L": "#eab308",
    "CNDX.L": "#ef4444",
}
CURRENCY_SYMBOL = {"USD": "$", "GBP": "£", "EUR": "€"}
CURRENCIES = ["EUR", "USD", "GBP"]
UP = "#22c55e"
DOWN = "#ef4444"
RANGE_DAYS = {"1M": 30, "3M": 91, "1Y": 365, "2Y": 730, "ALL": None}

st.set_page_config(page_title="ETF Analytics Dashboard", page_icon="📈", layout="wide")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(ttl=DATA_TTL, show_spinner="Downloading latest data…")
def _download_warehouse(url: str) -> str:
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    dest = os.path.join(tempfile.gettempdir(), "etf_warehouse_cached.duckdb")
    with open(dest, "wb") as fh:
        fh.write(resp.content)
    return dest


def _resolve_db_path() -> str:
    env_path = os.environ.get("DUCKDB_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in [
        os.path.join(here, "..", "warehouse.duckdb"),
        os.path.join(os.getcwd(), "warehouse.duckdb"),
        "warehouse.duckdb",
    ]:
        if os.path.exists(cand):
            return cand
    return _download_warehouse(RELEASE_URL)


@st.cache_data(ttl=DATA_TTL)
def load_data():
    con = duckdb.connect(_resolve_db_path(), read_only=True)
    try:
        price = con.execute("SELECT * FROM mart_price_history").df()
        metrics = con.execute("SELECT * FROM mart_52week_metrics").df()
        thresholds = con.execute("SELECT * FROM mart_entry_thresholds").df()
        # mart_fx_rates is newer: tolerate a published warehouse that predates it
        # (the app derives implied rates from price history as a fallback).
        try:
            fx = con.execute("SELECT * FROM mart_fx_rates").df()
        except duckdb.Error:
            fx = pd.DataFrame(columns=["from_currency", "to_currency", "rate_date", "exchange_rate"])
    finally:
        con.close()
    price["date"] = pd.to_datetime(price["date"])
    return price, metrics, thresholds, fx


# ---------------------------------------------------------------------------
# Currency conversion (EUR pivot / triangulation)
# ---------------------------------------------------------------------------
def build_rate_to_eur(fx: pd.DataFrame, price: pd.DataFrame):
    """Latest <ccy>→EUR rate per source currency, plus EUR→EUR = 1.

    Returns (rates, fx_available). If mart_fx_rates is missing from the published
    warehouse (e.g. a stale release built before that model existed), fall back to
    the implied rate from price history (close_eur / close) so the dashboard keeps
    working until the pipeline republishes.
    """
    rates = {"EUR": 1.0}
    if fx is not None and not fx.empty:
        latest = fx.sort_values("rate_date").groupby("from_currency").tail(1)
        for _, r in latest.iterrows():
            rates[r["from_currency"]] = float(r["exchange_rate"])
        return rates, True
    # Fallback: derive implied <ccy>→EUR from price history's EUR columns
    sub = price.dropna(subset=["close", "close_eur"])
    for ccy in sub["native_currency"].unique():
        rows = sub[sub["native_currency"] == ccy].sort_values("date")
        if not rows.empty and rows["close"].iloc[-1]:
            rates[ccy] = float(rows["close_eur"].iloc[-1]) / float(rows["close"].iloc[-1])
    return rates, False


def convert(value, src_ccy, tgt_ccy, rate_to_eur) -> float:
    """Convert a scalar from src_ccy to tgt_ccy via EUR."""
    if value is None or pd.isna(value):
        return None
    if src_ccy not in rate_to_eur or tgt_ccy not in rate_to_eur:
        return float(value)
    value_eur = float(value) * rate_to_eur[src_ccy]
    return value_eur / rate_to_eur[tgt_ccy]


def fmt(value, ccy) -> str:
    sym = CURRENCY_SYMBOL.get(ccy, "")
    if value is None or pd.isna(value):
        return "—"
    return f"{sym}{value:,.2f}"


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      div[data-testid="stMainBlockContainer"], .block-container {
        padding-top: 4.5rem !important; padding-bottom: 2rem; max-width: 1500px;
      }
      #MainMenu, footer {visibility: hidden;}
      .app-header {line-height: 1.25;}
      .app-title {font-size: 1.9rem; font-weight: 800;}
      .app-sub {color: #94a3b8; font-size: 0.95rem;}
      .app-meta {color: #94a3b8; font-size: 0.85rem; text-align: right; margin-top: 6px;}
      .kpi-ticker {font-size: 1.15rem; font-weight: 800;}
      .kpi-name {color: #94a3b8; font-size: 0.8rem; min-height: 2.2em; line-height: 1.1em;}
      .kpi-price {font-size: 1.7rem; font-weight: 800; margin-top: 4px;}
      .kpi-change {font-size: 0.95rem; font-weight: 700;}
      .panel-title {font-size: 1.15rem; font-weight: 700; margin-bottom: 0.2rem;}
      table.summary {width: 100%; border-collapse: collapse; font-size: 0.9rem;}
      table.summary th {color: #94a3b8; text-align: right; padding: 8px 10px; font-weight: 600;
                        border-bottom: 1px solid #1f2a44;}
      table.summary th.left, table.summary td.left {text-align: left;}
      table.summary td {padding: 10px; border-bottom: 1px solid #16203a; text-align: right;}
      .dot {display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 7px;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
try:
    price_df, metrics_df, thresholds_df, fx_df = load_data()
except Exception as exc:  # pragma: no cover - surfaced in the UI
    st.error(
        "Could not load the DuckDB warehouse. Ensure the pipeline has published "
        f"the `latest-data` release or a local `warehouse.duckdb` exists.\n\n{exc}"
    )
    st.stop()

tickers = [t for t in ORDER if t in set(price_df["ticker"])]
metrics_by_ticker = {r["ticker"]: r for _, r in metrics_df.iterrows()}
native_ccy = {t: metrics_by_ticker[t]["native_currency"] for t in tickers if t in metrics_by_ticker}
rate_to_eur, fx_available = build_rate_to_eur(fx_df, price_df)
last_updated = pd.to_datetime(price_df["date"]).max()
data_min = pd.to_datetime(price_df["date"]).min().date()
data_max = last_updated.date()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
h_left, h_right = st.columns([3, 1])
with h_left:
    st.markdown(
        '<div class="app-header">'
        '<span class="app-title">📈 ETF Analytics Dashboard</span><br>'
        '<span class="app-sub">ETF performance overview &amp; entry-point analysis</span>'
        "</div>",
        unsafe_allow_html=True,
    )
with h_right:
    st.markdown(f'<div class="app-meta">Last updated: {last_updated:%b %d, %Y}</div>', unsafe_allow_html=True)
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# Global controls
# ---------------------------------------------------------------------------
c1, c2, c3 = st.columns([2, 1, 2])
with c1:
    focus = st.selectbox("ETF", tickers, index=tickers.index("VOO") if "VOO" in tickers else 0)
with c2:
    currency = st.selectbox("Currency", CURRENCIES, index=CURRENCIES.index("EUR"))
with c3:
    compare_all = st.toggle("Compare all ETFs (normalized)", value=False)

sym = CURRENCY_SYMBOL.get(currency, "")


# ---------------------------------------------------------------------------
# KPI cards (all ETFs, in the selected currency)
# ---------------------------------------------------------------------------
kpi_cols = st.columns(len(tickers))
for col, tk in zip(kpi_cols, tickers):
    sub = price_df[price_df["ticker"] == tk].sort_values("date")
    last = sub.iloc[-1]
    change = last["daily_change_pct"]
    up = bool(change is not None and not pd.isna(change) and change >= 0)
    trend_color = UP if up else DOWN
    # convert EUR series to the selected currency (uniform scale)
    price_val = convert(last["close_eur"], "EUR", currency, rate_to_eur)
    spark = (sub["close_eur"] / rate_to_eur.get(currency, 1.0)).tail(30).tolist()

    with col:
        with st.container(border=True):
            st.markdown(
                f'<div class="kpi-ticker" style="color:{COLORS.get(tk,"#fff")}">{tk}</div>'
                f'<div class="kpi-name">{metrics_by_ticker.get(tk, {}).get("etf_name","")}</div>'
                f'<div class="kpi-price">{fmt(price_val, currency)}</div>'
                f'<div class="kpi-change" style="color:{trend_color}">'
                f'{"▲" if up else "▼"} {change:+.2f}%</div>',
                unsafe_allow_html=True,
            )
            spark_fig = go.Figure(go.Scatter(y=spark, mode="lines", line=dict(color=trend_color, width=2)))
            spark_fig.update_layout(
                height=52, margin=dict(l=0, r=0, t=6, b=0),
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
            )
            st.plotly_chart(spark_fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Price history
# ---------------------------------------------------------------------------
st.markdown("")
title_col, pills_col, cal_col = st.columns([2, 2, 1])
with title_col:
    st.markdown('<p class="panel-title">Price History</p>', unsafe_allow_html=True)
with pills_col:
    selected_range = st.segmented_control(
        "Range", list(RANGE_DAYS.keys()), default="1Y", label_visibility="collapsed"
    )
with cal_col:
    with st.popover("📅 Dates", use_container_width=True):
        custom = st.date_input(
            "Custom range",
            value=(),
            min_value=data_min,
            max_value=data_max,
            format="YYYY-MM-DD",
        )

# Resolve the active window: a custom date range overrides the pills.
start_date = end_date = None
if isinstance(custom, (list, tuple)) and len(custom) == 2:
    start_date = pd.Timestamp(custom[0])
    end_date = pd.Timestamp(custom[1])
else:
    days = RANGE_DAYS.get(selected_range or "1Y")
    end_date = last_updated
    start_date = (last_updated - pd.Timedelta(days=days)) if days else None

mask = price_df["date"] <= end_date
if start_date is not None:
    mask &= price_df["date"] >= start_date
ranged = price_df[mask]

fig = go.Figure()
if compare_all:
    for tk in tickers:
        s = ranged[ranged["ticker"] == tk].sort_values("date")
        if s.empty:
            continue
        base = s["close_eur"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=s["date"], y=s["close_eur"] / base * 100.0, mode="lines", name=tk,
                line=dict(color=COLORS.get(tk), width=2),
                hovertemplate=f"<b>{tk}</b> %{{x|%b %d, %Y}}<br>%{{y:.1f}}%<extra></extra>",
            )
        )
    y_title = "Indexed to 100 at range start"
else:
    s = ranged[ranged["ticker"] == focus].sort_values("date")
    conv = 1.0 / rate_to_eur.get(currency, 1.0)
    series = s["close_eur"] * conv
    fig.add_trace(
        go.Scatter(
            x=s["date"], y=series, mode="lines", name=focus,
            line=dict(color=COLORS.get(focus), width=2.2),
            hovertemplate=f"<b>{focus}</b> %{{x|%b %d, %Y}}<br>{sym}%{{y:,.2f}}<extra></extra>",
        )
    )
    # 52-week high/low (same source as the summary table) in the selected currency
    fm = metrics_by_ticker.get(focus)
    if fm is not None and pd.notna(fm["high_52week"]):
        src = fm["native_currency"]
        hi = convert(fm["high_52week"], src, currency, rate_to_eur)
        lo = convert(fm["low_52week"], src, currency, rate_to_eur)
        fig.add_hline(y=hi, line=dict(color=UP, width=1.3, dash="dash"),
                      annotation_text=f"52W High {fmt(hi, currency)}", annotation_position="top left")
        fig.add_hline(y=lo, line=dict(color=DOWN, width=1.3, dash="dash"),
                      annotation_text=f"52W Low {fmt(lo, currency)}", annotation_position="bottom left")
    y_title = f"Price ({currency})"

fig.update_layout(
    template="plotly_dark", height=430, margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(title=y_title, gridcolor="#1f2a44", ticksuffix="%" if compare_all else ""),
    xaxis=dict(gridcolor="#131c30"),
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Entry thresholds (selected ETF) + 52-week summary
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1])

with left:
    st.markdown(f'<p class="panel-title">Entry Point Thresholds — {focus} (Below 52-Week High)</p>', unsafe_allow_html=True)
    t = thresholds_df[thresholds_df["ticker"] == focus].sort_values("pct_below")
    if t.empty:
        st.info("No threshold data for this ETF.")
    else:
        src = t["native_currency"].iloc[0]
        current = convert(float(t["latest_close"].iloc[0]), src, currency, rate_to_eur)
        labels = [f"{int(p)}% Below High" for p in t["pct_below"]]
        prices = [convert(float(p), src, currency, rate_to_eur) for p in t["threshold_price"]]
        bar = go.Figure(
            go.Bar(
                x=prices, y=labels, orientation="h", marker_color="#3b82f6",
                text=[fmt(p, currency) for p in prices], textposition="outside",
                hovertemplate="%{y}: %{x:,.2f}<extra></extra>",
            )
        )
        bar.add_vline(
            x=current, line=dict(color="#e5e7eb", width=1.5, dash="dash"),
            annotation_text=f"Current {fmt(current, currency)}", annotation_position="top",
        )
        bar.update_layout(
            template="plotly_dark", height=360, margin=dict(l=10, r=50, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=f"Price ({currency})", gridcolor="#1f2a44"),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(bar, use_container_width=True, config={"displayModeBar": False})

with right:
    st.markdown('<p class="panel-title">52-Week Summary</p>', unsafe_allow_html=True)
    rows_html = [
        "<table class='summary'>",
        "<tr><th class='left'>Ticker</th><th class='left'>ETF Name</th>"
        f"<th>52-Week High ({currency})</th><th>52-Week Low ({currency})</th>"
        f"<th>Current ({currency})</th><th>Distance from High</th></tr>",
    ]
    for tk in tickers:
        m = metrics_by_ticker.get(tk)
        if m is None:
            continue
        src = m["native_currency"]
        hi = convert(m["high_52week"], src, currency, rate_to_eur)
        lo = convert(m["low_52week"], src, currency, rate_to_eur)
        cur = convert(m["latest_close"], src, currency, rate_to_eur)
        distance = -float(m["pct_below_52w_high"]) if pd.notna(m["pct_below_52w_high"]) else 0.0
        dcolor = DOWN if distance < 0 else UP
        rows_html.append(
            "<tr>"
            f"<td class='left'><span class='dot' style='background:{COLORS.get(tk)}'></span><b>{tk}</b></td>"
            f"<td class='left'>{m['etf_name']}</td>"
            f"<td>{fmt(hi, currency)}</td><td>{fmt(lo, currency)}</td><td>{fmt(cur, currency)}</td>"
            f"<td style='color:{dcolor}'>{distance:+.2f}%</td>"
            "</tr>"
        )
    rows_html.append("</table>")
    st.markdown("\n".join(rows_html), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("")
fx_note = "" if fx_available else " FX rates table not found in the published data — using rates implied from price history (re-run the pipeline to refresh)."
st.caption(
    f"Values shown in {currency}. Cross-currency figures use EUR as a pivot (latest FX rate). "
    f"Data as of {last_updated:%b %d, %Y}.{fx_note}"
)
