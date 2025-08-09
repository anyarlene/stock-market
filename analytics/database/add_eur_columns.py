#!/usr/bin/env python3
"""
Script to add EUR columns to existing etf_data table.
"""

import os
import sys
import sqlite3

# Add the analytics directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

def add_eur_columns():
    """Add EUR columns to the existing etf_data table."""
    db_path = "analytics/database/etf_database.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if EUR columns already exist
        cursor.execute("PRAGMA table_info(etf_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("Current columns in etf_data table:")
        for column in columns:
            print(f"  - {column}")
        
        # Add EUR columns if they don't exist
        eur_columns = ['open_eur', 'high_eur', 'low_eur', 'close_eur']
        added_columns = []
        
        for column in eur_columns:
            if column not in columns:
                try:
                    cursor.execute(f"ALTER TABLE etf_data ADD COLUMN {column} DECIMAL(10,2)")
                    added_columns.append(column)
                    print(f"✅ Added column: {column}")
                except sqlite3.Error as e:
                    print(f"❌ Error adding column {column}: {e}")
            else:
                print(f"ℹ️  Column already exists: {column}")
        
        # Commit changes
        conn.commit()
        
        if added_columns:
            print(f"\n🎉 Successfully added {len(added_columns)} EUR columns to the database!")
            print("Added columns:", ", ".join(added_columns))
        else:
            print("\nℹ️  All EUR columns already exist in the database.")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(etf_data)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"\nFinal columns in etf_data table ({len(columns)} total):")
        for column in columns:
            print(f"  - {column}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 Adding EUR columns to existing database...")
    add_eur_columns()
    print("✅ Done!")
