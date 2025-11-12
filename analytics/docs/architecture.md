# Architecture Overview

## System Architecture

Modular ETL pipeline with separate components for data fetching, currency conversion, and data export.

## ETL Pipeline Flow

```
Database Init → Load Symbols → Fetch Data → Convert Currencies → Export Data
```

## Database Schema

- `symbols` - ETF metadata
- `etf_data` - Historical price data with EUR conversions
- `currency_rates` - Exchange rate cache
- `fifty_two_week_metrics` - Calculated metrics
- `decrease_thresholds` - Entry point calculations

## Key Components

- **enhanced_workflow.py** - Main orchestrator
- **db_manager.py** - Database operations
- **enhanced_market_data_fetcher.py** - Market data fetching with incremental updates
- **currency_converter_etl.py** - Currency conversion
- **data_exporter.py** - Website data export

## Data Flow

1. Market data fetched from Yahoo Finance
2. Prices stored in original currency (USD/GBP)
3. Historical exchange rates fetched and cached
4. Prices converted to EUR using cached rates
5. Data exported to JSON for website consumption

## Performance Optimizations

- Incremental updates (only fetch new data)
- Exchange rate caching (avoid repeated API calls)
- Database indexing for fast queries
- Batch processing for currency conversion
