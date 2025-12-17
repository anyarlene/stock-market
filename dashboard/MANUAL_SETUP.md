# Manual Dashboard Setup Guide

This guide helps you create the ETF Dashboard manually in Metabase.

## Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  Header/Title: "ETF Analytics Dashboard"           │
│  (Full width, row 0)                                │
└─────────────────────────────────────────────────────┘
┌──────────────────────────────┬──────────────────────┐
│  ETF Line Chart              │  Fear & Greed Index  │
│  (Top Left, 8 columns)       │  (Top Right, 4 cols) │
│  With ETF filter             │  Gauge Chart        │
└──────────────────────────────┴──────────────────────┘
```

## Step-by-Step Instructions

### 1. Create Dashboard

1. In Metabase, go to **Home**
2. Click **"+ New"** → **"Dashboard"**
3. Name it: **"ETF Dashboard"**
4. Click **"Create"**

### 2. Add Header/Title

1. In the dashboard, click **"+"** → **"Text"**
2. Add this text:
   ```
   # ETF Analytics Dashboard
   
   **Track your ETF performance and market sentiment in real-time**
   ```
3. Position it at the top (full width)
4. Click **"Done"**

### 3. Create ETF Line Chart Question

1. Click **"+ New"** → **"Question"**
2. Select **"Stock Market Dashboard"** database
3. Choose **"Native query"** (SQL)
4. Paste this SQL:
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
   ORDER BY ed.date, s.ticker
   ```
5. Click **"Visualize"**
6. Choose **"Line"** chart type
7. Configure:
   - X-axis: `date`
   - Y-axis: `price_eur`
   - Series: `ticker` (this creates separate lines for each ETF)
8. Click **"Save"** → Name it: **"ETF Performance Over Time"**
9. When prompted, choose **"Add to dashboard"** → Select **"ETF Dashboard"**

### 4. Add ETF Filter

1. In the dashboard (edit mode), click the **filter icon** (funnel) in the top bar
2. Click **"Add a filter"**
3. Choose **"Text or Category"** → **"Dropdown list"**
4. Name it: **"Select ETF"**
5. Click **"Done"**
6. Connect the filter:
   - Click the **"ETF Performance Over Time"** card
   - Click **"Connect filter"**
   - Map **"Select ETF"** to the `ticker` field
7. Configure filter values:
   - Click the filter dropdown
   - Click **"Edit"**
   - Choose **"Custom list"**
   - Add your ETF tickers (e.g., VOO, QQQ, VTI, VUAA.L, CNDX.L)
   - Save

### 5. Create Fear & Greed Index Gauge

1. Click **"+ New"** → **"Question"**
2. Select **"Stock Market Dashboard"** database
3. Choose **"Native query"** (SQL)
4. Paste this SQL:
   ```sql
   SELECT
       value,
       CASE
           WHEN value <= 25 THEN 'EXTREME FEAR'
           WHEN value <= 45 THEN 'FEAR'
           WHEN value <= 55 THEN 'NEUTRAL'
           WHEN value <= 75 THEN 'GREED'
           ELSE 'EXTREME GREED'
       END as classification
   FROM vw_fear_greed_latest
   ```
5. Click **"Visualize"**
6. Choose **"Gauge"** (or "Progress") chart type
7. Configure ranges:
   - Click the gear icon (⚙️) next to "Visualization"
   - Go to **"Ranges"** tab
   - Add 5 ranges:
     - EXTREME FEAR: 0-25
     - FEAR: 25-45
     - NEUTRAL: 45-55
     - GREED: 55-75
     - EXTREME GREED: 75-100
8. Click **"Save"** → Name it: **"Fear & Greed Index"**
9. When prompted, choose **"Add to dashboard"** → Select **"ETF Dashboard"**

### 6. Arrange Layout

1. In dashboard edit mode:
   - Drag the **ETF Line Chart** to top-left (8 columns wide)
   - Drag the **Fear & Greed Gauge** to top-right (4 columns wide)
   - Resize cards as needed
2. Click **"Done"** to save

## Done!

Your dashboard is now ready. The ETF filter will allow users to select which ETFs to display on the line chart.

