#!/usr/bin/env python3
"""
Enhanced Upload Endpoints with Automatic LightRAG → Neo4j Integration
======================================================================

Seamless upload experience that automatically:
1. Processes PDF through LightRAG
2. Extracts entities and relationships  
3. Bridges to Neo4j with enterprise reliability
4. Provides real-time progress tracking

User Experience: Drag PDF → Everything automatic → Graph ready for queries

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.automatic_bridge_service import automatic_bridge_service, ProcessingStage

# Import comprehensive logging
from comprehensive_logging import (
    create_pipeline_logger,
    upload_logger,
    lightrag_logger,
    multimodal_logger,
    bridge_logger,
    neo4j_logger,
    error_tracker
)

logger = logging.getLogger(__name__)

# Enhanced response models
class AutomaticUploadResponse(BaseModel):
    """Enhanced upload response with automatic processing status"""
    success: bool
    message: str
    filename: str
    document_id: str
    pages_extracted: int
    
    # Automatic processing fields
    automatic_processing: bool = True
    process_id: str
    processing_stage: str
    progress_percent: float
    estimated_completion_time: Optional[str] = None
    
    # Status endpoints for tracking
    status_endpoint: str
    progress_endpoint: str
    result_endpoint: str

class ProcessingStatusResponse(BaseModel):
    """Real-time processing status response"""
    process_id: str
    stage: str
    progress_percent: float
    current_operation: str
    entities_extracted: int
    relationships_extracted: int
    entities_bridged: int
    relationships_bridged: int
    total_duration_seconds: float
    errors_count: int
    warnings_count: int
    completed: bool
    failed: bool
    
    # Next steps information
    next_action: Optional[str] = None
    graph_ready: bool = False

class ProcessingResultResponse(BaseModel):
    """Final processing result with complete metrics"""
    success: bool
    process_id: str
    filename: str
    processing_summary: Dict[str, Any]
    lightrag_metrics: Dict[str, Any]
    extraction_metrics: Dict[str, Any]
    bridge_metrics: Dict[str, Any]
    neo4j_verification: Dict[str, Any]
    
    # User-facing results
    graph_ready: bool
    total_entities: int
    total_relationships: int
    processing_time_seconds: float
    
    # Error information if failed
    error_details: Optional[Dict[str, Any]] = None

# Create router for enhanced upload endpoints
enhanced_upload_router = APIRouter(prefix="/api/v2", tags=["Enhanced Upload"])

@enhanced_upload_router.post("/upload-automatic", response_model=AutomaticUploadResponse)
async def upload_with_automatic_processing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Enhanced upload endpoint with fully automatic LightRAG → Neo4j processing.
    
    User Experience:
    1. User drags PDF to upload
    2. PDF is saved and validated
    3. Automatic processing starts in background
    4. Real-time progress tracking available
    5. Graph ready for queries when complete
    
    Returns immediate response with tracking endpoints.
    """
    
    try:
        # === CHECKPOINT 1: FastAPI Upload Endpoint ===
        
        # 1.0 Enterprise Pre-flight Health Checks (Non-blocking for Enterprise Bridge)
        from enterprise_bridge_reliability import (
            enterprise_health_checker,
            atomic_transaction_manager,
            enterprise_retry_logic,
            get_user_friendly_error,
            ErrorCode
        )
        
        logger.info("🔍 Running enterprise pre-flight health checks...")
        health_status, health_results = await enterprise_health_checker.run_pre_flight_checks()
        
        # For Enterprise Bridge system, only block on critical infrastructure failures
        # Neo4j connection issues are handled by the bridge, so don't block uploads
        blocking_failures = [
            r for r in health_results 
            if r.status in ["critical", "failed"] 
            and r.component in ["disk_space", "memory", "storage_permissions"]  # Only block on infrastructure
        ]
        
        if blocking_failures:
            error_code = blocking_failures[0].error_code or ErrorCode.UNKNOWN_ERROR
            error_info = get_user_friendly_error(error_code)
            raise HTTPException(
                status_code=503, 
                detail={
                    "error": error_info["user_message"],
                    "technical_details": error_info["technical_details"],
                    "recovery_action": error_info["recovery_action"],
                    "health_check_results": [
                        {
                            "component": r.component,
                            "status": r.status,
                            "message": r.message,
                            "recovery_suggestion": r.recovery_suggestion
                        }
                        for r in blocking_failures
                    ]
                }
            )
        
        # Log health status but don't block for Enterprise Bridge compatibility
        if not health_status:
            logger.warning("⚠️ Some health checks failed, but proceeding with Enterprise Bridge system")
        else:
            logger.info("✅ Pre-flight health checks passed")
        
        # 1.1 File received logging
        upload_logger.log_file_received(
            filename=file.filename,
            size=len(await file.read()),
            mime_type=file.content_type or "application/pdf"
        )
        
        # Reset file position after reading for size
        await file.seek(0)
        content = await file.read()
        
        # Validate file type and size
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Validate PDF content
        from main import is_valid_pdf, extract_pdf_text, generate_document_id
        if not is_valid_pdf(content):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        
        # 1.2 Validation passed logging
        upload_logger.log_validation_passed(file.filename)
        
        # Extract basic info for immediate response
        extracted_text, pages_count = extract_pdf_text(content)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from PDF")
        
        # Generate IDs
        doc_id = generate_document_id()
        process_id = f"auto_proc_{doc_id}_{int(datetime.now().timestamp())}"
        
        # Save file with automatic processing naming
        safe_filename = f"{doc_id}_{file.filename}"
        file_path = Path("uploaded_docs") / safe_filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 1.3 File saved logging
        upload_logger.log_file_saved(
            filename=file.filename,
            storage_path=str(file_path.absolute())
        )
        
        # 1.4 Processing initiated logging
        upload_logger.log_processing_initiated(
            filename=file.filename,
            file_id=doc_id
        )
        
        # Create comprehensive pipeline logger
        pipeline_logger = create_pipeline_logger(doc_id, file.filename)
        pipeline_logger.log_stage_start("upload", {
            "filename": file.filename,
            "size": len(content),
            "pages_count": pages_count,
            "text_length": len(extracted_text),
            "file_path": str(file_path)
        })
        
        logger.info(f"📁 Saved {file.filename} for automatic processing: {file_path}")
        
        # Update documents database (same as original upload)
        from main import load_documents_db, save_documents_db
        docs_db = load_documents_db()
        
        document_info = {
            "id": doc_id,
            "filename": safe_filename,
            "original_filename": file.filename,
            "upload_timestamp": datetime.now().isoformat(),
            "file_size": len(content),
            "pages_count": pages_count,
            "text_content": extracted_text,
            "text_preview": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
            "automatic_processing": True,
            "process_id": process_id
        }
        
        docs_db[doc_id] = document_info
        if not save_documents_db(docs_db):
            raise HTTPException(status_code=500, detail="Failed to save document information")
        
        # Add to existing search engine (for immediate availability)
        try:
            from main import search_engine
            search_engine.add_document(
                doc_id=doc_id,
                text=extracted_text,
                filename=file.filename
            )
            logger.info(f"✅ Added {file.filename} to search engine")
        except Exception as search_error:
            logger.warning(f"Search engine update failed: {search_error}")
        
        # Initialize WebSocket progress tracking
        from websocket_progress import notify_upload_received
        await notify_upload_received(process_id, file.filename, len(content), pages_count)
        
        # Start atomic transaction for enterprise reliability
        transaction = atomic_transaction_manager.start_transaction(process_id)
        
        # Add file cleanup to rollback
        await atomic_transaction_manager.add_operation(
            transaction.transaction_id,
            {"type": "file_upload", "file_path": str(file_path)},
            {"type": "file_delete", "file_path": str(file_path)}
        )
        
        # Start automatic processing in background with enterprise reliability
        background_tasks.add_task(
            start_automatic_processing_enterprise,
            str(file_path),
            file.filename,
            process_id,
            transaction.transaction_id
        )
        
        # Estimate completion time based on file size
        estimated_minutes = max(2, min(15, pages_count * 0.5))  # 0.5 min per page, 2-15 min range
        estimated_completion = datetime.now().timestamp() + (estimated_minutes * 60)
        
        logger.info(f"🚀 Started automatic processing for {file.filename}, estimated completion: {estimated_minutes} minutes")
        
        return AutomaticUploadResponse(
            success=True,
            message=f"Upload successful! Automatic processing started for {file.filename}",
            filename=file.filename,
            document_id=doc_id,
            pages_extracted=pages_count,
            automatic_processing=True,
            process_id=process_id,
            processing_stage=ProcessingStage.INITIALIZING.value,
            progress_percent=0.0,
            estimated_completion_time=datetime.fromtimestamp(estimated_completion).isoformat(),
            status_endpoint=f"/api/v2/processing-status/{process_id}",
            progress_endpoint=f"/api/v2/processing-progress/{process_id}",
            result_endpoint=f"/api/v2/processing-result/{process_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@enhanced_upload_router.get("/processing-status/{process_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(process_id: str):
    """
    Get real-time processing status for automatic upload.
    
    Returns current stage, progress, and metrics for UI updates.
    """
    
    try:
        status = automatic_bridge_service.get_process_status(process_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Process not found")
        
        # Determine next action for user
        next_action = None
        graph_ready = False
        
        if status["completed"]:
            next_action = "Graph ready for queries"
            graph_ready = True
        elif status["failed"]:
            next_action = "Processing failed - check error details"
        elif status["stage"] == ProcessingStage.NEO4J_BRIDGING.value:
            next_action = "Bridging to knowledge graph..."
        elif status["stage"] == ProcessingStage.LIGHTRAG_PROCESSING.value:
            next_action = "Extracting knowledge..."
        else:
            next_action = f"Processing: {status['current_operation']}"
        
        return ProcessingStatusResponse(
            process_id=process_id,
            stage=status["stage"],
            progress_percent=status["progress_percent"],
            current_operation=status["current_operation"],
            entities_extracted=status["entities_extracted"],
            relationships_extracted=status["relationships_extracted"],
            entities_bridged=status["entities_bridged"],
            relationships_bridged=status["relationships_bridged"],
            total_duration_seconds=status["total_duration_seconds"],
            errors_count=status["errors_count"],
            warnings_count=status["warnings_count"],
            completed=status["completed"],
            failed=status["failed"],
            next_action=next_action,
            graph_ready=graph_ready
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")

@enhanced_upload_router.get("/processing-progress/{process_id}")
async def get_processing_progress(process_id: str):
    """
    Get detailed processing progress with logs and metrics.
    Suitable for detailed progress displays and debugging.
    """
    
    try:
        status = automatic_bridge_service.get_process_status(process_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Process not found")
        
        # Get the full progress object for detailed information
        progress_obj = automatic_bridge_service.active_processes.get(process_id)
        
        if progress_obj:
            return {
                "process_id": process_id,
                "basic_status": status,
                "detailed_log": progress_obj.detailed_log,
                "errors": progress_obj.errors,
                "warnings": progress_obj.warnings,
                "stage_timings": [
                    {
                        "stage": entry["stage"],
                        "duration_seconds": entry["duration_seconds"],
                        "timestamp": entry["timestamp"]
                    }
                    for entry in progress_obj.detailed_log
                ],
                "performance_metrics": {
                    "entities_per_second": status["entities_extracted"] / max(status["total_duration_seconds"], 1),
                    "relationships_per_second": status["relationships_extracted"] / max(status["total_duration_seconds"], 1),
                    "avg_stage_duration": sum(entry["duration_seconds"] for entry in progress_obj.detailed_log) / max(len(progress_obj.detailed_log), 1)
                }
            }
        else:
            return {"process_id": process_id, "basic_status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Progress check failed: {e}")
        raise HTTPException(status_code=500, detail="Progress check failed")

@enhanced_upload_router.get("/processing-result/{process_id}", response_model=ProcessingResultResponse)
async def get_processing_result(process_id: str):
    """
    Get final processing result with complete metrics and verification.
    Call this when processing is completed for full results.
    """
    
    try:
        status = automatic_bridge_service.get_process_status(process_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Process not found")
        
        # Get the full progress object for complete information
        progress_obj = automatic_bridge_service.active_processes.get(process_id)
        
        if not progress_obj:
            raise HTTPException(status_code=404, detail="Detailed process information not available")
        
        # Determine if we have a successful result
        success = status["completed"] and not status["failed"]
        graph_ready = success and status["entities_bridged"] > 0
        
        # Extract metrics from detailed log
        lightrag_metrics = {}
        extraction_metrics = {}
        bridge_metrics = {}
        neo4j_verification = {}
        error_details = None
        
        if not success and progress_obj.errors:
            error_details = {
                "error_count": len(progress_obj.errors),
                "errors": progress_obj.errors,
                "warnings": progress_obj.warnings,
                "failed_at_stage": status["stage"]
            }
        
        # Build comprehensive result
        return ProcessingResultResponse(
            success=success,
            process_id=process_id,
            filename=getattr(progress_obj, 'filename', 'unknown'),
            processing_summary=status,
            lightrag_metrics=lightrag_metrics,
            extraction_metrics=extraction_metrics,
            bridge_metrics=bridge_metrics,
            neo4j_verification=neo4j_verification,
            graph_ready=graph_ready,
            total_entities=status["entities_bridged"],
            total_relationships=status["relationships_bridged"],
            processing_time_seconds=status["total_duration_seconds"],
            error_details=error_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Result check failed: {e}")
        raise HTTPException(status_code=500, detail="Result check failed")

@enhanced_upload_router.get("/active-processes")
async def list_active_processes():
    """
    List all currently active processing operations.
    Useful for admin monitoring and debugging.
    """
    
    try:
        active_processes = automatic_bridge_service.list_active_processes()
        
        return {
            "active_process_count": len(active_processes),
            "processes": active_processes,
            "summary": {
                "initializing": sum(1 for p in active_processes.values() if p["stage"] == ProcessingStage.INITIALIZING.value),
                "processing": sum(1 for p in active_processes.values() if p["stage"] in [ProcessingStage.LIGHTRAG_PROCESSING.value, ProcessingStage.DATA_EXTRACTION.value, ProcessingStage.NEO4J_BRIDGING.value]),
                "completed": sum(1 for p in active_processes.values() if p["completed"]),
                "failed": sum(1 for p in active_processes.values() if p["failed"])
            }
        }
        
    except Exception as e:
        logger.error(f"Process listing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list processes")

@enhanced_upload_router.post("/cleanup-processes")
async def cleanup_old_processes(max_age_hours: int = 24):
    """
    Clean up old completed/failed processes.
    Helps manage memory usage in production.
    """
    
    try:
        before_count = len(automatic_bridge_service.active_processes)
        automatic_bridge_service.cleanup_completed_processes(max_age_hours)
        after_count = len(automatic_bridge_service.active_processes)
        
        cleaned_count = before_count - after_count
        
        return {
            "cleanup_completed": True,
            "processes_cleaned": cleaned_count,
            "active_processes_remaining": after_count,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Process cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

# Background task function
async def start_automatic_processing_enterprise(file_path: str, filename: str, process_id: str, transaction_id: str):
    """
    Background task that runs the complete automatic processing pipeline.
    This is where the magic happens - user uploads, this runs automatically.
    """
    
    try:
        logger.info(f"🔄 Starting enterprise background processing for {filename}")
        
        # Import enterprise reliability components
        from enterprise_bridge_reliability import (
            atomic_transaction_manager,
            enterprise_retry_logic,
            get_user_friendly_error,
            ErrorCode
        )
        
        # Import WebSocket progress tracking
        from websocket_progress import (
            notify_text_extraction_start,
            notify_entity_extraction_start,
            notify_relationship_mapping_start,
            notify_graph_population_start,
            notify_processing_complete,
            notify_processing_error,
            progress_manager
        )
        
        # Get or create progress tracker
        tracker = None
        for process_id_key, history in progress_manager.progress_history.items():
            if process_id_key == process_id and history:
                # Convert the last progress update back to a tracker
                from websocket_progress import create_progress_tracker
                last_update = history[-1]
                tracker = create_progress_tracker(process_id, filename, last_update.total_pages)
                tracker.entities_found = last_update.entities_found
                tracker.relationships_found = last_update.relationships_found
                tracker.pages_processed = last_update.pages_processed
                break
        
        if not tracker:
            from websocket_progress import create_progress_tracker
            tracker = create_progress_tracker(process_id, filename, 0)
        
        # Start text extraction stage
        await notify_text_extraction_start(tracker)
        
        # Import RAG service (avoid circular imports)
        from services.rag_service import rag_service
        
        # Define enhanced progress callback for real-time updates
        async def progress_callback(progress_summary: Dict[str, Any]):
            stage = progress_summary.get('stage', 'unknown')
            entities = progress_summary.get('entities_extracted', tracker.entities_found)
            relationships = progress_summary.get('relationships_extracted', tracker.relationships_found)
            
            # Update tracker counts
            tracker.entities_found = entities
            tracker.relationships_found = relationships
            
            # Notify specific stage progress
            if stage == 'data_extraction' or stage == 'lightrag_processing':
                await notify_entity_extraction_start(tracker)
                
                # If we have entity counts, send progress update
                if entities > 0 or relationships > 0:
                    from websocket_progress import notify_entity_progress
                    await notify_entity_progress(tracker, entities, relationships)
                    
            elif stage == 'data_normalization':
                await notify_relationship_mapping_start(tracker)
            elif stage == 'neo4j_bridging':
                await notify_graph_population_start(tracker)
            
            logger.info(f"📊 Progress update for {filename}: {stage} ({progress_summary.get('progress_percent', 0):.1f}%)")
        
        # Enterprise-grade processing with retry logic
        async def enterprise_processing():
            return await automatic_bridge_service.process_document_automatically(
                file_path=file_path,
                filename=filename,
                rag_service=rag_service,
                process_id=process_id,
                progress_callback=progress_callback
            )
        
        # Execute with enterprise retry logic
        result = await enterprise_retry_logic.execute_with_retry(
            enterprise_processing,
            f"document_processing_{filename}",
        )
        
        if result["success"]:
            logger.info(f"✅ Enterprise processing completed successfully for {filename}")
            logger.info(f"📈 Results: {result['entities_bridged']} entities, {result['relationships_bridged']} relationships")
            
            # Add successful operations to transaction
            await atomic_transaction_manager.add_operation(
                transaction_id,
                {
                    "type": "neo4j_population", 
                    "entities": result.get('entities_bridged', 0),
                    "relationships": result.get('relationships_bridged', 0)
                },
                {
                    "type": "neo4j_delete",
                    "delete_query": f"MATCH (n) WHERE n.process_id = $process_id DELETE n",
                    "params": {"process_id": process_id}
                }
            )
            
            # Commit transaction
            await atomic_transaction_manager.commit_transaction(transaction_id)
            
            # Notify successful completion
            await notify_processing_complete(
                tracker,
                result.get('entities_bridged', 0),
                result.get('relationships_bridged', 0)
            )
        else:
            logger.error(f"❌ Enterprise processing failed for {filename}: {result.get('error')}")
            
            # Rollback transaction on failure
            await atomic_transaction_manager.rollback_transaction(
                transaction_id, 
                f"Processing failed: {result.get('error', 'Unknown error')}"
            )
            
            # Determine error code for user-friendly message
            error_message = result.get('error', 'Unknown processing error')
            error_code = ErrorCode.BRIDGE_FAILED
            
            if 'pdf' in error_message.lower() or 'invalid' in error_message.lower():
                error_code = ErrorCode.INVALID_PDF
            elif 'timeout' in error_message.lower():
                error_code = ErrorCode.PROCESSING_TIMEOUT
            elif 'neo4j' in error_message.lower() or 'database' in error_message.lower():
                error_code = ErrorCode.NEO4J_CONNECTION_FAILED
            
            error_info = get_user_friendly_error(error_code)
            
            # Notify processing error with user-friendly message
            await notify_processing_error(
                tracker,
                error_info["user_message"],
                retry_available=(error_info["recovery_action"] in ["retry", "automatic_retry"])
            )
        
    except Exception as e:
        logger.error(f"💥 Enterprise background processing crashed for {filename}: {e}")
        
        # Import enterprise error handling
        from enterprise_bridge_reliability import (
            atomic_transaction_manager,
            get_user_friendly_error,
            ErrorCode
        )
        from websocket_progress import notify_processing_error, progress_manager
        
        # Rollback transaction on crash
        try:
            await atomic_transaction_manager.rollback_transaction(
                transaction_id, 
                f"Processing crashed: {str(e)}"
            )
        except Exception as rollback_error:
            logger.error(f"❌ Transaction rollback failed: {rollback_error}")
        
        # Determine appropriate error code
        error_message = str(e)
        if 'memory' in error_message.lower():
            error_code = ErrorCode.MEMORY_INSUFFICIENT
        elif 'disk' in error_message.lower() or 'space' in error_message.lower():
            error_code = ErrorCode.DISK_FULL
        elif 'timeout' in error_message.lower():
            error_code = ErrorCode.PROCESSING_TIMEOUT
        elif 'lightrag' in error_message.lower():
            error_code = ErrorCode.LIGHTRAG_CRASH
        else:
            error_code = ErrorCode.UNKNOWN_ERROR
        
        error_info = get_user_friendly_error(error_code)
        
        # Try to get tracker for error notification
        tracker = None
        for process_id_key, history in progress_manager.progress_history.items():
            if process_id_key == process_id and history:
                from websocket_progress import create_progress_tracker
                last_update = history[-1]
                tracker = create_progress_tracker(process_id, filename, last_update.total_pages)
                break
        
        if tracker:
            await notify_processing_error(
                tracker,
                error_info["user_message"],
                retry_available=(error_info["recovery_action"] in ["retry", "automatic_retry"])
            )
        
        # Update the process status to failed
        if process_id in automatic_bridge_service.active_processes:
            progress = automatic_bridge_service.active_processes[process_id]
            progress.add_error(f"Enterprise processing crashed: {error_info['user_message']}")
            progress.update_stage(ProcessingStage.FAILED)

# Keep original function for backward compatibility
async def start_automatic_processing(file_path: str, filename: str, process_id: str):
    """Original background processing (for backward compatibility)"""
    # Default transaction for backward compatibility
    from enterprise_bridge_reliability import atomic_transaction_manager
    transaction = atomic_transaction_manager.start_transaction(process_id)
    await start_automatic_processing_enterprise(file_path, filename, process_id, transaction.transaction_id)

# Status check endpoint for UI polling
@enhanced_upload_router.get("/quick-status/{process_id}")
async def quick_status_check(process_id: str):
    """
    Lightweight status check for frequent UI polling.
    Returns minimal data for responsive UI updates.
    """
    
    try:
        status = automatic_bridge_service.get_process_status(process_id)
        
        if not status:
            return {"found": False}
        
        return {
            "found": True,
            "stage": status["stage"],
            "progress": status["progress_percent"],
            "completed": status["completed"],
            "failed": status["failed"],
            "entities": status["entities_bridged"],
            "relationships": status["relationships_bridged"]
        }
        
    except Exception as e:
        return {"found": False, "error": str(e)}

@enhanced_upload_router.get("/system-health")
async def get_system_health():
    """
    Enterprise health check endpoint for system status monitoring.
    Returns comprehensive health information for UI display.
    """
    
    try:
        from enterprise_bridge_reliability import (
            enterprise_health_checker,
            atomic_transaction_manager,
            get_user_friendly_error,
            ErrorCode
        )
        
        # Run health checks
        health_status, health_results = await enterprise_health_checker.run_pre_flight_checks()
        
        # Get transaction statistics
        active_tx_count = len(atomic_transaction_manager.active_transactions)
        tx_history_count = len(atomic_transaction_manager.transaction_history)
        
        # Calculate health summary
        healthy_components = len([r for r in health_results if r.status == "healthy"])
        warning_components = len([r for r in health_results if r.status == "warning"])
        critical_components = len([r for r in health_results if r.status in ["critical", "failed"]])
        
        return {
            "overall_status": "healthy" if health_status else "degraded",
            "timestamp": datetime.now().isoformat(),
            "health_summary": {
                "healthy_components": healthy_components,
                "warning_components": warning_components,
                "critical_components": critical_components,
                "total_components": len(health_results)
            },
            "component_details": [
                {
                    "component": result.component,
                    "status": result.status,
                    "message": result.message,
                    "error_code": result.error_code.value if result.error_code else None,
                    "recovery_suggestion": result.recovery_suggestion,
                    "details": result.details
                }
                for result in health_results
            ],
            "transaction_status": {
                "active_transactions": active_tx_count,
                "transaction_history": tx_history_count,
                "system_ready": health_status and active_tx_count < 10  # Arbitrary threshold
            },
            "recommendations": [
                result.recovery_suggestion for result in health_results 
                if result.recovery_suggestion and result.status in ["critical", "failed", "warning"]
            ]
        }
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return {
            "overall_status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "health_summary": {
                "healthy_components": 0,
                "warning_components": 0,
                "critical_components": 1,
                "total_components": 1
            },
            "component_details": [
                {
                    "component": "health_checker",
                    "status": "failed",
                    "message": f"Health check system failed: {str(e)}",
                    "error_code": ErrorCode.UNKNOWN_ERROR.value
                }
            ]
        }