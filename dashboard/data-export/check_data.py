#!/usr/bin/env python3
"""Quick script to check what data exists in SQLite"""

import sqlite3

conn = sqlite3.connect('database/etf_database.db')
cur = conn.cursor()

# Check symbols
cur.execute("SELECT COUNT(*) FROM symbols WHERE asset_type='ETF'")
print(f"ETF symbols in SQLite: {cur.fetchone()[0]}")

cur.execute("SELECT ticker, name FROM symbols WHERE asset_type='ETF' AND is_active=1 LIMIT 10")
etfs = cur.fetchall()
print("\nSample ETF tickers:")
for ticker, name in etfs:
    print(f"  {ticker}: {name}")

# Check etf_data
cur.execute("SELECT COUNT(*) FROM etf_data")
print(f"\nTotal rows in etf_data: {cur.fetchone()[0]}")

cur.execute("""
    SELECT DISTINCT s.ticker 
    FROM etf_data ed 
    JOIN symbols s ON ed.symbol_id = s.id 
    WHERE s.asset_type='ETF' 
    LIMIT 10
""")
tickers_with_data = cur.fetchall()
print("\nTickers with data:")
for (ticker,) in tickers_with_data:
    print(f"  {ticker}")

conn.close()

