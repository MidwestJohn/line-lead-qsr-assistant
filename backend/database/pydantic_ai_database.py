#!/usr/bin/env python3
"""
PydanticAI Compatible Database - Phase 3
=======================================

Database implementation following official PydanticAI patterns from their
FastAPI chat app example. Uses proper message serialization and async patterns.

Based on: https://ai.pydantic.dev/examples/chat-app/

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import sqlite3
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Callable, TypeVar
from collections.abc import AsyncIterator

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from typing_extensions import LiteralString, ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec('P')
R = TypeVar('R')

@dataclass
class PydanticAIDatabase:
    """
    PydanticAI compatible database following official patterns.
    
    This implementation follows the exact patterns from the official
    PydanticAI FastAPI chat app example with QSR-specific enhancements.
    """
    
    con: sqlite3.Connection
    _loop: asyncio.AbstractEventLoop
    _executor: ThreadPoolExecutor

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, file: Path = None
    ) -> AsyncIterator['PydanticAIDatabase']:
        """Connect to database with proper async context management"""
        if file is None:
            # Use environment-specific database path
            import os
            environment = os.getenv("ENVIRONMENT", "development")
            if environment == "production":
                file = Path("/data/qsr_production.sqlite")
            else:
                file = Path("qsr_conversations.sqlite")
        
        logger.info(f"Connecting to PydanticAI database: {file}")
        
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        con = await loop.run_in_executor(executor, cls._connect, file)
        slf = cls(con, loop, executor)
        
        try:
            yield slf
        finally:
            await slf._asyncify(con.close)
            logger.info("PydanticAI database connection closed")

    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        """Create database connection and initialize tables"""
        # Ensure database directory exists
        file.parent.mkdir(parents=True, exist_ok=True)
        
        con = sqlite3.connect(str(file))
        cur = con.cursor()
        
        # Create conversations table (PydanticAI pattern)
        cur.execute(
            'CREATE TABLE IF NOT EXISTS conversations ('
            'id INTEGER PRIMARY KEY AUTOINCREMENT, '
            'conversation_id TEXT NOT NULL, '
            'message_list TEXT NOT NULL, '
            'timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, '
            'agent_id TEXT, '
            'response_time REAL'
            ');'
        )
        
        # Create indexes for performance
        cur.execute('CREATE INDEX IF NOT EXISTS idx_conversation_id ON conversations(conversation_id);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp);')
        
        # QSR-specific analytics table
        cur.execute(
            'CREATE TABLE IF NOT EXISTS qsr_analytics ('
            'id INTEGER PRIMARY KEY AUTOINCREMENT, '
            'conversation_id TEXT NOT NULL, '
            'agent_type TEXT, '
            'classification_confidence REAL, '
            'response_time REAL, '
            'timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, '
            'metadata TEXT'
            ');'
        )
        
        con.commit()
        logger.info("Database tables initialized successfully")
        return con

    async def add_messages(
        self, 
        conversation_id: str, 
        messages: bytes, 
        agent_id: str = None, 
        response_time: float = None
    ) -> bool:
        """
        Add messages to conversation history (PydanticAI pattern).
        
        Args:
            conversation_id: Conversation identifier
            messages: Serialized messages from result.new_messages_json()
            agent_id: Agent that generated the messages
            response_time: Response time in seconds
            
        Returns:
            True if successful
        """
        try:
            await self._asyncify(
                self._execute,
                'INSERT INTO conversations (conversation_id, message_list, agent_id, response_time) VALUES (?, ?, ?, ?);',
                conversation_id,
                messages,
                agent_id,
                response_time,
                commit=True,
            )
            logger.debug(f"Added messages to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add messages to conversation {conversation_id}: {e}")
            return False

    async def get_messages(self, conversation_id: str = None, limit: int = None) -> list[ModelMessage]:
        """
        Get conversation history (PydanticAI pattern).
        
        Args:
            conversation_id: Specific conversation ID, or None for all
            limit: Maximum number of message entries to return
            
        Returns:
            List of ModelMessage objects
        """
        try:
            if conversation_id:
                sql = 'SELECT message_list FROM conversations WHERE conversation_id = ? ORDER BY id'
                args = [conversation_id]
            else:
                sql = 'SELECT message_list FROM conversations ORDER BY id'
                args = []
            
            if limit:
                sql += ' LIMIT ?'
                args.append(limit)
            
            c = await self._asyncify(self._execute, sql, *args)
            rows = await self._asyncify(c.fetchall)
            
            messages: list[ModelMessage] = []
            for row in rows:
                # Use PydanticAI's official message deserialization
                batch_messages = ModelMessagesTypeAdapter.validate_json(row[0])
                messages.extend(batch_messages)
            
            logger.debug(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []

    async def save_qsr_analytics(
        self,
        conversation_id: str,
        agent_type: str,
        classification_confidence: float = None,
        response_time: float = None,
        metadata: dict = None
    ) -> bool:
        """Save QSR-specific analytics data"""
        try:
            import json
            metadata_json = json.dumps(metadata) if metadata else None
            
            await self._asyncify(
                self._execute,
                'INSERT INTO qsr_analytics (conversation_id, agent_type, classification_confidence, response_time, metadata) VALUES (?, ?, ?, ?, ?);',
                conversation_id,
                agent_type,
                classification_confidence,
                response_time,
                metadata_json,
                commit=True,
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to save QSR analytics: {e}")
            return False

    async def get_conversation_stats(self, conversation_id: str) -> dict:
        """Get conversation statistics"""
        try:
            c = await self._asyncify(
                self._execute,
                'SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM conversations WHERE conversation_id = ?',
                conversation_id
            )
            row = await self._asyncify(c.fetchone)
            
            if row:
                return {
                    "message_count": row[0],
                    "first_message": row[1],
                    "last_message": row[2]
                }
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {}

    async def health_check(self) -> dict:
        """Perform database health check"""
        try:
            # Test basic query
            c = await self._asyncify(
                self._execute,
                'SELECT COUNT(*) FROM conversations'
            )
            row = await self._asyncify(c.fetchone)
            total_conversations = row[0] if row else 0
            
            return {
                "status": "healthy",
                "total_conversations": total_conversations,
                "database_file": str(self.con.execute("PRAGMA database_list").fetchone()[2])
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _execute(
        self, sql: LiteralString, *args: Any, commit: bool = False
    ) -> sqlite3.Cursor:
        """Execute SQL query synchronously"""
        cur = self.con.cursor()
        cur.execute(sql, args)
        if commit:
            self.con.commit()
        return cur

    async def _asyncify(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        """Convert synchronous function to async using thread pool"""
        return await self._loop.run_in_executor(  # type: ignore
            self._executor,
            partial(func, **kwargs),
            *args,  # type: ignore
        )


# Factory function following PydanticAI patterns
async def create_pydantic_ai_database(file: Path = None) -> PydanticAIDatabase:
    """
    Create PydanticAI database connection.
    
    Args:
        file: Database file path
        
    Returns:
        Async context manager for database
    """
    # Note: This returns the context manager, not the database directly
    # Use like: async with create_pydantic_ai_database() as db:
    return PydanticAIDatabase.connect(file)


# Global database instance for production use
_global_db_context = None

async def get_global_database() -> PydanticAIDatabase:
    """Get the global database instance (for dependency injection)"""
    global _global_db_context
    if _global_db_context is None:
        # This is for production apps with lifespan management
        raise RuntimeError("Global database not initialized. Use lifespan context manager.")
    return _global_db_context


# Export key functions
__all__ = [
    "PydanticAIDatabase",
    "create_pydantic_ai_database",
    "get_global_database"
]