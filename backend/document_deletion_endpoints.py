#!/usr/bin/env python3
"""
Document Deletion API Endpoints
Handles document deletion with Neo4j cleanup
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
import logging

from services.document_deletion_service import DocumentDeletionService, DeletionResult
from services.neo4j_service import neo4j_service
from services.rag_service import rag_service

logger = logging.getLogger(__name__)

# Create router
deletion_router = APIRouter(prefix="/api/v1/documents", tags=["document-deletion"])

def get_deletion_service() -> DocumentDeletionService:
    """Get document deletion service instance."""
    return DocumentDeletionService(neo4j_service, rag_service)

@deletion_router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    deletion_service: DocumentDeletionService = Depends(get_deletion_service)
) -> Dict:
    """
    Delete a document and all associated entities/relationships.
    
    Args:
        document_id: The ID of the document to delete
        
    Returns:
        Dictionary with deletion results
    """
    logger.info(f"🗑️  Document deletion requested: {document_id}")
    
    try:
        # Execute deletion
        result = await deletion_service.delete_document(document_id)
        
        # Format response
        response = {
            "success": result.success,
            "document_id": result.document_id,
            "entities_removed": result.entities_removed,
            "relationships_removed": result.relationships_removed,
            "shared_entities_preserved": result.shared_entities_preserved,
            "errors": result.errors,
            "rollback_performed": result.rollback_performed
        }
        
        if result.success:
            logger.info(f"✅ Document deleted successfully: {document_id}")
            return response
        else:
            logger.error(f"❌ Document deletion failed: {document_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Document deletion failed: {'; '.join(result.errors)}"
            )
            
    except Exception as e:
        logger.error(f"❌ Document deletion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during document deletion: {str(e)}"
        )

@deletion_router.get("/{document_id}/preview")
async def preview_document_deletion(
    document_id: str,
    deletion_service: DocumentDeletionService = Depends(get_deletion_service)
) -> Dict:
    """
    Preview what would be deleted for a document.
    
    Args:
        document_id: The ID of the document to preview deletion for
        
    Returns:
        Dictionary with deletion preview
    """
    logger.info(f"🔍 Document deletion preview requested: {document_id}")
    
    try:
        preview = await deletion_service.get_document_preview(document_id)
        
        return {
            "success": True,
            "preview": preview,
            "warning": "This shows what would be deleted. Shared entities will be preserved."
        }
        
    except Exception as e:
        logger.error(f"❌ Document deletion preview error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating deletion preview: {str(e)}"
        )

@deletion_router.get("/")
async def list_documents(
    deletion_service: DocumentDeletionService = Depends(get_deletion_service)
) -> Dict:
    """
    List all documents and their entity counts.
    
    Returns:
        Dictionary with document list
    """
    logger.info("📋 Document list requested")
    
    try:
        documents = await deletion_service.list_documents_with_entities()
        
        return {
            "success": True,
            "documents": documents,
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error(f"❌ Document list error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )

@deletion_router.post("/cleanup/orphaned")
async def cleanup_orphaned_entities(
    deletion_service: DocumentDeletionService = Depends(get_deletion_service)
) -> Dict:
    """
    Clean up orphaned entities (entities with no source document).
    
    Returns:
        Dictionary with cleanup results
    """
    logger.info("🧹 Orphaned entity cleanup requested")
    
    try:
        # Find orphaned entities
        orphaned_query = """
        MATCH (n)
        WHERE n.source_document_id IS NULL 
          AND (n.source_documents IS NULL OR size(n.source_documents) = 0)
        RETURN n.id as entity_id, n.name as entity_name, labels(n) as entity_types
        """
        
        result = neo4j_service.execute_query(orphaned_query)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="Failed to find orphaned entities"
            )
        
        orphaned_entities = result.get('records', [])
        
        if not orphaned_entities:
            return {
                "success": True,
                "message": "No orphaned entities found",
                "entities_removed": 0
            }
        
        # Remove orphaned entities
        cleanup_query = """
        MATCH (n)
        WHERE n.source_document_id IS NULL 
          AND (n.source_documents IS NULL OR size(n.source_documents) = 0)
        DETACH DELETE n
        """
        
        cleanup_result = neo4j_service.execute_query(cleanup_query)
        
        if cleanup_result.get('success'):
            return {
                "success": True,
                "message": f"Cleaned up {len(orphaned_entities)} orphaned entities",
                "entities_removed": len(orphaned_entities),
                "orphaned_entities": orphaned_entities
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to cleanup orphaned entities"
            )
            
    except Exception as e:
        logger.error(f"❌ Orphaned entity cleanup error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cleaning up orphaned entities: {str(e)}"
        )

@deletion_router.post("/reset")
async def reset_all_documents(
    deletion_service: DocumentDeletionService = Depends(get_deletion_service)
) -> Dict:
    """
    Reset all documents and clear the entire graph.
    
    WARNING: This will delete ALL data!
    
    Returns:
        Dictionary with reset results
    """
    logger.warning("⚠️  COMPLETE RESET REQUESTED - ALL DATA WILL BE DELETED")
    
    try:
        # Get current statistics
        stats_query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]-()
        RETURN count(distinct n) as total_nodes, count(r) as total_relationships
        """
        
        stats_result = neo4j_service.execute_query(stats_query)
        
        if not stats_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="Failed to get current statistics"
            )
        
        stats = stats_result.get('records', [{}])[0]
        total_nodes = stats.get('total_nodes', 0)
        total_relationships = stats.get('total_relationships', 0)
        
        # Delete all relationships first
        delete_rels_query = "MATCH ()-[r]-() DELETE r"
        rel_result = neo4j_service.execute_query(delete_rels_query)
        
        if not rel_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="Failed to delete relationships"
            )
        
        # Delete all nodes
        delete_nodes_query = "MATCH (n) DELETE n"
        node_result = neo4j_service.execute_query(delete_nodes_query)
        
        if not node_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="Failed to delete nodes"
            )
        
        return {
            "success": True,
            "message": "Complete reset performed",
            "nodes_deleted": total_nodes,
            "relationships_deleted": total_relationships,
            "warning": "ALL DATA HAS BEEN PERMANENTLY DELETED"
        }
        
    except Exception as e:
        logger.error(f"❌ Complete reset error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error performing complete reset: {str(e)}"
        )

# Enhanced document management endpoints
@deletion_router.get("/stats")
async def get_document_stats() -> Dict:
    """
    Get comprehensive document and entity statistics.
    
    Returns:
        Dictionary with statistics
    """
    logger.info("📊 Document statistics requested")
    
    try:
        # Get comprehensive stats
        stats_query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]-()
        WITH n, count(r) as relationship_count
        RETURN 
            count(n) as total_entities,
            count(distinct n.source_document_id) as unique_documents,
            collect(distinct labels(n)) as entity_types,
            sum(relationship_count) as total_relationships,
            collect(distinct n.source_document_id) as document_ids
        """
        
        result = neo4j_service.execute_query(stats_query)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="Failed to get statistics"
            )
        
        stats = result.get('records', [{}])[0]
        
        # Get entity type counts
        type_counts_query = """
        MATCH (n)
        RETURN labels(n) as entity_types, count(n) as count
        ORDER BY count DESC
        """
        
        type_result = neo4j_service.execute_query(type_counts_query)
        
        entity_type_counts = {}
        if type_result.get('success'):
            for record in type_result.get('records', []):
                entity_types = record.get('entity_types', [])
                count = record.get('count', 0)
                
                if entity_types:
                    entity_type_counts[entity_types[0]] = count
        
        return {
            "success": True,
            "statistics": {
                "total_entities": stats.get('total_entities', 0),
                "unique_documents": stats.get('unique_documents', 0),
                "total_relationships": stats.get('total_relationships', 0),
                "entity_type_counts": entity_type_counts,
                "document_ids": [doc_id for doc_id in stats.get('document_ids', []) if doc_id]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Document statistics error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document statistics: {str(e)}"
        )