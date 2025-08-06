"""Validation utilities for ETF analytics."""

import re
from typing import List, Dict, Any, Tuple

def validate_isin(isin: str) -> Tuple[bool, str]:
    """
    Validate ISIN (International Securities Identification Number) format.
    
    ISIN format:
    - 2 letters (country code)
    - 9 characters (alphanumeric)
    - 1 check digit
    
    Args:
        isin: ISIN code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isin:
        return False, "ISIN cannot be empty"
        
    # Basic format check
    isin_pattern = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}\d$')
    if not isin_pattern.match(isin):
        return False, "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 check digit"
    
    # Check country code (IE for Irish ETFs)
    if not isin.startswith('IE'):
        return False, "ISIN must start with 'IE' for Irish ETFs"
    
    return True, ""

def validate_symbol_data(symbol: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate symbol data before database insertion.
    
    Args:
        symbol: Dictionary containing symbol data
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    # Check required fields
    required_fields = ['isin', 'ticker', 'name', 'asset_type', 'exchange', 'currency']
    for field in required_fields:
        if field not in symbol or not symbol[field]:
            errors.append(f"Missing or empty required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate ISIN
    is_valid_isin, isin_error = validate_isin(symbol['isin'])
    if not is_valid_isin:
        errors.append(isin_error)
    
    # Validate asset_type
    valid_asset_types = ['ETF', 'STOCK']
    if symbol['asset_type'] not in valid_asset_types:
        errors.append(f"Invalid asset_type. Must be one of: {valid_asset_types}")
    
    # Validate exchange
    if symbol['exchange'] != 'LSE':
        errors.append("Currently only supporting LSE exchange")
    
    # Validate currency
    valid_currencies = ['USD', 'GBP', 'EUR']
    if symbol['currency'] not in valid_currencies:
        errors.append(f"Invalid currency. Must be one of: {valid_currencies}")
    
    return len(errors) == 0, errors

def verify_data_consistency(csv_data: List[Dict], db_data: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Verify that CSV and database data match.
    
    Args:
        csv_data: List of symbol dictionaries from CSV
        db_data: List of symbol dictionaries from database
        
    Returns:
        Tuple of (is_consistent, list_of_discrepancies)
    """
    discrepancies = []
    
    # Create lookup dictionaries
    csv_lookup = {item['isin']: item for item in csv_data}
    db_lookup = {item['isin']: item for item in db_data}
    
    # Check for missing or extra ISINs
    csv_isins = set(csv_lookup.keys())
    db_isins = set(db_lookup.keys())
    
    missing_in_db = csv_isins - db_isins
    if missing_in_db:
        discrepancies.append(f"ISINs in CSV but not in DB: {missing_in_db}")
    
    extra_in_db = db_isins - csv_isins
    if extra_in_db:
        discrepancies.append(f"ISINs in DB but not in CSV: {extra_in_db}")
    
    # Check for data mismatches
    for isin in csv_isins & db_isins:
        csv_item = csv_lookup[isin]
        db_item = db_lookup[isin]
        
        for field in ['ticker', 'name', 'asset_type', 'exchange', 'currency']:
            if csv_item[field] != db_item[field]:
                discrepancies.append(
                    f"Mismatch for ISIN {isin}, field {field}: "
                    f"CSV='{csv_item[field]}', DB='{db_item[field]}'"
                )
    
    return len(discrepancies) == 0, discrepancies