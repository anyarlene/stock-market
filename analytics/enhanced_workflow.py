"""
Enhanced Workflow Orchestrator for Automation

This module provides an enhanced workflow that includes:
- Incremental market data updates
- Data validation and quality checks
- Comprehensive error handling and retries
- Detailed logging and monitoring
- Results tracking for automation
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

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

from database.db_manager import DatabaseManager
from database.load_symbols import load_symbols
from etl.enhanced_market_data_fetcher import EnhancedMarketDataFetcher
from etl.currency_converter_etl import main as currency_converter_main
from etl.data_exporter import main as data_exporter_main
from etl.market_insights_fetcher import export_market_insights_data

class EnhancedWorkflowOrchestrator:
    """Enhanced workflow orchestrator with comprehensive error handling."""
    
    def __init__(self):
        """Initialize the enhanced workflow orchestrator."""
        self.db = DatabaseManager()
        self.results = {
            'workflow_start': datetime.now().isoformat(),
            'steps': {},
            'overall_success': False,
            'errors': []
        }
    
    def run_step(self, step_name: str, step_function, *args, **kwargs) -> bool:
        """
        Run a workflow step with error handling and logging.
        
        Args:
            step_name: Name of the step for logging
            step_function: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Starting Step: {step_name}")
        logger.info(f"{'='*60}")
        
        step_start = datetime.now()
        step_success = False
        step_error = None
        
        try:
            # Execute the step
            result = step_function(*args, **kwargs)
            step_success = True
            logger.info(f"✅ Step '{step_name}' completed successfully")
            
        except Exception as e:
            step_error = str(e)
            logger.error(f"❌ Step '{step_name}' failed: {e}")
            self.results['errors'].append(f"{step_name}: {e}")
        
        # Record step results
        step_duration = (datetime.now() - step_start).total_seconds()
        self.results['steps'][step_name] = {
            'start_time': step_start.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': step_duration,
            'success': step_success,
            'error': step_error
        }
        
        return step_success
    
    def initialize_database(self) -> bool:
        """Initialize database and load symbols."""
        try:
            logger.info("🗄️  Initializing database...")
            self.db.initialize_database()
            
            logger.info("📊 Loading symbols...")
            load_symbols()
            
            return True
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def run_market_data_fetch(self) -> bool:
        """Run enhanced market data fetching with incremental updates."""
        try:
            fetcher = EnhancedMarketDataFetcher()
            results = fetcher.run_incremental_update()
            
            # Check if no symbols were found
            if results['total_symbols'] == 0:
                logger.error("❌ No symbols found to process")
                return False
            
            # Check if any symbols failed
            if results['failed'] > 0:
                logger.warning(f"⚠️  {results['failed']} symbols failed to update")
                # Don't fail the entire workflow for partial failures
                return results['successful'] > 0
            
            return True
        except Exception as e:
            logger.error(f"❌ Market data fetch failed: {e}")
            raise
    
    def run_currency_conversion(self) -> bool:
        """Run currency conversion ETL."""
        try:
            logger.info("💱 Running currency conversion...")
            currency_converter_main()
            return True
        except Exception as e:
            logger.error(f"❌ Currency conversion failed: {e}")
            raise
    
    def run_data_export(self) -> bool:
        """Run data export for website."""
        try:
            logger.info("📤 Running data export...")
            data_exporter_main()
            return True
        except Exception as e:
            logger.error(f"❌ Data export failed: {e}")
            raise
    
    def run_market_insights_export(self) -> bool:
        """Run market insights data export for ETF Insights Explorer."""
        try:
            logger.info("📊 Running market insights export...")
            export_market_insights_data()
            return True
        except Exception as e:
            logger.error(f"❌ Market insights export failed: {e}")
            # Don't fail the entire workflow if market insights fail
            logger.warning("⚠️  Continuing workflow despite market insights export failure")
            return True
    
    def run_postgres_sync(self) -> bool:
        """Sync SQLite data to PostgreSQL for Metabase dashboard."""
        try:
            logger.info("🔄 Syncing data to PostgreSQL...")
            # Import here to avoid dependency issues if PostgreSQL is not available
            import sys
            import importlib.util
            from pathlib import Path
            
            # Load module from path (handles hyphenated directory name)
            script_path = Path(__file__).parent.parent / "dashboard" / "data-export" / "sqlite_to_postgres.py"
            if not script_path.exists():
                logger.warning("⚠️  PostgreSQL sync script not found, skipping")
                return True
            
            spec = importlib.util.spec_from_file_location("sqlite_to_postgres", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            sync = module.SQLiteToPostgresSync()
            sync.sync_all_tables()
            return True
        except ImportError as e:
            logger.warning(f"⚠️  PostgreSQL sync skipped (dependency not available): {e}")
            return True  # Don't fail workflow if PostgreSQL sync is not available
        except Exception as e:
            logger.error(f"❌ PostgreSQL sync failed: {e}")
            # Don't fail the entire workflow if PostgreSQL sync fails
            logger.warning("⚠️  Continuing workflow despite PostgreSQL sync failure")
            return True
    
    def run_market_insights_to_db(self) -> bool:
        """Export market insights data to PostgreSQL."""
        try:
            logger.info("📊 Exporting market insights to PostgreSQL...")
            # Import here to avoid dependency issues if PostgreSQL is not available
            import sys
            import importlib.util
            from pathlib import Path
            
            # Load module from path (handles hyphenated directory name)
            script_path = Path(__file__).parent.parent / "dashboard" / "data-export" / "market_insights_to_db.py"
            if not script_path.exists():
                logger.warning("⚠️  Market insights DB export script not found, skipping")
                return True
            
            spec = importlib.util.spec_from_file_location("market_insights_to_db", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            exporter = module.MarketInsightsToDB()
            exporter.export_all()
            return True
        except ImportError as e:
            logger.warning(f"⚠️  Market insights DB export skipped (dependency not available): {e}")
            return True  # Don't fail workflow if PostgreSQL export is not available
        except Exception as e:
            logger.error(f"❌ Market insights DB export failed: {e}")
            # Don't fail the entire workflow if this fails
            logger.warning("⚠️  Continuing workflow despite market insights DB export failure")
            return True
    
    def save_workflow_results(self) -> None:
        """Save workflow results to file."""
        try:
            self.results['workflow_end'] = datetime.now().isoformat()
            self.results['overall_duration'] = (
                datetime.now() - datetime.fromisoformat(self.results['workflow_start'])
            ).total_seconds()
            
            # Determine overall success
            failed_steps = [step for step, data in self.results['steps'].items() 
                          if not data['success']]
            self.results['overall_success'] = len(failed_steps) == 0
            
            # Save to file
            results_file = "analytics/logs/workflow_results.json"
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"📄 Workflow results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save workflow results: {e}")
    
    def print_summary(self) -> None:
        """Print workflow summary."""
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 WORKFLOW SUMMARY")
        logger.info(f"{'='*60}")
        
        total_duration = self.results.get('overall_duration', 0)
        logger.info(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        
        for step_name, step_data in self.results['steps'].items():
            status = "✅ SUCCESS" if step_data['success'] else "❌ FAILED"
            duration = step_data['duration']
            logger.info(f"   {step_name}: {status} ({duration:.2f}s)")
            
            if not step_data['success'] and step_data['error']:
                logger.error(f"      Error: {step_data['error']}")
        
        if self.results['overall_success']:
            logger.info(f"\n🎉 Overall Status: SUCCESS")
        else:
            logger.error(f"\n❌ Overall Status: FAILED")
            logger.error(f"   Failed steps: {len([s for s, d in self.results['steps'].items() if not d['success']])}")
    
    def run_full_workflow(self) -> bool:
        """Run the complete enhanced workflow."""
        logger.info("🚀 Starting Enhanced Workflow Orchestrator")
        logger.info(f"📅 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Step 1: Initialize database
            if not self.run_step("Database Initialization", self.initialize_database):
                return False
            
            # Step 2: Market data fetch (incremental)
            if not self.run_step("Market Data Fetch", self.run_market_data_fetch):
                return False
            
            # Step 3: Currency conversion
            if not self.run_step("Currency Conversion", self.run_currency_conversion):
                return False
            
            # Step 4: Data export
            if not self.run_step("Data Export", self.run_data_export):
                return False
            
            # Step 5: Market insights export (non-blocking)
            self.run_step("Market Insights Export", self.run_market_insights_export)
            
            # Step 6: PostgreSQL sync (non-blocking, for Metabase dashboard)
            self.run_step("PostgreSQL Sync", self.run_postgres_sync)
            
            # Step 7: Market insights to PostgreSQL (non-blocking)
            self.run_step("Market Insights to PostgreSQL", self.run_market_insights_to_db)
            
            # Save results and print summary
            self.save_workflow_results()
            self.print_summary()
            
            return self.results['overall_success']
            
        except Exception as e:
            logger.error(f"❌ Critical workflow error: {e}")
            self.results['errors'].append(f"Critical error: {str(e)}")
            self.save_workflow_results()
            self.print_summary()
            return False
    
    def run_incremental_update(self) -> bool:
        """Run only the incremental market data update."""
        logger.info("🔄 Running Incremental Update Only")
        
        try:
            if not self.run_step("Market Data Fetch", self.run_market_data_fetch):
                return False
            
            self.save_workflow_results()
            self.print_summary()
            
            return self.results['overall_success']
            
        except Exception as e:
            logger.error(f"❌ Critical error in incremental update: {e}")
            self.results['errors'].append(f"Critical error: {str(e)}")
            self.save_workflow_results()
            self.print_summary()
            return False

def main():
    """Main execution function with command line arguments."""
    parser = argparse.ArgumentParser(description='Enhanced Workflow Orchestrator')
    parser.add_argument('--step', choices=['full', 'incremental', 'fetch', 'currency', 'export', 'insights'],
                       default='full', help='Which step(s) to run')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    orchestrator = EnhancedWorkflowOrchestrator()
    
    try:
        if args.step == 'full':
            success = orchestrator.run_full_workflow()
        elif args.step == 'incremental':
            success = orchestrator.run_incremental_update()
        elif args.step == 'fetch':
            success = orchestrator.run_step("Market Data Fetch", orchestrator.run_market_data_fetch)
        elif args.step == 'currency':
            success = orchestrator.run_step("Currency Conversion", orchestrator.run_currency_conversion)
        elif args.step == 'export':
            success = orchestrator.run_step("Data Export", orchestrator.run_data_export)
        elif args.step == 'insights':
            success = orchestrator.run_step("Market Insights Export", orchestrator.run_market_insights_export)
        else:
            logger.error(f"Unknown step: {args.step}")
            sys.exit(1)
        
        if not success:
            logger.error("❌ Workflow failed")
            sys.exit(1)
        else:
            logger.info("✅ Workflow completed successfully")
            
    except KeyboardInterrupt:
        logger.info("⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
