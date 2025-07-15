#!/usr/bin/env python3
"""
QSR Database - Phase 1 Implementation
=====================================

SQLite database implementation following PydanticAI patterns.
Replaces JSON file storage with proper async database operations.

Features:
- Async SQLite operations with thread pool
- Conversation and message persistence
- QSR-specific analytics tables
- Performance monitoring
- Data integrity and validation

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import sqlite3
import logging
from collections.abc import AsyncIterator
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from typing_extensions import LiteralString, ParamSpec

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type definitions
P = ParamSpec('P')
R = TypeVar('R')

# Database file location
DEFAULT_DB_FILE = Path(__file__).parent / '.qsr_conversations.sqlite'

@dataclass
class ConversationMetadata:
    """Metadata for conversations"""
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    total_messages: int
    equipment_mentioned: List[str]
    safety_incidents: int
    user_location: Optional[str] = None
    session_duration: Optional[int] = None  # in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'conversation_id': self.conversation_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'total_messages': self.total_messages,
            'equipment_mentioned': json.dumps(self.equipment_mentioned),
            'safety_incidents': self.safety_incidents,
            'user_location': self.user_location,
            'session_duration': self.session_duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMetadata':
        return cls(
            conversation_id=data['conversation_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            total_messages=data['total_messages'],
            equipment_mentioned=json.loads(data['equipment_mentioned']),
            safety_incidents=data['safety_incidents'],
            user_location=data.get('user_location'),
            session_duration=data.get('session_duration')
        )

@dataclass
class QSRDatabase:
    """
    QSR conversation database with SQLite storage following PydanticAI patterns.
    
    Provides async operations for conversation and message management with
    QSR-specific analytics and monitoring.
    """
    
    con: sqlite3.Connection
    _loop: asyncio.AbstractEventLoop
    _executor: ThreadPoolExecutor
    
    @classmethod
    @asynccontextmanager
    async def connect(
        cls, 
        file: Path = DEFAULT_DB_FILE,
        max_workers: int = 1
    ) -> AsyncIterator['QSRDatabase']:
        """
        Create database connection with async context manager.
        
        Args:
            file: Database file path
            max_workers: Thread pool size for async operations
            
        Yields:
            QSRDatabase instance
        """
        
        logger.info(f"Connecting to QSR database: {file}")
        
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=max_workers)
        
        try:
            con = await loop.run_in_executor(executor, cls._connect, file)
            db = cls(con, loop, executor)
            
            # Perform initial health check
            await db._health_check()
            
            logger.info("QSR database connection established successfully")
            yield db
            
        except Exception as e:
            logger.error(f"Failed to connect to QSR database: {e}")
            raise
        finally:
            if 'con' in locals():
                await db._asyncify(con.close)
            executor.shutdown(wait=True)
            logger.info("QSR database connection closed")
    
    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        """
        Create SQLite connection and initialize schema.
        
        Args:
            file: Database file path
            
        Returns:
            SQLite connection
        """
        
        # Create database directory if it doesn't exist
        file.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        con = sqlite3.connect(str(file))
        con.row_factory = sqlite3.Row  # Enable column access by name
        
        # Enable foreign key constraints
        con.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        cursor = con.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                equipment_mentioned TEXT DEFAULT '[]',
                safety_incidents INTEGER DEFAULT 0,
                user_location TEXT,
                session_duration INTEGER,
                metadata TEXT DEFAULT '{}'
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                message_data TEXT NOT NULL,
                message_type TEXT DEFAULT 'chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time REAL,
                agent_id TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        
        # Equipment references table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                equipment_name TEXT NOT NULL,
                manual_reference TEXT,
                mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        
        # Safety incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS safety_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                incident_type TEXT NOT NULL,
                severity_level TEXT DEFAULT 'low',
                response_provided TEXT,
                escalation_required BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        
        # Analytics table for performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_data TEXT DEFAULT '{}',
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipment_conversation ON equipment_references(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_safety_conversation ON safety_incidents(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_conversation ON analytics(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(metric_type)')
        
        con.commit()
        return con
    
    async def add_messages(self, conversation_id: str, messages: bytes, agent_id: str = None, response_time: float = None) -> bool:
        """
        Add messages to conversation history.
        
        Args:
            conversation_id: Conversation identifier
            messages: Serialized messages from PydanticAI
            agent_id: Agent that generated the messages
            response_time: Response time in seconds
            
        Returns:
            True if successful
        """
        
        try:
            # Ensure conversation exists
            await self._ensure_conversation_exists(conversation_id)
            
            # Add messages
            await self._asyncify(
                self._execute,
                'INSERT INTO messages (conversation_id, message_data, agent_id, response_time) VALUES (?, ?, ?, ?)',
                conversation_id,
                messages,
                agent_id,
                response_time,
                commit=True
            )
            
            # Update conversation metadata
            await self._update_conversation_metadata(conversation_id)
            
            logger.debug(f"Added messages to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add messages to conversation {conversation_id}: {e}")
            return False
    
    async def get_messages(self, conversation_id: str, limit: int = None) -> List[ModelMessage]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of PydanticAI ModelMessage objects
        """
        
        try:
            # Build query
            query = 'SELECT message_data FROM messages WHERE conversation_id = ? ORDER BY id'
            args = [conversation_id]
            
            if limit:
                query += ' LIMIT ?'
                args.append(limit)
            
            # Execute query
            cursor = await self._asyncify(self._execute, query, *args)
            rows = await self._asyncify(cursor.fetchall)
            
            # Deserialize messages
            messages: List[ModelMessage] = []
            for row in rows:
                try:
                    message_data = row['message_data']
                    messages.extend(ModelMessagesTypeAdapter.validate_json(message_data))
                except Exception as e:
                    logger.warning(f"Failed to deserialize message in conversation {conversation_id}: {e}")
            
            logger.debug(f"Retrieved {len(messages)} messages from conversation {conversation_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages from conversation {conversation_id}: {e}")
            return []
    
    async def get_conversation_metadata(self, conversation_id: str) -> Optional[ConversationMetadata]:
        """
        Get conversation metadata.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            ConversationMetadata or None if not found
        """
        
        try:
            cursor = await self._asyncify(
                self._execute,
                'SELECT * FROM conversations WHERE id = ?',
                conversation_id
            )
            row = await self._asyncify(cursor.fetchone)
            
            if row:
                return ConversationMetadata.from_dict(dict(row))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get metadata for conversation {conversation_id}: {e}")
            return None
    
    async def add_equipment_reference(self, conversation_id: str, equipment_name: str, manual_reference: str = None, context: str = None) -> bool:
        """
        Add equipment reference to conversation.
        
        Args:
            conversation_id: Conversation identifier
            equipment_name: Name of the equipment
            manual_reference: Manual page or section reference
            context: Additional context
            
        Returns:
            True if successful
        """
        
        try:
            await self._asyncify(
                self._execute,
                'INSERT INTO equipment_references (conversation_id, equipment_name, manual_reference, context) VALUES (?, ?, ?, ?)',
                conversation_id,
                equipment_name,
                manual_reference,
                context,
                commit=True
            )
            
            logger.debug(f"Added equipment reference {equipment_name} to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add equipment reference to conversation {conversation_id}: {e}")
            return False
    
    async def add_safety_incident(self, conversation_id: str, incident_type: str, severity_level: str = 'low', 
                                 response_provided: str = None, escalation_required: bool = False) -> bool:
        """
        Add safety incident to conversation.
        
        Args:
            conversation_id: Conversation identifier
            incident_type: Type of safety incident
            severity_level: Severity level (low, medium, high, critical)
            response_provided: Response provided to user
            escalation_required: Whether escalation is required
            
        Returns:
            True if successful
        """
        
        try:
            await self._asyncify(
                self._execute,
                'INSERT INTO safety_incidents (conversation_id, incident_type, severity_level, response_provided, escalation_required) VALUES (?, ?, ?, ?, ?)',
                conversation_id,
                incident_type,
                severity_level,
                response_provided,
                escalation_required,
                commit=True
            )
            
            logger.info(f"Added safety incident {incident_type} to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add safety incident to conversation {conversation_id}: {e}")
            return False
    
    async def add_analytics_metric(self, conversation_id: str, metric_type: str, metric_value: float, metric_data: Dict[str, Any] = None) -> bool:
        """
        Add analytics metric.
        
        Args:
            conversation_id: Conversation identifier
            metric_type: Type of metric (response_time, confidence, etc.)
            metric_value: Metric value
            metric_data: Additional metric data
            
        Returns:
            True if successful
        """
        
        try:
            await self._asyncify(
                self._execute,
                'INSERT INTO analytics (conversation_id, metric_type, metric_value, metric_data) VALUES (?, ?, ?, ?)',
                conversation_id,
                metric_type,
                metric_value,
                json.dumps(metric_data or {}),
                commit=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add analytics metric to conversation {conversation_id}: {e}")
            return False
    
    async def get_conversation_analytics(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get analytics for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Dictionary with analytics data
        """
        
        try:
            # Get equipment references
            equipment_cursor = await self._asyncify(
                self._execute,
                'SELECT equipment_name, COUNT(*) as count FROM equipment_references WHERE conversation_id = ? GROUP BY equipment_name',
                conversation_id
            )
            equipment_rows = await self._asyncify(equipment_cursor.fetchall)
            
            # Get safety incidents
            safety_cursor = await self._asyncify(
                self._execute,
                'SELECT incident_type, severity_level, COUNT(*) as count FROM safety_incidents WHERE conversation_id = ? GROUP BY incident_type, severity_level',
                conversation_id
            )
            safety_rows = await self._asyncify(safety_cursor.fetchall)
            
            # Get performance metrics
            metrics_cursor = await self._asyncify(
                self._execute,
                'SELECT metric_type, AVG(metric_value) as avg_value, COUNT(*) as count FROM analytics WHERE conversation_id = ? GROUP BY metric_type',
                conversation_id
            )
            metrics_rows = await self._asyncify(metrics_cursor.fetchall)
            
            # Get message count
            message_cursor = await self._asyncify(
                self._execute,
                'SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?',
                conversation_id
            )
            message_row = await self._asyncify(message_cursor.fetchone)
            
            return {
                'conversation_id': conversation_id,
                'message_count': message_row['count'] if message_row else 0,
                'equipment_references': [
                    {'equipment': row['equipment_name'], 'count': row['count']} 
                    for row in equipment_rows
                ],
                'safety_incidents': [
                    {
                        'incident_type': row['incident_type'], 
                        'severity_level': row['severity_level'], 
                        'count': row['count']
                    } 
                    for row in safety_rows
                ],
                'performance_metrics': [
                    {
                        'metric_type': row['metric_type'], 
                        'avg_value': row['avg_value'], 
                        'count': row['count']
                    } 
                    for row in metrics_rows
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics for conversation {conversation_id}: {e}")
            return {}
    
    async def get_system_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get system-wide analytics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with system analytics
        """
        
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            # Get conversation count
            conv_cursor = await self._asyncify(
                self._execute,
                'SELECT COUNT(*) as count FROM conversations WHERE created_at >= ?',
                since_date
            )
            conv_row = await self._asyncify(conv_cursor.fetchone)
            
            # Get message count
            msg_cursor = await self._asyncify(
                self._execute,
                'SELECT COUNT(*) as count FROM messages WHERE created_at >= ?',
                since_date
            )
            msg_row = await self._asyncify(msg_cursor.fetchone)
            
            # Get top equipment
            equipment_cursor = await self._asyncify(
                self._execute,
                'SELECT equipment_name, COUNT(*) as count FROM equipment_references WHERE mentioned_at >= ? GROUP BY equipment_name ORDER BY count DESC LIMIT 10',
                since_date
            )
            equipment_rows = await self._asyncify(equipment_cursor.fetchall)
            
            # Get safety incidents
            safety_cursor = await self._asyncify(
                self._execute,
                'SELECT incident_type, severity_level, COUNT(*) as count FROM safety_incidents WHERE created_at >= ? GROUP BY incident_type, severity_level ORDER BY count DESC',
                since_date
            )
            safety_rows = await self._asyncify(safety_cursor.fetchall)
            
            # Get performance metrics
            perf_cursor = await self._asyncify(
                self._execute,
                'SELECT metric_type, AVG(metric_value) as avg_value, MIN(metric_value) as min_value, MAX(metric_value) as max_value, COUNT(*) as count FROM analytics WHERE recorded_at >= ? GROUP BY metric_type',
                since_date
            )
            perf_rows = await self._asyncify(perf_cursor.fetchall)
            
            return {
                'period_days': days,
                'since_date': since_date.isoformat(),
                'conversation_count': conv_row['count'] if conv_row else 0,
                'message_count': msg_row['count'] if msg_row else 0,
                'top_equipment': [
                    {'equipment': row['equipment_name'], 'count': row['count']} 
                    for row in equipment_rows
                ],
                'safety_incidents': [
                    {
                        'incident_type': row['incident_type'], 
                        'severity_level': row['severity_level'], 
                        'count': row['count']
                    } 
                    for row in safety_rows
                ],
                'performance_metrics': [
                    {
                        'metric_type': row['metric_type'], 
                        'avg_value': row['avg_value'],
                        'min_value': row['min_value'],
                        'max_value': row['max_value'],
                        'count': row['count']
                    } 
                    for row in perf_rows
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get system analytics: {e}")
            return {}
    
    async def cleanup_old_conversations(self, days: int = 30) -> int:
        """
        Clean up old conversations.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of conversations deleted
        """
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get conversations to delete
            cursor = await self._asyncify(
                self._execute,
                'SELECT id FROM conversations WHERE created_at < ?',
                cutoff_date
            )
            rows = await self._asyncify(cursor.fetchall)
            
            if not rows:
                return 0
            
            # Delete conversations (cascading will handle related records)
            await self._asyncify(
                self._execute,
                'DELETE FROM conversations WHERE created_at < ?',
                cutoff_date,
                commit=True
            )
            
            deleted_count = len(rows)
            logger.info(f"Cleaned up {deleted_count} old conversations")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {e}")
            return 0
    
    async def _ensure_conversation_exists(self, conversation_id: str) -> None:
        """Ensure conversation exists in database"""
        
        await self._asyncify(
            self._execute,
            'INSERT OR IGNORE INTO conversations (id) VALUES (?)',
            conversation_id,
            commit=True
        )
    
    async def _update_conversation_metadata(self, conversation_id: str) -> None:
        """Update conversation metadata after adding messages"""
        
        # Get current message count
        cursor = await self._asyncify(
            self._execute,
            'SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?',
            conversation_id
        )
        row = await self._asyncify(cursor.fetchone)
        message_count = row['count'] if row else 0
        
        # Update conversation
        await self._asyncify(
            self._execute,
            'UPDATE conversations SET updated_at = CURRENT_TIMESTAMP, total_messages = ? WHERE id = ?',
            message_count,
            conversation_id,
            commit=True
        )
    
    async def _health_check(self) -> None:
        """Perform database health check"""
        
        try:
            # Test basic query
            cursor = await self._asyncify(self._execute, 'SELECT 1')
            await self._asyncify(cursor.fetchone)
            
            # Check table existence
            cursor = await self._asyncify(
                self._execute,
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = await self._asyncify(cursor.fetchall)
            
            expected_tables = {'conversations', 'messages', 'equipment_references', 'safety_incidents', 'analytics'}
            actual_tables = {row['name'] for row in tables}
            
            if not expected_tables.issubset(actual_tables):
                missing_tables = expected_tables - actual_tables
                raise Exception(f"Missing database tables: {missing_tables}")
            
            logger.info("Database health check passed")
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise
    
    def _execute(self, sql: LiteralString, *args: Any, commit: bool = False) -> sqlite3.Cursor:
        """Execute SQL query"""
        cursor = self.con.cursor()
        cursor.execute(sql, args)
        if commit:
            self.con.commit()
        return cursor
    
    async def _asyncify(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Run function in thread pool executor"""
        return await self._loop.run_in_executor(
            self._executor,
            partial(func, **kwargs),
            *args,
        )

# Factory function for creating database connections
async def create_qsr_database(file: Path = None) -> QSRDatabase:
    """
    Factory function to create QSR database connection.
    
    Args:
        file: Database file path
        
    Returns:
        QSRDatabase instance
    """
    
    file = file or DEFAULT_DB_FILE
    
    async with QSRDatabase.connect(file) as db:
        return db

# Test function
async def test_database():
    """Test database functionality"""
    
    logger.info("Testing QSR Database...")
    
    async with QSRDatabase.connect() as db:
        # Test conversation creation
        conversation_id = "test_conversation"
        
        # Add test messages
        test_messages = b'[{"role": "user", "content": "Test message"}]'
        await db.add_messages(conversation_id, test_messages, "test_agent", 1.5)
        
        # Get messages
        messages = await db.get_messages(conversation_id)
        print(f"Retrieved {len(messages)} messages")
        
        # Add equipment reference
        await db.add_equipment_reference(conversation_id, "Taylor Ice Cream Machine", "Manual Page 42")
        
        # Add safety incident
        await db.add_safety_incident(conversation_id, "burn_incident", "medium", "Applied first aid", True)
        
        # Add analytics
        await db.add_analytics_metric(conversation_id, "response_time", 1.5)
        await db.add_analytics_metric(conversation_id, "confidence", 0.85)
        
        # Get analytics
        analytics = await db.get_conversation_analytics(conversation_id)
        print(f"Analytics: {analytics}")
        
        # Get system analytics
        system_analytics = await db.get_system_analytics(7)
        print(f"System Analytics: {system_analytics}")
    
    logger.info("Database test completed successfully")

if __name__ == "__main__":
    asyncio.run(test_database())