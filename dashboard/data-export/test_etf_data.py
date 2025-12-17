#!/usr/bin/env python3
"""Test etf_data sync"""

import sqlite3
import psycopg2

sqlite_conn = sqlite3.connect('database/etf_database.db')
pg_conn = psycopg2.connect(host='localhost', port='5432', database='stock_market', user='metabase', password='metabase_password')

sqlite_cur = sqlite_conn.cursor()
pg_cur = pg_conn.cursor()

# Check symbol_id mapping
print("Checking symbol_id mapping...")
sqlite_cur.execute("SELECT DISTINCT symbol_id FROM etf_data LIMIT 5")
sqlite_symbol_ids = [row[0] for row in sqlite_cur.fetchall()]
print(f"SQLite symbol_ids in etf_data: {sqlite_symbol_ids}")

pg_cur.execute("SELECT id FROM symbols")
pg_symbol_ids = [row[0] for row in pg_cur.fetchall()]
print(f"PostgreSQL symbol ids: {pg_symbol_ids}")

# Check if they match
if set(sqlite_symbol_ids).issubset(set(pg_symbol_ids)):
    print("✅ Symbol IDs match!")
else:
    print("❌ Symbol IDs don't match - need to remap")

# Try one insert
sqlite_cur.execute("SELECT id, symbol_id, date, open, high, low, close, volume, open_eur, high_eur, low_eur, close_eur, created_at FROM etf_data WHERE symbol_id IN (SELECT id FROM symbols LIMIT 1) LIMIT 1")
row = sqlite_cur.fetchone()
if row:
    print(f"\nTesting insert with row: symbol_id={row[1]}")
    try:
        query = """
        INSERT INTO etf_data (id, symbol_id, date, open, high, low, close, volume, open_eur, high_eur, low_eur, close_eur, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        ON CONFLICT (symbol_id, date) DO UPDATE SET open=EXCLUDED.open
        """
        pg_cur.execute(query, row)
        pg_conn.commit()
        print("✅ Insert successful!")
    except Exception as e:
        print(f"❌ Error: {e}")

sqlite_conn.close()
pg_conn.close()

