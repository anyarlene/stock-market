#!/usr/bin/env python3
"""
Cleanup Orphaned Records Script
Remove records that don't belong to valid symbols.
"""

import sys
from pathlib import Path

# Add analytics to path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager

def cleanup_orphaned_records():
    """Remove orphaned records from the database."""
    db = DatabaseManager()
    
    try:
        db.connect()
        
        print("🧹 Cleaning up orphaned records...")
        
        # First, let's see what orphaned records we have
        db.cursor.execute("""
            SELECT e.symbol_id, COUNT(*) as record_count
            FROM etf_data e
            LEFT JOIN symbols s ON e.symbol_id = s.id
            WHERE s.id IS NULL
            GROUP BY e.symbol_id
            ORDER BY e.symbol_id
        """)
        
        orphaned_groups = db.cursor.fetchall()
        
        print(f"📊 Found {len(orphaned_groups)} orphaned symbol IDs:")
        total_orphaned = 0
        for symbol_id, count in orphaned_groups:
            print(f"   Symbol ID {symbol_id}: {count} records")
            total_orphaned += count
        
        if total_orphaned == 0:
            print("✅ No orphaned records found!")
            return
        
        # Delete orphaned records
        print(f"\n🗑️  Deleting {total_orphaned} orphaned records...")
        
        db.cursor.execute("""
            DELETE FROM etf_data 
            WHERE symbol_id NOT IN (SELECT id FROM symbols WHERE is_active = 1)
        """)
        
        deleted_count = db.cursor.rowcount
        db.conn.commit()
        
        print(f"✅ Deleted {deleted_count} orphaned records")
        
        # Verify cleanup
        db.cursor.execute("""
            SELECT COUNT(*) as remaining_orphaned
            FROM etf_data e
            LEFT JOIN symbols s ON e.symbol_id = s.id
            WHERE s.id IS NULL
        """)
        
        remaining = db.cursor.fetchone()[0]
        print(f"📊 Remaining orphaned records: {remaining}")
        
        if remaining == 0:
            print("✅ All orphaned records cleaned up!")
        else:
            print(f"⚠️  {remaining} orphaned records still remain")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()

if __name__ == "__main__":
    cleanup_orphaned_records()
