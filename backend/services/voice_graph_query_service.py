#!/usr/bin/env python3
"""
Voice Graph Query Service
Integrates voice queries with Neo4j knowledge graph for context-aware conversations
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from .multimodal_citation_service import multimodal_citation_service

logger = logging.getLogger(__name__)

class VoiceGraphQueryService:
    """
    Service that connects voice queries to Neo4j knowledge graph for persistent context-aware conversations
    """
    
    def __init__(self, neo4j_service):
        self.neo4j_service = neo4j_service
        
        # Equipment detection patterns
        self.equipment_patterns = {
            "taylor": ["taylor", "c602", "c708", "ice cream machine", "soft serve"],
            "hobart": ["hobart", "hcm", "mixer"],
            "fryer": ["fryer", "frying", "deep fryer"],
            "grill": ["grill", "grilling", "griddle"],
            "oven": ["oven", "baking", "convection"],
            "freezer": ["freezer", "freezing", "walk-in"],
            "refrigerator": ["refrigerator", "cooler", "fridge"]
        }
        
        # Voice command patterns for navigation
        self.navigation_patterns = {
            "next_step": ["next step", "next", "continue", "what's next", "proceed"],
            "previous_step": ["previous step", "back", "go back", "last step", "previous"],
            "repeat_step": ["repeat", "say that again", "repeat step", "what was that"],
            "current_status": ["where am i", "current step", "what step", "status"],
            "start_over": ["start over", "begin", "restart", "from the beginning"],
            "list_steps": ["list steps", "show all steps", "what are the steps", "overview"]
        }
        
        # Context switching patterns
        self.context_patterns = {
            "switch_equipment": ["help with", "work on", "switch to", "now help with"],
            "what_equipment": ["what equipment", "which equipment", "current equipment"],
            "show_procedures": ["what procedures", "show procedures", "available procedures"],
            "safety_warnings": ["safety", "warnings", "precautions", "safety guidelines"]
        }
        
        # Conversation context state
        self.conversation_contexts = {}
    
    async def process_voice_query_with_graph_context(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Process voice query using Neo4j graph context for persistent conversation flow
        """
        try:
            query_lower = query.lower().strip()
            
            # Get or initialize conversation context
            context = self.get_conversation_context(session_id)
            
            # Analyze query type and intent
            query_analysis = await self._analyze_voice_query(query_lower, context)
            
            # Process based on query type
            if query_analysis["type"] == "equipment_selection":
                result = await self._handle_equipment_selection(query_analysis, session_id)
            elif query_analysis["type"] == "procedure_navigation":
                result = await self._handle_procedure_navigation(query_analysis, session_id)
            elif query_analysis["type"] == "context_query":
                result = await self._handle_context_query(query_analysis, session_id)
            elif query_analysis["type"] == "safety_query":
                result = await self._handle_safety_query(query_analysis, session_id)
            else:
                # General query with equipment context
                result = await self._handle_general_query_with_context(query, query_analysis, session_id)
            
            # Update conversation context
            await self._update_conversation_context(session_id, result)
            
            # Add multimodal citations to response
            if result.get("response"):
                result = await multimodal_citation_service.synchronize_voice_with_visuals(
                    result, timing_markers=None
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Voice graph query processing failed: {e}")
            return {
                "response": "I'm having trouble accessing the equipment information. Please try again.",
                "context_maintained": False,
                "error": str(e)
            }
    
    async def _analyze_voice_query(self, query: str, context: Dict) -> Dict[str, Any]:
        """
        Analyze voice query to determine intent and extract equipment/procedure information
        """
        analysis = {
            "type": "general",
            "equipment_detected": None,
            "procedure_detected": None,
            "navigation_command": None,
            "confidence": 0.5
        }
        
        # Check for equipment selection
        for equipment_type, patterns in self.equipment_patterns.items():
            if any(pattern in query for pattern in patterns):
                analysis["equipment_detected"] = equipment_type
                if any(switch_pattern in query for switch_pattern in self.context_patterns["switch_equipment"]):
                    analysis["type"] = "equipment_selection"
                    analysis["confidence"] = 0.9
                break
        
        # Check for navigation commands
        for nav_type, patterns in self.navigation_patterns.items():
            if any(pattern in query for pattern in patterns):
                analysis["navigation_command"] = nav_type
                analysis["type"] = "procedure_navigation"
                analysis["confidence"] = 0.95
                break
        
        # Check for context queries
        for context_type, patterns in self.context_patterns.items():
            if any(pattern in query for pattern in patterns):
                analysis["type"] = "context_query"
                analysis["context_request"] = context_type
                analysis["confidence"] = 0.9
                break
        
        # Check for safety queries
        if any(pattern in query for pattern in self.context_patterns["safety_warnings"]):
            analysis["type"] = "safety_query"
            analysis["confidence"] = 0.85
        
        # Check for procedure-related terms
        procedure_terms = ["cleaning", "maintenance", "service", "startup", "shutdown", "calibration"]
        for term in procedure_terms:
            if term in query:
                analysis["procedure_detected"] = term
                if analysis["type"] == "general":
                    analysis["type"] = "procedure_query"
                    analysis["confidence"] = 0.8
                break
        
        return analysis
    
    async def _handle_equipment_selection(self, analysis: Dict, session_id: str) -> Dict[str, Any]:
        """
        Handle equipment selection and context switching
        """
        equipment_type = analysis["equipment_detected"]
        
        if not self.neo4j_service.connected:
            return {
                "response": f"I'd like to help you with {equipment_type} equipment, but I can't access the equipment database right now.",
                "context_maintained": False
            }
        
        try:
            with self.neo4j_service.driver.session() as session:
                # Find equipment of the specified type
                equipment_query = """
                MATCH (e:Equipment)
                WHERE toLower(e.name) CONTAINS $equipment_type
                OPTIONAL MATCH (e)-[r:CONTAINS]->(c:Component)
                OPTIONAL MATCH (p:Procedure)-[pr:PROCEDURE_FOR]->(e)
                RETURN e.name as equipment_name, 
                       collect(DISTINCT c.name) as components,
                       collect(DISTINCT p.name) as procedures
                """
                
                result = session.run(equipment_query, equipment_type=equipment_type)
                equipment_data = [dict(record) for record in result]
                
                if equipment_data:
                    equipment = equipment_data[0]
                    equipment_name = equipment["equipment_name"]
                    procedures = [p for p in equipment["procedures"] if p]
                    components = [c for c in equipment["components"] if c]
                    
                    # Update conversation context
                    context = self.get_conversation_context(session_id)
                    context.update({
                        "current_equipment": equipment_name,
                        "equipment_type": equipment_type,
                        "available_procedures": procedures,
                        "equipment_components": components,
                        "context_timestamp": datetime.now().isoformat()
                    })
                    self.conversation_contexts[session_id] = context
                    
                    # Create voice-optimized response
                    response_parts = [f"Now helping you with the {equipment_name}."]
                    
                    if procedures:
                        response_parts.append(f"Available procedures include: {self._format_list_for_speech(procedures)}.")
                    
                    if components:
                        response_parts.append(f"This equipment contains: {self._format_list_for_speech(components)}.")
                    
                    response_parts.append("What would you like to do?")
                    
                    return {
                        "response": " ".join(response_parts),
                        "equipment_context": equipment_name,
                        "available_procedures": procedures,
                        "context_maintained": True,
                        "voice_optimized": True
                    }
                else:
                    return {
                        "response": f"I don't have information about {equipment_type} equipment in the system. Please check the equipment name.",
                        "context_maintained": False
                    }
                    
        except Exception as e:
            logger.error(f"Equipment selection failed: {e}")
            return {
                "response": f"I'm having trouble finding information about {equipment_type} equipment.",
                "context_maintained": False,
                "error": str(e)
            }
    
    async def _handle_procedure_navigation(self, analysis: Dict, session_id: str) -> Dict[str, Any]:
        """
        Handle navigation through multi-step procedures
        """
        navigation_command = analysis["navigation_command"]
        context = self.get_conversation_context(session_id)
        
        if not context.get("current_equipment"):
            return {
                "response": "Please select an equipment first by saying something like 'help me with the ice cream machine'.",
                "context_maintained": False
            }
        
        current_equipment = context["current_equipment"]
        
        try:
            with self.neo4j_service.driver.session() as session:
                if navigation_command == "next_step":
                    return await self._get_next_procedure_step(session, context, session_id)
                elif navigation_command == "previous_step":
                    return await self._get_previous_procedure_step(session, context, session_id)
                elif navigation_command == "repeat_step":
                    return await self._repeat_current_step(context)
                elif navigation_command == "current_status":
                    return await self._get_current_status(context)
                elif navigation_command == "start_over":
                    return await self._start_procedure_over(session, context, session_id)
                elif navigation_command == "list_steps":
                    return await self._list_all_steps(session, context)
                else:
                    return {
                        "response": "I didn't understand that navigation command. Try saying 'next step', 'previous step', or 'repeat that'.",
                        "context_maintained": True
                    }
                    
        except Exception as e:
            logger.error(f"Procedure navigation failed: {e}")
            return {
                "response": "I'm having trouble navigating the procedure steps. Please try again.",
                "context_maintained": True,
                "error": str(e)
            }
    
    async def _handle_context_query(self, analysis: Dict, session_id: str) -> Dict[str, Any]:
        """
        Handle queries about current context and status
        """
        context_request = analysis.get("context_request")
        context = self.get_conversation_context(session_id)
        
        if context_request == "what_equipment":
            if context.get("current_equipment"):
                return {
                    "response": f"You're currently working on the {context['current_equipment']}.",
                    "equipment_context": context["current_equipment"],
                    "context_maintained": True
                }
            else:
                return {
                    "response": "You haven't selected any equipment yet. Say something like 'help me with the ice cream machine' to get started.",
                    "context_maintained": False
                }
        
        elif context_request == "show_procedures":
            if context.get("available_procedures"):
                procedures = context["available_procedures"]
                response = f"Available procedures for the {context.get('current_equipment', 'current equipment')}: {self._format_list_for_speech(procedures)}."
                return {
                    "response": response,
                    "available_procedures": procedures,
                    "context_maintained": True
                }
            else:
                return {
                    "response": "No procedures are available for the current equipment.",
                    "context_maintained": True
                }
        
        else:
            return {
                "response": "I can tell you about your current equipment or available procedures. What would you like to know?",
                "context_maintained": True
            }
    
    async def _handle_safety_query(self, analysis: Dict, session_id: str) -> Dict[str, Any]:
        """
        Handle safety-related queries with multi-modal enhanced data
        """
        context = self.get_conversation_context(session_id)
        current_equipment = context.get("current_equipment")
        
        if not self.neo4j_service.connected:
            return {
                "response": "I can't access safety information right now. Please consult the equipment manual directly.",
                "context_maintained": True
            }
        
        try:
            with self.neo4j_service.driver.session() as session:
                # Enhanced safety query to use multi-modal data from New Crew Handbook
                safety_query = """
                MATCH (n)
                WHERE (n.name CONTAINS "safety" OR n.name CONTAINS "temperature" OR n.name CONTAINS "warning" OR n.name CONTAINS "procedure")
                AND n.document_source CONTAINS "New-Crew-Handbook"
                RETURN n.name as safety_item, 
                       n.description as safety_description, 
                       n.type as entity_type,
                       n.visual_refs as visual_refs,
                       n.page_refs as page_refs,
                       n.document_source as document
                ORDER BY size(coalesce(n.visual_refs, [])) DESC
                LIMIT 10
                """
                
                result = session.run(safety_query, equipment_name=current_equipment)
                safety_data = [dict(record) for record in result]
                
                if safety_data:
                    # Enhanced approach: Get actual safety content from source documents
                    from services.enhanced_document_retrieval_service import enhanced_document_retrieval_service
                    
                    # Retrieve source content for safety entities
                    safety_query_text = "safety procedures temperature requirements food safety guidelines"
                    retrieval_result = await enhanced_document_retrieval_service.retrieve_source_content_for_entities(
                        safety_data, safety_query_text, max_chunks=2
                    )
                    
                    equipment_text = f" for the {current_equipment}" if current_equipment else ""
                    
                    if retrieval_result["content_available"]:
                        # Use actual source content for safety guidelines
                        source_chunks = retrieval_result["source_content"]
                        visual_citations = retrieval_result["visual_citations"]
                        
                        response_parts = [f"Here are the safety guidelines{equipment_text}:"]
                        
                        # Add actual safety content from documents
                        for chunk in source_chunks:
                            content = chunk["content"]
                            if len(content) > 250:
                                content = content[:250] + "..."
                            response_parts.append(content)
                        
                        # Collect page references
                        page_references = []
                        for citation in visual_citations:
                            page_references.extend(citation.get("page_refs", []))
                        
                        # Add page references
                        if page_references:
                            unique_pages = list(set(page_references))
                            unique_pages.sort()
                            if len(unique_pages) <= 3:
                                response_parts.append(f"See pages {', '.join(map(str, unique_pages))} for complete safety procedures.")
                        
                        response_parts.append("Always follow these precautions when working with equipment.")
                        
                        return {
                            "response": " ".join(response_parts),
                            "source_content": [chunk["content"] for chunk in source_chunks],
                            "visual_citations": visual_citations,
                            "page_references": list(set(page_references)),
                            "multimodal_enhanced": True,
                            "context_maintained": True,
                            "priority": "high",
                            "content_source": "enhanced_retrieval"
                        }
                    else:
                        # Fallback to entity metadata if no source content
                        safety_items = []
                        page_references = []
                        
                        for item in safety_data:
                            safety_desc = item.get("safety_description") or item.get("item_description", "")
                            if safety_desc and len(safety_desc) > 20:
                                safety_items.append(safety_desc[:200] + "..." if len(safety_desc) > 200 else safety_desc)
                            
                            page_refs = item.get("page_refs") or []
                            page_references.extend(page_refs)
                        
                        response_parts = [f"Here are the safety guidelines{equipment_text}:"]
                        
                        if safety_items:
                            response_parts.extend(safety_items[:2])  # Top 2 items
                        
                        if page_references:
                            unique_pages = list(set(page_references))
                            unique_pages.sort()
                            response_parts.append(f"See pages {', '.join(map(str, unique_pages))} for complete details.")
                        
                        response_parts.append("Always follow these precautions when working with equipment.")
                        
                        return {
                            "response": " ".join(response_parts),
                            "safety_guidelines": safety_items,
                            "page_references": list(set(page_references)),
                            "multimodal_enhanced": True,
                            "context_maintained": True,
                            "priority": "high",
                            "content_source": "entity_metadata"
                        }
                else:
                    return {
                        "response": f"I don't have specific safety information{' for the ' + current_equipment if current_equipment else ''} in the system. Please refer to the equipment manual for safety guidelines.",
                        "context_maintained": True
                    }
                    
        except Exception as e:
            logger.error(f"Safety query failed: {e}")
            return {
                "response": "I'm having trouble accessing safety information. Please consult the equipment manual directly.",
                "context_maintained": True,
                "error": str(e)
            }
    
    async def _handle_general_query_with_context(self, query: str, analysis: Dict, session_id: str) -> Dict[str, Any]:
        """
        Handle general queries with equipment context from the graph, enhanced with multi-modal support
        """
        context = self.get_conversation_context(session_id)
        current_equipment = context.get("current_equipment")
        
        if not self.neo4j_service.connected:
            return {
                "response": "I can provide general assistance, but I can't access the equipment database right now.",
                "context_maintained": bool(current_equipment)
            }
        
        try:
            # Check if this is a temperature-related query
            query_lower = query.lower()
            is_temperature_query = any(term in query_lower for term in ["temperature", "temp", "degrees", "hot", "cold", "heating", "cooling"])
            is_safety_query = any(term in query_lower for term in ["safety", "safe", "danger", "warning", "precaution"])
            
            with self.neo4j_service.driver.session() as session:
                if is_temperature_query or is_safety_query:
                    # Enhanced query for temperature and safety across ALL documents
                    enhanced_query = """
                    MATCH (n)
                    WHERE (
                        n.name CONTAINS "temperature" OR 
                        n.name CONTAINS "safety" OR 
                        n.name CONTAINS "warning" OR
                        n.name CONTAINS "procedure" OR
                        n.name CONTAINS "temp" OR
                        n.name CONTAINS "heat" OR
                        n.name CONTAINS "food"
                    )
                    RETURN n.name as item_name, 
                           n.type as item_type,
                           n.description as item_description,
                           n.visual_refs as visual_refs,
                           n.page_refs as page_refs,
                           n.document_source as document_source,
                           n.multimodal_enhanced as enhanced
                    ORDER BY size(coalesce(n.visual_refs, [])) DESC
                    LIMIT 10
                    """
                    
                    result = session.run(enhanced_query)
                    items = [dict(record) for record in result]
                    
                    if items:
                        # Enhanced approach: Get actual source document content
                        from services.enhanced_document_retrieval_service import enhanced_document_retrieval_service
                        
                        # Retrieve source content for these entities
                        retrieval_result = await enhanced_document_retrieval_service.retrieve_source_content_for_entities(
                            items, query, max_chunks=3
                        )
                        
                        if retrieval_result["content_available"]:
                            # Use source content to generate natural response
                            source_chunks = retrieval_result["source_content"]
                            visual_citations = retrieval_result["visual_citations"]
                            
                            # Extract the most relevant content
                            content_snippets = []
                            page_refs = []
                            
                            for chunk in source_chunks[:2]:  # Top 2 most relevant chunks
                                content = chunk["content"]
                                # Clean up content for voice response
                                if len(content) > 300:
                                    content = content[:300] + "..."
                                content_snippets.append(content)
                            
                            # Collect page references from visual citations
                            for citation in visual_citations:
                                page_refs.extend(citation.get("page_refs", []))
                            
                            # Build natural language response
                            if is_temperature_query:
                                response_intro = "Here are the temperature requirements for food safety:"
                            else:
                                response_intro = "Here are the safety guidelines:"
                            
                            response_parts = [response_intro]
                            
                            # Add actual document content
                            for snippet in content_snippets:
                                response_parts.append(snippet)
                            
                            # Add page references if available
                            if page_refs:
                                unique_pages = list(set(page_refs))
                                unique_pages.sort()
                                if len(unique_pages) <= 3:
                                    response_parts.append(f"For complete details, see pages {', '.join(map(str, unique_pages))}.")
                            
                            return {
                                "response": " ".join(response_parts),
                                "source_content": content_snippets,
                                "page_references": list(set(page_refs)),
                                "visual_citations": visual_citations,
                                "multimodal_enhanced": True,
                                "context_maintained": True,
                                "query_type": "temperature" if is_temperature_query else "safety",
                                "content_source": "enhanced_retrieval"
                            }
                        else:
                            # Fallback to entity-based response if no source content
                            logger.warning("⚠️ No source content available, using entity metadata")
                            
                            response_parts = []
                            page_refs = []
                            
                            if is_temperature_query:
                                response_parts.append("Based on available information about temperature requirements:")
                            else:
                                response_parts.append("Based on available safety information:")
                            
                            # Use entity descriptions if available
                            for item in items[:3]:
                                item_desc = item.get("item_description", "")
                                if item_desc and len(item_desc) > 20:
                                    if len(item_desc) > 200:
                                        item_desc = item_desc[:200] + "..."
                                    response_parts.append(item_desc)
                                
                                # Collect page references
                                item_pages = item.get("page_refs") or []
                                page_refs.extend(item_pages)
                            
                            # Add page references
                            if page_refs:
                                unique_pages = list(set(page_refs))
                                unique_pages.sort()
                                response_parts.append(f"See pages {', '.join(map(str, unique_pages))} for complete details.")
                            
                            return {
                                "response": " ".join(response_parts),
                                "page_references": list(set(page_refs)),
                                "multimodal_enhanced": True,
                                "context_maintained": True,
                                "query_type": "temperature" if is_temperature_query else "safety",
                                "content_source": "entity_metadata"
                            }
                
                # Fallback to original context-aware search across ALL documents
                context_query = """
                MATCH (n)
                WHERE (
                    n.name CONTAINS $query_term OR 
                    coalesce(n.description, "") CONTAINS $query_term
                )
                RETURN n.name as item_name, 
                       n.type as item_type,
                       n.description as item_description,
                       n.visual_refs as visual_refs,
                       n.page_refs as page_refs,
                       n.document_source as document_source
                LIMIT 8
                """
                
                # Extract key terms from query
                query_terms = [term for term in query.lower().split() if len(term) > 3]
                
                results = []
                for term in query_terms[:3]:  # Limit to first 3 significant terms
                    result = session.run(context_query, 
                                       query_term=term, 
                                       equipment_name=current_equipment)
                    results.extend([dict(record) for record in result])
                
                if results:
                    # Process results to create contextual response
                    relevant_items = []
                    procedures = []
                    components = []
                    
                    for item in results:
                        item_types = item.get("item_types", [])
                        item_name = item.get("item_name")
                        
                        if "Procedure" in item_types:
                            procedures.append(item_name)
                        elif "Component" in item_types:
                            components.append(item_name)
                        else:
                            relevant_items.append(item_name)
                    
                    # Create context-aware response
                    response_parts = []
                    
                    if current_equipment:
                        response_parts.append(f"Based on your work with the {current_equipment}:")
                    
                    if procedures:
                        response_parts.append(f"Related procedures: {self._format_list_for_speech(procedures[:3])}.")
                    
                    if components:
                        response_parts.append(f"Related components: {self._format_list_for_speech(components[:3])}.")
                    
                    if relevant_items:
                        response_parts.append(f"Other relevant information: {self._format_list_for_speech(relevant_items[:2])}.")
                    
                    if not response_parts:
                        response_parts.append("I found some information related to your query.")
                    
                    response_parts.append("Would you like me to elaborate on any of these items?")
                    
                    return {
                        "response": " ".join(response_parts),
                        "context_maintained": bool(current_equipment),
                        "relevant_procedures": procedures,
                        "relevant_components": components,
                        "voice_optimized": True
                    }
                else:
                    context_response = f" for the {current_equipment}" if current_equipment else ""
                    return {
                        "response": f"I couldn't find specific information about that{context_response}. Could you be more specific about what you're looking for?",
                        "context_maintained": bool(current_equipment)
                    }
                    
        except Exception as e:
            logger.error(f"General query with context failed: {e}")
            return {
                "response": "I'm having trouble searching the equipment information. Please try rephrasing your question.",
                "context_maintained": bool(current_equipment),
                "error": str(e)
            }
    
    def get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation context for a session
        """
        return self.conversation_contexts.get(session_id, {
            "current_equipment": None,
            "equipment_type": None,
            "current_procedure": None,
            "procedure_step": 0,
            "available_procedures": [],
            "equipment_components": [],
            "conversation_history": [],
            "last_response": None,
            "context_timestamp": datetime.now().isoformat()
        })
    
    async def _update_conversation_context(self, session_id: str, result: Dict[str, Any]) -> None:
        """
        Update conversation context based on the result
        """
        context = self.get_conversation_context(session_id)
        
        # Update context with new information
        if result.get("equipment_context"):
            context["current_equipment"] = result["equipment_context"]
        
        if result.get("available_procedures"):
            context["available_procedures"] = result["available_procedures"]
        
        context["last_response"] = result.get("response")
        context["context_timestamp"] = datetime.now().isoformat()
        
        # Add to conversation history
        if "conversation_history" not in context:
            context["conversation_history"] = []
        
        context["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "response": result.get("response", "")[:100],  # Store first 100 chars
            "context_maintained": result.get("context_maintained", False)
        })
        
        # Keep only last 10 interactions
        context["conversation_history"] = context["conversation_history"][-10:]
        
        self.conversation_contexts[session_id] = context
    
    def _format_list_for_speech(self, items: List[str]) -> str:
        """
        Format a list of items for natural speech output
        """
        if not items:
            return ""
        elif len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return f"{', '.join(items[:-1])}, and {items[-1]}"
    
    async def _get_next_procedure_step(self, session, context: Dict, session_id: str) -> Dict[str, Any]:
        """Get the next step in the current procedure"""
        # Implementation for step navigation
        return {
            "response": "Next step functionality will be implemented with procedure step relationships.",
            "context_maintained": True
        }
    
    async def _get_previous_procedure_step(self, session, context: Dict, session_id: str) -> Dict[str, Any]:
        """Get the previous step in the current procedure"""
        return {
            "response": "Previous step functionality will be implemented with procedure step relationships.",
            "context_maintained": True
        }
    
    async def _repeat_current_step(self, context: Dict) -> Dict[str, Any]:
        """Repeat the current procedure step"""
        last_response = context.get("last_response")
        if last_response:
            return {
                "response": f"Let me repeat that: {last_response}",
                "context_maintained": True
            }
        else:
            return {
                "response": "I don't have a previous step to repeat. Please specify what you'd like me to repeat.",
                "context_maintained": True
            }
    
    async def _get_current_status(self, context: Dict) -> Dict[str, Any]:
        """Get current procedure status"""
        current_equipment = context.get("current_equipment")
        current_procedure = context.get("current_procedure")
        step = context.get("procedure_step", 0)
        
        if current_equipment:
            status_parts = [f"You're working on the {current_equipment}."]
            if current_procedure:
                status_parts.append(f"Current procedure: {current_procedure}, step {step}.")
            else:
                status_parts.append("No specific procedure is currently active.")
        else:
            status_parts = ["No equipment is currently selected."]
        
        return {
            "response": " ".join(status_parts),
            "context_maintained": True,
            "current_status": {
                "equipment": current_equipment,
                "procedure": current_procedure,
                "step": step
            }
        }
    
    async def _start_procedure_over(self, session, context: Dict, session_id: str) -> Dict[str, Any]:
        """Start a procedure from the beginning"""
        context["procedure_step"] = 0
        return {
            "response": "Starting the procedure from the beginning.",
            "context_maintained": True,
            "procedure_step": 0
        }
    
    async def _list_all_steps(self, session, context: Dict) -> Dict[str, Any]:
        """List all steps in the current procedure"""
        return {
            "response": "Step listing functionality will be implemented with procedure step relationships.",
            "context_maintained": True
        }

# Global instance
voice_graph_query_service = None