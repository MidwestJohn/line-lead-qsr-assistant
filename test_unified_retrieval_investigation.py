#!/usr/bin/env python3
"""
Investigation Script: Text vs Voice Retrieval Quality Analysis
============================================================

This script analyzes the current state of text vs voice retrieval to understand
whether unification is needed or already completed.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import requests
import json
import time
import asyncio

# Test endpoints
BASE_URL = "http://localhost:8000"
TEST_QUERIES = [
    "What temperature for Taylor C602?",
    "How do I clean the fryer?",
    "What are the safety procedures for the grill?",
    "How often should I change the oil?",
    "What's the procedure for opening the restaurant?"
]

def test_text_endpoint(query):
    """Test the main chat endpoint (text input)"""
    try:
        response = requests.post(f"{BASE_URL}/chat", json={
            "message": query,
            "conversation_id": "test_text_session"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "response": data.get("response", ""),
                "parsed_steps": data.get("parsed_steps"),
                "timestamp": data.get("timestamp"),
                "endpoint": "text_chat"
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}",
                "endpoint": "text_chat"
            }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "endpoint": "text_chat"
        }

def test_voice_endpoint(query):
    """Test the voice processing endpoint"""
    try:
        response = requests.post(f"{BASE_URL}/voice-with-graph-context", json={
            "message": query,
            "conversation_id": "test_voice_session"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "response": data.get("text_response", data.get("response", "")),
                "intent": data.get("detected_intent"),
                "confidence": data.get("confidence_score"),
                "equipment": data.get("equipment_mentioned"),
                "should_continue": data.get("should_continue_listening"),
                "endpoint": "voice_graph_context"
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}",
                "endpoint": "voice_graph_context"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e), 
            "endpoint": "voice_process"
        }

def analyze_response_quality(response_text, query):
    """Analyze response quality for specific indicators"""
    if not response_text:
        return {"quality": "poor", "reasons": ["Empty response"]}
    
    text_lower = response_text.lower()
    query_lower = query.lower()
    quality_indicators = []
    
    # Check for specific equipment mentions
    if "taylor" in query_lower or "c602" in query_lower:
        if "taylor" in text_lower or "c602" in text_lower:
            quality_indicators.append("Equipment-specific (Taylor C602)")
        else:
            quality_indicators.append("Missing equipment specificity")
    
    if "fryer" in query_lower:
        if "fryer" in text_lower:
            quality_indicators.append("Equipment-specific (fryer)")
        else:
            quality_indicators.append("Missing equipment specificity")
    
    # Check for temperature specificity
    if "temperature" in query_lower:
        temp_patterns = ["°f", "°c", "degrees", "fahrenheit", "celsius"]
        if any(pattern in text_lower for pattern in temp_patterns):
            quality_indicators.append("Specific temperature information")
        else:
            quality_indicators.append("Missing temperature specifics")
    
    # Check for procedural details
    if any(word in query_lower for word in ["clean", "procedure", "how"]):
        step_patterns = ["step", "first", "then", "next", "finally"]
        if any(pattern in text_lower for pattern in step_patterns):
            quality_indicators.append("Step-by-step procedures")
        else:
            quality_indicators.append("Missing procedural details")
    
    # Check for safety information
    if "safety" in query_lower:
        safety_patterns = ["safety", "warning", "caution", "danger", "protective"]
        if any(pattern in text_lower for pattern in safety_patterns):
            quality_indicators.append("Safety information included")
        else:
            quality_indicators.append("Missing safety details")
    
    # Check for generic responses
    generic_patterns = ["i can help", "let me assist", "i'm here to help", "happy to help"]
    if any(pattern in text_lower for pattern in generic_patterns):
        quality_indicators.append("Generic response detected")
    
    # Check for equipment manual references
    manual_patterns = ["manual", "documentation", "handbook", "guide"]
    if any(pattern in text_lower for pattern in manual_patterns):
        quality_indicators.append("References documentation")
    
    # Determine overall quality
    positive_indicators = [i for i in quality_indicators if not i.startswith("Missing") and "Generic" not in i]
    negative_indicators = [i for i in quality_indicators if i.startswith("Missing") or "Generic" in i]
    
    if len(positive_indicators) >= 2 and len(negative_indicators) == 0:
        quality = "high"
    elif len(positive_indicators) >= 1 and len(negative_indicators) <= 1:
        quality = "medium"
    else:
        quality = "poor"
    
    return {
        "quality": quality,
        "positive_indicators": positive_indicators,
        "negative_indicators": negative_indicators,
        "all_indicators": quality_indicators
    }

def main():
    """Run the investigation"""
    print("🔍 UNIFIED RETRIEVAL INVESTIGATION")
    print("=" * 50)
    print(f"Testing {len(TEST_QUERIES)} queries against text and voice endpoints")
    print()
    
    results = {}
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"📝 Query {i}: {query}")
        print("-" * 40)
        
        # Test text endpoint
        print("Testing TEXT endpoint...")
        text_result = test_text_endpoint(query)
        
        # Test voice endpoint 
        print("Testing VOICE endpoint...")
        voice_result = test_voice_endpoint(query)
        
        # Analyze responses
        text_analysis = None
        voice_analysis = None
        
        if text_result["status"] == "success":
            text_analysis = analyze_response_quality(text_result["response"], query)
            print(f"✅ TEXT: {text_analysis['quality'].upper()} quality")
            if text_analysis["negative_indicators"]:
                print(f"   Issues: {', '.join(text_analysis['negative_indicators'])}")
        else:
            print(f"❌ TEXT: {text_result['error']}")
        
        if voice_result["status"] == "success":
            voice_analysis = analyze_response_quality(voice_result["response"], query)
            print(f"✅ VOICE: {voice_analysis['quality'].upper()} quality")
            if voice_analysis["negative_indicators"]:
                print(f"   Issues: {', '.join(voice_analysis['negative_indicators'])}")
        else:
            print(f"❌ VOICE: {voice_result['error']}")
        
        results[query] = {
            "text_result": text_result,
            "voice_result": voice_result,
            "text_analysis": text_analysis,
            "voice_analysis": voice_analysis
        }
        
        print()
        time.sleep(1)  # Rate limiting
    
    # Summary analysis
    print("📊 SUMMARY ANALYSIS")
    print("=" * 50)
    
    text_qualities = []
    voice_qualities = []
    
    for query, result in results.items():
        if result["text_analysis"]:
            text_qualities.append(result["text_analysis"]["quality"])
        if result["voice_analysis"]:
            voice_qualities.append(result["voice_analysis"]["quality"])
    
    def quality_score(qualities):
        if not qualities:
            return 0
        score_map = {"high": 3, "medium": 2, "poor": 1}
        return sum(score_map.get(q, 0) for q in qualities) / len(qualities)
    
    text_score = quality_score(text_qualities)
    voice_score = quality_score(voice_qualities)
    
    print(f"TEXT Chat Average Quality: {text_score:.1f}/3.0")
    print(f"VOICE Chat Average Quality: {voice_score:.1f}/3.0")
    print()
    
    # Unification assessment
    if abs(text_score - voice_score) < 0.5:
        print("✅ UNIFICATION STATUS: Already unified")
        print("   Both text and voice show similar quality levels")
    elif voice_score > text_score:
        print("🔧 UNIFICATION NEEDED: Voice outperforms text")
        print("   Text chat should be upgraded to use voice retrieval logic")
    elif text_score > voice_score:
        print("🔧 UNIFICATION NEEDED: Text outperforms voice")
        print("   Voice chat should be upgraded to use text retrieval logic")
    else:
        print("❓ UNIFICATION STATUS: Unclear - both may need improvement")
    
    # Architecture analysis
    print()
    print("🏗️ ARCHITECTURE ANALYSIS")
    print("-" * 30)
    
    # Check if both are using the same orchestrator
    text_using_orchestrator = False
    voice_using_orchestrator = False
    
    for query, result in results.items():
        if result["text_result"]["status"] == "success":
            # Check for orchestrator indicators in response
            response = result["text_result"]["response"]
            if "sources consulted" in response.lower():
                text_using_orchestrator = True
                break
    
    for query, result in results.items():
        if result["voice_result"]["status"] == "success":
            # Check for voice orchestrator indicators
            if result["voice_result"].get("intent") or result["voice_result"].get("confidence"):
                voice_using_orchestrator = True
                break
    
    print(f"Text using orchestrator: {text_using_orchestrator}")
    print(f"Voice using orchestrator: {voice_using_orchestrator}")
    
    if text_using_orchestrator and voice_using_orchestrator:
        print("✅ Both endpoints appear to use advanced orchestration")
    elif voice_using_orchestrator and not text_using_orchestrator:
        print("🔧 Voice has orchestration, text needs upgrade")
    elif text_using_orchestrator and not voice_using_orchestrator:
        print("🔧 Text has orchestration, voice needs upgrade")
    else:
        print("❌ Neither endpoint using advanced orchestration")
    
    # Save detailed results
    with open("retrieval_investigation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: retrieval_investigation_results.json")

if __name__ == "__main__":
    main()