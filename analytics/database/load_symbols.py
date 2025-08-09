"""Script to load initial symbol data into the database.

This script represents the Load phase of the ETL process for symbol data.
It loads symbols from a CSV file into the database.
"""

import os
import sys
import pandas as pd
from typing import List, Dict, Any

# Add the analytics directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from utils.validators import validate_symbol_data, verify_data_consistency

def check_duplicates(df: pd.DataFrame) -> List[str]:
    """Check for duplicates in the DataFrame."""
    errors = []
    
    # Check duplicate ISINs
    duplicate_isins = df[df.duplicated(subset=['isin'], keep=False)]
    if not duplicate_isins.empty:
        errors.append(f"Duplicate ISINs found: {duplicate_isins['isin'].tolist()}")
    
    # Check duplicate names
    duplicate_names = df[df.duplicated(subset=['name'], keep=False)]
    if not duplicate_names.empty:
        errors.append(f"Duplicate names found: {duplicate_names['name'].tolist()}")
    
    # Check duplicate tickers
    duplicate_tickers = df[df.duplicated(subset=['ticker'], keep=False)]
    if not duplicate_tickers.empty:
        errors.append(f"Duplicate tickers found: {duplicate_tickers['ticker'].tolist()}")
    
    return errors

def load_symbols(csv_path: str = None) -> None:
    """
    Load symbol data into the database from a CSV file.
    
    Args:
        csv_path: Path to the CSV file. If None, uses default path.
    """
    if csv_path is None:
        # Default path relative to project root
        csv_path = os.path.join('analytics', 'database', 'reference', 'symbols.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Symbols file not found: {csv_path}")
    
    print(f"Loading symbols from: {csv_path}")
    
    # Read and validate CSV data
    try:
        df = pd.read_csv(csv_path)
        required_columns = ['isin', 'ticker', 'name', 'asset_type', 'exchange', 'currency']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Check for duplicates in CSV
        duplicate_errors = check_duplicates(df)
        if duplicate_errors:
            print("\nDuplicate entries found in CSV:")
            for error in duplicate_errors:
                print(f"  - {error}")
            return
        
        # Convert DataFrame to list of dictionaries
        csv_data = df.to_dict('records')
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Validate each symbol before processing
    invalid_symbols = []
    for symbol in csv_data:
        is_valid, errors = validate_symbol_data(symbol)
        if not is_valid:
            invalid_symbols.append((symbol.get('isin', 'Unknown ISIN'), errors))
    
    if invalid_symbols:
        print("\nValidation errors found:")
        for isin, errors in invalid_symbols:
            print(f"\nISIN: {isin}")
            for error in errors:
                print(f"  - {error}")
        return

    db = DatabaseManager()
    
    # Clear existing symbols to prevent duplicates
    try:
        db.clear_symbols()
        print("Cleared existing symbols from database")
    except Exception as e:
        print(f"Error clearing symbols: {e}")
        return
    
    # Process each symbol
    processed_symbols = []
    for symbol in csv_data:
        try:
            # Add new symbol
            symbol_id = db.add_symbol(**symbol)
            print(f"Added {symbol['name']} (ID: {symbol_id})")
            
            # Add to processed list with ID
            symbol['id'] = symbol_id
            processed_symbols.append(symbol)
                
        except Exception as e:
            print(f"Error processing {symbol['name']}: {e}")
    
    # Verify data consistency
    print("\nVerifying data consistency...")
    is_consistent, discrepancies = verify_data_consistency(csv_data, processed_symbols)
    
    if not is_consistent:
        print("\nDiscrepancies found between CSV and database:")
        for discrepancy in discrepancies:
            print(f"  - {discrepancy}")
    else:
        print("Data consistency verified - CSV and database match!")

def main():
    """Main function to handle script execution."""
    try:
        load_symbols()
    except Exception as e:
        print(f"Error during symbol loading: {e}")

if __name__ == "__main__":
    main()