"""
Test Enhanced Workflow Components

This script tests the enhanced workflow components to ensure they work correctly
before implementing automation.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Add the analytics directory to the Python path
analytics_path = Path(__file__).parent
sys.path.append(str(analytics_path))

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("🧪 Testing imports...")
    
    try:
        from database.db_manager import DatabaseManager
        logger.info("✅ DatabaseManager imported successfully")
        
        from etl.enhanced_market_data_fetcher import EnhancedMarketDataFetcher
        logger.info("✅ EnhancedMarketDataFetcher imported successfully")
        
        from enhanced_workflow import EnhancedWorkflowOrchestrator
        logger.info("✅ EnhancedWorkflowOrchestrator imported successfully")
        
        # Test load_symbols import separately
        from database.load_symbols import load_symbols
        logger.info("✅ load_symbols imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_database_connection():
    """Test database connection and initialization."""
    logger.info("🧪 Testing database connection...")
    
    try:
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        db.initialize_database()
        
        # Test getting active symbols
        symbols = db.get_active_symbols()
        logger.info(f"✅ Database connection successful, found {len(symbols)} active symbols")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_enhanced_fetcher():
    """Test the enhanced market data fetcher."""
    logger.info("🧪 Testing enhanced market data fetcher...")
    
    try:
        from etl.enhanced_market_data_fetcher import EnhancedMarketDataFetcher
        
        fetcher = EnhancedMarketDataFetcher()
        
        # Test getting latest data date
        symbols = fetcher.db.get_active_symbols()
        if symbols:
            symbol = symbols[0]
            latest_date = fetcher.get_latest_data_date(symbol['id'])
            logger.info(f"✅ Latest data date for {symbol['name']}: {latest_date}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced fetcher test failed: {e}")
        return False

def test_workflow_orchestrator():
    """Test the workflow orchestrator."""
    logger.info("🧪 Testing workflow orchestrator...")
    
    try:
        from enhanced_workflow import EnhancedWorkflowOrchestrator
        
        orchestrator = EnhancedWorkflowOrchestrator()
        logger.info("✅ Workflow orchestrator initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow orchestrator test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting Enhanced Workflow Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Connection Test", test_database_connection),
        ("Enhanced Fetcher Test", test_enhanced_fetcher),
        ("Workflow Orchestrator Test", test_workflow_orchestrator)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_function in tests:
        logger.info(f"\n🧪 Running {test_name}...")
        if test_function():
            passed += 1
            logger.info(f"✅ {test_name} PASSED")
        else:
            logger.error(f"❌ {test_name} FAILED")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"🎉 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All tests passed! Enhanced workflow is ready for automation.")
        return True
    else:
        logger.error("❌ Some tests failed. Please fix issues before proceeding with automation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
