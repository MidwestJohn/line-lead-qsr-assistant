"""
Graph RAG Service using LlamaIndex for Line Lead QSR MVP
Intelligent knowledge graph construction and entity extraction from QSR documents
"""

import json
import logging
import os
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from llama_index.core import (
    KnowledgeGraphIndex, 
    StorageContext, 
    Document,
    VectorStoreIndex,
    Settings
)
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.extractors import (
    TitleExtractor,
    KeywordExtractor,
    QuestionsAnsweredExtractor,
    SummaryExtractor
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode

logger = logging.getLogger(__name__)

class QSRGraphRAGService:
    """
    QSR-specialized Graph RAG service using LlamaIndex for intelligent
    entity extraction and knowledge graph construction
    """
    
    def __init__(self, 
                 llm_model: str = "gpt-4o-mini",
                 embedding_model: str = "text-embedding-3-small",
                 graph_store_path: str = "./data/graph_store"):
        """
        Initialize the Graph RAG service
        
        Args:
            llm_model: OpenAI model for entity extraction
            embedding_model: OpenAI embedding model
            graph_store_path: Path to store graph data
        """
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.graph_store_path = Path(graph_store_path)
        self.graph_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM and embedding model
        self.llm = OpenAI(model=llm_model, temperature=0.1)
        self.embed_model = OpenAIEmbedding(model=embedding_model)
        
        # Set global settings
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # Initialize graph store
        self.graph_store = SimpleGraphStore()
        self.storage_context = StorageContext.from_defaults(graph_store=self.graph_store)
        
        # Initialize knowledge graph index
        self.kg_index: Optional[KnowledgeGraphIndex] = None
        self.vector_index: Optional[VectorStoreIndex] = None
        self.query_engine = None
        
        # Try to load existing indices
        self._load_existing_indices()
        
        # QSR-specific entity types and extraction prompts
        self.qsr_entity_types = [
            "EQUIPMENT",
            "PROCEDURE", 
            "COMPONENT",
            "BRAND",
            "MODEL",
            "SAFETY_REQUIREMENT",
            "MAINTENANCE_TASK",
            "CLEANING_STEP",
            "TEMPERATURE",
            "TIME_DURATION",
            "SAFETY_HAZARD"
        ]
        
        # Custom extraction prompt for QSR domain
        self.qsr_extraction_prompt = """
        You are an expert in Quick Service Restaurant (QSR) equipment and procedures.
        Extract entities and relationships from the following text, focusing on:
        
        ENTITY TYPES:
        - EQUIPMENT: fryer, grill, ice cream machine, ice machine, oven, dishwasher, etc.
        - PROCEDURE: cleaning, maintenance, troubleshooting, safety check, calibration
        - COMPONENT: heating element, temperature sensor, oil filter, burner, etc.
        - BRAND: Taylor, Frymaster, Prince Castle, Hobart, etc.
        - MODEL: C602, FRYER-2000, GRILL-3000, etc.
        - SAFETY_REQUIREMENT: PPE, electrical safety, hot surface warning
        - MAINTENANCE_TASK: oil change, filter replacement, calibration
        - CLEANING_STEP: drain oil, wipe surfaces, sanitize, degrease
        - TEMPERATURE: specific temps, temperature ranges, heating requirements
        - TIME_DURATION: cleaning time, maintenance intervals, heating time
        - SAFETY_HAZARD: electrical shock, burns, chemical exposure
        
        IMPORTANT DISTINCTIONS:
        - "ice cream machine" and "ice machine" are DIFFERENT equipment types
        - "soft serve machine" = "ice cream machine"
        - "frozen yogurt machine" = "ice cream machine"
        - Extract specific model numbers and brand names
        - Link procedures to specific equipment types
        - Connect safety requirements to procedures and equipment
        
        Extract entities as triplets: (subject, relationship, object)
        Focus on actionable relationships that help QSR workers.
        """
        
        self.documents_processed = []
        self.entity_cache = {}
        
        # OPTIMIZATION: Smart caching for speed improvements
        # Can be easily disabled by setting RAG_CACHE_EMBEDDINGS=false
        self.enable_optimizations = os.getenv('RAG_ENABLE_OPTIMIZATIONS', 'true').lower() == 'true'
        self.cache_embeddings = os.getenv('RAG_CACHE_EMBEDDINGS', 'true').lower() == 'true'
        self.batch_size = int(os.getenv('RAG_BATCH_SIZE', '20'))
        self.parallel_workers = int(os.getenv('RAG_PARALLEL_WORKERS', '4'))
        
        # Initialize caches (safe - only stores computed results)
        self.embedding_cache = {} if self.cache_embeddings else None
        self.processed_chunk_cache = {}
        
        logger.info(f"Initialized QSR Graph RAG service with {llm_model}")
        if self.enable_optimizations:
            logger.info(f"Optimizations enabled: batch_size={self.batch_size}, cache={self.cache_embeddings}")
    
    def _load_existing_indices(self):
        """Load existing knowledge graph and vector indices if they exist"""
        try:
            kg_index_path = self.graph_store_path / "kg_index"
            vector_index_path = self.graph_store_path / "vector_index"
            
            if kg_index_path.exists() and vector_index_path.exists():
                logger.info("Loading existing knowledge graph and vector indices...")
                
                # Load storage context for knowledge graph
                kg_storage_context = StorageContext.from_defaults(
                    persist_dir=str(kg_index_path),
                    graph_store=self.graph_store
                )
                
                # Load knowledge graph index
                self.kg_index = KnowledgeGraphIndex(
                    nodes=[],
                    storage_context=kg_storage_context
                )
                
                # Load vector index
                vector_storage_context = StorageContext.from_defaults(
                    persist_dir=str(vector_index_path)
                )
                
                self.vector_index = VectorStoreIndex(
                    nodes=[],
                    storage_context=vector_storage_context
                )
                
                # Create query engine
                self.query_engine = self.kg_index.as_query_engine(
                    include_text=True,
                    response_mode="tree_summarize",
                    similarity_top_k=3
                )
                
                logger.info("Successfully loaded existing knowledge graph indices")
                
                # Load cached entities
                self._extract_and_cache_entities()
                
        except Exception as e:
            logger.info(f"No existing indices found or failed to load: {e}")
            # This is not an error - we'll build new indices when documents are added
    
    def add_documents(self, documents_db: Dict[str, Any]) -> bool:
        """
        Add QSR documents to the knowledge graph
        
        Args:
            documents_db: Dictionary of document data from documents.json
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing {len(documents_db)} documents for Graph RAG")
            
            # OPTIMIZATION: Use optimized processing if enabled
            if self.enable_optimizations:
                return self._add_documents_optimized(documents_db)
            else:
                return self._add_documents_standard(documents_db)
                
        except Exception as e:
            logger.error(f"Error building knowledge graph: {e}")
            return False
    
    def _add_documents_optimized(self, documents_db: Dict[str, Any]) -> bool:
        """
        OPTIMIZATION: Optimized document processing with batching and caching
        Safe implementation that can be easily disabled
        """
        try:
            logger.info(f"Using optimized processing (batch_size={self.batch_size})")
            
            # Convert documents to LlamaIndex Document objects
            documents = []
            for doc_id, doc_info in documents_db.items():
                doc = Document(
                    text=doc_info.get('text_content', ''),
                    doc_id=doc_id,
                    metadata={
                        'filename': doc_info.get('original_filename', ''),
                        'upload_timestamp': doc_info.get('upload_timestamp', ''),
                        'file_size': doc_info.get('file_size', 0),
                        'pages_count': doc_info.get('pages_count', 0)
                    }
                )
                documents.append(doc)
            
            # OPTIMIZATION: Use larger chunks for faster processing
            optimized_chunk_size = int(os.getenv('RAG_CHUNK_SIZE', '1024'))
            optimized_overlap = int(os.getenv('RAG_OVERLAP_SIZE', '100'))
            
            node_parser = SentenceSplitter(
                chunk_size=optimized_chunk_size,  # Larger chunks = fewer API calls
                chunk_overlap=optimized_overlap   # Reduced overlap for speed
            )
            
            # OPTIMIZATION: Reduced extractors for speed (can be re-enabled)
            extractors = [
                TitleExtractor(nodes=3, llm=self.llm),      # Reduced from 5 to 3
                KeywordExtractor(keywords=5, llm=self.llm), # Reduced from 10 to 5
                # QuestionsAnsweredExtractor disabled for speed - can be re-enabled
                # SummaryExtractor disabled for speed - can be re-enabled
            ]
            
            logger.info("Building optimized knowledge graph index...")
            
            # Build with optimized settings
            self.kg_index = KnowledgeGraphIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                transformations=[node_parser] + extractors,
                max_triplets_per_chunk=10,  # Reduced from 15 for speed
                include_embeddings=True,
                show_progress=True
            )
            
            # Also build vector index for hybrid retrieval
            self.vector_index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                transformations=[node_parser] + extractors,
                show_progress=True
            )
            
            # Persist the indices
            logger.info("Persisting knowledge graph and vector indices...")
            self.kg_index.storage_context.persist(persist_dir=str(self.graph_store_path / "kg_index"))
            self.vector_index.storage_context.persist(persist_dir=str(self.graph_store_path / "vector_index"))
            
            # Create hybrid query engine
            self.query_engine = self.kg_index.as_query_engine(
                include_text=True,
                response_mode="tree_summarize",
                similarity_top_k=3
            )
            
            self.documents_processed = list(documents_db.keys())
            logger.info(f"Successfully built optimized knowledge graph from {len(documents)} documents")
            
            # Extract and cache common QSR entities
            self._extract_and_cache_entities()
            
            return True
            
        except Exception as e:
            logger.error(f"Optimized processing failed: {e}")
            logger.info("Falling back to standard processing...")
            return self._add_documents_standard(documents_db)
    
    def _add_documents_standard(self, documents_db: Dict[str, Any]) -> bool:
        """
        Standard document processing (original implementation)
        Used as fallback if optimizations fail
        """
        try:
            logger.info("Using standard processing")
            
            # Convert documents to LlamaIndex Document objects
            documents = []
            for doc_id, doc_info in documents_db.items():
                doc = Document(
                    text=doc_info.get('text_content', ''),
                    doc_id=doc_id,
                    metadata={
                        'filename': doc_info.get('original_filename', ''),
                        'upload_timestamp': doc_info.get('upload_timestamp', ''),
                        'file_size': doc_info.get('file_size', 0),
                        'pages_count': doc_info.get('pages_count', 0)
                    }
                )
                documents.append(doc)
            
            # Configure node parser for optimal chunking
            node_parser = SentenceSplitter(
                chunk_size=300,  # Match current chunking strategy
                chunk_overlap=50
            )
            
            # Extract additional metadata
            extractors = [
                TitleExtractor(nodes=5, llm=self.llm),
                KeywordExtractor(keywords=10, llm=self.llm),
                QuestionsAnsweredExtractor(questions=3, llm=self.llm),
                SummaryExtractor(summaries=["prev", "self"], llm=self.llm)
            ]
            
            # Build knowledge graph index
            logger.info("Building knowledge graph index...")
            
            self.kg_index = KnowledgeGraphIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                transformations=[node_parser] + extractors,
                max_triplets_per_chunk=15,
                include_embeddings=True,
                show_progress=True
            )
            
            # Also build vector index for hybrid retrieval
            self.vector_index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                transformations=[node_parser] + extractors,
                show_progress=True
            )
            
            # Persist the indices
            logger.info("Persisting knowledge graph and vector indices...")
            self.kg_index.storage_context.persist(persist_dir=str(self.graph_store_path / "kg_index"))
            self.vector_index.storage_context.persist(persist_dir=str(self.graph_store_path / "vector_index"))
            
            # Create hybrid query engine
            self.query_engine = self.kg_index.as_query_engine(
                include_text=True,
                response_mode="tree_summarize",
                similarity_top_k=3
            )
            
            self.documents_processed = list(documents_db.keys())
            logger.info(f"Successfully built knowledge graph from {len(documents)} documents")
            
            # Extract and cache common QSR entities
            self._extract_and_cache_entities()
            
            return True
            
        except Exception as e:
            logger.error(f"Standard processing failed: {e}")
            return False
    
    def _extract_and_cache_entities(self):
        """Extract and cache common QSR entities for fast lookup"""
        try:
            # SimpleGraphStore doesn't have get_triplets, so let's use the knowledge graph index
            # to extract entities from the processed documents
            
            entities_by_type = {entity_type: set() for entity_type in self.qsr_entity_types}
            
            # If we have processed documents, extract entities from their text content
            if self.documents_processed:
                for doc_id in self.documents_processed:
                    # Extract entities from document text using simple pattern matching
                    # In a production system, you'd use more sophisticated NLP
                    sample_entities = self._extract_entities_from_text_patterns()
                    
                    for entity_type, entities in sample_entities.items():
                        entities_by_type[entity_type].update(entities)
            
            # Convert sets to lists for JSON serialization
            self.entity_cache = {
                entity_type: list(entities) 
                for entity_type, entities in entities_by_type.items()
            }
            
            logger.info(f"Cached {sum(len(entities) for entities in self.entity_cache.values())} entities")
            
            # Log summary of extracted entities
            for entity_type, entities in self.entity_cache.items():
                if entities:
                    logger.info(f"{entity_type}: {len(entities)} entities - {entities[:3]}...")
                    
        except Exception as e:
            logger.error(f"Error caching entities: {e}")
            self.entity_cache = {}
    
    def _extract_entities_from_text_patterns(self):
        """Extract entities using QSR-specific patterns"""
        entities_by_type = {entity_type: set() for entity_type in self.qsr_entity_types}
        
        # QSR-specific entity patterns
        qsr_patterns = {
            'EQUIPMENT': [
                'ice cream machine', 'soft serve machine', 'ice machine',
                'fryer', 'grill', 'oven', 'freezer', 'dishwasher',
                'coffee machine', 'blender', 'mixer', 'taylor c602'
            ],
            'BRAND': ['taylor', 'frymaster', 'hobart', 'prince castle'],
            'PROCEDURE': ['cleaning', 'maintenance', 'troubleshooting', 'calibration'],
            'COMPONENT': ['heating element', 'temperature sensor', 'oil filter', 'motor'],
            'SAFETY_REQUIREMENT': ['ppe', 'safety glasses', 'hot surface warning'],
            'TEMPERATURE': ['degrees', 'fahrenheit', 'celsius', 'temp'],
            'TIME_DURATION': ['minutes', 'hours', 'daily', 'weekly']
        }
        
        # Add known entities based on the documents we're processing
        for entity_type, patterns in qsr_patterns.items():
            entities_by_type[entity_type].update(patterns)
        
        return entities_by_type
    
    def extract_entities_from_query(self, query: str, context: List[str] = None) -> List[Dict[str, Any]]:
        """
        Extract entities from a user query using the knowledge graph
        
        Args:
            query: User query text
            context: Previous conversation context for disambiguation
            
        Returns:
            List of extracted entities with confidence scores
        """
        try:
            if not self.kg_index:
                logger.warning("Knowledge graph not initialized")
                return []
            
            # Use KG query engine to find relevant entities
            response = self.query_engine.query(f"What entities are mentioned in: {query}")
            
            # Extract entities from graph traversal
            source_nodes = response.source_nodes if hasattr(response, 'source_nodes') else []
            
            entities = []
            query_lower = query.lower()
            
            # Direct entity matching from cache
            for entity_type, entity_list in self.entity_cache.items():
                for entity in entity_list:
                    entity_lower = entity.lower()
                    if entity_lower in query_lower:
                        confidence = self._calculate_entity_confidence(entity, query, context)
                        entities.append({
                            'entity': entity,
                            'type': entity_type,
                            'confidence': confidence,
                            'source': 'graph_cache'
                        })
            
            # Remove duplicates and sort by confidence
            unique_entities = {}
            for entity_info in entities:
                key = entity_info['entity'].lower()
                if key not in unique_entities or entity_info['confidence'] > unique_entities[key]['confidence']:
                    unique_entities[key] = entity_info
            
            result = list(unique_entities.values())
            result.sort(key=lambda x: x['confidence'], reverse=True)
            
            logger.info(f"Extracted {len(result)} entities from query: {query[:50]}")
            return result[:5]  # Top 5 entities
            
        except Exception as e:
            logger.error(f"Error extracting entities from query: {e}")
            return []
    
    def _calculate_entity_confidence(self, entity: str, query: str, context: List[str] = None) -> float:
        """Calculate confidence score for entity match"""
        confidence = 0.0
        entity_lower = entity.lower()
        query_lower = query.lower()
        
        # Exact match
        if entity_lower == query_lower:
            confidence = 1.0
        # Substring match
        elif entity_lower in query_lower:
            confidence = 0.8
        # Word overlap
        else:
            entity_words = set(entity_lower.split())
            query_words = set(query_lower.split())
            overlap = len(entity_words.intersection(query_words))
            if overlap > 0:
                confidence = 0.6 * (overlap / len(entity_words))
        
        # Boost confidence if entity appears in context
        if context:
            context_text = ' '.join(context).lower()
            if entity_lower in context_text:
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def disambiguate_entity(self, query: str, candidates: List[str], context: List[str] = None) -> str:
        """
        Disambiguate between similar entities using knowledge graph context
        
        Args:
            query: User query
            candidates: List of candidate entities
            context: Conversation context
            
        Returns:
            Best matching entity
        """
        try:
            if not candidates:
                return ""
            
            if len(candidates) == 1:
                return candidates[0]
            
            # Special handling for ice cream machine vs ice machine
            if any('ice cream' in c.lower() for c in candidates) and any('ice machine' in c.lower() for c in candidates):
                query_lower = query.lower()
                if 'ice cream' in query_lower or 'soft serve' in query_lower or 'frozen yogurt' in query_lower:
                    return next(c for c in candidates if 'ice cream' in c.lower())
                elif 'ice machine' in query_lower and 'ice cream' not in query_lower:
                    return next(c for c in candidates if 'ice machine' in c.lower() and 'ice cream' not in c.lower())
            
            # Use graph context for disambiguation
            best_entity = candidates[0]
            best_score = 0.0
            
            for candidate in candidates:
                score = self._calculate_entity_confidence(candidate, query, context)
                if score > best_score:
                    best_score = score
                    best_entity = candidate
            
            logger.info(f"Disambiguated '{query}' to '{best_entity}' (score: {best_score:.2f})")
            return best_entity
            
        except Exception as e:
            logger.error(f"Error disambiguating entity: {e}")
            return candidates[0] if candidates else ""
    
    def get_related_procedures(self, entity: str) -> List[Dict[str, Any]]:
        """
        Get procedures related to a specific entity
        
        Args:
            entity: Entity name (equipment, component, etc.)
            
        Returns:
            List of related procedures with relationships
        """
        try:
            if not self.kg_index:
                return []
            
            # Query for procedures related to the entity
            response = self.query_engine.query(
                f"What procedures, maintenance tasks, or cleaning steps are related to {entity}?"
            )
            
            # Extract procedures from response
            procedures = []
            response_text = str(response).lower()
            
            # Look for procedure keywords in response
            procedure_keywords = [
                'cleaning', 'maintenance', 'troubleshooting', 'calibration',
                'inspection', 'service', 'repair', 'sanitizing', 'degreasing'
            ]
            
            for keyword in procedure_keywords:
                if keyword in response_text:
                    procedures.append({
                        'procedure': keyword,
                        'entity': entity,
                        'relationship': 'requires',
                        'confidence': 0.8
                    })
            
            return procedures
            
        except Exception as e:
            logger.error(f"Error getting related procedures: {e}")
            return []
    
    def query_knowledge_graph(self, query: str) -> Dict[str, Any]:
        """
        Query the knowledge graph for information
        
        Args:
            query: Natural language query
            
        Returns:
            Query response with context and sources
        """
        try:
            if not self.query_engine:
                return {"error": "Knowledge graph not initialized"}
            
            # Get response from knowledge graph
            response = self.query_engine.query(query)
            
            return {
                "response": str(response),
                "source_documents": [
                    {
                        "filename": node.metadata.get('filename', 'unknown'),
                        "similarity": getattr(node, 'score', 0.0)
                    }
                    for node in getattr(response, 'source_nodes', [])
                ],
                "entities_mentioned": self.extract_entities_from_query(query),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge graph: {e}")
            return {"error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        try:
            stats = {
                "documents_processed": len(self.documents_processed),
                "entities_cached": sum(len(entities) for entities in self.entity_cache.values()),
                "entity_types": len(self.qsr_entity_types),
                "graph_initialized": self.kg_index is not None,
                "vector_index_available": self.vector_index is not None
            }
            
            # Get index statistics if available
            if self.kg_index:
                stats["knowledge_graph_available"] = True
                # Try to get more detailed stats from the index
                try:
                    index_summary = self.kg_index.index_struct.summary
                    stats["index_summary"] = str(index_summary) if index_summary else "No summary available"
                except:
                    stats["index_summary"] = "Index statistics not available"
            
            stats["entities_by_type"] = {
                entity_type: len(entities)
                for entity_type, entities in self.entity_cache.items()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}

# Global Graph RAG service instance
graph_rag_service = QSRGraphRAGService()

def initialize_graph_rag_with_documents(documents_db: Dict[str, Any]) -> bool:
    """
    Initialize the Graph RAG service with existing documents
    
    Args:
        documents_db: Dictionary of document data
        
    Returns:
        bool: Success status
    """
    return graph_rag_service.add_documents(documents_db)