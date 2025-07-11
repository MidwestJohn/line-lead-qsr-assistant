#!/usr/bin/env python3
"""
Phase 3B: Automated Recovery System
===================================

Automated recovery system that detects and fixes common pipeline failures without manual intervention.
Implements recovery strategies for various failure types with escalation to manual intervention.

Features:
- Recovery strategies for stuck text extraction, entity processing, Neo4j population, memory exhaustion, connection failures
- Automatic retry triggering for files stuck in various processing stages
- Escalation system: automated recovery first, then manual intervention
- Recovery result tracking and reporting
- Integration with health monitoring to trigger recovery actions
- Non-interference with normal processing operations

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import psutil
import signal
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

# Import existing infrastructure
from reliability_infrastructure import circuit_breaker, transaction_manager, dead_letter_queue
from enhanced_neo4j_service import enhanced_neo4j_service
from reliable_upload_pipeline import reliable_upload_pipeline
from health_monitoring_system import health_monitoring_system, HealthStatus, AlertSeverity

logger = logging.getLogger(__name__)

class RecoveryStrategy(Enum):
    """Types of recovery strategies"""
    RESTART_PROCESS = "restart_process"
    RETRY_OPERATION = "retry_operation"
    CLEAR_MEMORY = "clear_memory"
    RESET_CONNECTION = "reset_connection"
    FORCE_COMPLETION = "force_completion"
    ESCALATE_TO_MANUAL = "escalate_to_manual"
    CIRCUIT_BREAKER_RESET = "circuit_breaker_reset"
    TRANSACTION_ROLLBACK = "transaction_rollback"

class RecoveryResult(Enum):
    """Recovery operation results"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    ESCALATED = "escalated"
    SKIPPED = "skipped"

class FailureType(Enum):
    """Types of failures that can be recovered"""
    STUCK_TEXT_EXTRACTION = "stuck_text_extraction"
    STUCK_ENTITY_PROCESSING = "stuck_entity_processing"
    STUCK_NEO4J_POPULATION = "stuck_neo4j_population"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    CONNECTION_FAILURE = "connection_failure"
    PROCESSING_TIMEOUT = "processing_timeout"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    TRANSACTION_STUCK = "transaction_stuck"

@dataclass
class RecoveryAction:
    """Recovery action to be performed"""
    action_id: str
    failure_type: FailureType
    strategy: RecoveryStrategy
    target_process_id: Optional[str] = None
    target_stage: Optional[str] = None
    priority: int = 1  # 1 = highest, 5 = lowest
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RecoveryExecution:
    """Recovery execution record"""
    action_id: str
    strategy: RecoveryStrategy
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[RecoveryResult] = None
    error_message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    escalation_reason: Optional[str] = None

@dataclass
class RecoveryStatistics:
    """Recovery system statistics"""
    total_recoveries_attempted: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    escalated_recoveries: int = 0
    recovery_success_rate: float = 0.0
    avg_recovery_time: float = 0.0
    most_common_failure_type: Optional[str] = None
    recovery_strategies_used: Dict[str, int] = field(default_factory=dict)

class AutomatedRecoverySystem:
    """
    Automated recovery system that detects and fixes common pipeline failures
    without manual intervention, with escalation capabilities.
    """
    
    def __init__(self):
        self.recovery_queue: List[RecoveryAction] = []
        self.recovery_history: List[RecoveryExecution] = []
        self.recovery_strategies: Dict[FailureType, List[RecoveryStrategy]] = {}
        self.recovery_in_progress: Dict[str, RecoveryExecution] = {}
        
        # Recovery system state
        self.recovery_enabled = True
        self.recovery_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="recovery")
        
        # Recovery configuration
        self.max_recovery_attempts = 3
        self.recovery_cooldown_minutes = 10
        self.escalation_threshold = 2  # Number of failed attempts before escalation
        
        # Storage for recovery data
        self.storage_path = Path("data/automated_recovery")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.recovery_log_file = self.storage_path / "recovery_log.json"
        self.recovery_config_file = self.storage_path / "recovery_config.json"
        
        # Initialize system
        self._initialize_recovery_strategies()
        self._load_recovery_config()
        self._load_recovery_history()
        
        logger.info("🔧 Automated Recovery System initialized")
    
    def _initialize_recovery_strategies(self):
        """Initialize recovery strategies for different failure types"""
        self.recovery_strategies = {
            FailureType.STUCK_TEXT_EXTRACTION: [
                RecoveryStrategy.RETRY_OPERATION,
                RecoveryStrategy.CLEAR_MEMORY,
                RecoveryStrategy.RESTART_PROCESS,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ],
            FailureType.STUCK_ENTITY_PROCESSING: [
                RecoveryStrategy.RETRY_OPERATION,
                RecoveryStrategy.CLEAR_MEMORY,
                RecoveryStrategy.FORCE_COMPLETION,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ],
            FailureType.STUCK_NEO4J_POPULATION: [
                RecoveryStrategy.CIRCUIT_BREAKER_RESET,
                RecoveryStrategy.RESET_CONNECTION,
                RecoveryStrategy.RETRY_OPERATION,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ],
            FailureType.MEMORY_EXHAUSTION: [
                RecoveryStrategy.CLEAR_MEMORY,
                RecoveryStrategy.RESTART_PROCESS,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ],
            FailureType.CONNECTION_FAILURE: [
                RecoveryStrategy.RESET_CONNECTION,
                RecoveryStrategy.CIRCUIT_BREAKER_RESET,
                RecoveryStrategy.RETRY_OPERATION,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ],
            FailureType.PROCESSING_TIMEOUT: [
                RecoveryStrategy.RETRY_OPERATION,
                RecoveryStrategy.FORCE_COMPLETION,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ],
            FailureType.CIRCUIT_BREAKER_OPEN: [
                RecoveryStrategy.CIRCUIT_BREAKER_RESET,
                RecoveryStrategy.RESET_CONNECTION,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ],
            FailureType.TRANSACTION_STUCK: [
                RecoveryStrategy.TRANSACTION_ROLLBACK,
                RecoveryStrategy.RETRY_OPERATION,
                RecoveryStrategy.ESCALATE_TO_MANUAL
            ]
        }
    
    def _load_recovery_config(self):
        """Load recovery configuration from storage"""
        try:
            if self.recovery_config_file.exists():
                with open(self.recovery_config_file, 'r') as f:
                    config = json.load(f)
                
                self.max_recovery_attempts = config.get("max_recovery_attempts", self.max_recovery_attempts)
                self.recovery_cooldown_minutes = config.get("recovery_cooldown_minutes", self.recovery_cooldown_minutes)
                self.escalation_threshold = config.get("escalation_threshold", self.escalation_threshold)
                self.recovery_enabled = config.get("recovery_enabled", self.recovery_enabled)
                
                logger.info(f"📥 Loaded recovery configuration")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load recovery config: {e}")
    
    def _save_recovery_config(self):
        """Save recovery configuration to storage"""
        try:
            config = {
                "max_recovery_attempts": self.max_recovery_attempts,
                "recovery_cooldown_minutes": self.recovery_cooldown_minutes,
                "escalation_threshold": self.escalation_threshold,
                "recovery_enabled": self.recovery_enabled,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.recovery_config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save recovery config: {e}")
    
    def _load_recovery_history(self):
        """Load recovery history from storage"""
        try:
            if self.recovery_log_file.exists():
                with open(self.recovery_log_file, 'r') as f:
                    log_data = json.load(f)
                
                self.recovery_history = [
                    RecoveryExecution(
                        action_id=entry["action_id"],
                        strategy=RecoveryStrategy(entry["strategy"]),
                        started_at=datetime.fromisoformat(entry["started_at"]),
                        completed_at=datetime.fromisoformat(entry["completed_at"]) if entry.get("completed_at") else None,
                        result=RecoveryResult(entry["result"]) if entry.get("result") else None,
                        error_message=entry.get("error_message"),
                        context=entry.get("context", {}),
                        escalation_reason=entry.get("escalation_reason")
                    )
                    for entry in log_data
                ]
                
                logger.info(f"📥 Loaded {len(self.recovery_history)} recovery history entries")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load recovery history: {e}")
    
    def _save_recovery_history(self):
        """Save recovery history to storage"""
        try:
            log_data = [
                {
                    "action_id": execution.action_id,
                    "strategy": execution.strategy.value,
                    "started_at": execution.started_at.isoformat(),
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                    "result": execution.result.value if execution.result else None,
                    "error_message": execution.error_message,
                    "context": execution.context,
                    "escalation_reason": execution.escalation_reason
                }
                for execution in self.recovery_history
            ]
            
            with open(self.recovery_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save recovery history: {e}")
    
    def start_recovery_monitoring(self):
        """Start automated recovery monitoring"""
        if self.recovery_thread and self.recovery_thread.is_alive():
            logger.warning("⚠️ Recovery monitoring already running")
            return
        
        self.recovery_enabled = True
        self.recovery_thread = threading.Thread(
            target=self._recovery_monitoring_loop,
            daemon=True,
            name="recovery_monitor"
        )
        self.recovery_thread.start()
        
        logger.info("🚀 Automated recovery monitoring started")
    
    def stop_recovery_monitoring(self):
        """Stop automated recovery monitoring"""
        self.recovery_enabled = False
        
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.recovery_thread.join(timeout=10)
        
        logger.info("🛑 Automated recovery monitoring stopped")
    
    def _recovery_monitoring_loop(self):
        """Main recovery monitoring loop"""
        logger.info("🔧 Recovery monitoring loop started")
        
        while self.recovery_enabled:
            try:
                # Check for failure conditions
                self._detect_failures()
                
                # Process recovery queue
                self._process_recovery_queue()
                
                # Clean up completed recoveries
                self._cleanup_completed_recoveries()
                
                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in recovery monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
        
        logger.info("🔧 Recovery monitoring loop stopped")
    
    def _detect_failures(self):
        """Detect failure conditions that require recovery"""
        try:
            # Get system health to detect failures
            system_health = health_monitoring_system.get_system_health()
            
            # Check for stuck files
            self._detect_stuck_files()
            
            # Check for memory exhaustion
            self._detect_memory_exhaustion()
            
            # Check for connection failures
            self._detect_connection_failures()
            
            # Check for circuit breaker issues
            self._detect_circuit_breaker_issues()
            
            # Check for transaction issues
            self._detect_transaction_issues()
            
        except Exception as e:
            logger.error(f"❌ Error detecting failures: {e}")
    
    def _detect_stuck_files(self):
        """Detect stuck files in processing pipeline"""
        try:
            dashboard_data = health_monitoring_system.get_health_dashboard_data()
            stuck_files = dashboard_data.get("stuck_files", [])
            
            for stuck_file in stuck_files:
                # Create recovery action for stuck file
                failure_type = self._determine_failure_type_from_stage(stuck_file["stage"])
                
                action = RecoveryAction(
                    action_id=f"stuck_file_{stuck_file['process_id']}_{int(time.time())}",
                    failure_type=failure_type,
                    strategy=self.recovery_strategies[failure_type][0],  # First strategy
                    target_process_id=stuck_file["process_id"],
                    target_stage=stuck_file["stage"],
                    priority=1,
                    context=stuck_file
                )
                
                # Add to recovery queue if not already there
                if not any(a.target_process_id == stuck_file["process_id"] for a in self.recovery_queue):
                    self.recovery_queue.append(action)
                    logger.info(f"🔧 Added recovery action for stuck file: {stuck_file['filename']}")
                
        except Exception as e:
            logger.error(f"❌ Error detecting stuck files: {e}")
    
    def _detect_memory_exhaustion(self):
        """Detect memory exhaustion conditions"""
        try:
            memory_info = psutil.virtual_memory()
            
            # If memory usage is critically high
            if memory_info.percent > 95:
                action = RecoveryAction(
                    action_id=f"memory_exhaustion_{int(time.time())}",
                    failure_type=FailureType.MEMORY_EXHAUSTION,
                    strategy=RecoveryStrategy.CLEAR_MEMORY,
                    priority=1,
                    context={"memory_percent": memory_info.percent}
                )
                
                # Add to recovery queue if not already there
                if not any(a.failure_type == FailureType.MEMORY_EXHAUSTION for a in self.recovery_queue):
                    self.recovery_queue.append(action)
                    logger.warning(f"🔧 Added recovery action for memory exhaustion: {memory_info.percent}%")
                
        except Exception as e:
            logger.error(f"❌ Error detecting memory exhaustion: {e}")
    
    def _detect_connection_failures(self):
        """Detect connection failure conditions"""
        try:
            # Check if there are connection health issues
            system_health = health_monitoring_system.get_system_health()
            
            # Check for connection health alerts
            connection_alerts = [
                alert for alert in system_health.active_alerts
                if "connection" in alert.metric_name.lower()
            ]
            
            for alert in connection_alerts:
                if alert.severity == AlertSeverity.CRITICAL:
                    action = RecoveryAction(
                        action_id=f"connection_failure_{alert.alert_id}",
                        failure_type=FailureType.CONNECTION_FAILURE,
                        strategy=RecoveryStrategy.RESET_CONNECTION,
                        priority=1,
                        context={"alert_id": alert.alert_id, "metric_name": alert.metric_name}
                    )
                    
                    # Add to recovery queue if not already there
                    if not any(a.action_id == action.action_id for a in self.recovery_queue):
                        self.recovery_queue.append(action)
                        logger.warning(f"🔧 Added recovery action for connection failure: {alert.metric_name}")
                
        except Exception as e:
            logger.error(f"❌ Error detecting connection failures: {e}")
    
    def _detect_circuit_breaker_issues(self):
        """Detect circuit breaker issues"""
        try:
            cb_metrics = circuit_breaker.get_metrics()
            
            # If circuit breaker is open for too long
            if cb_metrics.get("state") == "OPEN":
                last_opened = cb_metrics.get("last_opened_at")
                if last_opened:
                    open_duration = (datetime.now() - datetime.fromisoformat(last_opened)).total_seconds()
                    
                    # If open for more than 5 minutes, attempt recovery
                    if open_duration > 300:
                        action = RecoveryAction(
                            action_id=f"circuit_breaker_open_{int(time.time())}",
                            failure_type=FailureType.CIRCUIT_BREAKER_OPEN,
                            strategy=RecoveryStrategy.CIRCUIT_BREAKER_RESET,
                            priority=2,
                            context={"open_duration": open_duration}
                        )
                        
                        # Add to recovery queue if not already there
                        if not any(a.failure_type == FailureType.CIRCUIT_BREAKER_OPEN for a in self.recovery_queue):
                            self.recovery_queue.append(action)
                            logger.warning(f"🔧 Added recovery action for circuit breaker open: {open_duration:.0f}s")
                
        except Exception as e:
            logger.error(f"❌ Error detecting circuit breaker issues: {e}")
    
    def _detect_transaction_issues(self):
        """Detect transaction issues"""
        try:
            # Check for stuck transactions
            active_transactions = transaction_manager.get_active_transactions()
            
            for transaction_id, transaction in active_transactions.items():
                transaction_age = (datetime.now() - transaction.created_at).total_seconds()
                
                # If transaction is older than 30 minutes, it's likely stuck
                if transaction_age > 1800:
                    action = RecoveryAction(
                        action_id=f"transaction_stuck_{transaction_id}",
                        failure_type=FailureType.TRANSACTION_STUCK,
                        strategy=RecoveryStrategy.TRANSACTION_ROLLBACK,
                        priority=2,
                        context={"transaction_id": transaction_id, "age_seconds": transaction_age}
                    )
                    
                    # Add to recovery queue if not already there
                    if not any(a.context.get("transaction_id") == transaction_id for a in self.recovery_queue):
                        self.recovery_queue.append(action)
                        logger.warning(f"🔧 Added recovery action for stuck transaction: {transaction_id}")
                
        except Exception as e:
            logger.error(f"❌ Error detecting transaction issues: {e}")
    
    def _determine_failure_type_from_stage(self, stage_name: str) -> FailureType:
        """Determine failure type based on processing stage"""
        stage_to_failure_map = {
            "validation": FailureType.PROCESSING_TIMEOUT,
            "extraction": FailureType.STUCK_TEXT_EXTRACTION,
            "rag_processing": FailureType.STUCK_ENTITY_PROCESSING,
            "neo4j_population": FailureType.STUCK_NEO4J_POPULATION,
            "verification": FailureType.PROCESSING_TIMEOUT,
            "integrity_check": FailureType.PROCESSING_TIMEOUT,
            "finalization": FailureType.PROCESSING_TIMEOUT
        }
        
        return stage_to_failure_map.get(stage_name, FailureType.PROCESSING_TIMEOUT)
    
    def _process_recovery_queue(self):
        """Process recovery queue"""
        if not self.recovery_queue:
            return
        
        # Sort by priority (1 = highest)
        self.recovery_queue.sort(key=lambda x: x.priority)
        
        # Process high priority items first
        for action in self.recovery_queue[:]:
            if self._should_execute_recovery(action):
                # Execute recovery in background
                self.executor.submit(self._execute_recovery, action)
                self.recovery_queue.remove(action)
    
    def _should_execute_recovery(self, action: RecoveryAction) -> bool:
        """Check if recovery action should be executed"""
        # Check if already in progress
        if action.action_id in self.recovery_in_progress:
            return False
        
        # Check cooldown period
        recent_attempts = [
            execution for execution in self.recovery_history
            if execution.action_id.startswith(action.failure_type.value)
            and execution.started_at > datetime.now() - timedelta(minutes=self.recovery_cooldown_minutes)
        ]
        
        if len(recent_attempts) >= self.max_recovery_attempts:
            logger.info(f"⏳ Recovery action {action.action_id} in cooldown period")
            return False
        
        return True
    
    def _execute_recovery(self, action: RecoveryAction):
        """Execute recovery action"""
        execution = RecoveryExecution(
            action_id=action.action_id,
            strategy=action.strategy,
            started_at=datetime.now(),
            context=action.context
        )
        
        self.recovery_in_progress[action.action_id] = execution
        
        try:
            logger.info(f"🔧 Executing recovery: {action.strategy.value} for {action.failure_type.value}")
            
            # Execute recovery strategy
            if action.strategy == RecoveryStrategy.RETRY_OPERATION:
                result = self._retry_operation(action)
            elif action.strategy == RecoveryStrategy.RESTART_PROCESS:
                result = self._restart_process(action)
            elif action.strategy == RecoveryStrategy.CLEAR_MEMORY:
                result = self._clear_memory(action)
            elif action.strategy == RecoveryStrategy.RESET_CONNECTION:
                result = self._reset_connection(action)
            elif action.strategy == RecoveryStrategy.FORCE_COMPLETION:
                result = self._force_completion(action)
            elif action.strategy == RecoveryStrategy.CIRCUIT_BREAKER_RESET:
                result = self._reset_circuit_breaker(action)
            elif action.strategy == RecoveryStrategy.TRANSACTION_ROLLBACK:
                result = self._rollback_transaction(action)
            else:
                result = self._escalate_to_manual(action)
            
            execution.result = result
            execution.completed_at = datetime.now()
            
            if result == RecoveryResult.SUCCESS:
                logger.info(f"✅ Recovery successful: {action.action_id}")
            elif result == RecoveryResult.FAILED:
                logger.error(f"❌ Recovery failed: {action.action_id}")
                self._schedule_escalation(action)
            elif result == RecoveryResult.ESCALATED:
                logger.warning(f"⬆️ Recovery escalated: {action.action_id}")
            
        except Exception as e:
            execution.result = RecoveryResult.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            logger.error(f"❌ Recovery execution failed: {action.action_id} - {e}")
            self._schedule_escalation(action)
        
        finally:
            # Move from in-progress to history
            if action.action_id in self.recovery_in_progress:
                del self.recovery_in_progress[action.action_id]
            
            self.recovery_history.append(execution)
            self._save_recovery_history()
    
    def _retry_operation(self, action: RecoveryAction) -> RecoveryResult:
        """Retry failed operation"""
        try:
            if action.target_process_id:
                # Retry specific process
                process_result = reliable_upload_pipeline.active_processes.get(action.target_process_id)
                if process_result:
                    # Find the stuck stage and retry it
                    for stage in process_result.stages:
                        if stage.name == action.target_stage and not stage.completed:
                            # Reset stage to retry
                            stage.error = None
                            stage.start_time = None
                            stage.end_time = None
                            
                            logger.info(f"🔄 Retrying stage {stage.name} for process {action.target_process_id}")
                            return RecoveryResult.SUCCESS
            
            return RecoveryResult.FAILED
            
        except Exception as e:
            logger.error(f"❌ Error retrying operation: {e}")
            return RecoveryResult.FAILED
    
    def _restart_process(self, action: RecoveryAction) -> RecoveryResult:
        """Restart stuck process"""
        try:
            if action.target_process_id:
                # Remove from active processes to trigger restart
                if action.target_process_id in reliable_upload_pipeline.active_processes:
                    process_result = reliable_upload_pipeline.active_processes[action.target_process_id]
                    
                    # Add to dead letter queue for retry
                    dead_letter_queue.add_failed_operation(
                        "process_restart",
                        {
                            "process_id": action.target_process_id,
                            "filename": process_result.filename,
                            "reason": "automated_recovery_restart"
                        },
                        Exception("Process restarted by automated recovery")
                    )
                    
                    # Remove from active processes
                    del reliable_upload_pipeline.active_processes[action.target_process_id]
                    
                    logger.info(f"🔄 Restarted process {action.target_process_id}")
                    return RecoveryResult.SUCCESS
            
            return RecoveryResult.FAILED
            
        except Exception as e:
            logger.error(f"❌ Error restarting process: {e}")
            return RecoveryResult.FAILED
    
    def _clear_memory(self, action: RecoveryAction) -> RecoveryResult:
        """Clear memory to resolve exhaustion"""
        try:
            import gc
            
            # Force garbage collection
            gc.collect()
            
            # Clear metrics buffers if they're too large
            if hasattr(health_monitoring_system, 'metrics_buffer'):
                if len(health_monitoring_system.metrics_buffer) > 5000:
                    # Keep only recent metrics
                    recent_metrics = list(health_monitoring_system.metrics_buffer)[-1000:]
                    health_monitoring_system.metrics_buffer.clear()
                    health_monitoring_system.metrics_buffer.extend(recent_metrics)
            
            logger.info("🧹 Cleared memory and forced garbage collection")
            return RecoveryResult.SUCCESS
            
        except Exception as e:
            logger.error(f"❌ Error clearing memory: {e}")
            return RecoveryResult.FAILED
    
    def _reset_connection(self, action: RecoveryAction) -> RecoveryResult:
        """Reset connection to resolve connectivity issues"""
        try:
            # Reset Neo4j connection
            if hasattr(enhanced_neo4j_service, 'reset_connection'):
                enhanced_neo4j_service.reset_connection()
            
            # Reset circuit breaker if it's open
            if circuit_breaker.get_metrics().get("state") == "OPEN":
                circuit_breaker.reset()
            
            logger.info("🔄 Reset connections")
            return RecoveryResult.SUCCESS
            
        except Exception as e:
            logger.error(f"❌ Error resetting connection: {e}")
            return RecoveryResult.FAILED
    
    def _force_completion(self, action: RecoveryAction) -> RecoveryResult:
        """Force completion of stuck process"""
        try:
            if action.target_process_id:
                process_result = reliable_upload_pipeline.active_processes.get(action.target_process_id)
                if process_result:
                    # Mark current stage as completed with warning
                    for stage in process_result.stages:
                        if stage.name == action.target_stage and not stage.completed:
                            stage.completed = True
                            stage.end_time = datetime.now()
                            stage.error = "Force completed by automated recovery"
                            
                            logger.warning(f"⚠️ Force completed stage {stage.name} for process {action.target_process_id}")
                            return RecoveryResult.PARTIAL_SUCCESS
            
            return RecoveryResult.FAILED
            
        except Exception as e:
            logger.error(f"❌ Error force completing process: {e}")
            return RecoveryResult.FAILED
    
    def _reset_circuit_breaker(self, action: RecoveryAction) -> RecoveryResult:
        """Reset circuit breaker"""
        try:
            circuit_breaker.reset()
            logger.info("🔄 Reset circuit breaker")
            return RecoveryResult.SUCCESS
            
        except Exception as e:
            logger.error(f"❌ Error resetting circuit breaker: {e}")
            return RecoveryResult.FAILED
    
    def _rollback_transaction(self, action: RecoveryAction) -> RecoveryResult:
        """Rollback stuck transaction"""
        try:
            transaction_id = action.context.get("transaction_id")
            if transaction_id:
                success = transaction_manager.rollback_transaction(transaction_id)
                if success:
                    logger.info(f"↩️ Rolled back transaction {transaction_id}")
                    return RecoveryResult.SUCCESS
            
            return RecoveryResult.FAILED
            
        except Exception as e:
            logger.error(f"❌ Error rolling back transaction: {e}")
            return RecoveryResult.FAILED
    
    def _escalate_to_manual(self, action: RecoveryAction) -> RecoveryResult:
        """Escalate to manual intervention"""
        try:
            # Add to dead letter queue for manual review
            dead_letter_queue.add_failed_operation(
                "manual_intervention_required",
                {
                    "action_id": action.action_id,
                    "failure_type": action.failure_type.value,
                    "context": action.context,
                    "escalation_reason": "automated_recovery_failed"
                },
                Exception("Escalated to manual intervention")
            )
            
            logger.warning(f"⬆️ Escalated to manual intervention: {action.action_id}")
            return RecoveryResult.ESCALATED
            
        except Exception as e:
            logger.error(f"❌ Error escalating to manual: {e}")
            return RecoveryResult.FAILED
    
    def _schedule_escalation(self, action: RecoveryAction):
        """Schedule escalation if recovery fails multiple times"""
        # Count recent failures for this failure type
        recent_failures = [
            execution for execution in self.recovery_history
            if execution.action_id.startswith(action.failure_type.value)
            and execution.result == RecoveryResult.FAILED
            and execution.started_at > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_failures) >= self.escalation_threshold:
            # Create escalation action
            escalation_action = RecoveryAction(
                action_id=f"escalation_{action.failure_type.value}_{int(time.time())}",
                failure_type=action.failure_type,
                strategy=RecoveryStrategy.ESCALATE_TO_MANUAL,
                priority=1,
                context={
                    "original_action": action.action_id,
                    "failure_count": len(recent_failures),
                    "escalation_reason": "multiple_recovery_failures"
                }
            )
            
            self.recovery_queue.append(escalation_action)
            logger.warning(f"⬆️ Scheduled escalation for {action.failure_type.value}")
    
    def _cleanup_completed_recoveries(self):
        """Clean up completed recoveries"""
        # Remove old recovery history entries (keep last 1000)
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-1000:]
            self._save_recovery_history()
    
    def get_recovery_statistics(self) -> RecoveryStatistics:
        """Get recovery system statistics"""
        total_recoveries = len(self.recovery_history)
        successful_recoveries = len([r for r in self.recovery_history if r.result == RecoveryResult.SUCCESS])
        failed_recoveries = len([r for r in self.recovery_history if r.result == RecoveryResult.FAILED])
        escalated_recoveries = len([r for r in self.recovery_history if r.result == RecoveryResult.ESCALATED])
        
        success_rate = (successful_recoveries / total_recoveries) * 100 if total_recoveries > 0 else 0
        
        # Calculate average recovery time
        completed_recoveries = [r for r in self.recovery_history if r.completed_at]
        avg_recovery_time = 0
        if completed_recoveries:
            total_time = sum(
                (r.completed_at - r.started_at).total_seconds()
                for r in completed_recoveries
            )
            avg_recovery_time = total_time / len(completed_recoveries)
        
        # Find most common failure type
        failure_counts = defaultdict(int)
        for recovery in self.recovery_history:
            if recovery.action_id:
                failure_type = recovery.action_id.split('_')[0]
                failure_counts[failure_type] += 1
        
        most_common_failure = max(failure_counts, key=failure_counts.get) if failure_counts else None
        
        # Strategy usage
        strategy_counts = defaultdict(int)
        for recovery in self.recovery_history:
            strategy_counts[recovery.strategy.value] += 1
        
        return RecoveryStatistics(
            total_recoveries_attempted=total_recoveries,
            successful_recoveries=successful_recoveries,
            failed_recoveries=failed_recoveries,
            escalated_recoveries=escalated_recoveries,
            recovery_success_rate=success_rate,
            avg_recovery_time=avg_recovery_time,
            most_common_failure_type=most_common_failure,
            recovery_strategies_used=dict(strategy_counts)
        )
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status"""
        stats = self.get_recovery_statistics()
        
        return {
            "recovery_enabled": self.recovery_enabled,
            "monitoring_active": self.recovery_thread.is_alive() if self.recovery_thread else False,
            "queue_size": len(self.recovery_queue),
            "recoveries_in_progress": len(self.recovery_in_progress),
            "recent_recoveries": len([
                r for r in self.recovery_history
                if r.started_at > datetime.now() - timedelta(hours=24)
            ]),
            "statistics": {
                "total_recoveries_attempted": stats.total_recoveries_attempted,
                "successful_recoveries": stats.successful_recoveries,
                "failed_recoveries": stats.failed_recoveries,
                "escalated_recoveries": stats.escalated_recoveries,
                "recovery_success_rate": stats.recovery_success_rate,
                "avg_recovery_time": stats.avg_recovery_time,
                "most_common_failure_type": stats.most_common_failure_type
            },
            "configuration": {
                "max_recovery_attempts": self.max_recovery_attempts,
                "recovery_cooldown_minutes": self.recovery_cooldown_minutes,
                "escalation_threshold": self.escalation_threshold
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def configure_recovery(self, max_attempts: int = None, cooldown_minutes: int = None, 
                         escalation_threshold: int = None):
        """Configure recovery system parameters"""
        if max_attempts is not None:
            self.max_recovery_attempts = max_attempts
        if cooldown_minutes is not None:
            self.recovery_cooldown_minutes = cooldown_minutes
        if escalation_threshold is not None:
            self.escalation_threshold = escalation_threshold
        
        self._save_recovery_config()
        logger.info("🔧 Updated recovery configuration")


# Global automated recovery instance
automated_recovery_system = AutomatedRecoverySystem()

logger.info("🚀 Automated Recovery System ready")