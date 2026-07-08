-- DuckDB schema for the ETF analytics warehouse.
-- Numeric price/rate columns use DOUBLE (not DECIMAL) so the Python layer receives
-- native floats, keeping arithmetic (e.g. 52-week threshold math) type-safe.

-- Sequences backing the surrogate primary keys (DuckDB has no SERIAL keyword)
CREATE SEQUENCE IF NOT EXISTS seq_symbols_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_currency_rates_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_etf_data_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_fifty_two_week_metrics_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_decrease_thresholds_id START 1;

-- ETF/Stock symbols mapping table
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_symbols_id'),
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
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_currency_rates_id'),
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate_date DATE NOT NULL,
    exchange_rate DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency, rate_date)
);

-- ETF data table to store historical price data
CREATE TABLE IF NOT EXISTS etf_data (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_etf_data_id'),
    symbol_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    open_eur DOUBLE,
    high_eur DOUBLE,
    low_eur DOUBLE,
    close_eur DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, date)
);

-- 52-week metrics table
CREATE TABLE IF NOT EXISTS fifty_two_week_metrics (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_fifty_two_week_metrics_id'),
    symbol_id INTEGER NOT NULL,
    calculation_date DATE NOT NULL,
    high_52week DOUBLE,
    low_52week DOUBLE,
    high_date DATE,
    low_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, calculation_date)
);

-- Decrease thresholds tracking table
CREATE TABLE IF NOT EXISTS decrease_thresholds (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_decrease_thresholds_id'),
    symbol_id INTEGER NOT NULL,
    calculation_date DATE NOT NULL,
    high_52week_price DOUBLE,
    decrease_5_price DOUBLE,
    decrease_10_price DOUBLE,
    decrease_15_price DOUBLE,
    decrease_20_price DOUBLE,
    decrease_25_price DOUBLE,
    decrease_30_price DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, calculation_date)
);

-- Indices for query performance
CREATE INDEX IF NOT EXISTS idx_etf_data_date ON etf_data(date);
CREATE INDEX IF NOT EXISTS idx_etf_data_symbol ON etf_data(symbol_id);
CREATE INDEX IF NOT EXISTS idx_currency_rates_date ON currency_rates(rate_date);
CREATE INDEX IF NOT EXISTS idx_currency_rates_pair ON currency_rates(from_currency, to_currency);
CREATE INDEX IF NOT EXISTS idx_52week_metrics_date ON fifty_two_week_metrics(calculation_date);
CREATE INDEX IF NOT EXISTS idx_decrease_thresholds_date ON decrease_thresholds(calculation_date);
