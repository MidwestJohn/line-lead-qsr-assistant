#!/usr/bin/env python3
"""
Context-Aware Query Service
Implements hybrid retrieval with document context and hierarchical relationships
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# AI/ML imports
from openai import OpenAI

# Local imports
from .neo4j_service import Neo4jService

logger = logging.getLogger(__name__)

class ContextAwareQueryService:
    """
    Context-aware query service that combines:
    - Specific entity matches
    - Document-level context summaries  
    - Hierarchical relationship traversal
    - Semantic similarity at document level
    """
    
    def __init__(self):
        self.neo4j_service = Neo4jService()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Context templates for different query types
        self.context_templates = {
            "equipment_maintenance": {
                "prefix": "For QSR line lead performing equipment maintenance:",
                "context_fields": ["equipment_focus", "maintenance_schedules", "safety_protocols", "critical_temperatures"],
                "hierarchy_path": "Manual > Equipment > Maintenance Procedure"
            },
            "safety_protocol": {
                "prefix": "For QSR safety compliance:",
                "context_fields": ["safety_protocols", "brand_context", "equipment_focus"],
                "hierarchy_path": "Safety Manual > Equipment > Safety Protocol"
            },
            "cleaning_procedure": {
                "prefix": "For QSR cleaning and sanitation:",
                "context_fields": ["key_procedures", "safety_protocols", "equipment_focus"],
                "hierarchy_path": "Cleaning Guide > Equipment > Cleaning Procedure"
            },
            "troubleshooting": {
                "prefix": "For QSR equipment troubleshooting:",
                "context_fields": ["equipment_focus", "key_procedures", "critical_temperatures"],
                "hierarchy_path": "Service Manual > Equipment > Troubleshooting"
            },
            "general": {
                "prefix": "For QSR line lead:",
                "context_fields": ["equipment_focus", "purpose", "target_audience"],
                "hierarchy_path": "Manual > Information"
            }
        }
        
    async def process_context_aware_query(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Process query with context-aware retrieval and response generation
        
        Args:
            query: User query
            max_results: Maximum number of results to return
            
        Returns:
            Context-aware response with hierarchical information
        """
        
        logger.info(f"Processing context-aware query: {query[:100]}...")
        
        try:
            # 1. Classify query type
            query_type = await self._classify_query_type(query)
            
            # 2. Retrieve relevant entities with context
            entity_results = await self._retrieve_entities_with_context(query, max_results)
            
            # 3. Retrieve document-level context
            document_context = await self._retrieve_document_context(entity_results)
            
            # 4. Traverse hierarchical relationships
            hierarchical_context = await self._traverse_hierarchical_relationships(entity_results)
            
            # 5. Generate context-aware response
            response = await self._generate_context_aware_response(
                query, query_type, entity_results, document_context, hierarchical_context
            )
            
            return {
                "status": "success",
                "query": query,
                "query_type": query_type,
                "response": response,
                "context_sources": {
                    "entities_found": len(entity_results),
                    "documents_referenced": len(document_context),
                    "hierarchical_levels": len(set(h.get('hierarchy_level', 0) for h in hierarchical_context))
                },
                "entity_matches": entity_results,
                "document_context": document_context,
                "hierarchical_context": hierarchical_context,
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Context-aware query processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "query": query
            }
    
    async def _classify_query_type(self, query: str) -> str:
        """Classify query type for appropriate context retrieval"""
        
        query_lower = query.lower()
        
        # Classification patterns
        if any(term in query_lower for term in ['clean', 'sanitize', 'wash', 'hygiene']):
            return "cleaning_procedure"
        elif any(term in query_lower for term in ['maintain', 'service', 'repair', 'maintenance']):
            return "equipment_maintenance"
        elif any(term in query_lower for term in ['safe', 'safety', 'warning', 'caution', 'danger']):
            return "safety_protocol"
        elif any(term in query_lower for term in ['problem', 'issue', 'troubleshoot', 'error', 'fault']):
            return "troubleshooting"
        else:
            return "general"
    
    async def _retrieve_entities_with_context(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Retrieve entities with their document context"""
        
        try:
            if not self.neo4j_service.connected:
                await self.neo4j_service.connect()
            
            # Extract key terms from query
            key_terms = self._extract_key_terms(query)
            
            # Search for entities across all types
            with self.neo4j_service.driver.session() as session:
                # Build search query with multiple entity types
                search_conditions = []
                for term in key_terms:
                    search_conditions.append(f"toLower(e.canonical_name) CONTAINS toLower('{term}')")
                    search_conditions.append(f"toLower(e.entity_text) CONTAINS toLower('{term}')")
                    search_conditions.append(f"toLower(e.qsr_context) CONTAINS toLower('{term}')")
                
                where_clause = " OR ".join(search_conditions) if search_conditions else "true"
                
                query = f"""
                MATCH (e)
                WHERE (e:EQUIPMENT OR e:ENTITY OR e:PROCEDURE OR e:PROCESS OR e:TEMPERATURE OR e:QSR_SPECIFIC)
                AND ({where_clause})
                OPTIONAL MATCH (d:Document {{document_id: e.document_id}})
                RETURN e, d
                ORDER BY e.confidence DESC, e.hierarchy_level ASC
                LIMIT {max_results}
                """
                
                results = session.run(query)
                
                entities = []
                for record in results:
                    entity = dict(record['e']) if record['e'] else {}
                    document = dict(record['d']) if record['d'] else {}
                    
                    entity_with_context = {
                        **entity,
                        "document_context": document,
                        "relevance_score": self._calculate_relevance_score(entity, query)
                    }
                    entities.append(entity_with_context)
                
                # Sort by relevance score
                entities.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                
                return entities
                
        except Exception as e:
            logger.error(f"Entity retrieval failed: {e}")
            return []
    
    async def _retrieve_document_context(self, entity_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Retrieve document-level context for matched entities"""
        
        try:
            if not entity_results:
                return []
            
            # Get unique document IDs
            document_ids = list(set(
                entity.get('document_id') for entity in entity_results 
                if entity.get('document_id')
            ))
            
            if not document_ids:
                return []
            
            with self.neo4j_service.driver.session() as session:
                query = """
                MATCH (d:Document)
                WHERE d.document_id IN $document_ids
                RETURN d
                ORDER BY d.confidence_score DESC
                """
                
                results = session.run(query, document_ids=document_ids)
                
                documents = []
                for record in results:
                    doc = dict(record['d'])
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Document context retrieval failed: {e}")
            return []
    
    async def _traverse_hierarchical_relationships(self, entity_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traverse hierarchical relationships to get context"""
        
        try:
            if not entity_results:
                return []
            
            # Get entity canonical names
            entity_names = [entity.get('canonical_name') for entity in entity_results if entity.get('canonical_name')]
            
            if not entity_names:
                return []
            
            with self.neo4j_service.driver.session() as session:
                # Find hierarchical relationships
                query = """
                MATCH (child {canonical_name: $entity_name})-[r:BELONGS_TO*1..3]->(parent)
                RETURN child.canonical_name as child_name,
                       parent.canonical_name as parent_name,
                       parent.hierarchy_level as parent_level,
                       parent.entity_type as parent_type,
                       length(r) as hierarchy_distance
                ORDER BY hierarchy_distance
                """
                
                hierarchical_context = []
                
                for entity_name in entity_names:
                    results = session.run(query, entity_name=entity_name)
                    
                    for record in results:
                        hierarchical_context.append({
                            "child_entity": record['child_name'],
                            "parent_entity": record['parent_name'],
                            "parent_level": record['parent_level'],
                            "parent_type": record['parent_type'],
                            "hierarchy_distance": record['hierarchy_distance']
                        })
                
                return hierarchical_context
                
        except Exception as e:
            logger.error(f"Hierarchical traversal failed: {e}")
            return []
    
    async def _generate_context_aware_response(self, query: str, query_type: str,
                                               entity_results: List[Dict[str, Any]],
                                               document_context: List[Dict[str, Any]],
                                               hierarchical_context: List[Dict[str, Any]]) -> str:
        """Generate context-aware response using LLM"""
        
        # Get context template
        template = self.context_templates.get(query_type, self.context_templates["general"])
        
        # Build context information
        context_info = self._build_context_information(
            entity_results, document_context, hierarchical_context, template
        )
        
        # Create prompt with context
        prompt = f"""
        {template['prefix']}
        
        Query: {query}
        
        Document Context:
        {context_info['document_context']}
        
        Entity Information:
        {context_info['entity_context']}
        
        Hierarchical Context:
        {context_info['hierarchical_context']}
        
        Please provide a comprehensive response that:
        1. Directly answers the query with specific information
        2. Includes relevant document context and source
        3. Mentions hierarchical path when applicable
        4. Focuses on actionable information for QSR line leads
        5. Includes safety considerations if relevant
        6. Cites specific manual sections or procedures
        
        Format your response for a QSR line lead who needs clear, actionable guidance.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a QSR technical expert providing guidance to line leads. Always include document context and hierarchical information in your responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return f"I found relevant information about your query regarding {query}, but encountered an error generating the detailed response. Please try again."
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query for entity matching"""
        
        # Simple keyword extraction - can be enhanced with NLP
        import re
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'how', 'what', 'when', 'where', 'why', 'do', 'does', 'did'}
        
        # Extract words
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stop words and short words
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return key_terms[:10]  # Limit to top 10 terms
    
    def _calculate_relevance_score(self, entity: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for entity based on query"""
        
        score = 0.0
        query_lower = query.lower()
        
        # Check canonical name match
        canonical_name = entity.get('canonical_name', '').lower()
        if canonical_name in query_lower:
            score += 1.0
        
        # Check entity text match
        entity_text = entity.get('entity_text', '').lower()
        if entity_text in query_lower:
            score += 0.8
        
        # Check QSR context match
        qsr_context = entity.get('qsr_context', '').lower()
        common_terms = len(set(qsr_context.split()) & set(query_lower.split()))
        score += common_terms * 0.2
        
        # Boost score for higher confidence
        confidence = entity.get('confidence', 0.5)
        score *= confidence
        
        # Boost score for lower hierarchy levels (more specific)
        hierarchy_level = entity.get('hierarchy_level', 5)
        if hierarchy_level <= 3:
            score *= 1.2
        
        return score
    
    def _build_context_information(self, entity_results: List[Dict[str, Any]],
                                   document_context: List[Dict[str, Any]],
                                   hierarchical_context: List[Dict[str, Any]],
                                   template: Dict[str, Any]) -> Dict[str, str]:
        """Build formatted context information for prompt"""
        
        # Document context
        doc_context_parts = []
        for doc in document_context[:3]:  # Limit to top 3 documents
            doc_info = f"From {doc.get('brand_context', 'QSR')} {doc.get('filename', 'Manual')}"
            if doc.get('equipment_focus'):
                doc_info += f" > {doc.get('equipment_focus')}"
            if doc.get('purpose'):
                doc_info += f": {doc.get('purpose')[:200]}..."
            doc_context_parts.append(doc_info)
        
        document_context_str = "\n".join(doc_context_parts)
        
        # Entity context
        entity_context_parts = []
        for entity in entity_results[:5]:  # Limit to top 5 entities
            entity_info = f"- {entity.get('canonical_name', 'Unknown')}"
            if entity.get('entity_type'):
                entity_info += f" ({entity.get('entity_type')})"
            if entity.get('qsr_context'):
                entity_info += f": {entity.get('qsr_context')[:100]}..."
            entity_context_parts.append(entity_info)
        
        entity_context_str = "\n".join(entity_context_parts)
        
        # Hierarchical context
        hierarchical_parts = []
        for hier in hierarchical_context[:5]:  # Limit to top 5 relationships
            path = f"{hier.get('parent_entity', 'Unknown')} > {hier.get('child_entity', 'Unknown')}"
            hierarchical_parts.append(f"- {path}")
        
        hierarchical_context_str = "\n".join(hierarchical_parts)
        
        return {
            "document_context": document_context_str,
            "entity_context": entity_context_str,
            "hierarchical_context": hierarchical_context_str
        }