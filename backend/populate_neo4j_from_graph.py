#!/usr/bin/env python3
"""
Populate Neo4j with the actual knowledge graph data from LlamaIndex.
This script reads the rich graph data from graph_store.json and properly transfers it to Neo4j.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.neo4j_service import neo4j_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='.env.rag')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_graph_data():
    """Load the knowledge graph data from LlamaIndex storage."""
    graph_store_path = "./data/rag_storage/kg_index/graph_store.json"
    
    if not os.path.exists(graph_store_path):
        logger.error(f"Graph store not found: {graph_store_path}")
        return None
    
    with open(graph_store_path, 'r') as f:
        data = json.load(f)
    
    return data.get('graph_dict', {})

def clean_neo4j():
    """Clean existing Neo4j data."""
    logger.info("Cleaning existing Neo4j data...")
    
    # Connect to Neo4j
    try:
        neo4j_service.connect()
        if not neo4j_service.connected:
            logger.error("Cannot connect to Neo4j")
            return False
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        return False
    
    with neo4j_service.driver.session() as session:
        # Delete all relationships first
        session.run("MATCH ()-[r]-() DELETE r")
        
        # Delete all nodes
        session.run("MATCH (n) DELETE n")
        
        # Verify cleanup
        result = session.run("MATCH (n) RETURN count(n) as count")
        remaining = result.single()["count"]
        logger.info(f"Cleanup complete. Remaining nodes: {remaining}")
        
    return True

def populate_neo4j_with_graph_data(graph_dict):
    """Populate Neo4j with the rich knowledge graph data."""
    logger.info(f"Populating Neo4j with {len(graph_dict)} entities and their relationships...")
    
    try:
        neo4j_service.connect()
        if not neo4j_service.connected:
            logger.error("Cannot connect to Neo4j")
            return False
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        return False
    
    nodes_created = 0
    relationships_created = 0
    
    with neo4j_service.driver.session() as session:
        # First pass: Create all entity nodes
        for entity_name, relationships in graph_dict.items():
            # Clean entity name for Neo4j
            clean_entity_name = entity_name.replace("'", "").replace('"', '')
            
            # Determine entity type based on content
            entity_type = determine_entity_type(entity_name, relationships)
            
            # Create entity node
            session.run(
                f"MERGE (e:Entity:{entity_type} {{name: $name, original_name: $original_name}})",
                name=clean_entity_name,
                original_name=entity_name
            )
            nodes_created += 1
            
            if nodes_created % 10 == 0:
                logger.info(f"Created {nodes_created} entity nodes...")
        
        logger.info(f"Created {nodes_created} entity nodes")
        
        # Second pass: Create relationships
        for entity_name, relationships in graph_dict.items():
            clean_entity_name = entity_name.replace("'", "").replace('"', '')
            
            for relationship in relationships:
                if len(relationship) >= 2:
                    relation_type = relationship[0].upper().replace(" ", "_")
                    target_entity = relationship[1].replace("'", "").replace('"', '')
                    
                    # Create relationship
                    session.run(
                        """
                        MATCH (source:Entity {name: $source_name})
                        MATCH (target:Entity {name: $target_name})
                        MERGE (source)-[r:RELATIONSHIP {type: $relation_type, original_text: $original_text}]->(target)
                        """,
                        source_name=clean_entity_name,
                        target_name=target_entity,
                        relation_type=relation_type,
                        original_text=" ".join(relationship)
                    )
                    relationships_created += 1
                    
                    if relationships_created % 50 == 0:
                        logger.info(f"Created {relationships_created} relationships...")
        
        logger.info(f"Created {relationships_created} relationships")
        
        # Add summary statistics
        session.run(
            """
            CREATE (stats:GraphStats {
                entities_loaded: $entities,
                relationships_loaded: $relationships,
                load_timestamp: datetime(),
                source: 'LlamaIndex_QSR_Graph'
            })
            """,
            entities=nodes_created,
            relationships=relationships_created
        )
        
    return True

def determine_entity_type(entity_name, relationships):
    """Determine the entity type based on name and relationships."""
    entity_lower = entity_name.lower()
    
    # Equipment patterns
    if any(term in entity_lower for term in ['c602', 'machine', 'freezer', 'equipment', 'model']):
        return "Equipment"
    
    # Brand patterns
    elif any(term in entity_lower for term in ['taylor', 'company']):
        return "Brand"
    
    # Procedure patterns
    elif any(term in entity_lower for term in ['manual', 'cleaning', 'maintenance', 'service']):
        return "Procedure"
    
    # Safety patterns
    elif any(term in entity_lower for term in ['safety', 'warning', 'protection']):
        return "Safety"
    
    # Component patterns
    elif any(term in entity_lower for term in ['assembly', 'sensor', 'heater', 'coupling']):
        return "Component"
    
    # Default
    else:
        return "Concept"

def verify_population():
    """Verify the Neo4j population was successful."""
    logger.info("Verifying Neo4j population...")
    
    with neo4j_service.driver.session() as session:
        # Count nodes by type
        result = session.run("""
            MATCH (n:Entity)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
        """)
        
        logger.info("Node counts by type:")
        total_nodes = 0
        for record in result:
            labels = record["labels"]
            count = record["count"]
            total_nodes += count
            logger.info(f"  {labels}: {count}")
        
        # Count relationships
        rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        total_relationships = rel_result.single()["count"]
        
        logger.info(f"Total nodes: {total_nodes}")
        logger.info(f"Total relationships: {total_relationships}")
        
        # Sample some entities
        sample_result = session.run("""
            MATCH (n:Equipment)
            RETURN n.name as name
            LIMIT 5
        """)
        
        logger.info("Sample equipment entities:")
        for record in sample_result:
            logger.info(f"  - {record['name']}")
        
        return total_nodes, total_relationships

def main():
    """Main function to populate Neo4j with knowledge graph data."""
    logger.info("=== Neo4j Knowledge Graph Population ===")
    
    # Load graph data
    logger.info("Loading knowledge graph data from LlamaIndex...")
    graph_dict = load_graph_data()
    
    if not graph_dict:
        logger.error("No graph data found")
        return
    
    logger.info(f"Loaded graph data for {len(graph_dict)} entities")
    
    # Clean Neo4j
    if not clean_neo4j():
        logger.error("Failed to clean Neo4j")
        return
    
    # Populate Neo4j
    if not populate_neo4j_with_graph_data(graph_dict):
        logger.error("Failed to populate Neo4j")
        return
    
    # Verify population
    total_nodes, total_relationships = verify_population()
    
    logger.info("=== Population Complete ===")
    logger.info(f"Successfully loaded {total_nodes} nodes and {total_relationships} relationships")
    logger.info("You can now explore the rich knowledge graph in Neo4j Browser!")

if __name__ == "__main__":
    main()