# Fix: Cannot Select X-Axis and Y-Axis in Metabase

## Problem
When creating a line chart, the X-axis and Y-axis fields show "No valid fields" and you can't select columns.

## Cause
The SQL query can't run because a required parameter (`{{ticker_filter}}`) doesn't have a default value. Metabase needs to run the query first to detect available columns.

## Solution

### Option 1: Set a Default Value (Recommended)

1. **In the Filter Widget Settings (right panel):**
   - Find **"Default filter widget value"**
   - Enter one of your ETF tickers (e.g., `VOO`)
   - This allows the query to run immediately

2. **Run the Query:**
   - Click **"Run query"** or press Ctrl+Enter
   - The query should execute successfully

3. **Now Select Axes:**
   - Go to **"Display"** or **"Axes"** tab
   - X-axis: Select `date`
   - Y-axis: Select `price_eur`
   - Series (optional): Select `ticker` if you want multiple lines

### Option 2: Make Filter Optional

Change your SQL to make the filter optional:

```sql
SELECT 
    ed.date,
    s.ticker,
    s.name,
    ed.close_eur as price_eur
FROM vw_etf_data_with_symbols ed
JOIN symbols s ON ed.symbol_id = s.id
WHERE s.asset_type = 'ETF' 
    AND s.is_active = TRUE
    AND ({{ticker_filter}} IS NULL OR s.ticker = {{ticker_filter}})
ORDER BY ed.date ASC
```

Then in filter settings:
- Uncheck **"Always require a value"**
- Leave default value empty
- The query will run showing all ETFs, then filter when a value is selected

### Option 3: Use Different SQL First

1. **Start with SQL without filter:**
   ```sql
   SELECT 
       ed.date,
       s.ticker,
       s.name,
       ed.close_eur as price_eur
   FROM vw_etf_data_with_symbols ed
   JOIN symbols s ON ed.symbol_id = s.id
   WHERE s.asset_type = 'ETF' 
       AND s.is_active = TRUE
   ORDER BY ed.date ASC
   LIMIT 1000
   ```

2. **Run query and configure chart:**
   - Select X-axis: `date`
   - Select Y-axis: `price_eur`
   - Series: `ticker`

3. **Then add the filter:**
   - Go back to SQL
   - Add `AND s.ticker = {{ticker_filter}}`
   - Configure the filter variable
   - Set a default value

## Quick Fix Steps

1. **Set Default Value:**
   - Right panel → "Default filter widget value"
   - Enter: `VOO` (or any valid ETF ticker)

2. **Run Query:**
   - Click "Run query"
   - Should see data now

3. **Select Axes:**
   - Go to "Display" or "Axes" tab
   - X-axis: `date`
   - Y-axis: `price_eur`

4. **Visualize:**
   - Click "Visualize"
   - Choose "Line" chart

## Why This Happens

Metabase needs to execute the SQL query to:
- Detect column names and types
- Populate the axis dropdowns
- Preview the data

If the query can't run (due to missing parameters), Metabase can't determine what columns are available, so the axis fields remain empty.

## After Fixing

Once you set a default value and the query runs:
- ✅ X-axis dropdown will show: `date`, `ticker`, `name`, `price_eur`
- ✅ Y-axis dropdown will show: `date`, `ticker`, `name`, `price_eur`
- ✅ You can select `date` for X-axis and `price_eur` for Y-axis
- ✅ Chart will display correctly

