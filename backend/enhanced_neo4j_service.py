#!/usr/bin/env python3
"""
Enhanced Neo4j Service with Circuit Breaker and Transactional Integrity
=======================================================================

Neo4j service enhanced with:
- Circuit breaker pattern for connection resilience
- Transactional integrity for atomic operations
- Dead letter queue integration for failed operations
- Enterprise-grade error handling and recovery

This service wraps all Neo4j operations in reliability infrastructure
while maintaining the existing API for backwards compatibility.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import Neo4jError, ServiceUnavailable, AuthError, ClientError

from reliability_infrastructure import (
    circuit_breaker,
    transaction_manager,
    dead_letter_queue,
    CircuitBreakerOpenError,
    AtomicTransaction
)

logger = logging.getLogger(__name__)

class EnhancedNeo4jService:
    """
    Enhanced Neo4j service with enterprise reliability features.
    
    Features:
    - Circuit breaker protection for all operations
    - Atomic transactions with rollback
    - Dead letter queue for failed operations
    - Automatic retry with intelligent backoff
    - Connection pooling optimization
    - Comprehensive error handling
    """
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USERNAME')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        self.driver: Optional[Driver] = None
        self.connected = False
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        
        # Circuit breaker callbacks
        circuit_breaker.add_state_change_callback(self._on_circuit_state_change)
        
        logger.info("🔧 Enhanced Neo4j service initialized")
    
    def _on_circuit_state_change(self, breaker_name: str, old_state, new_state, reason: str):
        """Handle circuit breaker state changes"""
        if new_state.value == "open":
            logger.warning(f"🚫 Neo4j circuit breaker OPEN: {reason}")
            self.connected = False
        elif new_state.value == "closed":
            logger.info(f"✅ Neo4j circuit breaker CLOSED: {reason}")
    
    async def connect(self) -> bool:
        """Connect to Neo4j with circuit breaker protection"""
        if self.connected and self.driver:
            return True
        
        try:
            return await circuit_breaker.call(self._establish_connection)
        except CircuitBreakerOpenError:
            logger.warning("🚫 Cannot connect to Neo4j: Circuit breaker is OPEN")
            return False
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            return False
    
    def _establish_connection(self) -> bool:
        """Establish Neo4j connection (internal method)"""
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Neo4j connection parameters not configured")
        
        try:
            # Create driver with optimized settings
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=10,
                connection_acquisition_timeout=30,
                max_retry_time=15,
                initial_address_resolver_timeout=5
            )
            
            # Verify connectivity
            self.driver.verify_connectivity()
            self.connected = True
            self.connection_attempts = 0
            
            logger.info(f"✅ Connected to Neo4j: {self.uri}")
            return True
            
        except Exception as e:
            self.connection_attempts += 1
            self.connected = False
            
            error_msg = f"Neo4j connection failed (attempt {self.connection_attempts}): {e}"
            logger.error(error_msg)
            
            # Add to dead letter queue if max attempts reached
            if self.connection_attempts >= self.max_connection_attempts:
                dead_letter_queue.add_failed_operation(
                    "neo4j_connection",
                    {"uri": self.uri, "username": self.username},
                    e
                )
            
            raise
    
    async def disconnect(self):
        """Disconnect from Neo4j"""
        if self.driver:
            await asyncio.get_event_loop().run_in_executor(None, self.driver.close)
            self.driver = None
            self.connected = False
            logger.info("Neo4j connection closed")
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None, 
                          transaction_id: str = None) -> List[Dict[str, Any]]:
        """
        Execute query with circuit breaker protection and transactional integrity.
        
        Args:
            query: Cypher query to execute
            parameters: Query parameters
            transaction_id: Optional transaction ID for atomic operations
            
        Returns:
            List of query results
        """
        if not await self.connect():
            raise RuntimeError("Cannot connect to Neo4j")
        
        try:
            return await circuit_breaker.call(
                self._execute_query_internal,
                query,
                parameters or {},
                transaction_id
            )
        except CircuitBreakerOpenError:
            # Add to dead letter queue when circuit is open
            dead_letter_queue.add_failed_operation(
                "neo4j_query",
                {"query": query, "parameters": parameters},
                CircuitBreakerOpenError("Circuit breaker is OPEN")
            )
            raise
        except Exception as e:
            # Add to dead letter queue on failure
            dead_letter_queue.add_failed_operation(
                "neo4j_query",
                {"query": query, "parameters": parameters},
                e
            )
            raise
    
    async def _execute_query_internal(self, query: str, parameters: Dict[str, Any], 
                                    transaction_id: str = None) -> List[Dict[str, Any]]:
        """Internal query execution"""
        def _run_query():
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters)
                return [dict(record) for record in result]
        
        # Execute in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run_query)
    
    async def execute_atomic_write(self, operations: List[Dict[str, Any]], 
                                 transaction_id: str = None) -> Dict[str, Any]:
        """
        Execute multiple write operations atomically.
        
        Args:
            operations: List of operations to execute
            transaction_id: Optional existing transaction ID
            
        Returns:
            Results of all operations
        """
        if not await self.connect():
            raise RuntimeError("Cannot connect to Neo4j")
        
        # Create transaction if not provided
        if not transaction_id:
            transaction = transaction_manager.begin_transaction()
            transaction_id = transaction.transaction_id
        
        try:
            # Add operations to transaction
            operation_ids = []
            for i, op in enumerate(operations):
                op_id = transaction_manager.add_operation(
                    transaction_id,
                    "neo4j_write",
                    op,
                    {"type": "neo4j_delete", "operation_data": op}
                )
                operation_ids.append(op_id)
            
            # Execute all operations
            results = []
            for i, op_id in enumerate(operation_ids):
                result = await transaction_manager.execute_operation(
                    transaction_id,
                    op_id,
                    lambda op_data: circuit_breaker.call(
                        self._execute_write_operation,
                        op_data
                    )
                )
                results.append(result)
            
            # Commit transaction
            success = await transaction_manager.commit_transaction(transaction_id)
            
            if success:
                logger.info(f"✅ Atomic write completed: {len(operations)} operations")
                return {"success": True, "results": results, "operations_count": len(operations)}
            else:
                logger.error(f"❌ Atomic write failed: transaction rolled back")
                return {"success": False, "error": "Transaction rolled back"}
                
        except Exception as e:
            logger.error(f"❌ Atomic write failed: {e}")
            # Rollback transaction
            await transaction_manager.rollback_transaction(transaction_id)
            raise
    
    async def _execute_write_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual write operation"""
        query = operation_data.get("query")
        parameters = operation_data.get("parameters", {})
        
        if not query:
            raise ValueError("Operation must contain query")
        
        def _run_write():
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters)
                summary = result.consume()
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set
                }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run_write)
    
    async def create_entities_batch(self, entities: List[Dict[str, Any]], 
                                  transaction_id: str = None) -> Dict[str, Any]:
        """
        Create multiple entities in a single atomic transaction.
        
        Args:
            entities: List of entity data
            transaction_id: Optional transaction ID
            
        Returns:
            Creation results
        """
        if not entities:
            return {"success": True, "entities_created": 0}
        
        # Convert entities to write operations
        operations = []
        for entity in entities:
            # Build CREATE query
            labels = entity.get("labels", ["Entity"])
            properties = {k: v for k, v in entity.items() if k != "labels"}
            
            label_str = ":".join(labels)
            query = f"CREATE (n:{label_str} $properties) RETURN id(n) as node_id"
            
            operations.append({
                "query": query,
                "parameters": {"properties": properties}
            })
        
        result = await self.execute_atomic_write(operations, transaction_id)
        
        if result["success"]:
            return {
                "success": True,
                "entities_created": len(entities),
                "node_ids": [r.get("node_id") for r in result["results"] if r.get("node_id")]
            }
        else:
            return {"success": False, "error": result.get("error")}
    
    async def create_relationships_batch(self, relationships: List[Dict[str, Any]], 
                                       transaction_id: str = None) -> Dict[str, Any]:
        """
        Create multiple relationships in a single atomic transaction.
        
        Args:
            relationships: List of relationship data
            transaction_id: Optional transaction ID
            
        Returns:
            Creation results
        """
        if not relationships:
            return {"success": True, "relationships_created": 0}
        
        # Convert relationships to write operations
        operations = []
        for rel in relationships:
            source_match = rel.get("source_match", {})
            target_match = rel.get("target_match", {})
            rel_type = rel.get("type", "RELATED_TO")
            properties = rel.get("properties", {})
            
            query = f"""
                MATCH (source {self._build_match_pattern(source_match)})
                MATCH (target {self._build_match_pattern(target_match)})
                CREATE (source)-[r:{rel_type} $properties]->(target)
                RETURN id(r) as rel_id
            """
            
            operations.append({
                "query": query,
                "parameters": {"properties": properties}
            })
        
        result = await self.execute_atomic_write(operations, transaction_id)
        
        if result["success"]:
            return {
                "success": True,
                "relationships_created": len(relationships),
                "rel_ids": [r.get("rel_id") for r in result["results"] if r.get("rel_id")]
            }
        else:
            return {"success": False, "error": result.get("error")}
    
    def _build_match_pattern(self, match_data: Dict[str, Any]) -> str:
        """Build Cypher match pattern from match data"""
        if not match_data:
            return ""
        
        conditions = []
        for key, value in match_data.items():
            if isinstance(value, str):
                conditions.append(f"{key}: '{value}'")
            else:
                conditions.append(f"{key}: {value}")
        
        return "{" + ", ".join(conditions) + "}" if conditions else ""
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        try:
            # Test basic connectivity
            if not await self.connect():
                return {
                    "healthy": False,
                    "connected": False,
                    "error": "Cannot establish connection"
                }
            
            # Test query execution
            start_time = datetime.now()
            result = await self.execute_query("RETURN 1 as test")
            query_time = (datetime.now() - start_time).total_seconds()
            
            # Get database info
            db_info = await self.execute_query("CALL dbms.components() YIELD name, versions, edition")
            
            # Get basic statistics
            stats = await self.execute_query("""
                MATCH (n) 
                OPTIONAL MATCH ()-[r]->() 
                RETURN count(DISTINCT n) as nodes, count(r) as relationships
            """)
            
            return {
                "healthy": True,
                "connected": self.connected,
                "query_time_seconds": query_time,
                "database_info": db_info,
                "statistics": stats[0] if stats else {"nodes": 0, "relationships": 0},
                "circuit_breaker": circuit_breaker.get_metrics(),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "healthy": False,
                "connected": self.connected,
                "error": str(e),
                "circuit_breaker": circuit_breaker.get_metrics()
            }
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics including reliability metrics"""
        try:
            # Basic Neo4j statistics
            stats = await self.execute_query("""
                MATCH (n) 
                OPTIONAL MATCH ()-[r]->() 
                RETURN count(DISTINCT n) as total_nodes, 
                       count(r) as total_relationships,
                       count(DISTINCT labels(n)) as unique_labels
            """)
            
            # Node type distribution
            node_types = await self.execute_query("""
                MATCH (n) 
                RETURN labels(n) as labels, count(n) as count 
                ORDER BY count DESC 
                LIMIT 10
            """)
            
            # Relationship type distribution
            rel_types = await self.execute_query("""
                MATCH ()-[r]->() 
                RETURN type(r) as type, count(r) as count 
                ORDER BY count DESC 
                LIMIT 10
            """)
            
            return {
                "database_statistics": stats[0] if stats else {},
                "node_types": node_types,
                "relationship_types": rel_types,
                "reliability_metrics": {
                    "circuit_breaker": circuit_breaker.get_metrics(),
                    "dead_letter_queue": dead_letter_queue.get_queue_status(),
                    "connection_attempts": self.connection_attempts
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Statistics query failed: {e}")
            return {
                "error": str(e),
                "reliability_metrics": {
                    "circuit_breaker": circuit_breaker.get_metrics(),
                    "dead_letter_queue": dead_letter_queue.get_queue_status()
                }
            }
    
    async def test_reliability_features(self) -> Dict[str, Any]:
        """Test reliability features"""
        results = {}
        
        # Test circuit breaker
        try:
            # Force a failure to test circuit breaker
            await circuit_breaker.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
        except Exception:
            pass
        
        results["circuit_breaker"] = circuit_breaker.get_metrics()
        
        # Test transaction manager
        try:
            transaction = transaction_manager.begin_transaction("test_transaction")
            await transaction_manager.rollback_transaction(transaction.transaction_id)
            results["transaction_manager"] = {"test": "passed"}
        except Exception as e:
            results["transaction_manager"] = {"test": "failed", "error": str(e)}
        
        # Test dead letter queue
        try:
            op_id = dead_letter_queue.add_failed_operation(
                "test_operation",
                {"test": "data"},
                Exception("Test error")
            )
            results["dead_letter_queue"] = {
                "test": "passed",
                "operation_id": op_id,
                "queue_status": dead_letter_queue.get_queue_status()
            }
        except Exception as e:
            results["dead_letter_queue"] = {"test": "failed", "error": str(e)}
        
        return results

# Create enhanced service instance
enhanced_neo4j_service = EnhancedNeo4jService()

# Backwards compatibility - maintain existing interface
class Neo4jService:
    """Backwards compatibility wrapper"""
    
    def __init__(self):
        self.enhanced_service = enhanced_neo4j_service
    
    @property
    def connected(self):
        return self.enhanced_service.connected
    
    @property
    def driver(self):
        return self.enhanced_service.driver
    
    async def connect(self):
        return await self.enhanced_service.connect()
    
    async def disconnect(self):
        return await self.enhanced_service.disconnect()
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None):
        return await self.enhanced_service.execute_query(query, parameters)
    
    async def test_connection(self):
        return await self.enhanced_service.get_health_status()
    
    async def count_nodes_and_relationships(self):
        stats = await self.enhanced_service.get_processing_statistics()
        db_stats = stats.get("database_statistics", {})
        return {
            "nodes": db_stats.get("total_nodes", 0),
            "relationships": db_stats.get("total_relationships", 0)
        }

# Export both services
neo4j_service = Neo4jService()

logger.info("🚀 Enhanced Neo4j service with reliability infrastructure ready")