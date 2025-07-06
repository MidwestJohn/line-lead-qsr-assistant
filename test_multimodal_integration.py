#!/usr/bin/env python3
"""
Comprehensive test for multimodal citation integration
Tests the complete flow from voice input to visual citation display
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def test_multimodal_integration():
    """Test the complete multimodal citation system"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Multimodal Citation Integration")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check system status
        print("\n1. Checking system status...")
        async with session.get(f"{base_url}/multimodal-system-status") as resp:
            if resp.status == 200:
                status = await resp.json()
                print(f"   ✅ System ready: {status['multimodal_citations_ready']}")
                print(f"   📄 Documents available: {status['available_documents']}")
                print(f"   📁 Document names: {status['document_names']}")
            else:
                print(f"   ❌ System status check failed: {resp.status}")
                return
        
        # Test 2: Test citation extraction
        print("\n2. Testing citation extraction...")
        test_queries = [
            {
                "message": "What safety warnings should I know about the ice cream machine?",
                "equipment": "taylor"
            },
            {
                "message": "Show me the temperature settings for cleaning",
                "equipment": "taylor"
            },
            {
                "message": "Check diagram 3.2 for the compressor assembly",
                "equipment": "ice cream machine"
            }
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Test Query {i}: {query['message']}")
            
            async with session.post(
                f"{base_url}/voice-with-multimodal-citations",
                json={
                    "message": query["message"],
                    "current_equipment": query["equipment"],
                    "enable_citations": True
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    citations = result.get("visual_citations", [])
                    manual_refs = result.get("manual_references", [])
                    
                    print(f"      📝 Response: {result.get('response', '')[:80]}...")
                    print(f"      🖼️  Visual citations: {len(citations)}")
                    print(f"      📖 Manual references: {len(manual_refs)}")
                    
                    if citations:
                        for j, citation in enumerate(citations):
                            print(f"         Citation {j+1}: {citation['type']} - {citation['reference']} (Page {citation['page']})")
                            
                            # Test citation content retrieval
                            citation_id = citation['citation_id']
                            async with session.get(f"{base_url}/citation-content/{citation_id}") as content_resp:
                                if content_resp.status == 200:
                                    content_type = content_resp.headers.get('content-type', '')
                                    if 'image' in content_type:
                                        print(f"         ✅ Image content available ({content_type})")
                                    else:
                                        print(f"         ⚠️  Content type: {content_type}")
                                else:
                                    print(f"         ❌ Citation content not found: {content_resp.status}")
                    
                    if manual_refs:
                        for ref in manual_refs:
                            print(f"         Manual: {ref['document']} (Page {ref['page']})")
                else:
                    print(f"      ❌ Query failed: {resp.status}")
        
        # Test 3: Test voice + graph context integration
        print("\n3. Testing voice + graph context integration...")
        
        async with session.get(f"{base_url}/voice-graph-status") as resp:
            if resp.status == 200:
                status = await resp.json()
                print(f"   ✅ Voice graph integration: {status.get('voice_graph_integration_ready', False)}")
                print(f"   🧠 Neo4j connected: {status.get('service_status', {}).get('neo4j_connected', False)}")
                print(f"   🗣️  Voice orchestrator: {status.get('service_status', {}).get('voice_orchestrator_integration', False)}")
            else:
                print(f"   ❌ Voice graph status check failed: {resp.status}")
        
        # Test 4: Frontend API compatibility
        print("\n4. Testing frontend API compatibility...")
        
        # Test the regular chat endpoint that frontend might use
        async with session.post(
            f"{base_url}/chat",
            json={"message": "What safety precautions should I follow for the ice cream machine?"}
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Regular chat API working")
                print(f"   📝 Response: {result.get('response', '')[:60]}...")
            else:
                print(f"   ❌ Regular chat API failed: {resp.status}")
    
    print("\n" + "=" * 50)
    print("🎯 Multimodal Integration Test Complete")
    print("\nNext Steps:")
    print("1. Open http://localhost:3000 in browser")
    print("2. Ask equipment-related questions with visual references")
    print("3. Verify citations appear below assistant responses")
    print("4. Click citation cards to view visual content")

if __name__ == "__main__":
    asyncio.run(test_multimodal_integration())