-- PostgreSQL Schema for Stock Market Dashboard
-- Converted from SQLite schema with PostgreSQL-specific syntax

-- ETF/Stock symbols mapping table
CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    isin TEXT NOT NULL UNIQUE,
    ticker TEXT NOT NULL,
    name TEXT NOT NULL UNIQUE,
    asset_type TEXT NOT NULL CHECK(asset_type IN ('ETF', 'STOCK')),
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Currency exchange rates table for historical rates
CREATE TABLE IF NOT EXISTS currency_rates (
    id SERIAL PRIMARY KEY,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate_date DATE NOT NULL,
    exchange_rate DECIMAL(10,6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency, rate_date)
);

-- ETF data table to store historical price data
CREATE TABLE IF NOT EXISTS etf_data (
    id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    -- EUR conversion fields
    open_eur DECIMAL(10,2),
    high_eur DECIMAL(10,2),
    low_eur DECIMAL(10,2),
    close_eur DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, date)
);

-- 52-week metrics table
CREATE TABLE IF NOT EXISTS fifty_two_week_metrics (
    id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL,
    calculation_date DATE NOT NULL,
    high_52week DECIMAL(10,2),
    low_52week DECIMAL(10,2),
    high_date DATE,
    low_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, calculation_date)
);

-- Decrease thresholds tracking table
CREATE TABLE IF NOT EXISTS decrease_thresholds (
    id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL,
    calculation_date DATE NOT NULL,
    high_52week_price DECIMAL(10,2),
    decrease_5_price DECIMAL(10,2),
    decrease_10_price DECIMAL(10,2),
    decrease_15_price DECIMAL(10,2),
    decrease_20_price DECIMAL(10,2),
    decrease_25_price DECIMAL(10,2),
    decrease_30_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, calculation_date)
);

-- Market Insights Tables (for Fear & Greed Index, S&P 500, ETF Holdings)

-- Fear & Greed Index table
CREATE TABLE IF NOT EXISTS fear_greed_index (
    id SERIAL PRIMARY KEY,
    value INTEGER NOT NULL,
    classification TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(timestamp)
);

-- S&P 500 Sectors table
CREATE TABLE IF NOT EXISTS sp500_sectors (
    id SERIAL PRIMARY KEY,
    sector TEXT NOT NULL,
    ticker TEXT NOT NULL,
    current_price DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    market_cap BIGINT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sector, last_updated)
);

-- S&P 500 Companies table
CREATE TABLE IF NOT EXISTS sp500_companies (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    sector TEXT NOT NULL,
    current_price DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    market_cap BIGINT,
    weight DECIMAL(5,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETF Holdings table
CREATE TABLE IF NOT EXISTS etf_holdings (
    id SERIAL PRIMARY KEY,
    etf_ticker TEXT NOT NULL,
    etf_name TEXT NOT NULL,
    holding_name TEXT NOT NULL,
    percentage DECIMAL(5,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for better query performance
CREATE INDEX IF NOT EXISTS idx_etf_data_date ON etf_data(date);
CREATE INDEX IF NOT EXISTS idx_etf_data_symbol ON etf_data(symbol_id);
CREATE INDEX IF NOT EXISTS idx_currency_rates_date ON currency_rates(rate_date);
CREATE INDEX IF NOT EXISTS idx_currency_rates_pair ON currency_rates(from_currency, to_currency);
CREATE INDEX IF NOT EXISTS idx_52week_metrics_date ON fifty_two_week_metrics(calculation_date);
CREATE INDEX IF NOT EXISTS idx_decrease_thresholds_date ON decrease_thresholds(calculation_date);
CREATE INDEX IF NOT EXISTS idx_fear_greed_timestamp ON fear_greed_index(timestamp);
CREATE INDEX IF NOT EXISTS idx_sp500_sectors_sector ON sp500_sectors(sector);
CREATE INDEX IF NOT EXISTS idx_sp500_companies_symbol ON sp500_companies(symbol);
CREATE INDEX IF NOT EXISTS idx_etf_holdings_ticker ON etf_holdings(etf_ticker);

