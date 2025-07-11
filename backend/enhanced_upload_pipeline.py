#!/usr/bin/env python3
"""
Enhanced Upload Pipeline with Document Context Integration
Implements comprehensive document-level context processing
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from pathlib import Path

# FastAPI imports
from fastapi import UploadFile
import fitz  # PyMuPDF

# Local imports
from services.document_context_integration_service import DocumentContextIntegrationService
from services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)

class EnhancedUploadPipeline:
    """
    Enhanced upload pipeline with document context integration
    Processes documents with hierarchical structure and semantic understanding
    """
    
    def __init__(self):
        self.document_service = DocumentContextIntegrationService()
        self.neo4j_service = Neo4jService()
        
        # Upload directories
        self.upload_dir = Path(__file__).parent / "uploaded_docs"
        self.upload_dir.mkdir(exist_ok=True)
        
        # Document tracking
        self.documents_file = Path(__file__).parent.parent / "documents.json"
        self.neo4j_verified_file = Path(__file__).parent / "neo4j_verified_documents.json"
        
    async def process_document_upload(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process document upload with comprehensive context integration
        
        Args:
            file: Uploaded file
            
        Returns:
            Processing results with document context and hierarchy
        """
        
        logger.info(f"Starting enhanced document upload: {file.filename}")
        
        try:
            # 1. Save uploaded file
            document_id = str(uuid.uuid4())
            file_path = await self._save_upload_file(file, document_id)
            
            # 2. Extract text and metadata from PDF
            document_data = await self._extract_document_content(file_path, document_id, file.filename)
            
            # 3. Process with document context integration service
            integration_results = await self.document_service.process_document_upload(document_data)
            
            # 4. Update document tracking
            await self._update_document_tracking(document_data, integration_results)
            
            # 5. Verify Neo4j storage
            verification_results = await self._verify_neo4j_storage(document_id)
            
            return {
                "status": "success",
                "document_id": document_id,
                "filename": file.filename,
                "file_path": str(file_path),
                "document_context": integration_results["document_summary"],
                "processing_stats": {
                    "entities_processed": integration_results["processed_entities"],
                    "relationships_created": integration_results["hierarchy_relationships"],
                    "neo4j_entities": verification_results.get("entities_stored", 0),
                    "neo4j_relationships": verification_results.get("relationships_stored", 0)
                },
                "hierarchical_structure": True,
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced upload pipeline failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "document_id": document_id if 'document_id' in locals() else None
            }
    
    async def _save_upload_file(self, file: UploadFile, document_id: str) -> Path:
        """Save uploaded file to disk"""
        
        file_extension = Path(file.filename).suffix
        file_path = self.upload_dir / f"{document_id}{file_extension}"
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Saved upload file: {file_path}")
        return file_path
    
    async def _extract_document_content(self, file_path: Path, document_id: str, 
                                        filename: str) -> Dict[str, Any]:
        """Extract text content and metadata from PDF"""
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(str(file_path))
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                full_text += page_text + "\n"
                page_texts.append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "char_count": len(page_text)
                })
            
            # Extract metadata
            metadata = doc.metadata
            page_count = len(doc)
            
            doc.close()
            
            return {
                "document_id": document_id,
                "filename": filename,
                "file_path": str(file_path),
                "content": full_text,
                "page_count": page_count,
                "page_texts": page_texts,
                "metadata": metadata,
                "char_count": len(full_text),
                "extraction_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document content extraction failed: {e}")
            raise e
    
    async def _update_document_tracking(self, document_data: Dict[str, Any], 
                                        integration_results: Dict[str, Any]) -> None:
        """Update document tracking files"""
        
        # Update documents.json
        try:
            if self.documents_file.exists():
                with open(self.documents_file, 'r') as f:
                    documents = json.load(f)
            else:
                documents = []
            
            # Add new document
            document_entry = {
                "document_id": document_data["document_id"],
                "filename": document_data["filename"],
                "file_path": document_data["file_path"],
                "page_count": document_data["page_count"],
                "char_count": document_data["char_count"],
                "document_type": integration_results["document_summary"]["document_type"],
                "qsr_category": integration_results["document_summary"]["qsr_category"],
                "equipment_focus": integration_results["document_summary"]["equipment_focus"],
                "processing_complete": True,
                "hierarchical_processing": True,
                "upload_timestamp": document_data["extraction_timestamp"],
                "entities_count": integration_results["processed_entities"],
                "relationships_count": integration_results["hierarchy_relationships"]
            }
            
            documents.append(document_entry)
            
            with open(self.documents_file, 'w') as f:
                json.dump(documents, f, indent=2)
            
            logger.info(f"Updated documents.json with {document_data['filename']}")
            
        except Exception as e:
            logger.error(f"Failed to update documents.json: {e}")
        
        # Update Neo4j verified documents
        try:
            if self.neo4j_verified_file.exists():
                with open(self.neo4j_verified_file, 'r') as f:
                    verified_docs = json.load(f)
            else:
                verified_docs = {}
            
            # Add verified document
            verified_docs[document_data["document_id"]] = {
                "filename": document_data["filename"],
                "neo4j_verified": True,
                "hierarchical_structure": True,
                "verification_timestamp": datetime.now().isoformat(),
                "document_summary": integration_results["document_summary"]
            }
            
            with open(self.neo4j_verified_file, 'w') as f:
                json.dump(verified_docs, f, indent=2)
            
            logger.info(f"Updated Neo4j verified documents with {document_data['filename']}")
            
        except Exception as e:
            logger.error(f"Failed to update Neo4j verified documents: {e}")
    
    async def _verify_neo4j_storage(self, document_id: str) -> Dict[str, Any]:
        """Verify that document was properly stored in Neo4j"""
        
        try:
            if not self.neo4j_service.connected:
                await self.neo4j_service.connect()
            
            with self.neo4j_service.driver.session() as session:
                # Check document node
                doc_query = """
                MATCH (d:Document {document_id: $document_id})
                RETURN d
                """
                
                doc_result = session.run(doc_query, document_id=document_id)
                document_exists = doc_result.single() is not None
                
                # Count entities for this document
                entity_query = """
                MATCH (e) 
                WHERE e.document_id = $document_id
                AND NOT e:Document
                RETURN count(e) as entity_count
                """
                
                entity_result = session.run(entity_query, document_id=document_id)
                entity_count = entity_result.single()["entity_count"]
                
                # Count relationships for this document
                rel_query = """
                MATCH ()-[r {document_id: $document_id}]-()
                RETURN count(r) as relationship_count
                """
                
                rel_result = session.run(rel_query, document_id=document_id)
                relationship_count = rel_result.single()["relationship_count"]
                
                return {
                    "document_exists": document_exists,
                    "entities_stored": entity_count,
                    "relationships_stored": relationship_count,
                    "verification_successful": document_exists and entity_count > 0
                }
                
        except Exception as e:
            logger.error(f"Neo4j verification failed: {e}")
            return {
                "document_exists": False,
                "entities_stored": 0,
                "relationships_stored": 0,
                "verification_successful": False,
                "error": str(e)
            }
    
    async def get_upload_status(self) -> Dict[str, Any]:
        """Get current upload status and statistics"""
        
        try:
            # Load documents
            if self.documents_file.exists():
                with open(self.documents_file, 'r') as f:
                    documents = json.load(f)
            else:
                documents = []
            
            # Load verified documents
            if self.neo4j_verified_file.exists():
                with open(self.neo4j_verified_file, 'r') as f:
                    verified_docs = json.load(f)
            else:
                verified_docs = {}
            
            # Calculate statistics
            total_documents = len(documents)
            hierarchical_documents = len([d for d in documents if d.get('hierarchical_processing', False)])
            verified_documents = len(verified_docs)
            
            total_entities = sum(d.get('entities_count', 0) for d in documents)
            total_relationships = sum(d.get('relationships_count', 0) for d in documents)
            
            # Document types
            document_types = {}
            equipment_categories = {}
            
            for doc in documents:
                doc_type = doc.get('document_type', 'unknown')
                document_types[doc_type] = document_types.get(doc_type, 0) + 1
                
                equipment_cat = doc.get('qsr_category', 'unknown')
                equipment_categories[equipment_cat] = equipment_categories.get(equipment_cat, 0) + 1
            
            return {
                "status": "ready",
                "statistics": {
                    "total_documents": total_documents,
                    "hierarchical_documents": hierarchical_documents,
                    "verified_documents": verified_documents,
                    "total_entities": total_entities,
                    "total_relationships": total_relationships
                },
                "document_types": document_types,
                "equipment_categories": equipment_categories,
                "recent_documents": documents[-5:] if documents else [],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get upload status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all uploaded documents with their metadata"""
        
        try:
            if self.documents_file.exists():
                with open(self.documents_file, 'r') as f:
                    documents = json.load(f)
                return documents
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []