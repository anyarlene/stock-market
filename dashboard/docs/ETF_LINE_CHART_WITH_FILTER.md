# How to Build ETF Line Chart with Filter in Metabase

## Step-by-Step Guide

### Step 1: Create the Question (Chart)

1. **Open Metabase** → Click **"+ New"** → **"Question"**

2. **Select Data Source:**
   - Choose **"Stock Market Dashboard"** (your PostgreSQL database)
   - Select **"Native query"** (SQL editor)

3. **Write the SQL Query:**
   
   Paste this SQL:
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
       AND s.ticker = {{ticker_filter}}
   ORDER BY ed.date ASC
   ```
   
   **Important:** The `{{ticker_filter}}` is a Metabase variable that will become your filter.

4. **Configure the Variable:**
   - After pasting the SQL, Metabase will detect `{{ticker_filter}}`
   - Click on the variable box that appears (or the "Ticker Filter" dropdown in the top right)
   - Set:
     - **Variable type:** "Text"
     - **Variable name:** "ticker_filter"
     - **Display name:** "Select ETF"
     - **Widget type:** "Dropdown list"
     - **How should users filter on this column?:** "Dropdown list"
   
5. **Set Filter Options:**
   - Click **"Edit"** next to "Dropdown list"
   - Choose **"Custom list"**
   - Add your ETF tickers (one per line):
     ```
     VOO
     QQQ
     VTI
     VUAA.L
     CNDX.L
     ```
   - Click **"Done"**
   
6. **Set Default Value (IMPORTANT!):**
   - In the "Default filter widget value" field, enter one of your ETF tickers (e.g., `VOO`)
   - This allows the query to run and detect columns
   - OR check **"Always require a value"** and set a default

7. **Run the Query:**
   - Click **"Run query"** (or press Ctrl+Enter)
   - The query should now run successfully
   - Verify you see data

7. **Visualize:**
   - Click **"Visualize"**
   - Metabase will suggest a line chart (if not, select it manually)

8. **Configure the Chart:**
   - **X-axis:** `date`
   - **Y-axis:** `price_eur`
   - **Series:** Leave empty (or use `ticker` if you want multiple lines)
   - **Chart title:** "ETF Price Over Time"

9. **Save the Question:**
   - Click **"Save"** (top right)
   - Name it: **"ETF Performance Over Time"**
   - Choose a collection (e.g., "Your personal collection")
   - Click **"Save"**

---

### Step 2: Add to Dashboard

1. **Open your dashboard** (or create a new one)

2. **Add the Question:**
   - Click **"+"** → **"Saved questions"**
   - Find **"ETF Performance Over Time"**
   - Click it to add

3. **Position the Chart:**
   - Drag it to the desired position (e.g., top-left)
   - Resize as needed

---

### Step 3: Add Dashboard Filter (Alternative Method)

If you want the filter to appear at the dashboard level (affects multiple charts):

1. **In Dashboard Edit Mode:**
   - Click the **filter icon** (funnel) in the top bar
   - Click **"Add a filter"**

2. **Configure Filter:**
   - Choose **"Text or Category"** → **"Dropdown list"**
   - Name it: **"Select ETF"**
   - Click **"Done"**

3. **Set Filter Values:**
   - Click the filter dropdown
   - Click **"Edit"**
   - Choose **"Custom list"**
   - Add your ETF tickers:
     ```
     VOO
     QQQ
     VTI
     VUAA.L
     CNDX.L
     ```
   - Save

4. **Connect Filter to Chart:**
   - Click the **"ETF Performance Over Time"** card
   - Click **"Connect filter"**
   - Map **"Select ETF"** to the `ticker_filter` variable
   - Click **"Done"**

---

## Alternative: Show Multiple ETFs on Same Chart

If you want to show multiple ETFs on the same chart (with legend):

### SQL Query (No Filter):
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
    AND s.ticker IN ({{ticker_filter}})
ORDER BY ed.date ASC, s.ticker
```

### Variable Configuration:
- **Variable type:** "Text"
- **Widget type:** "Dropdown list"
- **Allow multiple values:** ✅ **Check this box**
- **Filter options:** Custom list with all ETF tickers

### Chart Configuration:
- **X-axis:** `date`
- **Y-axis:** `price_eur`
- **Series:** `ticker` (this creates separate lines for each selected ETF)

This way, users can select multiple ETFs and see them all on the same chart with different colored lines.

---

## Quick Reference

### SQL Template:
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
    AND s.ticker = {{ticker_filter}}  -- Single selection
    -- OR: AND s.ticker IN ({{ticker_filter}})  -- Multiple selection
ORDER BY ed.date ASC
```

### Filter Options:
- **Single ETF:** Use `ticker = {{ticker_filter}}`
- **Multiple ETFs:** Use `ticker IN ({{ticker_filter}})` and enable "Allow multiple values"

---

## Troubleshooting

### No data showing?
- Check if ETFs exist in database: Run `SELECT DISTINCT ticker FROM symbols WHERE asset_type='ETF'`
- Verify the view exists: `SELECT * FROM vw_etf_data_with_symbols LIMIT 10`

### Filter not working?
- Make sure variable name matches: `{{ticker_filter}}` in SQL
- Check filter is connected to the chart in dashboard
- Verify filter values match actual ticker values in database

### Chart not displaying correctly?
- Ensure `date` is recognized as date type
- Check `price_eur` is numeric
- Try switching between "Line" and "Area" chart types

---

## Example: Complete Setup

1. **Create question** with SQL above
2. **Add variable** `{{ticker_filter}}` with dropdown
3. **Visualize** as line chart
4. **Save** question
5. **Add to dashboard**
6. **Add dashboard filter** (optional, for dashboard-level filtering)
7. **Connect filter** to chart variable
8. **Done!**

Users can now select an ETF from the dropdown and see its price history on the line chart!

