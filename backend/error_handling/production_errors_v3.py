#!/usr/bin/env python3
"""
Production Error Handling v3 - BaseChat Enterprise Patterns
==========================================================

Production-ready error handling for Line Lead's proven architecture,
following BaseChat's error management patterns optimized for Render + Vercel.

Features:
- Service-specific error handling for proven components
- Render platform integration and optimization
- User experience protection with graceful degradation
- Cross-service error coordination
- Performance-based error categorization

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import logging
import traceback
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)

class ServiceError(Enum):
    """Service-specific error categories for Line Lead architecture"""
    PYDANTIC_AGENT_ERROR = "pydantic_agent_error"
    RAGIE_ENHANCEMENT_ERROR = "ragie_enhancement_error" 
    VISUAL_CITATION_ERROR = "visual_citation_error"
    VOICE_PROCESSING_ERROR = "voice_processing_error"
    DATABASE_ERROR = "database_error"
    DOCUMENT_STORAGE_ERROR = "document_storage_error"
    RENDER_PLATFORM_ERROR = "render_platform_error"
    VERCEL_FRONTEND_ERROR = "vercel_frontend_error"
    NETWORK_ERROR = "network_error"

@dataclass
class ErrorContext:
    """Error context for better handling"""
    service: ServiceError
    user_message: str
    recovery_time: str
    fallback_available: bool
    severity: str = "medium"  # "low", "medium", "high", "critical"

class ProductionErrorHandler:
    """Production error handler following BaseChat patterns"""
    
    def __init__(self, app: FastAPI):
        """Initialize production error handling"""
        self.app = app
        self.error_counts = {}
        self.setup_render_vercel_cors()
        self.setup_error_handlers()
        self.setup_error_context_mapping()
        
        logger.info("🛡️ Production error handling initialized with BaseChat patterns")
    
    def setup_render_vercel_cors(self):
        """Optimized CORS for Render ↔ Vercel deployment"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://*.vercel.app",
                "https://line-lead-qsr.vercel.app",  # Production domain
                "https://line-lead-qsr-*.vercel.app",  # Preview deployments
                "http://localhost:3000",  # Development
                "http://localhost:3001",  # Alternative dev port
            ],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=[
                "*",
                "X-Session-ID",
                "X-Health-Check", 
                "X-Heartbeat",
                "tenant"
            ],
            expose_headers=["X-Response-Time", "X-Service-Status"]
        )
        
        logger.info("🌐 Render ↔ Vercel CORS configured")
    
    def setup_error_context_mapping(self):
        """Define error contexts for proven Line Lead services"""
        self.error_contexts = {
            ServiceError.PYDANTIC_AGENT_ERROR: ErrorContext(
                service=ServiceError.PYDANTIC_AGENT_ERROR,
                user_message="AI assistant temporarily unavailable. Our team is working to restore service.",
                recovery_time="2-3 minutes",
                fallback_available=False,
                severity="critical"
            ),
            ServiceError.RAGIE_ENHANCEMENT_ERROR: ErrorContext(
                service=ServiceError.RAGIE_ENHANCEMENT_ERROR,
                user_message="Knowledge enhancement temporarily unavailable. Standard responses are still available.",
                recovery_time="30-60 seconds",
                fallback_available=True,
                severity="low"
            ),
            ServiceError.VISUAL_CITATION_ERROR: ErrorContext(
                service=ServiceError.VISUAL_CITATION_ERROR,
                user_message="Visual content temporarily unavailable. Text responses are still working.",
                recovery_time="30 seconds",
                fallback_available=True,
                severity="low"
            ),
            ServiceError.VOICE_PROCESSING_ERROR: ErrorContext(
                service=ServiceError.VOICE_PROCESSING_ERROR,
                user_message="Voice features temporarily unavailable. Please use text chat.",
                recovery_time="1-2 minutes",
                fallback_available=True,
                severity="medium"
            ),
            ServiceError.DATABASE_ERROR: ErrorContext(
                service=ServiceError.DATABASE_ERROR,
                user_message="Conversation history temporarily unavailable. Current session will work normally.",
                recovery_time="2-3 minutes",
                fallback_available=True,
                severity="medium"
            ),
            ServiceError.RENDER_PLATFORM_ERROR: ErrorContext(
                service=ServiceError.RENDER_PLATFORM_ERROR,
                user_message="Service temporarily unavailable due to platform maintenance.",
                recovery_time="3-5 minutes",
                fallback_available=False,
                severity="high"
            )
        }
    
    def setup_error_handlers(self):
        """Setup comprehensive error handlers"""
        
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """Global exception handler with service-specific categorization"""
            start_time = time.time()
            
            # Log error for Render logging system
            error_id = f"error_{int(time.time() * 1000)}"
            logger.error(f"🚨 Global error {error_id} in {request.url.path}: {traceback.format_exc()}")
            
            # Categorize error and get context
            error_type, context = self._categorize_error(exc, request)
            
            # Update error tracking
            self._track_error(error_type)
            
            # Create response based on error context
            response_data = {
                "error": "service_temporarily_unavailable",
                "error_id": error_id,
                "message": context.user_message,
                "service": "line-lead-qsr-assistant",
                "deployment": "render",
                "timestamp": datetime.now().isoformat(),
                "recovery_estimate": context.recovery_time,
                "fallback_available": context.fallback_available,
                "severity": context.severity,
                "request_path": str(request.url.path)
            }
            
            # Add performance context
            response_time = (time.time() - start_time) * 1000
            response_data["response_time_ms"] = round(response_time, 2)
            
            # Determine HTTP status based on severity
            status_code = self._get_status_code(context.severity)
            
            # Add appropriate headers for frontend handling
            headers = {
                "X-Error-Type": error_type.value,
                "X-Fallback-Available": str(context.fallback_available).lower(),
                "X-Service-Status": "degraded" if context.fallback_available else "unavailable"
            }
            
            return JSONResponse(
                status_code=status_code,
                content=response_data,
                headers=headers
            )
        
        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            """Handle request validation errors"""
            logger.warning(f"⚠️ Validation error on {request.url.path}: {exc}")
            
            return JSONResponse(
                status_code=422,
                content={
                    "error": "validation_error",
                    "message": "Invalid request format. Please check your input and try again.",
                    "details": exc.errors(),
                    "service": "line-lead-qsr-assistant",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions with user-friendly messages"""
            user_messages = {
                404: "The requested resource was not found.",
                403: "Access denied. Please check your permissions.",
                401: "Authentication required.",
                429: "Too many requests. Please wait before trying again.",
                500: "Internal server error. Our team has been notified."
            }
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": f"http_{exc.status_code}",
                    "message": user_messages.get(exc.status_code, exc.detail),
                    "service": "line-lead-qsr-assistant",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    def _categorize_error(self, exc: Exception, request: Request) -> tuple[ServiceError, ErrorContext]:
        """Categorize error based on proven Line Lead architecture"""
        error_str = str(exc).lower()
        path = str(request.url.path).lower()
        
        # PydanticAI orchestration errors (critical - core functionality)
        if any(keyword in error_str for keyword in ["pydantic", "agent", "orchestrator"]):
            return ServiceError.PYDANTIC_AGENT_ERROR, self.error_contexts[ServiceError.PYDANTIC_AGENT_ERROR]
        
        # Ragie enhancement errors (low severity - graceful fallback)
        if any(keyword in error_str for keyword in ["ragie", "enhancement"]) or "/ragie" in path:
            return ServiceError.RAGIE_ENHANCEMENT_ERROR, self.error_contexts[ServiceError.RAGIE_ENHANCEMENT_ERROR]
        
        # Visual citation errors (low severity - text fallback)
        if any(keyword in error_str for keyword in ["citation", "visual", "image"]) or "/visual" in path:
            return ServiceError.VISUAL_CITATION_ERROR, self.error_contexts[ServiceError.VISUAL_CITATION_ERROR]
        
        # Voice processing errors (medium severity - text fallback)
        if any(keyword in error_str for keyword in ["voice", "audio", "speech"]) or "/voice" in path:
            return ServiceError.VOICE_PROCESSING_ERROR, self.error_contexts[ServiceError.VOICE_PROCESSING_ERROR]
        
        # Database errors (medium severity - session memory fallback)
        if any(keyword in error_str for keyword in ["database", "connection", "pool", "sql"]):
            return ServiceError.DATABASE_ERROR, self.error_contexts[ServiceError.DATABASE_ERROR]
        
        # Document storage errors
        if any(keyword in error_str for keyword in ["document", "upload", "file"]) or "/documents" in path:
            context = ErrorContext(
                service=ServiceError.DOCUMENT_STORAGE_ERROR,
                user_message="Document processing temporarily unavailable. Please try again.",
                recovery_time="1-2 minutes",
                fallback_available=True,
                severity="medium"
            )
            return ServiceError.DOCUMENT_STORAGE_ERROR, context
        
        # Network/timeout errors
        if any(keyword in error_str for keyword in ["timeout", "network", "connection refused", "unreachable"]):
            context = ErrorContext(
                service=ServiceError.NETWORK_ERROR,
                user_message="Network connectivity issue. Please check your connection and try again.",
                recovery_time="1 minute",
                fallback_available=True,
                severity="medium"
            )
            return ServiceError.NETWORK_ERROR, context
        
        # Default to platform error
        return ServiceError.RENDER_PLATFORM_ERROR, self.error_contexts[ServiceError.RENDER_PLATFORM_ERROR]
    
    def _track_error(self, error_type: ServiceError):
        """Track error counts for monitoring"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Log high error rates
        if self.error_counts[error_type] % 10 == 0:
            logger.warning(f"🚨 High error rate for {error_type.value}: {self.error_counts[error_type]} occurrences")
    
    def _get_status_code(self, severity: str) -> int:
        """Get HTTP status code based on error severity"""
        status_codes = {
            "low": 503,      # Service Unavailable (temporary)
            "medium": 503,   # Service Unavailable
            "high": 503,     # Service Unavailable  
            "critical": 500  # Internal Server Error
        }
        return status_codes.get(severity, 500)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_errors": total_errors,
            "error_breakdown": {error_type.value: count for error_type, count in self.error_counts.items()},
            "error_rate_by_service": {
                error_type.value: {
                    "count": count,
                    "percentage": round((count / total_errors) * 100, 2) if total_errors > 0 else 0
                }
                for error_type, count in self.error_counts.items()
            },
            "timestamp": datetime.now().isoformat()
        }

# Service-specific error handlers for proven Line Lead components
class ServiceSpecificErrorHandlers:
    """Specific error handlers for each Line Lead service"""
    
    @staticmethod
    async def handle_ragie_enhancement_error(error: Exception) -> Dict[str, Any]:
        """Handle Ragie enhancement errors with graceful fallback"""
        logger.warning(f"⚠️ Ragie enhancement error: {error}")
        
        return {
            "enhancement_status": "unavailable",
            "fallback_active": True,
            "fallback_type": "standard_qsr_responses",
            "message": "Using standard QSR knowledge",
            "recovery_time": "30-60 seconds",
            "error_handled": True
        }
    
    @staticmethod
    async def handle_voice_processing_error(error: Exception) -> Dict[str, Any]:
        """Handle voice processing errors with text chat fallback"""
        logger.warning(f"⚠️ Voice processing error: {error}")
        
        return {
            "voice_status": "unavailable", 
            "text_chat_available": True,
            "fallback_active": True,
            "message": "Please use text chat temporarily",
            "recovery_time": "1-2 minutes",
            "error_handled": True
        }
    
    @staticmethod
    async def handle_visual_citation_error(error: Exception) -> Dict[str, Any]:
        """Handle visual citation errors with text-only fallback"""
        logger.warning(f"⚠️ Visual citation error: {error}")
        
        return {
            "visual_status": "unavailable",
            "text_response_available": True,
            "fallback_active": True,
            "message": "Visual content temporarily unavailable",
            "recovery_time": "30 seconds",
            "error_handled": True
        }
    
    @staticmethod
    async def handle_database_error(error: Exception) -> Dict[str, Any]:
        """Handle database errors with session memory fallback"""
        logger.warning(f"⚠️ Database error: {error}")
        
        return {
            "database_status": "unavailable",
            "session_memory_active": True,
            "conversation_history_status": "unavailable",
            "fallback_active": True,
            "message": "Conversation history temporarily unavailable",
            "recovery_time": "2-3 minutes",
            "error_handled": True
        }

def setup_production_error_handling(app: FastAPI) -> ProductionErrorHandler:
    """Setup production error handling for Line Lead"""
    error_handler = ProductionErrorHandler(app)
    
    # Add error stats endpoint
    @app.get("/health/errors")
    async def get_error_statistics():
        """Get error handling statistics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "error_statistics": error_handler.get_error_stats(),
            "service": "line-lead-error-handling"
        }
    
    logger.info("🛡️ Production error handling setup complete")
    return error_handler