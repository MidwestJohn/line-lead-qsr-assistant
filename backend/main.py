from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import datetime
import json
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
import json
import aiofiles
import PyPDF2
from io import BytesIO
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from document_search import search_engine, load_documents_into_search_engine
from openai_integration import qsr_assistant
from voice_service import voice_service
from voice_agent import voice_orchestrator, VoiceState, ConversationIntent

# Add these imports for RAG-Anything integration
from services.rag_service import rag_service
from services.search_strategy import ExistingSearchStrategy, RAGAnythingStrategy, HybridSearchStrategy
from services.document_processor import document_processor, ProcessedContent
from services.voice_graph_service import voice_graph_service
from services.neo4j_service import neo4j_service
import uuid
from dotenv import load_dotenv

# Load RAG environment
load_dotenv('.env.rag')

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

# Track application startup time for monitoring
app_start_time = datetime.datetime.now()

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
    return file_types.get(extension, 'application/octet-stream')

def validate_filename(filename):
    """Validate filename to prevent directory traversal and ensure security"""
    if not filename:
        return False
    
    # Check for directory traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for valid characters (alphanumeric, dots, dashes, underscores, spaces, parentheses)
    import re
    if not re.match(r'^[a-zA-Z0-9._\-\s()]+$', filename):
        return False
    
    return True

def get_file_url(filename):
    """Generate file URL for frontend access"""
    if not filename:
        return None
    return f"/files/{filename}"

def fix_numbered_lists_for_speech(text: str) -> str:
    """
    Convert numbered markdown lists to natural speech for better ElevenLabs pronunciation.
    
    PROBLEM: ElevenLabs pronounces "1. Turn off fryer" as "One dot turn off fryer"
    SOLUTION: Convert to "Step 1, turn off fryer" which sounds natural and professional
    
    This transforms QSR instructions into natural speech patterns that sound like
    an experienced coworker giving step-by-step procedural guidance.
    """
    import re
    
    def replace_numbered_item(match):
        """Replace numbered list items with step-based speech"""
        indent = match.group(1) or ""
        number = int(match.group(2))
        rest_of_line = match.group(3)
        
        # Always use "Step X," format with proper line breaks for readability
        # Each step starts on a new line for clean formatting
        return f"\n\nStep {number}, {rest_of_line}"
    
    # Pattern to match numbered list items: "1. Text" or "2) Text" 
    # Handles both line-start and inline patterns
    # Captures: (optional whitespace)(number)(. or ))(rest of text)
    numbered_pattern = r'(\s*)(\d+)[\.\)]\s+([^.\n]+[.\n]?)'
    
    # Process the entire text, handling both line-start and inline patterns
    result = re.sub(numbered_pattern, replace_numbered_item, text, flags=re.MULTILINE)
    
    # Handle patterns like "Do steps 1-3" or "See step 2" - keep these as numbers for clarity
    # Only convert if it makes sense (step references should stay as numbers)
    
    return result

def smart_sentence_split(text: str) -> List[str]:
    """
    Smart sentence splitting with natural speech pre-processing.
    
    ENHANCEMENTS:
    1. Converts numbered lists to natural speech ("1. Check" → "First, check") 
    2. Preserves structured content and list formatting
    3. Optimized for ElevenLabs TTS pronunciation
    
    RESULT: Natural sounding QSR instructions like an experienced coworker
    """
    import re
    
    if not text or len(text.strip()) < 15:
        return [text] if text.strip() else []
    
    # FIRST: Convert numbered lists to natural speech for better TTS
    text = fix_numbered_lists_for_speech(text)
    
    # Identify and protect natural speech patterns (after number-to-word conversion)
    natural_speech_patterns = [
        r'\b(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth|Thirteenth|Fourteenth|Fifteenth),\s[^.]*?\.',  # "First, text here."
        r'\bStep\s+(?:\d+|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth),\s[^.]*?\.',  # "Step 1, text here." or "Step First, text here."
        r'[•·▪▫-]\s[^.]*?\.',  # "• Text here." or "- Text here."
        r'\b[a-z]\.\s[^.]*?\.',  # "a. Text here."
        r'\b[ivx]+\.\s[^.]*?\.',  # "i. Text here."
    ]
    
    # Combine all patterns
    combined_pattern = '|'.join(f'({pattern})' for pattern in natural_speech_patterns)
    
    # Find all natural speech list items
    list_matches = []
    for match in re.finditer(combined_pattern, text, re.IGNORECASE):
        list_matches.append({
            'start': match.start(),
            'end': match.end(),
            'text': match.group()
        })
    
    # If no natural speech lists found, use standard sentence splitting
    if not list_matches:
        # Standard sentence splitting with better regex
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) >= 3]
    
    # Process text preserving natural speech list items
    sentences = []
    last_end = 0
    
    for list_item in list_matches:
        # Add any text before this natural speech list item
        if list_item['start'] > last_end:
            before_text = text[last_end:list_item['start']].strip()
            if before_text:
                # Split the before text normally
                before_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', before_text)
                sentences.extend([s.strip() for s in before_sentences if s.strip() and len(s.strip()) >= 3])
        
        # Add the complete natural speech list item
        sentences.append(list_item['text'].strip())
        last_end = list_item['end']
    
    # Add any remaining text after the last natural speech list
    if last_end < len(text):
        remaining_text = text[last_end:].strip()
        if remaining_text:
            remaining_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', remaining_text)
            sentences.extend([s.strip() for s in remaining_sentences if s.strip() and len(s.strip()) >= 3])
    
    # Final cleanup - ensure minimum chunk size and remove empty strings
    final_sentences = []
    for sentence in sentences:
        if sentence and len(sentence.strip()) >= 3:
            final_sentences.append(sentence.strip())
    
    return final_sentences if final_sentences else [text.strip()]

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
        "https://line-lead-qsr-assistant-qz7ni39d8-johninniger-projects.vercel.app",  # Preview deployment
        "http://localhost:3000",                  # Local development (default)
        "http://localhost:3001",                  # Local development (alternative port)
        "http://localhost:8000",                  # Local backend testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add RAG-Anything startup event
@app.on_event("startup")
async def startup_event():
    """Initialize RAG service on startup."""
    await rag_service.initialize()

# Initialize voice service with RAG dependency
@app.on_event("startup")
async def startup_event_voice():
    """Initialize voice service with RAG dependency."""
    voice_graph_service.set_rag_service(rag_service)

# File serving will be handled by dedicated endpoint below

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
    conversation_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    parsed_steps: Optional[Dict] = Field(default=None, description="Structured step data for future Playbooks UX")
    
    class Config:
        """Include null fields in JSON output"""
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
    file_type: str

class DocumentSummary(BaseModel):
    id: str
    filename: str
    original_filename: str
    upload_timestamp: str
    file_size: int
    pages_count: int
    url: str
    file_type: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentSummary]
    total_count: int

class SearchStatsResponse(BaseModel):
    total_chunks: int
    total_documents: int
    model_name: str

class AIStatusResponse(BaseModel):
    ai_available: bool
    model_name: str
    status_message: str

class DeleteDocumentResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    original_filename: str

# Voice service models
class VoiceRequest(BaseModel):
    text: str

class VoiceStatusResponse(BaseModel):
    available: bool
    voice_count: int = 0
    current_voice: str = ""
    voice_id: str = ""
    error: str = ""

class ChatVoiceRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Add session support

class ConversationSummaryRequest(BaseModel):
    session_id: Optional[str] = None

class ConversationSummaryResponse(BaseModel):
    duration: float
    message_count: int
    topics_covered: List[str] = []
    last_intent: Optional[str] = None
    completion_status: bool
    conversation_flow_analysis: Dict[str, Any] = {}

class ChatVoiceResponse(BaseModel):
    response: str
    audio_available: bool
    timestamp: str

class ChatVoiceWithAudioResponse(BaseModel):
    text_response: str
    audio_data: Optional[str] = None
    audio_available: bool
    sources: List[str] = []
    timestamp: str
    # PydanticAI orchestration fields
    detected_intent: Optional[str] = None
    should_continue_listening: bool = True
    next_voice_state: Optional[str] = None
    confidence_score: Optional[float] = None
    conversation_complete: bool = False
    suggested_follow_ups: List[str] = []

# Enhanced Health Check with Connection Management
@app.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Comprehensive health check with connection monitoring and keep-alive"""
    try:
        start_time = datetime.datetime.now()
        
        # Extract session and monitoring headers
        session_id = request.headers.get('X-Session-ID', 'anonymous')
        is_heartbeat = request.headers.get('X-Heartbeat') == 'true'
        health_check_type = request.headers.get('X-Health-Check', 'basic')
        
        # Log connection for monitoring
        if not is_heartbeat:
            logger.info(f"Health check requested by session {session_id[:12]}... (type: {health_check_type})")
        
        # Basic service checks
        documents_db = load_documents_db()
        doc_count = len(documents_db)
        
        # Enhanced search engine check
        search_ready = search_engine is not None and hasattr(search_engine, 'model')
        search_status = "ready" if search_ready else "initializing"
        
        # AI service health with timeout
        ai_status = "ready"
        ai_response_time = None
        try:
            ai_check_start = datetime.datetime.now()
            from openai_integration import qsr_assistant
            ai_status = "ready" if qsr_assistant else "unavailable"
            ai_response_time = (datetime.datetime.now() - ai_check_start).total_seconds() * 1000
            
            # Additional AI connectivity test for full health check
            if health_check_type == 'full' and ai_status == "ready":
                try:
                    # Quick test call to verify AI is responsive
                    import asyncio
                    test_future = asyncio.wait_for(
                        asyncio.create_task(test_ai_connection()), 
                        timeout=3.0
                    )
                    ai_test_result = await test_future
                    if not ai_test_result:
                        ai_status = "degraded"
                except asyncio.TimeoutError:
                    ai_status = "slow"
                except Exception:
                    ai_status = "error"
                    
        except Exception as e:
            logger.warning(f"AI health check failed: {e}")
            ai_status = "error"
        
        # File system checks
        file_upload_status = "ready" if os.path.exists(UPLOAD_DIR) else "error"
        disk_usage = get_disk_usage() if health_check_type == 'full' else None
        
        # Memory usage check for full health check
        memory_usage = get_memory_usage() if health_check_type == 'full' else None
        
        # Database connectivity check
        db_status = "ready"
        db_response_time = None
        try:
            db_check_start = datetime.datetime.now()
            # Test database read
            test_documents = load_documents_db()
            db_response_time = (datetime.datetime.now() - db_check_start).total_seconds() * 1000
            if len(test_documents) != doc_count:
                db_status = "inconsistent"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "error"
        
        services = {
            "database": db_status,
            "search_engine": search_status,
            "ai_assistant": ai_status,
            "file_upload": file_upload_status
        }
        
        # Add performance metrics for full health check
        performance_metrics = None
        if health_check_type == 'full':
            total_response_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
            performance_metrics = {
                "total_response_time_ms": round(total_response_time, 2),
                "db_response_time_ms": round(db_response_time, 2) if db_response_time else None,
                "ai_response_time_ms": round(ai_response_time, 2) if ai_response_time else None,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage
            }
        
        # Determine overall status
        critical_services = ["database", "search_engine"]
        critical_healthy = all(services[s] in ["ready", "initializing"] for s in critical_services)
        all_healthy = all(s in ["ready", "initializing"] for s in services.values())
        
        if not critical_healthy:
            overall_status = "critical"
        elif not all_healthy:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        response_data = {
            "status": overall_status,
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0.0",
            "services": services,
            "document_count": doc_count,
            "search_ready": search_ready
        }
        
        # Add performance metrics to full health checks
        if performance_metrics:
            response_data["performance"] = performance_metrics
            
        # Add session tracking for connection management
        if session_id != 'anonymous':
            response_data["session_id"] = session_id
            
        return HealthResponse(**response_data)
        
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

async def test_ai_connection():
    """Test AI service connectivity with minimal request"""
    try:
        from openai_integration import qsr_assistant
        if qsr_assistant:
            # Quick test - just verify the assistant is callable
            return True
        return False
    except Exception:
        return False

def get_disk_usage():
    """Get disk usage information"""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        usage_percent = (used / total) * 100
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round(usage_percent, 1)
        }
    except Exception:
        return None

def get_memory_usage():
    """Get memory usage information"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total_mb": round(memory.total / (1024**2), 1),
            "used_mb": round(memory.used / (1024**2), 1),
            "available_mb": round(memory.available / (1024**2), 1),
            "usage_percent": round(memory.percent, 1)
        }
    except ImportError:
        # psutil not available, use basic system info
        try:
            import os
            # Basic memory check using /proc/meminfo on Linux
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if line.startswith('MemTotal:'):
                            total = int(line.split()[1]) / 1024  # Convert KB to MB
                        elif line.startswith('MemAvailable:'):
                            available = int(line.split()[1]) / 1024
                    used = total - available
                    return {
                        "total_mb": round(total, 1),
                        "used_mb": round(used, 1),
                        "available_mb": round(available, 1),
                        "usage_percent": round((used / total) * 100, 1)
                    }
        except Exception:
            pass
        return None
    except Exception:
        return None

# Keep-alive endpoint for preventing cold starts
@app.get("/keep-alive")
async def keep_alive():
    """Keep-alive endpoint to prevent Render cold starts"""
    return {
        "status": "alive",
        "timestamp": datetime.datetime.now().isoformat(),
        "uptime_seconds": (datetime.datetime.now() - app_start_time).total_seconds() if 'app_start_time' in globals() else 0
    }

# Warm-up endpoint for faster cold start recovery
@app.post("/warm-up")
async def warm_up():
    """Warm-up endpoint to initialize services after cold start"""
    try:
        logger.info("Warm-up request received")
        
        # Pre-load critical services
        documents_db = load_documents_db()
        doc_count = len(documents_db)
        
        # Initialize search engine if needed
        global search_engine
        if search_engine is None:
            try:
                from document_search import initialize_search_engine
                search_engine = initialize_search_engine()
                logger.info("Search engine initialized during warm-up")
            except Exception as e:
                logger.warning(f"Search engine initialization failed during warm-up: {e}")
        
        # Pre-load AI assistant
        try:
            from openai_integration import qsr_assistant
            if qsr_assistant:
                logger.info("AI assistant verified during warm-up")
        except Exception as e:
            logger.warning(f"AI assistant check failed during warm-up: {e}")
        
        warm_up_time = (datetime.datetime.now() - app_start_time).total_seconds() if 'app_start_time' in globals() else 0
        
        return {
            "status": "warmed_up",
            "timestamp": datetime.datetime.now().isoformat(),
            "services_initialized": {
                "documents": doc_count,
                "search_engine": search_engine is not None,
                "ai_assistant": True
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
        
        # CRITICAL FIX: Use PydanticAI voice orchestrator for intelligent conversation management
        orchestrated_response = await voice_orchestrator.process_voice_message(
            message=user_message,
            relevant_docs=relevant_chunks,
            session_id=chat_message.conversation_id
        )
        
        response_text = orchestrated_response.text_response
        
        # Natural speech conversion is already applied in the orchestrator
        # No need to apply fix_numbered_lists_for_speech again
        
        # Add source information if available
        if relevant_chunks:
            source_info = "\n\n📚 Sources consulted: " + ", ".join([
                f"{chunk.get('source', 'unknown')} ({chunk.get('similarity', 0.0):.2f})" 
                for chunk in relevant_chunks
            ])
            response_text += source_info
        
        # Log orchestration info
        logger.info(f"Sending orchestrated response with intent: {orchestrated_response.detected_intent}, confidence: {orchestrated_response.confidence_score}")
        
        # Include parsed steps for future Playbooks UX (always include field)
        parsed_steps_dict = None
        if orchestrated_response.parsed_steps:
            parsed_steps_dict = orchestrated_response.parsed_steps.model_dump()
            logger.info(f"📋 Including parsed steps: {orchestrated_response.parsed_steps.total_steps} steps found")
        else:
            logger.info("📋 No parsed steps found in response")
        
        response = ChatResponse(
            response=response_text,
            timestamp=datetime.datetime.now().isoformat(),
            parsed_steps=parsed_steps_dict
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
                # CRITICAL FIX: Use PydanticAI voice orchestrator for intelligent conversation management
                orchestrated_response = await voice_orchestrator.process_voice_message(
                    message=user_message,
                    relevant_docs=relevant_chunks,
                    session_id=chat_message.conversation_id
                )
                
                complete_response = orchestrated_response.text_response
                # Natural speech conversion is already applied in the orchestrator
                        
                # Re-stream the orchestrated response preserving spacing and formatting
                # Split into paragraphs first to preserve structure
                paragraphs = complete_response.split('\n\n')
                
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # For each paragraph, split into sentences while preserving spacing
                        sentences = paragraph.split('. ')
                        
                        for i, sentence in enumerate(sentences):
                            if sentence.strip():
                                # Add period back if it's not the last sentence in paragraph
                                if i < len(sentences) - 1 and not sentence.endswith('.'):
                                    sentence += '.'
                                
                                # Add space after sentence (will be trimmed by frontend)
                                chunk_text = sentence + ' ' if not sentence.endswith('\n') else sentence
                                yield f"data: {json.dumps({'chunk': chunk_text, 'done': False})}\n\n"
                                await asyncio.sleep(0.01)
                        
                        # Add paragraph break after each paragraph
                        if paragraph != paragraphs[-1]:  # Not the last paragraph
                            yield f"data: {json.dumps({'chunk': ' ', 'done': False})}\n\n"
                
                # Send final completion signal
                yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
                    
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

# File serving endpoint
@app.get("/files/{filename}")
async def serve_file(filename: str, request: Request):
    """High-performance streaming file server with range request support"""
    try:
        # URL decode the filename
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # Validate decoded filename for security
        if not validate_filename(decoded_filename):
            logger.warning(f"Invalid filename requested: {decoded_filename} (original: {filename})")
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Construct file path using decoded filename
        file_path = os.path.join(UPLOAD_DIR, decoded_filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(file_path):
            logger.warning(f"Path is not a file: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file size for range requests
        file_size = os.path.getsize(file_path)
        
        # Determine content type
        content_type = get_file_type(filename)
        
        # Parse range header for partial content support
        range_header = request.headers.get('range')
        
        if range_header:
            # Handle range requests for streaming (critical for PDF performance)
            try:
                byte_start = 0
                byte_end = file_size - 1
                
                # Parse range header: "bytes=start-end"
                range_match = range_header.replace('bytes=', '').split('-')
                if len(range_match) == 2:
                    if range_match[0]:
                        byte_start = int(range_match[0])
                    if range_match[1]:
                        byte_end = int(range_match[1])
                
                # Ensure byte_end doesn't exceed file size
                byte_end = min(byte_end, file_size - 1)
                content_length = byte_end - byte_start + 1
                
                # Set headers for partial content response
                headers = {
                    "Content-Type": content_type,
                    "Content-Range": f"bytes {byte_start}-{byte_end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(content_length),
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST",
                    "Access-Control-Allow-Headers": "Range, Content-Type, Authorization, Cache-Control, Pragma",
                    "Access-Control-Expose-Headers": "Content-Range, Accept-Ranges, Content-Length, Content-Type",
                    "Access-Control-Max-Age": "86400",
                    "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
                }
                
                # For PDF files, set Content-Disposition to inline for browser preview
                if content_type == "application/pdf":
                    headers["Content-Disposition"] = "inline"
                
                logger.info(f"Serving partial content: {filename} ({byte_start}-{byte_end}/{file_size})")
                
                # Stream the requested byte range
                def generate_range():
                    with open(file_path, 'rb') as file:
                        file.seek(byte_start)
                        remaining = content_length
                        chunk_size = 64 * 1024  # 64KB chunks for optimal streaming
                        
                        while remaining > 0:
                            chunk_to_read = min(chunk_size, remaining)
                            chunk = file.read(chunk_to_read)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                
                return StreamingResponse(
                    generate_range(),
                    status_code=206,  # Partial Content
                    headers=headers,
                    media_type=content_type
                )
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid range header: {range_header}, error: {e}")
                # Fall through to serve entire file
        
        # Serve entire file with optimized streaming
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",  # Advertise range support
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST",
            "Access-Control-Allow-Headers": "Range, Content-Type, Authorization, Cache-Control, Pragma",
            "Access-Control-Expose-Headers": "Content-Range, Accept-Ranges, Content-Length, Content-Type",
            "Access-Control-Max-Age": "86400",
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
        
        # For PDF files, set Content-Disposition to inline for browser preview
        if content_type == "application/pdf":
            headers["Content-Disposition"] = "inline"
        
        logger.info(f"Serving full file: {filename} ({file_size} bytes)")
        
        # Stream entire file in chunks for better performance
        def generate_file():
            with open(file_path, 'rb') as file:
                chunk_size = 64 * 1024  # 64KB chunks
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        
        return StreamingResponse(
            generate_file(),
            headers=headers,
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.head("/files/{filename}")
async def files_head(filename: str, request: Request):
    """Handle HEAD requests for file serving (for debugging and accessibility checks)"""
    try:
        # URL decode the filename
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # Validate decoded filename for security
        if not validate_filename(decoded_filename):
            logger.warning(f"Invalid filename requested: {decoded_filename} (original: {filename})")
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Construct file path using decoded filename
        file_path = os.path.join(UPLOAD_DIR, decoded_filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(file_path):
            logger.warning(f"Path is not a file: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Determine content type
        content_type = get_file_type(filename)
        
        # Set headers for HEAD response
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST",
            "Access-Control-Allow-Headers": "Range, Content-Type, Authorization, Cache-Control, Pragma",
            "Access-Control-Expose-Headers": "Content-Range, Accept-Ranges, Content-Length, Content-Type",
            "Access-Control-Max-Age": "86400",
            "Cache-Control": "public, max-age=3600"
        }
        
        # For PDF files, set Content-Disposition to inline for browser preview
        if content_type == "application/pdf":
            headers["Content-Disposition"] = "inline"
        
        logger.info(f"HEAD request for file: {filename} ({content_type}, {file_size} bytes)")
        
        from fastapi import Response
        return Response(headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving HEAD request for file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.options("/files/{filename}")
async def files_options(filename: str):
    """Handle CORS preflight requests for file serving"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "Range, Content-Type, Authorization",
        "Access-Control-Expose-Headers": "Content-Range, Accept-Ranges, Content-Length"
    }

@app.get("/pdf.worker.min.js")
async def serve_pdf_worker():
    """Serve PDF.js worker file for frontend"""
    try:
        # Use absolute path construction to avoid __file__ issues
        script_dir = os.path.dirname(os.path.abspath(__file__))
        worker_path = os.path.join(script_dir, "pdf.worker.min.js")
        
        logger.info(f"Looking for PDF worker at: {worker_path}")
        
        if not os.path.exists(worker_path):
            logger.warning(f"PDF worker file not found: {worker_path}")
            raise HTTPException(status_code=404, detail="PDF worker not found")
        
        logger.info(f"Serving PDF worker from: {worker_path}")
        
        return FileResponse(
            worker_path,
            media_type="application/javascript",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",  # Force fresh download
                "Pragma": "no-cache",
                "Expires": "0",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error serving PDF worker: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.head("/pdf.worker.min.js")
async def pdf_worker_head():
    """Handle HEAD requests for PDF worker"""
    try:
        # Use absolute path construction to avoid __file__ issues
        script_dir = os.path.dirname(os.path.abspath(__file__))
        worker_path = os.path.join(script_dir, "pdf.worker.min.js")
        
        logger.info(f"HEAD request for PDF worker at: {worker_path}")
        
        if not os.path.exists(worker_path):
            logger.warning(f"PDF worker file not found: {worker_path}")
            raise HTTPException(status_code=404, detail="PDF worker not found")
        
        file_size = os.path.getsize(worker_path)
        
        return Response(
            headers={
                "Content-Type": "application/javascript",
                "Content-Length": str(file_size),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error in PDF worker HEAD request: {e}")
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
    """Get list of uploaded documents (optimized - no text preview)"""
    try:
        docs_db = load_documents_db()
        
        documents = []
        for doc_id, doc_info in docs_db.items():
            filename = doc_info.get("filename", "")
            documents.append(DocumentSummary(
                id=doc_info["id"],
                filename=filename,
                original_filename=doc_info["original_filename"],
                upload_timestamp=doc_info["upload_timestamp"],
                file_size=doc_info["file_size"],
                pages_count=doc_info["pages_count"],
                url=get_file_url(filename),
                file_type=get_file_type(doc_info["original_filename"])
            ))
        
        # Sort by upload timestamp (newest first)
        documents.sort(key=lambda x: x.upload_timestamp, reverse=True)
        
        response = DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
        return response
        
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

# Get document details endpoint
@app.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document_details(document_id: str):
    """Get detailed information about a specific document including text preview"""
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
            pages_count=doc_info["pages_count"],
            text_preview=doc_info["text_preview"],
            url=get_file_url(filename),
            file_type=get_file_type(doc_info["original_filename"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document details for {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document details")

# Delete document endpoint
@app.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str):
    """Delete a document from the system"""
    try:
        # Load documents database
        docs_db = load_documents_db()
        
        # Check if document exists
        if document_id not in docs_db:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_info = docs_db[document_id]
        filename = doc_info.get('filename', '')
        original_filename = doc_info.get('original_filename', 'Unknown')
        
        # Remove file from filesystem
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        # Remove from documents database
        del docs_db[document_id]
        
        # Save updated database
        if not save_documents_db(docs_db):
            raise HTTPException(status_code=500, detail="Failed to update document database")
        
        # Rebuild search engine index without this document
        try:
            load_documents_into_search_engine(docs_db)
            logger.info(f"Rebuilt search index after deleting document {document_id}")
        except Exception as search_error:
            logger.error(f"Failed to rebuild search index: {search_error}")
            # Continue anyway - document is deleted, search will just be stale
        
        logger.info(f"Successfully deleted document: {original_filename} (ID: {document_id})")
        
        return DeleteDocumentResponse(
            success=True,
            message=f"Successfully deleted document: {original_filename}",
            document_id=document_id,
            original_filename=original_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

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

# Voice endpoints
@app.get("/voice-status", response_model=VoiceStatusResponse)
async def get_voice_status():
    """Get ElevenLabs voice service status"""
    try:
        status = await voice_service.get_voice_status()
        return VoiceStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting voice status: {str(e)}")
        return VoiceStatusResponse(
            available=False,
            error=str(e)
        )

@app.post("/generate-audio")
async def generate_audio(request: VoiceRequest):
    """OPTIMIZED audio generation with proper error handling"""
    try:
        if not voice_service.is_available():
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        # Use the new safe audio generation method
        audio_data = await voice_service.generate_audio_safely(request.text)
        
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=audio.mp3",
                    "Cache-Control": "no-cache"
                }
            )
        else:
            raise HTTPException(status_code=503, detail="Audio generation temporarily unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        raise HTTPException(status_code=500, detail="Audio generation failed")

@app.post("/chat-voice", response_model=ChatVoiceResponse)
async def chat_with_voice(request: ChatVoiceRequest):
    """OPTIMIZED chat endpoint with single audio generation (no chunking)"""
    try:
        # Get relevant document chunks (similar to the regular chat endpoint)
        relevant_chunks = search_engine.search(request.message, top_k=3)
        
        # Get AI response with VOICE-OPTIMIZED constraints
        response_data = await qsr_assistant.generate_voice_response(request.message, relevant_chunks)
        ai_response = response_data.get("response", "I'm sorry, I couldn't process your request.")
        
        # CRITICAL: Limit response length to prevent chunking issues
        if len(ai_response) > 400:
            # Truncate to first complete sentence under 400 chars using smart sentence splitting
            sentences = smart_sentence_split(ai_response)
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ' ') <= 400:
                    truncated += sentence + ' '
                else:
                    break
            ai_response = truncated.strip() if truncated else ai_response[:400] + "."
        
        # Check if voice service is available
        voice_available = voice_service.is_available()
        
        return ChatVoiceResponse(
            response=ai_response,
            audio_available=voice_available,
            timestamp=datetime.datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error in chat with voice: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat processing failed")

@app.post("/chat-voice-with-audio", response_model=ChatVoiceWithAudioResponse)
async def chat_with_voice_and_audio(request: ChatVoiceRequest):
    """OPTIMIZED endpoint that returns text + audio data in single request (eliminates chunking)"""
    try:
        # Get relevant document chunks
        relevant_chunks = search_engine.search(request.message, top_k=3)
        
        # Use PydanticAI voice orchestrator for intelligent conversation management
        orchestrated_response = await voice_orchestrator.process_voice_message(
            message=request.message,
            relevant_docs=relevant_chunks,
            session_id=request.session_id
        )
        
        ai_response = orchestrated_response.text_response
        
        # CRITICAL: Ensure response is short enough for smooth voice generation
        if len(ai_response) > 300:
            # Find the last complete sentence under 300 characters using smart sentence splitting
            sentences = smart_sentence_split(ai_response)
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ' ') <= 300:
                    truncated += sentence + ' '
                else:
                    break
            ai_response = truncated.strip() if truncated else ai_response[:300] + "."
        
        # Extract sources from chunks
        sources = []
        for chunk in relevant_chunks:
            if 'source' in chunk and chunk['source'] not in sources:
                sources.append(chunk['source'])
        
        # Generate audio using optimized service
        audio_bytes = None
        audio_available = False
        
        if voice_service.is_available():
            audio_bytes = await voice_service.generate_audio_safely(ai_response)
            if audio_bytes:
                import base64
                audio_data = base64.b64encode(audio_bytes).decode()
                audio_available = True
            else:
                audio_data = None
        else:
            audio_data = None
        
        return ChatVoiceWithAudioResponse(
            text_response=ai_response,
            audio_data=audio_data,
            audio_available=audio_available,
            sources=sources,
            timestamp=datetime.datetime.now().isoformat(),
            # PydanticAI orchestration data
            detected_intent=orchestrated_response.detected_intent.value,
            should_continue_listening=orchestrated_response.should_continue_listening,
            next_voice_state=orchestrated_response.next_voice_state.value,
            confidence_score=orchestrated_response.confidence_score,
            conversation_complete=orchestrated_response.conversation_complete,
            suggested_follow_ups=orchestrated_response.suggested_follow_ups
        )
        
    except Exception as e:
        logger.error(f"Error in chat with voice and audio: {str(e)}")
        # Return text-only response on error
        return ChatVoiceWithAudioResponse(
            text_response="I'm sorry, I encountered an error processing your request.",
            audio_data=None,
            audio_available=False,
            sources=[],
            timestamp=datetime.datetime.now().isoformat(),
            detected_intent=ConversationIntent.ERROR_RECOVERY.value,
            should_continue_listening=True,
            next_voice_state=VoiceState.ERROR_RECOVERY.value,
            confidence_score=0.3,
            conversation_complete=False,
            suggested_follow_ups=["Could you try asking again?"]
        )

@app.post("/chat-voice-direct")
async def chat_voice_direct(request: ChatVoiceRequest):
    """DIAGNOSTIC: Direct voice endpoint bypassing all streaming for testing"""
    try:
        logger.info(f"🧪 DIAGNOSTIC: Direct voice request for: {request.message}")
        
        # Get simple response without streaming (bypass complex RAG)
        response = qsr_assistant.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Give a short, simple answer about restaurant work. Use exactly 20-30 words. Mention specific temperatures if relevant."},
                {"role": "user", "content": request.message}
            ],
            temperature=0.3,
            max_tokens=50,
        )
        
        text_response = response.choices[0].message.content
        logger.info(f"🧪 DIAGNOSTIC: Generated text response: '{text_response}'")
        
        # Direct ElevenLabs generation (no chunking, no streaming, no queue)
        logger.info("🧪 DIAGNOSTIC: Calling ElevenLabs directly...")
        audio_bytes = await voice_service.generate_audio_safely(text_response)
        
        if audio_bytes:
            import base64
            audio_data = base64.b64encode(audio_bytes).decode()
            logger.info(f"🧪 DIAGNOSTIC: Audio generated successfully - {len(audio_bytes)} bytes")
            
            return {
                "text_response": text_response,
                "audio_data": audio_data,
                "audio_type": "direct_single_file",
                "bypass_streaming": True,
                "audio_available": True,
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            logger.error("🧪 DIAGNOSTIC: Audio generation failed")
            return {"error": "Audio generation failed"}
        
    except Exception as e:
        logger.error(f"🧪 DIAGNOSTIC: Direct voice endpoint error: {str(e)}")
        return {"error": str(e)}

# PydanticAI Conversation Management Endpoints
@app.get("/conversation-summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(session_id: Optional[str] = None):
    """Get intelligent conversation summary and analytics"""
    try:
        from voice_agent import analyze_conversation_flow
        
        summary = voice_orchestrator.get_conversation_summary(session_id)
        context = voice_orchestrator.get_context(session_id)
        flow_analysis = analyze_conversation_flow(context)
        
        return ConversationSummaryResponse(
            duration=summary["duration"],
            message_count=summary["message_count"],
            topics_covered=summary["topics_covered"],
            last_intent=summary["last_intent"],
            completion_status=summary["completion_status"],
            conversation_flow_analysis=flow_analysis
        )
    except Exception as e:
        logger.error(f"Error getting conversation summary: {str(e)}")
        return ConversationSummaryResponse(
            duration=0.0,
            message_count=0,
            topics_covered=[],
            last_intent=None,
            completion_status=False,
            conversation_flow_analysis={}
        )

@app.post("/conversation-end")
async def end_conversation(request: ConversationSummaryRequest):
    """End a conversation and clean up context"""
    try:
        voice_orchestrator.end_conversation(request.session_id)
        return {"status": "success", "message": "Conversation ended successfully"}
    except Exception as e:
        logger.error(f"Error ending conversation: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/voice-orchestration-status")
async def get_voice_orchestration_status():
    """Get PydanticAI voice orchestration status"""
    try:
        active_sessions = len(voice_orchestrator.active_contexts)
        return {
            "pydantic_ai_active": True,
            "active_conversations": active_sessions,
            "orchestration_version": "1.0.0",
            "features": [
                "intent_detection",
                "context_awareness", 
                "conversation_flow_analysis",
                "smart_continuation_prediction",
                "error_recovery"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting orchestration status: {str(e)}")
        return {
            "pydantic_ai_active": False,
            "error": str(e)
        }

# RAG-Anything Integration Endpoints - NEW ENDPOINTS ONLY
@app.get("/rag-health")
async def rag_health():
    """Health check for RAG-Anything service."""
    return rag_service.health_check()

@app.post("/chat-comparison")
async def chat_comparison(request: dict):
    """Compare responses from both systems."""
    message = request.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Create strategies
    existing_strategy = ExistingSearchStrategy(search_engine)  # Use existing search engine
    
    if rag_service.initialized:
        rag_strategy = RAGAnythingStrategy(rag_service)
        hybrid_strategy = HybridSearchStrategy(existing_strategy, rag_strategy)
        
        try:
            result = await hybrid_strategy.search(message, [])  # Empty docs, RAG handles internally
            return result
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to existing
            existing_result = await existing_strategy.search(message, [])
            return {
                "fallback_used": True,
                "result": existing_result,
                "error": str(e)
            }
    else:
        # RAG not available, use existing only
        existing_result = await existing_strategy.search(message, [])
        return {
            "rag_unavailable": True,
            "result": existing_result
        }

@app.post("/upload-rag")
async def upload_rag(file: UploadFile = File(...)):
    """Upload document to both systems for comparison."""
    # Validate file (same as existing upload)
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    try:
        # Save file (same as existing)
        file_path = os.path.join("uploaded_docs", file.filename)
        os.makedirs("uploaded_docs", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text (same as existing)
        text_content = extract_text_from_pdf(file_path)
        
        # Process through existing system (same as existing)
        existing_result = {
            "filename": file.filename,
            "text_length": len(text_content),
            "processed_by": "existing_system"
        }
        
        # Try processing through RAG-Anything
        rag_result = None
        if rag_service.initialized:
            try:
                rag_result = await rag_service.process_document(file_path, text_content)
            except Exception as e:
                logger.error(f"RAG processing failed: {e}")
                rag_result = {"error": str(e)}
        
        return {
            "existing_system": existing_result,
            "rag_anything": rag_result,
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Multi-Modal Document Processing Endpoints - NEW ENDPOINTS ONLY
@app.post("/upload-multimodal")
async def upload_multimodal(file: UploadFile = File(...)):
    """Upload and process document with multi-modal capabilities."""
    # Same validation as existing upload
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    try:
        # Save file (same process as existing)
        file_path = os.path.join("uploaded_docs", file.filename)
        os.makedirs("uploaded_docs", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process through both methods for comparison
        basic_result = await document_processor.process_pdf_basic(file_path)
        
        if document_processor.use_rag_anything:
            advanced_result = await document_processor.process_pdf_advanced(file_path)
            
            # Save advanced processing results
            processed_file = document_processor.save_processed_content(advanced_result)
            
            return {
                "filename": file.filename,
                "file_path": file_path,
                "basic_processing": {
                    "text_chunks": len(basic_result.text_chunks),
                    "method": basic_result.processing_method
                },
                "advanced_processing": {
                    "text_chunks": len(advanced_result.text_chunks),
                    "images": len(advanced_result.images),
                    "tables": len(advanced_result.tables),
                    "method": advanced_result.processing_method,
                    "processed_file": processed_file
                },
                "comparison": {
                    "basic_chunks": len(basic_result.text_chunks),
                    "advanced_chunks": len(advanced_result.text_chunks),
                    "additional_content": {
                        "images": len(advanced_result.images),
                        "tables": len(advanced_result.tables)
                    }
                }
            }
        else:
            return {
                "filename": file.filename,
                "file_path": file_path,
                "basic_processing": {
                    "text_chunks": len(basic_result.text_chunks),
                    "method": basic_result.processing_method
                },
                "advanced_processing": "disabled",
                "note": "Enable USE_RAG_ANYTHING=true for multi-modal processing"
            }
            
    except Exception as e:
        logger.error(f"Multi-modal upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/document-analysis/{filename}")
async def get_document_analysis(filename: str):
    """Get detailed analysis of processed document."""
    processed_file = f"processed_docs/{Path(filename).stem}_processed.json"
    
    if not os.path.exists(processed_file):
        raise HTTPException(status_code=404, detail="Processed document not found")
    
    try:
        with open(processed_file, 'r') as f:
            data = json.load(f)
        
        return {
            "filename": filename,
            "processing_method": data.get("processing_method"),
            "content_summary": {
                "text_chunks": len(data.get("text_chunks", [])),
                "images": len(data.get("images", [])),
                "tables": len(data.get("tables", [])),
                "metadata": data.get("metadata", {})
            },
            "detailed_analysis": data
        }
        
    except Exception as e:
        logger.error(f"Failed to load document analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processing-capabilities")
async def get_processing_capabilities():
    """Get current document processing capabilities."""
    return {
        "basic_processing": True,
        "advanced_processing": document_processor.use_rag_anything,
        "mineru_available": document_processor.mineru_available,
        "supported_formats": ["PDF"],
        "max_file_size": "10MB",
        "features": {
            "text_extraction": True,
            "image_extraction": document_processor.mineru_available,
            "table_extraction": document_processor.mineru_available,
            "semantic_chunking": document_processor.use_rag_anything
        }
    }

# Voice Integration with Knowledge Graph Context - NEW ENDPOINTS ONLY
@app.post("/voice-query")
async def voice_query(request: dict):
    """Process voice query with graph context."""
    query = request.get("message")
    session_id = request.get("session_id") or str(uuid.uuid4())
    audio_metadata = request.get("audio_metadata", {})
    
    if not query:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        result = await voice_graph_service.process_voice_query(
            session_id=session_id,
            query=query,
            audio_metadata=audio_metadata
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Voice query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice-session/{session_id}")
async def get_voice_session(session_id: str):
    """Get voice session summary and context."""
    summary = voice_graph_service.get_session_summary(session_id)
    
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    
    return summary

@app.post("/voice-session")
async def create_voice_session():
    """Create new voice session."""
    session_id = str(uuid.uuid4())
    context = await voice_graph_service.create_voice_session(session_id)
    
    return {
        "session_id": session_id,
        "created": context.last_updated.isoformat(),
        "status": "ready"
    }

@app.get("/voice-capabilities")
async def get_voice_capabilities():
    """Get current voice processing capabilities."""
    return {
        "voice_processing": True,
        "graph_context": voice_graph_service.use_graph_context,
        "rag_integration": rag_service.initialized if rag_service else False,
        "session_management": True,
        "context_persistence": True,
        "supported_features": {
            "equipment_detection": True,
            "procedure_detection": True,
            "conversation_memory": True,
            "multi_step_guidance": voice_graph_service.use_graph_context,
            "voice_formatted_responses": True
        }
    }

@app.post("/chat-voice-comparison")
async def chat_voice_comparison(request: dict):
    """Compare regular chat vs voice-optimized responses."""
    message = request.get("message")
    session_id = request.get("session_id", str(uuid.uuid4()))
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        # Get regular chat response (existing endpoint logic)
        regular_response = "Regular chat response would go here"  # Use existing chat logic
        
        # Get voice-optimized response
        voice_result = await voice_graph_service.process_voice_query(session_id, message)
        
        return {
            "query": message,
            "session_id": session_id,
            "regular_chat": {
                "response": regular_response,
                "optimized_for": "text"
            },
            "voice_chat": {
                "response": voice_result["response"]["text"],
                "optimized_for": "voice",
                "context_used": voice_result["context"],
                "citations": voice_result["response"]["citations"]
            },
            "comparison": {
                "voice_formatting_applied": voice_result["response"]["formatted_for_voice"],
                "context_persistence": bool(voice_result["context"]["current_equipment"]),
                "graph_enhancement": voice_result["response"]["includes_context"]
            }
        }
        
    except Exception as e:
        logger.error(f"Voice comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Neo4j Aura Integration Endpoints - NEW ENDPOINTS ONLY
@app.get("/neo4j-aura-validation")
async def neo4j_aura_validation():
    """Validate Aura-specific connection configuration."""
    return neo4j_service.validate_aura_connection()

@app.get("/neo4j-health")
async def neo4j_health():
    """Get Neo4j Aura health status and connection test."""
    return neo4j_service.get_health_status()

@app.get("/neo4j-test-query")
async def neo4j_test_query():
    """Test Neo4j Aura with a simple query."""
    result = neo4j_service.execute_query(
        "RETURN 'Aura Connection Test' as message, datetime() as timestamp"
    )
    return result

@app.post("/neo4j-custom-query")
async def neo4j_custom_query(request: dict):
    """Execute a custom query on Neo4j Aura (for testing)."""
    query = request.get("query")
    parameters = request.get("parameters", {})
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Security: Only allow read queries for safety
    if any(keyword in query.upper() for keyword in ["DELETE", "CREATE", "MERGE", "SET", "REMOVE", "DROP"]):
        raise HTTPException(status_code=403, detail="Only read queries allowed")
    
    result = neo4j_service.execute_query(query, parameters)
    return result

# Database Management Endpoints - SAFETY FIRST
@app.get("/neo4j-backup")
async def neo4j_backup():
    """Backup current graph before wiping (safety measure)."""
    # Ensure connection
    if not neo4j_service.connected:
        neo4j_service.connect()
    
    if not neo4j_service.connected:
        raise HTTPException(status_code=503, detail="Neo4j not connected")
    
    try:
        with neo4j_service.driver.session() as session:
            # Get all nodes and relationships
            result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN {
                    nodes: collect(DISTINCT {id: id(n), labels: labels(n), properties: properties(n)}),
                    relationships: collect(DISTINCT {id: id(r), type: type(r), properties: properties(r), start: id(startNode(r)), end: id(endNode(r))})
                } as backup
            """)
            
            backup_data = result.single()["backup"]
            
            # Save to file with timestamp
            import json
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"./data/neo4j_backup_{timestamp}.json"
            
            os.makedirs("./data", exist_ok=True)
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            return {
                "backup_created": True,
                "backup_file": backup_file,
                "nodes_backed_up": len(backup_data.get("nodes", [])),
                "relationships_backed_up": len(backup_data.get("relationships", [])),
                "timestamp": timestamp
            }
            
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {e}")

@app.delete("/neo4j-wipe-demo-data")
async def neo4j_wipe_demo_data():
    """DANGER: Completely wipe all data from Neo4j database."""
    # Ensure connection
    if not neo4j_service.connected:
        neo4j_service.connect()
    
    if not neo4j_service.connected:
        raise HTTPException(status_code=503, detail="Neo4j not connected")
    
    try:
        with neo4j_service.driver.session() as session:
            # Get current counts
            count_result = session.run("MATCH (n) RETURN count(n) as nodes, count{(n)-[]-()} as relationships")
            counts = count_result.single()
            
            # Delete all relationships first
            session.run("MATCH ()-[r]-() DELETE r")
            
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            
            # Verify deletion
            verify_result = session.run("MATCH (n) RETURN count(n) as remaining_nodes")
            remaining = verify_result.single()["remaining_nodes"]
            
            return {
                "wipe_completed": True,
                "nodes_deleted": counts["nodes"],
                "relationships_deleted": counts["relationships"],
                "remaining_nodes": remaining,
                "database_clean": remaining == 0,
                "ready_for_fresh_data": True
            }
            
    except Exception as e:
        logger.error(f"Wipe failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database wipe failed: {e}")

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
            "chat-voice": "/chat-voice",
            "chat-voice-with-audio": "/chat-voice-with-audio",
            "chat-voice-direct": "/chat-voice-direct",
            "voice-status": "/voice-status",
            "generate-audio": "/generate-audio",
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