#!/usr/bin/env python3
"""
Unified Neo4j Service - Fix Connection Context Isolation
==================================================

Creates a shared Neo4j connection context accessible by all components.
Uses the same configuration that works for backend health checks.
"""

import os
import time
from neo4j import GraphDatabase
import json
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class UnifiedNeo4jService:
    """Unified Neo4j service accessible by all components."""
    
    def __init__(self):
        self.driver: Optional[GraphDatabase] = None
        self.connected: bool = False
        self.connection_config: Dict[str, Any] = {}
        
    def initialize_from_backend_config(self):
        """Initialize using the same configuration that works for backend health checks."""
        
        # Load environment variables from the same location as backend
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env.local'))
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env.production'))
        
        # Extract working configuration from backend environment
        self.connection_config = {
            "uri": os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io'),
            "username": os.getenv('NEO4J_USERNAME', 'neo4j'),
            "password": os.getenv('NEO4J_PASSWORD'),
            "database": os.getenv('NEO4J_DATABASE', 'neo4j'),
            # Aura-optimized settings (encryption handled by URI scheme)
            "max_connection_lifetime": 3600,
            "max_connection_pool_size": 50,
            "connection_acquisition_timeout": 60
        }
        
        # Try to get password from different sources
        if not self.connection_config["password"]:
            # Try keyring if available
            try:
                import keyring
                password = keyring.get_password("memex", "NEO4J_PASSWORD")
                if password:
                    self.connection_config["password"] = password
                    logger.info("✅ Found Neo4j password in keyring")
            except ImportError:
                pass
        
        # For now, let's extract the connection from the successful backend context
        # since the backend is successfully connecting to Aura
        if not self.connection_config["password"]:
            logger.info("🔄 NEO4J_PASSWORD not found in environment, extracting from backend context...")
            return self._extract_from_backend_context()
        
        try:
            logger.info(f"🔌 Connecting to: {self.connection_config['uri']}")
            
            # Create driver with same settings as successful backend connection
            self.driver = GraphDatabase.driver(
                self.connection_config["uri"],
                auth=(self.connection_config["username"], self.connection_config["password"]),
                max_connection_lifetime=self.connection_config["max_connection_lifetime"],
                max_connection_pool_size=self.connection_config["max_connection_pool_size"],
                connection_acquisition_timeout=self.connection_config["connection_acquisition_timeout"]
            )
            
            # Test connection
            with self.driver.session(database=self.connection_config["database"]) as session:
                result = session.run("RETURN 'Connection successful' as status")
                status = result.single()["status"]
                logger.info(f"✅ Unified Neo4j service connected: {status}")
                
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Unified Neo4j connection failed: {e}")
            self.connected = False
            return False
    
    def _extract_from_backend_context(self):
        """Extract connection from working backend context."""
        
        try:
            # Import the working Neo4j service from backend
            import sys
            import os
            
            # Add backend to path
            backend_path = os.path.dirname(__file__)
            if backend_path not in sys.path:
                sys.path.append(backend_path)
            
            from services.neo4j_service import neo4j_service
            
            if neo4j_service and neo4j_service.connected:
                logger.info("✅ Found working backend Neo4j service")
                
                # Use the same driver from the working service
                self.driver = neo4j_service.driver
                self.connected = True
                self._using_backend_driver = True  # Flag to not close the shared driver
                
                # Extract connection config
                self.connection_config = {
                    "uri": getattr(neo4j_service, 'uri', 'neo4j+s://57ed0189.databases.neo4j.io'),
                    "username": getattr(neo4j_service, 'username', 'neo4j'),
                    "database": getattr(neo4j_service, 'database', 'neo4j')
                }
                
                logger.info("✅ Unified service using backend's working connection")
                return True
            else:
                logger.error("❌ Backend Neo4j service not connected")
                return False
                
        except Exception as e:
            logger.error(f"❌ Could not extract from backend context: {e}")
            return False
    
    def get_session(self):
        """Get Neo4j session for database operations."""
        if not self.connected or not self.driver:
            raise RuntimeError("Neo4j service not connected. Call initialize_from_backend_config() first.")
        
        return self.driver.session(database=self.connection_config.get("database", "neo4j"))
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        try:
            with self.get_session() as session:
                # Test read
                result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                node_count = result.single()["total_nodes"]
                
                # Test write
                test_id = f"test_{int(time.time())}"
                session.run("""
                    CREATE (t:ConnectionTest {
                        id: $test_id,
                        timestamp: datetime(),
                        component: 'unified_service'
                    })
                """, test_id=test_id)
                
                # Verify write
                result = session.run("""
                    MATCH (t:ConnectionTest {id: $test_id})
                    RETURN count(t) as created
                """, test_id=test_id)
                
                created_count = result.single()["created"]
                
                # Cleanup
                session.run("MATCH (t:ConnectionTest {id: $test_id}) DELETE t", test_id=test_id)
                
                return {
                    "connected": True,
                    "can_read": True,
                    "can_write": created_count > 0,
                    "current_nodes": node_count,
                    "uri": self.connection_config.get("uri", "unknown"),
                    "database": self.connection_config.get("database", "neo4j")
                }
                
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "uri": self.connection_config.get("uri", "unknown")
            }
    
    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        if not self.connected or not self.driver:
            raise RuntimeError("Neo4j service not connected. Call initialize_from_backend_config() first.")
        
        try:
            with self.get_session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise e
    
    def close(self):
        """Close connection."""
        if self.driver and not getattr(self, '_using_backend_driver', False):
            self.driver.close()
        self.connected = False

# Global instance for all components to use
unified_neo4j = UnifiedNeo4jService()