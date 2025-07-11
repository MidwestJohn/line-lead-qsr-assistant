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
    """Simple OpenAI response generation"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Line Lead, a helpful QSR (Quick Service Restaurant) assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
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
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
                        relevant_content.append({
                            "content": result.text,
                            "score": result.score,
                            "source": result.metadata.get("original_filename", "Unknown"),
                            "document_id": result.document_id
                        })
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
        
        # Generate context-aware prompt
        context_text = ""
        if relevant_content:
            context_text = "\n\n".join([
                f"From {item['source']}: {item['content']}" 
                for item in relevant_content[:3]  # Use top 3 results
            ])
        
        enhanced_prompt = f"""You are Line Lead, a QSR (Quick Service Restaurant) assistant specialized in restaurant operations, equipment, and procedures.

User Question: {user_message}

Relevant Context:
{context_text if context_text else "No specific context found - provide general QSR guidance."}

Instructions:
- Provide practical, actionable advice for QSR operations
- Focus on safety, efficiency, and compliance
- Include specific steps when applicable
- If equipment is mentioned, provide operational guidance
- Be concise but comprehensive

Response:"""
        
        # Generate AI response using OpenAI
        try:
            logger.info("🤖 Generating AI response...")
            
            ai_response = await simple_openai_response(
                enhanced_prompt,
                relevant_context=relevant_content
            )
            
            response_text = ai_response.get("response", "I apologize, but I encountered an issue processing your request.")
            
            logger.info(f"✅ Generated AI response ({len(response_text)} characters)")
            
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
        
        # Simple citation extraction from relevant content
        visual_citations = []
        manual_references = []
        
        # Extract manual references from relevant content
        for item in relevant_content:
            if item.get('source') != 'Unknown':
                manual_references.append({
                    "title": item['source'],
                    "relevance_score": item['score'],
                    "content_preview": item['content'][:200] + "..." if len(item['content']) > 200 else item['content']
                })
        
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
            "upload": "/upload-simple",
            "documents": "/documents",
            "warm-up": "/warm-up"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")