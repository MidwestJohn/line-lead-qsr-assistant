#!/usr/bin/env python3
"""
Clean Ragie Service Implementation
=================================

Simple, focused Ragie integration without Neo4j dependencies.
Replaces the complex graph RAG system with Ragie's managed service.

Author: Generated with Memex (https://memex.tech)
"""

import os
import logging
import time
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ragie SDK imports
try:
    from ragie import Ragie
    RAGIE_AVAILABLE = True
except ImportError:
    RAGIE_AVAILABLE = False
    logging.warning("Ragie SDK not available. Install with: pip install ragie")

logger = logging.getLogger(__name__)

@dataclass
class RagieSearchResult:
    """Result from Ragie search"""
    text: str
    score: float
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any]
    images: Optional[List[Dict[str, Any]]] = None  # Image references from chunk

@dataclass
class RagieUploadResult:
    """Result from Ragie upload"""
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    chunk_count: Optional[int] = None
    error: Optional[str] = None

class CleanRagieService:
    """Clean Ragie service without Neo4j dependencies"""
    
    def __init__(self):
        """Initialize the service"""
        self.api_key = os.getenv("RAGIE_API_KEY")
        self.partition = os.getenv("RAGIE_PARTITION", "qsr_manuals")
        
        if not self.api_key:
            logger.error("RAGIE_API_KEY not found in environment variables")
            self.client = None
            return
        
        if not RAGIE_AVAILABLE:
            logger.error("Ragie SDK not available")
            self.client = None
            return
            
        try:
            # Initialize with proper timeout and retry configuration
            from ragie.utils import BackoffStrategy, RetryConfig
            
            # Configure retry strategy for better reliability
            retry_config = RetryConfig(
                strategy="backoff",
                backoff=BackoffStrategy(
                    initial_interval=1,    # Start with 1 second
                    max_interval=30,       # Max 30 seconds between retries
                    exponent=1.5,          # Exponential backoff
                    max_elapsed_time=300   # Give up after 5 minutes total
                ),
                retry_connection_errors=True
            )
            
            self.client = Ragie(
                auth=self.api_key,
                retry_config=retry_config,
                debug_logger=logger  # Enable debug logging
            )
            logger.info("✅ Ragie client initialized with enhanced error handling")
        except Exception as e:
            logger.error(f"Failed to initialize Ragie client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Ragie service is available"""
        return self.client is not None
    
    async def setup_qsr_instructions(self) -> bool:
        """
        Setup QSR-specific instructions for better content extraction
        This tells Ragie how to identify and extract pizza images and QSR content
        """
        if not self.client:
            logger.error("Cannot setup instructions: Ragie client not available")
            return False
        
        try:
            logger.info("🎯 Setting up QSR instructions for enhanced content extraction...")
            
            # Instruction for identifying pizza images and visual content
            pizza_instruction = {
                "name": "pizza_visual_content",
                "description": "Identify and extract pizza images, diagrams, and visual content from QSR manuals",
                "prompt": """Extract visual content related to pizzas from restaurant manuals. Look for:
- Pizza images showing different styles (Margherita, Romana, Canotto, etc.)
- Equipment diagrams for pizza ovens and kitchen tools
- Recipe cards with visual elements
- Step-by-step preparation images
- Temperature and timing charts
- Ingredient photos and portions

Tag content with pizza style, equipment type, and procedure context.""",
                "entity_schema": {
                    "type": "object",
                    "properties": {
                        "pizza_style": {"type": "string", "description": "Type of pizza (Margherita, Romana, Canotto, etc.)"},
                        "content_type": {"type": "string", "description": "Type of visual content (image, diagram, recipe_card, etc.)"},
                        "equipment_type": {"type": "string", "description": "Related equipment (oven, tools, etc.)"},
                        "procedure": {"type": "string", "description": "Related procedure (preparation, cooking, etc.)"},
                        "has_visual": {"type": "boolean", "description": "Whether this content contains visual elements"}
                    },
                    "required": ["content_type", "has_visual"]
                },
                "partition": self.partition
            }
            
            # Instruction for QSR equipment identification
            equipment_instruction = {
                "name": "qsr_equipment_content", 
                "description": "Identify equipment-related visual content in QSR manuals",
                "prompt": """Extract equipment-related visual content including:
- Fryer operation diagrams and maintenance images
- Grill setup and cleaning procedures
- Oven temperature controls and settings
- Safety equipment and PPE images
- Equipment troubleshooting diagrams
- Maintenance schedule charts

Tag with equipment type (fryer, grill, oven) and procedure type (operation, maintenance, safety).""",
                "entity_schema": {
                    "type": "object", 
                    "properties": {
                        "equipment_type": {"type": "string", "description": "Type of equipment (fryer, grill, oven, etc.)"},
                        "procedure_type": {"type": "string", "description": "Type of procedure (operation, maintenance, safety, cleaning)"},
                        "content_type": {"type": "string", "description": "Type of content (diagram, image, chart, procedure)"},
                        "safety_level": {"type": "string", "description": "Safety importance (critical, standard, informational)"},
                        "has_visual": {"type": "boolean", "description": "Whether this content contains visual elements"}
                    },
                    "required": ["equipment_type", "procedure_type", "has_visual"]
                },
                "partition": self.partition
            }
            
            # Check existing instructions first
            existing_instructions = self.client.entities.list_instructions()
            existing_names = [inst.name for inst in existing_instructions.instructions] if hasattr(existing_instructions, 'instructions') else []
            
            instructions_created = []
            
            # Create pizza instruction if it doesn't exist
            if "pizza_visual_content" not in existing_names:
                result = self.client.entities.create_instruction(request=pizza_instruction)
                instructions_created.append("pizza_visual_content")
                logger.info(f"✅ Created pizza visual content instruction: {result.id}")
            
            # Create equipment instruction if it doesn't exist  
            if "qsr_equipment_content" not in existing_names:
                result = self.client.entities.create_instruction(request=equipment_instruction)
                instructions_created.append("qsr_equipment_content")
                logger.info(f"✅ Created QSR equipment instruction: {result.id}")
            
            if instructions_created:
                logger.info(f"🎯 Setup complete: Created {len(instructions_created)} instructions")
            else:
                logger.info("🎯 Instructions already exist, skipping creation")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup QSR instructions: {e}")
            return False
    
    def _build_smart_filter(self, original_query: str, processed_query: str) -> Optional[Dict[str, Any]]:
        """
        Build intelligent filter based on query analysis to improve search relevance
        
        Args:
            original_query: Original user query
            processed_query: Preprocessed query
            
        Returns:
            Filter dictionary for Ragie API or None if no specific filter needed
        """
        query_lower = original_query.lower().strip()
        
        # Equipment-specific filters
        equipment_filters = self._get_equipment_filter(query_lower)
        if equipment_filters:
            return equipment_filters
        
        # Document type filters
        doc_type_filters = self._get_document_type_filter(query_lower)
        if doc_type_filters:
            return doc_type_filters
        
        # Content type filters
        content_filters = self._get_content_type_filter(query_lower)
        if content_filters:
            return content_filters
        
        # No specific filter needed
        return None
    
    def _get_equipment_filter(self, query_lower: str) -> Optional[Dict[str, Any]]:
        """Generate equipment-specific filters"""
        
        # Baxter equipment filter
        if any(term in query_lower for term in ['baxter', 'ov520e1']):
            return {
                "$or": [
                    {"document_name": {"$regex": ".*[Bb]axter.*"}},
                    {"document_name": {"$regex": ".*OV520E1.*"}},
                    {"document_name": {"$regex": ".*ov520e1.*"}}
                ]
            }
        
        # Taylor equipment filter
        if any(term in query_lower for term in ['taylor', 'c602']):
            return {
                "$or": [
                    {"document_name": {"$regex": ".*[Tt]aylor.*"}},
                    {"document_name": {"$regex": ".*C602.*"}},
                    {"document_name": {"$regex": ".*c602.*"}}
                ]
            }
        
        # Grote equipment filter
        if 'grote' in query_lower:
            return {
                "document_name": {"$regex": ".*[Gg]rote.*"}
            }
        
        return None
    
    def _get_document_type_filter(self, query_lower: str) -> Optional[Dict[str, Any]]:
        """Generate document type filters"""
        
        # Image/diagram requests
        image_terms = ['image', 'diagram', 'picture', 'photo', 'visual', 'show me']
        if any(term in query_lower for term in image_terms):
            return {
                "document_type": {"$in": ["png", "jpg", "jpeg", "pdf"]}
            }
        
        # Manual/documentation requests
        manual_terms = ['manual', 'documentation', 'guide', 'instructions']
        if any(term in query_lower for term in manual_terms):
            return {
                "document_type": {"$in": ["pdf", "doc", "docx"]}
            }
        
        return None
    
    def _get_content_type_filter(self, query_lower: str) -> Optional[Dict[str, Any]]:
        """Generate content-specific filters"""
        
        # Safety/procedure content
        safety_terms = ['safety', 'procedure', 'protocol', 'compliance']
        if any(term in query_lower for term in safety_terms):
            # Prefer recent documents for safety procedures
            return {
                "$and": [
                    {"document_type": {"$in": ["pdf", "doc", "docx"]}},
                    # Could add date filters here if we track upload dates
                ]
            }
        
        # Maintenance content
        maintenance_terms = ['maintenance', 'cleaning', 'service', 'repair']
        if any(term in query_lower for term in maintenance_terms):
            return {
                "document_type": {"$in": ["pdf", "png", "jpg"]}  # Include diagrams
            }
        
        return None
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query to improve Ragie search results
        Extract key terms and remove query patterns that don't match well
        """
        import re
        
        # Convert to lowercase for processing
        processed = query.lower()
        
        # Remove common request patterns that don't help with document search
        remove_patterns = [
            r"show me (?:an? )?(image|picture|photo) of ",
            r"can you show me ",
            r"i want to see ",
            r"display ",
            r"what does .* look like",
            r"how does .* look",
        ]
        
        for pattern in remove_patterns:
            processed = re.sub(pattern, "", processed)
        
        # Extract pizza types and key culinary terms
        pizza_terms = ["canotto", "margherita", "napoli", "gourmet", "new york"]
        culinary_terms = ["dough", "sauce", "cheese", "topping", "crust", "recipe"]
        equipment_terms = ["fryer", "grill", "oven", "mixer", "temperature"]
        
        # If we find key terms, prioritize them
        found_terms = []
        for term in pizza_terms + culinary_terms + equipment_terms:
            if term in processed:
                found_terms.append(term)
        
        # If we found key terms, use them as the primary query
        if found_terms:
            processed = " ".join(found_terms)
        
        # Clean up extra spaces
        processed = re.sub(r'\s+', ' ', processed).strip()
        
        # If query became too short, return original key parts
        if len(processed) < 3:
            processed = query
        
        return processed
    
    async def search(self, query: str, limit: int = 5) -> List[RagieSearchResult]:
        """
        Enhanced search with intelligent filtering based on query analysis
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        if not self.client:
            logger.error("Ragie client not available")
            return []
        
        try:
            # Preprocess query to extract key terms for better Ragie matching
            processed_query = self._preprocess_query(query)
            logger.info(f"🔍 Searching Ragie: '{query}' → '{processed_query}' (limit: {limit})")
            
            # Build intelligent filter based on query analysis
            smart_filter = self._build_smart_filter(query, processed_query)
            
            # Search using Ragie SDK with enhanced filtering
            search_request = {
                "query": processed_query,
                "rerank": True,
                "partition": self.partition,
                "limit": limit
            }
            
            # Add intelligent filter if one was generated
            if smart_filter:
                search_request["filter"] = smart_filter
                logger.info(f"🎯 Applying filter: {smart_filter}")
            
            response = self.client.retrievals.retrieve(request=search_request)
            
            results = []
            if hasattr(response, 'scored_chunks') and response.scored_chunks:
                for chunk in response.scored_chunks:
                    chunk_metadata = getattr(chunk, 'metadata', {})
                    chunk_text = getattr(chunk, 'text', '')
                    
                    # Enhanced metadata parsing based on Ragie documentation
                    # Check for file_type in metadata to identify content type
                    file_type = chunk_metadata.get('file_type', 'pdf')  # Default to pdf for text chunks
                    
                    # Debug enhanced metadata structure
                    logger.info(f"🔍 Chunk metadata: file_type={file_type}, keys={list(chunk_metadata.keys())}")
                    
                    # Enhanced content type detection from text patterns
                    image_keywords = ['figure', 'diagram', 'image', 'see illustration', 'pictured', 'photo', 'picture', 'visual', 'shown below', 'see below', 'example shown', 'gourmet', 'display']
                    video_keywords = ['video', 'demonstration', 'tutorial', 'watch', 'play']
                    
                    if file_type == 'pdf':
                        if any(keyword in chunk_text.lower() for keyword in image_keywords):
                            # This text chunk refers to visual content - mark as image type
                            file_type = 'image'
                            chunk_metadata['file_type'] = 'image'
                            logger.info(f"🖼️ Detected image reference in text: {chunk_text[:100]}...")
                        elif any(keyword in chunk_text.lower() for keyword in video_keywords):
                            # This text chunk refers to video content
                            file_type = 'video'
                            chunk_metadata['file_type'] = 'video'
                            logger.info(f"🎥 Detected video reference in text: {chunk_text[:100]}...")
                    
                    # Extract source and page information
                    source = chunk_metadata.get('source') or chunk_metadata.get('original_filename') or getattr(chunk, 'document_name', 'Unknown')
                    page_number = chunk_metadata.get('page_number', None)
                    
                    # Extract image information based on content type
                    images = []
                    url = None
                    
                    # Check for direct image URLs in various metadata fields
                    if 'images' in chunk_metadata:
                        images = chunk_metadata['images']
                        logger.info(f"🖼️ Found images in metadata: {len(images)}")
                    elif 'image_urls' in chunk_metadata:
                        images = [{'url': url} for url in chunk_metadata['image_urls']]
                        logger.info(f"🖼️ Found image_urls in metadata: {len(images)}")
                    elif 'url' in chunk_metadata:
                        url = chunk_metadata['url']
                        images = [{'url': url, 'caption': chunk_text[:100]}]
                        logger.info(f"🖼️ Found direct URL in metadata: {url}")
                    elif hasattr(chunk, 'images') and chunk.images:
                        images = chunk.images
                        logger.info(f"🖼️ Found images in chunk attributes: {len(images)}")
                    elif hasattr(chunk, 'links') and chunk.links:
                        # Check if links contain image references
                        links = chunk.links
                        if isinstance(links, list):
                            for link in links:
                                if hasattr(link, 'url') and any(ext in link.url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                    images.append({
                                        'url': link.url,
                                        'caption': getattr(link, 'text', chunk_text[:100]),
                                        'type': 'image'
                                    })
                        logger.info(f"🖼️ Found images in links: {len(images)}")
                    
                    # Enhance metadata with parsed information
                    enhanced_metadata = {
                        **chunk_metadata,
                        'file_type': file_type,
                        'source': source,
                        'page_number': page_number,
                        'content_type': file_type,
                        'has_images': len(images) > 0,
                        'image_count': len(images)
                    }
                    
                    # Add equipment-specific metadata if detected
                    if any(equip in chunk_text.lower() for equip in ['fryer', 'grill', 'oven', 'freezer', 'equipment']):
                        enhanced_metadata['equipment_type'] = 'kitchen_equipment'
                        if 'cleaning' in chunk_text.lower() or 'maintenance' in chunk_text.lower():
                            enhanced_metadata['procedure'] = 'maintenance'
                        elif 'cooking' in chunk_text.lower() or 'operating' in chunk_text.lower():
                            enhanced_metadata['procedure'] = 'operation'
                    
                    result = RagieSearchResult(
                        text=chunk_text,
                        score=chunk.score,
                        document_id=getattr(chunk, 'document_id', ''),
                        chunk_id=getattr(chunk, 'chunk_id', ''),
                        metadata=enhanced_metadata,
                        images=images if images else None
                    )
                    results.append(result)
            
            logger.info(f"✅ Found {len(results)} results from Ragie")
            return results
            
        except Exception as e:
            logger.error(f"Ragie search failed: {e}")
            return []
    
    async def get_document_entities(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get entities extracted from a document using instructions
        This should include visual content identified by our QSR instructions
        """
        if not self.client:
            return []
        
        try:
            logger.info(f"🎯 Getting entities for document: {document_id}")
            
            # Get entities extracted by our instructions
            entities = self.client.entities.list_by_document(document_id=document_id)
            
            visual_entities = []
            if hasattr(entities, 'entities') and entities.entities:
                for entity in entities.entities:
                    # Look for visual content entities
                    if hasattr(entity, 'instruction_name'):
                        if entity.instruction_name in ['pizza_visual_content', 'qsr_equipment_content']:
                            visual_entities.append({
                                'id': getattr(entity, 'id', ''),
                                'instruction': entity.instruction_name,
                                'content': getattr(entity, 'content', ''),
                                'metadata': getattr(entity, 'metadata', {}),
                                'confidence': getattr(entity, 'confidence', 0.0)
                            })
                            
            logger.info(f"🖼️ Found {len(visual_entities)} visual entities in document")
            return visual_entities
            
        except Exception as e:
            logger.debug(f"Entity retrieval failed: {e}")
            return []
    
    async def get_document_images(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Try to get images from a Ragie document using multiple methods
        """
        if not self.client:
            return []
        
        try:
            logger.info(f"🖼️ Attempting to retrieve images for document: {document_id}")
            
            # Method 1: Check entities for visual content
            entities = await self.get_document_entities(document_id)
            if entities:
                logger.info(f"Found {len(entities)} visual entities")
                return entities
            
            # Method 2: Check document chunks for image content
            try:
                chunks = self.client.documents.get_chunks(document_id=document_id)
                image_chunks = []
                
                if hasattr(chunks, 'chunks') and chunks.chunks:
                    for chunk in chunks.chunks:
                        chunk_metadata = getattr(chunk, 'metadata', {})
                        if chunk_metadata.get('content_type') == 'image' or 'image' in chunk_metadata.get('file_type', ''):
                            image_chunks.append({
                                'chunk_id': getattr(chunk, 'id', ''),
                                'content': getattr(chunk, 'content', ''),
                                'metadata': chunk_metadata
                            })
                
                logger.info(f"Found {len(image_chunks)} image chunks")
                return image_chunks
                
            except Exception as chunk_error:
                logger.debug(f"Chunk retrieval failed: {chunk_error}")
            
            return []
            
        except Exception as e:
            logger.debug(f"Image retrieval failed: {e}")
            return []

    async def upload_document(self, file_path: str, metadata: Dict[str, Any]) -> RagieUploadResult:
        """
        Upload document to Ragie with enhanced error handling and async support
        
        Args:
            file_path: Path to the document file
            metadata: Document metadata
            
        Returns:
            Upload result
        """
        if not self.client:
            return RagieUploadResult(success=False, error="Ragie client not available")
        
        # Import error types for proper handling
        from ragie import models
        
        try:
            logger.info(f"📤 Starting Ragie upload: {file_path}")
            start_time = time.time()
            
            # Prepare enhanced metadata for Ragie
            ragie_metadata = {
                "equipment_type": metadata.get("equipment_type", "general"),
                "qsr_document_type": "manual",
                "upload_source": "line_lead_qsr",
                "original_filename": metadata.get("original_filename", ""),
                "file_size": metadata.get("file_size", 0),
                "pages_count": metadata.get("pages_count", 0),
                "upload_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Use proper resource management with context manager
            with self.client as ragie_client:
                with open(file_path, 'rb') as f:
                    create_request = {
                        "file": {
                            "file_name": Path(file_path).name,
                            "content": f,
                        },
                        "metadata": ragie_metadata,
                        "mode": "hi_res",  # Extract images and tables for QSR manuals
                        "partition": self.partition
                    }
                    
                    logger.info("🔄 Sending upload request to Ragie...")
                    response = ragie_client.documents.create(request=create_request)
            
            upload_time = time.time() - start_time
            
            if response and response.id:
                logger.info(f"✅ Document uploaded to Ragie: {response.id} (took {upload_time:.2f}s)")
                logger.info(f"📊 Ragie processing stats: {getattr(response, 'chunk_count', 'unknown')} chunks, {getattr(response, 'page_count', 'unknown')} pages")
                
                return RagieUploadResult(
                    success=True,
                    document_id=response.id,
                    filename=Path(file_path).name,
                    chunk_count=getattr(response, 'chunk_count', None)
                )
            else:
                logger.error("❌ Ragie upload returned invalid response")
                return RagieUploadResult(success=False, error="Invalid response from Ragie")
        
        # Enhanced error handling based on Ragie documentation
        except models.HTTPValidationError as e:
            logger.error(f"❌ Ragie validation error: {e.message}")
            return RagieUploadResult(success=False, error=f"Validation error: {e.message}")
        
        except models.ErrorMessage as e:
            logger.error(f"❌ Ragie API error: {e.message}")
            return RagieUploadResult(success=False, error=f"API error: {e.message}")
        
        except models.SDKError as e:
            logger.error(f"❌ Ragie SDK error: {e.message} (Status: {e.status_code})")
            return RagieUploadResult(success=False, error=f"SDK error: {e.message}")
            
        except Exception as e:
            logger.error(f"❌ Unexpected upload error: {e}")
            return RagieUploadResult(success=False, error=f"Unexpected error: {str(e)}")
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document from Ragie
        
        Args:
            document_id: Document ID in Ragie
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Ragie client not available")
            return False
        
        try:
            logger.info(f"🗑️ Deleting from Ragie: {document_id}")
            
            self.client.documents.delete(id=document_id)
            logger.info(f"✅ Document deleted from Ragie: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document from Ragie: {e}")
            return False

# Global service instance
clean_ragie_service = CleanRagieService()