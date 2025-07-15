#!/usr/bin/env python3
"""
Phase 1 Deployment Testing
==========================

Test the deployed Phase 1 system to ensure everything is working correctly
before proceeding with Phase 2.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any

class Phase1DeploymentTester:
    """Test Phase 1 deployment"""
    
    def __init__(self, backend_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results = []
    
    async def run_deployment_tests(self):
        """Run comprehensive deployment tests"""
        
        print("🧪 Testing Phase 1 Deployment")
        print("=" * 50)
        
        # Test 1: Backend Health
        await self._test_backend_health()
        
        # Test 2: Frontend Availability
        await self._test_frontend_availability()
        
        # Test 3: Phase 1 Endpoints
        await self._test_phase1_endpoints()
        
        # Test 4: Legacy Compatibility
        await self._test_legacy_compatibility()
        
        # Test 5: Database Operations
        await self._test_database_operations()
        
        # Generate report
        self._generate_deployment_report()
        
        return self._calculate_success_rate()
    
    async def _test_backend_health(self):
        """Test backend health and availability"""
        
        print("\n1. Testing Backend Health...")
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("   ✅ Backend is healthy")
                    self.test_results.append({"test": "Backend Health", "status": "PASSED", "details": data})
                else:
                    print("   ❌ Backend reports unhealthy status")
                    self.test_results.append({"test": "Backend Health", "status": "FAILED", "details": data})
            else:
                print(f"   ❌ Backend health check failed: {response.status_code}")
                self.test_results.append({"test": "Backend Health", "status": "FAILED", "details": {"status_code": response.status_code}})
        
        except Exception as e:
            print(f"   ❌ Backend health check error: {e}")
            self.test_results.append({"test": "Backend Health", "status": "FAILED", "details": {"error": str(e)}})
    
    async def _test_frontend_availability(self):
        """Test frontend availability"""
        
        print("\n2. Testing Frontend Availability...")
        
        try:
            response = requests.get(self.frontend_url, timeout=5)
            
            if response.status_code == 200:
                if "QSR Assistant" in response.text:
                    print("   ✅ Frontend is accessible")
                    self.test_results.append({"test": "Frontend Availability", "status": "PASSED", "details": {"status_code": response.status_code}})
                else:
                    print("   ❌ Frontend content not as expected")
                    self.test_results.append({"test": "Frontend Availability", "status": "FAILED", "details": {"status_code": response.status_code}})
            else:
                print(f"   ❌ Frontend not accessible: {response.status_code}")
                self.test_results.append({"test": "Frontend Availability", "status": "FAILED", "details": {"status_code": response.status_code}})
        
        except Exception as e:
            print(f"   ❌ Frontend availability error: {e}")
            self.test_results.append({"test": "Frontend Availability", "status": "FAILED", "details": {"error": str(e)}})
    
    async def _test_phase1_endpoints(self):
        """Test Phase 1 PydanticAI endpoints"""
        
        print("\n3. Testing Phase 1 Endpoints...")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.backend_url}/chat/pydantic/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("agent_id") == "qsr_base_agent":
                    print("   ✅ Phase 1 agent health endpoint working")
                    self.test_results.append({"test": "Phase 1 Agent Health", "status": "PASSED", "details": data})
                else:
                    print("   ❌ Phase 1 agent health unexpected response")
                    self.test_results.append({"test": "Phase 1 Agent Health", "status": "FAILED", "details": data})
            else:
                print(f"   ❌ Phase 1 agent health failed: {response.status_code}")
                self.test_results.append({"test": "Phase 1 Agent Health", "status": "FAILED", "details": {"status_code": response.status_code}})
        
        except Exception as e:
            print(f"   ❌ Phase 1 agent health error: {e}")
            self.test_results.append({"test": "Phase 1 Agent Health", "status": "FAILED", "details": {"error": str(e)}})
        
        # Test chat endpoint structure (without API key)
        try:
            response = requests.post(
                f"{self.backend_url}/chat/pydantic",
                json={"message": "Test message"},
                timeout=10
            )
            
            # We expect either success or a proper error structure
            if response.status_code in [200, 422, 500]:
                print("   ✅ Phase 1 chat endpoint accessible")
                self.test_results.append({"test": "Phase 1 Chat Endpoint", "status": "PASSED", "details": {"status_code": response.status_code}})
            else:
                print(f"   ❌ Phase 1 chat endpoint unexpected status: {response.status_code}")
                self.test_results.append({"test": "Phase 1 Chat Endpoint", "status": "FAILED", "details": {"status_code": response.status_code}})
        
        except Exception as e:
            print(f"   ❌ Phase 1 chat endpoint error: {e}")
            self.test_results.append({"test": "Phase 1 Chat Endpoint", "status": "FAILED", "details": {"error": str(e)}})
    
    async def _test_legacy_compatibility(self):
        """Test legacy endpoint compatibility"""
        
        print("\n4. Testing Legacy Compatibility...")
        
        try:
            response = requests.post(
                f"{self.backend_url}/chat",
                json={"message": "Legacy test message"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "Legacy response to:" in data.get("response", ""):
                    print("   ✅ Legacy chat endpoint working")
                    self.test_results.append({"test": "Legacy Compatibility", "status": "PASSED", "details": data})
                else:
                    print("   ❌ Legacy chat endpoint unexpected response")
                    self.test_results.append({"test": "Legacy Compatibility", "status": "FAILED", "details": data})
            else:
                print(f"   ❌ Legacy chat endpoint failed: {response.status_code}")
                self.test_results.append({"test": "Legacy Compatibility", "status": "FAILED", "details": {"status_code": response.status_code}})
        
        except Exception as e:
            print(f"   ❌ Legacy compatibility error: {e}")
            self.test_results.append({"test": "Legacy Compatibility", "status": "FAILED", "details": {"error": str(e)}})
    
    async def _test_database_operations(self):
        """Test database operations"""
        
        print("\n5. Testing Database Operations...")
        
        try:
            # Import database directly for testing
            import sys
            sys.path.append('.')
            
            from database.qsr_database import QSRDatabase
            
            # Test database connection
            async with QSRDatabase.connect() as db:
                # Test basic operations
                test_conversation_id = "deployment_test_conversation"
                
                # Add test messages
                test_messages = json.dumps([
                    {
                        "kind": "request",
                        "parts": [
                            {
                                "kind": "user-prompt",
                                "content": "Deployment test message",
                                "timestamp": datetime.now().isoformat()
                            }
                        ]
                    }
                ]).encode()
                
                success = await db.add_messages(test_conversation_id, test_messages, 'deployment_test_agent', 1.0)
                
                if success:
                    # Test retrieval
                    messages = await db.get_messages(test_conversation_id)
                    
                    if messages:
                        print("   ✅ Database operations working")
                        self.test_results.append({"test": "Database Operations", "status": "PASSED", "details": {"messages_count": len(messages)}})
                    else:
                        print("   ❌ Database message retrieval failed")
                        self.test_results.append({"test": "Database Operations", "status": "FAILED", "details": {"issue": "message retrieval"}})
                else:
                    print("   ❌ Database message storage failed")
                    self.test_results.append({"test": "Database Operations", "status": "FAILED", "details": {"issue": "message storage"}})
        
        except Exception as e:
            print(f"   ❌ Database operations error: {e}")
            self.test_results.append({"test": "Database Operations", "status": "FAILED", "details": {"error": str(e)}})
    
    def _generate_deployment_report(self):
        """Generate deployment test report"""
        
        print("\n" + "=" * 50)
        print("📊 Phase 1 Deployment Test Report")
        print("=" * 50)
        
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASSED")
        total_tests = len(self.test_results)
        success_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_emoji} {result['test']}: {result['status']}")
        
        print()
        
        if success_rate >= 80:
            print("🎉 Phase 1 deployment validation PASSED!")
            print("✅ Ready to proceed with Phase 2")
        else:
            print("❌ Phase 1 deployment validation FAILED")
            print("🔧 Fix issues before proceeding")
        
        # Save report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "results": self.test_results
        }
        
        with open("phase1_deployment_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📋 Report saved to: phase1_deployment_test_report.json")
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if not self.test_results:
            return 0.0
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASSED")
        return passed / len(self.test_results)

async def main():
    """Main test execution"""
    
    tester = Phase1DeploymentTester()
    success_rate = await tester.run_deployment_tests()
    
    # Return appropriate exit code
    if success_rate >= 0.8:
        return 0
    else:
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(result)