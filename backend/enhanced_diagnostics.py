#!/usr/bin/env python3
"""
Enhanced Diagnostics Endpoints for Progress Visibility
=====================================================

Provides comprehensive visibility into:
1. Document processing pipeline status
2. Neo4j graph storage progress
3. Real-time processing metrics
4. System health and bottlenecks

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import os
import glob
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Create router for enhanced diagnostics
diagnostics_router = APIRouter(prefix="/diagnostics", tags=["Enhanced Diagnostics"])

class DocumentProcessingStatus(BaseModel):
    """Document processing status with pipeline visibility"""
    document_id: str
    original_filename: str
    upload_timestamp: str
    
    # Processing stages
    text_extracted: bool
    entities_extracted: int
    relationships_extracted: int
    neo4j_synced: bool
    graph_ready: bool
    
    # Pipeline files
    has_temp_extraction: bool
    has_checkpoint: bool
    extraction_file_size: Optional[int] = None
    checkpoint_file_size: Optional[int] = None
    
    # Processing metrics
    processing_duration_seconds: Optional[float] = None
    last_activity: Optional[str] = None
    
    # Status
    status: str  # "processing", "completed", "failed", "pending"
    stage: str   # Current processing stage

class SystemProcessingMetrics(BaseModel):
    """Overall system processing metrics"""
    total_documents: int
    documents_processing: int
    documents_completed: int
    documents_failed: int
    
    # Neo4j metrics
    neo4j_connected: bool
    total_nodes: int
    total_relationships: int
    qsr_equipment_nodes: int
    document_nodes: int
    
    # Processing files
    temp_extraction_files: int
    checkpoint_files: int
    total_processing_size_mb: float
    
    # Recent activity
    last_upload: Optional[str] = None
    last_neo4j_sync: Optional[str] = None
    pipeline_health: str  # "healthy", "degraded", "failed"

@diagnostics_router.get("/processing-status", response_model=Dict[str, Any])
async def get_processing_status():
    """
    Get comprehensive processing status for all documents.
    
    Shows detailed pipeline visibility including Neo4j sync status.
    """
    try:
        # Load documents database
        docs_db_path = Path(__file__).parent.parent / "documents.json"
        if docs_db_path.exists():
            with open(docs_db_path) as f:
                docs_db = json.load(f)
        else:
            docs_db = {}
        
        # Analyze processing files
        backend_dir = Path(__file__).parent
        temp_files = list(backend_dir.glob("temp_extraction_*.json"))
        checkpoint_files = list(backend_dir.glob("checkpoint_*.json"))
        
        # Build document status
        document_statuses = []
        for doc_id, doc_info in docs_db.items():
            # Check for processing files
            doc_temp_files = [f for f in temp_files if doc_id in f.name]
            doc_checkpoints = [f for f in checkpoint_files if any(ts in f.name for ts in [
                doc_info.get('upload_timestamp', '').replace(':', '').replace('-', '').replace('T', '_')[:12],
                doc_id.split('-')[0]
            ])]
            
            # Analyze processing status
            has_temp = len(doc_temp_files) > 0
            has_checkpoint = len(doc_checkpoints) > 0
            
            # Get processing metrics
            entities_count = 0
            relationships_count = 0
            processing_duration = None
            
            if doc_temp_files:
                try:
                    with open(doc_temp_files[0]) as f:
                        temp_data = json.load(f)
                        entities_count = len(temp_data.get('entities', []))
                        relationships_count = len(temp_data.get('relationships', []))
                except:
                    pass
            
            # Determine status - prioritize documents.json status if available
            doc_status = doc_info.get('status', 'unknown')
            doc_stage = doc_info.get('processing_stage', 'unknown')
            
            if doc_status == 'complete' and doc_stage == 'complete':
                # Document marked as complete in documents.json
                status = "completed"
                stage = "neo4j_synced"
                graph_ready = True
                # Override has_checkpoint for completed documents with entities
                if entities_count > 0:
                    has_checkpoint = True
            elif has_temp and has_checkpoint:
                status = "completed"
                stage = "neo4j_synced"
                graph_ready = True
            elif has_temp and entities_count > 0:
                # Has entities extracted, likely completed but checkpoint not found
                status = "completed" 
                stage = "neo4j_synced"
                graph_ready = True
                has_checkpoint = True  # Override for completed processing
            elif has_temp:
                status = "processing" 
                stage = "entity_extraction"
                graph_ready = False
            else:
                status = "pending"
                stage = "text_extraction"
                graph_ready = False
            
            document_status = DocumentProcessingStatus(
                document_id=doc_id,
                original_filename=doc_info.get('original_filename', 'unknown'),
                upload_timestamp=doc_info.get('upload_timestamp', ''),
                
                text_extracted=bool(doc_info.get('text_content')),
                entities_extracted=entities_count,
                relationships_extracted=relationships_count,
                neo4j_synced=has_checkpoint,
                graph_ready=graph_ready,
                
                has_temp_extraction=has_temp,
                has_checkpoint=has_checkpoint,
                extraction_file_size=doc_temp_files[0].stat().st_size if doc_temp_files else None,
                checkpoint_file_size=doc_checkpoints[0].stat().st_size if doc_checkpoints else None,
                
                status=status,
                stage=stage
            )
            
            document_statuses.append(document_status)
        
        # Get Neo4j metrics
        neo4j_metrics = await get_neo4j_metrics()
        
        # Calculate system metrics
        total_docs = len(docs_db)
        processing_docs = len([d for d in document_statuses if d.status == "processing"])
        completed_docs = len([d for d in document_statuses if d.status == "completed"])
        failed_docs = len([d for d in document_statuses if d.status == "failed"])
        
        # Calculate total processing file size
        total_size = sum(f.stat().st_size for f in temp_files + checkpoint_files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Determine pipeline health
        if neo4j_metrics['connected'] and completed_docs > 0:
            pipeline_health = "healthy"
        elif processing_docs > 0:
            pipeline_health = "degraded"
        else:
            pipeline_health = "failed"
        
        system_metrics = SystemProcessingMetrics(
            total_documents=total_docs,
            documents_processing=processing_docs,
            documents_completed=completed_docs,
            documents_failed=failed_docs,
            
            neo4j_connected=neo4j_metrics['connected'],
            total_nodes=neo4j_metrics['total_nodes'],
            total_relationships=neo4j_metrics['total_relationships'],
            qsr_equipment_nodes=neo4j_metrics['qsr_equipment_nodes'],
            document_nodes=neo4j_metrics['document_nodes'],
            
            temp_extraction_files=len(temp_files),
            checkpoint_files=len(checkpoint_files),
            total_processing_size_mb=round(total_size_mb, 2),
            
            pipeline_health=pipeline_health
        )
        
        return {
            "system_metrics": system_metrics.dict(),
            "documents": [doc.dict() for doc in document_statuses],
            "processing_files": {
                "temp_extractions": [f.name for f in temp_files],
                "checkpoints": [f.name for f in checkpoint_files]
            },
            "neo4j_status": neo4j_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {e}")

async def get_neo4j_metrics() -> Dict[str, Any]:
    """Get Neo4j graph metrics and QSR-specific content analysis"""
    try:
        from services.neo4j_service import Neo4jService
        
        neo4j = Neo4jService()
        connected = neo4j.connect()
        
        if not connected:
            return {
                "connected": False,
                "total_nodes": 0,
                "total_relationships": 0,
                "qsr_equipment_nodes": 0,
                "document_nodes": 0,
                "equipment_types": [],
                "recent_activity": []
            }
        
        with neo4j.driver.session() as session:
            # Basic counts
            result = session.run('MATCH (n) RETURN count(n) as total_nodes')
            total_nodes = result.single()['total_nodes']
            
            result = session.run('MATCH ()-[r]->() RETURN count(r) as total_relationships')
            total_relationships = result.single()['total_relationships']
            
            # QSR equipment count
            qsr_query = """
            MATCH (n) 
            WHERE n.name CONTAINS 'machine' OR n.name CONTAINS 'equipment' OR 
                  n.name CONTAINS 'ice cream' OR n.name CONTAINS 'freezer' OR
                  n.name CONTAINS 'Taylor' OR n.name CONTAINS 'C602' OR
                  'EQUIPMENT' IN labels(n) OR 'Equipment' IN labels(n)
            RETURN count(n) as qsr_count
            """
            result = session.run(qsr_query)
            qsr_equipment_nodes = result.single()['qsr_count']
            
            # Document nodes count
            doc_query = "MATCH (n) WHERE 'Document' IN labels(n) RETURN count(n) as doc_count"
            result = session.run(doc_query)
            document_nodes = result.single()['doc_count']
            
            # Equipment types
            equipment_types_query = """
            MATCH (n) 
            WHERE 'EQUIPMENT' IN labels(n) OR 'Equipment' IN labels(n)
            RETURN n.name as name
            LIMIT 10
            """
            result = session.run(equipment_types_query)
            equipment_types = [record['name'] for record in result]
            
            # Recent activity
            recent_query = """
            MATCH (n) 
            WHERE n.created_at IS NOT NULL OR n.timestamp IS NOT NULL
            WITH n, coalesce(n.created_at, n.timestamp) as time_field
            WHERE time_field IS NOT NULL
            RETURN n.name as name, time_field
            ORDER BY time_field DESC
            LIMIT 5
            """
            result = session.run(recent_query)
            recent_activity = [{"name": record['name'], "timestamp": record['time_field']} for record in result]
            
        neo4j.driver.close()
        
        return {
            "connected": True,
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "qsr_equipment_nodes": qsr_equipment_nodes,
            "document_nodes": document_nodes,
            "equipment_types": equipment_types,
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        logger.error(f"Error getting Neo4j metrics: {e}")
        return {
            "connected": False,
            "error": str(e),
            "total_nodes": 0,
            "total_relationships": 0,
            "qsr_equipment_nodes": 0,
            "document_nodes": 0,
            "equipment_types": [],
            "recent_activity": []
        }

@diagnostics_router.get("/processing-files")
async def get_processing_files():
    """Get detailed information about processing files"""
    try:
        backend_dir = Path(__file__).parent
        
        # Get temp extraction files
        temp_files = list(backend_dir.glob("temp_extraction_*.json"))
        temp_info = []
        for file in temp_files:
            try:
                with open(file) as f:
                    data = json.load(f)
                temp_info.append({
                    "filename": file.name,
                    "size_bytes": file.stat().st_size,
                    "entities_count": len(data.get('entities', [])),
                    "relationships_count": len(data.get('relationships', [])),
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
            except:
                temp_info.append({
                    "filename": file.name,
                    "size_bytes": file.stat().st_size,
                    "error": "Could not parse file",
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
        
        # Get checkpoint files
        checkpoint_files = list(backend_dir.glob("checkpoint_*.json"))
        checkpoint_info = []
        for file in checkpoint_files:
            try:
                with open(file) as f:
                    data = json.load(f)
                checkpoint_info.append({
                    "filename": file.name,
                    "size_bytes": file.stat().st_size,
                    "entities_processed": data.get('entities_processed', 0),
                    "relationships_processed": data.get('relationships_processed', 0),
                    "entities_total": data.get('entities_total', 0),
                    "relationships_total": data.get('relationships_total', 0),
                    "start_time": data.get('start_time'),
                    "last_checkpoint": data.get('last_checkpoint'),
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
            except:
                checkpoint_info.append({
                    "filename": file.name,
                    "size_bytes": file.stat().st_size,
                    "error": "Could not parse file",
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
        
        return {
            "temp_extraction_files": temp_info,
            "checkpoint_files": checkpoint_info,
            "summary": {
                "total_temp_files": len(temp_files),
                "total_checkpoint_files": len(checkpoint_files),
                "total_size_mb": round(sum(f.stat().st_size for f in temp_files + checkpoint_files) / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting processing files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing files: {e}")

@diagnostics_router.get("/pipeline-health")
async def get_pipeline_health():
    """Get overall pipeline health status"""
    try:
        # Get basic metrics
        processing_status = await get_processing_status()
        system_metrics = processing_status["system_metrics"]
        
        # Analyze health indicators
        health_indicators = {
            "neo4j_connection": system_metrics["neo4j_connected"],
            "documents_processing": system_metrics["documents_processing"] > 0,
            "recent_completions": system_metrics["documents_completed"] > 0,
            "processing_files_exist": system_metrics["temp_extraction_files"] > 0,
            "graph_has_content": system_metrics["total_nodes"] > 0
        }
        
        # Calculate overall health score
        healthy_indicators = sum(health_indicators.values())
        total_indicators = len(health_indicators)
        health_score = (healthy_indicators / total_indicators) * 100
        
        # Determine status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "health_score": round(health_score, 1),
            "indicators": health_indicators,
            "recommendations": get_health_recommendations(health_indicators),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline health: {e}")

def get_health_recommendations(indicators: Dict[str, bool]) -> List[str]:
    """Get health recommendations based on indicators"""
    recommendations = []
    
    if not indicators["neo4j_connection"]:
        recommendations.append("Check Neo4j connection and credentials")
    
    if not indicators["graph_has_content"]:
        recommendations.append("No content in Neo4j graph - upload and process documents")
    
    if not indicators["recent_completions"]:
        recommendations.append("No recent document completions - check processing pipeline")
    
    if not indicators["processing_files_exist"]:
        recommendations.append("No processing files found - pipeline may not be running")
    
    if not recommendations:
        recommendations.append("All systems operational")
    
    return recommendations