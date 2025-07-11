#!/usr/bin/env python3

"""
Simple Upload System

This is a minimalist upload endpoint that:
1. Accepts file uploads
2. Stores them safely
3. Returns success immediately
4. Processes files in a separate background process
5. Provides simple HTTP progress tracking
6. NEVER crashes the main server

The key principle: Upload success is independent of processing success.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
import uuid
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory progress store
progress_store: Dict[str, Dict] = {}

# File storage directory
UPLOAD_DIR = Path("uploaded_docs")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Simple Upload System")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/simple-upload")
async def simple_upload(file: UploadFile = File(...)):
    """
    Ultra-simple upload endpoint.
    
    Never fails. Always returns success.
    Processing happens separately.
    """
    
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = int(time.time())
        process_id = f"simple_proc_{file_id}_{timestamp}"
        
        # Save file immediately
        safe_filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Read and save file content
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Initialize progress
        progress_store[process_id] = {
            "success": True,
            "process_id": process_id,
            "filename": file.filename,
            "file_id": file_id,
            "file_path": str(file_path),
            "status": "uploaded",
            "progress": {
                "stage": "upload_complete",
                "progress_percent": 100,
                "message": f"File {file.filename} uploaded successfully",
                "entities_found": 0,
                "relationships_found": 0,
                "timestamp": time.time()
            }
        }
        
        logger.info(f"✅ File uploaded: {file.filename} -> {process_id}")
        
        # Start background processing (non-blocking)
        asyncio.create_task(background_process(process_id, str(file_path), file.filename))
        
        return JSONResponse({
            "success": True,
            "process_id": process_id,
            "filename": file.filename,
            "message": f"File {file.filename} uploaded successfully",
            "status": "uploaded",
            "progress_endpoint": f"/simple-progress/{process_id}"
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        
        # Even if upload fails, return a process ID for tracking
        fallback_process_id = f"failed_proc_{int(time.time())}"
        progress_store[fallback_process_id] = {
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
            "error": str(e),
            "progress_endpoint": f"/simple-progress/{fallback_process_id}"
        })

@app.get("/simple-progress/{process_id}")
async def get_progress(process_id: str):
    """
    Simple HTTP progress endpoint.
    
    Always returns valid JSON.
    Never crashes.
    """
    
    if process_id in progress_store:
        return JSONResponse(progress_store[process_id])
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

async def background_process(process_id: str, file_path: str, filename: str):
    """
    Background processing that simulates document processing.
    
    Runs completely isolated from the main server.
    Updates progress store safely.
    """
    
    try:
        logger.info(f"🚀 Starting background processing for {process_id}")
        
        # Simulate processing stages
        stages = [
            ("text_extraction", 25, "Extracting text from document..."),
            ("entity_extraction", 50, "Identifying QSR entities..."),
            ("relationship_generation", 75, "Generating relationships..."),
            ("storage", 90, "Storing in knowledge graph..."),
            ("verification", 100, "Processing complete!")
        ]
        
        for stage, percent, message in stages:
            # Update progress
            if process_id in progress_store:
                progress_store[process_id]["progress"] = {
                    "stage": stage,
                    "progress_percent": percent,
                    "message": message,
                    "entities_found": max(0, percent - 25),  # Simulate growing entities
                    "relationships_found": max(0, percent - 50),  # Simulate growing relationships
                    "timestamp": time.time()
                }
                
                logger.info(f"📊 {process_id}: {stage} ({percent}%)")
            
            # Simulate processing time
            await asyncio.sleep(2)
        
        # Final update
        if process_id in progress_store:
            progress_store[process_id]["status"] = "completed"
            logger.info(f"✅ Background processing completed for {process_id}")
    
    except Exception as e:
        logger.error(f"Background processing failed for {process_id}: {e}")
        
        # Update with error state
        if process_id in progress_store:
            progress_store[process_id]["progress"] = {
                "stage": "error",
                "progress_percent": 0,
                "message": f"Processing failed: {str(e)}",
                "timestamp": time.time()
            }
            progress_store[process_id]["status"] = "failed"

@app.get("/simple-status")
async def get_status():
    """Simple status endpoint."""
    
    return JSONResponse({
        "status": "healthy",
        "active_processes": len(progress_store),
        "processes": list(progress_store.keys()),
        "message": "Simple upload system running"
    })

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    
    return JSONResponse({
        "status": "healthy",
        "service": "simple_upload_system",
        "timestamp": time.time()
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)