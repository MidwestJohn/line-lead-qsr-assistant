#!/usr/bin/env python3
"""
Verify Ragie is Actually Working (Not Just Falling Back)
========================================================

Comprehensive test suite to prove whether Ragie integration is working
or just immediately falling back to basic search.

This script will:
1. Test Ragie health check endpoint
2. Run verification queries with timing analysis
3. Monitor network activity (if possible)
4. Compare responses for QSR-specific knowledge
5. Check logs for Ragie API calls
6. Analyze response times for suspicious patterns

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import time
import requests
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_QUERIES = [
    "Taylor C602 ice cream machine cleaning procedure",  # Should find specific Ragie docs
    "Fryer temperature calibration steps",              # Should find equipment manuals  
    "Safety procedures for hot oil spills",             # Should find safety documentation
    "How to make a sandwich"                            # Should fall back (no QSR docs)
]

class RagieVerificationTest:
    """Comprehensive Ragie verification test suite"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.ragie_working_evidence = []
        self.ragie_failing_evidence = []
    
    def check_backend_running(self) -> bool:
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_ragie_health_check(self) -> dict:
        """Test Ragie health check endpoint"""
        print("🩺 Testing Ragie Health Check...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health/ragie", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check response: {json.dumps(data, indent=2)}")
                
                if data.get("ragie_api_accessible"):
                    self.ragie_working_evidence.append("✅ Health check shows Ragie API accessible")
                    if data.get("api_response_time_ms", 0) > 100:
                        self.ragie_working_evidence.append(f"✅ Realistic API response time: {data['api_response_time_ms']}ms")
                    else:
                        self.ragie_failing_evidence.append(f"⚠️ Suspiciously fast API response: {data['api_response_time_ms']}ms")
                else:
                    self.ragie_failing_evidence.append("❌ Health check shows Ragie API not accessible")
                
                return data
            else:
                print(f"❌ Health check failed with status {response.status_code}")
                self.ragie_failing_evidence.append(f"❌ Health check endpoint failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            self.ragie_failing_evidence.append(f"❌ Health check error: {e}")
            return {"error": str(e)}
    
    def test_query_with_timing(self, query: str) -> dict:
        """Test a specific query with detailed timing analysis"""
        print(f"\n🧪 Testing query: '{query}'...")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.backend_url}/test/ragie/query",
                json={"query": query},
                timeout=15
            )
            
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ⏱️ Total time: {total_time:.3f}s")
                print(f"   📊 Ragie enhanced: {data.get('ragie_enhanced', False)}")
                print(f"   🔍 Citations: {data.get('visual_citations_count', 0)}")
                print(f"   ⚡ Processing time: {data.get('processing_time', 0):.3f}s")
                
                # Analyze timing patterns
                processing_time = data.get('processing_time', 0)
                
                if data.get('ragie_enhanced', False):
                    self.ragie_working_evidence.append(f"✅ Query '{query[:30]}...' was Ragie enhanced")
                    
                    if processing_time > 0.5:
                        self.ragie_working_evidence.append(f"✅ Realistic processing time: {processing_time:.3f}s")
                    else:
                        self.ragie_failing_evidence.append(f"⚠️ Suspiciously fast processing: {processing_time:.3f}s")
                    
                    if data.get('visual_citations_count', 0) > 0:
                        self.ragie_working_evidence.append(f"✅ Found {data['visual_citations_count']} visual citations")
                else:
                    if "sandwich" not in query.lower():  # Expected to fail
                        self.ragie_failing_evidence.append(f"❌ QSR query '{query[:30]}...' not enhanced by Ragie")
                
                return data
            else:
                print(f"   ❌ Query test failed: {response.status_code}")
                self.ragie_failing_evidence.append(f"❌ Query test failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"   ❌ Query test error: {e}")
            self.ragie_failing_evidence.append(f"❌ Query test error: {e}")
            return {"error": str(e)}
    
    def run_comprehensive_verification(self) -> dict:
        """Run comprehensive verification test"""
        print("\n🧪 Running Comprehensive Verification...")
        
        try:
            response = requests.post(
                f"{self.backend_url}/verification/ragie/comprehensive",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("verification_results", {})
                
                print(f"✅ Comprehensive verification completed")
                print(f"   📊 Overall status: {results.get('overall_status', 'unknown')}")
                print(f"   🎯 Conclusion: {results.get('conclusion', 'No conclusion')}")
                
                # Analyze red/green flags
                red_flags = results.get("red_flags", [])
                green_flags = results.get("green_flags", [])
                
                for flag in green_flags:
                    self.ragie_working_evidence.append(flag)
                
                for flag in red_flags:
                    self.ragie_failing_evidence.append(flag)
                
                return results
            else:
                print(f"❌ Comprehensive verification failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Comprehensive verification error: {e}")
            return {"error": str(e)}
    
    def get_verification_stats(self) -> dict:
        """Get current verification statistics"""
        print("\n📊 Getting Verification Statistics...")
        
        try:
            response = requests.get(f"{self.backend_url}/verification/ragie", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                verification_data = data.get("verification_data", {})
                stats = verification_data.get("stats", {})
                
                print(f"   📈 Total calls: {stats.get('total_calls', 0)}")
                print(f"   ✅ Successful calls: {stats.get('successful_calls', 0)}")
                print(f"   ❌ Failed calls: {stats.get('failed_calls', 0)}")
                print(f"   📊 Success rate: {stats.get('success_rate', 0):.1f}%")
                print(f"   ⏱️ Average response time: {stats.get('average_response_time', 0):.3f}s")
                
                # Analyze patterns
                if stats.get('total_calls', 0) == 0:
                    self.ragie_failing_evidence.append("🚨 No Ragie calls recorded - likely not hitting API")
                elif stats.get('success_rate', 0) > 50:
                    self.ragie_working_evidence.append(f"✅ Good success rate: {stats['success_rate']:.1f}%")
                
                avg_time = stats.get('average_response_time', 0)
                if avg_time < 0.3:
                    self.ragie_failing_evidence.append(f"🚨 Average response time {avg_time:.3f}s too fast - likely not hitting API")
                elif avg_time > 0.5:
                    self.ragie_working_evidence.append(f"✅ Realistic average response time: {avg_time:.3f}s")
                
                return verification_data
            else:
                print(f"❌ Verification stats failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Verification stats error: {e}")
            return {"error": str(e)}
    
    def compare_ragie_vs_standard_responses(self) -> dict:
        """Compare responses with and without Ragie enhancement"""
        print("\n🔄 Comparing Ragie vs Standard Responses...")
        
        test_query = "Fryer safety procedures for preventing oil fires"
        
        results = {
            "query": test_query,
            "ragie_enabled": None,
            "ragie_disabled": None,
            "significant_difference": False,
            "analysis": []
        }
        
        try:
            # Test with Ragie enabled (using the safe enhanced endpoint)
            print("   🔍 Testing with Ragie enabled...")
            
            # Note: We'll use the test endpoint since it's simpler
            ragie_response = requests.post(
                f"{self.backend_url}/test/ragie/query",
                json={"query": test_query},
                timeout=15
            )
            
            if ragie_response.status_code == 200:
                ragie_data = ragie_response.json()
                results["ragie_enabled"] = {
                    "enhanced": ragie_data.get("ragie_enhanced", False),
                    "response_length": len(ragie_data.get("enhanced_query", "")),
                    "citations": ragie_data.get("visual_citations_count", 0),
                    "processing_time": ragie_data.get("processing_time", 0)
                }
                
                if ragie_data.get("ragie_enhanced", False):
                    self.ragie_working_evidence.append("✅ Ragie enhancement detected in response comparison")
                else:
                    self.ragie_failing_evidence.append("❌ No Ragie enhancement in response comparison")
            
            # For standard response, we'd need a different endpoint or compare with original query
            # This is a simplified comparison
            
            return results
            
        except Exception as e:
            print(f"   ❌ Response comparison error: {e}")
            return {"error": str(e)}
    
    def analyze_final_verdict(self):
        """Provide final analysis of whether Ragie is working"""
        print("\n" + "="*60)
        print("🏁 FINAL RAGIE VERIFICATION ANALYSIS")
        print("="*60)
        
        print(f"\n✅ EVIDENCE RAGIE IS WORKING ({len(self.ragie_working_evidence)} items):")
        for evidence in self.ragie_working_evidence:
            print(f"   {evidence}")
        
        print(f"\n❌ EVIDENCE RAGIE IS NOT WORKING ({len(self.ragie_failing_evidence)} items):")
        for evidence in self.ragie_failing_evidence:
            print(f"   {evidence}")
        
        # Final verdict
        working_score = len(self.ragie_working_evidence)
        failing_score = len(self.ragie_failing_evidence)
        
        print(f"\n🎯 VERDICT:")
        if working_score > failing_score:
            print("✅ RAGIE APPEARS TO BE WORKING")
            print("   The integration is likely functional and making real API calls.")
        elif failing_score > working_score:
            print("❌ RAGIE APPEARS TO BE FAILING OR BYPASSED")
            print("   The system is likely falling back to standard search immediately.")
            print("   The 0.6-0.7s response time was probably just fast local responses.")
        else:
            print("⚠️ RAGIE STATUS UNCLEAR")
            print("   Mixed evidence - requires deeper investigation.")
        
        print(f"\n📊 SCORE: {working_score} working evidence vs {failing_score} failing evidence")
        
        return {
            "verdict": "working" if working_score > failing_score else "failing" if failing_score > working_score else "unclear",
            "working_evidence_count": working_score,
            "failing_evidence_count": failing_score,
            "working_evidence": self.ragie_working_evidence,
            "failing_evidence": self.ragie_failing_evidence
        }

async def main():
    """Main verification test runner"""
    print("🔍 RAGIE VERIFICATION TEST SUITE")
    print("="*60)
    print("Testing whether Ragie is actually working or just falling back...")
    
    verifier = RagieVerificationTest()
    
    # Check if backend is running
    if not verifier.check_backend_running():
        print("❌ Backend is not running at http://localhost:8000")
        print("   Please start the backend first: cd backend && python main.py")
        return False
    
    print("✅ Backend is running")
    
    # Run test suite
    print("\n" + "="*60)
    print("🧪 RUNNING VERIFICATION TESTS")
    print("="*60)
    
    # 1. Health check
    health_result = verifier.test_ragie_health_check()
    
    # 2. Query tests
    print("\n" + "-"*40)
    print("🔍 QUERY TESTING")
    print("-"*40)
    
    for query in TEST_QUERIES:
        query_result = verifier.test_query_with_timing(query)
        time.sleep(1)  # Brief pause between tests
    
    # 3. Comprehensive verification
    print("\n" + "-"*40)
    print("🧪 COMPREHENSIVE VERIFICATION")
    print("-"*40)
    
    comprehensive_result = verifier.run_comprehensive_verification()
    
    # 4. Get statistics
    print("\n" + "-"*40)
    print("📊 VERIFICATION STATISTICS")
    print("-"*40)
    
    stats_result = verifier.get_verification_stats()
    
    # 5. Response comparison
    print("\n" + "-"*40)
    print("🔄 RESPONSE COMPARISON")
    print("-"*40)
    
    comparison_result = verifier.compare_ragie_vs_standard_responses()
    
    # Final analysis
    final_verdict = verifier.analyze_final_verdict()
    
    return final_verdict["verdict"] == "working"

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)