#!/usr/bin/env python3
"""
Production Validation Test Runner
================================

Comprehensive test runner for Step 5.2: Production Validation
Executes all validation scenarios and generates detailed reports.

Usage:
    python run_production_validation.py

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('production_validation.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main test execution"""
    print("🚀 Starting Production Validation for PydanticAI + Ragie Integration")
    print("="*80)
    
    try:
        # Import and run validation system
        from production_validation_system import ProductionValidationSystem
        
        # Initialize validation system
        validator = ProductionValidationSystem()
        
        # Run validation
        print("📊 Running comprehensive validation tests...")
        start_time = time.time()
        
        results = await validator.run_validation()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Save detailed report
        report_file = await validator.save_validation_report()
        
        # Print comprehensive summary
        print("\n" + "="*80)
        print("PRODUCTION VALIDATION RESULTS")
        print("="*80)
        
        summary = results['validation_summary']
        print(f"Validation ID: {summary['validation_id']}")
        print(f"Total Duration: {duration:.1f} seconds")
        print(f"Overall Score: {summary['overall_score']:.1f}/100")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print()
        
        print("TEST RESULTS:")
        print(f"  ✅ Passed: {summary['tests_passed']}")
        print(f"  ❌ Failed: {summary['tests_failed']}")
        print(f"  ⚠️  Warnings: {summary['tests_warnings']}")
        print(f"  ⏭️  Skipped: {summary['tests_skipped']}")
        print(f"  📊 Total: {summary['total_tests']}")
        
        # Print scenario breakdown
        print("\nSCENARIO BREAKDOWN:")
        for scenario in results['detailed_results']['scenarios']:
            status_emoji = "✅" if scenario['success_rate'] >= 0.8 else "⚠️" if scenario['success_rate'] >= 0.6 else "❌"
            print(f"  {status_emoji} {scenario['name']}: {scenario['success_rate']:.1%} success ({scenario['overall_score']:.1f}/100)")
        
        # Print recommendations
        if results.get('recommendations'):
            print("\nRECOMMENDATIONS:")
            for rec in results['recommendations']:
                priority_emoji = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
                print(f"  {priority_emoji} [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        
        # Production readiness assessment
        print("\nPRODUCTION READINESS ASSESSMENT:")
        overall_score = summary['overall_score']
        success_rate = summary['success_rate']
        
        if overall_score >= 80 and success_rate >= 0.8:
            print("  🟢 READY FOR PRODUCTION")
            print("  - All critical systems validated")
            print("  - Performance meets requirements")
            print("  - Intelligence services fully integrated")
        elif overall_score >= 60 and success_rate >= 0.6:
            print("  🟡 NEEDS IMPROVEMENTS")
            print("  - Some systems require attention")
            print("  - Address failed tests before production")
            print("  - Consider gradual rollout")
        else:
            print("  🔴 NOT READY FOR PRODUCTION")
            print("  - Critical issues need resolution")
            print("  - Requires significant improvements")
            print("  - Do not deploy to production")
        
        print(f"\nDetailed report saved to: {report_file}")
        print("="*80)
        
        # Return exit code based on results
        if success_rate >= 0.8:
            return 0
        elif success_rate >= 0.6:
            return 1
        else:
            return 2
            
    except Exception as e:
        logger.error(f"Production validation failed: {str(e)}")
        print(f"❌ Production validation failed: {str(e)}")
        return 3

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)