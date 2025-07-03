import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from dotenv import load_dotenv

# Load RAG environment
load_dotenv('backend/.env.rag')

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
            # Import here to avoid startup errors if packages not installed
            from raganything import RAGAnything
            from lightrag import LightRAG
            
            # Initialize LightRAG with Neo4j
            self.rag_instance = LightRAG(
                working_dir=os.getenv('RAG_STORAGE_PATH', './rag_storage'),
                kg_storage="Neo4JStorage" if self._neo4j_available() else "NetworkXStorage",
                vector_storage="Neo4jVectorStorage" if self._neo4j_available() else "NanoVectorDBStorage",
                document_storage="Neo4jKVStorage" if self._neo4j_available() else "JsonKVStorage"
            )
            
            await self.rag_instance.initialize_storages()
            await self.rag_instance.initialize_pipeline_status()
            
            self.initialized = True
            logger.info("RAG-Anything service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG-Anything: {e}")
            if not self.fallback_enabled:
                raise
            return False
    
    def _neo4j_available(self) -> bool:
        """Check if Neo4j connection is available."""
        try:
            from neo4j import GraphDatabase
            uri = os.getenv('NEO4J_URI')
            username = os.getenv('NEO4J_USERNAME')
            password = os.getenv('NEO4J_PASSWORD')
            
            if not all([uri, username, password]):
                return False
                
            driver = GraphDatabase.driver(uri, auth=(username, password))
            driver.verify_connectivity()
            driver.close()
            return True
        except Exception:
            return False
    
    async def process_document(self, file_path: str, content: str) -> Dict[str, Any]:
        """Process document through RAG-Anything pipeline."""
        if not self.initialized:
            raise RuntimeError("RAG service not initialized")
            
        try:
            # Process through RAG-Anything
            await self.rag_instance.ainsert(content)
            
            return {
                "status": "success",
                "processed_with": "rag_anything",
                "file_path": file_path,
                "content_length": len(content)
            }
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise
    
    async def search(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Search using RAG-Anything."""
        if not self.initialized:
            raise RuntimeError("RAG service not initialized")
            
        try:
            response = await self.rag_instance.aquery(query, param={"mode": mode})
            
            return {
                "response": response,
                "source": "rag_anything",
                "mode": mode
            }
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Return health status of RAG service."""
        return {
            "enabled": self.enabled,
            "initialized": self.initialized,
            "neo4j_available": self._neo4j_available(),
            "fallback_enabled": self.fallback_enabled,
            "storage_path": os.getenv('RAG_STORAGE_PATH', './rag_storage')
        }

# Global instance
rag_service = RAGService()