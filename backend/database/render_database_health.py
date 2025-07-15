#!/usr/bin/env python3
"""
Render Database Health Integration
=================================

Database health monitoring optimized for Render PostgreSQL deployment,
following BaseChat's database health patterns.

Features:
- Render PostgreSQL connection pool health monitoring
- Query performance tracking for conversation storage
- Database resource usage monitoring
- Connection stability metrics
- Async operation performance optimization

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import asyncpg
import os
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class DatabaseHealthMetrics:
    """Database health metrics for monitoring"""
    connection_count: int = 0
    avg_query_time: float = 0.0
    last_health_check: float = 0.0
    total_connections_made: int = 0
    failed_connections: int = 0
    conversation_count_24h: int = 0
    database_size: str = "unknown"

class RenderDatabaseHealth:
    """Database health monitoring for Render PostgreSQL"""
    
    def __init__(self):
        """Initialize database health monitoring"""
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            # Fallback for development or file-based storage
            self.database_url = None
            logger.info("📂 No DATABASE_URL found - using file-based storage")
        
        self.pool = None
        self.metrics = DatabaseHealthMetrics()
        
        # Render-optimized pool settings
        self.pool_settings = {
            "min_size": 2,          # Render optimization - minimal connections
            "max_size": 10,         # Render connection limits
            "command_timeout": 30,   # Reasonable timeout for Render
            "server_settings": {
                'jit': 'off',        # Render PostgreSQL optimization
                'application_name': 'line-lead-qsr-health'
            }
        }
        
        logger.info("🗄️ Render Database Health monitoring initialized")
    
    async def initialize_pool(self) -> bool:
        """Initialize database connection pool with Render optimizations"""
        if not self.database_url:
            logger.info("📂 Skipping database pool initialization - using file storage")
            return False
        
        if self.pool:
            return True
        
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                **self.pool_settings
            )
            
            logger.info("✅ Database connection pool initialized for Render PostgreSQL")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            self.metrics.failed_connections += 1
            return False
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        start_time = time.time()
        
        # If no database URL, return file storage status
        if not self.database_url:
            return {
                "status": "file_storage",
                "storage_type": "local_file_system",
                "database": "none",
                "message": "Using file-based conversation storage",
                "performance_ms": (time.time() - start_time) * 1000,
                "fallback_active": True
            }
        
        try:
            # Initialize pool if needed
            pool_initialized = await self.initialize_pool()
            if not pool_initialized:
                return self._create_error_response("Failed to initialize connection pool", start_time)
            
            # Test basic connectivity
            async with self.pool.acquire() as connection:
                # Basic connectivity test
                connectivity_start = time.time()
                result = await connection.fetchval("SELECT 1")
                connectivity_time = (time.time() - connectivity_start) * 1000
                
                if result != 1:
                    return self._create_error_response("Database connectivity test failed", start_time)
                
                # Check conversation table health (if exists)
                conversation_count = await self._check_conversation_health(connection)
                
                # Check database performance metrics
                db_metrics = await self._get_database_metrics(connection)
                
                # Update internal metrics
                response_time = (time.time() - start_time) * 1000
                self.metrics.avg_query_time = response_time
                self.metrics.last_health_check = time.time()
                self.metrics.conversation_count_24h = conversation_count
                self.metrics.database_size = db_metrics.get("size", "unknown")
                
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "connectivity_time_ms": round(connectivity_time, 2),
                    "database": "render-postgresql",
                    "conversation_count_24h": conversation_count,
                    "database_size": db_metrics.get("size", "unknown"),
                    "connection_pool": {
                        "min_size": self.pool._minsize,
                        "max_size": self.pool._maxsize,
                        "current_size": self.pool.get_size(),
                        "idle_size": self.pool.get_idle_size()
                    },
                    "metrics": {
                        "total_connections": self.metrics.total_connections_made,
                        "failed_connections": self.metrics.failed_connections,
                        "avg_query_time_ms": round(self.metrics.avg_query_time, 2)
                    },
                    "optimization": "render_postgresql_optimized"
                }
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"💥 PostgreSQL error during health check: {e}")
            return self._create_error_response(f"PostgreSQL error: {str(e)}", start_time)
            
        except Exception as e:
            logger.error(f"💥 Unexpected error during database health check: {e}")
            return self._create_error_response(f"Unexpected error: {str(e)}", start_time)
    
    async def _check_conversation_health(self, connection) -> int:
        """Check conversation table health and recent activity"""
        try:
            # Check if conversations table exists
            table_exists = await connection.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'conversations'
                )
            """)
            
            if not table_exists:
                logger.info("📋 Conversations table does not exist - likely file-based storage")
                return 0
            
            # Get recent conversation count
            count = await connection.fetchval("""
                SELECT COUNT(*) FROM conversations 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            
            return count or 0
            
        except Exception as e:
            logger.warning(f"⚠️ Could not check conversation health: {e}")
            return 0
    
    async def _get_database_metrics(self, connection) -> Dict[str, Any]:
        """Get database performance and size metrics"""
        try:
            # Database size
            db_size = await connection.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            
            # Connection count
            conn_count = await connection.fetchval(
                "SELECT count(*) FROM pg_stat_activity"
            )
            
            # Database version
            version = await connection.fetchval("SELECT version()")
            
            return {
                "size": db_size or "unknown",
                "active_connections": conn_count or 0,
                "version": version.split()[0:2] if version else ["unknown"]
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get database metrics: {e}")
            return {"size": "unknown", "active_connections": 0}
    
    def _create_error_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Create standardized error response"""
        response_time = (time.time() - start_time) * 1000
        self.metrics.failed_connections += 1
        
        return {
            "status": "error",
            "error": error_message,
            "response_time_ms": round(response_time, 2),
            "database": "render-postgresql",
            "fallback": "file_based_conversation_storage",
            "fallback_available": True,
            "retry_recommended": True
        }
    
    async def optimize_for_render(self) -> Dict[str, Any]:
        """Apply Render-specific database optimizations"""
        if not self.database_url or not self.pool:
            return {"status": "skipped", "reason": "No database connection available"}
        
        try:
            async with self.pool.acquire() as connection:
                optimizations_applied = []
                
                # Create optimized indexes for Line Lead usage patterns
                try:
                    await connection.execute("""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_conversations_recent ON conversations(created_at DESC) 
                        WHERE created_at > NOW() - INTERVAL '7 days'
                    """)
                    optimizations_applied.append("recent_conversations_index")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create recent conversations index: {e}")
                
                # Optimize for conversation retrieval by session
                try:
                    await connection.execute("""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_conversations_session ON conversations(session_id, created_at)
                    """)
                    optimizations_applied.append("session_conversations_index")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create session conversations index: {e}")
                
                # Check if we need to create the conversations table
                table_exists = await connection.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'conversations'
                    )
                """)
                
                if not table_exists:
                    try:
                        await connection.execute("""
                            CREATE TABLE IF NOT EXISTS conversations (
                                id SERIAL PRIMARY KEY,
                                session_id VARCHAR(255) NOT NULL,
                                message_text TEXT NOT NULL,
                                response_text TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        optimizations_applied.append("conversations_table_created")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not create conversations table: {e}")
                
                return {
                    "status": "completed",
                    "optimizations_applied": optimizations_applied,
                    "database": "render-postgresql",
                    "message": f"Applied {len(optimizations_applied)} optimizations"
                }
                
        except Exception as e:
            logger.error(f"💥 Failed to apply Render optimizations: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "render-postgresql"
            }
    
    async def get_conversation_storage_health(self) -> Dict[str, Any]:
        """Check conversation storage performance specifically"""
        if not self.database_url:
            # File-based storage health
            try:
                import os
                import json
                
                # Check if conversations file exists and is readable
                conversations_file = "../conversations.json"  # Adjust path as needed
                if os.path.exists(conversations_file):
                    with open(conversations_file, 'r') as f:
                        conversations = json.load(f)
                    
                    return {
                        "status": "healthy",
                        "storage_type": "file_based",
                        "conversation_count": len(conversations),
                        "file_size_kb": round(os.path.getsize(conversations_file) / 1024, 2),
                        "performance": "file_system_dependent"
                    }
                else:
                    return {
                        "status": "healthy",
                        "storage_type": "file_based",
                        "conversation_count": 0,
                        "message": "Conversations file will be created on first use"
                    }
                    
            except Exception as e:
                return {
                    "status": "error",
                    "storage_type": "file_based",
                    "error": str(e)
                }
        
        # Database storage health
        if not self.pool:
            await self.initialize_pool()
        
        try:
            start_time = time.time()
            async with self.pool.acquire() as connection:
                # Test conversation storage performance
                test_query_time = time.time()
                recent_count = await connection.fetchval("""
                    SELECT COUNT(*) FROM conversations 
                    WHERE created_at > NOW() - INTERVAL '1 hour'
                """)
                query_time = (time.time() - test_query_time) * 1000
                
                total_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "healthy",
                    "storage_type": "postgresql",
                    "conversation_count_1h": recent_count,
                    "query_performance_ms": round(query_time, 2),
                    "total_response_time_ms": round(total_time, 2),
                    "target_performance": "< 100ms for conversation queries"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "storage_type": "postgresql",
                "error": str(e),
                "fallback": "file_based_storage_available"
            }
    
    async def close(self):
        """Clean up database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("🗄️ Database connection pool closed")

# Global database health instance
render_db_health = RenderDatabaseHealth()