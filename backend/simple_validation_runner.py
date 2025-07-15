#!/usr/bin/env python3
"""
Simple Validation Runner
========================

Basic validation runner that tests the core validation system without external dependencies.
Demonstrates the validation framework functionality.

Usage:
    python simple_validation_runner.py

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

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_simple_validation():
    """Run simple validation demonstration"""
    
    print("🚀 Simple Production Validation Runner")
    print("="*60)
    
    try:
        # Import and test production validation system
        from production_validation_system import ProductionValidationSystem
        
        print("📊 Initializing Production Validation System...")
        validator = ProductionValidationSystem()
        
        print("🔍 Running comprehensive validation tests...")
        start_time = time.time()
        
        # Run validation
        results = await validator.run_validation()
        
        execution_time = time.time() - start_time
        
        # Print results
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)
        
        summary = results['validation_summary']
        print(f"Validation ID: {summary['validation_id']}")
        print(f"Execution Time: {execution_time:.1f} seconds")
        print(f"Overall Score: {summary['overall_score']:.1f}/100")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Tests Passed: {summary['tests_passed']}/{summary['total_tests']}")
        
        # Print scenario breakdown
        print("\nSCENARIO BREAKDOWN:")
        for scenario in results['detailed_results']['scenarios']:
            status = "✅" if scenario['success_rate'] >= 0.8 else "⚠️" if scenario['success_rate'] >= 0.6 else "❌"
            print(f"  {status} {scenario['name']}: {scenario['success_rate']:.1%}")
        
        # Print recommendations
        if results.get('recommendations'):
            print("\nRECOMMENDATIONS:")
            for rec in results['recommendations']:
                priority_emoji = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
                print(f"  {priority_emoji} [{rec['priority']}] {rec['recommendation']}")
        
        # Production readiness
        print("\nPRODUCTION READINESS:")
        overall_score = summary['overall_score']
        success_rate = summary['success_rate']
        
        if overall_score >= 80 and success_rate >= 0.8:
            print("  🟢 READY FOR PRODUCTION")
        elif overall_score >= 60 and success_rate >= 0.6:
            print("  🟡 NEEDS IMPROVEMENTS")
        else:
            print("  🔴 NOT READY FOR PRODUCTION")
        
        # Save report
        report_file = await validator.save_validation_report()
        print(f"\nDetailed report saved to: {report_file}")
        
        print("="*60)
        print("✅ Simple validation complete!")
        
        return summary['success_rate'] >= 0.8
        
    except Exception as e:
        logger.error(f"Simple validation failed: {str(e)}")
        print(f"❌ Validation failed: {str(e)}")
        return False

async def main():
    """Main execution"""
    success = await run_simple_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)