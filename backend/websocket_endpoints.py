#!/usr/bin/env python3
"""
WebSocket Endpoints for Real-time Progress Tracking
==================================================

FastAPI WebSocket endpoints for broadcasting QSR document processing progress.
Enables real-time UI updates throughout the PDF → LightRAG → Neo4j pipeline.

Endpoints:
- /ws/progress/{process_id} - Track specific process
- /ws/progress - Track all processes
- /ws/health - WebSocket health check

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from websocket_progress import progress_manager, ProgressTracker, ProgressStage

logger = logging.getLogger(__name__)

# Create router for WebSocket endpoints
websocket_router = APIRouter(prefix="/ws", tags=["WebSocket Progress"])

@websocket_router.websocket("/progress/{process_id}")
async def websocket_process_progress(websocket: WebSocket, process_id: str):
    """
    WebSocket endpoint for tracking specific process progress.
    
    Usage:
    const ws = new WebSocket('ws://localhost:8000/ws/progress/{process_id}');
    ws.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        updateProgressUI(progress);
    };
    """
    
    try:
        await progress_manager.connect(websocket, process_id)
        logger.info(f"🔌 WebSocket client connected to process {process_id}")
        
        # Send current progress status immediately if available
        from services.automatic_bridge_service import automatic_bridge_service
        current_status = automatic_bridge_service.get_process_status(process_id)
        if current_status:
            try:
                await websocket.send_json({
                    "type": "current_status",
                    **current_status
                })
                logger.info(f"📤 Sent current status to new WebSocket client for {process_id}")
            except Exception as e:
                logger.warning(f"Failed to send initial status: {e}")
        
        # Send any historical progress if available
        if hasattr(progress_manager, 'progress_history') and process_id in progress_manager.progress_history:
            recent_progress = progress_manager.progress_history[process_id]
            if recent_progress:
                latest_progress = recent_progress[-1]
                try:
                    await websocket.send_json(latest_progress.__dict__)
                    logger.info(f"📤 Sent latest progress update to new client for {process_id}")
                except Exception as e:
                    logger.warning(f"Failed to send historical progress: {e}")
        
        # Keep connection alive and handle disconnection
        while True:
            try:
                # Wait for ping/pong or client messages with timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages (ping, status requests, etc.)
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "status":
                    # Send current status if available
                    status = automatic_bridge_service.get_process_status(process_id)
                    if status:
                        await websocket.send_json({
                            "type": "status_response",
                            "status": status
                        })
                    else:
                        await websocket.send_json({
                            "type": "status_response",
                            "error": "Process not found"
                        })
                        
            except asyncio.TimeoutError:
                # Send keepalive ping to client
                try:
                    await websocket.send_json({"type": "keepalive", "timestamp": time.time()})
                except:
                    break
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"WebSocket message handling error: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket client disconnected from process {process_id}")
    except Exception as e:
        logger.error(f"WebSocket connection error for process {process_id}: {e}")
    finally:
        await progress_manager.disconnect(websocket, process_id)

@websocket_router.websocket("/progress")
async def websocket_global_progress(websocket: WebSocket):
    """
    WebSocket endpoint for tracking all process progress globally.
    
    Useful for admin dashboards or monitoring multiple uploads.
    
    Usage:
    const ws = new WebSocket('ws://localhost:8000/ws/progress');
    ws.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        updateGlobalProgressUI(progress);
    };
    """
    
    try:
        await progress_manager.connect(websocket)
        logger.info(f"🌐 WebSocket client connected globally")
        
        # Keep connection alive and handle disconnection
        while True:
            try:
                # Wait for ping/pong or client messages
                message = await websocket.receive_text()
                
                # Handle client messages
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "list_active":
                    # Send list of active processes
                    from services.automatic_bridge_service import automatic_bridge_service
                    active_processes = automatic_bridge_service.list_active_processes()
                    await websocket.send_json({
                        "type": "active_processes",
                        "processes": active_processes
                    })
                        
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"Global WebSocket message handling error: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"🌐 WebSocket client disconnected globally")
    except Exception as e:
        logger.error(f"Global WebSocket connection error: {e}")
    finally:
        await progress_manager.disconnect(websocket)

@websocket_router.websocket("/health")
async def websocket_health_check(websocket: WebSocket):
    """
    WebSocket health check endpoint for connection testing.
    
    Simple echo service for testing WebSocket connectivity.
    """
    
    try:
        await websocket.accept()
        logger.info(f"🏥 WebSocket health check connected")
        
        await websocket.send_json({
            "type": "health_check",
            "status": "connected",
            "timestamp": "2024-01-01T00:00:00Z"  # You'd use actual timestamp
        })
        
        while True:
            try:
                message = await websocket.receive_text()
                
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "echo_test":
                    await websocket.send_json({
                        "type": "echo_response",
                        "message": "WebSocket is working correctly",
                        "timestamp": "2024-01-01T00:00:00Z"
                    })
                else:
                    await websocket.send_json({
                        "type": "echo",
                        "received": message,
                        "timestamp": "2024-01-01T00:00:00Z"
                    })
                        
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"Health check WebSocket error: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"🏥 WebSocket health check disconnected")
    except Exception as e:
        logger.error(f"Health check WebSocket connection error: {e}")

# HTTP endpoints for WebSocket management and status
@websocket_router.get("/status")
async def websocket_status():
    """
    Get current WebSocket connection status and statistics.
    
    Returns information about active connections and progress history.
    """
    
    try:
        # Calculate connection statistics
        total_process_connections = sum(
            len(connections) for connections in progress_manager.active_connections.values()
        )
        
        active_processes = list(progress_manager.active_connections.keys())
        processes_with_history = list(progress_manager.progress_history.keys())
        
        # Calculate total progress updates sent
        total_updates = sum(
            len(history) for history in progress_manager.progress_history.values()
        )
        
        return JSONResponse({
            "websocket_status": "active",
            "connection_stats": {
                "global_connections": len(progress_manager.global_connections),
                "process_specific_connections": total_process_connections,
                "total_connections": len(progress_manager.global_connections) + total_process_connections,
                "active_processes": len(active_processes),
                "processes_with_history": len(processes_with_history)
            },
            "active_processes": active_processes,
            "progress_stats": {
                "total_progress_updates": total_updates,
                "average_updates_per_process": total_updates / max(len(processes_with_history), 1)
            },
            "endpoints": {
                "process_specific": "/ws/progress/{process_id}",
                "global_monitoring": "/ws/progress",
                "health_check": "/ws/health"
            }
        })
        
    except Exception as e:
        logger.error(f"WebSocket status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebSocket status")

@websocket_router.post("/cleanup")
async def cleanup_websocket_data(max_age_hours: int = 24):
    """
    Clean up old WebSocket progress data to manage memory usage.
    
    Removes progress history older than specified hours.
    """
    
    try:
        initial_processes = len(progress_manager.progress_history)
        progress_manager.cleanup_old_history(max_age_hours)
        final_processes = len(progress_manager.progress_history)
        
        cleaned_count = initial_processes - final_processes
        
        return JSONResponse({
            "cleanup_completed": True,
            "processes_cleaned": cleaned_count,
            "remaining_processes": final_processes,
            "max_age_hours": max_age_hours
        })
        
    except Exception as e:
        logger.error(f"WebSocket cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

@websocket_router.get("/progress-history/{process_id}")
async def get_progress_history(process_id: str):
    """
    Get complete progress history for a specific process.
    
    Useful for debugging or showing complete processing timeline.
    """
    
    try:
        if process_id not in progress_manager.progress_history:
            raise HTTPException(status_code=404, detail="Process not found")
        
        history = progress_manager.progress_history[process_id]
        
        return JSONResponse({
            "process_id": process_id,
            "total_updates": len(history),
            "progress_history": [update.__dict__ for update in history],
            "summary": {
                "first_update": history[0].timestamp if history else None,
                "last_update": history[-1].timestamp if history else None,
                "final_stage": history[-1].stage if history else None,
                "final_progress": history[-1].progress_percent if history else 0,
                "completed": history[-1].stage == ProgressStage.VERIFICATION if history else False,
                "had_errors": any(update.stage == ProgressStage.ERROR for update in history)
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Progress history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress history")

# Test endpoint for WebSocket functionality
@websocket_router.post("/test-progress/{process_id}")
async def test_progress_broadcast(process_id: str):
    """
    Test endpoint to simulate progress updates for development/debugging.
    
    Sends a series of mock progress updates through the WebSocket system.
    """
    
    try:
        from websocket_progress import create_progress_tracker, ProgressStage
        
        # Create a test progress tracker
        tracker = create_progress_tracker(process_id, "test_manual.pdf", 10)
        
        # Simulate the complete progress sequence
        test_stages = [
            (ProgressStage.UPLOAD_RECEIVED, "Test upload received..."),
            (ProgressStage.TEXT_EXTRACTION, "Extracting test content..."),
            (ProgressStage.ENTITY_EXTRACTION, "Finding test entities..."),
            (ProgressStage.RELATIONSHIP_MAPPING, "Building test relationships..."),
            (ProgressStage.GRAPH_POPULATION, "Saving test data..."),
            (ProgressStage.VERIFICATION, "Test completed successfully!")
        ]
        
        for stage, message in test_stages:
            await tracker.update_stage(stage, message)
            await asyncio.sleep(1)  # Small delay for realistic simulation
        
        return JSONResponse({
            "test_completed": True,
            "process_id": process_id,
            "stages_sent": len(test_stages),
            "message": "Test progress updates sent successfully"
        })
        
    except Exception as e:
        logger.error(f"Progress test failed: {e}")
        raise HTTPException(status_code=500, detail="Progress test failed")