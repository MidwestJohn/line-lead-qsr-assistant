import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load RAG environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.rag'))

class Neo4jService:
    """Neo4j service optimized for Aura cloud connections"""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USERNAME')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to Neo4j with Aura-optimized settings"""
        try:
            from neo4j import GraphDatabase
            
            # Aura-optimized driver configuration
            # Note: neo4j+s:// URI already includes SSL, don't specify encrypted=True
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=10,      # Reduced for Aura
                connection_acquisition_timeout=60  # Increased for cloud latency
            )
            
            # Test connection
            self.driver.verify_connectivity()
            self.connected = True
            
            logger.info(f"✅ Connected to Neo4j Aura: {self.uri}")
            return True
            
        except ImportError:
            logger.error("❌ Neo4j Python driver not installed")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j Aura: {e}")
            self.connected = False
            return False
    
    async def count_nodes_and_relationships(self) -> Dict[str, int]:
        """Count nodes and relationships in Neo4j"""
        try:
            if not self.connected:
                self.connect()
            
            with self.driver.session() as session:
                # Count nodes
                nodes_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = nodes_result.single()["count"]
                
                # Count relationships
                rels_result = session.run("MATCH ()-[r]-() RETURN count(r) as count")
                rel_count = rels_result.single()["count"]
                
                return {
                    "nodes": node_count,
                    "relationships": rel_count
                }
                
        except Exception as e:
            logger.error(f"❌ Error counting Neo4j data: {e}")
            return {"nodes": 0, "relationships": 0}
    
    def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.connected = False
            logger.info("Neo4j connection closed")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Neo4j connection with Aura-specific checks"""
        if not self.connected:
            if not self.connect():
                return {
                    "status": "disconnected",
                    "connected": False,
                    "error": "Failed to establish connection"
                }
        
        try:
            with self.driver.session() as session:
                # Test basic query
                result = session.run("RETURN 'Hello Neo4j Aura!' as message, timestamp() as time")
                record = result.single()
                
                # Test database info query
                db_info = session.run("CALL dbms.components() YIELD name, versions, edition")
                components = list(db_info)
                
                return {
                    "status": "connected",
                    "connected": True,
                    "uri": self.uri,
                    "test_query_success": True,
                    "message": record["message"],
                    "timestamp": record["time"],
                    "database_responsive": True,
                    "database_info": {
                        "components": [{"name": comp["name"], "versions": comp["versions"], "edition": comp["edition"]} for comp in components]
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Neo4j test query failed: {e}")
            return {
                "status": "connection_error",
                "connected": False,
                "error": str(e),
                "test_query_success": False,
                "database_responsive": False
            }
    
    def validate_aura_connection(self) -> Dict[str, Any]:
        """Validate Aura-specific connection requirements."""
        issues = []
        
        if not self.uri or not self.uri.startswith('neo4j+s://'):
            issues.append("Aura URI must start with 'neo4j+s://' for SSL connection")
        
        if not self.uri or '.databases.neo4j.io' not in self.uri:
            issues.append("URI should contain '.databases.neo4j.io' for Aura instances")
        
        if self.username != 'neo4j':
            issues.append("Aura username should be 'neo4j'")
        
        if not self.password or len(self.password) < 8:
            issues.append("Aura password appears to be missing or too short")
        
        # Additional Aura-specific checks
        if self.uri and not self.uri.endswith('.databases.neo4j.io'):
            issues.append("Aura URI should end with '.databases.neo4j.io'")
        
        return {
            "aura_configuration_valid": len(issues) == 0,
            "issues_found": issues,
            "connection_type": "neo4j_aura_cloud",
            "configuration": {
                "uri": self.uri,
                "username": self.username,
                "password_length": len(self.password) if self.password else 0,
                "ssl_enabled": self.uri.startswith('neo4j+s://') if self.uri else False
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status for Aura connection"""
        validation = self.validate_aura_connection()
        
        if not validation["aura_configuration_valid"]:
            return {
                "healthy": False,
                "connection_test": None,
                "validation": validation,
                "error": "Configuration validation failed"
            }
        
        connection_test = self.test_connection()
        
        return {
            "healthy": connection_test.get("connected", False),
            "connection_test": connection_test,
            "validation": validation,
            "aura_optimized": True
        }
    
    def execute_query(self, query: str, parameters: Dict = None) -> Dict[str, Any]:
        """Execute a query on Neo4j Aura with error handling"""
        if not self.connected:
            if not self.connect():
                return {"error": "Not connected to Neo4j", "success": False}
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                records = [record.data() for record in result]
                
                return {
                    "success": True,
                    "records": records,
                    "count": len(records)
                }
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def get_node_count(self) -> int:
        """Get total node count in Neo4j."""
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            return result.single()["count"]

    def get_relationship_count(self) -> int:
        """Get total relationship count in Neo4j."""
        with self.driver.session() as session:
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            return result.single()["count"]

    def get_sample_entities(self, limit: int = 10) -> list:
        """Get sample entities from Neo4j."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.name IS NOT NULL
                RETURN n.name as name, labels(n) as labels
                LIMIT $limit
            """, limit=limit)
            return [dict(record) for record in result]
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics for optimization tracking."""
        try:
            if not self.connected:
                self.connect()
            
            with self.driver.session() as session:
                # Get total counts
                node_result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                total_nodes = node_result.single()["total_nodes"]
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")  
                total_relationships = rel_result.single()["total_relationships"]
                
                # Get node types (labels)
                type_result = session.run("""
                    MATCH (n) 
                    WITH labels(n) as labels 
                    UNWIND labels as label
                    RETURN label, count(*) as count
                    ORDER BY count DESC
                """)
                
                node_types = {}
                for record in type_result:
                    node_types[record["label"]] = record["count"]
                
                # Get relationship types
                rel_type_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as relationship_type, count(*) as count
                    ORDER BY count DESC
                """)
                
                relationship_types = {}
                for record in rel_type_result:
                    relationship_types[record["relationship_type"]] = record["count"]
                
                return {
                    "total_nodes": total_nodes,
                    "total_relationships": total_relationships,
                    "node_types": node_types,
                    "relationship_types": relationship_types,
                    "statistics_timestamp": "current"
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting graph statistics: {e}")
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "node_types": {},
                "relationship_types": {},
                "error": str(e)
            }
    
    def __del__(self):
        """Cleanup on destruction"""
        self.disconnect()

# Global instance
neo4j_service = Neo4jService()