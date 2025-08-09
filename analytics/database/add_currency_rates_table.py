#!/usr/bin/env python3
"""
Script to add currency_rates table to existing database.
"""

import os
import sys
import sqlite3

# Add the analytics directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

def add_currency_rates_table():
    """Add currency_rates table to the existing database."""
    db_path = "analytics/database/etf_database.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create currency_rates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS currency_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate_date DATE NOT NULL,
                exchange_rate DECIMAL(10,6) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_currency, to_currency, rate_date)
            )
        """)
        
        # Create indices for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_currency_rates_date 
            ON currency_rates(rate_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_currency_rates_pair 
            ON currency_rates(from_currency, to_currency)
        """)
        
        # Commit changes
        conn.commit()
        
        print("✅ Successfully created currency_rates table!")
        print("✅ Added performance indices for currency rates")
        
        # Verify the table was created
        cursor.execute("PRAGMA table_info(currency_rates)")
        columns = cursor.fetchall()
        
        print(f"\nCurrency rates table structure ({len(columns)} columns):")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 Adding currency_rates table to database...")
    add_currency_rates_table()
    print("✅ Done!")
