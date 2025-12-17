# Database Views for Metabase Dashboard

## Why Views?

**Yes, we create views for the dashboard.** Here's why:

### Benefits of Views:

1. **Simplified Queries** - Views combine multiple tables, so you don't need complex JOINs in Metabase
2. **Better Performance** - Views can be optimized and cached by PostgreSQL
3. **Cleaner Dashboards** - Easier to build visualizations with pre-joined data
4. **Data Security** - Can control what data is visible through views
5. **Business Logic** - Views can include calculated fields (e.g., percentage changes)

### Example:

**Without View (Complex):**
```sql
SELECT s.ticker, s.name, ed.date, ed.close
FROM etf_data ed
JOIN symbols s ON ed.symbol_id = s.id
WHERE s.is_active = TRUE
ORDER BY ed.date DESC
```

**With View (Simple):**
```sql
SELECT ticker, name, date, close
FROM vw_etf_data_with_symbols
ORDER BY date DESC
```

---

## Available Views

### 1. `vw_etf_data_with_symbols`
**Purpose:** ETF price data with symbol names (no JOIN needed)

**Columns:**
- `ticker`, `name`, `asset_type`, `currency`
- `date`, `open`, `high`, `low`, `close`, `volume`
- `open_eur`, `high_eur`, `low_eur`, `close_eur`

**Use Case:** Time series charts of ETF prices

---

### 2. `vw_latest_etf_prices`
**Purpose:** Most recent price for each ETF

**Columns:**
- `ticker`, `name`, `currency`
- `date`, `current_price`, `current_price_eur`
- `daily_change_pct` (calculated)

**Use Case:** Current price cards, comparison tables

---

### 3. `vw_52week_metrics`
**Purpose:** 52-week high/low metrics with symbol info

**Columns:**
- `ticker`, `name`, `currency`
- `high_52week`, `low_52week`, `high_date`, `low_date`
- `range_pct` (calculated: percentage range)

**Use Case:** 52-week analysis, entry point indicators

---

### 4. `vw_fear_greed_latest`
**Purpose:** Current Fear & Greed Index reading

**Columns:**
- `value` (0-100)
- `classification` (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
- `timestamp`

**Use Case:** Gauge chart, current sentiment display

---

### 5. `vw_fear_greed_historical`
**Purpose:** Fear & Greed Index for last 30 days

**Columns:**
- `value`, `classification`, `timestamp`

**Use Case:** Historical trend line, time series chart

---

### 6. `vw_sp500_sector_performance`
**Purpose:** S&P 500 sector performance (sorted by change %)

**Columns:**
- `sector`, `ticker`, `current_price`
- `change_percent`, `market_cap`
- `last_updated`

**Use Case:** Sector comparison, heatmap, bar chart

---

### 7. `vw_sp500_top_companies`
**Purpose:** Top S&P 500 companies by weight/market cap

**Columns:**
- `symbol`, `name`, `sector`
- `current_price`, `change_percent`, `market_cap`, `weight`
- `last_updated`

**Use Case:** Company rankings, sector breakdown, pie chart

---

### 8. `vw_etf_holdings_summary`
**Purpose:** Summary of holdings per ETF

**Columns:**
- `etf_ticker`, `etf_name`
- `total_holdings` (count)
- `total_percentage` (sum)
- `last_updated`

**Use Case:** ETF overview, holdings count

---

### 9. `vw_etf_holdings_detail`
**Purpose:** All holdings for each ETF (for pie charts)

**Columns:**
- `etf_ticker`, `etf_name`
- `holding_name`, `percentage`
- `last_updated`

**Use Case:** Pie charts, holdings distribution

---

### 10. `vw_etf_performance_summary`
**Purpose:** Combined ETF performance metrics

**Columns:**
- `ticker`, `name`, `currency`
- `current_price`, `current_price_eur`
- `high_52week`, `low_52week`
- `gain_from_low_pct` (calculated)
- `decline_from_high_pct` (calculated)

**Use Case:** Performance dashboard, comparison tables

---

## Using Views in Metabase

1. **Connect to Database** - Metabase automatically discovers views
2. **Select View** - Choose a view as your data source
3. **Build Visualization** - Use Metabase's visual query builder
4. **No SQL Needed** - Views handle the complexity

### Example: Fear & Greed Gauge Chart

1. Create new question
2. Select `vw_fear_greed_latest`
3. Choose "Gauge" visualization
4. Map `value` to gauge (0-100 range)
5. Use `classification` for color coding

---

## View Maintenance

Views are automatically created when you run:
```bash
python dashboard/data-export/init_postgres_db.py
```

Views are recreated each time (using `CREATE OR REPLACE VIEW`), so you can update them without losing data.

---

## Custom Views

You can create additional views by:
1. Editing `dashboard/data-export/dashboard_views.sql`
2. Running `init_postgres_db.py` again
3. Refreshing database schema in Metabase

---

## Performance Tips

- Views don't store data (they're virtual tables)
- PostgreSQL optimizes view queries automatically
- For very large datasets, consider materialized views
- Indexes on underlying tables improve view performance

---

## Summary

**Yes, views are required and recommended** because they:
- ✅ Simplify dashboard creation
- ✅ Improve query performance
- ✅ Make data easier to understand
- ✅ Reduce errors in complex JOINs
- ✅ Provide calculated fields automatically

You'll use these views extensively when building dashboards in Metabase!

