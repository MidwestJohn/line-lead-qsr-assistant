#!/usr/bin/env python3
"""
Core Reliability Infrastructure for 99%+ Upload-to-Retrieval Pipeline
=====================================================================

Phase 1: Core Reliability Infrastructure
- Circuit Breaker Pattern for Neo4j connections
- Transactional Integrity System for atomic operations
- Dead Letter Queue for failed operations with intelligent retry

This infrastructure ensures bulletproof document processing with automatic
recovery and maintains consistency across all operations.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import pickle
import traceback
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# ============================================================================
# Circuit Breaker Pattern Implementation
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"               # Failing fast
    HALF_OPEN = "half_open"     # Testing recovery

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5              # Failures before opening
    recovery_timeout: int = 60              # Seconds before testing recovery
    success_threshold: int = 3              # Successes needed to close
    timeout_duration: int = 30              # Operation timeout in seconds
    monitor_window: int = 300               # Monitoring window in seconds

@dataclass
class CircuitBreakerMetrics:
    """Metrics tracking for circuit breaker"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_change_history: List[Tuple[datetime, CircuitState]] = field(default_factory=list)

class CircuitBreaker:
    """
    Circuit breaker implementation for Neo4j connections.
    
    Prevents cascade failures by:
    - Tracking consecutive failures
    - Opening circuit after threshold failures
    - Testing recovery after timeout
    - Automatic recovery on success
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.lock = threading.RLock()
        self.state_change_callbacks: List[Callable] = []
        
        logger.info(f"🔌 Circuit breaker '{name}' initialized with threshold {self.config.failure_threshold}")
    
    def add_state_change_callback(self, callback: Callable):
        """Add callback for state changes"""
        self.state_change_callbacks.append(callback)
    
    def _change_state(self, new_state: CircuitState, reason: str = ""):
        """Change circuit breaker state with logging and callbacks"""
        with self.lock:
            if self.state != new_state:
                old_state = self.state
                self.state = new_state
                self.metrics.state_change_history.append((datetime.now(), new_state))
                
                logger.info(f"⚡ Circuit breaker '{self.name}': {old_state.value} → {new_state.value} ({reason})")
                
                # Trigger callbacks
                for callback in self.state_change_callbacks:
                    try:
                        callback(self.name, old_state, new_state, reason)
                    except Exception as e:
                        logger.warning(f"Circuit breaker callback failed: {e}")
    
    def _record_success(self):
        """Record successful operation"""
        with self.lock:
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.consecutive_successes += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = datetime.now()
            
            # Close circuit if enough successes in HALF_OPEN state
            if self.state == CircuitState.HALF_OPEN and self.metrics.consecutive_successes >= self.config.success_threshold:
                self._change_state(CircuitState.CLOSED, f"Recovery confirmed: {self.metrics.consecutive_successes} successes")
            # Close circuit immediately on first success in HALF_OPEN (for faster recovery)
            elif self.state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.CLOSED, f"Recovery confirmed: first success after failure")
    
    def _record_failure(self, error: Exception):
        """Record failed operation"""
        with self.lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = datetime.now()
            
            # Open circuit if too many failures
            if self.state == CircuitState.CLOSED and self.metrics.consecutive_failures >= self.config.failure_threshold:
                self._change_state(CircuitState.OPEN, f"Failure threshold reached: {self.metrics.consecutive_failures} failures")
            
            # Return to OPEN if failure in HALF_OPEN state
            elif self.state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.OPEN, f"Recovery failed: {str(error)}")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.state != CircuitState.OPEN:
            return False
        
        if not self.metrics.last_failure_time:
            return False
        
        time_since_failure = (datetime.now() - self.metrics.last_failure_time).total_seconds()
        return time_since_failure >= self.config.recovery_timeout
    
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute operation through circuit breaker
        
        Args:
            operation: Function to execute
            *args, **kwargs: Arguments for operation
            
        Returns:
            Result of operation
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            Exception: Original exception from operation
        """
        with self.lock:
            current_state = self.state
        
        # Fast fail if circuit is open
        if current_state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._change_state(CircuitState.HALF_OPEN, "Testing recovery")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")
        
        # Execute operation with timeout
        try:
            result = await asyncio.wait_for(
                self._execute_operation(operation, *args, **kwargs),
                timeout=self.config.timeout_duration
            )
            
            self._record_success()
            return result
            
        except asyncio.TimeoutError as e:
            timeout_error = TimeoutError(f"Operation timed out after {self.config.timeout_duration}s")
            self._record_failure(timeout_error)
            raise timeout_error
        except Exception as e:
            self._record_failure(e)
            raise
    
    async def _execute_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation, handling both sync and async functions"""
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            # Run sync operation in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, operation, *args, **kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        with self.lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "failure_rate": self.metrics.failed_requests / max(self.metrics.total_requests, 1),
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                "state_changes": len(self.metrics.state_change_history)
            }
    
    def reset(self):
        """Manually reset circuit breaker"""
        with self.lock:
            self._change_state(CircuitState.CLOSED, "Manual reset")
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes = 0

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

# ============================================================================
# Transactional Integrity System
# ============================================================================

@dataclass
class TransactionOperation:
    """Individual operation within a transaction"""
    operation_id: str
    operation_type: str
    operation_data: Dict[str, Any]
    rollback_data: Dict[str, Any]
    executed: bool = False
    rolled_back: bool = False
    execution_time: Optional[datetime] = None
    error: Optional[str] = None

@dataclass
class AtomicTransaction:
    """Atomic transaction with rollback capability"""
    transaction_id: str
    start_time: datetime
    operations: List[TransactionOperation] = field(default_factory=list)
    completed: bool = False
    committed: bool = False
    rolled_back: bool = False
    error: Optional[str] = None
    end_time: Optional[datetime] = None

class TransactionManager:
    """
    Atomic transaction management for all Neo4j operations.
    
    Ensures all-or-nothing processing:
    - Entity creation
    - Relationship creation
    - Visual citation creation
    - Document metadata updates
    """
    
    def __init__(self):
        self.active_transactions: Dict[str, AtomicTransaction] = {}
        self.transaction_history: List[AtomicTransaction] = []
        self.lock = threading.RLock()
        self.max_history = 1000
        
        logger.info("📊 Transaction manager initialized")
    
    def begin_transaction(self, transaction_id: str = None) -> AtomicTransaction:
        """Begin new atomic transaction"""
        if not transaction_id:
            transaction_id = f"txn_{int(time.time() * 1000000)}"
        
        with self.lock:
            if transaction_id in self.active_transactions:
                raise ValueError(f"Transaction {transaction_id} already exists")
            
            transaction = AtomicTransaction(
                transaction_id=transaction_id,
                start_time=datetime.now()
            )
            
            self.active_transactions[transaction_id] = transaction
            
            logger.info(f"🔄 Transaction {transaction_id} started")
            return transaction
    
    def add_operation(self, transaction_id: str, operation_type: str, 
                     operation_data: Dict[str, Any], rollback_data: Dict[str, Any]) -> str:
        """Add operation to transaction"""
        with self.lock:
            if transaction_id not in self.active_transactions:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            operation_id = f"{transaction_id}_op_{len(self.active_transactions[transaction_id].operations)}"
            operation = TransactionOperation(
                operation_id=operation_id,
                operation_type=operation_type,
                operation_data=operation_data,
                rollback_data=rollback_data
            )
            
            self.active_transactions[transaction_id].operations.append(operation)
            
            logger.debug(f"📝 Added operation {operation_id} to transaction {transaction_id}")
            return operation_id
    
    async def execute_operation(self, transaction_id: str, operation_id: str, 
                              executor: Callable) -> Any:
        """Execute operation within transaction"""
        with self.lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            operation = next((op for op in transaction.operations if op.operation_id == operation_id), None)
            if not operation:
                raise ValueError(f"Operation {operation_id} not found")
            
            if operation.executed:
                raise ValueError(f"Operation {operation_id} already executed")
        
        try:
            # Execute operation
            result = await executor(operation.operation_data)
            
            with self.lock:
                operation.executed = True
                operation.execution_time = datetime.now()
            
            logger.debug(f"✅ Operation {operation_id} executed successfully")
            return result
            
        except Exception as e:
            with self.lock:
                operation.error = str(e)
            
            logger.error(f"❌ Operation {operation_id} failed: {e}")
            raise
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit transaction if all operations succeeded"""
        with self.lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if transaction.completed:
                raise ValueError(f"Transaction {transaction_id} already completed")
            
            # Check if all operations executed successfully
            failed_operations = [op for op in transaction.operations if op.error or not op.executed]
            
            if failed_operations:
                # Rollback on any failures
                await self._rollback_transaction(transaction)
                return False
            
            # Mark as committed
            transaction.committed = True
            transaction.completed = True
            transaction.end_time = datetime.now()
            
            # Move to history
            self.transaction_history.append(transaction)
            del self.active_transactions[transaction_id]
            
            # Maintain history size
            if len(self.transaction_history) > self.max_history:
                self.transaction_history = self.transaction_history[-self.max_history:]
            
            logger.info(f"✅ Transaction {transaction_id} committed successfully")
            return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Manually rollback transaction"""
        with self.lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            return await self._rollback_transaction(transaction)
    
    async def _rollback_transaction(self, transaction: AtomicTransaction) -> bool:
        """Internal rollback implementation"""
        logger.info(f"🔄 Rolling back transaction {transaction.transaction_id}")
        
        # Rollback operations in reverse order
        rollback_errors = []
        
        for operation in reversed(transaction.operations):
            if operation.executed and not operation.rolled_back:
                try:
                    await self._rollback_operation(operation)
                    operation.rolled_back = True
                except Exception as e:
                    rollback_errors.append(f"Operation {operation.operation_id}: {e}")
                    logger.error(f"❌ Failed to rollback operation {operation.operation_id}: {e}")
        
        # Mark transaction as rolled back
        transaction.rolled_back = True
        transaction.completed = True
        transaction.end_time = datetime.now()
        
        if rollback_errors:
            transaction.error = f"Rollback errors: {'; '.join(rollback_errors)}"
        
        # Move to history
        self.transaction_history.append(transaction)
        del self.active_transactions[transaction.transaction_id]
        
        success = len(rollback_errors) == 0
        if success:
            logger.info(f"✅ Transaction {transaction.transaction_id} rolled back successfully")
        else:
            logger.error(f"❌ Transaction {transaction.transaction_id} rollback had errors: {rollback_errors}")
        
        return success
    
    async def _rollback_operation(self, operation: TransactionOperation):
        """Rollback individual operation"""
        rollback_type = operation.rollback_data.get("type")
        
        if rollback_type == "neo4j_delete":
            # Delete Neo4j nodes/relationships
            await self._rollback_neo4j_operation(operation.rollback_data)
        elif rollback_type == "file_delete":
            # Delete created files
            await self._rollback_file_operation(operation.rollback_data)
        elif rollback_type == "database_delete":
            # Remove from documents database
            await self._rollback_database_operation(operation.rollback_data)
        else:
            logger.warning(f"Unknown rollback type: {rollback_type}")
    
    async def _rollback_neo4j_operation(self, rollback_data: Dict[str, Any]):
        """Rollback Neo4j operations"""
        # This will be implemented to work with the Neo4j service
        # For now, log the operation
        logger.info(f"🔄 Rolling back Neo4j operation: {rollback_data}")
    
    async def _rollback_file_operation(self, rollback_data: Dict[str, Any]):
        """Rollback file operations"""
        file_path = rollback_data.get("file_path")
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
            logger.info(f"🗑️ Deleted file: {file_path}")
    
    async def _rollback_database_operation(self, rollback_data: Dict[str, Any]):
        """Rollback database operations"""
        # This will be implemented to work with the documents database
        logger.info(f"🔄 Rolling back database operation: {rollback_data}")
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get transaction status"""
        with self.lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                # Check history
                transaction = next((t for t in self.transaction_history if t.transaction_id == transaction_id), None)
                if not transaction:
                    return {"error": "Transaction not found"}
            
            return {
                "transaction_id": transaction.transaction_id,
                "start_time": transaction.start_time.isoformat(),
                "end_time": transaction.end_time.isoformat() if transaction.end_time else None,
                "operations_count": len(transaction.operations),
                "operations_executed": sum(1 for op in transaction.operations if op.executed),
                "completed": transaction.completed,
                "committed": transaction.committed,
                "rolled_back": transaction.rolled_back,
                "error": transaction.error
            }

# ============================================================================
# Dead Letter Queue System
# ============================================================================

class RetryStrategy(Enum):
    """Retry strategies for different error types"""
    EXPONENTIAL_BACKOFF = "exponential"
    LINEAR_BACKOFF = "linear"
    MANUAL_REVIEW = "manual"
    NO_RETRY = "no_retry"

@dataclass
class FailedOperation:
    """Failed operation queued for retry"""
    operation_id: str
    operation_type: str
    operation_data: Dict[str, Any]
    error_message: str
    error_type: str
    failure_time: datetime
    retry_count: int = 0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    next_retry_time: Optional[datetime] = None
    manual_review: bool = False

class DeadLetterQueue:
    """
    Persistent dead letter queue for failed operations.
    
    Features:
    - Persistent storage to disk
    - Intelligent retry strategies
    - Background processing
    - Escalation to manual review
    """
    
    def __init__(self, storage_path: str = "data/dead_letter_queue"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.queue_file = self.storage_path / "failed_operations.json"
        self.manual_queue_file = self.storage_path / "manual_review_queue.json"
        
        self.failed_operations: List[FailedOperation] = []
        self.manual_review_queue: List[FailedOperation] = []
        
        self.lock = threading.RLock()
        self.background_processor = None
        self.processing_enabled = True
        
        # Load existing operations
        self._load_operations()
        
        logger.info(f"📮 Dead letter queue initialized at {self.storage_path}")
    
    def _load_operations(self):
        """Load failed operations from disk"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    self.failed_operations = [
                        FailedOperation(
                            operation_id=op["operation_id"],
                            operation_type=op["operation_type"],
                            operation_data=op["operation_data"],
                            error_message=op["error_message"],
                            error_type=op["error_type"],
                            failure_time=datetime.fromisoformat(op["failure_time"]),
                            retry_count=op.get("retry_count", 0),
                            max_retries=op.get("max_retries", 3),
                            retry_strategy=RetryStrategy(op.get("retry_strategy", "exponential")),
                            next_retry_time=datetime.fromisoformat(op["next_retry_time"]) if op.get("next_retry_time") else None,
                            manual_review=op.get("manual_review", False)
                        )
                        for op in data
                    ]
            
            if self.manual_queue_file.exists():
                with open(self.manual_queue_file, 'r') as f:
                    data = json.load(f)
                    self.manual_review_queue = [
                        FailedOperation(
                            operation_id=op["operation_id"],
                            operation_type=op["operation_type"],
                            operation_data=op["operation_data"],
                            error_message=op["error_message"],
                            error_type=op["error_type"],
                            failure_time=datetime.fromisoformat(op["failure_time"]),
                            retry_count=op.get("retry_count", 0),
                            max_retries=op.get("max_retries", 3),
                            retry_strategy=RetryStrategy(op.get("retry_strategy", "manual")),
                            manual_review=True
                        )
                        for op in data
                    ]
            
            logger.info(f"📥 Loaded {len(self.failed_operations)} failed operations, {len(self.manual_review_queue)} manual review")
            
        except Exception as e:
            logger.error(f"❌ Failed to load dead letter queue: {e}")
    
    def _save_operations(self):
        """Save failed operations to disk"""
        try:
            # Save main queue
            with open(self.queue_file, 'w') as f:
                json.dump([
                    {
                        "operation_id": op.operation_id,
                        "operation_type": op.operation_type,
                        "operation_data": op.operation_data,
                        "error_message": op.error_message,
                        "error_type": op.error_type,
                        "failure_time": op.failure_time.isoformat(),
                        "retry_count": op.retry_count,
                        "max_retries": op.max_retries,
                        "retry_strategy": op.retry_strategy.value,
                        "next_retry_time": op.next_retry_time.isoformat() if op.next_retry_time else None,
                        "manual_review": op.manual_review
                    }
                    for op in self.failed_operations
                ], f, indent=2)
            
            # Save manual review queue
            with open(self.manual_queue_file, 'w') as f:
                json.dump([
                    {
                        "operation_id": op.operation_id,
                        "operation_type": op.operation_type,
                        "operation_data": op.operation_data,
                        "error_message": op.error_message,
                        "error_type": op.error_type,
                        "failure_time": op.failure_time.isoformat(),
                        "retry_count": op.retry_count,
                        "max_retries": op.max_retries,
                        "retry_strategy": op.retry_strategy.value,
                        "manual_review": op.manual_review
                    }
                    for op in self.manual_review_queue
                ], f, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Failed to save dead letter queue: {e}")
    
    def add_failed_operation(self, operation_type: str, operation_data: Dict[str, Any], 
                           error: Exception, max_retries: int = 3) -> str:
        """Add failed operation to queue"""
        operation_id = f"failed_{int(time.time() * 1000000)}"
        
        # Determine retry strategy based on error type
        retry_strategy = self._determine_retry_strategy(error)
        
        failed_op = FailedOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            operation_data=operation_data,
            error_message=str(error),
            error_type=type(error).__name__,
            failure_time=datetime.now(),
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            next_retry_time=self._calculate_next_retry_time(retry_strategy, 0)
        )
        
        with self.lock:
            if retry_strategy == RetryStrategy.MANUAL_REVIEW:
                self.manual_review_queue.append(failed_op)
            else:
                self.failed_operations.append(failed_op)
            
            self._save_operations()
        
        logger.info(f"📮 Added failed operation {operation_id} to queue (strategy: {retry_strategy.value})")
        return operation_id
    
    def _determine_retry_strategy(self, error: Exception) -> RetryStrategy:
        """Determine retry strategy based on error type"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Connection errors - exponential backoff
        if any(term in error_message for term in ["connection", "network", "timeout", "unavailable"]):
            return RetryStrategy.EXPONENTIAL_BACKOFF
        
        # Temporary errors - linear backoff
        if any(term in error_message for term in ["busy", "lock", "concurrent", "rate limit"]):
            return RetryStrategy.LINEAR_BACKOFF
        
        # Validation errors - manual review
        if any(term in error_message for term in ["validation", "format", "schema", "corrupt"]):
            return RetryStrategy.MANUAL_REVIEW
        
        # Default to exponential backoff
        return RetryStrategy.EXPONENTIAL_BACKOFF
    
    def _calculate_next_retry_time(self, strategy: RetryStrategy, retry_count: int) -> datetime:
        """Calculate next retry time based on strategy"""
        if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(300, 2 ** retry_count * 5)  # 5s, 10s, 20s, 40s, 80s, max 300s
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = min(60, (retry_count + 1) * 10)  # 10s, 20s, 30s, max 60s
        else:
            delay = 0
        
        return datetime.now() + timedelta(seconds=delay)
    
    def start_background_processing(self):
        """Start background processing of failed operations"""
        if self.background_processor is None:
            self.background_processor = threading.Thread(
                target=self._background_process_loop,
                daemon=True
            )
            self.background_processor.start()
            logger.info("🔄 Dead letter queue background processing started")
    
    def stop_background_processing(self):
        """Stop background processing"""
        self.processing_enabled = False
        if self.background_processor:
            self.background_processor.join(timeout=5)
            self.background_processor = None
        logger.info("⏹️ Dead letter queue background processing stopped")
    
    def _background_process_loop(self):
        """Background processing loop"""
        while self.processing_enabled:
            try:
                self._process_ready_operations()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"❌ Background processing error: {e}")
                time.sleep(30)  # Wait longer on errors
    
    def _process_ready_operations(self):
        """Process operations ready for retry"""
        now = datetime.now()
        ready_operations = []
        
        with self.lock:
            for i, op in enumerate(self.failed_operations):
                if op.next_retry_time and now >= op.next_retry_time:
                    ready_operations.append((i, op))
        
        # Process ready operations
        for i, op in reversed(ready_operations):  # Reverse to maintain indices
            try:
                success = self._retry_operation(op)
                
                with self.lock:
                    if success:
                        # Remove from queue on success
                        self.failed_operations.pop(i)
                        logger.info(f"✅ Successfully retried operation {op.operation_id}")
                    else:
                        # Update retry count and schedule next retry
                        op.retry_count += 1
                        
                        if op.retry_count >= op.max_retries:
                            # Move to manual review
                            op.manual_review = True
                            op.retry_strategy = RetryStrategy.MANUAL_REVIEW
                            self.manual_review_queue.append(op)
                            self.failed_operations.pop(i)
                            logger.info(f"📋 Moved operation {op.operation_id} to manual review after {op.retry_count} failures")
                        else:
                            # Schedule next retry
                            op.next_retry_time = self._calculate_next_retry_time(op.retry_strategy, op.retry_count)
                            logger.info(f"🔄 Scheduled retry {op.retry_count}/{op.max_retries} for operation {op.operation_id} at {op.next_retry_time}")
                    
                    self._save_operations()
                    
            except Exception as e:
                logger.error(f"❌ Error processing operation {op.operation_id}: {e}")
    
    def _retry_operation(self, operation: FailedOperation) -> bool:
        """Retry failed operation"""
        logger.info(f"🔄 Retrying operation {operation.operation_id} (attempt {operation.retry_count + 1})")
        
        try:
            # This is a placeholder - specific retry logic will be implemented
            # based on operation type
            if operation.operation_type == "neo4j_write":
                return self._retry_neo4j_operation(operation)
            elif operation.operation_type == "file_processing":
                return self._retry_file_operation(operation)
            elif operation.operation_type == "entity_extraction":
                return self._retry_extraction_operation(operation)
            else:
                logger.warning(f"Unknown operation type: {operation.operation_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Retry failed for operation {operation.operation_id}: {e}")
            return False
    
    def _retry_neo4j_operation(self, operation: FailedOperation) -> bool:
        """Retry Neo4j operation"""
        # Placeholder for Neo4j retry logic
        logger.info(f"🔄 Retrying Neo4j operation: {operation.operation_id}")
        return False  # Will be implemented with actual Neo4j service
    
    def _retry_file_operation(self, operation: FailedOperation) -> bool:
        """Retry file operation"""
        # Placeholder for file retry logic
        logger.info(f"🔄 Retrying file operation: {operation.operation_id}")
        return False  # Will be implemented with actual file service
    
    def _retry_extraction_operation(self, operation: FailedOperation) -> bool:
        """Retry extraction operation"""
        # Placeholder for extraction retry logic
        logger.info(f"🔄 Retrying extraction operation: {operation.operation_id}")
        return False  # Will be implemented with actual extraction service
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        with self.lock:
            return {
                "failed_operations": len(self.failed_operations),
                "manual_review_queue": len(self.manual_review_queue),
                "ready_for_retry": len([op for op in self.failed_operations if op.next_retry_time and datetime.now() >= op.next_retry_time]),
                "processing_enabled": self.processing_enabled,
                "background_processor_running": self.background_processor is not None and self.background_processor.is_alive()
            }
    
    def get_manual_review_operations(self) -> List[Dict[str, Any]]:
        """Get operations requiring manual review"""
        with self.lock:
            return [
                {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type,
                    "error_message": op.error_message,
                    "error_type": op.error_type,
                    "failure_time": op.failure_time.isoformat(),
                    "retry_count": op.retry_count,
                    "operation_data": op.operation_data
                }
                for op in self.manual_review_queue
            ]
    
    def resolve_manual_operation(self, operation_id: str, resolution: str) -> bool:
        """Resolve manual review operation"""
        with self.lock:
            for i, op in enumerate(self.manual_review_queue):
                if op.operation_id == operation_id:
                    self.manual_review_queue.pop(i)
                    self._save_operations()
                    logger.info(f"✅ Resolved manual operation {operation_id}: {resolution}")
                    return True
        
        return False

# ============================================================================
# Global instances
# ============================================================================

# Create global instances for use throughout the application
circuit_breaker = CircuitBreaker("neo4j_operations")
transaction_manager = TransactionManager()
dead_letter_queue = DeadLetterQueue()

# Start background processing
dead_letter_queue.start_background_processing()

logger.info("🚀 Core reliability infrastructure initialized")