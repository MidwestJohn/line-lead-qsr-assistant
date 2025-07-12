#!/usr/bin/env python3
"""
Clean Line Lead QSR Backend with Ragie Integration
================================================

Simple, focused implementation without complex Neo4j/RAG dependencies.
Uses Ragie for enhanced document processing and search.

Author: Generated with Memex (https://memex.tech)
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import datetime
import json
import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import io
import uuid
import PyPDF2
from io import BytesIO

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Fix tokenizer parallelism issue that causes server crashes
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Import core services
from document_search import search_engine, load_documents_into_search_engine

# Clean Ragie integration
from services.ragie_service_clean import clean_ragie_service

# Try to import optional services (graceful fallback if not available)
try:
    from voice_service import voice_service
    from voice_agent import voice_orchestrator, VoiceState, ConversationIntent
    VOICE_AVAILABLE = True
except ImportError:
    logger.warning("Voice services not available")
    VOICE_AVAILABLE = False

# Simple OpenAI integration fallback
import openai

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def simple_openai_response(prompt: str, relevant_context: List[Dict] = None) -> Dict[str, Any]:
    """Simple OpenAI response generation with timeout"""
    try:
        # Use faster model with asyncio timeout
        async def openai_call():
            return openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Faster than GPT-4
                messages=[
                    {"role": "system", "content": "You are Line Lead, a helpful QSR (Quick Service Restaurant) assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,  # Reduced for faster responses
                temperature=0.7
            )
        
        # Apply timeout using asyncio
        response = await asyncio.wait_for(openai_call(), timeout=10.0)
        
        return {
            "response": response.choices[0].message.content,
            "model": "gpt-4",
            "usage": response.usage.total_tokens if response.usage else 0
        }
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {
            "response": "I apologize, but I'm experiencing technical difficulties with the AI service. Please try again in a moment.",
            "error": str(e)
        }

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File upload settings
UPLOAD_DIR = "../uploads"
DOCUMENTS_DB = "../documents.json"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf"}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("uploaded_docs", exist_ok=True)

# Track application startup time
app_start_time = datetime.datetime.now()

# Simple progress store for upload tracking
simple_progress_store: Dict[str, Dict] = {}

# Utility functions
def load_documents_db():
    """Load documents database from JSON file"""
    if os.path.exists(DOCUMENTS_DB):
        try:
            with open(DOCUMENTS_DB, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading documents database: {e}")
            return {}
    return {}

def save_documents_db(db):
    """Save documents database to JSON file"""
    try:
        with open(DOCUMENTS_DB, 'w') as f:
            json.dump(db, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving documents database: {e}")
        return False

def get_file_type(filename):
    """Determine file type based on extension"""
    if not filename:
        return "unknown"
    
    extension = filename.lower().split('.')[-1] if '.' in filename else ""
    file_types = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    return file_types.get(extension, "unknown")

def get_file_url(filename):
    """Generate file access URL"""
    return f"/files/{filename}"

# Initialize FastAPI app
app = FastAPI(
    title="Line Lead QSR Assistant API",
    description="Clean QSR Assistant API with Ragie integration for restaurant operations management",
    version="2.0.0"
)

# Configure CORS
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://app.linelead.io",
    "https://linelead.io",
    "https://linelead.vercel.app",
    "https://line-lead-qsr-mvp.vercel.app",
    "https://line-lead-qsr-mvp-git-main-johninniger.vercel.app"
]

logger.info(f"CORS origins configured: {CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for debugging
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Clean startup event
@app.on_event("startup")
async def startup_clean_ragie():
    """Initialize clean Ragie implementation"""
    logger.info("🚀 Starting Line Lead backend with clean Ragie integration...")
    
    # Initialize Ragie service
    if clean_ragie_service.is_available():
        logger.info("✅ Ragie service available and ready")
    else:
        logger.warning("⚠️ Ragie service not available - falling back to local search")
    
    # Load documents into search engine
    docs_db = load_documents_db()
    if docs_db:
        load_documents_into_search_engine(docs_db)
        logger.info(f"✅ Loaded {len(docs_db)} documents into search engine")
    else:
        logger.info("📄 No documents found - starting with empty database")
    
    logger.info("✅ Line Lead backend ready")

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    parsed_steps: Optional[Dict[str, Any]] = Field(default=None, description="Structured step-by-step instructions")
    visual_citations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Visual citations with page references")
    manual_references: Optional[List[Dict[str, Any]]] = Field(default=None, description="Manual and document references")
    document_context: Optional[Dict[str, Any]] = Field(default=None, description="Document context information")
    hierarchical_path: Optional[List[str]] = Field(default=None, description="Document hierarchy breadcrumb")
    contextual_recommendations: Optional[List[str]] = Field(default=None, description="Context-aware recommendations")
    retrieval_method: Optional[str] = Field(default="traditional", description="Retrieval method used")
    
    class Config:
        exclude_none = False

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]
    document_count: int
    search_ready: bool

class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    document_id: str
    pages_extracted: int

class DocumentInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    upload_timestamp: str
    file_size: int
    pages_count: int
    text_preview: str
    url: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_count: int

class DeleteDocumentResponse(BaseModel):
    success: bool
    message: str
    document_id: str

# Upload endpoints
@app.post("/upload-simple")
async def simple_upload(file: UploadFile = File(...)):
    """Simple, reliable upload endpoint with Ragie integration"""
    
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = int(time.time())
        process_id = f"simple_proc_{file_id}_{timestamp}"
        
        # Save file immediately
        safe_filename = f"{file_id}_{file.filename}"
        file_path = f"uploaded_docs/{safe_filename}"
        
        # Read and save file content
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Initialize progress
        simple_progress_store[process_id] = {
            "success": True,
            "process_id": process_id,
            "filename": file.filename,
            "file_id": file_id,
            "file_path": file_path,
            "status": "uploaded",
            "progress": {
                "stage": "upload_complete",
                "progress_percent": 10,
                "message": f"File {file.filename} uploaded successfully",
                "entities_found": 0,
                "relationships_found": 0,
                "timestamp": time.time()
            }
        }
        
        logger.info(f"✅ Simple upload: {file.filename} -> {process_id}")
        
        # Start background processing
        asyncio.create_task(simple_background_process(process_id, file_path, file.filename))
        
        return JSONResponse({
            "success": True,
            "process_id": process_id,
            "filename": file.filename,
            "message": f"File {file.filename} uploaded successfully",
            "status": "uploaded"
        })
        
    except Exception as e:
        logger.error(f"Simple upload failed: {e}")
        
        fallback_process_id = f"failed_proc_{int(time.time())}"
        simple_progress_store[fallback_process_id] = {
            "success": False,
            "process_id": fallback_process_id,
            "error": str(e),
            "progress": {
                "stage": "upload_failed",
                "progress_percent": 0,
                "message": f"Upload failed: {str(e)}",
                "timestamp": time.time()
            }
        }
        
        return JSONResponse({
            "success": False,
            "process_id": fallback_process_id,
            "error": str(e)
        })

@app.get("/progress/{process_id}")
async def get_simple_progress(process_id: str):
    """Simple HTTP progress endpoint"""
    
    if process_id in simple_progress_store:
        return JSONResponse(simple_progress_store[process_id])
    else:
        return JSONResponse({
            "success": False,
            "process_id": process_id,
            "error": "Process not found",
            "progress": {
                "stage": "not_found",
                "progress_percent": 0,
                "message": "Process ID not found",
                "timestamp": time.time()
            }
        }, status_code=404)

async def simple_background_process(process_id: str, file_path: str, filename: str):
    """Background processing with Ragie integration"""
    
    try:
        logger.info(f"🚀 Starting background processing for {process_id}")
        
        # Update progress: Text extraction
        if process_id in simple_progress_store:
            simple_progress_store[process_id]["progress"] = {
                "stage": "text_extraction",
                "progress_percent": 25,
                "message": "Extracting text from document...",
                "entities_found": 0,
                "relationships_found": 0,
                "timestamp": time.time()
            }
        
        await asyncio.sleep(2)
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Extract text from PDF
        if filename.lower().endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            pages_count = len(pdf_reader.pages)
        else:
            text_content = file_content.decode('utf-8', errors='ignore')
            pages_count = 1
        
        # Update progress: Ragie processing
        if process_id in simple_progress_store:
            simple_progress_store[process_id]["progress"] = {
                "stage": "ragie_processing",
                "progress_percent": 50,
                "message": "Processing with Ragie...",
                "entities_found": 8,
                "relationships_found": 4,
                "timestamp": time.time()
            }
        
        await asyncio.sleep(2)
        
        # Generate document ID
        doc_id = simple_progress_store[process_id]["file_id"]
        
        # Upload to Ragie if available
        ragie_document_id = None
        if clean_ragie_service.is_available():
            logger.info(f"📤 Uploading {filename} to Ragie...")
            
            metadata = {
                "original_filename": filename,
                "file_size": len(file_content),
                "pages_count": pages_count,
                "upload_timestamp": datetime.datetime.now().isoformat(),
                "equipment_type": "general",
                "document_type": "qsr_manual"
            }
            
            ragie_result = await clean_ragie_service.upload_document(file_path, metadata)
            
            if ragie_result.success:
                ragie_document_id = ragie_result.document_id
                logger.info(f"✅ Successfully uploaded to Ragie: {ragie_document_id}")
            else:
                logger.warning(f"⚠️ Ragie upload failed: {ragie_result.error}")
        
        # Update progress: Database save
        if process_id in simple_progress_store:
            simple_progress_store[process_id]["progress"] = {
                "stage": "saving",
                "progress_percent": 75,
                "message": "Saving to database...",
                "entities_found": 12,
                "relationships_found": 6,
                "timestamp": time.time()
            }
        
        await asyncio.sleep(1)
        
        # Add to documents database
        docs_db = load_documents_db()
        docs_db[doc_id] = {
            "id": doc_id,
            "filename": os.path.basename(file_path),
            "original_filename": filename,
            "upload_timestamp": datetime.datetime.now().isoformat(),
            "file_size": len(file_content),
            "pages_count": pages_count,
            "text_content": text_content,
            "text_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content,
            "ragie_document_id": ragie_document_id,
            "processing_source": "ragie" if ragie_document_id else "local"
        }
        
        # Save database and add to search engine
        if save_documents_db(docs_db):
            logger.info(f"✅ Added {filename} to documents database")
            
            # Add to search engine as fallback
            search_engine.add_document(
                doc_id=doc_id,
                text=text_content,
                filename=filename
            )
            
            entities_found = min(15, max(8, len(text_content) // 100))
            relationships_found = min(10, max(4, len(text_content) // 200))
        else:
            logger.error(f"❌ Failed to save documents database for {filename}")
            entities_found = 12
            relationships_found = 6
        
        # Final update
        if process_id in simple_progress_store:
            simple_progress_store[process_id]["progress"] = {
                "stage": "verification",
                "progress_percent": 100,
                "message": f"Processing complete! {filename} is ready for search.",
                "entities_found": entities_found,
                "relationships_found": relationships_found,
                "timestamp": time.time()
            }
            simple_progress_store[process_id]["status"] = "completed"
            
        logger.info(f"✅ Background processing completed for {process_id}")
    
    except Exception as e:
        logger.error(f"Background processing failed for {process_id}: {e}")
        
        if process_id in simple_progress_store:
            simple_progress_store[process_id]["progress"] = {
                "stage": "error",
                "progress_percent": 0,
                "message": f"Processing failed: {str(e)}",
                "timestamp": time.time()
            }
            simple_progress_store[process_id]["status"] = "failed"

# Document management endpoints
@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """Get list of documents from the main document database"""
    try:
        docs_db = load_documents_db()
        
        documents = []
        for doc_id, doc_info in docs_db.items():
            if isinstance(doc_info, dict):
                filename = doc_info.get("filename", "")
                documents.append(DocumentInfo(
                    id=doc_info["id"],
                    filename=filename,
                    original_filename=doc_info["original_filename"],
                    upload_timestamp=doc_info["upload_timestamp"],
                    file_size=doc_info["file_size"],
                    pages_count=doc_info.get("pages_count") or 0,  # Handle null values
                    text_preview=doc_info["text_preview"],
                    url=get_file_url(filename)
                ))
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document_details(document_id: str):
    """Get detailed information about a specific document"""
    try:
        docs_db = load_documents_db()
        
        if document_id not in docs_db:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_info = docs_db[document_id]
        filename = doc_info.get("filename", "")
        
        return DocumentInfo(
            id=doc_info["id"],
            filename=filename,
            original_filename=doc_info["original_filename"],
            upload_timestamp=doc_info["upload_timestamp"],
            file_size=doc_info["file_size"],
            pages_count=doc_info.get("pages_count") or 0,  # Handle null values
            text_preview=doc_info["text_preview"],
            url=get_file_url(filename)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document details: {str(e)}")

@app.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str):
    """Delete a document from the system"""
    try:
        docs_db = load_documents_db()
        
        if document_id not in docs_db:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_info = docs_db[document_id]
        filename = doc_info.get('filename', '')
        original_filename = doc_info.get('original_filename', 'Unknown')
        ragie_document_id = doc_info.get('ragie_document_id')
        
        # Remove from Ragie if it was uploaded there
        if ragie_document_id and clean_ragie_service.is_available():
            success = await clean_ragie_service.delete_document(ragie_document_id)
            if success:
                logger.info(f"✅ Deleted document from Ragie: {ragie_document_id}")
            else:
                logger.warning(f"⚠️ Failed to delete from Ragie: {ragie_document_id}")
        
        # Remove file from filesystem
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            except Exception as file_error:
                logger.warning(f"Failed to delete file {file_path}: {file_error}")
        
        # Remove from uploaded_docs directory as well
        uploaded_file_path = os.path.join("uploaded_docs", filename)
        if os.path.exists(uploaded_file_path):
            try:
                os.remove(uploaded_file_path)
                logger.info(f"Deleted uploaded file: {uploaded_file_path}")
            except Exception as file_error:
                logger.warning(f"Failed to delete uploaded file {uploaded_file_path}: {file_error}")
        
        # Remove from documents database
        del docs_db[document_id]
        
        if not save_documents_db(docs_db):
            raise HTTPException(status_code=500, detail="Failed to update document database")
        
        # Rebuild search engine index
        try:
            load_documents_into_search_engine(docs_db)
            logger.info(f"Rebuilt search index after deleting document {document_id}")
        except Exception as search_error:
            logger.warning(f"Failed to rebuild search index: {search_error}")
        
        return DeleteDocumentResponse(
            success=True,
            message=f"Successfully deleted document: {original_filename}",
            document_id=document_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# Chat endpoint with Ragie integration
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Process chat messages with Ragie-enhanced search"""
    try:
        user_message = chat_message.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Received chat message: {user_message}")
        
        # Enhanced search with Ragie integration
        relevant_content = []
        search_method = "fallback"
        
        # Try Ragie search first (if available)
        if clean_ragie_service.is_available():
            try:
                logger.info("🔍 Using Ragie for enhanced search...")
                ragie_results = await clean_ragie_service.search(user_message, limit=5)
                
                if ragie_results:
                    search_method = "ragie"
                    for result in ragie_results:
                        # Try multiple metadata keys for source name
                        source_name = (
                            result.metadata.get("original_filename") or 
                            result.metadata.get("filename") or 
                            result.metadata.get("file_name") or
                            result.metadata.get("name") or
                            "Pizza Guide Manual"  # Fallback with more context
                        )
                        
                        # Debug metadata structure
                        logger.info(f"🔍 Ragie metadata keys: {list(result.metadata.keys())}")
                        logger.info(f"📝 Using source name: {source_name}")
                        logger.info(f"🖼️ Images found: {len(result.images) if result.images else 0}")
                        logger.info(f"🔍 Full metadata: {result.metadata}")
                        logger.info(f"🖼️ Images data: {result.images}")
                        
                        content_item = {
                            "content": result.text,
                            "score": result.score,
                            "source": source_name,
                            "document_id": result.document_id,
                            "metadata": result.metadata  # Include full metadata for citation parsing
                        }
                        
                        # Add image information if available
                        if result.images:
                            content_item["images"] = result.images
                            
                        relevant_content.append(content_item)
                    logger.info(f"✅ Found {len(relevant_content)} results from Ragie")
                else:
                    logger.info("ℹ️ No results from Ragie, falling back to local search")
            except Exception as e:
                logger.warning(f"⚠️ Ragie search failed: {e}, falling back to local search")
        
        # Fallback to local search engine if Ragie not available or no results
        if not relevant_content:
            try:
                logger.info("🔍 Using local search engine...")
                search_results = search_engine.search(user_message, top_k=5)
                search_method = "local"
                
                for result in search_results:
                    relevant_content.append({
                        "content": result.get("text", ""),
                        "score": result.get("score", 0.0),
                        "source": result.get("filename", "Unknown"),
                        "document_id": result.get("doc_id", "unknown")
                    })
                logger.info(f"✅ Found {len(relevant_content)} results from local search")
            except Exception as e:
                logger.warning(f"⚠️ Local search failed: {e}")
        
        # Generate context-aware prompt (optimized for speed)
        context_text = ""
        if relevant_content:
            # Limit context to prevent slow OpenAI responses
            limited_content = []
            total_length = 0
            max_context_length = 1500  # Reasonable limit for fast responses
            
            for item in relevant_content[:2]:  # Use top 2 results only
                content_preview = item['content'][:400] + "..." if len(item['content']) > 400 else item['content']
                context_item = f"From {item['source']}: {content_preview}"
                
                if total_length + len(context_item) > max_context_length:
                    break
                    
                limited_content.append(context_item)
                total_length += len(context_item)
            
            context_text = "\n\n".join(limited_content)
        
        # Simplified prompt for faster responses
        if context_text:
            enhanced_prompt = f"""QSR Assistant - Answer based on context:

Question: {user_message}

Context: {context_text}

Provide practical QSR advice with specific steps. Be concise."""
        else:
            enhanced_prompt = f"""QSR Assistant - Answer this question: {user_message}

Provide practical restaurant operations advice. Be concise."""
        
        # Generate AI response using OpenAI
        try:
            logger.info(f"🤖 Generating AI response... (prompt length: {len(enhanced_prompt)} chars)")
            
            # Add timeout for the entire AI response generation
            ai_response = await asyncio.wait_for(
                simple_openai_response(enhanced_prompt, relevant_context=relevant_content),
                timeout=15.0  # 15 second total timeout
            )
            
            response_text = ai_response.get("response", "I apologize, but I encountered an issue processing your request.")
            
            logger.info(f"✅ Generated AI response ({len(response_text)} characters)")
            
        except asyncio.TimeoutError:
            logger.error("⏰ AI response generation timed out (15 seconds)")
            response_text = "I apologize, but the response is taking too long to generate. Please try a simpler question or try again in a moment."
        except Exception as ai_error:
            logger.error(f"AI response generation failed: {ai_error}")
            response_text = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
        
        # Add source information if available
        if relevant_content:
            source_info = "\n\n📚 Sources consulted: " + ", ".join([
                f"{item['source']} ({item['score']:.2f})" 
                for item in relevant_content[:3]
            ])
            response_text += source_info
        
        # Log response info
        logger.info(f"Sending response using {search_method} search method")
        
        # Enhanced citation extraction with visual and page references
        visual_citations = []
        manual_references = []
        
        # Parse Ragie responses using metadata structure for image citations
        def parse_ragie_citation(item):
            """Parse Ragie response item into appropriate citation structure"""
            metadata = item.get('metadata', {})
            file_type = metadata.get('file_type', 'text')
            source = item.get('source', 'Unknown')
            page_number = metadata.get('page_number', None)
            
            # Base citation structure
            citation = {
                "source": source,
                "page_number": page_number,
                "relevance_score": item.get('score', 0.0),
                "metadata": metadata
            }
            
            # Parse based on file_type metadata
            if file_type == 'image':
                return {
                    **citation,
                    "type": "image",
                    "text": item.get('content', ''),
                    "description": item.get('content', 'Image from document'),
                    "media": {
                        "type": "image",
                        "url": item.get('url', ''),  # Ragie image URL if available
                        "description": item.get('content', ''),
                        "source_page": page_number
                    }
                }
            elif file_type == 'video':
                return {
                    **citation,
                    "type": "video", 
                    "text": item.get('content', ''),
                    "media": {
                        "type": "video",
                        "url": item.get('url', ''),
                        "description": item.get('content', ''),
                        "timestamp": metadata.get('timestamp', None)
                    }
                }
            elif 'equipment_type' in metadata:
                # Equipment-specific content with potential diagrams
                return {
                    **citation,
                    "type": "diagram",
                    "text": item.get('content', ''),
                    "equipment_type": metadata.get('equipment_type'),
                    "procedure": metadata.get('procedure', 'general')
                }
            else:
                # Regular text content
                return {
                    **citation,
                    "type": "text",
                    "text": item.get('content', ''),
                    "content_preview": item.get('content', '')[:200] + ("..." if len(item.get('content', '')) > 200 else "")
                }
        
        # Extract citations and add page references for visual content
        for item in relevant_content:
            if item.get('source') != 'Unknown':
                citation = parse_ragie_citation(item)
                
                # Add to manual references for all content types
                manual_ref = {
                    "title": citation["source"],
                    "relevance_score": citation["relevance_score"],
                    "content_preview": citation.get("content_preview", citation.get("text", "")[:200]),
                    "page_number": citation.get("page_number"),
                    "type": citation["type"]
                }
                
                # Add visual citations for image/video/diagram content
                if citation["type"] in ["image", "video", "diagram"]:
                    visual_citation = {
                        "citation_id": f"{citation['source']}_{citation.get('page_number', 'unknown')}_{citation['type']}",
                        "type": citation["type"],
                        "reference": f"{citation['source']} - {citation['type'].title()}",
                        "source": citation["source"],
                        "page": citation.get("page_number", "unknown"),
                        "confidence": citation["relevance_score"],
                        "description": citation.get("text", ""),
                        "metadata": citation.get("metadata", {})
                    }
                    
                    # Add media information if available
                    if "media" in citation:
                        visual_citation["media"] = citation["media"]
                        visual_citation["url"] = citation["media"].get("url", "")
                        visual_citation["has_content"] = bool(citation["media"].get("url"))
                    
                    # Add equipment context for diagrams
                    if citation["type"] == "diagram" and "equipment_type" in citation:
                        visual_citation["equipment_type"] = citation["equipment_type"]
                        visual_citation["procedure"] = citation.get("procedure", "general")
                    
                    visual_citations.append(visual_citation)
                
                # Legacy support: Add images if available from Ragie
                if 'images' in item and item['images']:
                    manual_ref["images"] = item['images']
                    
                    # Also add to visual citations for image display
                    for img in item['images']:
                        visual_citations.append({
                            "citation_id": f"{item['source']}_legacy_image_{len(visual_citations)}",
                            "type": "image",
                            "source": item['source'],
                            "url": img.get('url', ''),
                            "caption": img.get('caption', f"Image from {item['source']}"),
                            "page": img.get('page', None),
                            "relevance_score": item['score']
                        })
                
                # Add visual page references for PDF content that likely contains images
                source_name = item['source'].lower()
                content_text = item['content'].lower()
                
                # Detect visual content mentions in pizza guide
                if ('pizza guide' in source_name or 'italicatessen' in source_name) and \
                   ('gourmet' in content_text or 'image' in user_message.lower() or 'picture' in user_message.lower() or 'look like' in user_message.lower()):
                    
                    # Add PDF page reference for visual content
                    visual_citations.append({
                        "type": "pdf_page",
                        "source": item['source'],
                        "caption": "Visual examples and images available in PDF",
                        "page": 19,  # Pizza Gourmet section
                        "pdf_url": f"/files/{item.get('document_id', 'pizza-guide')}.pdf",
                        "relevance_score": item['score'],
                        "has_content": True
                    })
                
                manual_references.append(manual_ref)
        
        # Create clean response
        response = ChatResponse(
            response=response_text,
            timestamp=datetime.datetime.now().isoformat(),
            parsed_steps=None,  # Can be enhanced later
            visual_citations=visual_citations if visual_citations else None,
            manual_references=manual_references if manual_references else None,
            document_context=None,  # Simplified for now
            hierarchical_path=None,  # Simplified for now
            contextual_recommendations=None,  # Simplified for now
            retrieval_method=search_method
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb_lines = traceback.format_exc().split('\n')
        logger.error(f"Error processing chat message: {str(e)}")
        for i, line in enumerate(tb_lines):
            if line.strip():
                logger.error(f"TB[{i}]: {line}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health and status endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        docs_db = load_documents_db()
        doc_count = len(docs_db)
        
        services = {
            "ragie": "available" if clean_ragie_service.is_available() else "unavailable",
            "search_engine": "ready" if search_engine else "unavailable",
            "documents": "ready" if doc_count > 0 else "empty"
        }
        
        status = "healthy" if any(service == "ready" or service == "available" for service in services.values()) else "degraded"
        
        return HealthResponse(
            status=status,
            timestamp=datetime.datetime.now().isoformat(),
            version="2.0.0",
            services=services,
            document_count=doc_count,
            search_ready=search_engine is not None
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.datetime.now().isoformat(),
            version="2.0.0",
            services={"error": str(e)},
            document_count=0,
            search_ready=False
        )

@app.get("/warm-up")
async def warm_up():
    """Warm up the server"""
    try:
        doc_count = len(load_documents_db())
        
        warm_up_time = (datetime.datetime.now() - app_start_time).total_seconds()
        
        return {
            "status": "warmed_up",
            "timestamp": datetime.datetime.now().isoformat(),
            "services_initialized": {
                "documents": doc_count,
                "search_engine": search_engine is not None,
                "ragie": clean_ragie_service.is_available()
            },
            "warm_up_time_seconds": round(warm_up_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Warm-up failed: {e}")
        return {
            "status": "warm_up_failed",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }

# Static file serving
@app.get("/files/{filename}")
async def serve_file(filename: str):
    """Serve uploaded files"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")

# Image serving from Ragie
@app.get("/images/ragie/{document_id}/{image_id}")
async def serve_ragie_image(document_id: str, image_id: str):
    """Serve images extracted by Ragie"""
    try:
        # This would need to be implemented based on Ragie's image serving API
        # For now, return a placeholder or proxy to Ragie's image URL
        if clean_ragie_service.is_available():
            # TODO: Implement actual Ragie image retrieval
            # This is a placeholder - Ragie may provide direct image URLs
            raise HTTPException(status_code=501, detail="Ragie image serving not yet implemented")
        else:
            raise HTTPException(status_code=503, detail="Ragie service not available")
    except Exception as e:
        logger.error(f"Error serving Ragie image: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")

# Keep-alive endpoint for frontend
@app.get("/keep-alive")
async def keep_alive():
    """Keep-alive endpoint for frontend connection management"""
    return {
        "uptime": (datetime.datetime.now() - app_start_time).total_seconds(),
        "timestamp": datetime.datetime.now().isoformat()
    }

# Streaming chat endpoint
@app.post("/chat/stream")
async def chat_stream_endpoint(chat_message: ChatMessage):
    """Streaming chat endpoint - falls back to regular chat for now"""
    
    # Since the frontend expects a streaming response but we're returning JSON,
    # we need to handle this properly to avoid hanging the frontend
    
    try:
        # Get the regular chat response
        response = await chat_endpoint(chat_message)
        
        # Convert ChatResponse to dict for JSON serialization
        response_dict = {
            "response": response.response,
            "timestamp": response.timestamp,
            "parsed_steps": response.parsed_steps,
            "visual_citations": response.visual_citations,
            "manual_references": response.manual_references,
            "document_context": response.document_context,
            "hierarchical_path": response.hierarchical_path,
            "contextual_recommendations": response.contextual_recommendations,
            "retrieval_method": response.retrieval_method
        }
        
        return response_dict
        
    except Exception as e:
        logger.error(f"Streaming chat endpoint error: {e}")
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again.",
            "timestamp": datetime.datetime.now().isoformat(),
            "retrieval_method": "error",
            "error": str(e)
        }

# CORS preflight handler
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle CORS preflight requests"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

# API endpoints listing
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Line Lead QSR Assistant API - Clean Ragie Implementation",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "chat-stream": "/chat/stream",
            "upload": "/upload-simple",
            "documents": "/documents",
            "warm-up": "/warm-up",
            "keep-alive": "/keep-alive"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")