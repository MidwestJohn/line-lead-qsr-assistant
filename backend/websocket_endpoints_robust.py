#!/usr/bin/env python3
"""
Robust WebSocket Endpoints for Real-time Progress Tracking
========================================================

Enhanced WebSocket endpoints with comprehensive error handling, graceful degradation,
and backend crash prevention. Replaces the existing websocket_endpoints.py with
a production-ready implementation.

Key Features:
- Robust error handling that prevents backend crashes
- Graceful degradation when WebSocket fails
- Automatic connection cleanup and memory management
- HTTP fallback endpoints for progress tracking
- Comprehensive health monitoring

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import JSONResponse

from websocket_robust_fix import (
    robust_websocket_manager,
    handle_websocket_connection,
    broadcast_progress_update,
    get_websocket_health
)

logger = logging.getLogger(__name__)

# Create router for robust WebSocket endpoints
websocket_router = APIRouter(prefix="/ws", tags=["Robust WebSocket Progress"])

@websocket_router.websocket("/progress/{process_id}")
async def websocket_process_progress_robust(websocket: WebSocket, process_id: str):
    """
    Robust WebSocket endpoint for tracking specific process progress.
    
    Features:
    - Automatic connection recovery
    - Error isolation (won't crash backend)
    - Graceful degradation
    - Memory leak prevention
    
    Usage:
    const ws = new WebSocket('ws://localhost:8000/ws/progress/{process_id}');
    ws.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        updateProgressUI(progress);
    };
    """
    
    await handle_websocket_connection(websocket, process_id)

@websocket_router.websocket("/progress")
async def websocket_global_progress_robust(websocket: WebSocket):
    """
    Robust WebSocket endpoint for global progress monitoring.
    
    Features:
    - Monitor all active processes
    - Automatic cleanup of stale connections
    - Error isolation
    - Connection limits to prevent overload
    """
    
    connection_id = None
    try:
        connection_id = await robust_websocket_manager.connect_global(websocket)
        
        if not connection_id:
            logger.error("Failed to establish global WebSocket connection")
            return
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await robust_websocket_manager.handle_client_message(connection_id, message)
                
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "keepalive", "timestamp": time.time()})
                except:
                    break
                    
            except WebSocketDisconnect:
                break
                
            except Exception as e:
                logger.warning(f"Global WebSocket message error: {e}")
                
    except Exception as e:
        logger.error(f"Global WebSocket connection error: {e}")
        
    finally:
        if connection_id:
            await robust_websocket_manager.disconnect(connection_id)

@websocket_router.websocket("/health")
async def websocket_health_check_robust(websocket: WebSocket):
    """
    Robust WebSocket health check endpoint.
    
    Simple echo service for testing WebSocket connectivity with error protection.
    """
    
    try:
        await websocket.accept()
        logger.info("🏥 WebSocket health check connected")
        
        await websocket.send_json({
            "type": "health_check",
            "status": "connected",
            "timestamp": time.time(),
            "server_info": {
                "websocket_system": "robust",
                "error_protection": True,
                "backend_crash_prevention": True
            }
        })
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "health_status":
                    health_info = get_websocket_health()
                    await websocket.send_json({
                        "type": "health_status",
                        **health_info
                    })
                elif message == "connection_stats":
                    stats = robust_websocket_manager.get_connection_stats()
                    await websocket.send_json({
                        "type": "connection_stats",
                        **stats
                    })
                else:
                    await websocket.send_json({
                        "type": "echo",
                        "received": message,
                        "timestamp": time.time()
                    })
                        
            except asyncio.TimeoutError:
                # Send periodic keepalive
                try:
                    await websocket.send_json({
                        "type": "keepalive",
                        "timestamp": time.time()
                    })
                except:
                    break
                    
            except WebSocketDisconnect:
                break
                
            except Exception as e:
                logger.warning(f"Health check WebSocket error: {e}")
                # Continue on errors
    
    except Exception as e:
        logger.error(f"Health check WebSocket connection error: {e}")
    
    finally:
        logger.info("🏥 WebSocket health check disconnected")

# HTTP Fallback Endpoints for Progress Tracking
# These provide alternative access when WebSocket fails

@websocket_router.get("/progress/{process_id}")
async def get_process_progress_http(process_id: str):
    """
    HTTP fallback for getting process progress when WebSocket fails.
    
    Returns the latest progress update for the specified process.
    """
    
    try:
        # Get progress from cache
        if process_id in robust_websocket_manager.progress_cache:
            progress_history = robust_websocket_manager.progress_cache[process_id]
            if progress_history:
                latest_progress = progress_history[-1]
                return JSONResponse({
                    "success": True,
                    "process_id": process_id,
                    "progress": latest_progress,
                    "fallback_mode": True,
                    "websocket_available": False
                })
        
        # Try to get from automatic bridge service
        try:
            from services.automatic_bridge_service import automatic_bridge_service
            status = automatic_bridge_service.get_process_status(process_id)
            if status:
                return JSONResponse({
                    "success": True,
                    "process_id": process_id,
                    "progress": status,
                    "fallback_mode": True,
                    "websocket_available": False
                })
        except Exception as bridge_error:
            logger.warning(f"Bridge service unavailable: {bridge_error}")
        
        return JSONResponse({
            "success": False,
            "process_id": process_id,
            "error": "Process not found",
            "fallback_mode": True
        })
        
    except Exception as e:
        logger.error(f"HTTP progress fallback failed: {e}")
        raise HTTPException(status_code=500, detail="Progress retrieval failed")

@websocket_router.get("/progress")
async def get_all_progress_http():
    """
    HTTP fallback for getting all active process progress.
    
    Returns progress for all active processes when WebSocket fails.
    """
    
    try:
        all_progress = {}
        
        # Get from WebSocket cache
        for process_id, progress_history in robust_websocket_manager.progress_cache.items():
            if progress_history:
                all_progress[process_id] = progress_history[-1]
        
        # Get from automatic bridge service
        try:
            from services.automatic_bridge_service import automatic_bridge_service
            active_processes = automatic_bridge_service.list_active_processes()
            for process_id, status in active_processes.items():
                if process_id not in all_progress:
                    all_progress[process_id] = status
        except Exception as bridge_error:
            logger.warning(f"Bridge service unavailable: {bridge_error}")
        
        return JSONResponse({
            "success": True,
            "active_processes": len(all_progress),
            "progress": all_progress,
            "fallback_mode": True,
            "websocket_available": False
        })
        
    except Exception as e:
        logger.error(f"HTTP all progress fallback failed: {e}")
        raise HTTPException(status_code=500, detail="Progress retrieval failed")

@websocket_router.get("/status")
async def websocket_status_robust():
    """
    Get comprehensive WebSocket system status and health information.
    
    Provides detailed information about WebSocket health, connections, and fallback options.
    """
    
    try:
        # Get WebSocket health
        health_info = get_websocket_health()
        
        # Get connection statistics
        connection_stats = robust_websocket_manager.get_connection_stats()
        
        # Get progress cache info
        cache_info = {
            "cached_processes": len(robust_websocket_manager.progress_cache),
            "total_progress_updates": sum(
                len(history) for history in robust_websocket_manager.progress_cache.values()
            )
        }
        
        return JSONResponse({
            "websocket_health": health_info,
            "connection_statistics": connection_stats,
            "progress_cache": cache_info,
            "fallback_endpoints": {
                "process_progress": "/ws/progress/{process_id}",
                "all_progress": "/ws/progress",
                "health_check": "/ws/health"
            },
            "websocket_endpoints": {
                "process_websocket": "/ws/progress/{process_id}",
                "global_websocket": "/ws/progress",
                "health_websocket": "/ws/health"
            },
            "system_info": {
                "robust_mode": True,
                "error_protection": True,
                "backend_crash_prevention": True,
                "graceful_degradation": True
            }
        })
        
    except Exception as e:
        logger.error(f"WebSocket status check failed: {e}")
        return JSONResponse({
            "error": "Status check failed",
            "details": str(e),
            "fallback_available": True
        }, status_code=500)

@websocket_router.post("/test/{process_id}")
async def test_websocket_system(process_id: str):
    """
    Test the complete WebSocket system with a mock progress sequence.
    
    Useful for debugging WebSocket connectivity and progress broadcasting.
    """
    
    try:
        logger.info(f"🧪 Starting WebSocket test for process {process_id}")
        
        # Test progress sequence
        test_progress = [
            {
                "stage": "upload_received",
                "progress_percent": 10,
                "message": f"Test upload received for {process_id}",
                "entities_found": 0,
                "relationships_found": 0
            },
            {
                "stage": "text_extraction",
                "progress_percent": 30,
                "message": "Extracting test content...",
                "entities_found": 5,
                "relationships_found": 2
            },
            {
                "stage": "entity_extraction",
                "progress_percent": 60,
                "message": "Finding test entities...",
                "entities_found": 15,
                "relationships_found": 8
            },
            {
                "stage": "relationship_mapping",
                "progress_percent": 80,
                "message": "Building test relationships...",
                "entities_found": 25,
                "relationships_found": 18
            },
            {
                "stage": "verification",
                "progress_percent": 100,
                "message": "Test completed successfully!",
                "entities_found": 30,
                "relationships_found": 25,
                "success_summary": {
                    "total_entities": 30,
                    "total_relationships": 25,
                    "processing_time": "45 seconds"
                }
            }
        ]
        
        # Broadcast test progress with delays
        for i, progress in enumerate(test_progress):
            await broadcast_progress_update(process_id, progress)
            logger.info(f"📡 Sent test progress {i+1}/{len(test_progress)}")
            
            if i < len(test_progress) - 1:  # Don't delay after the last update
                await asyncio.sleep(2)  # 2 second delay between updates
        
        return JSONResponse({
            "test_completed": True,
            "process_id": process_id,
            "updates_sent": len(test_progress),
            "websocket_health": get_websocket_health(),
            "message": "WebSocket test completed successfully"
        })
        
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")
        return JSONResponse({
            "test_completed": False,
            "process_id": process_id,
            "error": str(e),
            "message": "WebSocket test failed"
        }, status_code=500)

@websocket_router.post("/cleanup")
async def cleanup_websocket_data_robust(max_age_hours: int = Query(24, ge=1, le=168)):
    """
    Clean up old WebSocket data and stale connections.
    
    Performs maintenance to prevent memory leaks and clean up old progress data.
    """
    
    try:
        initial_connections = len(robust_websocket_manager.connections)
        initial_processes = len(robust_websocket_manager.progress_cache)
        
        # Force cleanup
        await robust_websocket_manager._cleanup_stale_connections()
        
        final_connections = len(robust_websocket_manager.connections)
        final_processes = len(robust_websocket_manager.progress_cache)
        
        return JSONResponse({
            "cleanup_completed": True,
            "connections_cleaned": initial_connections - final_connections,
            "processes_cleaned": initial_processes - final_processes,
            "remaining_connections": final_connections,
            "remaining_processes": final_processes,
            "max_age_hours": max_age_hours
        })
        
    except Exception as e:
        logger.error(f"WebSocket cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

# Integration function to broadcast progress from the upload pipeline
async def notify_upload_progress(process_id: str, stage: str, progress_percent: float, 
                                message: str, **kwargs):
    """
    Integration function for the upload pipeline to broadcast progress updates.
    
    This function is called by the automatic bridge service to update WebSocket clients.
    It includes comprehensive error handling to prevent upload pipeline crashes.
    """
    
    try:
        progress_data = {
            "process_id": process_id,
            "stage": stage,
            "progress_percent": progress_percent,
            "message": message,
            "timestamp": time.time(),
            **kwargs
        }
        
        await broadcast_progress_update(process_id, progress_data)
        logger.debug(f"📡 Upload progress broadcast: {process_id} - {progress_percent}%")
        
    except Exception as e:
        logger.error(f"Upload progress broadcast failed (but upload continues): {e}")
        # Never let WebSocket failures stop the upload process


# HTTP Fallback Endpoints
@websocket_router.get("/progress/{process_id}")
async def get_process_progress_http(process_id: str):
    """
    HTTP fallback endpoint to get progress for a specific process.
    
    This endpoint serves as a fallback when WebSocket connections fail.
    """
    
    try:
        # Get latest progress from cache
        progress_history = robust_websocket_manager.progress_cache.get(process_id, [])
        
        if not progress_history:
            return JSONResponse({
                "success": False,
                "process_id": process_id,
                "error": "Process not found",
                "fallback_mode": True
            }, status_code=404)
        
        # Get the latest progress update
        latest_progress = progress_history[-1] if progress_history else None
        
        return JSONResponse({
            "success": True,
            "process_id": process_id,
            "progress": latest_progress,
            "progress_history_length": len(progress_history),
            "fallback_mode": True,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"HTTP progress fallback failed for {process_id}: {e}")
        return JSONResponse({
            "process_id": process_id,
            "status": "error",
            "error": str(e),
            "fallback_mode": True
        }, status_code=500)


@websocket_router.get("/progress")
async def get_all_progress_http():
    """
    HTTP fallback endpoint to get progress for all active processes.
    
    This endpoint serves as a fallback when WebSocket connections fail.
    """
    
    try:
        all_progress = {}
        
        for process_id, progress_history in robust_websocket_manager.progress_cache.items():
            if progress_history:
                all_progress[process_id] = {
                    "latest_progress": progress_history[-1],
                    "total_updates": len(progress_history)
                }
        
        return JSONResponse({
            "status": "success",
            "active_processes": len(all_progress),
            "processes": all_progress,
            "fallback_mode": True,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"HTTP progress fallback failed for all processes: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "fallback_mode": True
        }, status_code=500)