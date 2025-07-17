#!/usr/bin/env python3
"""
Ragie Upload Service
===================

Handles document uploads to Ragie, replacing the complex LightRAG/Neo4j pipeline.
Provides QSR-specific metadata enhancement and batch processing capabilities.

Author: Generated with Memex (https://memex.tech)
"""

import logging
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from fastapi import UploadFile, BackgroundTasks
from services.ragie_service import ragie_service
from models.ragie_models import RagieUploadResponse, QSRMetadata

logger = logging.getLogger(__name__)

class RagieUploadService:
    """Service for handling document uploads to Ragie"""
    
    def __init__(self):
        """Initialize the upload service"""
        self.upload_dir = Path("../uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
        # Track upload progress for status endpoints
        self.upload_progress = {}
        
    async def upload_document(self, file: UploadFile, background_tasks: BackgroundTasks, 
                            metadata: Optional[Dict[str, Any]] = None) -> RagieUploadResponse:
        """
        Upload a document to Ragie with QSR enhancement
        
        Args:
            file: Uploaded file from FastAPI
            background_tasks: Background tasks for async processing
            metadata: Optional metadata dictionary
            
        Returns:
            Upload response with document ID and status
        """
        upload_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        try:
            # Initialize progress tracking
            self.upload_progress[upload_id] = {
                "status": "starting",
                "filename": file.filename,
                "progress": 0.0,
                "message": "Upload starting...",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Starting Ragie upload: {file.filename}")
            
            # Validate file
            validation_result = await self._validate_file(file)
            if not validation_result["valid"]:
                return RagieUploadResponse(
                    success=False,
                    filename=file.filename,
                    error=validation_result["error"]
                )
            
            # Save file temporarily
            temp_path = await self._save_temp_file(file)
            self._update_progress(upload_id, 20.0, "File saved, processing...")
            
            # Enhance metadata with QSR-specific information
            enhanced_metadata = self._enhance_metadata(file.filename, metadata or {})
            self._update_progress(upload_id, 40.0, "Metadata enhanced...")
            
            # Upload to Ragie
            upload_result = await ragie_service.upload_document(str(temp_path), enhanced_metadata)
            self._update_progress(upload_id, 80.0, "Uploaded to Ragie...")
            
            if upload_result["success"]:
                # Save document record for compatibility
                await self._save_document_record(upload_result, enhanced_metadata)
                self._update_progress(upload_id, 100.0, "Upload complete!")
                
                # Cleanup temp file
                if temp_path.exists():
                    temp_path.unlink()
                
                logger.info(f"Successfully uploaded {file.filename} to Ragie: {upload_result['document_id']}")
                
                return RagieUploadResponse(
                    success=True,
                    document_id=upload_result["document_id"],
                    filename=file.filename,
                    chunk_count=upload_result.get("chunk_count"),
                    page_count=upload_result.get("page_count"),
                    ragie_metadata=enhanced_metadata
                )
                
            else:
                self._update_progress(upload_id, 0.0, f"Upload failed: {upload_result.get('error')}")
                return RagieUploadResponse(
                    success=False,
                    filename=file.filename,
                    error=upload_result.get("error", "Unknown upload error")
                )
                
        except Exception as e:
            error_msg = f"Upload processing failed: {str(e)}"
            logger.error(f"Upload failed for {file.filename}: {e}")
            self._update_progress(upload_id, 0.0, error_msg)
            
            return RagieUploadResponse(
                success=False,
                filename=file.filename,
                error=error_msg
            )
    
    async def batch_upload_documents(self, upload_dir: str) -> Dict[str, Any]:
        """
        Batch upload multiple documents from a directory
        
        Args:
            upload_dir: Directory containing documents to upload
            
        Returns:
            Batch upload results
        """
        upload_dir_path = Path(upload_dir)
        if not upload_dir_path.exists():
            return {"success": False, "error": f"Directory {upload_dir} does not exist"}
        
        # Find all supported files
        supported_extensions = {".pdf", ".txt", ".doc", ".docx"}
        files_to_upload = []
        
        for file_path in upload_dir_path.rglob("*"):
            if file_path.suffix.lower() in supported_extensions:
                files_to_upload.append(file_path)
        
        logger.info(f"Found {len(files_to_upload)} files for batch upload")
        
        # Upload files
        results = []
        successful_uploads = 0
        
        for file_path in files_to_upload:
            try:
                # Extract metadata from file path and name
                metadata = self._extract_metadata_from_path(file_path)
                
                # Upload to Ragie
                upload_result = await ragie_service.upload_document(str(file_path), metadata)
                
                if upload_result["success"]:
                    successful_uploads += 1
                    await self._save_document_record(upload_result, metadata)
                
                results.append({
                    "filename": file_path.name,
                    "success": upload_result["success"],
                    "document_id": upload_result.get("document_id"),
                    "error": upload_result.get("error")
                })
                
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")
                results.append({
                    "filename": file_path.name,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": successful_uploads > 0,
            "total_files": len(files_to_upload),
            "successful_uploads": successful_uploads,
            "failed_uploads": len(files_to_upload) - successful_uploads,
            "results": results
        }
    
    def get_upload_status(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get upload progress status"""
        return self.upload_progress.get(upload_id)
    
    async def _validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        # Check file size (10MB limit)
        if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
            return {"valid": False, "error": "File size exceeds 10MB limit"}
        
        # Check file extension
        allowed_extensions = {".pdf", ".txt", ".doc", ".docx", ".md"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            return {"valid": False, "error": f"File type {file_ext} not supported"}
        
        return {"valid": True}
    
    async def _save_temp_file(self, file: UploadFile) -> Path:
        """Save uploaded file to temporary location"""
        # Create temp file with original extension
        suffix = Path(file.filename).suffix
        temp_file = Path(tempfile.mktemp(suffix=suffix))
        
        # Read and save file content
        content = await file.read()
        with open(temp_file, 'wb') as f:
            f.write(content)
        
        # Reset file pointer for potential re-reading
        await file.seek(0)
        
        return temp_file
    
    def _enhance_metadata(self, filename: str, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata with QSR-specific information"""
        # Create QSR metadata object for validation
        qsr_metadata = QSRMetadata(
            display_name=base_metadata.get("original_filename", filename)
        )
        
        # Auto-detect from filename
        filename_lower = filename.lower()
        
        # Equipment type detection
        equipment_map = {
            "fryer": "fryer",
            "grill": "grill", 
            "oven": "oven",
            "ice": "ice_machine",
            "pos": "pos_system",
            "drive": "drive_thru",
            "mixer": "mixer",
            "dishwasher": "dishwasher"
        }
        
        for keyword, equipment_type in equipment_map.items():
            if keyword in filename_lower:
                qsr_metadata.equipment_type = equipment_type
                break
        
        # Document type detection (using qsr_document_type to avoid reserved keys)
        if "manual" in filename_lower:
            qsr_metadata.qsr_document_type = "manual"
        elif "cleaning" in filename_lower:
            qsr_metadata.qsr_document_type = "cleaning_guide"
            qsr_metadata.procedure_type = "cleaning"
        elif "safety" in filename_lower:
            qsr_metadata.qsr_document_type = "safety_protocol"
            qsr_metadata.safety_level = "critical"
        elif "manager" in filename_lower:
            qsr_metadata.qsr_document_type = "management_guide"
            qsr_metadata.target_role = "manager"
        
        # Convert to dict and merge with base metadata
        enhanced = qsr_metadata.dict(exclude_none=True)
        enhanced.update(base_metadata)
        
        # Add upload timestamp
        enhanced["upload_timestamp"] = datetime.now().isoformat()
        
        return enhanced
    
    def _extract_metadata_from_path(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file path for batch uploads"""
        metadata = {
            "original_filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "source": "batch_upload"
        }
        
        # Try to extract equipment/category from parent directory
        parent_dir = file_path.parent.name.lower()
        
        equipment_keywords = ["fryer", "grill", "oven", "ice", "pos", "drive"]
        for keyword in equipment_keywords:
            if keyword in parent_dir:
                metadata["equipment_type"] = keyword
                break
        
        return self._enhance_metadata(file_path.name, metadata)
    
    async def _save_document_record(self, upload_result: Dict[str, Any], 
                                  metadata: Dict[str, Any]) -> None:
        """Save document record for compatibility with existing system"""
        try:
            # Load existing documents
            docs_file = Path("../documents.json")
            
            if docs_file.exists():
                with open(docs_file, 'r') as f:
                    docs_db = json.load(f)
            else:
                docs_db = {}
            
            # Create document record
            doc_id = upload_result["document_id"]
            docs_db[doc_id] = {
                "id": doc_id,
                "filename": upload_result["filename"],
                "original_filename": metadata.get("display_name", upload_result["filename"]),
                "upload_timestamp": metadata.get("upload_timestamp", datetime.now().isoformat()),
                "file_size": metadata.get("file_size", 0),
                "pages_count": upload_result.get("page_count", 0),
                "text_preview": f"Document uploaded to Ragie: {upload_result['filename'][:100]}...",
                "ragie_document_id": doc_id,
                "source": "ragie_integration"
            }
            
            # Save updated database
            with open(docs_file, 'w') as f:
                json.dump(docs_db, f, indent=2)
            
            logger.info(f"Saved document record for {doc_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save document record: {e}")
    
    def _update_progress(self, upload_id: str, progress: float, message: str) -> None:
        """Update upload progress"""
        if upload_id in self.upload_progress:
            self.upload_progress[upload_id].update({
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            
            if progress >= 100.0:
                self.upload_progress[upload_id]["status"] = "completed"
            elif progress <= 0.0:
                self.upload_progress[upload_id]["status"] = "failed"
            else:
                self.upload_progress[upload_id]["status"] = "processing"

# Global instance
ragie_upload_service = RagieUploadService()