#!/usr/bin/env python3
"""
End-to-End Test with Real-Time Monitoring
Tests complete pipeline: PDF upload → LightRAG → Neo4j
With comprehensive real-time monitoring and validation
"""

import asyncio
import time
import json
import os
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Enhanced logging
from enhanced_logging import (
    pipeline_logger, 
    upload_logger, 
    lightrag_logger,
    multimodal_logger,
    bridge_logger
)

class E2ETestMonitor:
    """End-to-end test with real-time monitoring."""
    
    def __init__(self):
        self.test_start_time = None
        self.test_results = {}
        self.monitoring_active = False
        self.api_base_url = "http://localhost:8000"
        self.neo4j_browser_url = "http://localhost:7474"
        self.logger = logging.getLogger('E2ETest')
        
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger.info("🔧 SETTING UP TEST ENVIRONMENT")
        
        # Verify services are running
        services_status = await self.check_services_status()
        
        if not all(services_status.values()):
            self.logger.error("❌ Not all services are running")
            for service, status in services_status.items():
                status_icon = "✅" if status else "❌"
                self.logger.error(f"   {service}: {status_icon}")
            return False
        
        self.logger.info("✅ All services are running")
        return True
        
    async def check_services_status(self) -> Dict[str, bool]:
        """Check if all required services are running."""
        services = {
            'FastAPI Backend': await self.check_fastapi_status(),
            'Neo4j Database': await self.check_neo4j_status(),
            'Frontend (optional)': await self.check_frontend_status()
        }
        
        return services
        
    async def check_fastapi_status(self) -> bool:
        """Check FastAPI backend status."""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"FastAPI check failed: {e}")
            return False
            
    async def check_neo4j_status(self) -> bool:
        """Check Neo4j database status."""
        try:
            from services.neo4j_service import neo4j_service
            if not neo4j_service.connected:
                neo4j_service.connect()
            
            result = neo4j_service.execute_query("RETURN 1 as test")
            return result.get('success', False)
        except Exception as e:
            self.logger.error(f"Neo4j check failed: {e}")
            return False
            
    async def check_frontend_status(self) -> bool:
        """Check frontend status (optional)."""
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Frontend check failed (optional): {e}")
            return False
            
    def start_real_time_monitoring(self):
        """Start real-time monitoring in separate thread."""
        self.monitoring_active = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
    def _monitor_loop(self):
        """Real-time monitoring loop."""
        self.logger.info("👁️  REAL-TIME MONITORING STARTED")
        
        while self.monitoring_active:
            try:
                # Monitor Neo4j statistics
                neo4j_stats = self._get_neo4j_stats()
                if neo4j_stats:
                    self.logger.info(f"📊 Neo4j: {neo4j_stats['total_nodes']} nodes, {neo4j_stats['total_relationships']} relationships")
                
                # Monitor log file size
                log_file_size = self._get_log_file_size()
                if log_file_size:
                    self.logger.info(f"📝 Log file: {log_file_size:,} bytes")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                
    def _get_neo4j_stats(self) -> Optional[Dict[str, Any]]:
        """Get current Neo4j statistics."""
        try:
            from services.neo4j_service import neo4j_service
            result = neo4j_service.execute_query("""
                MATCH (n) 
                OPTIONAL MATCH ()-[r]->() 
                RETURN count(DISTINCT n) as nodes, count(r) as relationships
            """)
            
            if result.get('success') and result.get('records'):
                record = result['records'][0]
                return {
                    'total_nodes': record.get('nodes', 0),
                    'total_relationships': record.get('relationships', 0)
                }
        except Exception as e:
            self.logger.debug(f"Neo4j stats error: {e}")
        return None
        
    def _get_log_file_size(self) -> Optional[int]:
        """Get current log file size."""
        try:
            if os.path.exists("pipeline_diagnostic.log"):
                return os.path.getsize("pipeline_diagnostic.log")
        except Exception as e:
            self.logger.debug(f"Log file size error: {e}")
        return None
        
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        self.logger.info("👁️  REAL-TIME MONITORING STOPPED")
        
    async def prepare_test_document(self) -> str:
        """Prepare test document for upload."""
        self.logger.info("📄 PREPARING TEST DOCUMENT")
        
        # Create a test QSR manual PDF simulation
        test_content = """
        Taylor C602 Soft Serve Ice Cream Machine
        Service Manual - Model C602-27
        
        EQUIPMENT OVERVIEW:
        The Taylor C602 is a commercial soft serve ice cream machine designed for high-volume operations.
        
        SPECIFICATIONS:
        - Model: C602-27
        - Serial Number: TYL-2024-001
        - Capacity: 27 quarts/hour
        - Power: 7.5 kW, 208-240V, 3-phase
        - Weight: 485 lbs
        - Refrigerant: R-404A
        
        MAJOR COMPONENTS:
        1. Compressor Assembly (C602-COMP-001)
        2. Evaporator Coils (C602-EVAP-001)
        3. Mixing Chamber (C602-MIX-001)
        4. Control Panel (C602-CTRL-001)
        5. Dispensing System (C602-DISP-001)
        
        DAILY PROCEDURES:
        Step 1: Visual inspection
        Step 2: Temperature check
        Step 3: Clean dispensing area
        Step 4: Check refrigerant levels
        
        SAFETY PROTOCOLS:
        - Lockout/Tagout required
        - PPE must be worn
        - Emergency stop accessible
        """
        
        test_file = "test_taylor_c602_manual.txt"
        with open(test_file, 'w') as f:
            f.write(test_content)
            
        self.logger.info(f"✅ Test document created: {test_file}")
        return test_file
        
    async def upload_test_document(self, file_path: str) -> Dict[str, Any]:
        """Upload test document via API."""
        self.logger.info(f"📤 UPLOADING TEST DOCUMENT: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path, f, 'text/plain')}
                
                # Start timer
                upload_start = time.time()
                
                # Upload via API
                response = requests.post(
                    f"{self.api_base_url}/api/upload-document",
                    files=files,
                    timeout=300  # 5 minute timeout
                )
                
                upload_duration = time.time() - upload_start
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"✅ UPLOAD SUCCESSFUL in {upload_duration:.2f}s")
                    return {
                        'success': True,
                        'duration': upload_duration,
                        'response': result
                    }
                else:
                    self.logger.error(f"❌ UPLOAD FAILED: {response.status_code}")
                    return {
                        'success': False,
                        'duration': upload_duration,
                        'error': response.text
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ UPLOAD ERROR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def verify_neo4j_data(self, expected_min_entities: int = 10) -> Dict[str, Any]:
        """Verify data appears in Neo4j."""
        self.logger.info("🔍 VERIFYING NEO4J DATA")
        
        try:
            from services.neo4j_service import neo4j_service
            
            # Get final statistics
            stats_result = neo4j_service.execute_query("""
                MATCH (n) 
                OPTIONAL MATCH ()-[r]->() 
                RETURN count(DISTINCT n) as nodes, count(r) as relationships
            """)
            
            if stats_result.get('success') and stats_result.get('records'):
                record = stats_result['records'][0]
                nodes = record.get('nodes', 0)
                relationships = record.get('relationships', 0)
                
                self.logger.info(f"📊 Neo4j contains: {nodes} nodes, {relationships} relationships")
                
                # Check if we have minimum expected entities
                success = nodes >= expected_min_entities
                
                if success:
                    self.logger.info(f"✅ NEO4J VERIFICATION PASSED")
                else:
                    self.logger.error(f"❌ NEO4J VERIFICATION FAILED: {nodes} < {expected_min_entities}")
                
                return {
                    'success': success,
                    'nodes': nodes,
                    'relationships': relationships,
                    'meets_minimum': success
                }
            else:
                self.logger.error("❌ Failed to query Neo4j statistics")
                return {'success': False, 'error': 'Query failed'}
                
        except Exception as e:
            self.logger.error(f"❌ NEO4J VERIFICATION ERROR: {e}")
            return {'success': False, 'error': str(e)}
            
    async def test_neo4j_browser_access(self) -> bool:
        """Test if Neo4j browser is accessible."""
        self.logger.info("🌐 TESTING NEO4J BROWSER ACCESS")
        
        try:
            response = requests.get(self.neo4j_browser_url, timeout=10)
            success = response.status_code == 200
            
            if success:
                self.logger.info(f"✅ NEO4J BROWSER ACCESSIBLE: {self.neo4j_browser_url}")
            else:
                self.logger.error(f"❌ NEO4J BROWSER NOT ACCESSIBLE: {response.status_code}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ NEO4J BROWSER ERROR: {e}")
            return False
            
    async def run_complete_e2e_test(self):
        """Run complete end-to-end test."""
        self.test_start_time = time.time()
        
        self.logger.info("🧪 STARTING END-TO-END TEST")
        self.logger.info("=" * 70)
        
        # Start monitoring
        self.start_real_time_monitoring()
        
        try:
            # Phase 1: Setup
            self.logger.info("🔧 PHASE 1: ENVIRONMENT SETUP")
            setup_success = await self.setup_test_environment()
            if not setup_success:
                self.logger.error("❌ Environment setup failed")
                return False
            
            # Phase 2: Document preparation
            self.logger.info("📄 PHASE 2: DOCUMENT PREPARATION")
            test_file = await self.prepare_test_document()
            
            # Phase 3: Upload and processing
            self.logger.info("📤 PHASE 3: UPLOAD AND PROCESSING")
            upload_result = await self.upload_test_document(test_file)
            
            if not upload_result['success']:
                self.logger.error("❌ Upload failed")
                return False
            
            # Phase 4: Wait and verify
            self.logger.info("⏳ PHASE 4: WAITING FOR PROCESSING")
            await asyncio.sleep(30)  # Wait 30 seconds for processing
            
            # Phase 5: Verification
            self.logger.info("🔍 PHASE 5: VERIFICATION")
            verification_result = await self.verify_neo4j_data(expected_min_entities=10)
            
            if not verification_result['success']:
                self.logger.error("❌ Verification failed")
                return False
            
            # Phase 6: Browser access test
            self.logger.info("🌐 PHASE 6: BROWSER ACCESS TEST")
            browser_success = await self.test_neo4j_browser_access()
            
            # Calculate total test time
            total_time = time.time() - self.test_start_time
            
            # Final results
            self.test_results = {
                'test_duration': total_time,
                'upload_result': upload_result,
                'verification_result': verification_result,
                'browser_accessible': browser_success,
                'overall_success': all([
                    upload_result['success'],
                    verification_result['success'],
                    browser_success
                ])
            }
            
            self.logger.info("=" * 70)
            if self.test_results['overall_success']:
                self.logger.info("🎉 END-TO-END TEST PASSED!")
                self.logger.info(f"✅ Total time: {total_time:.2f} seconds")
                self.logger.info(f"✅ Entities created: {verification_result['nodes']}")
                self.logger.info(f"✅ Relationships created: {verification_result['relationships']}")
                self.logger.info(f"✅ Neo4j browser accessible: {browser_success}")
            else:
                self.logger.error("❌ END-TO-END TEST FAILED")
                self.logger.error("Check individual phase results above")
            
            return self.test_results['overall_success']
            
        except Exception as e:
            self.logger.error(f"❌ E2E TEST ERROR: {e}")
            return False
            
        finally:
            # Stop monitoring
            self.stop_monitoring()
            
            # Save test results
            self.save_test_results()
            
    def save_test_results(self):
        """Save test results to file."""
        results_file = f"e2e_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            self.logger.info(f"📊 Test results saved to {results_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save test results: {e}")

async def main():
    """Main test function."""
    print("🧪 MEMEX END-TO-END TEST")
    print("=" * 50)
    print("This will test the complete pipeline:")
    print("1. PDF upload via API")
    print("2. LightRAG processing")
    print("3. Entity extraction")
    print("4. Neo4j bridge")
    print("5. Data verification")
    print("6. Browser access")
    print("=" * 50)
    
    # Confirm test
    confirm = input("Ready to run end-to-end test? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Test cancelled")
        return False
    
    # Run test
    monitor = E2ETestMonitor()
    success = await monitor.run_complete_e2e_test()
    
    if success:
        print("\n🎉 END-TO-END TEST PASSED!")
        print("✅ Complete pipeline working correctly")
        print("✅ Ready for production use")
    else:
        print("\n❌ END-TO-END TEST FAILED")
        print("⚠️  Check logs for specific errors")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🚀 SYSTEM READY FOR PRODUCTION!")
    else:
        print("\n⚠️  SYSTEM NEEDS FIXES BEFORE PRODUCTION")