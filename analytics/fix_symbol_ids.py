#!/usr/bin/env python3
"""
Fix Symbol IDs Script
Change symbol IDs from 9,10 to 1,2 for cleaner database.
"""

import sys
from pathlib import Path

# Add analytics to path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager

def fix_symbol_ids():
    """Fix symbol IDs to use 1 and 2 instead of 9 and 10."""
    db = DatabaseManager()
    
    try:
        db.connect()
        
        print("🔧 Fixing symbol IDs...")
        
        # First, let's see current state
        print("\n📊 Current Symbols:")
        db.cursor.execute("SELECT id, name, ticker, currency FROM symbols ORDER BY id")
        symbols = db.cursor.fetchall()
        
        for symbol in symbols:
            symbol_id, name, ticker, currency = symbol
            print(f"   ID {symbol_id}: {name} ({ticker}) - {currency}")
        
        # Check if we have data for these symbols
        print("\n📈 Current Data Distribution:")
        for symbol in symbols:
            symbol_id, name, ticker, currency = symbol
            db.cursor.execute("SELECT COUNT(*) FROM etf_data WHERE symbol_id = ?", (symbol_id,))
            count = db.cursor.fetchone()[0]
            print(f"   Symbol {symbol_id}: {count} records")
        
        # Create new symbols with IDs 1 and 2
        print("\n🔄 Creating new symbols with IDs 1 and 2...")
        
        # First, update the ETF data to use new symbol IDs
        print("   📊 Updating ETF data symbol references...")
        
        # Update VUAA.L data from symbol_id 9 to 1
        db.cursor.execute("UPDATE etf_data SET symbol_id = 1 WHERE symbol_id = 9")
        vuaa_updated = db.cursor.rowcount
        print(f"   ✅ Updated {vuaa_updated} VUAA.L records (9 → 1)")
        
        # Update CNDX.L data from symbol_id 10 to 2
        db.cursor.execute("UPDATE etf_data SET symbol_id = 2 WHERE symbol_id = 10")
        cndx_updated = db.cursor.rowcount
        print(f"   ✅ Updated {cndx_updated} CNDX.L records (10 → 2)")
        
        # Now delete old symbols and create new ones
        db.cursor.execute("DELETE FROM symbols WHERE id IN (9, 10)")
        
        # Insert symbols with new IDs
        db.cursor.execute("""
            INSERT INTO symbols (id, isin, ticker, name, asset_type, exchange, currency, is_active)
            VALUES 
            (1, 'IE00BFMXXD54', 'VUAA.L', 'Vanguard S&P 500 UCITS ETF', 'ETF', 'LSE', 'USD', 1),
            (2, 'IE00B53SZB19', 'CNDX.L', 'iShares NASDAQ 100 UCITS ETF', 'ETF', 'LSE', 'GBP', 1)
        """)
        
        db.conn.commit()
        print("✅ New symbols created with IDs 1 and 2")
        
        # Verify the change
        print("\n📊 Updated Symbols:")
        db.cursor.execute("SELECT id, name, ticker, currency FROM symbols ORDER BY id")
        symbols = db.cursor.fetchall()
        
        for symbol in symbols:
            symbol_id, name, ticker, currency = symbol
            print(f"   ID {symbol_id}: {name} ({ticker}) - {currency}")
        
        # Check data distribution
        print("\n📈 Updated Data Distribution:")
        for symbol in symbols:
            symbol_id, name, ticker, currency = symbol
            db.cursor.execute("SELECT COUNT(*) FROM etf_data WHERE symbol_id = ?", (symbol_id,))
            count = db.cursor.fetchone()[0]
            print(f"   Symbol {symbol_id}: {count} records")
        
        # Check EUR conversion status
        print("\n💱 EUR Conversion Status:")
        db.cursor.execute("""
            SELECT s.id, s.name, s.ticker, s.currency,
                   COUNT(e.id) as total_records,
                   COUNT(e.open_eur) as with_eur_records
            FROM symbols s
            LEFT JOIN etf_data e ON s.id = e.symbol_id
            GROUP BY s.id, s.name, s.ticker, s.currency
            ORDER BY s.id
        """)
        
        conversion_status = db.cursor.fetchall()
        for status in conversion_status:
            symbol_id, name, ticker, currency, total, with_eur = status
            print(f"   {name} ({ticker}): {with_eur}/{total} converted")
        
        print("\n✅ Symbol ID fix completed!")
        
    except Exception as e:
        print(f"❌ Error during symbol ID fix: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()

if __name__ == "__main__":
    fix_symbol_ids()
