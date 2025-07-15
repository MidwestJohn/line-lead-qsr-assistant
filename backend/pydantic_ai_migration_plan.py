#!/usr/bin/env python3
"""
PydanticAI Migration Plan
========================

Demonstrates how to migrate the current FastAPI implementation to follow
official PydanticAI patterns while maintaining QSR-specific functionality.

This shows the proper way to implement:
- PydanticAI Agent integration
- Message history management
- Streaming responses
- Database integration
- QSR-specific features

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import sqlite3
from collections.abc import AsyncIterator
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Annotated, Any, Callable, Dict, List, Optional, Literal, TypeVar

import fastapi
from fastapi import Depends, Request, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing_extensions import LiteralString, ParamSpec, TypedDict

# PydanticAI imports - following official patterns
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

# Existing QSR imports
from services.ragie_service_clean import clean_ragie_service
from document_search import search_engine

# Configuration
THIS_DIR = Path(__file__).parent
P = ParamSpec('P')
R = TypeVar('R')

# QSR-specific system prompt
QSR_SYSTEM_PROMPT = """You are an expert QSR (Quick Service Restaurant) assistant with extensive knowledge of:

1. Equipment operation and troubleshooting (Taylor, Vulcan, Hobart, Traulsen, etc.)
2. Food safety protocols and procedures
3. Opening and closing procedures
4. Staff training and management
5. Customer service best practices
6. Emergency response procedures

You have access to detailed equipment manuals, procedural documents, and safety protocols.
Always provide accurate, actionable advice with proper citations when referencing specific documents.
For safety-critical situations, emphasize immediate actions and when to seek additional help.

When providing equipment troubleshooting:
- Reference specific manual sections
- Provide step-by-step instructions
- Include safety warnings
- Suggest when to call for professional service

For procedural questions:
- Break down complex processes into clear steps
- Reference relevant training materials
- Emphasize compliance requirements
- Provide context for why procedures matter
"""

# PydanticAI Agent setup - following official patterns
qsr_agent = Agent(
    'openai:gpt-4o',
    system_prompt=QSR_SYSTEM_PROMPT
)

# Message format matching PydanticAI patterns
class ChatMessage(TypedDict):
    """Format of messages sent to/from the browser - matches PydanticAI patterns"""
    role: Literal['user', 'model']
    timestamp: str
    content: str

class QSRChatMessage(BaseModel):
    """Enhanced chat message model for QSR features"""
    message: str
    conversation_id: Optional[str] = "default"
    include_citations: bool = True
    search_documents: bool = True

class QSRChatResponse(BaseModel):
    """Enhanced chat response with QSR-specific features"""
    response: str
    timestamp: str
    conversation_id: str
    
    # QSR-specific fields
    visual_citations: Optional[List[Dict]] = Field(default=None)
    equipment_references: Optional[List[Dict]] = Field(default=None)
    safety_alerts: Optional[List[str]] = Field(default=None)
    procedural_steps: Optional[List[str]] = Field(default=None)
    
    # PydanticAI compatibility
    role: Literal['model'] = 'model'
    
    class Config:
        exclude_none = False

def to_chat_message(m: ModelMessage) -> ChatMessage:
    """Convert PydanticAI message to chat format - following official patterns"""
    first_part = m.parts[0]
    if isinstance(m, ModelRequest):
        if isinstance(first_part, UserPromptPart):
            assert isinstance(first_part.content, str)
            return {
                'role': 'user',
                'timestamp': first_part.timestamp.isoformat(),
                'content': first_part.content,
            }
    elif isinstance(m, ModelResponse):
        if isinstance(first_part, TextPart):
            return {
                'role': 'model',
                'timestamp': m.timestamp.isoformat(),
                'content': first_part.content,
            }
    raise UnexpectedModelBehavior(f'Unexpected message type for QSR chat app: {m}')

@dataclass
class QSRDatabase:
    """
    QSR conversation database with SQLite storage - following official patterns
    but enhanced for QSR-specific features
    """
    con: sqlite3.Connection
    _loop: asyncio.AbstractEventLoop
    _executor: ThreadPoolExecutor

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, file: Path = THIS_DIR / '.qsr_conversations.sqlite'
    ) -> AsyncIterator['QSRDatabase']:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        con = await loop.run_in_executor(executor, cls._connect, file)
        slf = cls(con, loop, executor)
        try:
            yield slf
        finally:
            await slf._asyncify(con.close)

    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        con = sqlite3.connect(str(file))
        cur = con.cursor()
        
        # Create tables for conversations and messages
        cur.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                message_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
        ''')
        
        # QSR-specific tables
        cur.execute('''
            CREATE TABLE IF NOT EXISTS equipment_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                equipment_name TEXT,
                manual_reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS safety_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                incident_type TEXT,
                response_provided TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
        ''')
        
        con.commit()
        return con

    async def add_messages(self, conversation_id: str, messages: bytes):
        """Add messages to conversation history"""
        await self._asyncify(
            self._execute,
            'INSERT OR IGNORE INTO conversations (id) VALUES (?);',
            conversation_id,
            commit=True,
        )
        
        await self._asyncify(
            self._execute,
            'INSERT INTO messages (conversation_id, message_data) VALUES (?, ?);',
            conversation_id,
            messages,
            commit=True,
        )

    async def get_messages(self, conversation_id: str) -> List[ModelMessage]:
        """Get conversation history"""
        c = await self._asyncify(
            self._execute,
            'SELECT message_data FROM messages WHERE conversation_id = ? ORDER BY id',
            conversation_id
        )
        rows = await self._asyncify(c.fetchall)
        messages: List[ModelMessage] = []
        for row in rows:
            messages.extend(ModelMessagesTypeAdapter.validate_json(row[0]))
        return messages

    async def add_equipment_reference(self, conversation_id: str, equipment_name: str, manual_reference: str):
        """Track equipment references for analytics"""
        await self._asyncify(
            self._execute,
            'INSERT INTO equipment_references (conversation_id, equipment_name, manual_reference) VALUES (?, ?, ?);',
            conversation_id,
            equipment_name,
            manual_reference,
            commit=True,
        )

    async def add_safety_incident(self, conversation_id: str, incident_type: str, response_provided: str):
        """Track safety incidents for compliance"""
        await self._asyncify(
            self._execute,
            'INSERT INTO safety_incidents (conversation_id, incident_type, response_provided) VALUES (?, ?, ?);',
            conversation_id,
            incident_type,
            response_provided,
            commit=True,
        )

    def _execute(
        self, sql: LiteralString, *args: Any, commit: bool = False
    ) -> sqlite3.Cursor:
        cur = self.con.cursor()
        cur.execute(sql, args)
        if commit:
            self.con.commit()
        return cur

    async def _asyncify(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        return await self._loop.run_in_executor(
            self._executor,
            partial(func, **kwargs),
            *args,
        )

class QSRDocumentSearcher:
    """Enhanced document search with Ragie integration"""
    
    def __init__(self):
        self.ragie_service = clean_ragie_service
        self.local_search = search_engine
    
    async def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Search documents with Ragie fallback to local search"""
        documents = []
        
        # Try Ragie first
        if self.ragie_service.is_available():
            try:
                ragie_results = await self.ragie_service.search(query, limit=limit)
                for result in ragie_results:
                    documents.append({
                        'content': result.text,
                        'score': result.score,
                        'source': result.metadata.get('original_filename', 'Unknown'),
                        'document_id': result.document_id,
                        'search_method': 'ragie'
                    })
            except Exception as e:
                print(f"Ragie search failed: {e}")
        
        # Fallback to local search if needed
        if not documents:
            try:
                local_results = self.local_search.search(query, top_k=limit)
                for result in local_results:
                    documents.append({
                        'content': result.get('text', ''),
                        'score': result.get('score', 0.0),
                        'source': result.get('filename', 'Unknown'),
                        'document_id': result.get('doc_id', 'unknown'),
                        'search_method': 'local'
                    })
            except Exception as e:
                print(f"Local search failed: {e}")
        
        return documents

class QSRResponseProcessor:
    """Process responses for QSR-specific features"""
    
    @staticmethod
    def extract_visual_citations(response: str, documents: List[Dict]) -> List[Dict]:
        """Extract visual citations from response"""
        citations = []
        for doc in documents:
            if doc['source'].lower() in response.lower():
                citations.append({
                    'source': doc['source'],
                    'document_id': doc['document_id'],
                    'relevance_score': doc['score']
                })
        return citations
    
    @staticmethod
    def extract_equipment_references(response: str) -> List[Dict]:
        """Extract equipment references from response"""
        equipment_brands = ['taylor', 'vulcan', 'hobart', 'traulsen', 'rational', 'cleveland']
        references = []
        
        for brand in equipment_brands:
            if brand.lower() in response.lower():
                references.append({
                    'equipment_brand': brand.title(),
                    'mentioned_in_response': True
                })
        
        return references
    
    @staticmethod
    def extract_safety_alerts(response: str) -> List[str]:
        """Extract safety alerts from response"""
        safety_keywords = ['danger', 'warning', 'caution', 'emergency', 'immediately', 'stop']
        alerts = []
        
        sentences = response.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in safety_keywords):
                alerts.append(sentence.strip())
        
        return alerts
    
    @staticmethod
    def extract_procedural_steps(response: str) -> List[str]:
        """Extract procedural steps from response"""
        steps = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered steps or bullet points
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('•', '-', '*')) or
                line.startswith(('Step', 'First', 'Then', 'Next', 'Finally'))):
                steps.append(line)
        
        return steps

# FastAPI application with PydanticAI integration
@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    async with QSRDatabase.connect() as db:
        yield {'db': db}

app = fastapi.FastAPI(lifespan=lifespan)

async def get_db(request: Request) -> QSRDatabase:
    return request.state.db

@app.get('/chat/{conversation_id}')
async def get_chat_history(
    conversation_id: str,
    database: QSRDatabase = Depends(get_db)
) -> JSONResponse:
    """Get conversation history - following PydanticAI patterns"""
    messages = await database.get_messages(conversation_id)
    chat_messages = [to_chat_message(m) for m in messages]
    return JSONResponse(content=chat_messages)

@app.post('/chat/')
async def post_chat(
    request: QSRChatMessage,
    database: QSRDatabase = Depends(get_db)
) -> StreamingResponse:
    """
    QSR Chat endpoint with PydanticAI integration and streaming
    Following official patterns but enhanced for QSR features
    """
    
    # Initialize services
    doc_searcher = QSRDocumentSearcher()
    response_processor = QSRResponseProcessor()
    
    async def stream_messages():
        """Stream chat messages following PydanticAI patterns"""
        
        # Stream user message immediately
        user_message = {
            'role': 'user',
            'timestamp': datetime.now(tz=timezone.utc).isoformat(),
            'content': request.message,
        }
        yield json.dumps(user_message).encode('utf-8') + b'\n'
        
        # Get conversation history
        messages = await database.get_messages(request.conversation_id)
        
        # Search for relevant documents if requested
        relevant_docs = []
        if request.search_documents:
            relevant_docs = await doc_searcher.search_documents(request.message)
        
        # Create context for the agent
        context = {
            'documents': relevant_docs,
            'conversation_id': request.conversation_id,
            'include_citations': request.include_citations
        }
        
        # Enhanced prompt with document context
        enhanced_prompt = request.message
        if relevant_docs:
            doc_context = "\n\n".join([
                f"Document: {doc['source']}\nContent: {doc['content'][:500]}..."
                for doc in relevant_docs[:3]
            ])
            enhanced_prompt = f"{request.message}\n\nRelevant Documents:\n{doc_context}"
        
        # Run agent with streaming - following PydanticAI patterns
        complete_response = ""
        async with qsr_agent.run_stream(enhanced_prompt, message_history=messages) as result:
            async for text in result.stream(debounce_by=0.01):
                complete_response += text
                # Stream each chunk as it comes
                m = ModelResponse(parts=[TextPart(text)], timestamp=result.timestamp())
                yield json.dumps(to_chat_message(m)).encode('utf-8') + b'\n'
        
        # Process response for QSR features
        visual_citations = response_processor.extract_visual_citations(complete_response, relevant_docs)
        equipment_refs = response_processor.extract_equipment_references(complete_response)
        safety_alerts = response_processor.extract_safety_alerts(complete_response)
        procedural_steps = response_processor.extract_procedural_steps(complete_response)
        
        # Send final metadata
        metadata = {
            'role': 'metadata',
            'timestamp': datetime.now(tz=timezone.utc).isoformat(),
            'content': json.dumps({
                'visual_citations': visual_citations,
                'equipment_references': equipment_refs,
                'safety_alerts': safety_alerts,
                'procedural_steps': procedural_steps
            })
        }
        yield json.dumps(metadata).encode('utf-8') + b'\n'
        
        # Save conversation history
        await database.add_messages(request.conversation_id, result.new_messages_json())
        
        # Track QSR-specific data
        for ref in equipment_refs:
            await database.add_equipment_reference(
                request.conversation_id,
                ref['equipment_brand'],
                'Response mention'
            )
        
        if safety_alerts:
            await database.add_safety_incident(
                request.conversation_id,
                'Safety guidance provided',
                complete_response[:500]
            )
    
    return StreamingResponse(stream_messages(), media_type='text/plain')

@app.post('/chat/standard')
async def post_chat_standard(
    request: QSRChatMessage,
    database: QSRDatabase = Depends(get_db)
) -> QSRChatResponse:
    """
    Standard (non-streaming) chat endpoint with QSR features
    Following PydanticAI patterns
    """
    
    # Initialize services
    doc_searcher = QSRDocumentSearcher()
    response_processor = QSRResponseProcessor()
    
    # Get conversation history
    messages = await database.get_messages(request.conversation_id)
    
    # Search for relevant documents
    relevant_docs = []
    if request.search_documents:
        relevant_docs = await doc_searcher.search_documents(request.message)
    
    # Enhanced prompt with document context
    enhanced_prompt = request.message
    if relevant_docs:
        doc_context = "\n\n".join([
            f"Document: {doc['source']}\nContent: {doc['content'][:500]}..."
            for doc in relevant_docs[:3]
        ])
        enhanced_prompt = f"{request.message}\n\nRelevant Documents:\n{doc_context}"
    
    # Run agent - following PydanticAI patterns
    result = await qsr_agent.run(enhanced_prompt, message_history=messages)
    
    # Process response for QSR features
    visual_citations = response_processor.extract_visual_citations(result.data, relevant_docs)
    equipment_refs = response_processor.extract_equipment_references(result.data)
    safety_alerts = response_processor.extract_safety_alerts(result.data)
    procedural_steps = response_processor.extract_procedural_steps(result.data)
    
    # Save conversation history
    await database.add_messages(request.conversation_id, result.new_messages_json())
    
    # Track QSR-specific data
    for ref in equipment_refs:
        await database.add_equipment_reference(
            request.conversation_id,
            ref['equipment_brand'],
            'Response mention'
        )
    
    if safety_alerts:
        await database.add_safety_incident(
            request.conversation_id,
            'Safety guidance provided',
            result.data[:500]
        )
    
    return QSRChatResponse(
        response=result.data,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        conversation_id=request.conversation_id,
        visual_citations=visual_citations,
        equipment_references=equipment_refs,
        safety_alerts=safety_alerts,
        procedural_steps=procedural_steps
    )

@app.get('/analytics/{conversation_id}')
async def get_conversation_analytics(
    conversation_id: str,
    database: QSRDatabase = Depends(get_db)
) -> JSONResponse:
    """Get analytics for a conversation"""
    
    # Get equipment references
    equipment_cursor = await database._asyncify(
        database._execute,
        'SELECT equipment_name, COUNT(*) as count FROM equipment_references WHERE conversation_id = ? GROUP BY equipment_name',
        conversation_id
    )
    equipment_data = await database._asyncify(equipment_cursor.fetchall)
    
    # Get safety incidents
    safety_cursor = await database._asyncify(
        database._execute,
        'SELECT incident_type, COUNT(*) as count FROM safety_incidents WHERE conversation_id = ? GROUP BY incident_type',
        conversation_id
    )
    safety_data = await database._asyncify(safety_cursor.fetchall)
    
    return JSONResponse(content={
        'conversation_id': conversation_id,
        'equipment_references': [{'equipment': row[0], 'count': row[1]} for row in equipment_data],
        'safety_incidents': [{'incident_type': row[0], 'count': row[1]} for row in safety_data]
    })

@app.get('/health')
async def health_check() -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse(content={
        'status': 'healthy',
        'timestamp': datetime.now(tz=timezone.utc).isoformat(),
        'agent_model': str(qsr_agent.model),
        'ragie_available': clean_ragie_service.is_available()
    })

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'pydantic_ai_migration_plan:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )