#!/usr/bin/env python3
"""
Fix Graph Distribution - Create better distributed connectivity
Remove duplicates and self-references, create meaningful sparse connections
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphDistributionFixer:
    """Fixes graph distribution by removing duplicates and creating better connectivity"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Neo4j connection
        self.uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
    def fix_graph_distribution(self):
        """Main method to fix graph distribution"""
        
        logger.info("🔧 Fixing graph distribution...")
        
        # 1. Remove self-referential relationships
        logger.info("Removing self-referential relationships...")
        self.remove_self_references()
        
        # 2. Remove duplicate relationships  
        logger.info("Removing duplicate relationships...")
        self.remove_duplicate_relationships()
        
        # 3. Connect low-degree nodes to the main graph
        logger.info("Connecting low-degree nodes...")
        self.connect_low_degree_nodes()
        
        # 4. Create hub-and-spoke connections for better distribution
        logger.info("Creating hub-and-spoke connections...")
        self.create_hub_spoke_connections()
        
        # 5. Final verification
        self.verify_distribution()
        
    def remove_self_references(self):
        """Remove self-referential relationships"""
        
        with self.driver.session() as session:
            query = """
            MATCH (n)-[r]->(n)
            DELETE r
            RETURN count(r) as deleted_count
            """
            
            result = session.run(query)
            deleted_count = result.single()['deleted_count']
            logger.info(f"Removed {deleted_count} self-referential relationships")
    
    def remove_duplicate_relationships(self):
        """Remove duplicate relationships between the same nodes"""
        
        with self.driver.session() as session:
            # Find and remove duplicate relationships, keeping only one of each type
            query = """
            MATCH (a)-[r]->(b)
            WITH a, b, type(r) as rel_type, collect(r) as rels
            WHERE size(rels) > 1
            UNWIND rels[1..] as duplicate_rel
            DELETE duplicate_rel
            RETURN count(duplicate_rel) as deleted_duplicates
            """
            
            result = session.run(query)
            deleted_count = result.single()['deleted_duplicates']
            logger.info(f"Removed {deleted_count} duplicate relationships")
    
    def connect_low_degree_nodes(self):
        """Connect nodes with very few relationships to better distribute the graph"""
        
        created = 0
        
        with self.driver.session() as session:
            # Find nodes with ≤5 relationships
            query = """
            MATCH (n)
            WHERE n:ENTITY OR n:EQUIPMENT OR n:QSR_SPECIFIC OR n:TEMPERATURE OR n:PROCESS OR n:PROCEDURE
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as rel_count
            WHERE rel_count <= 5
            RETURN n, elementId(n) as node_id, labels(n) as labels, rel_count
            LIMIT 50
            """
            
            low_degree_nodes = session.run(query).data()
            
            for node_data in low_degree_nodes:
                node_id = node_data['node_id']
                labels = node_data['labels']
                rel_count = node_data['rel_count']
                
                # Connect to medium-degree nodes (not super hubs)
                target_label = self.get_target_label(labels)
                
                query = f"""
                MATCH (target:{target_label})
                OPTIONAL MATCH (target)-[r]-()
                WITH target, count(r) as target_rel_count
                WHERE target_rel_count > 10 AND target_rel_count < 100
                AND elementId(target) <> $node_id
                AND NOT EXISTS {{ (source)-[]-(target) WHERE elementId(source) = $node_id }}
                RETURN target, elementId(target) as target_id
                ORDER BY target_rel_count
                LIMIT 3
                """
                
                targets = session.run(query, node_id=node_id).data()
                
                for target in targets:
                    target_id = target['target_id']
                    
                    if self.create_relationship(node_id, "RELATED_TO", target_id):
                        created += 1
        
        logger.info(f"Created {created} connections for low-degree nodes")
        return created
    
    def create_hub_spoke_connections(self):
        """Create hub-and-spoke connections for better graph distribution"""
        
        created = 0
        
        with self.driver.session() as session:
            # Find medium-degree nodes to act as regional hubs
            query = """
            MATCH (hub)
            WHERE hub:EQUIPMENT OR hub:ENTITY
            OPTIONAL MATCH (hub)-[r]-()
            WITH hub, count(r) as hub_rel_count
            WHERE hub_rel_count > 50 AND hub_rel_count < 500
            RETURN hub, elementId(hub) as hub_id, labels(hub) as hub_labels, hub_rel_count
            ORDER BY hub_rel_count DESC
            LIMIT 10
            """
            
            regional_hubs = session.run(query).data()
            
            for hub_data in regional_hubs:
                hub_id = hub_data['hub_id']
                hub_labels = hub_data['hub_labels']
                
                # Connect isolated nodes to this regional hub
                query = """
                MATCH (isolated)
                WHERE isolated:QSR_SPECIFIC OR isolated:TEMPERATURE OR isolated:PROCESS OR isolated:PROCEDURE
                OPTIONAL MATCH (isolated)-[r]-()
                WITH isolated, count(r) as isolated_rel_count
                WHERE isolated_rel_count <= 10
                AND NOT EXISTS { (isolated)-[]-(hub) WHERE elementId(hub) = $hub_id }
                RETURN isolated, elementId(isolated) as isolated_id
                LIMIT 5
                """
                
                isolated_nodes = session.run(query, hub_id=hub_id).data()
                
                for isolated in isolated_nodes:
                    isolated_id = isolated['isolated_id']
                    
                    if self.create_relationship(isolated_id, "RELATED_TO", hub_id):
                        created += 1
        
        logger.info(f"Created {created} hub-spoke connections")
        return created
    
    def get_target_label(self, labels):
        """Get appropriate target label for connection"""
        
        if "ENTITY" in labels:
            return "EQUIPMENT"
        elif "EQUIPMENT" in labels:
            return "ENTITY"
        elif "QSR_SPECIFIC" in labels:
            return "EQUIPMENT"
        elif "TEMPERATURE" in labels:
            return "EQUIPMENT"
        elif "PROCESS" in labels:
            return "EQUIPMENT"
        elif "PROCEDURE" in labels:
            return "EQUIPMENT"
        else:
            return "ENTITY"
    
    def create_relationship(self, source_id: str, rel_type: str, target_id: str) -> bool:
        """Create a relationship between two nodes"""
        
        try:
            query = f"""
            MATCH (source), (target)
            WHERE elementId(source) = $source_id AND elementId(target) = $target_id
            AND NOT EXISTS {{ (source)-[:{rel_type}]-(target) }}
            CREATE (source)-[r:{rel_type}]->(target)
            RETURN r
            """
            
            with self.driver.session() as session:
                result = session.run(query, source_id=source_id, target_id=target_id)
                
                if result.single():
                    return True
                
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return False
        
        return False
    
    def verify_distribution(self):
        """Verify the distribution improvements"""
        
        logger.info("🔍 Verifying distribution improvements...")
        
        with self.driver.session() as session:
            # Check total relationships
            query = """
            MATCH ()-[r]->()
            RETURN count(r) as total_relationships
            """
            
            result = session.run(query)
            total_relationships = result.single()['total_relationships']
            logger.info(f"Total relationships after cleanup: {total_relationships}")
            
            # Check self-references
            query = """
            MATCH (n)-[r]->(n)
            RETURN count(r) as self_refs
            """
            
            result = session.run(query)
            self_refs = result.single()['self_refs']
            logger.info(f"Remaining self-references: {self_refs}")
            
            # Check duplicates
            query = """
            MATCH (a)-[r]->(b)
            WITH a, b, type(r) as rel_type, count(r) as rel_count
            WHERE rel_count > 1
            RETURN sum(rel_count - 1) as duplicate_count
            """
            
            result = session.run(query)
            duplicate_count = result.single()['duplicate_count'] or 0
            logger.info(f"Remaining duplicates: {duplicate_count}")
            
            # Check relationship distribution
            query = """
            MATCH (n)
            WHERE n:ENTITY OR n:EQUIPMENT OR n:QSR_SPECIFIC OR n:TEMPERATURE OR n:PROCESS OR n:PROCEDURE
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as rel_count
            RETURN 
                min(rel_count) as min_rels,
                max(rel_count) as max_rels,
                avg(rel_count) as avg_rels,
                count(n) as total_nodes,
                sum(CASE WHEN rel_count <= 5 THEN 1 ELSE 0 END) as low_degree_nodes,
                sum(CASE WHEN rel_count > 100 THEN 1 ELSE 0 END) as high_degree_nodes
            """
            
            result = session.run(query)
            record = result.single()
            
            logger.info(f"Relationship distribution:")
            logger.info(f"  Min: {record['min_rels']}, Max: {record['max_rels']}, Avg: {record['avg_rels']:.1f}")
            logger.info(f"  Total nodes: {record['total_nodes']}")
            logger.info(f"  Low-degree nodes (≤5): {record['low_degree_nodes']}")
            logger.info(f"  High-degree nodes (>100): {record['high_degree_nodes']}")
            
            # Check isolated nodes
            query = """
            MATCH (n)
            WHERE NOT EXISTS { (n)-[]-() }
            RETURN count(n) as isolated_count
            """
            
            result = session.run(query)
            isolated_count = result.single()['isolated_count']
            logger.info(f"Truly isolated nodes: {isolated_count}")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

def main():
    """Main execution function"""
    
    fixer = GraphDistributionFixer()
    
    try:
        fixer.fix_graph_distribution()
    except KeyboardInterrupt:
        logger.info("Distribution fix interrupted by user")
    except Exception as e:
        logger.error(f"Distribution fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fixer.close()

if __name__ == "__main__":
    main()