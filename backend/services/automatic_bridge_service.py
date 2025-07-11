#!/usr/bin/env python3
"""
Automatic LightRAG → Neo4j Bridge Service
=========================================

Seamless integration that automatically bridges LightRAG extractions to Neo4j
after document processing. Converts 3-step manual process into background automation.

Features:
- Automatic triggering after LightRAG.insert() completion
- Real-time progress tracking
- Enterprise-grade error handling and recovery
- Background processing with status updates
- Seamless user experience: Upload PDF → Graph ready

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from lightrag_neo4j_bridge import LightRAGNeo4jBridge
from extract_lightrag_data import LightRAGDataExtractor

# Import comprehensive logging
from comprehensive_logging import (
    lightrag_logger,
    multimodal_logger,
    bridge_logger,
    neo4j_logger,
    error_tracker
)

logger = logging.getLogger(__name__)

class ProcessingStage(str, Enum):
    """Processing stages for progress tracking"""
    INITIALIZING = "initializing"
    LIGHTRAG_PROCESSING = "lightrag_processing"
    DATA_EXTRACTION = "data_extraction"
    DATA_NORMALIZATION = "data_normalization"
    NEO4J_BRIDGING = "neo4j_bridging"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessingProgress:
    """Real-time processing progress tracking"""
    process_id: str = ""
    stage: ProcessingStage = ProcessingStage.INITIALIZING
    progress_percent: float = 0.0
    current_operation: str = ""
    entities_extracted: int = 0
    relationships_extracted: int = 0
    entities_bridged: int = 0
    relationships_bridged: int = 0
    start_time: float = field(default_factory=time.time)
    stage_start_time: float = field(default_factory=time.time)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detailed_log: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_stage(self, new_stage: ProcessingStage, operation: str = ""):
        """Update processing stage with timing"""
        stage_duration = time.time() - self.stage_start_time
        self.detailed_log.append({
            "stage": self.stage.value,
            "duration_seconds": round(stage_duration, 2),
            "timestamp": datetime.now().isoformat()
        })
        
        self.stage = new_stage
        self.current_operation = operation
        self.stage_start_time = time.time()
        
        # Update progress percentage based on stage
        stage_progress = {
            ProcessingStage.INITIALIZING: 0,
            ProcessingStage.LIGHTRAG_PROCESSING: 20,
            ProcessingStage.DATA_EXTRACTION: 40,
            ProcessingStage.DATA_NORMALIZATION: 60,
            ProcessingStage.NEO4J_BRIDGING: 80,
            ProcessingStage.VERIFICATION: 95,
            ProcessingStage.COMPLETED: 100,
            ProcessingStage.FAILED: 0
        }
        self.progress_percent = stage_progress.get(new_stage, 0)
    
    def add_error(self, error: str):
        """Add error to tracking"""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
        logger.error(f"Processing error: {error}")
    
    def add_warning(self, warning: str):
        """Add warning to tracking"""
        self.warnings.append(f"{datetime.now().isoformat()}: {warning}")
        logger.warning(f"Processing warning: {warning}")
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since start"""
        return time.time() - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        total_duration = time.time() - self.start_time
        return {
            "stage": self.stage.value,
            "progress_percent": self.progress_percent,
            "current_operation": self.current_operation,
            "total_duration_seconds": round(total_duration, 2),
            "entities_extracted": self.entities_extracted,
            "relationships_extracted": self.relationships_extracted,
            "entities_bridged": self.entities_bridged,
            "relationships_bridged": self.relationships_bridged,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "completed": self.stage == ProcessingStage.COMPLETED,
            "failed": self.stage == ProcessingStage.FAILED
        }

class AutomaticBridgeService:
    """
    Service that automatically bridges LightRAG extractions to Neo4j after document processing.
    Converts manual workflow into seamless background automation.
    """
    
    def __init__(self):
        self.active_processes: Dict[str, ProcessingProgress] = {}
        self.bridge_instance = None
        self.extractor_instance = None
        
    def initialize_components(self) -> bool:
        """Initialize bridge and extractor components"""
        try:
            # Initialize bridge with production settings
            self.bridge_instance = LightRAGNeo4jBridge(
                batch_size=1000,  # Large batches for efficiency
                max_retries=5,     # Extra retries for reliability
                checkpoint_file="auto_bridge_checkpoint.json"
            )
            
            # Initialize data extractor
            self.extractor_instance = LightRAGDataExtractor()
            
            logger.info("✅ Automatic bridge service components initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize bridge components: {e}")
            return False
    
    async def process_document_automatically(
        self,
        file_path: str,
        filename: str,
        rag_service,
        process_id: str = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Automatically process document through complete LightRAG → Neo4j pipeline.
        
        Args:
            file_path: Path to uploaded PDF
            filename: Original filename
            rag_service: LightRAG service instance
            process_id: Unique process identifier
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete processing result with status and metrics
        """
        
        if not process_id:
            process_id = f"auto_bridge_{int(time.time())}"
        
        # Initialize progress tracking
        progress = ProcessingProgress(process_id=process_id)
        self.active_processes[process_id] = progress
        
        try:
            logger.info(f"🚀 Starting automatic processing for {filename}")
            
            # Stage 1: Initialize components
            progress.update_stage(ProcessingStage.INITIALIZING, "Initializing bridge components")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            if not self.initialize_components():
                progress.add_error("Failed to initialize bridge components")
                progress.update_stage(ProcessingStage.FAILED)
                return progress.get_summary()
            
            # Stage 2: Process document context (NEW)
            progress.update_stage(ProcessingStage.LIGHTRAG_PROCESSING, f"Extracting document context for {filename}")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            # Broadcast progress via robust WebSocket system
            await self._broadcast_progress_safely(process_id, progress)
            
            document_context_result = await self._process_document_context(file_path, filename, progress)
            if not document_context_result.get("success"):
                progress.add_warning(f"Document context processing failed: {document_context_result.get('error')}")
                # Continue processing - document context is enhancement, not critical
            
            # Stage 3: Process through LightRAG
            progress.update_stage(ProcessingStage.LIGHTRAG_PROCESSING, f"Processing {filename} through LightRAG")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            # Broadcast progress via robust WebSocket system
            await self._broadcast_progress_safely(process_id, progress)
            
            lightrag_result = await self._process_through_lightrag(file_path, rag_service, progress)
            if not lightrag_result.get("success"):
                progress.add_error(f"LightRAG processing failed: {lightrag_result.get('error')}")
                progress.update_stage(ProcessingStage.FAILED)
                await self._broadcast_progress_safely(process_id, progress)
                return progress.get_summary()
            
            # Stage 4: Extract data from LightRAG storage
            progress.update_stage(ProcessingStage.DATA_EXTRACTION, "Extracting entities and relationships")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            extraction_result = await self._extract_lightrag_data(progress)
            if not extraction_result.get("success"):
                progress.add_error(f"Data extraction failed: {extraction_result.get('error')}")
                progress.update_stage(ProcessingStage.FAILED)
                return progress.get_summary()
            
            progress.entities_extracted = extraction_result.get("entities_count", 0)
            progress.relationships_extracted = extraction_result.get("relationships_count", 0)
            
            # Stage 5: Enhance entities with hierarchical context (NEW)
            progress.update_stage(ProcessingStage.DATA_NORMALIZATION, "Enhancing entities with document context")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            enhanced_entities = await self._enhance_entities_with_context(
                extraction_result.get("entities", []),
                document_context_result.get("document_summary"),
                progress
            )
            
            # Stage 6: Normalize and prepare data
            progress.update_stage(ProcessingStage.DATA_NORMALIZATION, "Normalizing data for Neo4j")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            normalized_data = await self._normalize_extracted_data(
                enhanced_entities,
                extraction_result.get("relationships", []),
                filename,
                progress
            )
            
            # Stage 5: Bridge to Neo4j
            progress.update_stage(ProcessingStage.NEO4J_BRIDGING, "Bridging data to Neo4j with enterprise reliability")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            bridge_result = await self._bridge_to_neo4j(normalized_data, progress)
            if not bridge_result.get("success"):
                progress.add_error(f"Neo4j bridging failed: {bridge_result.get('error')}")
                progress.update_stage(ProcessingStage.FAILED)
                return progress.get_summary()
            
            progress.entities_bridged = bridge_result.get("entities_processed", 0)
            progress.relationships_bridged = bridge_result.get("relationships_processed", 0)
            
            # Stage 6: Verify results
            progress.update_stage(ProcessingStage.VERIFICATION, "Verifying Neo4j population")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            verification_result = await self._verify_neo4j_population(progress)
            
            # Stage 7: Complete
            progress.update_stage(ProcessingStage.COMPLETED, "Processing completed successfully")
            if progress_callback:
                await progress_callback(progress.get_summary())
            
            logger.info(f"✅ Automatic processing completed for {filename}")
            logger.info(f"📊 Final results: {progress.entities_bridged} entities, {progress.relationships_bridged} relationships")
            
            return {
                **progress.get_summary(),
                "success": True,
                "filename": filename,
                "lightrag_result": lightrag_result,
                "extraction_result": extraction_result,
                "bridge_result": bridge_result,
                "verification_result": verification_result,
                "process_id": process_id
            }
            
        except Exception as e:
            logger.error(f"❌ Automatic processing failed for {filename}: {e}")
            progress.add_error(f"Unexpected error: {str(e)}")
            progress.update_stage(ProcessingStage.FAILED)
            
            return {
                **progress.get_summary(),
                "success": False,
                "error": str(e),
                "process_id": process_id
            }
        
        finally:
            # Keep process in memory for status queries, but mark as completed
            if process_id in self.active_processes:
                self.active_processes[process_id] = progress
    
    async def _process_through_lightrag(self, file_path: str, rag_service, progress: ProcessingProgress) -> Dict[str, Any]:
        """Process document through Multi-Modal Enterprise Bridge with progress updates"""
        try:
            # Import multi-modal processor
            from services.multimodal_bridge_processor import multimodal_bridge_processor
            
            progress.current_operation = "Starting multi-modal processing with Enterprise Bridge"
            
            # Process document through multi-modal pipeline
            logger.info("🎨 Using Multi-Modal Enterprise Bridge with RAG-Anything integration")
            
            # Get filename from file path
            filename = Path(file_path).name
            
            # Process with multi-modal capabilities
            multimodal_result = await multimodal_bridge_processor.process_document_with_multimodal(
                file_path, 
                filename,
                progress_callback=self._create_multimodal_progress_callback(progress)
            )
            
            # Store comprehensive data for extraction stage
            temp_data = {
                "entities": multimodal_result.entities,
                "relationships": multimodal_result.relationships,
                "visual_citations": multimodal_result.visual_citations,
                "processed_content": {
                    "text_chunks": multimodal_result.processed_content.text_chunks,
                    "images": multimodal_result.processed_content.images,
                    "tables": multimodal_result.processed_content.tables,
                    "metadata": multimodal_result.processed_content.metadata
                },
                "statistics": multimodal_result.statistics,
                "processing_method": multimodal_result.processing_method,
                "source_file": file_path,
                "processed_at": datetime.now().isoformat()
            }
            
            # Save temporary data for next stage
            temp_file = f"temp_extraction_{progress.process_id}.json"
            with open(temp_file, 'w') as f:
                json.dump(temp_data, f, indent=2, default=str)
            
            stats = multimodal_result.statistics
            progress.current_operation = (
                f"Multi-modal extraction completed: {stats['entities_extracted']} entities, "
                f"{stats['visual_citations']} visual citations, {stats['images_found']} images"
            )
            
            return {
                "success": True,
                "entities_count": len(multimodal_result.entities),
                "relationships_count": len(multimodal_result.relationships),
                "visual_citations_count": len(multimodal_result.visual_citations),
                "temp_file": temp_file,
                "processing_method": multimodal_result.processing_method,
                "statistics": stats,
                "message": "Multi-Modal Enterprise Bridge processing completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Multi-Modal Enterprise Bridge processing failed: {e}")
            
            # Fallback to basic processing
            logger.info("🔄 Falling back to basic Enterprise Bridge processing")
            try:
                # Read file content
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Extract text from PDF
                from main import extract_pdf_text
                text_content, pages = extract_pdf_text(content)
                
                if not text_content.strip():
                    return {"success": False, "error": "No text extracted from PDF"}
                
                progress.current_operation = f"Processing {len(text_content)} characters through basic Enterprise Bridge"
                
                # Basic entity extraction
                from services.qsr_entity_extractor import extract_qsr_entities_from_text
                entities, relationships = extract_qsr_entities_from_text(text_content)
                
                # Store basic data
                temp_data = {
                    "entities": entities,
                    "relationships": relationships,
                    "visual_citations": [],
                    "source_file": file_path,
                    "processing_method": "basic_enterprise_bridge",
                    "processed_at": datetime.now().isoformat()
                }
                
                # Save temporary data for next stage
                temp_file = f"temp_extraction_{progress.process_id}.json"
                with open(temp_file, 'w') as f:
                    json.dump(temp_data, f, indent=2)
                
                progress.current_operation = f"Basic extraction: {len(entities)} entities and {len(relationships)} relationships"
                
                return {
                    "success": True,
                    "entities_count": len(entities),
                    "relationships_count": len(relationships),
                    "visual_citations_count": 0,
                    "temp_file": temp_file,
                    "processing_method": "basic_fallback",
                    "message": "Basic Enterprise Bridge processing completed successfully"
                }
                
            except Exception as fallback_error:
                logger.error(f"Even basic processing failed: {fallback_error}")
                return {"success": False, "error": str(fallback_error)}
    
    def _create_multimodal_progress_callback(self, main_progress: ProcessingProgress):
        """Create progress callback for multi-modal processor"""
        async def callback(multimodal_progress: Dict[str, Any]):
            # Update main progress with multi-modal details
            stage = multimodal_progress.get('stage', 'processing')
            operation = multimodal_progress.get('operation', 'Multi-modal processing')
            main_progress.current_operation = f"{stage}: {operation}"
        
        return callback
    
    async def _extract_lightrag_data(self, progress: ProcessingProgress) -> Dict[str, Any]:
        """Extract data from Multi-Modal Enterprise Bridge temporary files"""
        try:
            progress.current_operation = "Loading data from Multi-Modal Enterprise Bridge extraction"
            
            # Load from temporary file created by Multi-Modal Enterprise Bridge
            temp_file = f"temp_extraction_{progress.process_id}.json"
            
            if not os.path.exists(temp_file):
                return {"success": False, "error": "Multi-Modal Enterprise Bridge temporary file not found"}
            
            with open(temp_file, 'r') as f:
                extracted_data = json.load(f)
            
            entities = extracted_data.get("entities", [])
            relationships = extracted_data.get("relationships", [])
            visual_citations = extracted_data.get("visual_citations", [])
            statistics = extracted_data.get("statistics", {})
            processing_method = extracted_data.get("processing_method", "unknown")
            
            progress.current_operation = (
                f"Loaded {len(entities)} entities, {len(relationships)} relationships, "
                f"{len(visual_citations)} visual citations ({processing_method})"
            )
            
            return {
                "success": True,
                "entities_count": len(entities),
                "relationships_count": len(relationships),
                "visual_citations_count": len(visual_citations),
                "entities": entities,
                "relationships": relationships,
                "visual_citations": visual_citations,
                "statistics": statistics,
                "processing_method": processing_method,
                "source": "multimodal_enterprise_bridge"
            }
                
        except Exception as e:
            logger.error(f"Multi-Modal Enterprise Bridge data extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _normalize_extracted_data(
        self, 
        entities: List[Dict], 
        relationships: List[Dict], 
        filename: str,
        progress: ProcessingProgress
    ) -> Dict[str, Any]:
        """Normalize extracted data for Neo4j bridging with multi-modal support"""
        try:
            progress.current_operation = "Normalizing entities and relationships with multi-modal enhancements"
            
            # Add source information and timestamps
            normalized_entities = []
            multimodal_enhanced_count = 0
            
            for entity in entities:
                normalized_entity = {
                    **entity,
                    "document_source": filename,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "processing_method": "multimodal_automatic_bridge"
                }
                
                # Count multi-modal enhancements
                if entity.get('multimodal_enhanced'):
                    multimodal_enhanced_count += 1
                
                normalized_entities.append(normalized_entity)
            
            normalized_relationships = []
            visual_relationships_count = 0
            
            for relationship in relationships:
                normalized_relationship = {
                    **relationship,
                    "document_source": filename,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "processing_method": "multimodal_automatic_bridge"
                }
                
                # Count relationships with visual context
                if relationship.get('has_visual_context'):
                    visual_relationships_count += 1
                
                normalized_relationships.append(normalized_relationship)
            
            progress.current_operation = (
                f"Normalized {len(normalized_entities)} entities ({multimodal_enhanced_count} multi-modal), "
                f"{len(normalized_relationships)} relationships ({visual_relationships_count} with visuals)"
            )
            
            return {
                "entities": normalized_entities,
                "relationships": normalized_relationships,
                "source_document": filename,
                "multimodal_stats": {
                    "enhanced_entities": multimodal_enhanced_count,
                    "visual_relationships": visual_relationships_count
                }
            }
            
        except Exception as e:
            logger.error(f"Data normalization failed: {e}")
            return {"entities": entities, "relationships": relationships}  # Return original on error
    
    async def _bridge_to_neo4j(self, normalized_data: Dict[str, Any], progress: ProcessingProgress) -> Dict[str, Any]:
        """Bridge normalized data to Neo4j with enterprise reliability"""
        try:
            # Save normalized data to temporary files for the bridge
            entities_file = "temp_bridge_entities.json"
            relationships_file = "temp_bridge_relationships.json"
            
            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(normalized_data["entities"], f, indent=2, ensure_ascii=False)
            
            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(normalized_data["relationships"], f, indent=2, ensure_ascii=False)
            
            progress.current_operation = "Executing enterprise-grade Neo4j bridge"
            
            # Configure bridge for this specific run
            self.bridge_instance.entities_file = Path(entities_file)
            self.bridge_instance.relationships_file = Path(relationships_file)
            self.bridge_instance.checkpoint_file = Path(f"checkpoint_{int(time.time())}.json")
            
            # Run the enterprise bridge
            bridge_result = self.bridge_instance.run_bridge()
            
            # Cleanup temporary files
            try:
                Path(entities_file).unlink(missing_ok=True)
                Path(relationships_file).unlink(missing_ok=True)
            except:
                pass  # Non-critical cleanup
            
            return bridge_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _verify_neo4j_population(self, progress: ProcessingProgress) -> Dict[str, Any]:
        """Verify that data was successfully populated in Neo4j"""
        try:
            progress.current_operation = "Verifying Neo4j graph population"
            
            # Use the bridge's Neo4j connection to verify
            if self.bridge_instance and self.bridge_instance.connect_to_neo4j():
                from services.neo4j_service import neo4j_service
                
                # Get updated counts
                if neo4j_service.connect():
                    counts = await neo4j_service.count_nodes_and_relationships()
                    sample_entities = await neo4j_service.get_sample_entities(5)
                    
                    return {
                        "success": True,
                        "total_nodes": counts["nodes"],
                        "total_relationships": counts["relationships"],
                        "sample_entities": sample_entities,
                        "verification_timestamp": datetime.now().isoformat()
                    }
                else:
                    return {"success": False, "error": "Could not connect to Neo4j for verification"}
            else:
                return {"success": False, "error": "Bridge Neo4j connection not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_process_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a processing operation"""
        if process_id in self.active_processes:
            return self.active_processes[process_id].get_summary()
        return None
    
    def list_active_processes(self) -> Dict[str, Dict[str, Any]]:
        """List all active processing operations"""
        return {
            process_id: progress.get_summary() 
            for process_id, progress in self.active_processes.items()
        }
    
    def cleanup_completed_processes(self, max_age_hours: int = 24):
        """Clean up old completed processes"""
        current_time = time.time()
        to_remove = []
        
        for process_id, progress in self.active_processes.items():
            age_hours = (current_time - progress.start_time) / 3600
            if age_hours > max_age_hours and progress.stage in [ProcessingStage.COMPLETED, ProcessingStage.FAILED]:
                to_remove.append(process_id)
        
        for process_id in to_remove:
            del self.active_processes[process_id]
        
        logger.info(f"🧹 Cleaned up {len(to_remove)} old processing records")
    
    async def _process_document_context(self, file_path: str, filename: str, 
                                       progress: ProcessingProgress) -> Dict[str, Any]:
        """
        Process document for hierarchical context and summarization
        """
        try:
            from services.document_context_service import document_context_service
            from services.neo4j_service import neo4j_service
            
            progress.current_operation = "Extracting document-level context and purpose"
            
            # Initialize document context service with Neo4j
            document_context_service.neo4j_service = neo4j_service
            
            # Process document for context
            file_path_obj = Path(file_path)
            document_summary = await document_context_service.process_document_for_context(file_path_obj)
            
            if document_summary:
                logger.info(f"✅ Document context processed: {document_summary.document_type.value}/{document_summary.qsr_category.value}")
                return {
                    "success": True,
                    "document_summary": document_summary,
                    "document_id": document_summary.document_id,
                    "context_summary": {
                        "document_type": document_summary.document_type.value,
                        "qsr_category": document_summary.qsr_category.value,
                        "target_audience": document_summary.target_audience,
                        "brand_context": document_summary.brand_context,
                        "equipment_focus": document_summary.equipment_focus,
                        "confidence_score": document_summary.confidence_score
                    }
                }
            else:
                return {"success": False, "error": "Document context extraction returned no summary"}
                
        except Exception as e:
            logger.error(f"❌ Document context processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _enhance_entities_with_context(self, entities: List[Dict[str, Any]], 
                                           document_summary, progress: ProcessingProgress) -> List[Dict[str, Any]]:
        """
        Enhance extracted entities with hierarchical document context
        """
        try:
            if not document_summary:
                logger.warning("No document summary available for entity enhancement")
                return entities
            
            from services.document_context_service import document_context_service
            
            progress.current_operation = "Enhancing entities with hierarchical context"
            enhanced_entities = []
            
            for i, entity in enumerate(entities):
                try:
                    # Add document context to entity
                    entity["document_id"] = document_summary.document_id
                    entity["document_context"] = {
                        "filename": document_summary.filename,
                        "document_type": document_summary.document_type.value,
                        "qsr_category": document_summary.qsr_category.value,
                        "brand_context": document_summary.brand_context,
                        "target_audience": document_summary.target_audience
                    }
                    
                    # Enhance with hierarchical context
                    hierarchical_entity = await document_context_service.enhance_entity_with_hierarchy(
                        entity, document_summary.document_id
                    )
                    
                    if hierarchical_entity:
                        # Convert hierarchical entity to enhanced dict
                        enhanced_entity = entity.copy()
                        enhanced_entity["hierarchical_context"] = {
                            "section_path": hierarchical_entity.section_path,
                            "contextual_description": hierarchical_entity.contextual_description,
                            "related_procedures": hierarchical_entity.related_procedures,
                            "safety_considerations": hierarchical_entity.safety_considerations,
                            "qsr_specific_notes": hierarchical_entity.qsr_specific_notes
                        }
                        enhanced_entities.append(enhanced_entity)
                    else:
                        # Fallback to basic document context
                        enhanced_entities.append(entity)
                    
                    # Update progress
                    if i % 10 == 0:  # Update every 10 entities
                        progress.current_operation = f"Enhanced {i+1}/{len(entities)} entities with context"
                        
                except Exception as entity_error:
                    logger.warning(f"Failed to enhance entity {entity.get('name', 'unknown')}: {entity_error}")
                    enhanced_entities.append(entity)  # Add original entity
            
            logger.info(f"✅ Enhanced {len(enhanced_entities)} entities with document context")
            return enhanced_entities
            
        except Exception as e:
            logger.error(f"❌ Entity context enhancement failed: {e}")
            return entities  # Return original entities on failure
    
    async def _broadcast_progress_safely(self, process_id: str, progress: ProcessingProgress):
        """
        Safely broadcast progress updates without crashing the processing pipeline
        """
        try:
            # Import here to avoid circular imports
            from websocket_endpoints_robust import notify_upload_progress
            
            await notify_upload_progress(
                process_id=process_id,
                stage=progress.stage.value,
                progress_percent=progress.progress_percent,
                message=progress.current_operation,
                entities_found=progress.entities_extracted,
                relationships_found=progress.relationships_extracted,
                elapsed_seconds=progress.get_elapsed_time(),
                error_count=len(progress.errors)
            )
            
        except Exception as e:
            logger.warning(f"Progress broadcast failed (processing continues): {e}")
            # Never let WebSocket failures crash the upload processing

# Global service instance
automatic_bridge_service = AutomaticBridgeService()