#!/usr/bin/env python3
"""Test script to debug sync issues"""

import sqlite3
import psycopg2

# Connect to both databases
sqlite_conn = sqlite3.connect('database/etf_database.db')
pg_conn = psycopg2.connect(host='localhost', port='5432', database='stock_market', user='metabase', password='metabase_password')

sqlite_cur = sqlite_conn.cursor()
pg_cur = pg_conn.cursor()

# Get one symbol from SQLite
sqlite_cur.execute('SELECT id, isin, ticker, name, asset_type, exchange, currency, created_at, is_active FROM symbols LIMIT 1')
row = sqlite_cur.fetchone()
print(f'SQLite row: {row}')

# Try to insert into PostgreSQL
try:
    query = """
    INSERT INTO symbols (id, isin, ticker, name, asset_type, exchange, currency, created_at, is_active) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
    ON CONFLICT (id) DO UPDATE SET 
        isin=EXCLUDED.isin, 
        ticker=EXCLUDED.ticker, 
        name=EXCLUDED.name,
        asset_type=EXCLUDED.asset_type,
        exchange=EXCLUDED.exchange,
        currency=EXCLUDED.currency,
        is_active=EXCLUDED.is_active
    """
    pg_cur.execute(query, row)
    pg_conn.commit()
    print('✅ Insert successful!')
except Exception as e:
    print(f'❌ Error: {e}')

sqlite_conn.close()
pg_conn.close()

