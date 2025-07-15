#!/usr/bin/env python3
"""
Comprehensive Ragie SDK vs Direct API Filtering Test
==================================================

Tests current SDK filtering capabilities vs potential direct API improvements.
Addresses critical questions about equipment-specific queries and performance.
"""

import asyncio
import sys
import os
import json
import time
import httpx

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.ragie_service_clean import clean_ragie_service

class RagieFilteringAnalysis:
    """Comprehensive analysis of Ragie filtering capabilities"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.ragie.ai"
        self._initialize_api_key()
    
    def _initialize_api_key(self):
        """Get API key from environment or keyring"""
        try:
            self.api_key = os.getenv("RAGIE_API_KEY")
            if not self.api_key:
                try:
                    import keyring
                    self.api_key = keyring.get_password("memex", "RAGIE_API_KEY")
                except ImportError:
                    pass
        except Exception as e:
            print(f"❌ Failed to get API key: {e}")
    
    async def test_current_sdk_capabilities(self):
        """Test our current SDK implementation capabilities"""
        print("🔍 Testing Current SDK Implementation")
        print("=" * 50)
        
        if not clean_ragie_service.is_available():
            print("❌ Ragie service not available")
            return {}
        
        test_queries = [
            # Equipment-specific queries
            "Baxter OV520E1",
            "fryer equipment", 
            "oven maintenance",
            "Taylor equipment",
            
            # Document type queries
            "diagram",
            "manual",
            "safety procedures",
            
            # QSR-specific queries
            "pizza preparation",
            "kitchen equipment",
            "cleaning procedures",
            
            # Generic queries
            "temperature",
            "procedures",
            "equipment"
        ]
        
        results = {}
        
        for query in test_queries:
            try:
                start_time = time.time()
                search_results = await clean_ragie_service.search(query, limit=5)
                response_time = (time.time() - start_time) * 1000
                
                results[query] = {
                    "result_count": len(search_results),
                    "response_time_ms": round(response_time, 2),
                    "results": []
                }
                
                if search_results:
                    for result in search_results:
                        results[query]["results"].append({
                            "score": result.score,
                            "document_id": result.document_id[:8] + "...",
                            "metadata_keys": list(result.metadata.keys()),
                            "has_equipment_metadata": any(key in result.metadata for key in ['equipment_type', 'model_number', 'manufacturer']),
                            "document_type": result.metadata.get('file_type', 'unknown'),
                            "source": result.metadata.get('original_filename', 'Unknown')[:50] + "..."
                        })
                
                print(f"  '{query}': {len(search_results)} results ({response_time:.0f}ms)")
                
            except Exception as e:
                print(f"  '{query}': Error - {e}")
                results[query] = {"error": str(e)}
        
        return results
    
    async def test_direct_api_with_filters(self):
        """Test direct API with advanced filtering capabilities"""
        print("\n🎯 Testing Direct API with Advanced Filters")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ No API key available for direct API testing")
            return {}
        
        # Advanced filter examples that SDK might not support well
        filter_tests = [
            {
                "name": "Equipment Documents Only",
                "query": "oven",
                "filter": {
                    "document_type": {"$in": ["pdf", "png", "jpg"]}
                }
            },
            {
                "name": "Recent Equipment Manuals",
                "query": "maintenance",
                "filter": {
                    "$and": [
                        {"document_type": "pdf"},
                        {"document_uploaded_at": {"$gte": 1700000000}}  # Recent uploads
                    ]
                }
            },
            {
                "name": "Image Documents",
                "query": "diagram",
                "filter": {
                    "document_type": {"$in": ["png", "jpg", "jpeg"]}
                }
            },
            {
                "name": "Equipment by Name Pattern",
                "query": "Baxter",
                "filter": {
                    "document_name": {"$regex": ".*[Bb]axter.*"}  # May not be supported
                }
            }
        ]
        
        results = {}
        
        async with httpx.AsyncClient() as client:
            for test in filter_tests:
                try:
                    start_time = time.time()
                    
                    # Direct API call with filters
                    response = await client.post(
                        f"{self.base_url}/retrievals",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "query": test["query"],
                            "top_k": 5,
                            "filter": test["filter"],
                            "rerank": True
                        }
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        data = response.json()
                        chunk_count = len(data.get("scored_chunks", []))
                        
                        results[test["name"]] = {
                            "success": True,
                            "result_count": chunk_count,
                            "response_time_ms": round(response_time, 2),
                            "filter_used": test["filter"],
                            "chunks": []
                        }
                        
                        # Analyze first few chunks
                        for chunk in data.get("scored_chunks", [])[:3]:
                            chunk_info = {
                                "score": chunk.get("score", 0),
                                "document_id": chunk.get("document_id", "unknown")[:8] + "...",
                                "metadata": chunk.get("metadata", {})
                            }
                            results[test["name"]]["chunks"].append(chunk_info)
                        
                        print(f"  ✅ {test['name']}: {chunk_count} results ({response_time:.0f}ms)")
                    else:
                        results[test["name"]] = {
                            "success": False,
                            "error": f"HTTP {response.status_code}: {response.text}",
                            "filter_used": test["filter"]
                        }
                        print(f"  ❌ {test['name']}: HTTP {response.status_code}")
                
                except Exception as e:
                    results[test["name"]] = {
                        "success": False,
                        "error": str(e),
                        "filter_used": test["filter"]
                    }
                    print(f"  ❌ {test['name']}: {e}")
        
        return results
    
    async def test_equipment_specific_queries(self):
        """Test equipment-specific query performance"""
        print("\n🔧 Testing Equipment-Specific Query Capabilities")
        print("=" * 50)
        
        equipment_tests = [
            {
                "equipment": "Baxter OV520E1",
                "search_terms": ["Baxter OV520E1", "OV520E1", "Baxter oven", "electric diagram"]
            },
            {
                "equipment": "Taylor Fryer",
                "search_terms": ["Taylor", "fryer", "Taylor fryer", "C602"]
            },
            {
                "equipment": "Slicer Equipment", 
                "search_terms": ["slicer", "Grote", "slicing equipment"]
            }
        ]
        
        results = {}
        
        for equipment_test in equipment_tests:
            equipment_name = equipment_test["equipment"]
            results[equipment_name] = {}
            
            print(f"\n  Testing {equipment_name}:")
            
            for search_term in equipment_test["search_terms"]:
                try:
                    start_time = time.time()
                    search_results = await clean_ragie_service.search(search_term, limit=3)
                    response_time = (time.time() - start_time) * 1000
                    
                    # Analyze relevance
                    relevant_count = 0
                    total_score = 0
                    
                    for result in search_results:
                        total_score += result.score
                        # Check if result seems relevant to equipment
                        text_lower = result.text.lower()
                        equipment_lower = equipment_name.lower()
                        if any(term in text_lower for term in equipment_lower.split()):
                            relevant_count += 1
                    
                    avg_score = total_score / len(search_results) if search_results else 0
                    relevance_ratio = relevant_count / len(search_results) if search_results else 0
                    
                    results[equipment_name][search_term] = {
                        "total_results": len(search_results),
                        "relevant_results": relevant_count,
                        "relevance_ratio": round(relevance_ratio, 2),
                        "avg_score": round(avg_score, 3),
                        "response_time_ms": round(response_time, 2)
                    }
                    
                    print(f"    '{search_term}': {len(search_results)} results, {relevant_count} relevant ({relevance_ratio:.0%})")
                    
                except Exception as e:
                    results[equipment_name][search_term] = {"error": str(e)}
                    print(f"    '{search_term}': Error - {e}")
        
        return results
    
    async def analyze_document_type_distribution(self):
        """Analyze what document types we have and their searchability"""
        print("\n📊 Analyzing Document Type Distribution")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ No API key available for document analysis")
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                # Get document list to analyze types
                response = await client.get(
                    f"{self.base_url}/documents",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"limit": 100}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    documents = data.get("documents", [])
                    
                    # Analyze document types
                    type_distribution = {}
                    equipment_docs = []
                    
                    for doc in documents:
                        doc_type = doc.get("metadata", {}).get("document_type", "unknown")
                        doc_name = doc.get("name", "")
                        
                        if doc_type not in type_distribution:
                            type_distribution[doc_type] = {"count": 0, "examples": []}
                        
                        type_distribution[doc_type]["count"] += 1
                        if len(type_distribution[doc_type]["examples"]) < 3:
                            type_distribution[doc_type]["examples"].append(doc_name)
                        
                        # Check for equipment-related documents
                        if any(term in doc_name.lower() for term in ['baxter', 'taylor', 'oven', 'fryer', 'slicer']):
                            equipment_docs.append({
                                "name": doc_name,
                                "type": doc_type,
                                "id": doc.get("id", "")[:8] + "..."
                            })
                    
                    print(f"📋 Total Documents: {len(documents)}")
                    print(f"📋 Equipment Documents: {len(equipment_docs)}")
                    print("\n📊 Document Type Distribution:")
                    for doc_type, info in type_distribution.items():
                        print(f"  {doc_type}: {info['count']} documents")
                        for example in info['examples'][:2]:
                            print(f"    - {example[:60]}...")
                    
                    print("\n🔧 Equipment Documents Found:")
                    for eq_doc in equipment_docs[:5]:
                        print(f"  {eq_doc['type']}: {eq_doc['name'][:60]}...")
                    
                    return {
                        "total_documents": len(documents),
                        "equipment_documents": len(equipment_docs),
                        "type_distribution": type_distribution,
                        "equipment_docs": equipment_docs
                    }
                else:
                    print(f"❌ Failed to get documents: HTTP {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            print(f"❌ Error analyzing documents: {e}")
            return {"error": str(e)}
    
    async def run_comprehensive_analysis(self):
        """Run complete analysis of SDK vs Direct API capabilities"""
        print("🚀 Comprehensive Ragie Filtering Capability Analysis")
        print("=" * 70)
        
        analysis_results = {
            "timestamp": time.time(),
            "sdk_capabilities": {},
            "direct_api_capabilities": {},
            "equipment_query_performance": {},
            "document_analysis": {},
            "recommendations": {}
        }
        
        # Test current SDK
        analysis_results["sdk_capabilities"] = await self.test_current_sdk_capabilities()
        
        # Test direct API with filters
        analysis_results["direct_api_capabilities"] = await self.test_direct_api_with_filters()
        
        # Test equipment-specific queries
        analysis_results["equipment_query_performance"] = await self.test_equipment_specific_queries()
        
        # Analyze document distribution
        analysis_results["document_analysis"] = await self.analyze_document_type_distribution()
        
        # Generate recommendations
        analysis_results["recommendations"] = self._generate_recommendations(analysis_results)
        
        return analysis_results
    
    def _generate_recommendations(self, results):
        """Generate recommendations based on test results"""
        recommendations = {
            "overall_assessment": "analysis_complete",
            "sdk_vs_api": [],
            "performance_insights": [],
            "architecture_recommendations": []
        }
        
        # SDK vs Direct API comparison
        sdk_results = results.get("sdk_capabilities", {})
        api_results = results.get("direct_api_capabilities", {})
        
        if sdk_results and not any("error" in r for r in sdk_results.values()):
            recommendations["sdk_vs_api"].append("✅ SDK is working and provides basic search functionality")
        
        if api_results:
            successful_filters = [name for name, result in api_results.items() if result.get("success")]
            if successful_filters:
                recommendations["sdk_vs_api"].append(f"✅ Direct API supports advanced filtering: {len(successful_filters)} filters work")
            else:
                recommendations["sdk_vs_api"].append("❌ Direct API filtering may have limitations")
        
        # Equipment query performance
        equipment_results = results.get("equipment_query_performance", {})
        if equipment_results:
            total_equipment_tests = sum(len(tests) for tests in equipment_results.values())
            successful_tests = sum(
                1 for tests in equipment_results.values() 
                for test in tests.values() 
                if isinstance(test, dict) and "error" not in test
            )
            
            if successful_tests / total_equipment_tests > 0.7:
                recommendations["performance_insights"].append("✅ Equipment queries generally successful")
            else:
                recommendations["performance_insights"].append("⚠️ Equipment query success rate could be improved")
        
        # Architecture recommendations
        doc_analysis = results.get("document_analysis", {})
        if doc_analysis and not doc_analysis.get("error"):
            equipment_doc_count = doc_analysis.get("equipment_documents", 0)
            total_docs = doc_analysis.get("total_documents", 0)
            
            if equipment_doc_count > 0:
                recommendations["architecture_recommendations"].append(
                    f"📊 Found {equipment_doc_count}/{total_docs} equipment documents - good foundation for filtering"
                )
            
            type_dist = doc_analysis.get("type_distribution", {})
            if "png" in type_dist or "jpg" in type_dist:
                recommendations["architecture_recommendations"].append(
                    "🖼️ Image documents present - entity extraction recommended for searchability"
                )
        
        return recommendations

async def main():
    """Run the comprehensive analysis"""
    analyzer = RagieFilteringAnalysis()
    
    try:
        results = await analyzer.run_comprehensive_analysis()
        
        print("\n" + "=" * 70)
        print("📋 ANALYSIS SUMMARY")
        print("=" * 70)
        
        # Print recommendations
        recommendations = results.get("recommendations", {})
        
        print("\n🔍 SDK vs Direct API Assessment:")
        for rec in recommendations.get("sdk_vs_api", []):
            print(f"  {rec}")
        
        print("\n⚡ Performance Insights:")
        for rec in recommendations.get("performance_insights", []):
            print(f"  {rec}")
        
        print("\n🏗️ Architecture Recommendations:")
        for rec in recommendations.get("architecture_recommendations", []):
            print(f"  {rec}")
        
        # Save detailed results
        with open("ragie_filtering_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: ragie_filtering_analysis_results.json")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())