#!/usr/bin/env python3
"""
Comprehensive test of the unified chat system
Tests both the advanced multi-agent system and fallback mechanisms
"""

import asyncio
import json
import requests
import sys
import time
from datetime import datetime

class UnifiedChatTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def test_endpoint(self, message, test_name):
        """Test a single chat endpoint"""
        print(f"\n=== {test_name} ===")
        print(f"Message: {message}")
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    "test_name": test_name,
                    "message": message,
                    "status": "success",
                    "response_length": len(data.get("response", "")),
                    "retrieval_method": data.get("retrieval_method", "unknown"),
                    "has_visual_citations": bool(data.get("visual_citations")),
                    "has_manual_references": bool(data.get("manual_references")),
                    "has_document_context": bool(data.get("document_context")),
                    "has_parsed_steps": bool(data.get("parsed_steps")),
                    "has_contextual_recommendations": bool(data.get("contextual_recommendations")),
                    "response_preview": data.get("response", "")[:200] + "..." if len(data.get("response", "")) > 200 else data.get("response", "")
                }
                
                self.results.append(result)
                
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Response Length: {result['response_length']} chars")
                print(f"✓ Retrieval Method: {result['retrieval_method']}")
                print(f"✓ Visual Citations: {result['has_visual_citations']}")
                print(f"✓ Manual References: {result['has_manual_references']}")
                print(f"✓ Document Context: {result['has_document_context']}")
                print(f"✓ Parsed Steps: {result['has_parsed_steps']}")
                print(f"✓ Contextual Recommendations: {result['has_contextual_recommendations']}")
                print(f"✓ Response Preview: {result['response_preview']}")
                
                return True
                
            else:
                print(f"✗ HTTP Error: {response.status_code}")
                print(f"✗ Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🧪 COMPREHENSIVE UNIFIED CHAT SYSTEM TEST")
        print("=" * 60)
        
        # Test 1: Basic Equipment Question
        self.test_endpoint(
            "What temperature should I set the fryer to?",
            "Basic Equipment Question"
        )
        
        # Test 2: Safety Procedure
        self.test_endpoint(
            "How do I clean the fryer safely?",
            "Safety Procedure"
        )
        
        # Test 3: Image Request
        self.test_endpoint(
            "Show me an image of the Baxter oven",
            "Image Request"
        )
        
        # Test 4: Troubleshooting
        self.test_endpoint(
            "The fryer isn't heating up properly, what should I check?",
            "Troubleshooting"
        )
        
        # Test 5: Maintenance Question
        self.test_endpoint(
            "How often should I change the fryer oil?",
            "Maintenance Question"
        )
        
        # Test 6: Complex Multi-Part Question
        self.test_endpoint(
            "I need to train new staff on fryer operation - what are the key safety steps and what temperature should we use for chicken?",
            "Complex Multi-Part Question"
        )
        
        # Test 7: Equipment Comparison
        self.test_endpoint(
            "What's the difference between convection and regular ovens?",
            "Equipment Comparison"
        )
        
        # Test 8: Vague Question (Should trigger intelligent classification)
        self.test_endpoint(
            "Something's wrong with the equipment",
            "Vague Question"
        )
        
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["status"] == "success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Analyze retrieval methods
        methods = {}
        for result in self.results:
            method = result["retrieval_method"]
            if method not in methods:
                methods[method] = 0
            methods[method] += 1
        
        print(f"\n📈 Retrieval Methods Used:")
        for method, count in methods.items():
            print(f"  {method}: {count} tests")
        
        # Analyze advanced features
        features = {
            "visual_citations": len([r for r in self.results if r["has_visual_citations"]]),
            "manual_references": len([r for r in self.results if r["has_manual_references"]]),
            "document_context": len([r for r in self.results if r["has_document_context"]]),
            "parsed_steps": len([r for r in self.results if r["has_parsed_steps"]]),
            "contextual_recommendations": len([r for r in self.results if r["has_contextual_recommendations"]])
        }
        
        print(f"\n🔧 Advanced Features Usage:")
        for feature, count in features.items():
            print(f"  {feature}: {count}/{total_tests} tests ({(count/total_tests)*100:.1f}%)")
        
        # Identify potential issues
        print(f"\n⚠️  Potential Issues:")
        fallback_count = methods.get("ragie_fallback", 0) + methods.get("fallback", 0)
        if fallback_count > 0:
            print(f"  - {fallback_count} tests used fallback methods (not multi-agent)")
        
        if features["visual_citations"] == 0:
            print(f"  - No visual citations generated")
        
        if features["parsed_steps"] == 0:
            print(f"  - No parsed steps generated")
        
        if features["contextual_recommendations"] == 0:
            print(f"  - No contextual recommendations generated")
        
        multi_agent_count = methods.get("multi_agent", 0) + methods.get("equipment_specialist", 0) + methods.get("safety_specialist", 0)
        if multi_agent_count < total_tests * 0.5:
            print(f"  - Multi-agent system only used in {multi_agent_count}/{total_tests} tests")
        
        print(f"\n🎯 Recommendations:")
        if fallback_count > total_tests * 0.3:
            print(f"  - Investigate why voice orchestrator is falling back frequently")
        
        if features["visual_citations"] == 0:
            print(f"  - Check visual citation extraction from voice responses")
        
        if features["parsed_steps"] == 0:
            print(f"  - Verify step parsing is working in voice orchestrator")
        
        print(f"\n✅ System Status: {'🟢 HEALTHY' if successful_tests == total_tests and multi_agent_count > 0 else '🟡 NEEDS ATTENTION'}")

if __name__ == "__main__":
    tester = UnifiedChatTester()
    tester.run_comprehensive_test()