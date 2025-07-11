#!/usr/bin/env python3
"""
Real-time Comprehensive Logging Monitor
======================================

Monitor all PDF→Neo4j processing checkpoints in real-time.
Displays comprehensive logging across all 6 checkpoints:

1. FastAPI Upload Endpoint
2. LightRAG Processing  
3. RAG-Anything/Multi-Modal
4. Manual Bridge Trigger
5. Neo4j Operations
6. Error Tracking

Usage: python monitor_comprehensive_logging.py
Then upload a PDF through the UI at http://localhost:3000

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import time
import subprocess
from datetime import datetime
from pathlib import Path

class LogMonitor:
    def __init__(self):
        self.log_files = [
            'backend_comprehensive_logging.log',
            'frontend_comprehensive_logging.log'
        ]
        self.last_positions = {}
        
    def monitor_logs(self):
        """Monitor logs in real-time"""
        print("🔍 COMPREHENSIVE LOGGING MONITOR")
        print("=" * 60)
        print("📋 Monitoring all PDF→Neo4j processing checkpoints:")
        print("   1. ✅ FastAPI Upload Endpoint")
        print("   2. ✅ LightRAG Processing")
        print("   3. ✅ RAG-Anything/Multi-Modal")
        print("   4. ✅ Manual Bridge Trigger")
        print("   5. ✅ Neo4j Operations")
        print("   6. ✅ Error Tracking")
        print()
        print("🚀 Ready to track your PDF upload at http://localhost:3000")
        print("=" * 60)
        print()
        
        while True:
            try:
                for log_file in self.log_files:
                    self.check_log_file(log_file)
                time.sleep(0.5)
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error monitoring logs: {e}")
                time.sleep(1)
    
    def check_log_file(self, log_file):
        """Check log file for new content"""
        log_path = Path(log_file)
        
        if not log_path.exists():
            return
            
        try:
            current_size = log_path.stat().st_size
            last_position = self.last_positions.get(log_file, 0)
            
            if current_size > last_position:
                with open(log_path, 'r') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    
                    if new_content.strip():
                        # Filter for comprehensive logging entries
                        lines = new_content.split('\n')
                        for line in lines:
                            if self.is_comprehensive_log_line(line):
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                print(f"[{timestamp}] {line}")
                
                self.last_positions[log_file] = current_size
                
        except Exception as e:
            pass  # Ignore file access errors
    
    def is_comprehensive_log_line(self, line):
        """Check if line is from comprehensive logging"""
        comprehensive_keywords = [
            # Upload checkpoint
            "📄 File received:",
            "✅ Validation passed:",
            "💾 File saved:",
            "🚀 Processing initiated:",
            
            # LightRAG checkpoint
            "📄 Document insertion started:",
            "✅ Text extraction completed",
            "🔍 Entity extraction progress:",
            "🔗 Relationship extraction:",
            "💾 LightRAG storage written",
            
            # Multi-modal checkpoint
            "🖼️  Multi-modal content detected",
            "🔄 Extraction progress:",
            "📋 Citation generation completed",
            
            # Bridge checkpoint
            "🌉 Bridge script initiated",
            "📊 Data extraction from LightRAG",
            "📦 Batch processing:",
            
            # Neo4j checkpoint
            "🔌 Connection established:",
            "📦 Batch insertion started",
            "💾 Transaction committed",
            "🏁 Completion status:",
            
            # Error tracking
            "💥 ERROR",
            "🔄 RETRY",
            "🛠️  RECOVERY",
            
            # Pipeline stages
            "🚀 STAGE START:",
            "📊 PROGRESS",
            "✅ STAGE COMPLETE:",
            "❌ STAGE COMPLETE:",
            
            # General pipeline
            "pipeline.",
            "upload.received",
            "upload.validation",
            "upload.storage",
            "upload.processing",
            "lightrag.insertion",
            "lightrag.extraction",
            "lightrag.entities",
            "lightrag.relationships",
            "lightrag.storage",
            "multimodal.detection",
            "multimodal.extraction",
            "multimodal.citations",
            "bridge.initiation",
            "bridge.extraction",
            "bridge.batching",
            "neo4j.connection",
            "neo4j.insertion",
            "neo4j.transaction",
            "neo4j.completion",
            "error.tracker"
        ]
        
        return any(keyword in line for keyword in comprehensive_keywords)

if __name__ == "__main__":
    monitor = LogMonitor()
    monitor.monitor_logs()