#!/usr/bin/env python3
"""
Enhanced WebSocket Progress Tracking
===================================

Real-time progress updates for multi-format file uploads with WebSocket support.
Integrates with existing WebSocket infrastructure while adding multi-format capabilities.

Features:
- Real-time progress updates for all file types
- Backward compatible with existing WebSocket patterns
- Multi-format processing status
- Connection management and error handling
- Ragie integration status updates

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, asdict

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import JSONResponse

# Import existing patterns
from main import simple_progress_store

# Import enhanced services
from services.enhanced_qsr_ragie_service import (
    get_processing_status,
    is_ragie_service_available
)

logger = logging.getLogger(__name__)

@dataclass
class WebSocketConnection:
    """WebSocket connection information"""
    websocket: WebSocket
    client_id: str
    connected_at: datetime
    subscribed_processes: Set[str]
    
    def __post_init__(self):
        if self.subscribed_processes is None:
            self.subscribed_processes = set()

class EnhancedWebSocketManager:
    """
    Enhanced WebSocket manager for multi-format progress tracking
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.process_subscribers: Dict[str, Set[str]] = {}  # process_id -> set of client_ids
        self.update_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        try:
            await websocket.accept()
            
            connection = WebSocketConnection(
                websocket=websocket,
                client_id=client_id,
                connected_at=datetime.now(),
                subscribed_processes=set()
            )
            
            self.active_connections[client_id] = connection
            
            # Send connection confirmation
            await self._send_to_client(client_id, {
                "type": "connection_confirmed",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "supported_features": [
                    "multi_format_progress",
                    "ragie_integration", 
                    "real_time_updates",
                    "process_subscription"
                ]
            })
            
            self.logger.info(f"✅ WebSocket client {client_id} connected")
            
            # Start update task if not running
            if not self.update_task or self.update_task.done():
                self.update_task = asyncio.create_task(self._update_loop())
            
        except Exception as e:
            self.logger.error(f"WebSocket connection failed for {client_id}: {e}")
            raise
    
    async def disconnect(self, client_id: str):
        """Handle client disconnection"""
        try:
            if client_id in self.active_connections:
                connection = self.active_connections[client_id]
                
                # Remove from process subscriptions
                for process_id in connection.subscribed_processes:
                    if process_id in self.process_subscribers:
                        self.process_subscribers[process_id].discard(client_id)
                        if not self.process_subscribers[process_id]:
                            del self.process_subscribers[process_id]
                
                # Remove connection
                del self.active_connections[client_id]
                
                self.logger.info(f"❌ WebSocket client {client_id} disconnected")
                
                # Stop update task if no connections
                if not self.active_connections and self.update_task:
                    self.update_task.cancel()
                    
        except Exception as e:
            self.logger.error(f"WebSocket disconnection error for {client_id}: {e}")
    
    async def subscribe_to_process(self, client_id: str, process_id: str):
        """Subscribe client to process updates"""
        try:
            if client_id not in self.active_connections:
                return False
            
            connection = self.active_connections[client_id]
            connection.subscribed_processes.add(process_id)
            
            # Track subscribers by process
            if process_id not in self.process_subscribers:
                self.process_subscribers[process_id] = set()
            self.process_subscribers[process_id].add(client_id)
            
            # Send initial status
            await self._send_process_update(process_id, [client_id])
            
            self.logger.info(f"📡 Client {client_id} subscribed to process {process_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Process subscription failed: {e}")
            return False
    
    async def unsubscribe_from_process(self, client_id: str, process_id: str):
        """Unsubscribe client from process updates"""
        try:
            if client_id in self.active_connections:
                connection = self.active_connections[client_id]
                connection.subscribed_processes.discard(process_id)
            
            if process_id in self.process_subscribers:
                self.process_subscribers[process_id].discard(client_id)
                if not self.process_subscribers[process_id]:
                    del self.process_subscribers[process_id]
            
            self.logger.info(f"📡 Client {client_id} unsubscribed from process {process_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Process unsubscription failed: {e}")
            return False
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            if client_id in self.active_connections:
                connection = self.active_connections[client_id]
                await connection.websocket.send_text(json.dumps(message))
                
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            self.logger.error(f"Failed to send message to client {client_id}: {e}")
            await self.disconnect(client_id)
    
    async def _send_to_multiple_clients(self, client_ids: List[str], message: Dict[str, Any]):
        """Send message to multiple clients"""
        tasks = []
        for client_id in client_ids:
            if client_id in self.active_connections:
                tasks.append(self._send_to_client(client_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_process_update(self, process_id: str, target_clients: Optional[List[str]] = None):
        """Send process update to subscribed clients"""
        try:
            # Get subscribers for this process
            if target_clients is None:
                target_clients = list(self.process_subscribers.get(process_id, set()))
            
            if not target_clients:
                return
            
            # Get local progress
            local_progress = simple_progress_store.get(process_id)
            
            # Get Ragie progress if available
            ragie_progress = None
            if is_ragie_service_available():
                ragie_status = get_processing_status(process_id)
                if ragie_status:
                    ragie_progress = {
                        "status": ragie_status.status,
                        "progress_percent": ragie_status.progress_percent,
                        "current_operation": ragie_status.current_operation,
                        "error_message": ragie_status.error_message,
                        "completed_at": ragie_status.completed_at.isoformat() if ragie_status.completed_at else None
                    }
            
            # Combine progress information
            if local_progress:
                update_message = {
                    "type": "progress_update",
                    "process_id": process_id,
                    "timestamp": datetime.now().isoformat(),
                    "local_progress": local_progress,
                    "ragie_progress": ragie_progress,
                    "filename": local_progress.get("filename", "unknown"),
                    "file_type": local_progress.get("file_type", "unknown"),
                    "status": local_progress.get("status", "unknown")
                }
            elif ragie_progress:
                update_message = {
                    "type": "progress_update",
                    "process_id": process_id,
                    "timestamp": datetime.now().isoformat(),
                    "local_progress": None,
                    "ragie_progress": ragie_progress,
                    "filename": "unknown",
                    "file_type": "unknown",
                    "status": ragie_progress["status"]
                }
            else:
                # Process not found
                update_message = {
                    "type": "progress_update",
                    "process_id": process_id,
                    "timestamp": datetime.now().isoformat(),
                    "local_progress": None,
                    "ragie_progress": None,
                    "filename": "unknown",
                    "file_type": "unknown",
                    "status": "not_found",
                    "error": "Process not found"
                }
            
            # Send to subscribed clients
            await self._send_to_multiple_clients(target_clients, update_message)
            
        except Exception as e:
            self.logger.error(f"Failed to send process update for {process_id}: {e}")
    
    async def _update_loop(self):
        """Main update loop for sending progress updates"""
        try:
            while self.active_connections:
                # Get all processes being tracked
                all_processes = set()
                
                # Add local processes
                all_processes.update(simple_progress_store.keys())
                
                # Add Ragie processes if available
                if is_ragie_service_available():
                    try:
                        from services.enhanced_qsr_ragie_service import enhanced_qsr_ragie_service
                        ragie_statuses = enhanced_qsr_ragie_service.get_all_processing_statuses()
                        all_processes.update(ragie_statuses.keys())
                    except Exception as e:
                        self.logger.warning(f"Failed to get Ragie processes: {e}")
                
                # Send updates for processes with subscribers
                for process_id in all_processes:
                    if process_id in self.process_subscribers:
                        await self._send_process_update(process_id)
                
                # Send system status to all clients
                await self._send_system_status()
                
                # Wait before next update
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except asyncio.CancelledError:
            self.logger.info("WebSocket update loop cancelled")
        except Exception as e:
            self.logger.error(f"WebSocket update loop error: {e}")
    
    async def _send_system_status(self):
        """Send system status to all connected clients"""
        try:
            if not self.active_connections:
                return
            
            # Get system status
            active_processes = len(simple_progress_store)
            ragie_available = is_ragie_service_available()
            
            # Count processes by status
            status_counts = {"uploaded": 0, "processing": 0, "completed": 0, "failed": 0}
            for process_data in simple_progress_store.values():
                status = process_data.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1
            
            system_message = {
                "type": "system_status",
                "timestamp": datetime.now().isoformat(),
                "active_connections": len(self.active_connections),
                "active_processes": active_processes,
                "status_counts": status_counts,
                "ragie_available": ragie_available,
                "total_subscriptions": sum(len(subs) for subs in self.process_subscribers.values())
            }
            
            # Send to all clients
            client_ids = list(self.active_connections.keys())
            await self._send_to_multiple_clients(client_ids, system_message)
            
        except Exception as e:
            self.logger.error(f"Failed to send system status: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about current connections"""
        return {
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.process_subscribers.values()),
            "tracked_processes": len(self.process_subscribers),
            "update_task_running": self.update_task and not self.update_task.done()
        }

# Global WebSocket manager
websocket_manager = EnhancedWebSocketManager()

# Create router for WebSocket endpoints
websocket_router = APIRouter(prefix="/ws", tags=["WebSocket"])

@websocket_router.websocket("/progress")
async def websocket_progress_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time progress updates
    
    Protocol:
    - Send: {"action": "subscribe", "process_id": "process_id"}
    - Send: {"action": "unsubscribe", "process_id": "process_id"}
    - Receive: {"type": "progress_update", "process_id": "...", "progress": {...}}
    """
    
    client_id = f"client_{datetime.now().timestamp()}"
    
    try:
        await websocket_manager.connect(websocket, client_id)
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                action = message.get("action")
                process_id = message.get("process_id")
                
                if action == "subscribe" and process_id:
                    success = await websocket_manager.subscribe_to_process(client_id, process_id)
                    await websocket_manager._send_to_client(client_id, {
                        "type": "subscription_response",
                        "action": "subscribe",
                        "process_id": process_id,
                        "success": success
                    })
                
                elif action == "unsubscribe" and process_id:
                    success = await websocket_manager.unsubscribe_from_process(client_id, process_id)
                    await websocket_manager._send_to_client(client_id, {
                        "type": "subscription_response",
                        "action": "unsubscribe",
                        "process_id": process_id,
                        "success": success
                    })
                
                elif action == "ping":
                    await websocket_manager._send_to_client(client_id, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                else:
                    await websocket_manager._send_to_client(client_id, {
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })
                    
            except json.JSONDecodeError:
                await websocket_manager._send_to_client(client_id, {
                    "type": "error",
                    "message": "Invalid JSON message"
                })
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await websocket_manager.disconnect(client_id)

@websocket_router.get("/info")
async def websocket_info():
    """Get WebSocket connection information"""
    try:
        info = websocket_manager.get_connection_info()
        return {
            "success": True,
            "websocket_info": info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@websocket_router.post("/notify/{process_id}")
async def notify_process_update(process_id: str):
    """
    Manually trigger process update notification
    
    Useful for testing or external integrations
    """
    try:
        await websocket_manager._send_process_update(process_id)
        return {
            "success": True,
            "message": f"Update sent for process {process_id}",
            "subscribers": len(websocket_manager.process_subscribers.get(process_id, set()))
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Helper functions for integration
async def notify_upload_started(process_id: str, filename: str, file_type: str):
    """Notify WebSocket clients that upload started"""
    try:
        if process_id in websocket_manager.process_subscribers:
            await websocket_manager._send_to_multiple_clients(
                list(websocket_manager.process_subscribers[process_id]),
                {
                    "type": "upload_started",
                    "process_id": process_id,
                    "filename": filename,
                    "file_type": file_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Failed to notify upload started: {e}")

async def notify_upload_completed(process_id: str, filename: str, success: bool, error_message: str = None):
    """Notify WebSocket clients that upload completed"""
    try:
        if process_id in websocket_manager.process_subscribers:
            await websocket_manager._send_to_multiple_clients(
                list(websocket_manager.process_subscribers[process_id]),
                {
                    "type": "upload_completed",
                    "process_id": process_id,
                    "filename": filename,
                    "success": success,
                    "error_message": error_message,
                    "timestamp": datetime.now().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Failed to notify upload completed: {e}")

def get_websocket_manager():
    """Get global WebSocket manager instance"""
    return websocket_manager