#!/usr/bin/env python3
"""
Phase 1 Document Source Integration Test
========================================

Comprehensive test of the Ragie document source integration
following BaseChat patterns.

Tests:
- Document source API integration
- Metadata retrieval
- Caching functionality
- Error handling
- Multiple file types (text, image, etc.)

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import requests
import time
import json
from typing import Dict, Any, List

class DocumentSourceTester:
    """Test suite for document source integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log test result"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
    
    def test_service_health(self) -> bool:
        """Test document source service health"""
        try:
            response = requests.get(f"{self.base_url}/api/documents/source/health")
            
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get("status") == "healthy" and health_data.get("service_available"):
                    self.log_test(
                        "Service Health",
                        True,
                        "Document source service is healthy",
                        health_data
                    )
                    return True
                else:
                    self.log_test(
                        "Service Health",
                        False,
                        "Service not healthy",
                        health_data
                    )
                    return False
            else:
                self.log_test(
                    "Service Health",
                    False,
                    f"Health check failed with status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Service Health",
                False,
                f"Health check error: {e}",
                {"error": str(e)}
            )
            return False
    
    def get_test_document_ids(self) -> List[str]:
        """Get available document IDs for testing"""
        # Known document IDs from previous uploads
        test_ids = [
            "76f50b46-f9c9-4926-a16a-4723087775a1",  # Text file
            "cefc0e1b-dcb6-41ca-bcbd-b787bacc8d0f",  # Image file
            "fc5dbc1a-0de4-4bba-afd9-0cbf9141bafc",  # Another file
        ]
        
        return test_ids
    
    def test_document_source_retrieval(self, document_id: str) -> bool:
        """Test document source retrieval"""
        try:
            response = requests.get(f"{self.base_url}/api/documents/{document_id}/source")
            
            if response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get("Content-Type", "unknown")
                
                self.log_test(
                    f"Source Retrieval ({document_id[:8]}...)",
                    True,
                    f"Retrieved {content_length} bytes, type: {content_type}",
                    {
                        "document_id": document_id,
                        "content_length": content_length,
                        "content_type": content_type
                    }
                )
                return True
            else:
                self.log_test(
                    f"Source Retrieval ({document_id[:8]}...)",
                    False,
                    f"Failed with status {response.status_code}",
                    {
                        "document_id": document_id,
                        "status_code": response.status_code,
                        "response": response.text
                    }
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"Source Retrieval ({document_id[:8]}...)",
                False,
                f"Error: {e}",
                {"document_id": document_id, "error": str(e)}
            )
            return False
    
    def test_document_metadata(self, document_id: str) -> bool:
        """Test document metadata retrieval"""
        try:
            response = requests.get(f"{self.base_url}/api/documents/{document_id}/metadata")
            
            if response.status_code == 200:
                metadata = response.json()
                
                required_fields = ["document_id", "name", "content_type", "size", "created_at"]
                missing_fields = [field for field in required_fields if field not in metadata]
                
                if not missing_fields:
                    self.log_test(
                        f"Metadata Retrieval ({document_id[:8]}...)",
                        True,
                        f"Retrieved metadata for {metadata.get('name', 'unknown')}",
                        metadata
                    )
                    return True
                else:
                    self.log_test(
                        f"Metadata Retrieval ({document_id[:8]}...)",
                        False,
                        f"Missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "metadata": metadata}
                    )
                    return False
            else:
                self.log_test(
                    f"Metadata Retrieval ({document_id[:8]}...)",
                    False,
                    f"Failed with status {response.status_code}",
                    {"document_id": document_id, "status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"Metadata Retrieval ({document_id[:8]}...)",
                False,
                f"Error: {e}",
                {"document_id": document_id, "error": str(e)}
            )
            return False
    
    def test_caching_functionality(self, document_id: str) -> bool:
        """Test caching functionality"""
        try:
            # First request should fetch from Ragie
            start_time = time.time()
            response1 = requests.get(f"{self.base_url}/api/documents/{document_id}/source")
            fetch_time = time.time() - start_time
            
            if response1.status_code != 200:
                self.log_test(
                    f"Caching Test ({document_id[:8]}...)",
                    False,
                    "First request failed",
                    {"status_code": response1.status_code}
                )
                return False
            
            # Second request should hit cache (should be faster)
            start_time = time.time()
            response2 = requests.get(f"{self.base_url}/api/documents/{document_id}/source")
            cache_time = time.time() - start_time
            
            if response2.status_code != 200:
                self.log_test(
                    f"Caching Test ({document_id[:8]}...)",
                    False,
                    "Second request failed",
                    {"status_code": response2.status_code}
                )
                return False
            
            # Verify content is the same
            if response1.content == response2.content:
                self.log_test(
                    f"Caching Test ({document_id[:8]}...)",
                    True,
                    f"Cache working - fetch: {fetch_time:.3f}s, cache: {cache_time:.3f}s",
                    {
                        "document_id": document_id,
                        "fetch_time": fetch_time,
                        "cache_time": cache_time,
                        "content_match": True
                    }
                )
                return True
            else:
                self.log_test(
                    f"Caching Test ({document_id[:8]}...)",
                    False,
                    "Content mismatch between requests",
                    {"content_match": False}
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"Caching Test ({document_id[:8]}...)",
                False,
                f"Error: {e}",
                {"document_id": document_id, "error": str(e)}
            )
            return False
    
    def test_cache_stats(self) -> bool:
        """Test cache statistics"""
        try:
            response = requests.get(f"{self.base_url}/api/documents/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                cache_stats = stats.get("cache_stats", {})
                
                cached_docs = cache_stats.get("cached_documents", 0)
                
                self.log_test(
                    "Cache Statistics",
                    True,
                    f"Cache contains {cached_docs} documents",
                    stats
                )
                return True
            else:
                self.log_test(
                    "Cache Statistics",
                    False,
                    f"Failed with status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Cache Statistics",
                False,
                f"Error: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid document ID"""
        try:
            invalid_id = "invalid-document-id-12345"
            response = requests.get(f"{self.base_url}/api/documents/{invalid_id}/source")
            
            if response.status_code == 404:
                self.log_test(
                    "Error Handling",
                    True,
                    "Correctly returned 404 for invalid document ID",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_test(
                    "Error Handling",
                    False,
                    f"Expected 404, got {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Error Handling",
                False,
                f"Error: {e}",
                {"error": str(e)}
            )
            return False
    
    def run_all_tests(self):
        """Run all Phase 1 tests"""
        print("🎯 Phase 1: Ragie Document Source Integration Tests")
        print("=" * 60)
        
        # Test 1: Service Health
        if not self.test_service_health():
            print("❌ Service not healthy, skipping other tests")
            return self.generate_report()
        
        # Test 2: Cache Stats
        self.test_cache_stats()
        
        # Test 3: Error Handling
        self.test_error_handling()
        
        # Test 4-6: Document operations with available IDs
        document_ids = self.get_test_document_ids()
        
        for doc_id in document_ids:
            self.test_document_source_retrieval(doc_id)
            self.test_document_metadata(doc_id)
            self.test_caching_functionality(doc_id)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎯 Phase 1 Test Results")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        report = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "phase_1_complete": failed_tests == 0,
            "results": self.test_results
        }
        
        return report

def main():
    """Run Phase 1 tests"""
    tester = DocumentSourceTester()
    report = tester.run_all_tests()
    
    if report["phase_1_complete"]:
        print("\n🎉 Phase 1: Document Source Integration - COMPLETE")
        print("✅ Ready to proceed to Phase 2: Video Player Implementation")
    else:
        print("\n⚠️ Phase 1: Document Source Integration - INCOMPLETE")
        print("❌ Please fix issues before proceeding to Phase 2")
    
    return report

if __name__ == "__main__":
    main()