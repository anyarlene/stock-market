#!/usr/bin/env python3
"""
Currency Conversion ETL Script
Converts existing market data prices to EUR using historical exchange rates.
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add analytics to path
sys.path.append(str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from utils.currency_converter import CurrencyConverter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_price_data_for_symbol(db: DatabaseManager, symbol_id: int) -> List[Dict[str, Any]]:
    """Get all price data for a specific symbol."""
    query = """
    SELECT date, open, high, low, close, volume
    FROM etf_data 
    WHERE symbol_id = ? 
    ORDER BY date ASC
    """
    
    try:
        db.connect()
        db.cursor.execute(query, (symbol_id,))
        rows = db.cursor.fetchall()
    finally:
        db.disconnect()
    
    price_data = []
    for row in rows:
        price_record = {
            "date": row[0],
            "open": float(row[1]) if row[1] is not None else None,
            "high": float(row[2]) if row[2] is not None else None,
            "low": float(row[3]) if row[3] is not None else None,
            "close": float(row[4]) if row[4] is not None else None,
            "volume": int(row[5]) if row[5] is not None else None
        }
        price_data.append(price_record)
    
    return price_data

def update_eur_prices(db: DatabaseManager, symbol_id: int, converted_data: List[Dict[str, Any]]):
    """Update the database with EUR converted prices."""
    try:
        db.connect()
        
        for data in converted_data:
            db.cursor.execute("""
                UPDATE etf_data 
                SET open_eur = ?, high_eur = ?, low_eur = ?, close_eur = ?
                WHERE symbol_id = ? AND date = ?
            """, (
                data.get('open_eur'),
                data.get('high_eur'),
                data.get('low_eur'),
                data.get('close_eur'),
                symbol_id,
                data['date']
            ))
        
        db.conn.commit()
        logger.info(f"Updated {len(converted_data)} records for symbol {symbol_id}")
        
    except Exception as e:
        logger.error(f"Error updating EUR prices for symbol {symbol_id}: {e}")
        raise
    finally:
        db.disconnect()

def convert_existing_data_to_eur():
    """Convert all existing market data to EUR."""
    db = DatabaseManager()
    converter = CurrencyConverter()
    
    # First, let's see what's in the database
    try:
        db.connect()
        
        # Check all symbols and their record counts
        db.cursor.execute("""
            SELECT s.id, s.name, s.ticker, s.currency, COUNT(e.id) as record_count
            FROM symbols s
            LEFT JOIN etf_data e ON s.id = e.symbol_id
            WHERE s.is_active = 1
            GROUP BY s.id, s.name, s.ticker, s.currency
            ORDER BY s.id
        """)
        
        symbol_stats = db.cursor.fetchall()
        
        print("📊 Database Analysis:")
        for stat in symbol_stats:
            symbol_id, name, ticker, currency, record_count = stat
            print(f"   Symbol {symbol_id}: {name} ({ticker}) - {currency} - {record_count} records")
        
        # Check EUR conversion status
        db.cursor.execute("""
            SELECT s.id, s.name, s.ticker, s.currency,
                   COUNT(e.id) as total_records,
                   COUNT(e.open_eur) as with_eur_records
            FROM symbols s
            LEFT JOIN etf_data e ON s.id = e.symbol_id
            WHERE s.is_active = 1
            GROUP BY s.id, s.name, s.ticker, s.currency
            ORDER BY s.id
        """)
        
        conversion_stats = db.cursor.fetchall()
        
        print("\n💱 EUR Conversion Status:")
        for stat in conversion_stats:
            symbol_id, name, ticker, currency, total, with_eur = stat
            missing = total - with_eur
            print(f"   {name} ({ticker}): {with_eur}/{total} converted ({missing} missing)")
        
    finally:
        db.disconnect()
    
    # Get all symbols with their currencies
    symbols = db.get_active_symbols()
    
    if not symbols:
        print("⚠️  No symbols found in database")
        return
    
    print(f"\n📊 Processing {len(symbols)} symbols...")
    
    for symbol in symbols:
        symbol_id = symbol['id']
        currency = symbol['currency']
        symbol_name = symbol['name']
        
        print(f"\n💱 Processing {symbol_name} ({symbol['ticker']}) - Currency: {currency}")
        
        if currency == 'EUR':
            print(f"   ℹ️  Already in EUR, setting EUR fields to same values...")
            
            # For EUR symbols, set EUR fields to same values
            try:
                db.connect()
                db.cursor.execute("""
                    UPDATE etf_data 
                    SET open_eur = open, high_eur = high, low_eur = low, close_eur = close
                    WHERE symbol_id = ? AND (open_eur IS NULL OR high_eur IS NULL OR low_eur IS NULL OR close_eur IS NULL)
                """, (symbol_id,))
                
                updated_count = db.cursor.rowcount
                db.conn.commit()
                print(f"   ✅ Updated {updated_count} records")
                
            except Exception as e:
                logger.error(f"Error updating EUR fields for {symbol_name}: {e}")
            finally:
                db.disconnect()
            
            continue
        
        # Get price data that needs EUR conversion
        price_data = get_price_data_for_symbol(db, symbol_id)
        
        print(f"   📊 Found {len(price_data)} price records to process")
        
        if not price_data:
            print(f"   ℹ️  No price data found")
            continue
        
        print(f"   📈 Converting {len(price_data)} price records from {currency} to EUR...")
        
        # Convert to EUR
        try:
            converted_data = converter.convert_price_data_batch(price_data, currency)
            
            # Update database with EUR values
            update_eur_prices(db, symbol_id, converted_data)
            
            print(f"   ✅ Successfully converted {len(converted_data)} records")
            
        except Exception as e:
            print(f"   ❌ Error converting {symbol_name}: {e}")
            logger.error(f"Currency conversion failed for {symbol_name}: {e}")

def verify_conversion():
    """Verify that EUR conversion was successful."""
    db = DatabaseManager()
    
    try:
        db.connect()
        
        # Check how many records have EUR data
        db.cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(open_eur) as with_eur,
                   COUNT(*) - COUNT(open_eur) as without_eur
            FROM etf_data
        """)
        
        result = db.cursor.fetchone()
        total, with_eur, without_eur = result
        
        print(f"\n📊 Conversion Verification:")
        print(f"   Total records: {total}")
        print(f"   With EUR data: {with_eur}")
        print(f"   Without EUR data: {without_eur}")
        
        if without_eur == 0:
            print("   ✅ All records have EUR data!")
        else:
            print(f"   ⚠️  {without_eur} records still missing EUR data")
            
    except Exception as e:
        logger.error(f"Error verifying conversion: {e}")
    finally:
        db.disconnect()

def main():
    """Main function for currency conversion."""
    print("💱 Starting Currency Conversion ETL...")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Add currency rates table if it doesn't exist
        print("\n🔧 Ensuring currency_rates table exists...")
        from database.add_currency_rates_table import add_currency_rates_table
        add_currency_rates_table()
        
        # Convert existing data
        print("\n💱 Converting existing market data to EUR...")
        convert_existing_data_to_eur()
        
        # Verify conversion
        print("\n🔍 Verifying conversion results...")
        verify_conversion()
        
        print(f"\n✅ Currency conversion completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")
        
    except Exception as e:
        print(f"\n❌ Currency conversion failed: {e}")
        raise

if __name__ == "__main__":
    main()
