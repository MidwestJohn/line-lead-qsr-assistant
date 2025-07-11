#!/usr/bin/env python3
"""
Start Continuous Pipeline Monitoring
====================================

Launch script for continuous pipeline health monitoring and recovery.
This keeps the QSR processing pipeline reliable and automatically recovers from issues.

Usage:
    python start_monitoring.py          # Start monitoring service
    python start_monitoring.py --check  # Run one-time health check
    python start_monitoring.py --recover # Run immediate recovery

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def start_continuous_monitoring():
    """
    Start continuous monitoring service.
    """
    print("🔄 Starting Line Lead QSR Pipeline Monitoring Service...")
    print("="*60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚡ Monitoring interval: 60 seconds")
    print("🔧 Recovery actions: Enabled")
    print("📊 Health reporting: Enabled")
    print()
    print("Press Ctrl+C to stop monitoring")
    print("="*60)
    
    try:
        from pipeline_recovery_system import PipelineRecoverySystem
        
        # Initialize recovery system with 1-minute heartbeat
        recovery_system = PipelineRecoverySystem(heartbeat_interval=60)
        
        # Start monitoring
        await recovery_system.start_heartbeat_monitoring()
        
    except KeyboardInterrupt:
        print("\n👋 Monitoring service stopped by user")
        logger.info("Monitoring service stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring service error: {e}")
        logger.error(f"Monitoring service error: {e}")

async def run_health_check():
    """
    Run a one-time health check.
    """
    print("🏥 Running One-Time Pipeline Health Check...")
    print("="*50)
    
    try:
        from pipeline_health_monitor import PipelineHealthMonitor
        
        monitor = PipelineHealthMonitor()
        health_report = await monitor.run_health_verification()
        
        # Display simplified results
        print(f"🎯 Health Score: {health_report['health_score']}/100")
        print(f"📊 Overall Status: {health_report['overall_health'].upper()}")
        print()
        
        # Show document status
        print("📄 Document Status:")
        for doc in health_report['documents_status']:
            status_icon = "✅" if doc['actual_status']['graph_ready'] else "🔄"
            print(f"  {status_icon} {doc['filename']}: {doc['actual_status']['entities_extracted']} entities")
        
        # Show key recommendations
        print("\n💡 Key Recommendations:")
        for rec in health_report['recommendations'][:3]:  # Show top 3
            print(f"  • {rec}")
            
        print(f"\n📈 Neo4j Graph: {health_report['neo4j_sync_status']['total_nodes']} nodes, {health_report['neo4j_sync_status']['total_relationships']} relationships")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        logger.error(f"Health check failed: {e}")

async def run_immediate_recovery():
    """
    Run immediate recovery for stuck files.
    """
    print("🔧 Running Immediate Pipeline Recovery...")
    print("="*45)
    
    try:
        from pipeline_recovery_system import run_immediate_recovery
        
        await run_immediate_recovery()
        
        print("\n✅ Recovery operation completed!")
        print("💡 Run health check to verify results:")
        print("   python start_monitoring.py --check")
        
    except Exception as e:
        print(f"❌ Recovery failed: {e}")
        logger.error(f"Recovery failed: {e}")

def main():
    """
    Main entry point with argument parsing.
    """
    parser = argparse.ArgumentParser(
        description="Line Lead QSR Pipeline Monitoring and Recovery System"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Run one-time health check"
    )
    parser.add_argument(
        "--recover", 
        action="store_true", 
        help="Run immediate recovery for stuck files"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds (default: 60)"
    )
    
    args = parser.parse_args()
    
    # Show banner
    print("\n" + "="*70)
    print("🎯 LINE LEAD QSR PIPELINE MONITORING & RECOVERY SYSTEM")
    print("="*70)
    print("🔧 Enterprise-grade pipeline reliability for QSR processing")
    print("📊 Automatic stuck file detection and recovery")
    print("🏥 Continuous health monitoring and reporting")
    print("="*70)
    
    if args.check:
        asyncio.run(run_health_check())
    elif args.recover:
        asyncio.run(run_immediate_recovery())
    else:
        asyncio.run(start_continuous_monitoring())

if __name__ == "__main__":
    main()