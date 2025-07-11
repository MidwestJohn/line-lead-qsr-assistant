"""
Optimized QSR RAG Service - Enhanced LightRAG for QSR Manual Processing
Target: 200+ entities from QSR equipment manuals (10x current extraction)
"""

import os
import asyncio
from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
import logging

logger = logging.getLogger(__name__)

class OptimizedQSRRAGService:
    def __init__(self):
        self.rag_instance = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize LightRAG with QSR-optimized configuration."""
        
        if self.initialized:
            return True
            
        try:
            # Set Neo4j environment variables
            os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
            os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
            os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
            
            if not os.environ['NEO4J_PASSWORD']:
                raise ValueError("NEO4J_PASSWORD environment variable required")
            
            logger.info("🔧 Configuring LightRAG with QSR optimization...")
            
            # QSR-OPTIMIZED CONFIGURATION
            self.rag_instance = LightRAG(
                working_dir="./rag_storage_qsr_optimized",
                
                # Neo4j storage backend
                graph_storage="Neo4JStorage",
                
                # LLM configuration
                llm_model_func=gpt_4o_mini_complete,
                embedding_func=EmbeddingFunc(
                    embedding_dim=1536,
                    max_token_size=8192,
                    func=self._get_embedding_function()
                ),
                
                # QSR-OPTIMIZED EXTRACTION PARAMETERS
                chunk_token_size=400,  # Optimal for QSR content (256-512 range)
                chunk_overlap_token_size=80,  # Increased overlap for better context
                
                # Debugging
                log_level="DEBUG"
            )
            
            # Initialize storage connections
            logger.info("🔌 Initializing storage connections...")
            await self.rag_instance.initialize_storages()
            
            self.initialized = True
            logger.info("✅ QSR-Optimized LightRAG initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ QSR-Optimized LightRAG initialization failed: {e}")
            self.initialized = False
            return False
    
    def _get_qsr_entity_extraction_prompt(self):
        """Get QSR-specific entity extraction prompt."""
        return """
        Extract ALL entities from this QSR equipment manual content, focusing on:
        
        EQUIPMENT: All equipment names, models, parts, components, tools, machinery
        PROCEDURES: All operational procedures, maintenance steps, safety protocols
        INGREDIENTS: All food items, ingredients, supplies, materials
        SAFETY: All safety warnings, cautions, hazards, protective equipment
        MAINTENANCE: All maintenance tasks, schedules, intervals, requirements
        TROUBLESHOOTING: All problems, solutions, diagnostic steps, error codes
        TEMPERATURES: All temperature settings, ranges, requirements
        TIMES: All timing requirements, durations, schedules
        MEASUREMENTS: All quantities, sizes, dimensions, capacities
        LOCATIONS: All physical locations, positions, zones in restaurant
        
        Extract entities even if they appear only once. Include:
        - Technical specifications and model numbers
        - Step-by-step procedure elements
        - Safety warnings and cautions
        - Maintenance intervals and requirements
        - Temperature and time specifications
        - Part names and component identifiers
        - Troubleshooting symptoms and solutions
        
        Be thorough - this is for a comprehensive QSR knowledge system.
        """
    
    def _get_embedding_function(self):
        """Get embedding function for LightRAG."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            return lambda texts: model.encode(texts).tolist()
        except ImportError:
            logger.warning("SentenceTransformers not available, using OpenAI embeddings")
            return None
    
    async def process_document_multipass(self, content: str, file_path: str = None):
        """Process document through multiple passes for comprehensive extraction."""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            raise RuntimeError("QSR RAG service failed to initialize")
        
        try:
            logger.info(f"📄 Processing document with multi-pass extraction: {file_path or 'content'}")
            
            # PASS 1: Equipment and Technical Specifications
            logger.info("🔧 Pass 1: Equipment and Technical Extraction")
            equipment_focused_content = f"""
            EQUIPMENT AND TECHNICAL FOCUS:
            Extract all equipment, models, parts, specifications, and technical details.
            
            {content}
            """
            result_1 = await self.rag_instance.ainsert(equipment_focused_content)
            
            # PASS 2: Procedures and Safety
            logger.info("📋 Pass 2: Procedures and Safety Extraction")
            procedures_focused_content = f"""
            PROCEDURES AND SAFETY FOCUS:
            Extract all procedures, steps, safety protocols, and operational instructions.
            
            {content}
            """
            result_2 = await self.rag_instance.ainsert(procedures_focused_content)
            
            # PASS 3: Maintenance and Troubleshooting
            logger.info("🔧 Pass 3: Maintenance and Troubleshooting Extraction")
            maintenance_focused_content = f"""
            MAINTENANCE AND TROUBLESHOOTING FOCUS:
            Extract all maintenance requirements, schedules, troubleshooting steps, and diagnostic information.
            
            {content}
            """
            result_3 = await self.rag_instance.ainsert(maintenance_focused_content)
            
            logger.info("✅ Multi-pass document processing completed")
            return {
                "equipment_extraction": result_1,
                "procedures_extraction": result_2,
                "maintenance_extraction": result_3,
                "total_passes": 3
            }
            
        except Exception as e:
            logger.error(f"❌ Multi-pass document processing failed: {e}")
            raise

    async def process_document_single_pass(self, content: str, file_path: str = None):
        """Process document through single optimized pass."""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            raise RuntimeError("QSR RAG service failed to initialize")
        
        try:
            logger.info(f"📄 Processing document with single optimized pass: {file_path or 'content'}")
            
            # Enhanced content with QSR context
            enhanced_content = f"""
            QSR EQUIPMENT MANUAL CONTENT:
            This is content from a Quick Service Restaurant (QSR) equipment manual.
            Extract ALL entities comprehensively including equipment, procedures, safety, maintenance, and specifications.
            
            {content}
            """
            
            result = await self.rag_instance.ainsert(enhanced_content)
            
            logger.info("✅ Single-pass document processing completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Single-pass document processing failed: {e}")
            raise

    async def get_extraction_statistics(self):
        """Get statistics about entity extraction."""
        try:
            if not self.rag_instance:
                return {"error": "RAG instance not initialized"}
            
            # Get LightRAG statistics
            stats = self.rag_instance.get_statistics()
            
            # Calculate QSR-specific metrics
            entity_count = stats.get("entities_cached", 0)
            relationship_count = stats.get("relationships_cached", 0)
            
            return {
                "total_entities": entity_count,
                "total_relationships": relationship_count,
                "entities_per_document": entity_count / max(1, stats.get("documents_processed", 1)),
                "optimization_target": 200,  # Target entities per document
                "optimization_achieved": entity_count >= 200,
                "improvement_factor": entity_count / max(1, 35),  # vs original 35 entities
                "raw_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting extraction statistics: {e}")
            return {"error": str(e)}


# Global optimized QSR RAG service instance
optimized_qsr_rag_service = OptimizedQSRRAGService()