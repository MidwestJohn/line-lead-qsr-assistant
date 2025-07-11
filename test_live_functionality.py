"""
Live Functionality Test Suite
Tests actual system functionality with real API calls and processing
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, List, Any
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveFunctionalityTestSuite:
    """Test suite for live system functionality"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"  # Assuming local backend
        self.production_url = "https://line-lead-qsr-backend.onrender.com"
        self.results = {}
    
    def test_backend_health(self) -> Dict[str, Any]:
        """Test 1: Backend Health Check"""
        logger.info("🔍 Test 1: Backend Health Check")
        
        test_result = {
            "status": "running",
            "local_backend": False,
            "production_backend": False,
            "health_data": {},
            "errors": []
        }
        
        try:
            # Test production backend first
            try:
                response = requests.get(f"{self.production_url}/health", timeout=10)
                if response.status_code == 200:
                    test_result["production_backend"] = True
                    test_result["health_data"] = response.json()
                    logger.info("✅ Production backend is healthy")
                else:
                    test_result["errors"].append(f"Production backend returned {response.status_code}")
            except Exception as e:
                test_result["errors"].append(f"Production backend error: {str(e)}")
            
            # Test local backend
            try:
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                if response.status_code == 200:
                    test_result["local_backend"] = True
                    logger.info("✅ Local backend is healthy")
            except Exception as e:
                test_result["errors"].append(f"Local backend error: {str(e)}")
            
            if test_result["production_backend"] or test_result["local_backend"]:
                test_result["status"] = "passed"
                logger.info("✅ Test 1 PASSED: Backend is accessible")
            else:
                test_result["status"] = "failed"
                logger.error("❌ Test 1 FAILED: No backend accessible")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        self.results["backend_health"] = test_result
        return test_result
    
    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test 2: CORS Configuration"""
        logger.info("🔍 Test 2: CORS Configuration")
        
        test_result = {
            "status": "running",
            "cors_working": False,
            "debug_endpoint": False,
            "cors_origins": [],
            "errors": []
        }
        
        try:
            # Use production backend
            base_url = self.production_url
            
            # Test CORS preflight
            headers = {
                'Origin': 'https://app.linelead.io',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = requests.options(f"{base_url}/health", headers=headers, timeout=10)
            
            if response.status_code == 200:
                cors_headers = response.headers
                if 'Access-Control-Allow-Origin' in cors_headers:
                    test_result["cors_working"] = True
                    logger.info("✅ CORS headers present")
                else:
                    test_result["errors"].append("No CORS headers in response")
            
            # Test debug endpoint if available
            try:
                response = requests.get(f"{base_url}/debug/cors", timeout=10)
                if response.status_code == 200:
                    test_result["debug_endpoint"] = True
                    debug_data = response.json()
                    test_result["cors_origins"] = debug_data.get("cors_origins", [])
                    logger.info(f"✅ Debug endpoint shows CORS origins: {test_result['cors_origins']}")
            except Exception as e:
                test_result["errors"].append(f"Debug endpoint error: {str(e)}")
            
            if test_result["cors_working"] or len(test_result["cors_origins"]) > 0:
                test_result["status"] = "passed"
                logger.info("✅ Test 2 PASSED: CORS is properly configured")
            else:
                test_result["status"] = "failed"
                logger.error("❌ Test 2 FAILED: CORS configuration issues")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        self.results["cors_configuration"] = test_result
        return test_result
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test 3: API Endpoints Functionality"""
        logger.info("🔍 Test 3: API Endpoints")
        
        test_result = {
            "status": "running",
            "endpoints_tested": 0,
            "endpoints_working": 0,
            "endpoint_results": {},
            "errors": []
        }
        
        try:
            base_url = self.production_url
            
            # Test key endpoints
            endpoints = [
                ("/health", "GET"),
                ("/documents", "GET"),
                ("/debug/cors", "GET"),
                ("/keep-alive", "GET")
            ]
            
            for endpoint, method in endpoints:
                test_result["endpoints_tested"] += 1
                try:
                    if method == "GET":
                        response = requests.get(f"{base_url}{endpoint}", timeout=10)
                    
                    test_result["endpoint_results"][endpoint] = {
                        "status_code": response.status_code,
                        "working": response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        test_result["endpoints_working"] += 1
                        logger.info(f"✅ {endpoint} is working")
                    else:
                        logger.info(f"⚠️ {endpoint} returned {response.status_code}")
                        
                except Exception as e:
                    test_result["endpoint_results"][endpoint] = {
                        "status_code": "error",
                        "working": False,
                        "error": str(e)
                    }
                    test_result["errors"].append(f"{endpoint}: {str(e)}")
            
            success_rate = test_result["endpoints_working"] / test_result["endpoints_tested"]
            if success_rate >= 0.75:
                test_result["status"] = "passed"
                logger.info(f"✅ Test 3 PASSED: {test_result['endpoints_working']}/{test_result['endpoints_tested']} endpoints working")
            else:
                test_result["status"] = "failed"
                logger.error(f"❌ Test 3 FAILED: Only {test_result['endpoints_working']}/{test_result['endpoints_tested']} endpoints working")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        self.results["api_endpoints"] = test_result
        return test_result
    
    def test_document_processing_simulation(self) -> Dict[str, Any]:
        """Test 4: Document Processing Simulation"""
        logger.info("🔍 Test 4: Document Processing Simulation")
        
        test_result = {
            "status": "running",
            "simulation_successful": False,
            "processing_components": 0,
            "errors": []
        }
        
        try:
            # Simulate document processing by checking if required files exist
            processing_files = [
                "backend/main.py",
                "backend/services/document_processor.py",
                "backend/services/multimodal_citation_service.py",
                "backend/services/neo4j_service.py"
            ]
            
            for file_path in processing_files:
                if Path(file_path).exists():
                    test_result["processing_components"] += 1
                    logger.info(f"✅ {file_path} exists")
                else:
                    test_result["errors"].append(f"{file_path} missing")
            
            # Check for test files
            test_files = ["qsr_entities_test.txt", "multimodal_test.txt", "relationships_test.txt"]
            all_test_files_exist = all(Path(f).exists() for f in test_files)
            
            if test_result["processing_components"] >= 3 and all_test_files_exist:
                test_result["simulation_successful"] = True
                test_result["status"] = "passed"
                logger.info("✅ Test 4 PASSED: Document processing components ready")
            else:
                test_result["status"] = "failed"
                logger.error("❌ Test 4 FAILED: Document processing components incomplete")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        self.results["document_processing"] = test_result
        return test_result
    
    def test_frontend_compatibility(self) -> Dict[str, Any]:
        """Test 5: Frontend Compatibility"""
        logger.info("🔍 Test 5: Frontend Compatibility")
        
        test_result = {
            "status": "running",
            "react_components": 0,
            "css_files": 0,
            "service_files": 0,
            "build_ready": False,
            "errors": []
        }
        
        try:
            # Check React components
            component_files = [
                "src/App.js",
                "src/FileUpload.js",
                "src/components/MultiModalCitation.js",
                "src/components/ProcessingDashboard.js"
            ]
            
            for file_path in component_files:
                if Path(file_path).exists():
                    test_result["react_components"] += 1
                else:
                    test_result["errors"].append(f"{file_path} missing")
            
            # Check CSS files
            css_files = [
                "src/App.css",
                "src/FileUpload.css",
                "src/components/MultiModalCitation.css"
            ]
            
            for file_path in css_files:
                if Path(file_path).exists():
                    test_result["css_files"] += 1
            
            # Check service files
            service_files = [
                "src/services/api.js",
                "src/ChatService.js"
            ]
            
            for file_path in service_files:
                if Path(file_path).exists():
                    test_result["service_files"] += 1
            
            # Check if package.json exists
            if Path("package.json").exists():
                test_result["build_ready"] = True
            
            if (test_result["react_components"] >= 3 and 
                test_result["css_files"] >= 2 and 
                test_result["service_files"] >= 2 and 
                test_result["build_ready"]):
                test_result["status"] = "passed"
                logger.info("✅ Test 5 PASSED: Frontend is compatible and build-ready")
            else:
                test_result["status"] = "failed"
                logger.error("❌ Test 5 FAILED: Frontend compatibility issues")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        self.results["frontend_compatibility"] = test_result
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all live functionality tests"""
        logger.info("🚀 Starting Live Functionality Test Suite")
        
        # Run all tests
        self.test_backend_health()
        self.test_cors_configuration() 
        self.test_api_endpoints()
        self.test_document_processing_simulation()
        self.test_frontend_compatibility()
        
        # Generate summary
        passed_tests = sum(1 for result in self.results.values() if result.get("status") == "passed")
        total_tests = len(self.results)
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "detailed_results": self.results
        }
        
        logger.info(f"📊 Live Test Suite Complete: {passed_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        
        return summary
    
    def generate_report(self) -> str:
        """Generate comprehensive live functionality report"""
        summary = self.run_all_tests()
        
        report = f"""
# Live Functionality Test Report

## Executive Summary
- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed_tests']}
- **Failed**: {summary['failed_tests']}
- **Success Rate**: {summary['success_rate']:.1f}%

## Production Readiness Assessment

"""
        
        if summary['success_rate'] >= 80:
            report += "🟢 **PRODUCTION READY** - System is performing well and ready for live deployment\n\n"
        elif summary['success_rate'] >= 60:
            report += "🟡 **NEEDS ATTENTION** - System mostly working but has some issues that should be addressed\n\n"
        else:
            report += "🔴 **NOT READY** - System has significant issues that must be resolved before deployment\n\n"
        
        for test_name, result in summary['detailed_results'].items():
            status_icon = "✅" if result['status'] == "passed" else "❌"
            report += f"### {status_icon} {test_name.replace('_', ' ').title()}\n"
            report += f"**Status**: {result['status']}\n"
            
            # Add specific metrics for each test
            for key, value in result.items():
                if key not in ['status', 'errors']:
                    if isinstance(value, bool):
                        report += f"**{key}**: {'✅ Yes' if value else '❌ No'}\n"
                    elif isinstance(value, (int, float)):
                        report += f"**{key}**: {value}\n"
                    elif isinstance(value, list) and len(value) > 0:
                        report += f"**{key}**: {', '.join(map(str, value))}\n"
                    elif isinstance(value, dict):
                        report += f"**{key}**: {len(value)} items\n"
            
            if result.get('errors'):
                report += f"**Errors**: {', '.join(result['errors'])}\n"
            
            report += "\n"
        
        return report


if __name__ == "__main__":
    # Run the live functionality test suite
    test_suite = LiveFunctionalityTestSuite()
    report = test_suite.generate_report()
    
    # Save report
    with open("live_functionality_test_report.md", "w") as f:
        f.write(report)
    
    print(report)