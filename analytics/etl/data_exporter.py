#!/usr/bin/env python3
"""
Data Export Script for Website
Exports ETF data from SQLite database to JSON files for the frontend.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3

from analytics.database.db_manager import DatabaseManager


def export_etf_data_to_json(db: DatabaseManager, months: int = 3) -> None:
    """
    Export ETF data to JSON files for the website.
    
    Args:
        db: DatabaseManager instance
        months: Number of months of data to export (default: 3)
    """
    # Create website data directory if it doesn't exist
    data_dir = "website/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Get all symbols
    symbols = db.get_active_symbols()
    
    # Calculate date range (last N months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)  # Approximate months to days
    
    exported_data = {}
    
    for symbol in symbols:
        symbol_id = symbol['id']
        symbol_name = symbol['name']
        symbol_ticker = symbol['ticker']
        
        print(f"Exporting data for {symbol_name} ({symbol_ticker})...")
        
        # Get price data for the last N months
        price_data = get_price_data_for_period(db, symbol_id, start_date, end_date)
        
        # Get 52-week metrics
        metrics = get_52week_metrics(db, symbol_id)
        
        # Get decrease thresholds
        thresholds = get_decrease_thresholds(db, symbol_id)
        
        # Format data for Chart.js
        chart_data = {
            "symbol": {
                "id": symbol_id,
                "name": symbol_name,
                "ticker": symbol_ticker,
                "isin": symbol['isin']
            },
            "priceData": price_data,
            "metrics": metrics,
            "thresholds": thresholds,
            "lastUpdated": datetime.now().isoformat()
        }
        
        exported_data[symbol_ticker] = chart_data
        
        # Export individual symbol file
        symbol_file = os.path.join(data_dir, f"{symbol_ticker.lower()}.json")
        with open(symbol_file, 'w') as f:
            json.dump(chart_data, f, indent=2)
    
    # Export combined data file
    combined_file = os.path.join(data_dir, "etf_data.json")
    with open(combined_file, 'w') as f:
        json.dump(exported_data, f, indent=2)
    
    # Export symbols list for the frontend dropdown
    symbols_list = [
        {
            "ticker": symbol['ticker'],
            "name": symbol['name'],
            "isin": symbol['isin']
        }
        for symbol in symbols
    ]
    
    symbols_file = os.path.join(data_dir, "symbols.json")
    with open(symbols_file, 'w') as f:
        json.dump(symbols_list, f, indent=2)
    
    print(f"✅ Data export completed! Files created in {data_dir}/")
    print(f"   - etf_data.json (combined data)")
    print(f"   - symbols.json (symbols list)")
    for symbol in symbols:
        print(f"   - {symbol['ticker'].lower()}.json")


def get_price_data_for_period(db: DatabaseManager, symbol_id: int, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get price data for a specific period."""
    query = """
    SELECT date, open, high, low, close, volume
    FROM etf_data 
    WHERE symbol_id = ? AND date >= ? AND date <= ?
    ORDER BY date ASC
    """
    
    try:
        db.connect()
        db.cursor.execute(query, (symbol_id, start_date.date(), end_date.date()))
        rows = db.cursor.fetchall()
    finally:
        db.disconnect()
    
    price_data = []
    for row in rows:
        price_data.append({
            "date": row[0],
            "open": float(row[1]) if row[1] is not None else None,
            "high": float(row[2]) if row[2] is not None else None,
            "low": float(row[3]) if row[3] is not None else None,
            "close": float(row[4]) if row[4] is not None else None,
            "volume": int(row[5]) if row[5] is not None else None
        })
    
    return price_data


def get_52week_metrics(db: DatabaseManager, symbol_id: int) -> Dict:
    """Get 52-week high/low metrics."""
    query = """
    SELECT high_52week, low_52week, high_date, low_date, calculation_date
    FROM fifty_two_week_metrics 
    WHERE symbol_id = ?
    ORDER BY calculation_date DESC
    LIMIT 1
    """
    
    try:
        db.connect()
        db.cursor.execute(query, (symbol_id,))
        row = db.cursor.fetchone()
    finally:
        db.disconnect()
    
    if row:
        return {
            "high52week": float(row[0]) if row[0] is not None else None,
            "low52week": float(row[1]) if row[1] is not None else None,
            "highDate": row[2],
            "lowDate": row[3],
            "calculationDate": row[4]
        }
    else:
        return {}


def get_decrease_thresholds(db: DatabaseManager, symbol_id: int) -> List[Dict]:
    """Get decrease threshold data."""
    query = """
    SELECT calculation_date, high_52week_price, 
           decrease_10_price, decrease_15_price, decrease_20_price, 
           decrease_25_price, decrease_30_price
    FROM decrease_thresholds 
    WHERE symbol_id = ?
    ORDER BY calculation_date DESC
    LIMIT 1
    """
    
    try:
        db.connect()
        db.cursor.execute(query, (symbol_id,))
        row = db.cursor.fetchone()
    finally:
        db.disconnect()
    
    thresholds = []
    if row:
        calculation_date = row[0]
        high_52week_price = row[1]
        decreases = [
            (10, row[2]),
            (15, row[3]),
            (20, row[4]),
            (25, row[5]),
            (30, row[6])
        ]
        
        for percentage, threshold_price in decreases:
            thresholds.append({
                "percentage": percentage,
                "thresholdPrice": float(threshold_price) if threshold_price is not None else None,
                "calculationDate": calculation_date
            })
    
    return thresholds


def main():
    """Main function to export data."""
    print("Starting data export for website...")
    
    db = DatabaseManager()
    
    try:
        export_etf_data_to_json(db, months=3)
        print("✅ Data export completed successfully!")
    except Exception as e:
        print(f"❌ Error during data export: {e}")
        raise


if __name__ == "__main__":
    main()