-- ETF/Stock symbols mapping table
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isin TEXT NOT NULL UNIQUE,
    ticker TEXT NOT NULL,
    name TEXT NOT NULL UNIQUE,  -- Added UNIQUE constraint
    asset_type TEXT NOT NULL CHECK(asset_type IN ('ETF', 'STOCK')),
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- ETF data table to store historical price data
CREATE TABLE IF NOT EXISTS etf_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, date)
);

-- 52-week metrics table
CREATE TABLE IF NOT EXISTS fifty_two_week_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    calculation_date DATE NOT NULL,
    high_52week_price DECIMAL(10,2),
    decrease_10_price DECIMAL(10,2),
    decrease_15_price DECIMAL(10,2),
    decrease_20_price DECIMAL(10,2),
    decrease_25_price DECIMAL(10,2),
    decrease_30_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, calculation_date)
);

-- Create indices for better query performance
CREATE INDEX IF NOT EXISTS idx_etf_data_date ON etf_data(date);
CREATE INDEX IF NOT EXISTS idx_etf_data_symbol ON etf_data(symbol_id);
CREATE INDEX IF NOT EXISTS idx_52week_metrics_date ON fifty_two_week_metrics(calculation_date);
CREATE INDEX IF NOT EXISTS idx_decrease_thresholds_date ON decrease_thresholds(calculation_date);