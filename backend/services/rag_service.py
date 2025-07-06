import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
import datetime
from dotenv import load_dotenv

# Load RAG environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.rag'))

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.enabled = os.getenv('USE_RAG_ANYTHING', 'false').lower() == 'true'
        self.fallback_enabled = os.getenv('FALLBACK_TO_EXISTING', 'true').lower() == 'true'
        self.rag_instance = None
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize RAG-Anything service. Returns True if successful."""
        if not self.enabled:
            logger.info("RAG-Anything disabled via environment variable")
            return False
            
        try:
            # Use our custom QSR Graph RAG service instead of LightRAG
            # This avoids dependency compatibility issues
            logger.info("Initializing QSR Graph RAG service...")
            
            # Import our custom graph RAG service
            from graph_rag_service import QSRGraphRAGService
            
            # Get storage path
            storage_path = os.getenv('RAG_STORAGE_PATH', './data/rag_storage')
            os.makedirs(storage_path, exist_ok=True)
            
            # Initialize our custom QSR Graph RAG
            self.rag_instance = QSRGraphRAGService(
                llm_model="gpt-4o-mini",
                embedding_model="text-embedding-3-small",
                graph_store_path=storage_path
            )
            
            # Test Neo4j connection if configured
            if self._neo4j_available():
                logger.info("Neo4j connection available - knowledge graph ready")
            else:
                logger.warning("Neo4j not available - using local graph storage")
            
            self.initialized = True
            logger.info("QSR Graph RAG service initialized successfully")
            return True
            
        except ImportError as e:
            logger.error(f"LightRAG import failed: {e}")
            if self.fallback_enabled:
                logger.info("Using fallback mode - will use existing search engine")
                self.initialized = True
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to initialize LightRAG: {e}")
            if self.fallback_enabled:
                logger.info("Using fallback mode - will use existing search engine")
                self.initialized = True
                return True
            return False
    
    def _neo4j_available(self) -> bool:
        """Check if Neo4j connection is available (Aura-compatible)."""
        try:
            from neo4j import GraphDatabase
            uri = os.getenv('NEO4J_URI')
            username = os.getenv('NEO4J_USERNAME')
            password = os.getenv('NEO4J_PASSWORD')
            
            if not all([uri, username, password]):
                return False
                
            # Aura-compatible driver configuration
            driver = GraphDatabase.driver(
                uri, 
                auth=(username, password),
                max_connection_lifetime=30 * 60,
                connection_acquisition_timeout=60
            )
            driver.verify_connectivity()
            driver.close()
            return True
        except Exception as e:
            logger.debug(f"Neo4j connection test failed: {e}")
            return False
    
    async def process_document(self, file_path: str, content: str) -> Dict[str, Any]:
        """Process document through RAG-Anything pipeline."""
        if not self.initialized:
            raise RuntimeError("RAG service not initialized")
            
        if self.rag_instance is None:
            # Fallback mode - just acknowledge the document
            logger.info(f"Processing document in fallback mode: {file_path}")
            return {
                "status": "success",
                "processed_with": "fallback",
                "file_path": file_path,
                "content_length": len(content),
                "note": "Using fallback mode - knowledge graph not populated"
            }
            
        try:
            # Process through QSR Graph RAG
            logger.info(f"Processing document through QSR Graph RAG: {file_path}")
            
            # Create a simple documents_db structure for this document
            doc_id = f"doc_{hash(file_path)}"
            documents_db = {
                doc_id: {
                    'text_content': content,
                    'original_filename': os.path.basename(file_path),
                    'upload_timestamp': str(datetime.datetime.now()),
                    'file_size': len(content),
                    'pages_count': 1
                }
            }
            
            # Process the document
            success = self.rag_instance.add_documents(documents_db)
            
            # Also populate Neo4j if available
            if self._neo4j_available():
                await self._populate_neo4j_from_content(content, file_path)
            
            return {
                "status": "success" if success else "error",
                "processed_with": "qsr_graph_rag", 
                "file_path": file_path,
                "content_length": len(content),
                "neo4j_populated": self._neo4j_available(),
                "knowledge_graph_built": success
            }
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path
            }
    
    async def search(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Search using RAG-Anything."""
        if not self.initialized:
            raise RuntimeError("RAG service not initialized")
        
        if self.rag_instance is None:
            # Fallback mode - return indication to use existing search
            return {
                "response": None,
                "source": "fallback",
                "mode": mode,
                "use_existing_search": True
            }
            
        try:
            # Query through QSR Graph RAG
            result = self.rag_instance.query_knowledge_graph(query)
            
            if "error" in result:
                raise Exception(result["error"])
            
            return {
                "response": result["response"],
                "source": "qsr_graph_rag",
                "mode": mode,
                "use_existing_search": False,
                "entities_mentioned": result.get("entities_mentioned", []),
                "source_documents": result.get("source_documents", [])
            }
        except Exception as e:
            logger.error(f"LightRAG search failed: {e}")
            # Return fallback indication on error
            return {
                "response": None,
                "source": "fallback_on_error",
                "mode": mode,
                "use_existing_search": True,
                "error": str(e)
            }
    
    async def _populate_neo4j_from_content(self, content: str, file_path: str):
        """Populate Neo4j database with extracted knowledge graph data."""
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv('NEO4J_URI')
            username = os.getenv('NEO4J_USERNAME')
            password = os.getenv('NEO4J_PASSWORD')
            
            if not all([uri, username, password]):
                logger.warning("Neo4j credentials not configured")
                return
            
            # Connect to Neo4j
            driver = GraphDatabase.driver(
                uri, 
                auth=(username, password),
                max_connection_lifetime=30 * 60,
                connection_acquisition_timeout=60
            )
            
            # Extract entities and relationships from content using simple patterns
            # This is a simplified approach - in production you'd use more sophisticated NLP
            entities = self._extract_entities_simple(content)
            relationships = self._extract_relationships_simple(content)
            
            # Populate Neo4j
            with driver.session() as session:
                # Create document node
                session.run(
                    "MERGE (d:Document {path: $path, content_length: $length})",
                    path=file_path,
                    length=len(content)
                )
                
                # Create entity nodes
                for entity in entities:
                    session.run(
                        "MERGE (e:Entity {name: $name, type: $type}) "
                        "MERGE (d:Document {path: $path}) "
                        "MERGE (d)-[:CONTAINS]->(e)",
                        name=entity['name'],
                        type=entity['type'],
                        path=file_path
                    )
                
                # Create relationships
                for rel in relationships:
                    session.run(
                        "MATCH (e1:Entity {name: $from}) "
                        "MATCH (e2:Entity {name: $to}) "
                        "MERGE (e1)-[:RELATES {type: $rel_type}]->(e2)",
                        **rel
                    )
            
            driver.close()
            logger.info(f"Populated Neo4j with {len(entities)} entities and {len(relationships)} relationships")
            
        except Exception as e:
            logger.error(f"Failed to populate Neo4j: {e}")
    
    def _extract_entities_simple(self, content: str) -> List[Dict[str, str]]:
        """Extract entities using simple pattern matching."""
        entities = []
        content_lower = content.lower()
        
        # QSR equipment patterns
        equipment_patterns = [
            'ice cream machine', 'soft serve machine', 'ice machine',
            'fryer', 'grill', 'oven', 'freezer', 'dishwasher',
            'coffee machine', 'blender', 'mixer'
        ]
        
        for equipment in equipment_patterns:
            if equipment in content_lower:
                entities.append({
                    'name': equipment.title(),
                    'type': 'EQUIPMENT'
                })
        
        # Brand patterns
        brand_patterns = ['taylor', 'frymaster', 'hobart', 'prince castle']
        for brand in brand_patterns:
            if brand in content_lower:
                entities.append({
                    'name': brand.title(),
                    'type': 'BRAND'
                })
        
        # Procedure patterns
        procedure_patterns = ['cleaning', 'maintenance', 'troubleshooting', 'calibration']
        for procedure in procedure_patterns:
            if procedure in content_lower:
                entities.append({
                    'name': procedure.title(),
                    'type': 'PROCEDURE'
                })
        
        return entities
    
    def _extract_relationships_simple(self, content: str) -> List[Dict[str, str]]:
        """Extract relationships using simple pattern matching."""
        relationships = []
        content_lower = content.lower()
        
        # Simple relationship patterns
        if 'ice cream machine' in content_lower and 'cleaning' in content_lower:
            relationships.append({
                'from': 'Ice Cream Machine',
                'to': 'Cleaning',
                'rel_type': 'REQUIRES'
            })
        
        if 'taylor' in content_lower and 'ice cream machine' in content_lower:
            relationships.append({
                'from': 'Taylor',
                'to': 'Ice Cream Machine',
                'rel_type': 'MANUFACTURES'
            })
        
        return relationships
    
    def health_check(self) -> Dict[str, Any]:
        """Return health status of RAG service."""
        return {
            "enabled": self.enabled,
            "initialized": self.initialized,
            "qsr_graph_rag_active": self.rag_instance is not None,
            "neo4j_available": self._neo4j_available(),
            "fallback_enabled": self.fallback_enabled,
            "storage_path": os.getenv('RAG_STORAGE_PATH', './data/rag_storage'),
            "service_type": "QSRGraphRAG" if self.rag_instance else "fallback"
        }

# Global instance
rag_service = RAGService()