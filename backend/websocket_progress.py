#!/usr/bin/env python3
"""
WebSocket Progress Tracking for QSR Document Processing
======================================================

Real-time progress updates for PDF upload → LightRAG → Neo4j pipeline.
Provides granular progress tracking through all 6 processing stages.

Features:
- WebSocket broadcasting for real-time UI updates
- Detailed progress stages with percentages
- ETA calculations based on file size
- Error notifications with recovery suggestions
- Success confirmation with entity/relationship counts

User Experience:
PDF Upload → Text Extraction → Entity Processing → Graph Population → Complete ✅

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from services.automatic_bridge_service import ProcessingStage

logger = logging.getLogger(__name__)

class ProgressStage(str, Enum):
    """Detailed progress stages for UI display"""
    UPLOAD_RECEIVED = "upload_received"           # 5%  - "Uploading manual..."
    TEXT_EXTRACTION = "text_extraction"          # 25% - "Extracting text and images..."
    ENTITY_EXTRACTION = "entity_extraction"      # 50% - "Identifying equipment and procedures..."
    RELATIONSHIP_MAPPING = "relationship_mapping" # 75% - "Building knowledge connections..."
    GRAPH_POPULATION = "graph_population"        # 90% - "Saving to knowledge base..."
    VERIFICATION = "verification"                # 100% - "Ready! Found 47 procedures, 23 equipment items"
    ERROR = "error"                              # 0% - "Processing failed: {error_message}"

@dataclass
class ProgressUpdate:
    """Progress update data structure for WebSocket broadcasting"""
    process_id: str
    stage: ProgressStage
    progress_percent: float
    message: str
    
    # Stage-specific data
    entities_found: int = 0
    relationships_found: int = 0
    pages_processed: int = 0
    total_pages: int = 0
    
    # Timing information
    elapsed_seconds: float = 0.0
    eta_seconds: Optional[float] = None
    eta_message: Optional[str] = None
    
    # Error information
    error_message: Optional[str] = None
    error_stage: Optional[str] = None
    retry_available: bool = False
    
    # Success information
    success_summary: Optional[Dict[str, Any]] = None
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class WebSocketProgressManager:
    """Manages WebSocket connections and progress broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # process_id -> set of websockets
        self.global_connections: Set[WebSocket] = set()          # connections listening to all processes
        self.progress_history: Dict[str, List[ProgressUpdate]] = {}  # process_id -> progress history
        
    async def connect(self, websocket: WebSocket, process_id: Optional[str] = None):
        """Connect a WebSocket client to progress updates"""
        await websocket.accept()
        
        if process_id:
            # Connect to specific process
            if process_id not in self.active_connections:
                self.active_connections[process_id] = set()
            self.active_connections[process_id].add(websocket)
            logger.info(f"🔌 WebSocket connected to process {process_id}")
            
            # Send historical progress if available
            if process_id in self.progress_history:
                for progress in self.progress_history[process_id]:
                    try:
                        await websocket.send_json(progress.__dict__)
                    except:
                        pass  # Connection might have closed
        else:
            # Connect to all processes
            self.global_connections.add(websocket)
            logger.info(f"🌐 WebSocket connected globally")
    
    async def disconnect(self, websocket: WebSocket, process_id: Optional[str] = None):
        """Disconnect a WebSocket client"""
        try:
            if process_id and process_id in self.active_connections:
                self.active_connections[process_id].discard(websocket)
                if not self.active_connections[process_id]:
                    del self.active_connections[process_id]
                logger.info(f"🔌 WebSocket disconnected from process {process_id}")
            else:
                self.global_connections.discard(websocket)
                logger.info(f"🌐 WebSocket disconnected globally")
        except Exception as e:
            logger.warning(f"WebSocket disconnect error: {e}")
    
    async def broadcast_progress(self, progress: ProgressUpdate):
        """Broadcast progress update to all relevant connections"""
        progress_data = progress.__dict__
        
        # Store in history
        if progress.process_id not in self.progress_history:
            self.progress_history[progress.process_id] = []
        self.progress_history[progress.process_id].append(progress)
        
        # Keep only last 100 updates per process
        if len(self.progress_history[progress.process_id]) > 100:
            self.progress_history[progress.process_id] = self.progress_history[progress.process_id][-100:]
        
        # Broadcast to process-specific connections
        process_connections = self.active_connections.get(progress.process_id, set()).copy()
        for websocket in process_connections:
            try:
                await websocket.send_json(progress_data)
            except WebSocketDisconnect:
                self.active_connections[progress.process_id].discard(websocket)
            except Exception as e:
                logger.warning(f"Failed to send progress to WebSocket: {e}")
                self.active_connections[progress.process_id].discard(websocket)
        
        # Broadcast to global connections
        global_connections = self.global_connections.copy()
        for websocket in global_connections:
            try:
                await websocket.send_json(progress_data)
            except WebSocketDisconnect:
                self.global_connections.discard(websocket)
            except Exception as e:
                logger.warning(f"Failed to send progress to global WebSocket: {e}")
                self.global_connections.discard(websocket)
        
        logger.info(f"📡 Broadcasted progress: {progress.stage} ({progress.progress_percent:.1f}%) for {progress.process_id}")
    
    def cleanup_old_history(self, max_age_hours: int = 24):
        """Clean up old progress history to manage memory"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cutoff_iso = cutoff_time.isoformat()
        
        processes_to_remove = []
        for process_id, history in self.progress_history.items():
            # Remove old entries
            self.progress_history[process_id] = [
                progress for progress in history 
                if progress.timestamp > cutoff_iso
            ]
            
            # Remove empty histories
            if not self.progress_history[process_id]:
                processes_to_remove.append(process_id)
        
        for process_id in processes_to_remove:
            del self.progress_history[process_id]
        
        logger.info(f"🧹 Cleaned up progress history: removed {len(processes_to_remove)} old processes")

# Global progress manager instance
progress_manager = WebSocketProgressManager()

class ProgressTracker:
    """High-level progress tracking for document processing pipeline"""
    
    def __init__(self, process_id: str, filename: str, total_pages: int = 0):
        self.process_id = process_id
        self.filename = filename
        self.total_pages = total_pages
        self.start_time = time.time()
        
        # Progress tracking
        self.current_stage = ProgressStage.UPLOAD_RECEIVED
        self.entities_found = 0
        self.relationships_found = 0
        self.pages_processed = 0
        
        # Error tracking
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    async def update_stage(self, stage: ProgressStage, message: str, **kwargs):
        """Update current processing stage with progress broadcast"""
        self.current_stage = stage
        
        # Calculate progress percentage based on stage
        stage_percentages = {
            ProgressStage.UPLOAD_RECEIVED: 5.0,
            ProgressStage.TEXT_EXTRACTION: 25.0,
            ProgressStage.ENTITY_EXTRACTION: 50.0,
            ProgressStage.RELATIONSHIP_MAPPING: 75.0,
            ProgressStage.GRAPH_POPULATION: 90.0,
            ProgressStage.VERIFICATION: 100.0,
            ProgressStage.ERROR: 0.0
        }
        
        progress_percent = stage_percentages.get(stage, 0.0)
        elapsed_seconds = time.time() - self.start_time
        
        # Calculate ETA based on progress
        eta_seconds = None
        eta_message = None
        if progress_percent > 5.0 and progress_percent < 100.0:
            estimated_total_time = elapsed_seconds / (progress_percent / 100.0)
            eta_seconds = estimated_total_time - elapsed_seconds
            if eta_seconds > 0:
                if eta_seconds < 60:
                    eta_message = f"{int(eta_seconds)} seconds remaining"
                else:
                    eta_minutes = int(eta_seconds / 60)
                    eta_message = f"{eta_minutes} minute{'s' if eta_minutes != 1 else ''} remaining"
        
        # Update entity/relationship counts from kwargs
        if 'entities_found' in kwargs:
            self.entities_found = kwargs['entities_found']
        if 'relationships_found' in kwargs:
            self.relationships_found = kwargs['relationships_found']
        if 'pages_processed' in kwargs:
            self.pages_processed = kwargs['pages_processed']
        
        # Create progress update
        progress = ProgressUpdate(
            process_id=self.process_id,
            stage=stage,
            progress_percent=progress_percent,
            message=message,
            entities_found=self.entities_found,
            relationships_found=self.relationships_found,
            pages_processed=self.pages_processed,
            total_pages=self.total_pages,
            elapsed_seconds=elapsed_seconds,
            eta_seconds=eta_seconds,
            eta_message=eta_message,
            error_message=kwargs.get('error_message'),
            error_stage=kwargs.get('error_stage'),
            retry_available=kwargs.get('retry_available', False),
            success_summary=kwargs.get('success_summary')
        )
        
        # Broadcast the update
        await progress_manager.broadcast_progress(progress)
        
        logger.info(f"📊 Stage update: {stage} ({progress_percent:.1f}%) - {message}")
    
    async def report_error(self, error_message: str, stage: Optional[ProgressStage] = None, retry_available: bool = False):
        """Report an error during processing"""
        self.errors.append(error_message)
        
        await self.update_stage(
            ProgressStage.ERROR,
            f"Processing failed: {error_message}",
            error_message=error_message,
            error_stage=stage.value if stage else self.current_stage.value,
            retry_available=retry_available
        )
    
    async def report_success(self, entities_total: int, relationships_total: int, **additional_metrics):
        """Report successful completion with final metrics"""
        self.entities_found = entities_total
        self.relationships_found = relationships_total
        
        success_message = f"Ready! Found {entities_total} entities, {relationships_total} relationships"
        if self.total_pages > 0:
            success_message += f" from {self.total_pages} pages"
        
        success_summary = {
            "total_entities": entities_total,
            "total_relationships": relationships_total,
            "processing_time_seconds": time.time() - self.start_time,
            "filename": self.filename,
            **additional_metrics
        }
        
        await self.update_stage(
            ProgressStage.VERIFICATION,
            success_message,
            success_summary=success_summary
        )

def create_progress_tracker(process_id: str, filename: str, total_pages: int = 0) -> ProgressTracker:
    """Factory function to create a progress tracker"""
    return ProgressTracker(process_id, filename, total_pages)

# Utility functions for integration with existing services
async def notify_upload_received(process_id: str, filename: str, file_size: int, pages: int):
    """Notify that a file upload has been received"""
    tracker = create_progress_tracker(process_id, filename, pages)
    await tracker.update_stage(
        ProgressStage.UPLOAD_RECEIVED,
        f"Uploading {filename}... ({file_size // 1024}KB, {pages} pages)"
    )
    return tracker

async def notify_text_extraction_start(tracker: ProgressTracker):
    """Notify that text extraction has started"""
    await tracker.update_stage(
        ProgressStage.TEXT_EXTRACTION,
        "Extracting text and images from PDF..."
    )

async def notify_entity_extraction_start(tracker: ProgressTracker):
    """Notify that entity extraction has started"""
    await tracker.update_stage(
        ProgressStage.ENTITY_EXTRACTION,
        "Identifying equipment, procedures, and components..."
    )

async def notify_entity_progress(tracker: ProgressTracker, entities_found: int, relationships_found: int):
    """Update entity extraction progress"""
    # Calculate sub-progress within entity extraction stage (50-75%)
    base_progress = 50.0
    if tracker.total_pages > 0 and tracker.pages_processed > 0:
        page_progress = (tracker.pages_processed / tracker.total_pages) * 25.0
        progress_percent = base_progress + page_progress
    else:
        progress_percent = base_progress + (25.0 * min(entities_found / 50, 1.0))  # Assume 50 entities target
    
    # Override the stage progress calculation
    progress = ProgressUpdate(
        process_id=tracker.process_id,
        stage=ProgressStage.ENTITY_EXTRACTION,
        progress_percent=progress_percent,
        message=f"Found {entities_found} entities, {relationships_found} relationships so far...",
        entities_found=entities_found,
        relationships_found=relationships_found,
        pages_processed=tracker.pages_processed,
        total_pages=tracker.total_pages,
        elapsed_seconds=time.time() - tracker.start_time
    )
    
    await progress_manager.broadcast_progress(progress)

async def notify_relationship_mapping_start(tracker: ProgressTracker):
    """Notify that relationship mapping has started"""
    await tracker.update_stage(
        ProgressStage.RELATIONSHIP_MAPPING,
        "Building knowledge connections and semantic relationships..."
    )

async def notify_graph_population_start(tracker: ProgressTracker):
    """Notify that graph population has started"""
    await tracker.update_stage(
        ProgressStage.GRAPH_POPULATION,
        "Saving knowledge to Neo4j graph database..."
    )

async def notify_processing_complete(tracker: ProgressTracker, final_entities: int, final_relationships: int):
    """Notify that processing has completed successfully"""
    await tracker.report_success(final_entities, final_relationships)

async def notify_processing_error(tracker: ProgressTracker, error_message: str, retry_available: bool = True):
    """Notify that processing has failed with an error"""
    await tracker.report_error(error_message, retry_available=retry_available)