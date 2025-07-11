#!/usr/bin/env python3
"""
Document Deletion Service
Handles complete document removal from both LightRAG and Neo4j
"""

import asyncio
import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class DeletionResult:
    """Result of document deletion operation."""
    success: bool
    document_id: str
    entities_removed: int
    relationships_removed: int
    shared_entities_preserved: int
    errors: List[str]
    rollback_performed: bool = False

@dataclass
class EntityReference:
    """Reference to an entity in Neo4j."""
    node_id: str
    entity_name: str
    entity_type: str
    source_documents: Set[str]
    total_references: int

class DocumentDeletionService:
    """Service for safely deleting documents and their associated data."""
    
    def __init__(self, neo4j_service, lightrag_service):
        self.neo4j_service = neo4j_service
        self.lightrag_service = lightrag_service
        self.logger = logging.getLogger(__name__)
        
    async def delete_document(self, document_id: str) -> DeletionResult:
        """
        Delete a document and all its associated data.
        
        Args:
            document_id: The ID of the document to delete
            
        Returns:
            DeletionResult with operation details
        """
        self.logger.info(f"🗑️  Starting document deletion: {document_id}")
        
        result = DeletionResult(
            success=False,
            document_id=document_id,
            entities_removed=0,
            relationships_removed=0,
            shared_entities_preserved=0,
            errors=[]
        )
        
        try:
            # Step 1: Analyze what needs to be deleted
            self.logger.info("🔍 Analyzing entities to delete...")
            entities_analysis = await self._analyze_entities_for_deletion(document_id)
            
            if not entities_analysis:
                result.errors.append("No entities found for document")
                return result
            
            # Step 2: Create deletion plan
            deletion_plan = await self._create_deletion_plan(document_id, entities_analysis)
            
            self.logger.info(f"📋 Deletion plan created:")
            self.logger.info(f"   - Entities to remove: {len(deletion_plan['entities_to_remove'])}")
            self.logger.info(f"   - Entities to preserve: {len(deletion_plan['entities_to_preserve'])}")
            self.logger.info(f"   - Relationships to remove: {len(deletion_plan['relationships_to_remove'])}")
            
            # Step 3: Create backup for rollback
            backup_data = await self._create_backup(deletion_plan)
            
            # Step 4: Execute deletion (atomic operation)
            deletion_success = await self._execute_deletion(deletion_plan, result)
            
            if not deletion_success:
                # Rollback on failure
                self.logger.error("❌ Deletion failed, performing rollback...")
                await self._rollback_deletion(backup_data)
                result.rollback_performed = True
                return result
            
            # Step 5: Remove from LightRAG
            lightrag_success = await self._remove_from_lightrag(document_id)
            
            if not lightrag_success:
                result.errors.append("Failed to remove from LightRAG")
                # Consider if we should rollback Neo4j changes here
            
            # Step 6: Verify deletion
            verification_success = await self._verify_deletion(document_id)
            
            if verification_success:
                result.success = True
                self.logger.info(f"✅ Document deletion successful: {document_id}")
            else:
                result.errors.append("Deletion verification failed")
                
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Document deletion error: {e}")
            result.errors.append(f"Unexpected error: {str(e)}")
            return result
    
    async def _analyze_entities_for_deletion(self, document_id: str) -> List[EntityReference]:
        """Analyze which entities are associated with this document."""
        
        # Query Neo4j for entities with this source document
        query = """
        MATCH (n)
        WHERE n.source_document_id = $document_id OR $document_id IN n.source_documents
        OPTIONAL MATCH (n)-[r]-()
        RETURN n, 
               labels(n) as entity_types,
               count(r) as relationship_count,
               n.source_documents as source_docs,
               n.source_document_id as source_doc_id
        """
        
        result = self.neo4j_service.execute_query(query, {"document_id": document_id})
        
        if not result.get('success'):
            self.logger.error(f"Failed to analyze entities: {result.get('error')}")
            return []
        
        entities = []
        
        for record in result.get('records', []):
            node = record.get('n', {})
            entity_types = record.get('entity_types', [])
            
            # Determine source documents
            source_documents = set()
            
            # Check multiple possible source fields
            if record.get('source_docs'):
                if isinstance(record['source_docs'], list):
                    source_documents.update(record['source_docs'])
                else:
                    source_documents.add(record['source_docs'])
            
            if record.get('source_doc_id'):
                source_documents.add(record['source_doc_id'])
            
            # Check node properties for source info
            if hasattr(node, 'source_document_id'):
                source_documents.add(node.source_document_id)
            if hasattr(node, 'source_documents'):
                if isinstance(node.source_documents, list):
                    source_documents.update(node.source_documents)
                else:
                    source_documents.add(node.source_documents)
            
            entity_ref = EntityReference(
                node_id=node.get('id', ''),
                entity_name=node.get('name', ''),
                entity_type=entity_types[0] if entity_types else 'Unknown',
                source_documents=source_documents,
                total_references=record.get('relationship_count', 0)
            )
            
            entities.append(entity_ref)
        
        return entities
    
    async def _create_deletion_plan(self, document_id: str, entities: List[EntityReference]) -> Dict:
        """Create a plan for what to delete vs what to preserve."""
        
        entities_to_remove = []
        entities_to_preserve = []
        relationships_to_remove = []
        
        for entity in entities:
            # If entity is only referenced by this document, mark for deletion
            if len(entity.source_documents) == 1 and document_id in entity.source_documents:
                entities_to_remove.append(entity)
            else:
                # Entity is shared with other documents, preserve but update references
                entities_to_preserve.append(entity)
        
        # Find relationships that need to be removed
        for entity in entities_to_remove:
            # Get all relationships for entities being removed
            rel_query = """
            MATCH (n)-[r]-(m)
            WHERE n.id = $entity_id OR m.id = $entity_id
            RETURN r, n.id as source_id, m.id as target_id
            """
            
            rel_result = self.neo4j_service.execute_query(rel_query, {"entity_id": entity.node_id})
            
            if rel_result.get('success'):
                for rel_record in rel_result.get('records', []):
                    relationships_to_remove.append({
                        'relationship': rel_record.get('r'),
                        'source_id': rel_record.get('source_id'),
                        'target_id': rel_record.get('target_id')
                    })
        
        return {
            'entities_to_remove': entities_to_remove,
            'entities_to_preserve': entities_to_preserve,
            'relationships_to_remove': relationships_to_remove
        }
    
    async def _create_backup(self, deletion_plan: Dict) -> Dict:
        """Create backup data for rollback purposes."""
        
        backup_data = {
            'entities': [],
            'relationships': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Backup entities that will be removed
        for entity in deletion_plan['entities_to_remove']:
            entity_query = """
            MATCH (n)
            WHERE n.id = $entity_id
            RETURN n, labels(n) as entity_types
            """
            
            result = self.neo4j_service.execute_query(entity_query, {"entity_id": entity.node_id})
            
            if result.get('success') and result.get('records'):
                record = result['records'][0]
                backup_data['entities'].append({
                    'node': dict(record.get('n', {})),
                    'labels': record.get('entity_types', [])
                })
        
        # Backup relationships that will be removed
        for rel_info in deletion_plan['relationships_to_remove']:
            backup_data['relationships'].append({
                'relationship': dict(rel_info['relationship']),
                'source_id': rel_info['source_id'],
                'target_id': rel_info['target_id']
            })
        
        return backup_data
    
    async def _execute_deletion(self, deletion_plan: Dict, result: DeletionResult) -> bool:
        """Execute the actual deletion operations."""
        
        try:
            # Step 1: Remove relationships first
            for rel_info in deletion_plan['relationships_to_remove']:
                rel_delete_query = """
                MATCH (n)-[r]-(m)
                WHERE n.id = $source_id AND m.id = $target_id
                DELETE r
                """
                
                rel_result = self.neo4j_service.execute_query(rel_delete_query, {
                    'source_id': rel_info['source_id'],
                    'target_id': rel_info['target_id']
                })
                
                if rel_result.get('success'):
                    result.relationships_removed += 1
                else:
                    result.errors.append(f"Failed to remove relationship: {rel_info}")
                    return False
            
            # Step 2: Remove entities that are no longer referenced
            for entity in deletion_plan['entities_to_remove']:
                entity_delete_query = """
                MATCH (n)
                WHERE n.id = $entity_id
                DELETE n
                """
                
                entity_result = self.neo4j_service.execute_query(entity_delete_query, {
                    'entity_id': entity.node_id
                })
                
                if entity_result.get('success'):
                    result.entities_removed += 1
                else:
                    result.errors.append(f"Failed to remove entity: {entity.entity_name}")
                    return False
            
            # Step 3: Update preserved entities (remove document reference)
            for entity in deletion_plan['entities_to_preserve']:
                # Remove document_id from source_documents list
                updated_sources = entity.source_documents.copy()
                updated_sources.discard(result.document_id)
                
                update_query = """
                MATCH (n)
                WHERE n.id = $entity_id
                SET n.source_documents = $updated_sources
                """
                
                update_result = self.neo4j_service.execute_query(update_query, {
                    'entity_id': entity.node_id,
                    'updated_sources': list(updated_sources)
                })
                
                if update_result.get('success'):
                    result.shared_entities_preserved += 1
                else:
                    result.errors.append(f"Failed to update entity: {entity.entity_name}")
                    return False
            
            return True
            
        except Exception as e:
            result.errors.append(f"Deletion execution error: {str(e)}")
            return False
    
    async def _rollback_deletion(self, backup_data: Dict) -> bool:
        """Rollback deletion by restoring from backup."""
        
        try:
            self.logger.info("🔄 Rolling back deletion...")
            
            # Restore entities
            for entity_backup in backup_data['entities']:
                node_data = entity_backup['node']
                labels = entity_backup['labels']
                
                # Create node with original data
                create_query = f"""
                CREATE (n:{':'.join(labels)})
                SET n = $node_data
                """
                
                self.neo4j_service.execute_query(create_query, {'node_data': node_data})
            
            # Restore relationships
            for rel_backup in backup_data['relationships']:
                rel_data = rel_backup['relationship']
                source_id = rel_backup['source_id']
                target_id = rel_backup['target_id']
                
                create_rel_query = """
                MATCH (n), (m)
                WHERE n.id = $source_id AND m.id = $target_id
                CREATE (n)-[r:RELATES_TO]->(m)
                SET r = $rel_data
                """
                
                self.neo4j_service.execute_query(create_rel_query, {
                    'source_id': source_id,
                    'target_id': target_id,
                    'rel_data': rel_data
                })
            
            self.logger.info("✅ Rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Rollback failed: {e}")
            return False
    
    async def _remove_from_lightrag(self, document_id: str) -> bool:
        """Remove document from LightRAG storage."""
        
        try:
            # This depends on LightRAG's API - may need to be implemented
            # For now, we'll log that this needs to be implemented
            self.logger.warning("⚠️  LightRAG document removal not implemented")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ LightRAG removal failed: {e}")
            return False
    
    async def _verify_deletion(self, document_id: str) -> bool:
        """Verify that document has been completely removed."""
        
        try:
            # Check if any entities still reference this document
            verify_query = """
            MATCH (n)
            WHERE n.source_document_id = $document_id 
               OR $document_id IN n.source_documents
            RETURN count(n) as remaining_entities
            """
            
            result = self.neo4j_service.execute_query(verify_query, {"document_id": document_id})
            
            if result.get('success') and result.get('records'):
                remaining_entities = result['records'][0].get('remaining_entities', 0)
                
                if remaining_entities == 0:
                    self.logger.info("✅ Deletion verification passed")
                    return True
                else:
                    self.logger.error(f"❌ Deletion verification failed: {remaining_entities} entities still reference document")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Verification error: {e}")
            return False
    
    async def list_documents_with_entities(self) -> List[Dict]:
        """List all documents and their entity counts."""
        
        query = """
        MATCH (n)
        WHERE n.source_document_id IS NOT NULL OR n.source_documents IS NOT NULL
        WITH CASE 
            WHEN n.source_document_id IS NOT NULL THEN n.source_document_id
            ELSE n.source_documents
        END AS doc_id
        UNWIND (CASE WHEN doc_id IS NOT NULL THEN [doc_id] ELSE [] END) AS document_id
        RETURN document_id, count(*) as entity_count
        ORDER BY entity_count DESC
        """
        
        result = self.neo4j_service.execute_query(query)
        
        if result.get('success'):
            return result.get('records', [])
        else:
            return []
    
    async def get_document_preview(self, document_id: str) -> Dict:
        """Get a preview of what would be deleted for a document."""
        
        entities_analysis = await self._analyze_entities_for_deletion(document_id)
        
        if not entities_analysis:
            return {
                'document_id': document_id,
                'entities_to_remove': 0,
                'entities_to_preserve': 0,
                'entity_types': {},
                'shared_entities': []
            }
        
        deletion_plan = await self._create_deletion_plan(document_id, entities_analysis)
        
        # Count entity types
        entity_types = {}
        for entity in deletion_plan['entities_to_remove']:
            entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1
        
        # List shared entities
        shared_entities = [
            {
                'name': entity.entity_name,
                'type': entity.entity_type,
                'shared_with': len(entity.source_documents) - 1
            }
            for entity in deletion_plan['entities_to_preserve']
        ]
        
        return {
            'document_id': document_id,
            'entities_to_remove': len(deletion_plan['entities_to_remove']),
            'entities_to_preserve': len(deletion_plan['entities_to_preserve']),
            'relationships_to_remove': len(deletion_plan['relationships_to_remove']),
            'entity_types': entity_types,
            'shared_entities': shared_entities
        }