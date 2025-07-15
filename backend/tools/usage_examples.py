#!/usr/bin/env python3
"""
PydanticAI Tools Usage Examples
==============================

Practical examples showing how to use the QSR PydanticAI Tools with
existing services and voice_agent.py integration.

These examples demonstrate:
1. Basic tool usage with existing services
2. Multi-agent coordination with tools
3. Enhanced response generation
4. Production integration patterns

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.qsr_pydantic_tools import (
    VisualCitationTool, GraphRAGEquipmentTool, SafetyValidationTool,
    QSRToolContext, VisualCitationQuery, GraphRAGQuery, SafetyValidationQuery
)

from tools.agent_tool_integration import (
    AgentToolCoordinator, ToolEnhancedResponseBuilder,
    create_tool_enhanced_agent_system
)

from voice_agent import (
    VoiceResponse, ConversationContext, AgentType, 
    ConversationIntent, VoiceState
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================================================================
# EXAMPLE 1: BASIC TOOL USAGE
# ===============================================================================

async def example_basic_visual_citation_tool():
    """Basic usage of visual citation tool with existing services"""
    
    print("📖 Example 1: Basic Visual Citation Tool Usage")
    print("-" * 50)
    
    # Create tool context (would use real services in production)
    tool_context = QSRToolContext(
        session_id="example_session_1",
        uploaded_docs_path="uploaded_docs",
        enable_visual_citations=True
    )
    
    # Create visual citation tool
    citation_tool = VisualCitationTool(tool_context)
    
    # Create query
    query = VisualCitationQuery(
        query_text="Show me the fryer temperature control diagram",
        equipment_context=["taylor c602", "fryer"],
        citation_types=["diagram", "image"],
        safety_critical=False,
        max_results=5
    )
    
    # Execute tool
    result = await citation_tool.search_visual_citations(query)
    
    # Display results
    print(f"Found {result.total_found} citations in {result.search_time_ms:.2f}ms")
    print(f"Searched documents: {', '.join(result.source_documents)}")
    
    for i, citation in enumerate(result.citations):
        print(f"  {i+1}. {citation.get('description', 'N/A')} (confidence: {citation.get('confidence', 0):.2f})")
    
    return result

async def example_graph_rag_equipment_tool():
    """Graph-RAG equipment tool with existing Neo4j integration"""
    
    print("\n📖 Example 2: Graph-RAG Equipment Tool Usage")
    print("-" * 50)
    
    # Create tool context
    tool_context = QSRToolContext(
        session_id="example_session_2",
        enable_graph_context=True
    )
    
    # Create Graph-RAG tool
    graph_tool = GraphRAGEquipmentTool(tool_context)
    
    # Create query
    query = GraphRAGQuery(
        equipment_name="Taylor C602",
        query_context="I need to troubleshoot the fryer temperature control",
        include_relationships=True,
        max_depth=2
    )
    
    # Execute tool
    result = await graph_tool.query_equipment_context(query)
    
    # Display results
    print(f"Graph context confidence: {result.confidence_score:.2f}")
    print(f"Found {len(result.entities)} entities and {len(result.relationships)} relationships")
    print(f"Summary: {result.graph_summary}")
    
    if result.equipment_context:
        print(f"Equipment: {result.equipment_context.get('equipment_name', 'N/A')}")
        print(f"Type: {result.equipment_context.get('equipment_type', 'N/A')}")
    
    return result

# ===============================================================================
# EXAMPLE 2: MULTI-AGENT COORDINATION
# ===============================================================================

async def example_multi_agent_coordination():
    """Multi-agent coordination with tools"""
    
    print("\n📖 Example 3: Multi-Agent Coordination with Tools")
    print("-" * 50)
    
    # Create agent tool coordinator
    coordinator = AgentToolCoordinator()
    
    # Setup different agents with their tools
    session_id = "multi_agent_session"
    
    # Equipment agent
    equipment_context = coordinator.setup_agent_with_tools(
        agent_type=AgentType.EQUIPMENT,
        session_id=session_id
    )
    
    # Safety agent  
    safety_context = coordinator.setup_agent_with_tools(
        agent_type=AgentType.SAFETY,
        session_id=session_id
    )
    
    # Procedure agent
    procedure_context = coordinator.setup_agent_with_tools(
        agent_type=AgentType.PROCEDURE,
        session_id=session_id
    )
    
    print(f"Equipment Agent: {len(equipment_context.available_tools)} tools")
    print(f"Safety Agent: {len(safety_context.available_tools)} tools")
    print(f"Procedure Agent: {len(procedure_context.available_tools)} tools")
    
    # Simulate user query requiring multiple agents
    user_query = "How do I safely clean the Taylor C602 fryer?"
    
    # Equipment agent provides technical context
    equipment_result = await coordinator.execute_tool_for_agent(
        AgentType.EQUIPMENT,
        session_id,
        "graph_rag",
        GraphRAGQuery(
            equipment_name="Taylor C602",
            query_context=user_query,
            include_relationships=True
        )
    )
    
    # Safety agent validates safety compliance
    safety_result = await coordinator.execute_tool_for_agent(
        AgentType.SAFETY,
        session_id,
        "safety_validation",
        SafetyValidationQuery(
            content_to_validate="Clean fryer with hot oil and cleaning solution",
            equipment_mentioned=["taylor c602", "fryer"],
            context_critical=True
        )
    )
    
    print(f"Equipment tool execution: {equipment_result['success']}")
    print(f"Safety tool execution: {safety_result['success']}")
    
    if safety_result['success']:
        safety_data = safety_result['result']
        print(f"Safety risk level: {safety_data.risk_level}")
        print(f"Safety warnings: {len(safety_data.safety_warnings)}")
    
    return {
        'equipment_result': equipment_result,
        'safety_result': safety_result,
        'coordinator': coordinator
    }

# ===============================================================================
# EXAMPLE 3: ENHANCED RESPONSE GENERATION
# ===============================================================================

async def example_enhanced_response_generation():
    """Enhanced response generation with tool integration"""
    
    print("\n📖 Example 4: Enhanced Response Generation")
    print("-" * 50)
    
    # Create complete system
    coordinator, response_builder = await create_tool_enhanced_agent_system()
    
    # Create base response (from existing voice_agent.py)
    base_response = VoiceResponse(
        text_response="The Taylor C602 fryer should be cleaned daily. First, ensure the fryer is cool, then follow proper cleaning procedures.",
        detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
        confidence_score=0.9,
        equipment_mentioned="Taylor C602",
        safety_priority=True,
        response_type="procedural",
        suggested_follow_ups=["What cleaning supplies do I need?", "How often should I clean it?"]
    )
    
    # Create conversation context
    conversation_context = ConversationContext(
        current_topic="fryer cleaning",
        current_entity="Taylor C602",
        conversation_history=[
            {"role": "user", "content": "Tell me about the Taylor C602 fryer"},
            {"role": "assistant", "content": "The Taylor C602 is a commercial fryer..."}
        ]
    )
    
    # Build enhanced response
    enhanced_response = await response_builder.build_enhanced_response(
        agent_type=AgentType.EQUIPMENT,
        session_id="enhanced_session",
        base_response=base_response,
        query_text="How do I clean the Taylor C602 fryer?",
        conversation_context=conversation_context,
        auto_enhance=True
    )
    
    # Display enhanced response
    print(f"Original response length: {len(base_response.text_response)} chars")
    print(f"Enhanced response type: {type(enhanced_response).__name__}")
    print(f"Primary agent: {enhanced_response.primary_agent.value}")
    print(f"Safety priority: {enhanced_response.safety_priority}")
    print(f"Visual citations: {len(enhanced_response.visual_citations.citations)}")
    
    # Show safety warnings if any
    if enhanced_response.safety_warnings:
        print(f"Safety warnings: {len(enhanced_response.safety_warnings)}")
        for warning in enhanced_response.safety_warnings[:2]:
            print(f"  - {warning}")
    
    return enhanced_response

# ===============================================================================
# EXAMPLE 4: PRODUCTION INTEGRATION PATTERN
# ===============================================================================

async def example_production_integration():
    """Production integration pattern with existing voice_agent.py"""
    
    print("\n📖 Example 5: Production Integration Pattern")
    print("-" * 50)
    
    # This shows how to integrate with existing voice_agent.py
    
    # Step 1: Initialize tool system with existing services
    # (In production, these would be your real services)
    coordinator, response_builder = await create_tool_enhanced_agent_system()
    
    # Step 2: Create enhanced voice processing function
    async def process_voice_with_tools(
        user_query: str,
        session_id: str,
        agent_type: AgentType = AgentType.GENERAL,
        conversation_context: Optional[ConversationContext] = None
    ) -> Dict[str, Any]:
        """Enhanced voice processing with tool integration"""
        
        # This would call your existing voice_agent.py logic
        # For demo, we'll create a mock response
        base_response = VoiceResponse(
            text_response=f"Processing query: {user_query}",
            detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
            confidence_score=0.8,
            should_continue_listening=True,
            next_voice_state=VoiceState.LISTENING,
            context_updates={},
            conversation_complete=False
        )
        
        # Enhance response with tools
        enhanced_response = await response_builder.build_enhanced_response(
            agent_type=agent_type,
            session_id=session_id,
            base_response=base_response,
            query_text=user_query,
            conversation_context=conversation_context,
            auto_enhance=True
        )
        
        # Return both legacy and enhanced formats
        return {
            'legacy_response': base_response.dict(),
            'enhanced_response': enhanced_response.dict(),
            'tool_enhanced': True,
            'visual_citations': enhanced_response.visual_citations.citations,
            'safety_priority': enhanced_response.safety_priority
        }
    
    # Step 3: Use enhanced processing
    result = await process_voice_with_tools(
        user_query="How do I troubleshoot the fryer temperature?",
        session_id="production_session",
        agent_type=AgentType.EQUIPMENT
    )
    
    print(f"Tool enhancement: {result['tool_enhanced']}")
    print(f"Visual citations: {len(result['visual_citations'])}")
    print(f"Safety priority: {result['safety_priority']}")
    
    return result

# ===============================================================================
# EXAMPLE 5: CONVERSATION CONTEXT INTEGRATION
# ===============================================================================

async def example_conversation_context_integration():
    """Conversation context integration with tools"""
    
    print("\n📖 Example 6: Conversation Context Integration")
    print("-" * 50)
    
    # Create coordinator
    coordinator = AgentToolCoordinator()
    
    # Simulate conversation flow
    session_id = "context_session"
    
    # Initial context
    context = ConversationContext(
        current_topic="equipment troubleshooting",
        current_entity="Taylor C602",
        conversation_history=[
            {"role": "user", "content": "I'm having trouble with the fryer"},
            {"role": "assistant", "content": "I can help with fryer troubleshooting..."}
        ]
    )
    
    # Setup agent with context
    agent_context = coordinator.setup_agent_with_tools(
        agent_type=AgentType.EQUIPMENT,
        session_id=session_id,
        conversation_context=context
    )
    
    # Execute context-aware tool
    from tools.qsr_pydantic_tools import ContextEnhancementQuery
    
    context_result = await coordinator.execute_tool_for_agent(
        AgentType.EQUIPMENT,
        session_id,
        "context_enhancement",
        ContextEnhancementQuery(
            current_query="What should I check next?",
            conversation_history=context.conversation_history,
            enhance_equipment_context=True,
            enhance_graph_context=True,
            session_id=session_id
        )
    )
    
    if context_result['success']:
        enhancement = context_result['result']
        print(f"Context score: {enhancement.context_score:.2f}")
        print(f"Equipment continuity: {enhancement.equipment_continuity}")
        print(f"Topic continuity: {', '.join(enhancement.topic_continuity)}")
        
        if enhancement.recommendations:
            print("Recommendations:")
            for rec in enhancement.recommendations:
                print(f"  - {rec}")
    
    return context_result

# ===============================================================================
# MAIN EXAMPLE RUNNER
# ===============================================================================

async def run_all_examples():
    """Run all usage examples"""
    
    print("🚀 PydanticAI Tools Usage Examples")
    print("=" * 80)
    
    examples = [
        example_basic_visual_citation_tool,
        example_graph_rag_equipment_tool,
        example_multi_agent_coordination,
        example_enhanced_response_generation,
        example_production_integration,
        example_conversation_context_integration
    ]
    
    results = {}
    
    for example in examples:
        try:
            result = await example()
            results[example.__name__] = result
            print("✅ Success\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
            results[example.__name__] = {'error': str(e)}
    
    print("=" * 80)
    print("🎉 Examples completed!")
    print(f"Successfully ran {len([r for r in results.values() if 'error' not in r])}/{len(examples)} examples")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_all_examples())