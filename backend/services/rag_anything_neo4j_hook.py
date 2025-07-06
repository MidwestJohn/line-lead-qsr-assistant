import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class RAGAnythingNeo4jHook:
    """Hooks into RAG-Anything processing to generate semantic Neo4j relationships."""
    
    def __init__(self, rag_service, neo4j_generator):
        self.rag_service = rag_service
        self.neo4j_generator = neo4j_generator
    
    async def hook_into_knowledge_graph_construction(self, processing_data: Dict) -> Dict[str, Any]:
        """Hook into RAG-Anything's knowledge graph construction stage."""
        
        try:
            # Extract entities and relationships from RAG-Anything processing
            entities = self._extract_entities_from_rag_anything(processing_data)
            relationships = self._extract_relationships_from_rag_anything(processing_data)
            
            # Process through semantic relationship generator
            semantic_data = self.neo4j_generator.process_rag_anything_entities(entities, relationships)
            
            if "error" in semantic_data:
                return semantic_data
            
            # Populate Neo4j with semantic graph
            neo4j_result = self.neo4j_generator.populate_neo4j_with_semantic_graph(semantic_data)
            
            return {
                "hook_successful": True,
                "entities_processed": len(entities),
                "relationships_processed": len(relationships),
                "semantic_data": semantic_data,
                "neo4j_result": neo4j_result,
                "integration_method": "rag_anything_neo4j_hook"
            }
            
        except Exception as e:
            logger.error(f"RAG-Anything Neo4j hook failed: {e}")
            return {"error": str(e)}
    
    def _extract_entities_from_rag_anything(self, processing_data: Dict) -> List[Dict]:
        """Extract entities from RAG-Anything internal processing data."""
        
        entities = []
        
        # Try different possible data structures from RAG-Anything
        if "entities" in processing_data:
            entities = processing_data["entities"]
        elif "nodes" in processing_data:
            entities = processing_data["nodes"]
        elif "multimodal_entities" in processing_data:
            entities = processing_data["multimodal_entities"]
        
        # Normalize entity format
        normalized_entities = []
        for entity in entities:
            if isinstance(entity, dict):
                normalized_entities.append({
                    "name": entity.get("name", entity.get("id", "unknown")),
                    "description": entity.get("description", entity.get("content", "")),
                    "properties": entity.get("properties", {}),
                    "multimodal_content": entity.get("multimodal_content", [])
                })
            elif isinstance(entity, str):
                normalized_entities.append({
                    "name": entity,
                    "description": "",
                    "properties": {},
                    "multimodal_content": []
                })
        
        return normalized_entities
    
    def _extract_relationships_from_rag_anything(self, processing_data: Dict) -> List[Dict]:
        """Extract relationships from RAG-Anything internal processing data."""
        
        relationships = []
        
        # Try different possible data structures
        if "relationships" in processing_data:
            relationships = processing_data["relationships"]
        elif "edges" in processing_data:
            relationships = processing_data["edges"]
        elif "cross_modal_relationships" in processing_data:
            relationships = processing_data["cross_modal_relationships"]
        
        # Normalize relationship format
        normalized_relationships = []
        for relationship in relationships:
            if isinstance(relationship, dict):
                normalized_relationships.append({
                    "source": relationship.get("source", relationship.get("from", "")),
                    "target": relationship.get("target", relationship.get("to", "")),
                    "description": relationship.get("description", relationship.get("type", "")),
                    "context": relationship.get("context", ""),
                    "properties": relationship.get("properties", {})
                })
        
        return normalized_relationships