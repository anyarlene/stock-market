-- Database Views for Metabase Dashboard
-- These views simplify queries and make dashboards easier to build

-- View: ETF Data with Symbol Names
-- Combines etf_data with symbols for easy querying
CREATE OR REPLACE VIEW vw_etf_data_with_symbols AS
SELECT 
    ed.id,
    ed.symbol_id,
    s.ticker,
    s.name,
    s.asset_type,
    s.currency,
    ed.date,
    ed.open,
    ed.high,
    ed.low,
    ed.close,
    ed.volume,
    ed.open_eur,
    ed.high_eur,
    ed.low_eur,
    ed.close_eur,
    ed.created_at
FROM etf_data ed
JOIN symbols s ON ed.symbol_id = s.id
WHERE s.is_active = TRUE;

-- View: Latest ETF Prices
-- Shows the most recent price for each ETF
CREATE OR REPLACE VIEW vw_latest_etf_prices AS
SELECT DISTINCT ON (s.ticker)
    s.ticker,
    s.name,
    s.currency,
    ed.date,
    ed.close AS current_price,
    ed.close_eur AS current_price_eur,
    ed.volume,
    (ed.close - LAG(ed.close) OVER (PARTITION BY s.ticker ORDER BY ed.date)) / LAG(ed.close) OVER (PARTITION BY s.ticker ORDER BY ed.date) * 100 AS daily_change_pct
FROM etf_data ed
JOIN symbols s ON ed.symbol_id = s.id
WHERE s.is_active = TRUE
ORDER BY s.ticker, ed.date DESC;

-- View: 52-Week Metrics with Symbol Info
-- Combines 52-week metrics with symbol details
CREATE OR REPLACE VIEW vw_52week_metrics AS
SELECT 
    m.symbol_id,
    s.ticker,
    s.name,
    s.currency,
    m.calculation_date,
    m.high_52week,
    m.low_52week,
    m.high_date,
    m.low_date,
    (m.high_52week - m.low_52week) / m.low_52week * 100 AS range_pct
FROM fifty_two_week_metrics m
JOIN symbols s ON m.symbol_id = s.id
WHERE s.is_active = TRUE;

-- View: Fear & Greed Index Latest
-- Shows the most recent Fear & Greed Index reading
CREATE OR REPLACE VIEW vw_fear_greed_latest AS
SELECT 
    value,
    classification,
    timestamp,
    created_at
FROM fear_greed_index
ORDER BY timestamp DESC
LIMIT 1;

-- View: Fear & Greed Index Historical (Last 30 Days)
-- Shows Fear & Greed Index for the last 30 days
CREATE OR REPLACE VIEW vw_fear_greed_historical AS
SELECT 
    value,
    classification,
    timestamp,
    created_at
FROM fear_greed_index
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY timestamp DESC;

-- View: S&P 500 Sector Performance
-- Shows current sector performance sorted by change percentage
CREATE OR REPLACE VIEW vw_sp500_sector_performance AS
SELECT 
    sector,
    ticker,
    current_price,
    change_percent,
    market_cap,
    last_updated
FROM sp500_sectors
WHERE last_updated >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY change_percent DESC;

-- View: S&P 500 Top Companies
-- Shows top companies by market cap/weight
CREATE OR REPLACE VIEW vw_sp500_top_companies AS
SELECT 
    symbol,
    name,
    sector,
    current_price,
    change_percent,
    market_cap,
    weight,
    last_updated
FROM sp500_companies
WHERE last_updated >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY weight DESC;

-- View: ETF Holdings Summary
-- Shows holdings grouped by ETF with total percentage
CREATE OR REPLACE VIEW vw_etf_holdings_summary AS
SELECT 
    etf_ticker,
    etf_name,
    COUNT(*) AS total_holdings,
    SUM(percentage) AS total_percentage,
    MAX(last_updated) AS last_updated
FROM etf_holdings
GROUP BY etf_ticker, etf_name;

-- View: ETF Holdings by ETF
-- Shows all holdings for a specific ETF (for pie charts)
CREATE OR REPLACE VIEW vw_etf_holdings_detail AS
SELECT 
    etf_ticker,
    etf_name,
    holding_name,
    percentage,
    last_updated
FROM etf_holdings
WHERE last_updated >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY etf_ticker, percentage DESC;

-- View: ETF Performance Summary
-- Combines latest prices with 52-week metrics
CREATE OR REPLACE VIEW vw_etf_performance_summary AS
SELECT 
    s.ticker,
    s.name,
    s.currency,
    latest.date AS latest_date,
    latest.close AS current_price,
    latest.close_eur AS current_price_eur,
    metrics.high_52week,
    metrics.low_52week,
    metrics.calculation_date,
    (latest.close - metrics.low_52week) / metrics.low_52week * 100 AS gain_from_low_pct,
    (metrics.high_52week - latest.close) / metrics.high_52week * 100 AS decline_from_high_pct
FROM symbols s
LEFT JOIN LATERAL (
    SELECT date, close, close_eur
    FROM etf_data
    WHERE symbol_id = s.id
    ORDER BY date DESC
    LIMIT 1
) latest ON TRUE
LEFT JOIN LATERAL (
    SELECT high_52week, low_52week, calculation_date
    FROM fifty_two_week_metrics
    WHERE symbol_id = s.id
    ORDER BY calculation_date DESC
    LIMIT 1
) metrics ON TRUE
WHERE s.is_active = TRUE;

