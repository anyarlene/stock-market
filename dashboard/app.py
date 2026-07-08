"""
ETF Analytics Dashboard (Streamlit)

Reads the DuckDB warehouse produced by the pipeline (mart_price_history,
mart_52week_metrics, mart_entry_thresholds) and renders the dashboard from
analytics/docs/assets/etf-dashboard-mockup.png.

Data source resolution (first match wins):
  1. $DUCKDB_PATH (if the file exists)
  2. a local warehouse.duckdb in the repo (dev convenience)
  3. the published GitHub Release asset ($WAREHOUSE_URL, tag `latest-data`)
"""

import os
import tempfile
from datetime import datetime

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
    "https://github.com/anyarlene/stock-market/releases/download/latest-data/warehouse.duckdb",
)
DATA_TTL = 6 * 3600  # refresh cached data every 6h (pipeline runs daily)

# Per-ETF display order and accent colors (matches the mockup)
ORDER = ["VOO", "VTI", "QQQ", "VUAA.L", "CNDX.L"]
COLORS = {
    "VOO": "#3b82f6",
    "VTI": "#a855f7",
    "QQQ": "#22d3ee",
    "VUAA.L": "#eab308",
    "CNDX.L": "#ef4444",
}
CURRENCY_SYMBOL = {"USD": "$", "GBP": "£", "EUR": "€"}
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
    candidates = [
        os.path.join(here, "..", "warehouse.duckdb"),
        os.path.join(os.getcwd(), "warehouse.duckdb"),
        "warehouse.duckdb",
    ]
    for cand in candidates:
        if os.path.exists(cand):
            return cand
    return _download_warehouse(RELEASE_URL)


@st.cache_data(ttl=DATA_TTL)
def load_data():
    path = _resolve_db_path()
    con = duckdb.connect(path, read_only=True)
    try:
        price = con.execute("SELECT * FROM mart_price_history").df()
        metrics = con.execute("SELECT * FROM mart_52week_metrics").df()
        thresholds = con.execute("SELECT * FROM mart_entry_thresholds").df()
    finally:
        con.close()
    price["date"] = pd.to_datetime(price["date"])
    return price, metrics, thresholds


def fmt_price(value, currency) -> str:
    sym = CURRENCY_SYMBOL.get(currency, "")
    if value is None or pd.isna(value):
        return "—"
    return f"{sym}{value:,.2f}"


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}
      .app-title {font-size: 1.8rem; font-weight: 800; margin: 0;}
      .app-sub {color: #94a3b8; font-size: 0.95rem; margin-top: -2px;}
      .app-meta {color: #94a3b8; font-size: 0.85rem; text-align: right;}
      .kpi-ticker {font-size: 1.15rem; font-weight: 800;}
      .kpi-name {color: #94a3b8; font-size: 0.8rem; min-height: 2.2em; line-height: 1.1em;}
      .kpi-price {font-size: 1.7rem; font-weight: 800; margin-top: 4px;}
      .kpi-change {font-size: 0.95rem; font-weight: 700;}
      .panel-title {font-size: 1.15rem; font-weight: 700; margin-bottom: 0.4rem;}
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
    price_df, metrics_df, thresholds_df = load_data()
except Exception as exc:  # pragma: no cover - surfaced in the UI
    st.error(
        "Could not load the DuckDB warehouse. Ensure the pipeline has published "
        f"the `latest-data` release or a local `warehouse.duckdb` exists.\n\n{exc}"
    )
    st.stop()

tickers = [t for t in ORDER if t in set(price_df["ticker"])]
metrics_by_ticker = {r["ticker"]: r for _, r in metrics_df.iterrows()}
last_updated = pd.to_datetime(price_df["date"]).max()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
h_left, h_right = st.columns([3, 1])
with h_left:
    st.markdown('<p class="app-title">📈 ETF Analytics Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-sub">Performance overview and entry point analysis</p>', unsafe_allow_html=True)
with h_right:
    st.markdown(
        f'<p class="app-meta">Last updated<br><b>{last_updated:%b %d, %Y}</b></p>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
kpi_cols = st.columns(len(tickers))
for col, tk in zip(kpi_cols, tickers):
    sub = price_df[price_df["ticker"] == tk].sort_values("date")
    last = sub.iloc[-1]
    m = metrics_by_ticker.get(tk, {})
    currency = last["native_currency"]
    change = last["daily_change_pct"]
    up = bool(change is not None and not pd.isna(change) and change >= 0)
    trend_color = UP if up else DOWN
    spark = sub["close"].tail(30).tolist()

    with col:
        with st.container(border=True):
            st.markdown(
                f'<div class="kpi-ticker" style="color:{COLORS.get(tk,"#fff")}">{tk}</div>'
                f'<div class="kpi-name">{m.get("etf_name","")}</div>'
                f'<div class="kpi-price">{fmt_price(last["close"], currency)}</div>'
                f'<div class="kpi-change" style="color:{trend_color}">'
                f'{"▲" if up else "▼"} {change:+.2f}%</div>',
                unsafe_allow_html=True,
            )
            spark_fig = go.Figure(go.Scatter(y=spark, mode="lines", line=dict(color=trend_color, width=2)))
            spark_fig.update_layout(
                height=52,
                margin=dict(l=0, r=0, t=6, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )
            st.plotly_chart(spark_fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Price history (normalized to 100 at the start of the selected range)
# ---------------------------------------------------------------------------
st.markdown("")
ph_left, ph_right = st.columns([2, 3])
with ph_left:
    st.markdown('<p class="panel-title">Price History</p>', unsafe_allow_html=True)
with ph_right:
    selected_range = st.radio(
        "Range", list(RANGE_DAYS.keys()), index=2, horizontal=True, label_visibility="collapsed"
    )

days = RANGE_DAYS[selected_range]
if days is not None:
    cutoff = last_updated - pd.Timedelta(days=days)
    ranged = price_df[price_df["date"] >= cutoff]
else:
    ranged = price_df

fig = go.Figure()
for tk in tickers:
    s = ranged[ranged["ticker"] == tk].sort_values("date")
    if s.empty:
        continue
    base = s["close"].iloc[0]
    indexed = s["close"] / base * 100.0
    fig.add_trace(
        go.Scatter(
            x=s["date"],
            y=indexed,
            mode="lines",
            name=tk,
            line=dict(color=COLORS.get(tk), width=2),
            hovertemplate=f"<b>{tk}</b> %{{x|%b %d, %Y}}<br>%{{y:.1f}}%<extra></extra>",
        )
    )
fig.update_layout(
    template="plotly_dark",
    height=420,
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(title="Indexed to 100 at range start", ticksuffix="%", gridcolor="#1f2a44"),
    xaxis=dict(gridcolor="#131c30"),
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Entry thresholds + 52-week summary
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1])

with left:
    st.markdown('<p class="panel-title">Entry Point Thresholds (Below 52-Week High)</p>', unsafe_allow_html=True)
    sel = st.selectbox("ETF", tickers, index=tickers.index("VOO") if "VOO" in tickers else 0)
    t = thresholds_df[thresholds_df["ticker"] == sel].sort_values("pct_below")
    if t.empty:
        st.info("No threshold data for this ETF.")
    else:
        currency = t["native_currency"].iloc[0]
        current = float(t["latest_close"].iloc[0])
        labels = [f"{int(p)}% Below High" for p in t["pct_below"]]
        prices = t["threshold_price"].astype(float).tolist()
        bar = go.Figure()
        bar.add_trace(
            go.Bar(
                x=prices,
                y=labels,
                orientation="h",
                marker_color="#3b82f6",
                text=[fmt_price(p, currency) for p in prices],
                textposition="outside",
                hovertemplate="%{y}: %{x:.2f}<extra></extra>",
            )
        )
        bar.add_vline(
            x=current,
            line=dict(color="#e5e7eb", width=1.5, dash="dash"),
            annotation_text=f"Current {fmt_price(current, currency)}",
            annotation_position="top",
        )
        bar.update_layout(
            template="plotly_dark",
            height=360,
            margin=dict(l=10, r=40, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=f"Price ({currency})", gridcolor="#1f2a44"),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(bar, use_container_width=True, config={"displayModeBar": False})

with right:
    st.markdown('<p class="panel-title">52-Week Summary</p>', unsafe_allow_html=True)
    rows_html = [
        "<table class='summary'>",
        "<tr><th class='left'>Ticker</th><th class='left'>ETF Name</th>"
        "<th>52-Week High</th><th>52-Week Low</th><th>Current Price</th><th>Distance from High</th></tr>",
    ]
    for tk in tickers:
        m = metrics_by_ticker.get(tk)
        if m is None:
            continue
        cur = m["native_currency"]
        distance = -float(m["pct_below_52w_high"]) if pd.notna(m["pct_below_52w_high"]) else 0.0
        dcolor = DOWN if distance < 0 else UP
        rows_html.append(
            "<tr>"
            f"<td class='left'><span class='dot' style='background:{COLORS.get(tk)}'></span><b>{tk}</b></td>"
            f"<td class='left'>{m['etf_name']}</td>"
            f"<td>{fmt_price(m['high_52week'], cur)}</td>"
            f"<td>{fmt_price(m['low_52week'], cur)}</td>"
            f"<td>{fmt_price(m['latest_close'], cur)}</td>"
            f"<td style='color:{dcolor}'>{distance:+.2f}%</td>"
            "</tr>"
        )
    rows_html.append("</table>")
    st.markdown("\n".join(rows_html), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("")
st.caption(
    "Prices shown in each ETF's native currency. Data built by the automated DuckDB "
    f"pipeline · Data as of {last_updated:%b %d, %Y}"
)
