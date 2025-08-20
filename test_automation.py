#!/usr/bin/env python3
"""
Test script for the automation
Runs the workflow once to verify everything works
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_automation():
    """Test the automation workflow."""
    try:
        print("🧪 Testing automation workflow...")
        
        # Import and run the workflow
        from analytics.enhanced_workflow import EnhancedWorkflowOrchestrator
        
        orchestrator = EnhancedWorkflowOrchestrator()
        success = orchestrator.run_incremental_update()
        
        if success:
            print("✅ Test completed successfully!")
            print("🚀 Automation is ready to run daily at 10 PM Berlin time")
        else:
            print("❌ Test failed")
            
    except Exception as e:
        print(f"❌ Error in test: {e}")

if __name__ == "__main__":
    test_automation()
