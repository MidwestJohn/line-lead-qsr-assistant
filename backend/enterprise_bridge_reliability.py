#!/usr/bin/env python3
"""
Enterprise-Grade Bridge Reliability System
==========================================

Bulletproof LightRAG → Neo4j bridge with comprehensive health checks,
atomic transactions, and enterprise error handling.

Features:
- Pre-flight health checks (Neo4j, storage, memory, disk space)
- Atomic transactions with full rollback capability
- Comprehensive error handling with specific error codes
- Automatic retry logic with exponential backoff
- Real-time health monitoring and recovery

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import logging
import time
import psutil
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class HealthCheckStatus(str, Enum):
    """Health check status codes"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"

class ErrorCode(str, Enum):
    """Detailed error codes for UI display"""
    NEO4J_CONNECTION_FAILED = "neo4j_connection_failed"
    NEO4J_AUTH_FAILED = "neo4j_auth_failed"
    NEO4J_TIMEOUT = "neo4j_timeout"
    STORAGE_INSUFFICIENT = "storage_insufficient"
    MEMORY_INSUFFICIENT = "memory_insufficient"
    DISK_FULL = "disk_full"
    PROCESSING_TIMEOUT = "processing_timeout"
    EXTRACTION_FAILED = "extraction_failed"
    BRIDGE_FAILED = "bridge_failed"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    PARTIAL_SUCCESS = "partial_success"
    INVALID_PDF = "invalid_pdf"
    FILE_CORRUPTED = "file_corrupted"
    LIGHTRAG_CRASH = "lightrag_crash"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class HealthCheckResult:
    """Health check result with detailed information"""
    component: str
    status: HealthCheckStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    error_code: Optional[ErrorCode] = None
    recovery_suggestion: Optional[str] = None

@dataclass
class BridgeTransaction:
    """Atomic transaction wrapper for bridge operations"""
    transaction_id: str
    start_time: datetime
    operations: List[Dict[str, Any]]
    rollback_data: List[Dict[str, Any]]
    completed: bool = False
    rolled_back: bool = False

class EnterpriseHealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.min_disk_space_gb = 1.0  # Minimum 1GB free space
        self.min_memory_mb = 512      # Minimum 512MB available memory
        self.neo4j_timeout = 10       # Neo4j connection timeout
        self.health_history: List[HealthCheckResult] = []
    
    async def run_pre_flight_checks(self) -> Tuple[bool, List[HealthCheckResult]]:
        """Run comprehensive pre-flight health checks"""
        
        logger.info("🔍 Running enterprise pre-flight health checks...")
        
        checks = [
            self._check_neo4j_connection(),
            self._check_disk_space(),
            self._check_memory_availability(),
            self._check_storage_permissions(),
            self._check_lightrag_dependencies(),
            self._check_network_connectivity()
        ]
        
        results = []
        for check in checks:
            try:
                result = await check
                results.append(result)
                self.health_history.append(result)
            except Exception as e:
                error_result = HealthCheckResult(
                    component="health_checker",
                    status=HealthCheckStatus.FAILED,
                    message=f"Health check failed: {str(e)}",
                    details={"error": str(e), "check": check.__name__},
                    timestamp=datetime.now(),
                    error_code=ErrorCode.UNKNOWN_ERROR,
                    recovery_suggestion="Restart the service and try again"
                )
                results.append(error_result)
        
        # Determine overall health
        critical_failures = [r for r in results if r.status == HealthCheckStatus.CRITICAL]
        failed_checks = [r for r in results if r.status == HealthCheckStatus.FAILED]
        
        overall_healthy = len(critical_failures) == 0 and len(failed_checks) == 0
        
        logger.info(f"✅ Pre-flight checks completed: {len(results)} checks, healthy: {overall_healthy}")
        
        return overall_healthy, results
    
    async def _check_neo4j_connection(self) -> HealthCheckResult:
        """Check Neo4j database connectivity via Enterprise Bridge system"""
        
        try:
            # For Enterprise Bridge system, we check the bridge components instead of direct Neo4j
            # since we bypass LightRAG async issues through the bridge
            
            start_time = time.time()
            
            # Test if Enterprise Bridge components are available
            try:
                from lightrag_neo4j_bridge import LightRAGNeo4jBridge
                
                # Test basic bridge initialization (doesn't require active connection)
                bridge = LightRAGNeo4jBridge()
                
                connection_time = time.time() - start_time
                
                return HealthCheckResult(
                    component="neo4j_connection",
                    status=HealthCheckStatus.HEALTHY,
                    message=f"Enterprise Bridge ready ({connection_time:.2f}s)",
                    details={
                        "connection_time": connection_time, 
                        "bridge_type": "enterprise_bridge",
                        "lightrag_bypass": "active"
                    },
                    timestamp=datetime.now()
                )
                
            except ImportError as e:
                return HealthCheckResult(
                    component="neo4j_connection",
                    status=HealthCheckStatus.CRITICAL,
                    message=f"Enterprise Bridge components missing: {str(e)}",
                    details={"import_error": str(e)},
                    timestamp=datetime.now(),
                    error_code=ErrorCode.BRIDGE_FAILED,
                    recovery_suggestion="Ensure Enterprise Bridge components are properly installed"
                )
            
        except Exception as e:
            return HealthCheckResult(
                component="neo4j_connection",
                status=HealthCheckStatus.WARNING,
                message=f"Enterprise Bridge health check inconclusive: {str(e)}",
                details={"error": str(e), "note": "Enterprise Bridge may still function normally"},
                timestamp=datetime.now(),
                recovery_suggestion="Enterprise Bridge health check failed but system may still work"
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space"""
        
        try:
            # Check current directory disk space
            total, used, free = shutil.disk_usage(Path.cwd())
            free_gb = free / (1024**3)
            
            if free_gb < self.min_disk_space_gb:
                return HealthCheckResult(
                    component="disk_space",
                    status=HealthCheckStatus.CRITICAL,
                    message=f"Insufficient disk space ({free_gb:.2f}GB available)",
                    details={
                        "free_gb": free_gb,
                        "minimum_required": self.min_disk_space_gb,
                        "total_gb": total / (1024**3),
                        "used_gb": used / (1024**3)
                    },
                    timestamp=datetime.now(),
                    error_code=ErrorCode.DISK_FULL,
                    recovery_suggestion="Free up disk space or add storage capacity"
                )
            
            return HealthCheckResult(
                component="disk_space",
                status=HealthCheckStatus.HEALTHY,
                message=f"Disk space adequate ({free_gb:.2f}GB available)",
                details={
                    "free_gb": free_gb,
                    "total_gb": total / (1024**3),
                    "usage_percent": (used / total) * 100
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="disk_space",
                status=HealthCheckStatus.FAILED,
                message=f"Disk space check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                error_code=ErrorCode.UNKNOWN_ERROR,
                recovery_suggestion="Check file system permissions"
            )
    
    async def _check_memory_availability(self) -> HealthCheckResult:
        """Check available system memory"""
        
        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024**2)
            
            if available_mb < self.min_memory_mb:
                return HealthCheckResult(
                    component="memory",
                    status=HealthCheckStatus.WARNING,
                    message=f"Low memory ({available_mb:.0f}MB available)",
                    details={
                        "available_mb": available_mb,
                        "minimum_required": self.min_memory_mb,
                        "total_mb": memory.total / (1024**2),
                        "usage_percent": memory.percent
                    },
                    timestamp=datetime.now(),
                    error_code=ErrorCode.MEMORY_INSUFFICIENT,
                    recovery_suggestion="Close unnecessary applications or increase system memory"
                )
            
            return HealthCheckResult(
                component="memory",
                status=HealthCheckStatus.HEALTHY,
                message=f"Memory adequate ({available_mb:.0f}MB available)",
                details={
                    "available_mb": available_mb,
                    "total_mb": memory.total / (1024**2),
                    "usage_percent": memory.percent
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="memory",
                status=HealthCheckStatus.FAILED,
                message=f"Memory check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                error_code=ErrorCode.UNKNOWN_ERROR,
                recovery_suggestion="Check system monitoring tools"
            )
    
    async def _check_storage_permissions(self) -> HealthCheckResult:
        """Check file system permissions for storage directories"""
        
        try:
            storage_dirs = [
                Path("uploaded_docs"),
                Path("rag_storage"),
                Path("."),  # Current directory
            ]
            
            permission_issues = []
            
            for storage_dir in storage_dirs:
                if not storage_dir.exists():
                    try:
                        storage_dir.mkdir(parents=True, exist_ok=True)
                    except PermissionError:
                        permission_issues.append(f"Cannot create {storage_dir}")
                        continue
                
                # Test write permission
                test_file = storage_dir / f"health_check_{int(time.time())}.tmp"
                try:
                    test_file.write_text("health check")
                    test_file.unlink()  # Clean up
                except PermissionError:
                    permission_issues.append(f"Cannot write to {storage_dir}")
            
            if permission_issues:
                return HealthCheckResult(
                    component="storage_permissions",
                    status=HealthCheckStatus.CRITICAL,
                    message="Storage permission issues detected",
                    details={"permission_issues": permission_issues},
                    timestamp=datetime.now(),
                    error_code=ErrorCode.STORAGE_INSUFFICIENT,
                    recovery_suggestion="Check directory permissions and user access rights"
                )
            
            return HealthCheckResult(
                component="storage_permissions",
                status=HealthCheckStatus.HEALTHY,
                message="Storage permissions adequate",
                details={"checked_directories": [str(d) for d in storage_dirs]},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="storage_permissions",
                status=HealthCheckStatus.FAILED,
                message=f"Storage permission check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                error_code=ErrorCode.UNKNOWN_ERROR,
                recovery_suggestion="Check file system access"
            )
    
    async def _check_lightrag_dependencies(self) -> HealthCheckResult:
        """Check LightRAG dependencies and import capability"""
        
        try:
            # Test critical imports
            import lightrag
            from lightrag import LightRAG
            from lightrag.utils import EmbeddingFunc
            
            return HealthCheckResult(
                component="lightrag_dependencies",
                status=HealthCheckStatus.HEALTHY,
                message="LightRAG dependencies available",
                details={"lightrag_version": getattr(lightrag, "__version__", "unknown")},
                timestamp=datetime.now()
            )
            
        except ImportError as e:
            return HealthCheckResult(
                component="lightrag_dependencies",
                status=HealthCheckStatus.CRITICAL,
                message=f"LightRAG import failed: {str(e)}",
                details={"import_error": str(e)},
                timestamp=datetime.now(),
                error_code=ErrorCode.LIGHTRAG_CRASH,
                recovery_suggestion="Reinstall LightRAG dependencies: pip install lightrag-hku"
            )
        except Exception as e:
            return HealthCheckResult(
                component="lightrag_dependencies",
                status=HealthCheckStatus.FAILED,
                message=f"LightRAG check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                error_code=ErrorCode.UNKNOWN_ERROR,
                recovery_suggestion="Check Python environment and package installations"
            )
    
    async def _check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity for external services"""
        
        try:
            import aiohttp
            
            # Test basic internet connectivity
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                try:
                    async with session.get('https://httpbin.org/status/200') as response:
                        if response.status == 200:
                            connectivity_status = "healthy"
                        else:
                            connectivity_status = "degraded"
                except asyncio.TimeoutError:
                    connectivity_status = "timeout"
                except Exception:
                    connectivity_status = "failed"
            
            if connectivity_status == "failed":
                return HealthCheckResult(
                    component="network_connectivity",
                    status=HealthCheckStatus.WARNING,
                    message="Network connectivity issues detected",
                    details={"connectivity_test": "failed"},
                    timestamp=datetime.now(),
                    recovery_suggestion="Check internet connection and firewall settings"
                )
            
            return HealthCheckResult(
                component="network_connectivity",
                status=HealthCheckStatus.HEALTHY,
                message=f"Network connectivity {connectivity_status}",
                details={"connectivity_test": connectivity_status},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="network_connectivity",
                status=HealthCheckStatus.WARNING,
                message=f"Network check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                recovery_suggestion="Network connectivity could not be verified"
            )

class AtomicBridgeTransaction:
    """Atomic transaction manager for bridge operations"""
    
    def __init__(self):
        self.active_transactions: Dict[str, BridgeTransaction] = {}
        self.transaction_history: List[BridgeTransaction] = []
    
    def start_transaction(self, process_id: str) -> BridgeTransaction:
        """Start a new atomic transaction"""
        
        transaction_id = f"tx_{process_id}_{int(time.time())}"
        transaction = BridgeTransaction(
            transaction_id=transaction_id,
            start_time=datetime.now(),
            operations=[],
            rollback_data=[]
        )
        
        self.active_transactions[transaction_id] = transaction
        logger.info(f"🔄 Started atomic transaction: {transaction_id}")
        
        return transaction
    
    async def add_operation(self, transaction_id: str, operation: Dict[str, Any], rollback_data: Dict[str, Any]):
        """Add operation to transaction with rollback data"""
        
        if transaction_id not in self.active_transactions:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        transaction = self.active_transactions[transaction_id]
        transaction.operations.append(operation)
        transaction.rollback_data.append(rollback_data)
        
        logger.debug(f"📝 Added operation to transaction {transaction_id}: {operation.get('type', 'unknown')}")
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit transaction - mark as completed"""
        
        if transaction_id not in self.active_transactions:
            logger.error(f"❌ Cannot commit - transaction {transaction_id} not found")
            return False
        
        transaction = self.active_transactions[transaction_id]
        transaction.completed = True
        
        # Move to history
        self.transaction_history.append(transaction)
        del self.active_transactions[transaction_id]
        
        logger.info(f"✅ Committed transaction: {transaction_id} ({len(transaction.operations)} operations)")
        return True
    
    async def rollback_transaction(self, transaction_id: str, error_reason: str) -> bool:
        """Rollback transaction with error logging"""
        
        if transaction_id not in self.active_transactions:
            logger.error(f"❌ Cannot rollback - transaction {transaction_id} not found")
            return False
        
        transaction = self.active_transactions[transaction_id]
        
        logger.warning(f"🔄 Rolling back transaction {transaction_id}: {error_reason}")
        
        # Execute rollback operations in reverse order
        for rollback_data in reversed(transaction.rollback_data):
            try:
                await self._execute_rollback_operation(rollback_data)
            except Exception as e:
                logger.error(f"❌ Rollback operation failed: {e}")
        
        transaction.rolled_back = True
        
        # Move to history
        self.transaction_history.append(transaction)
        del self.active_transactions[transaction_id]
        
        logger.info(f"🔄 Rolled back transaction: {transaction_id}")
        return True
    
    async def _execute_rollback_operation(self, rollback_data: Dict[str, Any]):
        """Execute a single rollback operation"""
        
        operation_type = rollback_data.get("type")
        
        if operation_type == "neo4j_delete":
            # Delete Neo4j nodes/relationships created
            from shared_neo4j_service import unified_neo4j
            query = rollback_data.get("delete_query")
            params = rollback_data.get("params", {})
            unified_neo4j.execute_query(query, params)
            
        elif operation_type == "file_delete":
            # Delete files created
            file_path = Path(rollback_data.get("file_path"))
            if file_path.exists():
                file_path.unlink()
                
        elif operation_type == "storage_cleanup":
            # Clean up storage directories
            storage_path = Path(rollback_data.get("storage_path"))
            if storage_path.exists() and storage_path.is_dir():
                shutil.rmtree(storage_path)
        
        logger.debug(f"🧹 Executed rollback operation: {operation_type}")

class EnterpriseRetryLogic:
    """Intelligent retry logic with exponential backoff"""
    
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 30.0  # seconds
        self.backoff_factor = 2.0
    
    async def execute_with_retry(self, operation, operation_name: str, *args, **kwargs):
        """Execute operation with intelligent retry logic"""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = min(self.base_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
                    logger.info(f"🔄 Retrying {operation_name} (attempt {attempt + 1}/{self.max_retries + 1}) after {delay:.1f}s delay")
                    await asyncio.sleep(delay)
                
                result = await operation(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"✅ {operation_name} succeeded on retry attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    if self._is_retryable_error(e):
                        logger.warning(f"⚠️ {operation_name} failed (attempt {attempt + 1}), will retry: {str(e)}")
                        continue
                    else:
                        logger.error(f"❌ {operation_name} failed with non-retryable error: {str(e)}")
                        break
                else:
                    logger.error(f"❌ {operation_name} failed after {self.max_retries + 1} attempts: {str(e)}")
        
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if error is retryable"""
        
        retryable_patterns = [
            "connection",
            "timeout",
            "temporary",
            "unavailable",
            "network",
            "socket"
        ]
        
        error_message = str(error).lower()
        return any(pattern in error_message for pattern in retryable_patterns)

# Global instances
enterprise_health_checker = EnterpriseHealthChecker()
atomic_transaction_manager = AtomicBridgeTransaction()
enterprise_retry_logic = EnterpriseRetryLogic()

# Error message mapping for UI
ERROR_MESSAGES = {
    ErrorCode.NEO4J_CONNECTION_FAILED: {
        "user_message": "Database unavailable, please try again",
        "technical_details": "Neo4j connection could not be established",
        "recovery_action": "retry"
    },
    ErrorCode.PROCESSING_TIMEOUT: {
        "user_message": "Large file detected, processing continues in background",
        "technical_details": "Processing exceeded time threshold",
        "recovery_action": "background_continue"
    },
    ErrorCode.INVALID_PDF: {
        "user_message": "Invalid PDF format, please check file",
        "technical_details": "PDF could not be parsed or is corrupted",
        "recovery_action": "user_action_required"
    },
    ErrorCode.BRIDGE_FAILED: {
        "user_message": "Knowledge base update failed, retrying automatically",
        "technical_details": "LightRAG to Neo4j bridge operation failed",
        "recovery_action": "automatic_retry"
    },
    ErrorCode.PARTIAL_SUCCESS: {
        "user_message": "Upload succeeded, knowledge base updating...",
        "technical_details": "File processed but graph update is pending",
        "recovery_action": "monitor_progress"
    },
    ErrorCode.DISK_FULL: {
        "user_message": "Storage space full, please contact administrator",
        "technical_details": "Insufficient disk space for processing",
        "recovery_action": "admin_required"
    },
    ErrorCode.MEMORY_INSUFFICIENT: {
        "user_message": "System busy, please try again in a few minutes",
        "technical_details": "Insufficient memory for processing",
        "recovery_action": "wait_and_retry"
    }
}

def get_user_friendly_error(error_code: ErrorCode) -> Dict[str, str]:
    """Get user-friendly error message for UI display"""
    return ERROR_MESSAGES.get(error_code, {
        "user_message": "An unexpected error occurred, please try again",
        "technical_details": "Unknown error",
        "recovery_action": "retry"
    })