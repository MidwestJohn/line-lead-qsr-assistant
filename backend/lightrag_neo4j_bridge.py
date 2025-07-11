#!/usr/bin/env python3
"""
LightRAG → Neo4j Bridge Script
================================

Reliable manual script to push LightRAG JSON outputs to Neo4j with enterprise-grade reliability.
Handles batch operations, retry logic, deduplication, and resume capability.

Features:
- Batch processing (configurable batch size)
- Exponential backoff retries (3 attempts)
- Transaction rollback on failure
- Deduplication logic
- Progress tracking with logs
- Resume from checkpoint on interruption
- Connection drop handling
- Partial failure recovery

Author: Generated with Memex (https://memex.tech)
"""

import json
import logging
import time
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from dotenv import load_dotenv
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lightrag_neo4j_bridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv(dotenv_path='.env.rag')

class LightRAGNeo4jBridge:
    """
    Enterprise-grade bridge for transferring LightRAG JSON outputs to Neo4j.
    """
    
    def __init__(self, 
                 entities_file: str = "entities.json",
                 relationships_file: str = "relationships.json",
                 batch_size: int = 500,
                 max_retries: int = 3,
                 checkpoint_file: str = "bridge_checkpoint.json"):
        
        self.entities_file = Path(entities_file)
        self.relationships_file = Path(relationships_file)
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.checkpoint_file = Path(checkpoint_file)
        
        # Neo4j connection
        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USERNAME')  
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = None
        
        # Progress tracking
        self.progress = {
            'entities_processed': 0,
            'relationships_processed': 0,
            'entities_total': 0,
            'relationships_total': 0,
            'start_time': None,
            'last_checkpoint': None,
            'failed_entities': [],
            'failed_relationships': [],
            'entity_hashes': set(),
            'relationship_hashes': set()
        }
        
        # Load existing progress if available
        self.load_checkpoint()
        
    def connect_to_neo4j(self) -> bool:
        """
        Connect to Neo4j with Aura-optimized settings and retry logic.
        """
        for attempt in range(self.max_retries):
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                    max_connection_lifetime=30 * 60,
                    max_connection_pool_size=10,
                    connection_acquisition_timeout=60
                )
                
                # Test connection
                self.driver.verify_connectivity()
                logger.info(f"✅ Connected to Neo4j: {self.uri}")
                return True
                
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed to connect after {self.max_retries} attempts")
                    return False
        
        return False
    
    def load_lightrag_json(self, filepath: Path) -> List[Dict]:
        """
        Load and validate LightRAG JSON output files.
        """
        try:
            if not filepath.exists():
                logger.error(f"❌ File not found: {filepath}")
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both single objects and arrays
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                logger.error(f"❌ Invalid JSON format in {filepath}")
                return []
            
            logger.info(f"✅ Loaded {len(data)} items from {filepath}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error in {filepath}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error loading {filepath}: {e}")
            return []
    
    def generate_hash(self, item: Dict) -> str:
        """
        Generate a unique hash for deduplication.
        """
        # Create a deterministic string representation
        item_str = json.dumps(item, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(item_str.encode('utf-8')).hexdigest()
    
    def retry_with_backoff(self, func, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Execute function with exponential backoff retry logic.
        """
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                return True, result
            except neo4j_exceptions.TransientError as e:
                wait_time = 2 ** attempt
                logger.warning(f"Transient error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed after {self.max_retries} attempts: {e}")
                    return False, str(e)
            except Exception as e:
                logger.error(f"❌ Non-retryable error: {e}")
                return False, str(e)
        
        return False, "Max retries exceeded"
    
    def batch_insert_entities(self, entities: List[Dict]) -> Tuple[int, List[Dict]]:
        """
        Insert entities in batches with transaction rollback on failure.
        """
        processed = 0
        failed = []
        
        for i in range(0, len(entities), self.batch_size):
            batch = entities[i:i + self.batch_size]
            
            # Filter out duplicates and already processed entities
            unique_batch = []
            for entity in batch:
                entity_hash = self.generate_hash(entity)
                if entity_hash not in self.progress['entity_hashes']:
                    unique_batch.append(entity)
                    self.progress['entity_hashes'].add(entity_hash)
                else:
                    logger.debug(f"Skipping duplicate entity: {entity.get('name', 'Unknown')}")
            
            if not unique_batch:
                continue
            
            logger.info(f"Processing entity batch {i//self.batch_size + 1}: {len(unique_batch)} entities")
            
            success, result = self.retry_with_backoff(self._insert_entity_batch, unique_batch)
            
            if success:
                processed += len(unique_batch)
                self.progress['entities_processed'] += len(unique_batch)
                logger.info(f"✅ Successfully inserted {len(unique_batch)} entities")
            else:
                logger.error(f"❌ Failed to insert entity batch: {result}")
                failed.extend(unique_batch)
                self.progress['failed_entities'].extend(unique_batch)
            
            # Save checkpoint after each batch
            self.save_checkpoint()
        
        return processed, failed
    
    def _insert_entity_batch(self, entities: List[Dict]) -> bool:
        """
        Insert a batch of entities within a transaction with multi-modal support.
        """
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                for entity in entities:
                    # Extract entity properties
                    name = entity.get('name', entity.get('id', 'Unknown'))
                    entity_type = entity.get('type', entity.get('label', 'Entity'))
                    description = entity.get('description', '')
                    
                    # Standard properties
                    properties = {
                        'name': name,
                        'type': entity_type,
                        'description': description,
                        'created_at': datetime.now().isoformat(),
                        'source': 'lightrag_bridge'
                    }
                    
                    # Multi-modal properties
                    multimodal_props = {
                        'visual_refs': entity.get('visual_refs', []),
                        'image_refs': entity.get('image_refs', []),
                        'table_refs': entity.get('table_refs', []),
                        'diagram_refs': entity.get('diagram_refs', []),
                        'page_refs': entity.get('page_refs', []),
                        'citation_ids': entity.get('citation_ids', []),
                        'multimodal_enhanced': entity.get('multimodal_enhanced', False)
                    }
                    
                    # Add multi-modal properties if they exist
                    for key, value in multimodal_props.items():
                        if value:  # Only add if not empty
                            properties[key] = value
                    
                    # Add any additional properties from the entity
                    for key, value in entity.items():
                        if key not in ['name', 'type', 'description', 'id', 'label'] and not key.startswith('visual_'):
                            properties[key] = value
                    
                    # Create node with dynamic label
                    label = entity_type.replace(' ', '_').upper()
                    query = f"""
                    MERGE (n:{label} {{name: $name}})
                    SET n += $properties
                    """
                    
                    tx.run(query, name=name, properties=properties)
                    
                    # Create visual citation nodes and relationships if available
                    if entity.get('citation_ids'):
                        self._create_visual_citation_nodes(tx, entity, entity.get('citation_ids', []))
                
                # Commit transaction
                tx.commit()
                return True
    
    def _create_visual_citation_nodes(self, tx, entity: Dict, citation_ids: List[str]):
        """
        Create visual citation nodes and link them to entities
        """
        for citation_id in citation_ids:
            # Create or merge visual citation node
            citation_query = """
            MERGE (c:VisualCitation {citation_id: $citation_id})
            SET c.created_at = $created_at,
                c.entity_linked = $entity_name
            """
            
            tx.run(citation_query, 
                   citation_id=citation_id, 
                   created_at=datetime.now().isoformat(),
                   entity_name=entity.get('name', 'Unknown'))
            
            # Create relationship between entity and citation
            entity_name = entity.get('name', entity.get('id', 'Unknown'))
            entity_type = entity.get('type', entity.get('label', 'Entity'))
            label = entity_type.replace(' ', '_').upper()
            
            link_query = f"""
            MATCH (e:{label} {{name: $entity_name}})
            MATCH (c:VisualCitation {{citation_id: $citation_id}})
            MERGE (e)-[:HAS_VISUAL_REFERENCE]->(c)
            """
            
            tx.run(link_query, entity_name=entity_name, citation_id=citation_id)
    
    def batch_insert_relationships(self, relationships: List[Dict]) -> Tuple[int, List[Dict]]:
        """
        Insert relationships in batches with transaction rollback on failure.
        """
        processed = 0
        failed = []
        
        for i in range(0, len(relationships), self.batch_size):
            batch = relationships[i:i + self.batch_size]
            
            # Filter out duplicates and already processed relationships
            unique_batch = []
            for relationship in batch:
                rel_hash = self.generate_hash(relationship)
                if rel_hash not in self.progress['relationship_hashes']:
                    unique_batch.append(relationship)
                    self.progress['relationship_hashes'].add(rel_hash)
                else:
                    logger.debug(f"Skipping duplicate relationship")
            
            if not unique_batch:
                continue
            
            logger.info(f"Processing relationship batch {i//self.batch_size + 1}: {len(unique_batch)} relationships")
            
            success, result = self.retry_with_backoff(self._insert_relationship_batch, unique_batch)
            
            if success:
                processed += len(unique_batch)
                self.progress['relationships_processed'] += len(unique_batch)
                logger.info(f"✅ Successfully inserted {len(unique_batch)} relationships")
            else:
                logger.error(f"❌ Failed to insert relationship batch: {result}")
                failed.extend(unique_batch)
                self.progress['failed_relationships'].extend(unique_batch)
            
            # Save checkpoint after each batch
            self.save_checkpoint()
        
        return processed, failed
    
    def _insert_relationship_batch(self, relationships: List[Dict]) -> bool:
        """
        Insert a batch of relationships within a transaction.
        """
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                for relationship in relationships:
                    # Extract relationship properties
                    source = relationship.get('source', relationship.get('from', relationship.get('start')))
                    target = relationship.get('target', relationship.get('to', relationship.get('end')))
                    rel_type = relationship.get('type', relationship.get('relationship', 'RELATED_TO'))
                    description = relationship.get('description', '')
                    
                    if not source or not target:
                        logger.warning(f"Skipping relationship with missing source/target: {relationship}")
                        continue
                    
                    # Relationship properties
                    properties = {
                        'description': description,
                        'created_at': datetime.now().isoformat(),
                        'source': 'lightrag_bridge'
                    }
                    
                    # Add any additional properties
                    for key, value in relationship.items():
                        if key not in ['source', 'target', 'type', 'from', 'to', 'start', 'end', 'relationship']:
                            properties[key] = value
                    
                    # Create relationship with dynamic type
                    rel_type_clean = rel_type.replace(' ', '_').upper()
                    query = f"""
                    MATCH (a {{name: $source}})
                    MATCH (b {{name: $target}})
                    MERGE (a)-[r:{rel_type_clean}]->(b)
                    SET r += $properties
                    """
                    
                    tx.run(query, source=source, target=target, properties=properties)
                
                # Commit transaction
                tx.commit()
                return True
    
    def save_checkpoint(self):
        """
        Save current progress to checkpoint file.
        """
        try:
            self.progress['last_checkpoint'] = datetime.now().isoformat()
            
            # Convert sets to lists for JSON serialization
            checkpoint_data = self.progress.copy()
            checkpoint_data['entity_hashes'] = list(self.progress['entity_hashes'])
            checkpoint_data['relationship_hashes'] = list(self.progress['relationship_hashes'])
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Checkpoint saved: {self.checkpoint_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")
    
    def load_checkpoint(self):
        """
        Load progress from checkpoint file to resume processing.
        """
        try:
            if not self.checkpoint_file.exists():
                logger.info("No checkpoint file found, starting fresh")
                return
            
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            # Convert lists back to sets
            self.progress.update(checkpoint_data)
            self.progress['entity_hashes'] = set(checkpoint_data.get('entity_hashes', []))
            self.progress['relationship_hashes'] = set(checkpoint_data.get('relationship_hashes', []))
            
            logger.info(f"✅ Checkpoint loaded: {checkpoint_data['last_checkpoint']}")
            logger.info(f"Progress: {self.progress['entities_processed']}/{self.progress['entities_total']} entities, "
                       f"{self.progress['relationships_processed']}/{self.progress['relationships_total']} relationships")
            
        except Exception as e:
            logger.error(f"❌ Failed to load checkpoint: {e}")
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive progress summary.
        """
        if self.progress['start_time']:
            elapsed = (datetime.now() - datetime.fromisoformat(self.progress['start_time'])).total_seconds()
            entities_rate = self.progress['entities_processed'] / elapsed if elapsed > 0 else 0
            relationships_rate = self.progress['relationships_processed'] / elapsed if elapsed > 0 else 0
        else:
            elapsed = 0
            entities_rate = 0
            relationships_rate = 0
        
        return {
            'entities': {
                'processed': self.progress['entities_processed'],
                'total': self.progress['entities_total'],
                'failed': len(self.progress['failed_entities']),
                'percentage': (self.progress['entities_processed'] / self.progress['entities_total'] * 100) if self.progress['entities_total'] > 0 else 0,
                'rate_per_second': entities_rate
            },
            'relationships': {
                'processed': self.progress['relationships_processed'],
                'total': self.progress['relationships_total'],
                'failed': len(self.progress['failed_relationships']),
                'percentage': (self.progress['relationships_processed'] / self.progress['relationships_total'] * 100) if self.progress['relationships_total'] > 0 else 0,
                'rate_per_second': relationships_rate
            },
            'elapsed_seconds': elapsed,
            'last_checkpoint': self.progress['last_checkpoint']
        }
    
    def run_bridge(self, entities_file: str = None, relationships_file: str = None) -> Dict[str, Any]:
        """
        Main bridge execution with comprehensive error handling and progress tracking.
        """
        try:
            # Override file paths if provided
            if entities_file:
                self.entities_file = Path(entities_file)
            if relationships_file:
                self.relationships_file = Path(relationships_file)
            
            # Initialize start time
            if not self.progress['start_time']:
                self.progress['start_time'] = datetime.now().isoformat()
            
            logger.info("🚀 Starting LightRAG → Neo4j Bridge")
            logger.info(f"Entities file: {self.entities_file}")
            logger.info(f"Relationships file: {self.relationships_file}")
            logger.info(f"Batch size: {self.batch_size}")
            
            # Connect to Neo4j
            if not self.connect_to_neo4j():
                return {"success": False, "error": "Failed to connect to Neo4j"}
            
            # Load data
            entities = self.load_lightrag_json(self.entities_file)
            relationships = self.load_lightrag_json(self.relationships_file)
            
            # Update totals
            self.progress['entities_total'] = len(entities)
            self.progress['relationships_total'] = len(relationships)
            
            logger.info(f"📊 Data loaded: {len(entities)} entities, {len(relationships)} relationships")
            
            # Process entities
            if entities:
                logger.info("🔄 Processing entities...")
                entities_processed, entities_failed = self.batch_insert_entities(entities)
                logger.info(f"✅ Entities complete: {entities_processed} processed, {len(entities_failed)} failed")
            
            # Process relationships
            if relationships:
                logger.info("🔄 Processing relationships...")
                relationships_processed, relationships_failed = self.batch_insert_relationships(relationships)
                logger.info(f"✅ Relationships complete: {relationships_processed} processed, {len(relationships_failed)} failed")
            
            # Final summary
            summary = self.get_progress_summary()
            logger.info("🎉 Bridge processing complete!")
            logger.info(f"📈 Final Summary:")
            logger.info(f"   Entities: {summary['entities']['processed']}/{summary['entities']['total']} ({summary['entities']['percentage']:.1f}%)")
            logger.info(f"   Relationships: {summary['relationships']['processed']}/{summary['relationships']['total']} ({summary['relationships']['percentage']:.1f}%)")
            logger.info(f"   Elapsed: {summary['elapsed_seconds']:.1f} seconds")
            
            return {
                "success": True,
                "summary": summary,
                "entities_processed": summary['entities']['processed'],
                "relationships_processed": summary['relationships']['processed'],
                "entities_failed": summary['entities']['failed'],
                "relationships_failed": summary['relationships']['failed']
            }
            
        except Exception as e:
            logger.error(f"❌ Bridge execution failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            # Cleanup
            if self.driver:
                self.driver.close()
                logger.info("Neo4j connection closed")
    
    def retry_failed_items(self) -> Dict[str, Any]:
        """
        Retry processing failed entities and relationships.
        """
        logger.info("🔄 Retrying failed items...")
        
        if not self.connect_to_neo4j():
            return {"success": False, "error": "Failed to connect to Neo4j"}
        
        try:
            # Retry failed entities
            if self.progress['failed_entities']:
                logger.info(f"Retrying {len(self.progress['failed_entities'])} failed entities...")
                entities_processed, entities_failed = self.batch_insert_entities(self.progress['failed_entities'])
                self.progress['failed_entities'] = entities_failed
                logger.info(f"Retry results: {entities_processed} entities recovered")
            
            # Retry failed relationships
            if self.progress['failed_relationships']:
                logger.info(f"Retrying {len(self.progress['failed_relationships'])} failed relationships...")
                relationships_processed, relationships_failed = self.batch_insert_relationships(self.progress['failed_relationships'])
                self.progress['failed_relationships'] = relationships_failed
                logger.info(f"Retry results: {relationships_processed} relationships recovered")
            
            # Save final checkpoint
            self.save_checkpoint()
            
            return {
                "success": True,
                "entities_recovered": entities_processed if self.progress['failed_entities'] else 0,
                "relationships_recovered": relationships_processed if self.progress['failed_relationships'] else 0,
                "entities_still_failed": len(self.progress['failed_entities']),
                "relationships_still_failed": len(self.progress['failed_relationships'])
            }
            
        except Exception as e:
            logger.error(f"❌ Retry failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            if self.driver:
                self.driver.close()
    
    async def bridge_to_neo4j_async(self, entities_file: str = None, relationships_file: str = None) -> bool:
        """
        Async wrapper for bridge execution that can be called from async contexts.
        """
        import concurrent.futures
        import asyncio
        
        try:
            # Run the synchronous bridge method in a thread pool
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.run_bridge, entities_file, relationships_file)
                result = await asyncio.get_event_loop().run_in_executor(None, lambda: future.result())
                return result.get("success", False)
        except Exception as e:
            logger.error(f"❌ Async bridge error: {e}")
            return False

def main():
    """
    Main execution function with command-line argument support.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="LightRAG → Neo4j Bridge")
    parser.add_argument("--entities", "-e", help="Path to entities JSON file", default="entities.json")
    parser.add_argument("--relationships", "-r", help="Path to relationships JSON file", default="relationships.json")
    parser.add_argument("--batch-size", "-b", type=int, default=500, help="Batch size for processing")
    parser.add_argument("--retry-failed", action="store_true", help="Retry only failed items from previous run")
    parser.add_argument("--checkpoint", "-c", help="Checkpoint file path", default="bridge_checkpoint.json")
    
    args = parser.parse_args()
    
    # Create bridge instance
    bridge = LightRAGNeo4jBridge(
        entities_file=args.entities,
        relationships_file=args.relationships,
        batch_size=args.batch_size,
        checkpoint_file=args.checkpoint
    )
    
    # Execute bridge
    if args.retry_failed:
        result = bridge.retry_failed_items()
    else:
        result = bridge.run_bridge()
    
    # Print results
    if result["success"]:
        print("✅ Bridge execution completed successfully!")
        if "summary" in result:
            print(f"📊 Entities: {result['entities_processed']} processed, {result['entities_failed']} failed")
            print(f"📊 Relationships: {result['relationships_processed']} processed, {result['relationships_failed']} failed")
    else:
        print(f"❌ Bridge execution failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()