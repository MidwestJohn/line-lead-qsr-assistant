from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SearchStrategy(ABC):
    @abstractmethod
    async def search(self, query: str, documents: List[Dict]) -> Dict[str, Any]:
        pass

class ExistingSearchStrategy(SearchStrategy):
    """Uses current sentence-transformers approach."""
    
    def __init__(self, search_engine):
        self.search_engine = search_engine
    
    async def search(self, query: str, documents: List[Dict]) -> Dict[str, Any]:
        # Use existing search engine
        if self.search_engine is None:
            raise RuntimeError("Search engine not initialized")
            
        results = self.search_engine.search(query, top_k=3)
        
        return {
            "results": results,
            "source": "existing_system",
            "method": "sentence_transformers"
        }

class RAGAnythingStrategy(SearchStrategy):
    """Uses new RAG-Anything approach."""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
    
    async def search(self, query: str, documents: List[Dict]) -> Dict[str, Any]:
        if not self.rag_service.initialized:
            raise RuntimeError("RAG-Anything service not initialized")
        
        result = await self.rag_service.search(query)
        
        return {
            "results": result["response"],
            "source": "rag_anything",
            "method": "multimodal_knowledge_graph"
        }

class HybridSearchStrategy(SearchStrategy):
    """Compares both strategies and returns both results."""
    
    def __init__(self, existing_strategy, rag_strategy):
        self.existing_strategy = existing_strategy
        self.rag_strategy = rag_strategy
    
    async def search(self, query: str, documents: List[Dict]) -> Dict[str, Any]:
        results = {}
        
        # Try existing strategy
        try:
            existing_result = await self.existing_strategy.search(query, documents)
            results["existing"] = existing_result
        except Exception as e:
            logger.error(f"Existing strategy failed: {e}")
            results["existing"] = {"error": str(e)}
        
        # Try RAG-Anything strategy
        try:
            rag_result = await self.rag_strategy.search(query, documents)
            results["rag_anything"] = rag_result
        except Exception as e:
            logger.error(f"RAG-Anything strategy failed: {e}")
            results["rag_anything"] = {"error": str(e)}
        
        return {
            "comparison": results,
            "source": "hybrid_comparison",
            "primary_result": results.get("rag_anything", results.get("existing"))
        }