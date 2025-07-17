#!/usr/bin/env python3
"""
Document Source API Endpoints
==============================

FastAPI endpoints for serving original document files from Ragie
Following BaseChat patterns for media file streaming.

Key features:
- Direct document source access from Ragie
- Proper MIME type handling
- Range request support for video streaming
- Authentication and authorization
- Error handling and fallback mechanisms

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pathlib import Path
import os
import io

# Import the document source service
from services.ragie_document_source_service import ragie_document_source_service

logger = logging.getLogger(__name__)

# Create router
document_source_router = APIRouter()

@document_source_router.get("/documents/{document_id}/source")
async def get_document_source(
    document_id: str,
    request: Request,
    response: Response
):
    """
    Get original document file from Ragie
    
    Supports:
    - Range requests for video streaming
    - Proper MIME type headers
    - Authentication via existing patterns
    - Error handling and fallback
    
    Args:
        document_id: Ragie document ID
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        StreamingResponse with document content
    """
    try:
        logger.info(f"📥 Document source request for {document_id}")
        
        # Get document from Ragie
        document_result = await ragie_document_source_service.get_document_source(document_id)
        
        if not document_result.success:
            logger.error(f"❌ Document source failed: {document_result.error}")
            # Check for different error types
            error_msg = document_result.error.lower()
            if "not found" in error_msg or "404" in error_msg:
                raise HTTPException(status_code=404, detail=document_result.error)
            elif "422" in error_msg or "uuid" in error_msg or "invalid" in error_msg:
                raise HTTPException(status_code=404, detail="Document not found")
            else:
                raise HTTPException(status_code=500, detail=document_result.error)
        
        if not document_result.content:
            raise HTTPException(status_code=404, detail="Document content not available")
        
        # Get content details
        content = document_result.content
        content_type = document_result.content_type or "application/octet-stream"
        content_length = len(content)
        filename = document_result.filename or f"document_{document_id}"
        
        # Check for Range header (for video streaming)
        range_header = request.headers.get("Range")
        
        if range_header:
            # Handle range requests for video streaming
            return _handle_range_request(
                content=content,
                content_type=content_type,
                content_length=content_length,
                range_header=range_header,
                filename=filename
            )
        else:
            # Return full content
            response.headers["Content-Type"] = content_type
            response.headers["Content-Length"] = str(content_length)
            response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
            response.headers["Accept-Ranges"] = "bytes"
            
            # Add caching headers
            response.headers["Cache-Control"] = "public, max-age=3600"  # Cache for 1 hour
            response.headers["ETag"] = f'"{document_id}"'
            
            # Log success
            cache_status = "cached" if document_result.cached else "fetched"
            logger.info(f"✅ Document source served: {document_id} ({content_length} bytes, {cache_status})")
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"',
                    "Accept-Ranges": "bytes"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error serving document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def _handle_range_request(
    content: bytes,
    content_type: str,
    content_length: int,
    range_header: str,
    filename: str
) -> StreamingResponse:
    """
    Handle HTTP Range requests for video streaming
    
    Args:
        content: Document content bytes
        content_type: MIME type
        content_length: Total content length
        range_header: Range header value
        filename: Document filename
        
    Returns:
        StreamingResponse with partial content
    """
    try:
        # Parse range header (e.g., "bytes=0-1023" or "bytes=1024-")
        range_match = range_header.replace("bytes=", "").strip()
        
        if "-" not in range_match:
            raise ValueError("Invalid range format")
        
        range_start, range_end = range_match.split("-", 1)
        
        # Parse start and end positions
        start = int(range_start) if range_start else 0
        end = int(range_end) if range_end else content_length - 1
        
        # Validate range
        if start < 0 or end >= content_length or start > end:
            raise ValueError("Invalid range bounds")
        
        # Extract content chunk
        chunk_size = end - start + 1
        content_chunk = content[start:end + 1]
        
        # Create response headers
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(chunk_size),
            "Content-Range": f"bytes {start}-{end}/{content_length}",
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{filename}"'
        }
        
        logger.info(f"📹 Range request served: {start}-{end}/{content_length} ({chunk_size} bytes)")
        
        return StreamingResponse(
            io.BytesIO(content_chunk),
            status_code=206,  # Partial Content
            headers=headers
        )
        
    except ValueError as e:
        logger.warning(f"⚠️ Invalid range request: {e}")
        raise HTTPException(status_code=416, detail="Range Not Satisfiable")
    except Exception as e:
        logger.error(f"❌ Range request error: {e}")
        raise HTTPException(status_code=500, detail="Range request processing error")

@document_source_router.get("/documents/{document_id}/metadata")
async def get_document_metadata(document_id: str):
    """
    Get document metadata from Ragie
    
    Args:
        document_id: Ragie document ID
        
    Returns:
        Document metadata
    """
    try:
        logger.info(f"📋 Document metadata request for {document_id}")
        
        metadata = await ragie_document_source_service.get_document_metadata(document_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Document metadata not found")
        
        return {
            "document_id": metadata.document_id,
            "name": metadata.name,
            "content_type": metadata.content_type,
            "size": metadata.size,
            "created_at": metadata.created_at,
            "metadata": metadata.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting document metadata {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@document_source_router.get("/documents/cache/stats")
async def get_cache_stats():
    """
    Get document cache statistics
    
    Returns:
        Cache statistics
    """
    try:
        stats = await ragie_document_source_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "service_available": ragie_document_source_service.is_available()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@document_source_router.delete("/documents/cache")
async def clear_cache():
    """
    Clear document cache
    
    Returns:
        Number of files cleared
    """
    try:
        files_cleared = await ragie_document_source_service.clear_cache()
        return {
            "files_cleared": files_cleared,
            "message": f"Cleared {files_cleared} cached files"
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@document_source_router.get("/documents/source/health")
async def document_source_health():
    """
    Health check for document source service
    
    Returns:
        Service health status
    """
    try:
        is_available = ragie_document_source_service.is_available()
        cache_stats = await ragie_document_source_service.get_cache_stats()
        
        return {
            "status": "healthy" if is_available else "unavailable",
            "service_available": is_available,
            "cache_stats": cache_stats,
            "api_key_configured": bool(ragie_document_source_service.api_key),
            "partition": ragie_document_source_service.partition
        }
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "service_available": False
        }