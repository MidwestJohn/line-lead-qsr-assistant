#!/usr/bin/env python3
"""
QSR-Optimized Ragie Service
===========================

Comprehensive implementation following the enhanced philosophy:
- Structured QSR response models
- Metadata filtering with MongoDB-style queries
- Multi-format file upload support
- Type-safe integration patterns
- Production-ready error handling

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import time
import json
from typing import Dict, List, Optional, Any, Union, IO
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import mimetypes

# Load environment variables
load_dotenv()

# Ragie SDK imports
try:
    from ragie import Ragie
    from ragie.utils import BackoffStrategy, RetryConfig
    RAGIE_AVAILABLE = True
except ImportError:
    RAGIE_AVAILABLE = False
    logging.warning("Ragie SDK not available. Install with: pip install ragie")

# Import our QSR models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.qsr_models import (
        QSRTaskResponse, QSRSearchResult, QSRSearchRequest, QSRUploadMetadata,
        MediaReference, EquipmentReference, SafetyWarning, ProcedureStep,
        QSR_EQUIPMENT_TYPES, QSR_PROCEDURE_TYPES, QSR_SAFETY_LEVELS
    )
    QSR_MODELS_AVAILABLE = True
except ImportError as e:
    logger.error(f"QSR models not available: {e}")
    QSR_MODELS_AVAILABLE = False

logger = logging.getLogger(__name__)

class QSRRagieService:
    """
    Comprehensive QSR-optimized Ragie service implementing the full philosophy
    """
    
    # Multi-format file support as outlined in philosophy
    SUPPORTED_FORMATS = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'mp4': 'video/mp4',
        'txt': 'text/plain',
        'docm': 'application/vnd.ms-word.document.macroEnabled.12',
        'xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12'
    }
    
    def __init__(self):
        """Initialize QSR Ragie service with production-ready configuration"""
        self.api_key = os.getenv("RAGIE_API_KEY")
        self.partition = os.getenv("RAGIE_PARTITION", "qsr_manuals")
        self.available = RAGIE_AVAILABLE and bool(self.api_key) and QSR_MODELS_AVAILABLE
        
        if self.available:
            # Configure retry strategy for production reliability
            retry_config = RetryConfig(
                strategy="backoff",
                backoff=BackoffStrategy(
                    initial_interval=1,
                    max_interval=30,
                    exponent=1.5,
                    max_elapsed_time=300
                ),
                retry_connection_errors=True
            )
            
            self.client = Ragie(
                auth=self.api_key,
                retry_config=retry_config,
                debug_logger=logger
            )
            logger.info("✅ QSR Ragie service initialized with production configuration")
        else:
            self.client = None
            logger.warning("❌ QSR Ragie service not available (missing API key or SDK)")
    
    def is_available(self) -> bool:
        """Check if service is available for operations"""
        return self.available
    
    async def upload_qsr_document(
        self, 
        file_content: Union[bytes, IO], 
        filename: str,
        metadata: Optional[QSRUploadMetadata] = None
    ) -> Dict[str, Any]:
        """
        Upload document with QSR-specific metadata classification
        
        Args:
            file_content: File content as bytes or file-like object
            filename: Original filename
            metadata: QSR metadata for classification
            
        Returns:
            Upload result with document ID and processing status
        """
        if not self.available:
            return {"success": False, "error": "Ragie service not available"}
        
        try:
            # Validate file format
            file_ext = Path(filename).suffix.lower().lstrip('.')
            if file_ext not in self.SUPPORTED_FORMATS:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {file_ext}. Supported: {list(self.SUPPORTED_FORMATS.keys())}"
                }
            
            # Auto-generate metadata if not provided
            if metadata is None:
                metadata = self._auto_classify_document(filename)
            
            # Convert QSR metadata to Ragie format
            ragie_metadata = self._convert_to_ragie_metadata(metadata)
            
            # Prepare file for upload
            if isinstance(file_content, bytes):
                file_data = file_content
            else:
                file_data = file_content.read()
            
            # Upload to Ragie with enhanced metadata
            logger.info(f"🔄 Uploading {filename} to Ragie with QSR metadata...")
            
            response = self.client.documents.create(request={
                "file": {
                    "file_name": filename,
                    "content": file_data
                },
                "metadata": ragie_metadata,
                "partition": self.partition,
                "mode": "hi_res" if self._requires_hi_res(filename, metadata) else "fast"
            })
            
            document_id = getattr(response, 'id', 'unknown')
            logger.info(f"✅ Successfully uploaded {filename} with document ID: {document_id}")
            
            return {
                "success": True,
                "document_id": document_id,
                "filename": filename,
                "metadata": ragie_metadata,
                "processing_mode": "hi_res" if self._requires_hi_res(filename, metadata) else "fast"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {filename}: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_qsr_procedures(self, search_request: QSRSearchRequest) -> List[QSRSearchResult]:
        """
        Search with QSR-specific metadata filtering following the philosophy
        
        Args:
            search_request: Structured search request with QSR parameters
            
        Returns:
            List of QSR-enhanced search results
        """
        if not self.available:
            logger.warning("Ragie service not available for search")
            return []
        
        try:
            start_time = time.time()
            
            # Build MongoDB-style filter criteria as outlined in philosophy
            filter_criteria = self._build_qsr_filter(search_request)
            
            # Enhanced query preprocessing for QSR context
            processed_query = self._enhance_qsr_query(search_request.query, search_request)
            
            # Execute search with Ragie
            logger.info(f"🔍 Searching QSR procedures: '{search_request.query}' → '{processed_query}'")
            
            ragie_request = {
                "query": processed_query,
                "rerank": True,
                "partition": self.partition,
                "limit": search_request.max_results,
                "mode": "hi_res" if search_request.include_images else "fast"
            }
            
            if filter_criteria:
                ragie_request["filter"] = filter_criteria
                logger.info(f"🎯 Applying QSR filter: {filter_criteria}")
            
            response = self.client.retrievals.retrieve(request=ragie_request)
            
            # Convert to QSR-enhanced results
            results = []
            if hasattr(response, 'scored_chunks') and response.scored_chunks:
                for chunk in response.scored_chunks:
                    qsr_result = self._convert_to_qsr_result(chunk)
                    results.append(qsr_result)
            
            search_time = time.time() - start_time
            logger.info(f"✅ Found {len(results)} QSR results in {search_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ QSR search failed: {e}")
            return []
    
    async def get_structured_qsr_response(
        self, 
        search_request: QSRSearchRequest
    ) -> QSRTaskResponse:
        """
        Get comprehensive structured QSR response following the philosophy
        
        This method combines search results into a complete QSRTaskResponse
        with steps, safety warnings, equipment needs, and media references.
        """
        try:
            start_time = time.time()
            
            # Perform QSR-optimized search
            search_results = await self.search_qsr_procedures(search_request)
            
            if not search_results:
                # Return empty but valid response
                return QSRTaskResponse(
                    task_title=f"No procedures found for: {search_request.query}",
                    steps=[],
                    estimated_time="Unknown",
                    confidence_level=0.0,
                    procedure_type='training',  # Default fallback
                    source_documents=[],
                    ragie_search_time=time.time() - start_time
                )
            
            # Parse results into structured QSR response
            qsr_response = self._parse_results_to_qsr_response(search_results, search_request)
            qsr_response.ragie_search_time = time.time() - start_time
            
            logger.info(f"✅ Generated structured QSR response with {len(qsr_response.steps)} steps")
            return qsr_response
            
        except Exception as e:
            logger.error(f"❌ Failed to generate structured QSR response: {e}")
            # Return error response
            return QSRTaskResponse(
                task_title=f"Error processing: {search_request.query}",
                steps=[ProcedureStep(
                    step_number=1,
                    instruction=f"Unable to retrieve procedure information. Error: {str(e)}",
                    safety_notes=["Contact management for assistance"]
                )],
                estimated_time="Unknown",
                confidence_level=0.0,
                procedure_type='training',
                source_documents=[],
                ragie_search_time=0.0
            )
    
    def _auto_classify_document(self, filename: str) -> QSRUploadMetadata:
        """Auto-classify document based on filename patterns"""
        filename_lower = filename.lower()
        
        # Detect equipment types
        equipment_types = []
        for equipment in QSR_EQUIPMENT_TYPES:
            if equipment in filename_lower:
                equipment_types.append(equipment)
        
        # Detect procedure types
        procedure_types = []
        for procedure in QSR_PROCEDURE_TYPES:
            if procedure in filename_lower:
                procedure_types.append(procedure)
        
        # Detect document type
        if any(word in filename_lower for word in ['manual', 'guide', 'instruction']):
            doc_type = 'manual'
        elif any(word in filename_lower for word in ['sop', 'procedure', 'protocol']):
            doc_type = 'sop'
        elif any(word in filename_lower for word in ['safety', 'hazard', 'msds']):
            doc_type = 'safety'
        elif any(word in filename_lower for word in ['train', 'learn', 'course']):
            doc_type = 'training'
        else:
            doc_type = 'reference'
        
        # Detect safety level
        safety_level = None
        if any(word in filename_lower for word in ['critical', 'danger', 'warning']):
            safety_level = 'critical'
        elif any(word in filename_lower for word in ['safety', 'caution']):
            safety_level = 'high'
        
        # Detect media content
        file_ext = Path(filename).suffix.lower()
        contains_images = file_ext in ['.jpg', '.jpeg', '.png', '.pdf']
        contains_diagrams = 'diagram' in filename_lower or 'schematic' in filename_lower
        contains_procedures = any(word in filename_lower for word in ['step', 'procedure', 'process'])
        
        return QSRUploadMetadata(
            original_filename=filename,
            file_type=file_ext.lstrip('.'),
            equipment_types=equipment_types,
            procedure_types=procedure_types,
            safety_level=safety_level,
            document_type=doc_type,
            contains_images=contains_images,
            contains_diagrams=contains_diagrams,
            contains_procedures=contains_procedures
        )
    
    def _convert_to_ragie_metadata(self, qsr_metadata: QSRUploadMetadata) -> Dict[str, Any]:
        """Convert QSR metadata to Ragie format"""
        return {
            "original_filename": qsr_metadata.original_filename,
            "file_type": qsr_metadata.file_type,
            "equipment_types": qsr_metadata.equipment_types,
            "procedure_types": qsr_metadata.procedure_types,
            "safety_level": qsr_metadata.safety_level,
            "document_type": qsr_metadata.document_type,
            "contains_images": qsr_metadata.contains_images,
            "contains_diagrams": qsr_metadata.contains_diagrams,
            "contains_procedures": qsr_metadata.contains_procedures,
            "language": qsr_metadata.language,
            "department": qsr_metadata.department,
            "version": qsr_metadata.version,
            "uploaded_by": qsr_metadata.uploaded_by,
            "upload_timestamp": qsr_metadata.upload_timestamp.isoformat() if qsr_metadata.upload_timestamp else None
        }
    
    def _requires_hi_res(self, filename: str, metadata: Optional[QSRUploadMetadata]) -> bool:
        """Determine if document requires hi_res processing for images/diagrams"""
        file_ext = Path(filename).suffix.lower()
        
        # Always use hi_res for image files
        if file_ext in ['.jpg', '.jpeg', '.png', '.pdf']:
            return True
        
        # Use hi_res if metadata indicates visual content
        if metadata and (metadata.contains_images or metadata.contains_diagrams):
            return True
        
        # Use hi_res for complex document formats
        if file_ext in ['.docx', '.pptx', '.xlsx']:
            return True
        
        return False
    
    def _build_qsr_filter(self, search_request: QSRSearchRequest) -> Dict[str, Any]:
        """Build MongoDB-style filter criteria as outlined in philosophy"""
        filter_criteria = {}
        
        # Equipment type filtering
        if search_request.equipment_type:
            filter_criteria["equipment_types"] = {"$in": [search_request.equipment_type]}
        
        # Procedure type filtering  
        if search_request.procedure_type:
            filter_criteria["procedure_types"] = {"$in": [search_request.procedure_type]}
        
        # Safety level filtering
        if search_request.safety_level:
            filter_criteria["safety_level"] = {"$eq": search_request.safety_level}
        
        # Visual content filtering
        if search_request.include_images:
            filter_criteria["$or"] = [
                {"contains_images": {"$eq": True}},
                {"contains_diagrams": {"$eq": True}},
                {"file_type": {"$in": ["jpg", "jpeg", "png", "pdf"]}}
            ]
        
        return filter_criteria
    
    def _enhance_qsr_query(self, query: str, search_request: QSRSearchRequest) -> str:
        """Enhance query with QSR-specific context"""
        enhanced_terms = []
        
        # Add equipment context
        if search_request.equipment_type:
            enhanced_terms.append(search_request.equipment_type)
        
        # Add procedure context
        if search_request.procedure_type:
            enhanced_terms.append(search_request.procedure_type)
        
        # Add visual context for image searches
        if search_request.include_images:
            enhanced_terms.extend(["diagram", "image", "visual", "shows"])
        
        # Combine original query with enhancements
        if enhanced_terms:
            return f"{query} {' '.join(enhanced_terms)}"
        
        return query
    
    def _convert_to_qsr_result(self, chunk) -> QSRSearchResult:
        """Convert Ragie chunk to QSR-enhanced result"""
        chunk_text = getattr(chunk, 'text', '')
        chunk_metadata = getattr(chunk, 'metadata', {})
        
        # Extract QSR-specific information from content
        equipment_mentioned = []
        for equipment in QSR_EQUIPMENT_TYPES:
            if equipment.lower() in chunk_text.lower():
                equipment_mentioned.append(equipment)
        
        # Detect procedure type from content
        procedure_type = None
        for proc_type in QSR_PROCEDURE_TYPES:
            if proc_type in chunk_text.lower():
                procedure_type = proc_type
                break
        
        # Detect safety level from content
        safety_level = None
        if any(word in chunk_text.lower() for word in ['critical', 'danger', 'warning']):
            safety_level = 'critical'
        elif any(word in chunk_text.lower() for word in ['caution', 'safety']):
            safety_level = 'high'
        
        # Detect content characteristics
        contains_steps = any(pattern in chunk_text.lower() for pattern in ['step', '1.', 'first', 'then', 'next'])
        contains_images = any(pattern in chunk_text.lower() for pattern in ['image', 'figure', 'diagram', 'see'])
        
        return QSRSearchResult(
            document_id=getattr(chunk, 'document_id', 'unknown'),
            chunk_id=getattr(chunk, 'id', 'unknown'), 
            content=chunk_text,
            score=getattr(chunk, 'score', 0.0),
            equipment_mentioned=equipment_mentioned,
            procedure_type=procedure_type,
            safety_level=safety_level,
            contains_steps=contains_steps,
            contains_images=contains_images,
            source_filename=chunk_metadata.get('original_filename'),
            page_number=chunk_metadata.get('page_number')
        )
    
    def _parse_results_to_qsr_response(
        self, 
        results: List[QSRSearchResult], 
        search_request: QSRSearchRequest
    ) -> QSRTaskResponse:
        """Parse search results into comprehensive QSRTaskResponse"""
        
        # Aggregate information from all results
        all_equipment = set()
        all_safety_warnings = []
        all_steps = []
        source_docs = []
        media_refs = []
        
        # Calculate confidence based on result scores
        if results:
            avg_score = sum(r.score for r in results) / len(results)
            confidence = min(1.0, avg_score * 2)  # Scale to 0-1 range
        else:
            confidence = 0.0
        
        for result in results:
            # Collect equipment references
            for equipment in result.equipment_mentioned:
                all_equipment.add(equipment)
            
            # Extract safety warnings
            if result.safety_level in ['critical', 'high']:
                safety_warnings = self._extract_safety_warnings(result.content, result.safety_level)
                all_safety_warnings.extend(safety_warnings)
            
            # Extract procedural steps
            if result.contains_steps:
                steps = self._extract_steps(result.content)
                all_steps.extend(steps)
            
            # Track source documents
            if result.source_filename:
                source_docs.append(result.source_filename)
            
            # Extract media references
            if result.contains_images:
                media_refs.extend(self._extract_media_references(result.content))
        
        # Build equipment references
        equipment_refs = [
            EquipmentReference(name=eq, type=self._classify_equipment_type(eq))
            for eq in all_equipment
        ]
        
        # Determine task title and procedure type
        task_title = self._generate_task_title(search_request.query, equipment_refs)
        procedure_type = search_request.procedure_type or self._infer_procedure_type(search_request.query)
        
        # Estimate time based on steps and complexity
        estimated_time = self._estimate_task_time(len(all_steps), all_equipment)
        
        return QSRTaskResponse(
            task_title=task_title,
            steps=all_steps[:20],  # Limit to reasonable number
            safety_warnings=all_safety_warnings[:10],  # Limit safety warnings
            equipment_needed=equipment_refs,
            estimated_time=estimated_time,
            media_references=media_refs,
            source_documents=list(set(source_docs)),
            confidence_level=confidence,
            procedure_type=procedure_type,
            tools_needed=self._extract_tools_from_content([r.content for r in results])
        )
    
    def _extract_safety_warnings(self, content: str, level: str) -> List[SafetyWarning]:
        """Extract safety warnings from content"""
        warnings = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['warning', 'caution', 'danger', 'safety']):
                warnings.append(SafetyWarning(
                    level=level,
                    message=line.strip(),
                    required_ppe=self._extract_ppe_from_text(line)
                ))
        
        return warnings[:5]  # Limit to 5 warnings
    
    def _extract_steps(self, content: str) -> List[ProcedureStep]:
        """Extract procedural steps from content"""
        steps = []
        lines = content.split('\n')
        step_num = 1
        
        for line in lines:
            line_stripped = line.strip()
            # Look for numbered steps or step indicators
            if any(pattern in line_stripped.lower() for pattern in ['step', '1.', '2.', '3.', 'first', 'then', 'next']):
                if len(line_stripped) > 10:  # Avoid short fragments
                    steps.append(ProcedureStep(
                        step_number=step_num,
                        instruction=line_stripped,
                        tools_needed=self._extract_tools_from_text(line_stripped),
                        safety_notes=self._extract_safety_from_text(line_stripped)
                    ))
                    step_num += 1
        
        return steps[:15]  # Limit to reasonable number of steps
    
    def _extract_media_references(self, content: str) -> List[MediaReference]:
        """Extract media references from content"""
        media_refs = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['image', 'figure', 'diagram', 'chart']):
                media_type = 'image'
                if 'diagram' in line_lower:
                    media_type = 'diagram'
                elif 'chart' in line_lower:
                    media_type = 'chart'
                
                media_refs.append(MediaReference(
                    type=media_type,
                    url="",  # Would need to be populated from actual image extraction
                    description=line.strip()
                ))
        
        return media_refs[:5]  # Limit media references
    
    def _extract_tools_from_content(self, content_list: List[str]) -> List[str]:
        """Extract tools mentioned across all content"""
        tools = set()
        tool_keywords = ['wrench', 'screwdriver', 'cleaning', 'cloth', 'brush', 'gloves', 'sanitizer']
        
        for content in content_list:
            for keyword in tool_keywords:
                if keyword in content.lower():
                    tools.add(keyword)
        
        return list(tools)
    
    def _extract_tools_from_text(self, text: str) -> List[str]:
        """Extract tools from a single text line"""
        tools = []
        tool_keywords = ['wrench', 'screwdriver', 'cleaning', 'cloth', 'brush', 'gloves']
        
        for keyword in tool_keywords:
            if keyword in text.lower():
                tools.append(keyword)
        
        return tools
    
    def _extract_safety_from_text(self, text: str) -> List[str]:
        """Extract safety notes from text"""
        safety_notes = []
        if any(word in text.lower() for word in ['careful', 'warning', 'caution', 'safety']):
            safety_notes.append("Exercise caution during this step")
        
        return safety_notes
    
    def _extract_ppe_from_text(self, text: str) -> List[str]:
        """Extract PPE requirements from text"""
        ppe = []
        ppe_keywords = ['gloves', 'goggles', 'apron', 'mask', 'helmet']
        
        for keyword in ppe_keywords:
            if keyword in text.lower():
                ppe.append(keyword)
        
        return ppe
    
    def _classify_equipment_type(self, equipment_name: str) -> str:
        """Classify equipment into general categories"""
        name_lower = equipment_name.lower()
        
        if any(word in name_lower for word in ['fryer', 'fry']):
            return 'fryer'
        elif any(word in name_lower for word in ['oven', 'bake']):
            return 'oven'
        elif any(word in name_lower for word in ['grill', 'griddle']):
            return 'grill'
        elif any(word in name_lower for word in ['ice', 'freezer', 'refriger']):
            return 'refrigeration'
        else:
            return 'equipment'
    
    def _generate_task_title(self, query: str, equipment_refs: List[EquipmentReference]) -> str:
        """Generate a clear task title"""
        if equipment_refs:
            equipment_names = [eq.name for eq in equipment_refs[:2]]  # Limit to 2
            return f"{query.title()} - {', '.join(equipment_names)}"
        else:
            return query.title()
    
    def _infer_procedure_type(self, query: str) -> str:
        """Infer procedure type from query"""
        query_lower = query.lower()
        
        for proc_type in QSR_PROCEDURE_TYPES:
            if proc_type in query_lower:
                return proc_type
        
        # Default fallback
        return 'maintenance'
    
    def _estimate_task_time(self, num_steps: int, equipment_set: set) -> str:
        """Estimate task completion time"""
        base_time = max(5, num_steps * 2)  # 2 minutes per step, minimum 5
        complexity_multiplier = 1 + len(equipment_set) * 0.2  # More equipment = more time
        
        total_minutes = int(base_time * complexity_multiplier)
        
        if total_minutes < 15:
            return f"{total_minutes} minutes"
        elif total_minutes < 60:
            return f"{total_minutes//5*5}-{(total_minutes//5+1)*5} minutes"  # Round to 5-minute intervals
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours > 1 else ''} {minutes} minutes"


# Global service instance
qsr_ragie_service = QSRRagieService()