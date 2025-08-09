#!/usr/bin/env python3
"""
Database Diagnostic Script
Check what's in the database and why EUR conversion isn't working.
"""

import sys
from pathlib import Path

# Add analytics to path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager

def diagnose_database():
    """Diagnose the database to understand the EUR conversion issue."""
    db = DatabaseManager()
    
    try:
        db.connect()
        
        print("🔍 Database Diagnostic Report")
        print("=" * 50)
        
        # 1. Check all symbols
        print("\n📋 All Symbols in Database:")
        db.cursor.execute("SELECT id, name, ticker, currency, is_active FROM symbols ORDER BY id")
        symbols = db.cursor.fetchall()
        
        for symbol in symbols:
            symbol_id, name, ticker, currency, is_active = symbol
            status = "ACTIVE" if is_active else "INACTIVE"
            print(f"   ID {symbol_id}: {name} ({ticker}) - {currency} - {status}")
        
        # 2. Check record counts by symbol
        print("\n📊 Record Counts by Symbol:")
        db.cursor.execute("""
            SELECT s.id, s.name, s.ticker, s.currency, COUNT(e.id) as record_count
            FROM symbols s
            LEFT JOIN etf_data e ON s.id = e.symbol_id
            GROUP BY s.id, s.name, s.ticker, s.currency
            ORDER BY s.id
        """)
        
        record_counts = db.cursor.fetchall()
        for record in record_counts:
            symbol_id, name, ticker, currency, count = record
            print(f"   {name} ({ticker}): {count} records")
        
        # 3. Check EUR conversion status
        print("\n💱 EUR Conversion Status:")
        db.cursor.execute("""
            SELECT s.id, s.name, s.ticker, s.currency,
                   COUNT(e.id) as total_records,
                   COUNT(e.open_eur) as with_eur_records,
                   COUNT(CASE WHEN e.open_eur IS NULL THEN 1 END) as null_eur_records
            FROM symbols s
            LEFT JOIN etf_data e ON s.id = e.symbol_id
            GROUP BY s.id, s.name, s.ticker, s.currency
            ORDER BY s.id
        """)
        
        conversion_status = db.cursor.fetchall()
        for status in conversion_status:
            symbol_id, name, ticker, currency, total, with_eur, null_eur = status
            print(f"   {name} ({ticker}): {with_eur}/{total} converted, {null_eur} NULL EUR")
        
        # 4. Check for orphaned records
        print("\n🔍 Orphaned Records Check:")
        db.cursor.execute("""
            SELECT COUNT(*) as orphaned_count
            FROM etf_data e
            LEFT JOIN symbols s ON e.symbol_id = s.id
            WHERE s.id IS NULL
        """)
        
        orphaned = db.cursor.fetchone()[0]
        print(f"   Records without valid symbol: {orphaned}")
        
        # 5. Check specific symbol data
        print("\n📈 Sample Data Check:")
        db.cursor.execute("""
            SELECT e.id, e.symbol_id, e.date, e.close, e.close_eur, s.ticker, s.currency
            FROM etf_data e
            JOIN symbols s ON e.symbol_id = s.id
            WHERE e.open_eur IS NULL
            LIMIT 5
        """)
        
        sample_data = db.cursor.fetchall()
        for data in sample_data:
            record_id, symbol_id, date, close, close_eur, ticker, currency = data
            print(f"   Record {record_id}: {ticker} ({currency}) - {date} - Close: {close}, EUR: {close_eur}")
        
        # 6. Check currency rates table
        print("\n💱 Currency Rates Table:")
        db.cursor.execute("SELECT COUNT(*) FROM currency_rates")
        rates_count = db.cursor.fetchone()[0]
        print(f"   Total exchange rates stored: {rates_count}")
        
        if rates_count > 0:
            db.cursor.execute("SELECT from_currency, to_currency, COUNT(*) FROM currency_rates GROUP BY from_currency, to_currency")
            rate_pairs = db.cursor.fetchall()
            for pair in rate_pairs:
                from_curr, to_curr, count = pair
                print(f"   {from_curr}/{to_curr}: {count} rates")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()

if __name__ == "__main__":
    diagnose_database()
