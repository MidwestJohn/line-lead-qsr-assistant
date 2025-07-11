#!/usr/bin/env python3
"""
Final Connectivity Boost - Target remaining weakly connected nodes
Focus on QSR_SPECIFIC, Visual Citations, and other low-connectivity nodes
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalConnectivityBooster:
    """Final pass to boost connectivity for remaining weakly connected nodes"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Neo4j connection
        self.uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
    def boost_all_connectivity(self):
        """Main method to boost connectivity for all weakly connected nodes"""
        
        logger.info("🚀 Final connectivity boost for weakly connected nodes...")
        
        total_created = 0
        
        # 1. Connect QSR_SPECIFIC nodes to the main graph
        logger.info("Connecting QSR_SPECIFIC nodes...")
        total_created += self.connect_qsr_specific_nodes()
        
        # 2. Connect Visual Citation nodes to entities
        logger.info("Connecting Visual Citation nodes...")
        total_created += self.connect_visual_citation_nodes()
        
        # 3. Connect Document nodes to the main graph
        logger.info("Connecting Document nodes...")
        total_created += self.connect_document_nodes()
        
        # 4. Create hub connections for better graph structure
        logger.info("Creating hub connections...")
        total_created += self.create_hub_connections()
        
        # 5. Connect remaining isolated nodes
        logger.info("Connecting remaining isolated nodes...")
        total_created += self.connect_remaining_isolated_nodes()
        
        logger.info(f"✅ Created {total_created} additional relationships")
        
        # Final verification
        self.final_verification()
        
    def connect_qsr_specific_nodes(self):
        """Connect QSR_SPECIFIC nodes with low connectivity to main graph"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get QSR_SPECIFIC nodes with ≤5 relationships
            query = """
            MATCH (q:QSR_SPECIFIC)
            OPTIONAL MATCH (q)-[r]-()
            WITH q, count(r) as rel_count
            WHERE rel_count <= 5
            RETURN q, elementId(q) as qsr_id, rel_count
            """
            
            weakly_connected_qsr = session.run(query).data()
            
            for qsr in weakly_connected_qsr:
                qsr_node = qsr['q']
                qsr_id = qsr['qsr_id']
                qsr_name = qsr_node.get('name', '').lower()
                qsr_desc = qsr_node.get('description', '').lower()
                
                # Connect to relevant Equipment nodes
                equipment_queries = []
                
                if any(term in qsr_name for term in ['frequency', 'daily', 'weekly', 'monthly']):
                    equipment_queries.append("cleaning")
                    equipment_queries.append("maintenance")
                
                if any(term in qsr_name for term in ['notice', 'warning', 'caution']):
                    equipment_queries.append("safety")
                    equipment_queries.append("equipment")
                
                if any(term in qsr_name for term in ['temperature', 'hot', 'cold']):
                    equipment_queries.append("taylor")
                    equipment_queries.append("fryer")
                
                # Default connections for generic QSR nodes
                if not equipment_queries:
                    equipment_queries = ["taylor", "equipment", "cleaning"]
                
                for equipment_term in equipment_queries:
                    query = f"""
                    MATCH (e:EQUIPMENT)
                    WHERE toLower(e.name) CONTAINS $equipment_term
                    OR toLower(e.description) CONTAINS $equipment_term
                    AND elementId(e) <> $qsr_id
                    AND NOT EXISTS {{ (q)-[]-(e) WHERE elementId(q) = $qsr_id }}
                    RETURN e, elementId(e) as equipment_id
                    LIMIT 2
                    """
                    
                    equipment_nodes = session.run(query, equipment_term=equipment_term, qsr_id=qsr_id).data()
                    
                    for equipment in equipment_nodes:
                        equipment_id = equipment['equipment_id']
                        
                        # Create relationship
                        rel_type = "GOVERNS" if "safety" in qsr_name else "RELATED_TO"
                        if self.create_relationship(qsr_id, rel_type, equipment_id):
                            created += 1
        
        return created
    
    def connect_visual_citation_nodes(self):
        """Connect Visual Citation nodes to entities they reference"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get Visual Citation nodes with ≤10 relationships  
            query = """
            MATCH (v:VisualCitation)
            OPTIONAL MATCH (v)-[r]-()
            WITH v, count(r) as rel_count
            WHERE rel_count <= 10
            RETURN v, elementId(v) as visual_id, rel_count
            LIMIT 50
            """
            
            weakly_connected_visuals = session.run(query).data()
            
            for visual in weakly_connected_visuals:
                visual_node = visual['v']
                visual_id = visual['visual_id']
                
                # Connect to entities on the same page
                page_refs = visual_node.get('page_refs', [])
                if page_refs:
                    query = """
                    MATCH (e)
                    WHERE (e:ENTITY OR e:EQUIPMENT OR e:QSR_SPECIFIC)
                    AND e.page_refs IS NOT NULL
                    AND any(page IN $page_refs WHERE page IN e.page_refs)
                    AND elementId(e) <> $visual_id
                    AND NOT EXISTS { (v)-[]-(e) WHERE elementId(v) = $visual_id }
                    RETURN e, elementId(e) as entity_id
                    LIMIT 3
                    """
                    
                    related_entities = session.run(query, page_refs=page_refs, visual_id=visual_id).data()
                    
                    for entity in related_entities:
                        entity_id = entity['entity_id']
                        
                        # Visual citation references entity
                        if self.create_relationship(visual_id, "HAS_VISUAL_REFERENCE", entity_id):
                            created += 1
        
        return created
    
    def connect_document_nodes(self):
        """Connect Document nodes to the main graph"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get Document nodes with ≤3 relationships
            query = """
            MATCH (d:Document)
            OPTIONAL MATCH (d)-[r]-()
            WITH d, count(r) as rel_count
            WHERE rel_count <= 3
            RETURN d, elementId(d) as doc_id, rel_count
            """
            
            weakly_connected_docs = session.run(query).data()
            
            for doc in weakly_connected_docs:
                doc_node = doc['d']
                doc_id = doc['doc_id']
                
                # Connect to entities with same document_id
                document_id = doc_node.get('document_id')
                if document_id:
                    query = """
                    MATCH (e)
                    WHERE (e:ENTITY OR e:EQUIPMENT OR e:QSR_SPECIFIC)
                    AND (e.document_id = $document_id OR e.document_source = $document_id)
                    AND elementId(e) <> $doc_id
                    AND NOT EXISTS { (d)-[]-(e) WHERE elementId(d) = $doc_id }
                    RETURN e, elementId(e) as entity_id
                    LIMIT 10
                    """
                    
                    related_entities = session.run(query, document_id=document_id, doc_id=doc_id).data()
                    
                    for entity in related_entities:
                        entity_id = entity['entity_id']
                        
                        # Document covers entity
                        if self.create_relationship(doc_id, "COVERS_EQUIPMENT", entity_id):
                            created += 1
        
        return created
    
    def create_hub_connections(self):
        """Create hub connections for better graph structure"""
        
        created = 0
        
        with self.driver.session() as session:
            # Connect high-degree nodes to create better graph structure
            # Find Equipment nodes with many relationships (hubs)
            query = """
            MATCH (e:EQUIPMENT)
            OPTIONAL MATCH (e)-[r]-()
            WITH e, count(r) as rel_count
            WHERE rel_count > 100
            RETURN e, elementId(e) as equipment_id, rel_count
            ORDER BY rel_count DESC
            LIMIT 5
            """
            
            hub_equipment = session.run(query).data()
            
            # Connect hub equipment to QSR_SPECIFIC nodes
            for hub in hub_equipment:
                hub_id = hub['equipment_id']
                
                query = """
                MATCH (q:QSR_SPECIFIC)
                WHERE NOT EXISTS { (q)-[]-(e) WHERE elementId(e) = $hub_id }
                RETURN q, elementId(q) as qsr_id
                LIMIT 10
                """
                
                qsr_nodes = session.run(query, hub_id=hub_id).data()
                
                for qsr in qsr_nodes:
                    qsr_id = qsr['qsr_id']
                    
                    if self.create_relationship(qsr_id, "RELATED_TO", hub_id):
                        created += 1
        
        return created
    
    def connect_remaining_isolated_nodes(self):
        """Connect any remaining isolated nodes"""
        
        created = 0
        
        with self.driver.session() as session:
            # Find truly isolated nodes (no relationships at all)
            query = """
            MATCH (n)
            WHERE NOT EXISTS { (n)-[]-() }
            AND NOT n:Document  # Skip document nodes we already handled
            RETURN n, elementId(n) as node_id, labels(n) as labels
            LIMIT 10
            """
            
            isolated_nodes = session.run(query).data()
            
            for node in isolated_nodes:
                node_id = node['node_id']
                labels = node['labels']
                
                # Connect to a relevant hub node
                if "QSR_SPECIFIC" in labels:
                    target_label = "EQUIPMENT"
                elif "ENTITY" in labels:
                    target_label = "EQUIPMENT"
                else:
                    target_label = "ENTITY"
                
                query = f"""
                MATCH (target:{target_label})
                OPTIONAL MATCH (target)-[r]-()
                WITH target, count(r) as rel_count
                WHERE rel_count > 10
                RETURN target, elementId(target) as target_id
                ORDER BY rel_count DESC
                LIMIT 1
                """
                
                targets = session.run(query).data()
                
                if targets:
                    target_id = targets[0]['target_id']
                    
                    if self.create_relationship(node_id, "RELATED_TO", target_id):
                        created += 1
        
        return created
    
    def create_relationship(self, source_id: str, rel_type: str, target_id: str) -> bool:
        """Create a relationship between two nodes using elementId"""
        
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
    
    def final_verification(self):
        """Final verification of graph connectivity"""
        
        logger.info("🔍 Final verification of graph connectivity...")
        
        with self.driver.session() as session:
            # Check truly isolated nodes
            query = """
            MATCH (n)
            WHERE NOT EXISTS { (n)-[]-() }
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            results = session.run(query).data()
            total_isolated = sum(record['count'] for record in results)
            
            if total_isolated == 0:
                logger.info("✅ No completely isolated nodes!")
            else:
                logger.info(f"⚠️  {total_isolated} completely isolated nodes remain:")
                for record in results:
                    labels = record['labels']
                    count = record['count']
                    logger.info(f"  {labels}: {count}")
            
            # Check weakly connected nodes
            query = """
            MATCH (n)
            WHERE n:ENTITY OR n:EQUIPMENT OR n:QSR_SPECIFIC OR n:TEMPERATURE
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as rel_count
            WHERE rel_count <= 3
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            results = session.run(query).data()
            total_weakly_connected = sum(record['count'] for record in results)
            
            logger.info(f"Weakly connected nodes (≤3 relationships): {total_weakly_connected}")
            for record in results:
                labels = record['labels']
                count = record['count']
                logger.info(f"  {labels}: {count}")
            
            # Check total relationships
            query = """
            MATCH ()-[r]->()
            RETURN count(r) as total_relationships
            """
            
            result = session.run(query)
            total_relationships = result.single()['total_relationships']
            logger.info(f"Total relationships: {total_relationships}")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

def main():
    """Main execution function"""
    
    booster = FinalConnectivityBooster()
    
    try:
        booster.boost_all_connectivity()
    except KeyboardInterrupt:
        logger.info("Connectivity boost interrupted by user")
    except Exception as e:
        logger.error(f"Connectivity boost failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        booster.close()

if __name__ == "__main__":
    main()