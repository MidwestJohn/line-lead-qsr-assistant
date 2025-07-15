"""
Ragie Entity Management Service
Manages instructions and entity extraction to make images and documents searchable
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import httpx
import os

logger = logging.getLogger(__name__)

class RagieEntityManager:
    """Manages Ragie instructions and entity extraction for improved searchability"""
    
    def __init__(self):
        self.base_url = "https://api.ragie.ai"
        self.api_key = None
        self._initialize_api_key()
        
    def _initialize_api_key(self):
        """Initialize API key from environment"""
        try:
            # Get API key from environment
            self.api_key = os.getenv("RAGIE_API_KEY")
            
            # Fallback to keyring if available
            if not self.api_key:
                try:
                    import keyring
                    self.api_key = keyring.get_password("memex", "RAGIE_API_KEY")
                except ImportError:
                    pass
            
            if not self.api_key:
                logger.warning("No Ragie API key found - entity management disabled")
            else:
                logger.info("Ragie entity management initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Ragie API key: {e}")
    
    def is_available(self) -> bool:
        """Check if the entity manager is available"""
        return self.api_key is not None
    
    async def list_instructions(self) -> List[Dict[str, Any]]:
        """List all existing instructions"""
        if not self.is_available():
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/instructions",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to list instructions: {e}")
            return []
    
    async def create_equipment_image_instruction(self) -> Optional[str]:
        """Create instruction to extract equipment information from images"""
        if not self.is_available():
            return None
        
        instruction_data = {
            "name": "equipment_image_metadata",
            "active": True,
            "scope": "document",  # Analyze full image
            "prompt": """Analyze this image and extract equipment information. Look for:
            - Equipment model numbers (like OV520E1, CV123, etc.)
            - Equipment brands/manufacturers (like Baxter, Taylor, Hobart, etc.)
            - Equipment types (oven, fryer, slicer, freezer, etc.)
            - Any visible text, labels, or part numbers
            - Equipment categories (heating, refrigeration, prep, etc.)
            
            If this is a diagram, schematic, or technical drawing, identify:
            - What equipment it shows
            - Type of diagram (electrical, parts, assembly, etc.)
            - Any model numbers or specifications visible
            
            Extract all identifiable information to make this equipment searchable.""",
            "entity_schema": {
                "type": "object",
                "properties": {
                    "equipment_info": {
                        "type": "object",
                        "properties": {
                            "model_number": {
                                "type": "string",
                                "description": "Equipment model number if visible"
                            },
                            "manufacturer": {
                                "type": "string", 
                                "description": "Equipment manufacturer or brand"
                            },
                            "equipment_type": {
                                "type": "string",
                                "description": "Type of equipment (oven, fryer, etc.)"
                            },
                            "category": {
                                "type": "string",
                                "description": "Equipment category (heating, refrigeration, etc.)"
                            },
                            "diagram_type": {
                                "type": "string",
                                "description": "Type of diagram if applicable (electrical, parts, etc.)"
                            },
                            "visible_text": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Any visible text, labels, or part numbers"
                            },
                            "searchable_terms": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "Key terms to make this equipment findable"
                            }
                        }
                    }
                }
            },
            "filter": {
                "document_type": {"$in": ["PNG", "JPG", "JPEG", "PDF", "image"]}
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/instructions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=instruction_data
                )
                response.raise_for_status()
                result = response.json()
                instruction_id = result.get("id")
                logger.info(f"✅ Created equipment image instruction: {instruction_id}")
                return instruction_id
        except Exception as e:
            logger.error(f"Failed to create equipment image instruction: {e}")
            return None
    
    async def create_general_document_instruction(self) -> Optional[str]:
        """Create instruction to extract general document metadata"""
        if not self.is_available():
            return None
        
        instruction_data = {
            "name": "general_document_metadata", 
            "active": True,
            "scope": "document",
            "prompt": """Extract key metadata and searchable information from this document. Look for:
            - Document type and purpose
            - Key topics and subjects covered
            - Important names, models, or identifiers
            - Equipment or product references
            - Procedures or processes described
            - Safety information
            - Technical specifications
            
            Make this document easily findable by extracting the most important searchable terms.""",
            "entity_schema": {
                "type": "object",
                "properties": {
                    "document_metadata": {
                        "type": "object", 
                        "properties": {
                            "document_type": {
                                "type": "string",
                                "description": "Type of document (manual, guide, diagram, etc.)"
                            },
                            "main_topics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Main topics or subjects covered"
                            },
                            "equipment_mentioned": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "Equipment, models, or products mentioned"
                            },
                            "key_procedures": {
                                "type": "array",
                                "items": {"type": "string"}, 
                                "description": "Key procedures or processes described"
                            },
                            "safety_topics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Safety-related topics or warnings"
                            },
                            "searchable_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Important keywords for searchability"
                            }
                        }
                    }
                }
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/instructions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=instruction_data
                )
                response.raise_for_status()
                result = response.json()
                instruction_id = result.get("id")
                logger.info(f"✅ Created general document instruction: {instruction_id}")
                return instruction_id
        except Exception as e:
            logger.error(f"Failed to create general document instruction: {e}")
            return None
    
    async def trigger_document_reprocessing(self, document_id: str) -> bool:
        """Trigger reprocessing of a document to apply new instructions
        
        Uses the patch_metadata endpoint to update metadata, which should trigger
        entity extraction for active instructions.
        """
        if not self.is_available():
            return False
        
        try:
            import datetime
            
            # Use PATCH metadata to trigger reprocessing with updated metadata
            # This is the correct approach for triggering entity extraction
            async with httpx.AsyncClient() as client:
                update_data = {
                    "metadata": {
                        "entity_extraction_triggered": datetime.datetime.now().isoformat(),
                        "reprocessing_requested": True,
                        "instructions_version": "v2025.1"
                    }
                }
                
                # Use the correct PATCH metadata endpoint
                update_response = await client.patch(
                    f"{self.base_url}/documents/{document_id}/metadata",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=update_data
                )
                update_response.raise_for_status()
                logger.info(f"✅ Triggered metadata update for document: {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to trigger document reprocessing: {e}")
            return False
    
    async def trigger_file_reprocessing(self, document_id: str, file_path: str) -> bool:
        """Trigger full document reprocessing by updating the file
        
        This is the most reliable way to trigger entity extraction as it 
        completely reprocesses the document through the full pipeline.
        """
        if not self.is_available():
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                # Read the file
                with open(file_path, 'rb') as f:
                    files = {
                        "file": (os.path.basename(file_path), f, "application/octet-stream")
                    }
                    
                    # Use the update_file endpoint to trigger full reprocessing
                    update_response = await client.put(
                        f"{self.base_url}/documents/{document_id}/file",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files
                    )
                    update_response.raise_for_status()
                    
                logger.info(f"✅ Triggered file reprocessing for document: {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to trigger file reprocessing: {e}")
            return False
    
    async def get_document_entities(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all extracted entities for a document"""
        if not self.is_available():
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/entities/document/{document_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("entities", [])
        except Exception as e:
            logger.error(f"Failed to get document entities: {e}")
            return []
    
    async def get_document_details(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get complete document details including status and metadata"""
        if not self.is_available():
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/documents/{document_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get document details: {e}")
            return None
    
    async def get_document_content(self, document_id: str, as_json: bool = True) -> Optional[Dict[str, Any]]:
        """Get document content with metadata"""
        if not self.is_available():
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if as_json:
                    params["media_type"] = "application/json"
                
                response = await client.get(
                    f"{self.base_url}/documents/{document_id}/content",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params=params
                )
                response.raise_for_status()
                return response.json() if as_json else response.content
        except Exception as e:
            logger.error(f"Failed to get document content: {e}")
            return None
    
    async def get_document_summary(self, document_id: str) -> Optional[str]:
        """Get LLM-generated summary of the document"""
        if not self.is_available():
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/documents/{document_id}/summary",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("summary", "")
        except Exception as e:
            logger.error(f"Failed to get document summary: {e}")
            return None
    
    async def get_document_chunks(self, document_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get document chunks with pagination"""
        if not self.is_available():
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                params = {"limit": limit}
                response = await client.get(
                    f"{self.base_url}/documents/{document_id}/chunks",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params=params
                )
                response.raise_for_status()
                result = response.json()
                return result.get("chunks", [])
        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []
    
    async def setup_equipment_searchability(self) -> Dict[str, Any]:
        """Setup instructions to make equipment images and documents searchable"""
        results = {
            "equipment_instruction_id": None,
            "general_instruction_id": None,
            "success": False,
            "message": ""
        }
        
        if not self.is_available():
            results["message"] = "Ragie API key not available"
            return results
        
        try:
            # Check existing instructions first
            existing_instructions = await self.list_instructions()
            existing_names = [inst.get("name", "") for inst in existing_instructions]
            
            # Create equipment image instruction if not exists
            if "equipment_image_metadata" not in existing_names:
                equipment_id = await self.create_equipment_image_instruction()
                results["equipment_instruction_id"] = equipment_id
            else:
                logger.info("Equipment image instruction already exists")
                for inst in existing_instructions:
                    if inst.get("name") == "equipment_image_metadata":
                        results["equipment_instruction_id"] = inst.get("id")
            
            # Create general document instruction if not exists  
            if "general_document_metadata" not in existing_names:
                general_id = await self.create_general_document_instruction()
                results["general_instruction_id"] = general_id
            else:
                logger.info("General document instruction already exists")
                for inst in existing_instructions:
                    if inst.get("name") == "general_document_metadata":
                        results["general_instruction_id"] = inst.get("id")
            
            if results["equipment_instruction_id"] or results["general_instruction_id"]:
                results["success"] = True
                results["message"] = "Entity extraction instructions configured successfully"
            else:
                results["message"] = "Instructions already exist"
                results["success"] = True
            
        except Exception as e:
            logger.error(f"Failed to setup equipment searchability: {e}")
            results["message"] = f"Setup failed: {e}"
        
        return results

# Global instance
ragie_entity_manager = RagieEntityManager()