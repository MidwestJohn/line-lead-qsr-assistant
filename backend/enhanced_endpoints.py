#!/usr/bin/env python3
"""
Enhanced FastAPI Endpoints with Document Context Integration
Implements comprehensive document-level context and hierarchical retrieval
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# FastAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from enhanced_upload_pipeline import EnhancedUploadPipeline
from services.context_aware_query_service import ContextAwareQueryService
from services.neo4j_service import Neo4jService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
upload_pipeline = EnhancedUploadPipeline()
query_service = ContextAwareQueryService()
neo4j_service = Neo4jService()

app = FastAPI(
    title="Line Lead QSR System - Enhanced",
    description="Document Context Integration with Hierarchical Knowledge Graph",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    
    logger.info("🚀 Starting Enhanced Line Lead QSR System...")
    
    # Connect to Neo4j
    try:
        await neo4j_service.connect()
        logger.info("✅ Neo4j connection established")
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")

@app.get("/")
async def root():
    """Root endpoint with system information"""
    
    return {
        "message": "Line Lead QSR System - Enhanced with Document Context Integration",
        "version": "2.0.0",
        "features": [
            "Document-level context integration",
            "Hierarchical entity structure", 
            "Context-aware query processing",
            "Entity deduplication and normalization",
            "Hybrid retrieval system"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with detailed system status"""
    
    try:
        # Check Neo4j connection
        neo4j_status = "connected" if neo4j_service.connected else "disconnected"
        
        # Get upload status
        upload_status = await upload_pipeline.get_upload_status()
        
        # Get database statistics
        db_stats = await get_database_statistics()
        
        return {
            "status": "healthy",
            "services": {
                "neo4j": neo4j_status,
                "upload_pipeline": "ready",
                "query_service": "ready"
            },
            "database_statistics": db_stats,
            "upload_statistics": upload_status.get("statistics", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Enhanced document upload with context integration
    Implements document summarization and hierarchical structure
    """
    
    logger.info(f"📄 Enhanced upload request: {file.filename}")
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Process with enhanced pipeline
        result = await upload_pipeline.process_document_upload(file)
        
        if result["status"] == "success":
            logger.info(f"✅ Enhanced upload successful: {file.filename}")
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Document '{file.filename}' uploaded and processed with context integration",
                    "result": result
                }
            )
        else:
            logger.error(f"❌ Enhanced upload failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Upload processing failed'))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def context_aware_query(request: Dict[str, Any]):
    """
    Context-aware query processing with hierarchical retrieval
    Implements hybrid retrieval system with document context
    """
    
    query = request.get("query", "").strip()
    max_results = request.get("max_results", 10)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    logger.info(f"🔍 Context-aware query: {query[:100]}...")
    
    try:
        # Process with context-aware service
        result = await query_service.process_context_aware_query(query, max_results)
        
        if result["status"] == "success":
            logger.info(f"✅ Query processed successfully")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Query processed with context integration",
                    "result": result
                }
            )
        else:
            logger.error(f"❌ Query processing failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Query processing failed'))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all uploaded documents with their context metadata"""
    
    try:
        documents = await upload_pipeline.list_documents()
        
        return {
            "documents": documents,
            "total_count": len(documents),
            "hierarchical_documents": len([d for d in documents if d.get('hierarchical_processing', False)]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}")
async def get_document_details(document_id: str):
    """Get detailed information about a specific document"""
    
    try:
        # Get document details from Neo4j
        if not neo4j_service.connected:
            await neo4j_service.connect()
        
        with neo4j_service.driver.session() as session:
            # Get document node
            doc_query = """
            MATCH (d:Document {document_id: $document_id})
            RETURN d
            """
            
            doc_result = session.run(doc_query, document_id=document_id)
            doc_record = doc_result.single()
            
            if not doc_record:
                raise HTTPException(status_code=404, detail="Document not found")
            
            document = dict(doc_record['d'])
            
            # Get entities for this document
            entity_query = """
            MATCH (e)
            WHERE e.document_id = $document_id
            AND NOT e:Document
            RETURN e, labels(e) as entity_labels
            ORDER BY e.hierarchy_level, e.canonical_name
            """
            
            entity_results = session.run(entity_query, document_id=document_id)
            entities = []
            
            for record in entity_results:
                entity = dict(record['e'])
                entity['labels'] = record['entity_labels']
                entities.append(entity)
            
            # Get relationships for this document
            rel_query = """
            MATCH (source)-[r {document_id: $document_id}]->(target)
            RETURN type(r) as relationship_type, 
                   source.canonical_name as source_name,
                   target.canonical_name as target_name,
                   r.confidence as confidence
            ORDER BY r.confidence DESC
            """
            
            rel_results = session.run(rel_query, document_id=document_id)
            relationships = []
            
            for record in rel_results:
                relationships.append({
                    "type": record['relationship_type'],
                    "source": record['source_name'],
                    "target": record['target_name'],
                    "confidence": record['confidence']
                })
            
            return {
                "document": document,
                "entities": entities,
                "relationships": relationships,
                "statistics": {
                    "entity_count": len(entities),
                    "relationship_count": len(relationships)
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_entities(
    query: str = Query(..., description="Search query"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    max_results: int = Query(20, description="Maximum results to return")
):
    """Search entities with filtering and context"""
    
    try:
        if not neo4j_service.connected:
            await neo4j_service.connect()
        
        # Build search query
        search_conditions = [
            f"toLower(e.canonical_name) CONTAINS toLower('{query}')",
            f"toLower(e.entity_text) CONTAINS toLower('{query}')",
            f"toLower(e.qsr_context) CONTAINS toLower('{query}')"
        ]
        
        where_clause = f"({' OR '.join(search_conditions)})"
        
        # Add filters
        if entity_type:
            where_clause += f" AND e.entity_type = '{entity_type}'"
        
        if document_type:
            where_clause += f" AND e.document_type = '{document_type}'"
        
        with neo4j_service.driver.session() as session:
            search_query = f"""
            MATCH (e)
            WHERE (e:EQUIPMENT OR e:ENTITY OR e:PROCEDURE OR e:PROCESS OR e:TEMPERATURE OR e:QSR_SPECIFIC)
            AND {where_clause}
            OPTIONAL MATCH (d:Document {{document_id: e.document_id}})
            RETURN e, d
            ORDER BY e.confidence DESC, e.hierarchy_level ASC
            LIMIT {max_results}
            """
            
            results = session.run(search_query)
            
            search_results = []
            for record in results:
                entity = dict(record['e']) if record['e'] else {}
                document = dict(record['d']) if record['d'] else {}
                
                search_results.append({
                    "entity": entity,
                    "document_context": {
                        "filename": document.get('filename', 'Unknown'),
                        "document_type": document.get('document_type', 'Unknown'),
                        "equipment_focus": document.get('equipment_focus', 'Unknown')
                    }
                })
            
            return {
                "query": query,
                "filters": {
                    "entity_type": entity_type,
                    "document_type": document_type
                },
                "results": search_results,
                "total_found": len(search_results),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_system_statistics():
    """Get comprehensive system statistics"""
    
    try:
        # Get upload statistics
        upload_stats = await upload_pipeline.get_upload_status()
        
        # Get database statistics
        db_stats = await get_database_statistics()
        
        return {
            "system_status": "operational",
            "upload_statistics": upload_stats.get("statistics", {}),
            "database_statistics": db_stats,
            "document_distribution": {
                "by_type": upload_stats.get("document_types", {}),
                "by_category": upload_stats.get("equipment_categories", {})
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def get_database_statistics() -> Dict[str, Any]:
    """Get Neo4j database statistics"""
    
    try:
        if not neo4j_service.connected:
            return {"error": "Neo4j not connected"}
        
        with neo4j_service.driver.session() as session:
            # Count nodes by type
            node_query = """
            MATCH (n)
            RETURN labels(n) as node_labels, count(n) as count
            ORDER BY count DESC
            """
            
            node_results = session.run(node_query)
            node_counts = {}
            total_nodes = 0
            
            for record in node_results:
                labels = record['node_labels']
                count = record['count']
                label_key = labels[0] if labels else 'Unknown'
                node_counts[label_key] = count
                total_nodes += count
            
            # Count relationships by type
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """
            
            rel_results = session.run(rel_query)
            relationship_counts = {}
            total_relationships = 0
            
            for record in rel_results:
                rel_type = record['rel_type']
                count = record['count']
                relationship_counts[rel_type] = count
                total_relationships += count
            
            return {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "node_distribution": node_counts,
                "relationship_distribution": relationship_counts
            }
            
    except Exception as e:
        logger.error(f"Database statistics error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)