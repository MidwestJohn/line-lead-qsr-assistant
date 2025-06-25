from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List
import logging
import datetime
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import os
import json
import aiofiles
import PyPDF2
from io import BytesIO
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from document_search import search_engine, load_documents_into_search_engine
from openai_integration import qsr_assistant

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

def extract_pdf_text(pdf_content: bytes) -> tuple[str, int]:
    """Extract text from PDF content"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        text_content = ""
        pages_count = len(pdf_reader.pages)
        
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        return text_content.strip(), pages_count
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

def generate_document_id() -> str:
    """Generate unique document ID"""
    import uuid
    return str(uuid.uuid4())

def is_valid_pdf(content: bytes) -> bool:
    """Check if content is a valid PDF"""
    try:
        PyPDF2.PdfReader(BytesIO(content))
        return True
    except:
        return False

# Initialize FastAPI app
app = FastAPI(
    title="Line Lead QSR Assistant API",
    description="Backend API for QSR maintenance assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://linelead.io",                    # Your custom domain
        "https://line-lead-qsr-assistant.vercel.app",  # Default Vercel URL
        "http://localhost:3000",                  # Local development
        "http://localhost:8000",                  # Local backend testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search engine with existing documents on startup
@app.on_event("startup")
async def startup_event():
    """Load existing documents into search engine on startup"""
    try:
        docs_db = load_documents_db()
        if docs_db:
            load_documents_into_search_engine(docs_db)
            logger.info(f"Loaded {len(docs_db)} documents into search engine at startup")
    except Exception as e:
        logger.error(f"Error loading documents at startup: {e}")

# Pydantic models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

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

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_count: int

class SearchStatsResponse(BaseModel):
    total_chunks: int
    total_documents: int
    model_name: str

class AIStatusResponse(BaseModel):
    ai_available: bool
    model_name: str
    status_message: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with service status"""
    try:
        # Check document database
        documents_db = load_documents_db()
        doc_count = len(documents_db)
        
        # Check search engine readiness
        search_ready = search_engine is not None and hasattr(search_engine, 'model')
        
        # Check AI service (basic check - could be enhanced to ping OpenAI)
        ai_status = "ready"
        try:
            from openai_integration import qsr_assistant
            ai_status = "ready" if qsr_assistant else "unavailable"
        except Exception:
            ai_status = "error"
        
        services = {
            "database": "ready",
            "search_engine": "ready" if search_ready else "initializing",
            "ai_assistant": ai_status,
            "file_upload": "ready" if os.path.exists(UPLOAD_DIR) else "error"
        }
        
        overall_status = "healthy" if all(s in ["ready", "initializing"] for s in services.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.datetime.now().isoformat(),
            version="1.0.0",
            services=services,
            document_count=doc_count,
            search_ready=search_ready
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            timestamp=datetime.datetime.now().isoformat(),
            version="1.0.0",
            services={"error": str(e)},
            document_count=0,
            search_ready=False
        )

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Process chat messages and return AI-powered QSR assistant responses"""
    try:
        user_message = chat_message.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Received chat message: {user_message}")
        
        # Search for relevant document chunks
        relevant_chunks = search_engine.search(user_message, top_k=3)
        
        # Generate AI-powered response
        ai_result = await qsr_assistant.generate_response(user_message, relevant_chunks)
        
        response_text = ai_result['response']
        
        # Add source information if available
        if ai_result.get('sources'):
            source_info = "\n\n📚 Sources consulted: " + ", ".join([
                f"{src['filename']} ({src['similarity']:.2f})" 
                for src in ai_result['sources']
            ])
            response_text += source_info
        
        # Add AI model info if available
        if ai_result.get('model_used'):
            logger.info(f"AI response generated using {ai_result['model_used']} with {ai_result.get('chunks_used', 0)} document chunks")
        
        response = ChatResponse(
            response=response_text,
            timestamp=datetime.datetime.now().isoformat()
        )
        
        logger.info(f"Sending {ai_result['type']} response with {len(relevant_chunks)} relevant chunks")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Streaming chat endpoint
@app.post("/chat/stream")
async def chat_stream_endpoint(chat_message: ChatMessage):
    """Process chat messages and return streaming AI-powered QSR assistant responses"""
    try:
        user_message = chat_message.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Received streaming chat message: {user_message}")
        
        # Search for relevant document chunks
        relevant_chunks = search_engine.search(user_message, top_k=3)
        
        async def generate_stream():
            try:
                async for chunk_data in qsr_assistant.generate_response_stream(user_message, relevant_chunks):
                    # Format as Server-Sent Events
                    data = json.dumps(chunk_data)
                    yield f"data: {data}\n\n"
                    
                    # Small delay to ensure proper streaming
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Error in streaming response: {e}")
                # Send error as final message
                error_data = json.dumps({"chunk": f"Error: {str(e)}", "done": True, "error": True})
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up streaming chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# File upload endpoint
@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process PDF manual files"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit")
        
        # Validate PDF content
        if not is_valid_pdf(content):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        
        # Extract text from PDF
        extracted_text, pages_count = extract_pdf_text(content)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from PDF")
        
        # Generate document ID and filename
        doc_id = generate_document_id()
        safe_filename = f"{doc_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Load and update documents database
        docs_db = load_documents_db()
        
        document_info = {
            "id": doc_id,
            "filename": safe_filename,
            "original_filename": file.filename,
            "upload_timestamp": datetime.datetime.now().isoformat(),
            "file_size": len(content),
            "pages_count": pages_count,
            "text_content": extracted_text,
            "text_preview": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
        }
        
        docs_db[doc_id] = document_info
        
        if not save_documents_db(docs_db):
            raise HTTPException(status_code=500, detail="Failed to save document information")
        
        # Add document to search engine
        try:
            search_engine.add_document(
                doc_id=doc_id,
                text=extracted_text,
                filename=file.filename
            )
            logger.info(f"Added document to search engine: {file.filename}")
        except Exception as search_error:
            logger.error(f"Failed to add document to search engine: {search_error}")
            # Continue anyway - document is saved, just not searchable yet
        
        logger.info(f"Successfully uploaded and processed: {file.filename} ({pages_count} pages)")
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded and processed {file.filename}",
            filename=file.filename,
            document_id=doc_id,
            pages_extracted=pages_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process uploaded file")

# List documents endpoint
@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """Get list of uploaded documents"""
    try:
        docs_db = load_documents_db()
        
        documents = []
        for doc_id, doc_info in docs_db.items():
            documents.append(DocumentInfo(
                id=doc_info["id"],
                filename=doc_info["filename"],
                original_filename=doc_info["original_filename"],
                upload_timestamp=doc_info["upload_timestamp"],
                file_size=doc_info["file_size"],
                pages_count=doc_info["pages_count"],
                text_preview=doc_info["text_preview"]
            ))
        
        # Sort by upload timestamp (newest first)
        documents.sort(key=lambda x: x.upload_timestamp, reverse=True)
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document list")

# Search stats endpoint
@app.get("/search-stats", response_model=SearchStatsResponse)
async def get_search_stats():
    """Get search engine statistics"""
    try:
        stats = search_engine.get_stats()
        return SearchStatsResponse(
            total_chunks=stats['total_chunks'],
            total_documents=stats['total_documents'],
            model_name=stats['model_name']
        )
    except Exception as e:
        logger.error(f"Error getting search stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get search statistics")

# AI status endpoint
@app.get("/ai-status", response_model=AIStatusResponse)
async def get_ai_status():
    """Get AI integration status"""
    try:
        ai_available = qsr_assistant.is_available()
        
        if ai_available:
            status_message = f"AI integration active with {qsr_assistant.model}"
            model_name = qsr_assistant.model
        else:
            status_message = "AI integration disabled - no OpenAI API key configured"
            model_name = "none"
        
        return AIStatusResponse(
            ai_available=ai_available,
            model_name=model_name,
            status_message=status_message
        )
    except Exception as e:
        logger.error(f"Error getting AI status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get AI status")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Line Lead QSR Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "upload": "/upload",
            "documents": "/documents",
            "search-stats": "/search-stats",
            "ai-status": "/ai-status",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)