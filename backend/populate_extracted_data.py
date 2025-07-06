#!/usr/bin/env python3
"""
Extracted Data Populator - Populate Neo4j Aura with Extracted Data
================================================================

Finds and populates Neo4j Aura with extracted entities and relationships
from JSON files created by the semantic extraction pipeline.
"""

import json
import os
from shared_neo4j_service import unified_neo4j
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class ExtractedDataPopulator:
    """Populate Neo4j Aura with extracted data from JSON files."""
    
    def __init__(self):
        self.data_sources = [
            "./data/rag_storage",
            "./backend/data/rag_storage", 
            "./rag_storage",
            "./lightrag_storage",
            "./extracted_data"
        ]
    
    def find_extracted_data(self) -> Dict[str, Any]:
        """Find and load extracted entity and relationship data."""
        
        found_data = {
            "entities": [],
            "relationships": [],
            "source_files": [],
            "latest_extraction": None
        }
        
        for data_dir in self.data_sources:
            if os.path.exists(data_dir):
                logger.info(f"🔍 Checking directory: {data_dir}")
                
                files = os.listdir(data_dir)
                json_files = [f for f in files if f.endswith('.json')]
                
                # Look for semantic graph files specifically
                semantic_files = [f for f in json_files if 'semantic_graph' in f]
                
                if semantic_files:
                    # Sort by modification time to get the latest
                    semantic_files.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
                    latest_file = semantic_files[0]
                    
                    logger.info(f"📄 Processing latest semantic graph: {latest_file}")
                    
                    file_path = os.path.join(data_dir, latest_file)
                    
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Extract entities and relationships from semantic graph format
                        if isinstance(data, dict):
                            entities = data.get('entities', [])
                            relationships = data.get('relationships', [])
                            
                            if entities:
                                found_data["entities"].extend(entities)
                                logger.info(f"✅ Loaded {len(entities)} entities from {latest_file}")
                            
                            if relationships:
                                found_data["relationships"].extend(relationships)
                                logger.info(f"✅ Loaded {len(relationships)} relationships from {latest_file}")
                            
                            found_data["source_files"].append(file_path)
                            found_data["latest_extraction"] = latest_file
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Could not load {latest_file}: {e}")
                
                # Also check for other entity/relationship files
                for json_file in json_files:
                    if json_file in [found_data["latest_extraction"]]:
                        continue  # Skip already processed
                        
                    file_path = os.path.join(data_dir, json_file)
                    
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Identify entity vs relationship files by filename patterns
                        if any(pattern in json_file.lower() for pattern in ['entit', 'node', 'vertex']):
                            if isinstance(data, list):
                                found_data["entities"].extend(data)
                            elif isinstance(data, dict) and 'entities' in data:
                                found_data["entities"].extend(data['entities'])
                            
                            logger.info(f"✅ Loaded entities from: {json_file}")
                        
                        elif any(pattern in json_file.lower() for pattern in ['rel', 'edge', 'link']):
                            if isinstance(data, list):
                                found_data["relationships"].extend(data)
                            elif isinstance(data, dict) and 'relationships' in data:
                                found_data["relationships"].extend(data['relationships'])
                            
                            logger.info(f"✅ Loaded relationships from: {json_file}")
                        
                        found_data["source_files"].append(file_path)
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Could not load {json_file}: {e}")
                
                # If we found data in this directory, use it
                if found_data["entities"] or found_data["relationships"]:
                    break
        
        logger.info(f"📊 Total found: {len(found_data['entities'])} entities, {len(found_data['relationships'])} relationships")
        return found_data
    
    def populate_neo4j(self) -> Dict[str, Any]:
        """Populate Neo4j Aura with extracted data."""
        
        # Ensure unified service is connected
        if not unified_neo4j.connected:
            logger.info("🔌 Initializing unified Neo4j service...")
            success = unified_neo4j.initialize_from_backend_config()
            if not success:
                return {"error": "Could not connect to Neo4j Aura"}
        
        # Find extracted data
        extracted_data = self.find_extracted_data()
        
        if not extracted_data["entities"] and not extracted_data["relationships"]:
            return {"error": "No extracted data found in JSON files"}
        
        try:
            with unified_neo4j.get_session() as session:
                # Get baseline count
                result = session.run("MATCH (n) RETURN count(n) as baseline")
                baseline_count = result.single()["baseline"]
                
                logger.info(f"📊 Current nodes in Aura: {baseline_count}")
                
                # Populate entities with proper QSR types
                entities_created = 0
                for entity in extracted_data["entities"]:
                    if isinstance(entity, dict) and entity.get("name"):
                        entity_type = entity.get("type", "Entity")
                        
                        # Create entity with proper label
                        session.run(f"""
                            MERGE (e:`{entity_type}` {{name: $name}})
                            SET e.description = $description,
                                e.content = $content,
                                e.document_source = $document_source,
                                e.entity_id = $entity_id,
                                e.classification_confidence = $confidence,
                                e.qsr_classified = $qsr_classified,
                                e.extracted_timestamp = datetime(),
                                e.extraction_method = 'unified_populator'
                        """, 
                        name=entity.get("name"),
                        description=entity.get("description", ""),
                        content=entity.get("content", ""),
                        document_source=entity.get("document_source", "extracted_data"),
                        entity_id=entity.get("id", ""),
                        confidence=entity.get("classification_confidence", 0.5),
                        qsr_classified=entity.get("qsr_classified", False)
                        )
                        entities_created += 1
                        
                        if entities_created <= 5:  # Log first few for verification
                            logger.info(f"  ✅ Created {entity_type}: {entity.get('name')}")
                
                # Populate relationships with semantic types
                relationships_created = 0
                for rel in extracted_data["relationships"]:
                    if isinstance(rel, dict):
                        source_name = rel.get("source_entity") or rel.get("source")
                        target_name = rel.get("target_entity") or rel.get("target")
                        rel_type = rel.get("relationship_type") or rel.get("type", "RELATED_TO")
                        
                        if source_name and target_name:
                            # Clean relationship type for Cypher
                            rel_type = rel_type.replace(" ", "_").replace("-", "_")
                            
                            session.run(f"""
                                MATCH (source {{name: $source_name}})
                                MATCH (target {{name: $target_name}})
                                MERGE (source)-[r:`{rel_type}`]->(target)
                                SET r.description = $description,
                                    r.context = $context,
                                    r.confidence = $confidence,
                                    r.semantic_type = $semantic_type,
                                    r.qsr_specific = $qsr_specific,
                                    r.document_source = $document_source,
                                    r.extracted_timestamp = datetime(),
                                    r.extraction_method = 'unified_populator'
                            """,
                            source_name=source_name,
                            target_name=target_name,
                            description=rel.get("description", ""),
                            context=rel.get("context", ""),
                            confidence=rel.get("confidence", 0.5),
                            semantic_type=rel.get("semantic_type", ""),
                            qsr_specific=rel.get("qsr_specific", False),
                            document_source=rel.get("document_source", "")
                            )
                            relationships_created += 1
                            
                            if relationships_created <= 5:  # Log first few for verification
                                logger.info(f"  🔗 Created {rel_type}: {source_name} → {target_name}")
                
                # Get final count
                result = session.run("MATCH (n) RETURN count(n) as final")
                final_count = result.single()["final"]
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as total_rels")
                total_rels = result.single()["total_rels"]
                
                logger.info(f"🎉 Population complete! Nodes: {baseline_count} → {final_count} (+{final_count - baseline_count})")
                
                return {
                    "success": True,
                    "baseline_nodes": baseline_count,
                    "final_nodes": final_count,
                    "nodes_added": final_count - baseline_count,
                    "total_relationships": total_rels,
                    "entities_processed": entities_created,
                    "relationships_processed": relationships_created,
                    "source_files": extracted_data["source_files"],
                    "latest_extraction_file": extracted_data["latest_extraction"]
                }
                
        except Exception as e:
            logger.error(f"❌ Population failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"error": str(e)}

# Global instance
data_populator = ExtractedDataPopulator()