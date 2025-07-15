#!/usr/bin/env python3
"""
Ragie Tools Usage Examples for PydanticAI Agents
===============================================

Demonstrates how to use the Ragie-powered tools with PydanticAI agents
for both text and voice interactions. Shows integration patterns and
best practices for universal QSR assistance.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import json

# Import our Ragie tools
from ragie_tools import (
    ragie_tools,
    ToolExecutionContext,
    search_ragie_knowledge,
    extract_ragie_visual,
    get_ragie_equipment_info,
    get_ragie_procedure_info,
    get_ragie_safety_info,
    RagieKnowledgeResult,
    RagieVisualResult,
    RagieEquipmentResult,
    RagieProcedureResult,
    RagieSafetyResult
)

# ===============================================================================
# EXAMPLE 1: TEXT CHAT AGENT WITH RAGIE TOOLS
# ===============================================================================

async def text_chat_example():
    """Example of using Ragie tools in a text chat agent"""
    
    print("🔧 TEXT CHAT AGENT WITH RAGIE TOOLS")
    print("=" * 50)
    
    # Simulate a text chat conversation
    user_queries = [
        "How do I clean the fryer?",
        "What safety procedures should I follow?",
        "Show me visual guides for pizza making",
        "What equipment do I need for maintenance?",
        "Walk me through the dough making procedure"
    ]
    
    for query in user_queries:
        print(f"\n👤 User: {query}")
        
        # Create context for this query
        context = ToolExecutionContext(
            query=query,
            interaction_mode="text",
            session_id="text_chat_example",
            conversation_history=[]
        )
        
        # Determine which tool to use based on query
        if "safety" in query.lower():
            result = await get_ragie_safety_info(query, context)
            print(f"🛡️  Safety Agent: {result.content[:100]}...")
            if result.safety_warnings:
                print(f"   ⚠️  {len(result.safety_warnings)} safety warnings")
        
        elif "visual" in query.lower() or "show" in query.lower():
            result = await extract_ragie_visual(query, context)
            print(f"📸 Visual Agent: {result.content[:100]}...")
            if result.visual_citations:
                print(f"   🖼️  {len(result.visual_citations)} visual citations")
        
        elif "equipment" in query.lower() or "fryer" in query.lower():
            equipment_name = "fryer" if "fryer" in query.lower() else "equipment"
            result = await get_ragie_equipment_info(equipment_name, context)
            print(f"⚙️  Equipment Agent: {result.content[:100]}...")
            if result.troubleshooting_steps:
                print(f"   🔧 {len(result.troubleshooting_steps)} troubleshooting steps")
        
        elif "procedure" in query.lower() or "walk me through" in query.lower():
            procedure_name = "dough making" if "dough" in query.lower() else "procedure"
            result = await get_ragie_procedure_info(procedure_name, context)
            print(f"📋 Procedure Agent: {result.content[:100]}...")
            if result.procedure_steps:
                print(f"   📝 {len(result.procedure_steps)} procedure steps")
        
        else:
            result = await search_ragie_knowledge(query, context)
            print(f"🧠 Knowledge Agent: {result.content[:100]}...")
            if result.knowledge_type:
                print(f"   📚 Knowledge type: {result.knowledge_type}")
        
        # Show suggested actions
        if result.suggested_actions:
            print(f"   💡 Suggested actions: {len(result.suggested_actions)}")

# ===============================================================================
# EXAMPLE 2: VOICE AGENT WITH RAGIE TOOLS
# ===============================================================================

async def voice_agent_example():
    """Example of using Ragie tools in a voice agent"""
    
    print("\n🎤 VOICE AGENT WITH RAGIE TOOLS")
    print("=" * 50)
    
    # Simulate a voice interaction
    voice_queries = [
        "Tell me about fryer maintenance",
        "What are the safety protocols for the grill?",
        "How do I make pizza dough step by step?"
    ]
    
    for query in voice_queries:
        print(f"\n🎙️  Voice Input: {query}")
        
        # Create voice context
        context = ToolExecutionContext(
            query=query,
            interaction_mode="voice",
            session_id="voice_agent_example",
            conversation_history=[]
        )
        
        # Use intelligent routing for voice
        if "safety" in query.lower():
            result = await get_ragie_safety_info(query, context)
            
            # Format for voice output
            voice_response = f"Safety information: {result.content[:150]}..."
            if result.immediate_actions:
                voice_response += f" Immediate actions required: {len(result.immediate_actions)} steps."
            
            print(f"🔊 Voice Output: {voice_response}")
        
        elif "maintenance" in query.lower():
            equipment_name = "fryer" if "fryer" in query.lower() else "equipment"
            result = await get_ragie_equipment_info(equipment_name, context)
            
            voice_response = f"Equipment maintenance: {result.content[:150]}..."
            if result.maintenance_required:
                voice_response += " Regular maintenance is required."
            
            print(f"🔊 Voice Output: {voice_response}")
        
        elif "step by step" in query.lower():
            procedure_name = "pizza dough" if "dough" in query.lower() else "procedure"
            result = await get_ragie_procedure_info(procedure_name, context)
            
            voice_response = f"Procedure: {result.content[:150]}..."
            if result.estimated_time:
                voice_response += f" Estimated time: {result.estimated_time}."
            
            print(f"🔊 Voice Output: {voice_response}")
        
        # Show performance metrics
        print(f"   ⏱️  Response time: {result.execution_time_ms:.1f}ms")
        print(f"   📊 Confidence: {result.confidence:.1%}")

# ===============================================================================
# EXAMPLE 3: MULTI-TOOL COORDINATION
# ===============================================================================

async def multi_tool_coordination_example():
    """Example of coordinating multiple tools for complex queries"""
    
    print("\n🎯 MULTI-TOOL COORDINATION")
    print("=" * 50)
    
    # Complex query that requires multiple tools
    complex_query = "I need to clean the fryer safely - show me the procedure and any visual guides"
    
    print(f"👤 Complex Query: {complex_query}")
    
    # Create context
    context = ToolExecutionContext(
        query=complex_query,
        interaction_mode="text",
        equipment_context="fryer",
        safety_priority=True,
        session_id="multi_tool_example"
    )
    
    # Use multiple tools in coordination
    print("\n🔄 Coordinating multiple tools...")
    
    # 1. Get safety information first (priority)
    safety_result = await get_ragie_safety_info("fryer cleaning safety", context)
    print(f"1️⃣ Safety: {safety_result.content[:80]}...")
    
    # 2. Get equipment-specific information
    equipment_result = await get_ragie_equipment_info("fryer", context)
    print(f"2️⃣ Equipment: {equipment_result.content[:80]}...")
    
    # 3. Get procedure information
    procedure_result = await get_ragie_procedure_info("fryer cleaning", context)
    print(f"3️⃣ Procedure: {procedure_result.content[:80]}...")
    
    # 4. Get visual guides
    visual_result = await extract_ragie_visual("fryer cleaning visual guide", context)
    print(f"4️⃣ Visual: {visual_result.content[:80]}...")
    
    # Combine results for comprehensive response
    comprehensive_response = {
        "safety_warnings": safety_result.safety_warnings,
        "equipment_info": equipment_result.content,
        "procedure_steps": procedure_result.procedure_steps,
        "visual_citations": visual_result.visual_citations,
        "total_sources": len(safety_result.sources) + len(equipment_result.sources) + len(procedure_result.sources),
        "confidence": (safety_result.confidence + equipment_result.confidence + procedure_result.confidence) / 3
    }
    
    print(f"\n📊 Comprehensive Response:")
    print(f"   Safety Warnings: {len(comprehensive_response['safety_warnings'])}")
    print(f"   Procedure Steps: {len(comprehensive_response['procedure_steps'])}")
    print(f"   Visual Citations: {len(comprehensive_response['visual_citations'])}")
    print(f"   Total Sources: {comprehensive_response['total_sources']}")
    print(f"   Average Confidence: {comprehensive_response['confidence']:.1%}")

# ===============================================================================
# EXAMPLE 4: CONTEXT-AWARE CONVERSATION
# ===============================================================================

async def context_aware_conversation_example():
    """Example of context-aware conversation using Ragie tools"""
    
    print("\n💬 CONTEXT-AWARE CONVERSATION")
    print("=" * 50)
    
    # Simulate a conversation with context building
    conversation = [
        "I'm having trouble with the fryer",
        "What safety precautions should I take?",
        "Show me the cleaning procedure",
        "How often should I do this maintenance?"
    ]
    
    conversation_history = []
    session_id = "context_aware_example"
    
    for i, query in enumerate(conversation):
        print(f"\n{i+1}. 👤 User: {query}")
        
        # Build context with conversation history
        context = ToolExecutionContext(
            query=query,
            interaction_mode="text",
            equipment_context="fryer",  # Persistent equipment context
            session_id=session_id,
            conversation_history=conversation_history
        )
        
        # Context-aware tool selection
        if i == 0:  # First query - general equipment issue
            result = await get_ragie_equipment_info("fryer", context)
            print(f"   ⚙️  Equipment Agent: {result.content[:100]}...")
        
        elif i == 1:  # Safety question - context includes fryer
            result = await get_ragie_safety_info("fryer safety", context)
            print(f"   🛡️  Safety Agent: {result.content[:100]}...")
        
        elif i == 2:  # Procedure question - context includes fryer and safety
            result = await get_ragie_procedure_info("fryer cleaning", context)
            print(f"   📋 Procedure Agent: {result.content[:100]}...")
        
        elif i == 3:  # Follow-up question - context includes all previous
            result = await search_ragie_knowledge("fryer maintenance schedule", context)
            print(f"   🧠 Knowledge Agent: {result.content[:100]}...")
        
        # Add to conversation history
        conversation_history.append({
            "query": query,
            "response": result.content[:200],
            "timestamp": datetime.now().isoformat(),
            "tool_used": result.tool_name
        })
        
        # Show context enhancement
        if result.metadata.get('context_enhanced'):
            print(f"   🔗 Context enhanced from {len(conversation_history)} previous exchanges")

# ===============================================================================
# EXAMPLE 5: PERFORMANCE MONITORING
# ===============================================================================

async def performance_monitoring_example():
    """Example of performance monitoring with Ragie tools"""
    
    print("\n📊 PERFORMANCE MONITORING")
    print("=" * 50)
    
    # Run multiple queries to generate performance data
    test_queries = [
        ("equipment", "fryer maintenance"),
        ("safety", "safety protocols"),
        ("procedure", "pizza making steps"),
        ("knowledge", "restaurant operations"),
        ("visual", "equipment diagrams")
    ]
    
    print("🔄 Running performance tests...")
    
    for tool_type, query in test_queries:
        context = ToolExecutionContext(
            query=query,
            interaction_mode="text",
            session_id="performance_test"
        )
        
        if tool_type == "equipment":
            result = await get_ragie_equipment_info("fryer", context)
        elif tool_type == "safety":
            result = await get_ragie_safety_info(query, context)
        elif tool_type == "procedure":
            result = await get_ragie_procedure_info("pizza making", context)
        elif tool_type == "knowledge":
            result = await search_ragie_knowledge(query, context)
        elif tool_type == "visual":
            result = await extract_ragie_visual(query, context)
        
        print(f"   {tool_type}: {result.execution_time_ms:.1f}ms")
    
    # Get comprehensive performance metrics
    print("\n📈 Performance Metrics:")
    metrics = ragie_tools.get_tool_metrics()
    
    for tool_name, tool_metrics in metrics.items():
        print(f"   {tool_name}:")
        print(f"     Executions: {tool_metrics['execution_count']}")
        print(f"     Success Rate: {tool_metrics['success_rate']:.1%}")
        print(f"     Avg Time: {tool_metrics['avg_execution_time_ms']:.1f}ms")
        print(f"     Total Time: {tool_metrics['total_execution_time_ms']:.1f}ms")
    
    # Health check
    health = ragie_tools.health_check()
    print(f"\n💚 Health Status:")
    print(f"   Ragie Available: {health['ragie_available']}")
    print(f"   Tools Available: {health['available_tools']}/{health['total_tools']}")

# ===============================================================================
# EXAMPLE 6: ERROR HANDLING AND FALLBACKS
# ===============================================================================

async def error_handling_example():
    """Example of error handling and fallback strategies"""
    
    print("\n🚨 ERROR HANDLING AND FALLBACKS")
    print("=" * 50)
    
    # Test queries that might cause issues
    edge_cases = [
        "",  # Empty query
        "completely unrelated query about space travel",  # No relevant results
        "a" * 1000,  # Very long query
        "special characters !@#$%^&*()_+{}[]|;':\",./<>?",  # Special characters
    ]
    
    for i, query in enumerate(edge_cases):
        print(f"\n{i+1}. Testing edge case: {query[:50]}...")
        
        context = ToolExecutionContext(
            query=query,
            interaction_mode="text",
            session_id="error_handling_test"
        )
        
        try:
            result = await search_ragie_knowledge(query, context)
            
            if result.success:
                print(f"   ✅ Handled successfully: {result.content[:60]}...")
            else:
                print(f"   ⚠️  Graceful failure: {result.content[:60]}...")
            
            print(f"   📊 Confidence: {result.confidence:.1%}")
            
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:60]}...")

# ===============================================================================
# MAIN EXAMPLE RUNNER
# ===============================================================================

async def main():
    """Run all usage examples"""
    
    print("🚀 RAGIE TOOLS USAGE EXAMPLES")
    print("=" * 60)
    
    # Run all examples
    examples = [
        text_chat_example,
        voice_agent_example,
        multi_tool_coordination_example,
        context_aware_conversation_example,
        performance_monitoring_example,
        error_handling_example
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL USAGE EXAMPLES COMPLETED")
    print("=" * 60)
    
    print("\n🎯 KEY TAKEAWAYS:")
    print("• Ragie tools work seamlessly with both text and voice agents")
    print("• Context-aware search provides better results over time")
    print("• Multi-tool coordination enables comprehensive responses")
    print("• Performance monitoring helps optimize tool usage")
    print("• Error handling ensures graceful degradation")
    print("• Tools are ready for production PydanticAI integration")

if __name__ == "__main__":
    asyncio.run(main())