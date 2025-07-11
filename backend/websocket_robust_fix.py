#!/usr/bin/env python3
"""
Robust WebSocket Fix for Line Lead QSR System
============================================

Comprehensive solution for WebSocket connection failures and backend stability.
Implements graceful degradation, error recovery, and prevents backend crashes.

Key Issues Addressed:
1. WebSocket connection failures with code 1006
2. Backend crashes when WebSocket fails
3. Repeated failed connection attempts
4. No graceful fallback when WebSocket unavailable
5. React Strict Mode causing multiple connections

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ConnectionState(str, Enum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    websocket: WebSocket
    process_id: Optional[str]
    connected_at: datetime
    last_ping: datetime
    state: ConnectionState = ConnectionState.CONNECTING
    error_count: int = 0
    
    def to_dict(self):
        return {
            "process_id": self.process_id,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping.isoformat(),
            "state": self.state.value,
            "error_count": self.error_count
        }

class RobustWebSocketManager:
    """
    Robust WebSocket manager with error recovery and graceful degradation
    """
    
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}  # connection_id -> ConnectionInfo
        self.process_connections: Dict[str, Set[str]] = {}  # process_id -> set of connection_ids
        self.global_connections: Set[str] = set()  # connection_ids for global listeners
        self.progress_cache: Dict[str, List[Dict]] = {}  # process_id -> progress history
        self.connection_counter = 0
        self.max_connections = 100  # Prevent memory issues
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
    def _generate_connection_id(self) -> str:
        """Generate unique connection ID"""
        self.connection_counter += 1
        return f"conn_{int(time.time())}_{self.connection_counter}"
    
    async def connect_process(self, websocket: WebSocket, process_id: str) -> Optional[str]:
        """
        Connect WebSocket to specific process with robust error handling
        """
        connection_id = None
        try:
            # Check connection limits
            if len(self.connections) >= self.max_connections:
                logger.warning(f"Connection limit reached ({self.max_connections}), refusing new connection")
                await websocket.close(code=1008, reason="Server overloaded")
                return None
            
            # Accept connection with timeout
            try:
                await asyncio.wait_for(websocket.accept(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.error(f"WebSocket accept timeout for process {process_id}")
                return None
            
            connection_id = self._generate_connection_id()
            now = datetime.now()
            
            # Create connection info
            conn_info = ConnectionInfo(
                websocket=websocket,
                process_id=process_id,
                connected_at=now,
                last_ping=now,
                state=ConnectionState.CONNECTED
            )
            
            # Store connection
            self.connections[connection_id] = conn_info
            
            # Add to process connections
            if process_id not in self.process_connections:
                self.process_connections[process_id] = set()
            self.process_connections[process_id].add(connection_id)
            
            logger.info(f"✅ WebSocket connected: {connection_id} for process {process_id}")
            
            # Send cached progress if available
            await self._send_cached_progress(connection_id, process_id)
            
            return connection_id
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed for process {process_id}: {e}")
            if connection_id and connection_id in self.connections:
                del self.connections[connection_id]
            try:
                await websocket.close(code=1011, reason="Internal error")
            except:
                pass
            return None
    
    async def connect_global(self, websocket: WebSocket) -> Optional[str]:
        """
        Connect WebSocket for global monitoring with robust error handling
        """
        connection_id = None
        try:
            # Check connection limits
            if len(self.connections) >= self.max_connections:
                logger.warning(f"Connection limit reached ({self.max_connections}), refusing global connection")
                await websocket.close(code=1008, reason="Server overloaded")
                return None
            
            # Accept connection with timeout
            try:
                await asyncio.wait_for(websocket.accept(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.error("WebSocket accept timeout for global connection")
                return None
            
            connection_id = self._generate_connection_id()
            now = datetime.now()
            
            # Create connection info
            conn_info = ConnectionInfo(
                websocket=websocket,
                process_id=None,
                connected_at=now,
                last_ping=now,
                state=ConnectionState.CONNECTED
            )
            
            # Store connection
            self.connections[connection_id] = conn_info
            self.global_connections.add(connection_id)
            
            logger.info(f"✅ Global WebSocket connected: {connection_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"❌ Global WebSocket connection failed: {e}")
            if connection_id and connection_id in self.connections:
                del self.connections[connection_id]
            try:
                await websocket.close(code=1011, reason="Internal error")
            except:
                pass
            return None
    
    async def disconnect(self, connection_id: str):
        """
        Safely disconnect WebSocket with cleanup
        """
        try:
            if connection_id not in self.connections:
                return
            
            conn_info = self.connections[connection_id]
            conn_info.state = ConnectionState.DISCONNECTING
            
            # Remove from process connections
            if conn_info.process_id and conn_info.process_id in self.process_connections:
                self.process_connections[conn_info.process_id].discard(connection_id)
                if not self.process_connections[conn_info.process_id]:
                    del self.process_connections[conn_info.process_id]
            
            # Remove from global connections
            self.global_connections.discard(connection_id)
            
            # Remove connection
            del self.connections[connection_id]
            
            logger.info(f"🔌 WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"❌ Error during WebSocket disconnect: {e}")
    
    async def broadcast_progress(self, process_id: str, progress_data: Dict[str, Any]):
        """
        Broadcast progress with robust error handling and automatic cleanup
        """
        try:
            # Cache progress data
            if process_id not in self.progress_cache:
                self.progress_cache[process_id] = []
            
            self.progress_cache[process_id].append({
                **progress_data,
                "timestamp": datetime.now().isoformat()
            })
            
            # Limit cache size
            if len(self.progress_cache[process_id]) > 50:
                self.progress_cache[process_id] = self.progress_cache[process_id][-50:]
            
            # Get connections for this process
            connection_ids = self.process_connections.get(process_id, set()).copy()
            connection_ids.update(self.global_connections)
            
            successful_sends = 0
            failed_connections = []
            
            for connection_id in connection_ids:
                if connection_id not in self.connections:
                    failed_connections.append(connection_id)
                    continue
                
                conn_info = self.connections[connection_id]
                if conn_info.state != ConnectionState.CONNECTED:
                    continue
                
                try:
                    await asyncio.wait_for(
                        conn_info.websocket.send_json(progress_data),
                        timeout=5.0
                    )
                    successful_sends += 1
                    conn_info.last_ping = datetime.now()
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Send timeout for connection {connection_id}")
                    conn_info.error_count += 1
                    failed_connections.append(connection_id)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket {connection_id} disconnected during send")
                    failed_connections.append(connection_id)
                    
                except Exception as e:
                    logger.warning(f"Send failed for connection {connection_id}: {e}")
                    conn_info.error_count += 1
                    if conn_info.error_count > 3:
                        failed_connections.append(connection_id)
            
            # Clean up failed connections
            for connection_id in failed_connections:
                await self.disconnect(connection_id)
            
            logger.info(f"📡 Progress broadcast: {successful_sends} successful, {len(failed_connections)} failed")
            
            # Periodic cleanup
            if time.time() - self.last_cleanup > self.cleanup_interval:
                await self._cleanup_stale_connections()
                self.last_cleanup = time.time()
            
        except Exception as e:
            logger.error(f"❌ Progress broadcast failed: {e}")
            # Don't let broadcast failures crash the system
    
    async def _send_cached_progress(self, connection_id: str, process_id: str):
        """Send cached progress to newly connected client"""
        try:
            if process_id not in self.progress_cache:
                return
            
            conn_info = self.connections.get(connection_id)
            if not conn_info or conn_info.state != ConnectionState.CONNECTED:
                return
            
            # Send recent progress updates
            recent_progress = self.progress_cache[process_id][-10:]  # Last 10 updates
            
            for progress_data in recent_progress:
                try:
                    await conn_info.websocket.send_json({
                        "type": "cached_progress",
                        **progress_data
                    })
                except:
                    break  # Stop if any send fails
                    
            logger.info(f"📤 Sent {len(recent_progress)} cached progress updates to {connection_id}")
            
        except Exception as e:
            logger.warning(f"Failed to send cached progress: {e}")
    
    async def _cleanup_stale_connections(self):
        """Clean up stale connections and old progress data"""
        try:
            current_time = datetime.now()
            stale_connections = []
            
            for connection_id, conn_info in self.connections.items():
                # Check for stale connections (no ping in 10 minutes)
                if (current_time - conn_info.last_ping).total_seconds() > 600:
                    stale_connections.append(connection_id)
                    continue
                
                # Check for error-prone connections
                if conn_info.error_count > 5:
                    stale_connections.append(connection_id)
            
            # Clean up stale connections
            for connection_id in stale_connections:
                await self.disconnect(connection_id)
            
            # Clean up old progress data (keep only last 24 hours)
            cutoff_time = current_time.timestamp() - (24 * 3600)
            
            for process_id in list(self.progress_cache.keys()):
                self.progress_cache[process_id] = [
                    update for update in self.progress_cache[process_id]
                    if datetime.fromisoformat(update["timestamp"]).timestamp() > cutoff_time
                ]
                
                if not self.progress_cache[process_id]:
                    del self.progress_cache[process_id]
            
            if stale_connections:
                logger.info(f"🧹 Cleaned up {len(stale_connections)} stale WebSocket connections")
            
        except Exception as e:
            logger.error(f"❌ Connection cleanup failed: {e}")
    
    async def handle_client_message(self, connection_id: str, message: str):
        """Handle incoming client messages with error protection"""
        try:
            conn_info = self.connections.get(connection_id)
            if not conn_info:
                return
            
            conn_info.last_ping = datetime.now()
            
            if message == "ping":
                await conn_info.websocket.send_text("pong")
            elif message == "status":
                # Send connection status
                await conn_info.websocket.send_json({
                    "type": "connection_status",
                    "connection_id": connection_id,
                    "connected_at": conn_info.connected_at.isoformat(),
                    "state": conn_info.state.value
                })
            elif message.startswith("get_progress:"):
                # Get progress for specific process
                requested_process = message.split(":", 1)[1]
                if requested_process in self.progress_cache:
                    latest_progress = self.progress_cache[requested_process][-1]
                    await conn_info.websocket.send_json({
                        "type": "progress_response",
                        "process_id": requested_process,
                        **latest_progress
                    })
            
        except Exception as e:
            logger.warning(f"Client message handling failed: {e}")
            # Don't disconnect on message handling errors
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        try:
            active_count = sum(1 for conn in self.connections.values() 
                             if conn.state == ConnectionState.CONNECTED)
            
            process_count = len(self.process_connections)
            global_count = len(self.global_connections)
            
            return {
                "total_connections": len(self.connections),
                "active_connections": active_count,
                "process_connections": process_count,
                "global_connections": global_count,
                "cached_processes": len(self.progress_cache),
                "last_cleanup": self.last_cleanup,
                "connection_limit": self.max_connections
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {"error": str(e)}

# Global robust manager instance
robust_websocket_manager = RobustWebSocketManager()


async def handle_websocket_connection(websocket: WebSocket, process_id: str):
    """
    Robust WebSocket connection handler that prevents backend crashes
    """
    connection_id = None
    try:
        # Connect with robust error handling
        connection_id = await robust_websocket_manager.connect_process(websocket, process_id)
        
        if not connection_id:
            logger.error(f"Failed to establish WebSocket connection for process {process_id}")
            return
        
        # Connection loop with comprehensive error handling
        while True:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await robust_websocket_manager.handle_client_message(connection_id, message)
                
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "keepalive", "timestamp": time.time()})
                except:
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
                
            except Exception as e:
                logger.warning(f"WebSocket message error: {e}")
                # Continue on message errors, don't break connection
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id or 'unknown'}")
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
    finally:
        # Always clean up, even if errors occurred
        if connection_id:
            await robust_websocket_manager.disconnect(connection_id)


async def broadcast_progress_update(process_id: str, progress_data: Dict[str, Any]):
    """
    Broadcast progress update with error protection
    """
    try:
        await robust_websocket_manager.broadcast_progress(process_id, progress_data)
    except Exception as e:
        logger.error(f"Progress broadcast failed but system continues: {e}")
        # Never let WebSocket failures crash the main process


def get_websocket_health() -> Dict[str, Any]:
    """
    Get WebSocket system health status
    """
    try:
        stats = robust_websocket_manager.get_connection_stats()
        return {
            "status": "healthy",
            "websocket_enabled": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "websocket_enabled": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }