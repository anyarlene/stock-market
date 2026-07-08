#!/usr/bin/env python3
"""
ETF Analytics Workflow Orchestrator
Manages the complete ETL pipeline for ETF data processing.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add analytics to path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager

def run_full_workflow():
    """Run the complete ETL workflow."""
    print("🚀 Starting ETF Analytics Workflow...")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Initialize Database
        print("\n📊 Step 1: Initializing database...")
        db = DatabaseManager()
        db.initialize_database()
        print("✅ Database initialized with complete schema (including currency_rates and EUR columns)")
        
        # Step 2: Load Symbols
        print("\n📋 Step 2: Loading ETF symbols...")
        from database.load_symbols import load_symbols
        load_symbols()
        print("✅ Symbols loaded")
        
        # Step 3: Fetch Market Data
        print("\n📈 Step 3: Fetching market data...")
        from etl.market_data_fetcher import main as fetch_market_data
        fetch_market_data()
        print("✅ Market data fetched")
        
        # Step 4: Convert Currencies
        print("\n💱 Step 4: Converting currencies to EUR...")
        from etl.currency_converter_etl import main as convert_currencies
        convert_currencies()
        print("✅ Currencies converted")
        
        # Step 5: Export Data
        print("\n📤 Step 5: Exporting data for website...")
        from etl.data_exporter import main as export_data
        export_data()
        print("✅ Data exported")
        
        print(f"\n🎉 Workflow completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        raise

def run_currency_conversion_only():
    """Run only currency conversion (for testing)."""
    print("💱 Running currency conversion only...")
    try:
        from etl.currency_converter_etl import main as convert_currencies
        convert_currencies()
        print("✅ Currency conversion completed!")
    except Exception as e:
        print(f"❌ Currency conversion failed: {e}")
        raise

def run_data_export_only():
    """Run only data export (for testing)."""
    print("📤 Running data export only...")
    try:
        from etl.data_exporter import main as export_data
        export_data()
        print("✅ Data export completed!")
    except Exception as e:
        print(f"❌ Data export failed: {e}")
        raise

def run_market_data_fetch_only():
    """Run only market data fetching (for testing)."""
    print("📈 Running market data fetch only...")
    try:
        from etl.market_data_fetcher import main as fetch_market_data
        fetch_market_data()
        print("✅ Market data fetch completed!")
    except Exception as e:
        print(f"❌ Market data fetch failed: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ETF Analytics Workflow")
    parser.add_argument("--step", choices=["full", "currency", "export", "fetch"], 
                       default="full", help="Which step to run")
    
    args = parser.parse_args()
    
    if args.step == "full":
        run_full_workflow()
    elif args.step == "currency":
        run_currency_conversion_only()
    elif args.step == "export":
        run_data_export_only()
    elif args.step == "fetch":
        run_market_data_fetch_only()
