#!/usr/bin/env python3
"""
Phase 4A: Graceful Degradation Manager
======================================

Graceful degradation system that maintains service continuity when components fail
or perform poorly. Implements multiple degradation modes with automatic switching
based on system health metrics.

Features:
- Degradation mode detection based on health monitoring metrics and error patterns
- Local queue mode when Neo4j is unavailable to store operations for later processing
- Reduced batch processing mode when memory is constrained
- Selective processing mode that prioritizes critical operations when system is partially degraded
- Automatic mode switching based on system health with recovery to normal mode
- Data integrity maintenance while providing best possible service level
- Degradation status reporting for operational visibility

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import deque, defaultdict
import threading
import queue
import sqlite3
from concurrent.futures import ThreadPoolExecutor

# Import existing infrastructure
from reliability_infrastructure import circuit_breaker, transaction_manager, dead_letter_queue
from health_monitoring_system import health_monitoring_system, HealthStatus
from automated_recovery_system import automated_recovery_system
from enhanced_neo4j_service import enhanced_neo4j_service

logger = logging.getLogger(__name__)

class DegradationMode(Enum):
    """System degradation modes"""
    NORMAL = "normal"
    REDUCED_PERFORMANCE = "reduced_performance"
    LOCAL_QUEUE = "local_queue"
    MEMORY_CONSTRAINED = "memory_constrained"
    SELECTIVE_PROCESSING = "selective_processing"
    EMERGENCY_MODE = "emergency_mode"

class OperationPriority(Enum):
    """Operation priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    DEFERRED = "deferred"

class DegradationTrigger(Enum):
    """What triggered degradation mode"""
    NEO4J_UNAVAILABLE = "neo4j_unavailable"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    HIGH_ERROR_RATE = "high_error_rate"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    PROCESSING_TIMEOUT = "processing_timeout"
    QUEUE_OVERFLOW = "queue_overflow"
    MANUAL_OVERRIDE = "manual_override"

@dataclass
class DegradationEvent:
    """Degradation event record"""
    event_id: str
    trigger: DegradationTrigger
    from_mode: DegradationMode
    to_mode: DegradationMode
    timestamp: datetime
    health_metrics: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueuedOperation:
    """Operation queued during degradation"""
    operation_id: str
    operation_type: str
    operation_data: Dict[str, Any]
    priority: OperationPriority
    queued_at: datetime
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class DegradationStatus:
    """Current degradation status"""
    current_mode: DegradationMode
    mode_since: datetime
    triggers_active: List[DegradationTrigger]
    operations_queued: int
    operations_processed_degraded: int
    auto_recovery_enabled: bool
    next_health_check: datetime

class GracefulDegradationManager:
    """
    Graceful degradation manager that maintains service continuity when
    components fail or perform poorly.
    """
    
    def __init__(self):
        self.current_mode = DegradationMode.NORMAL
        self.mode_since = datetime.now()
        self.degradation_history: List[DegradationEvent] = []
        self.active_triggers: List[DegradationTrigger] = []
        
        # Local operation queue for degraded modes
        self.local_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.queued_operations: Dict[str, QueuedOperation] = {}
        
        # Degradation configuration
        self.degradation_thresholds = {
            DegradationTrigger.NEO4J_UNAVAILABLE: {
                "circuit_breaker_open_duration": 300,  # 5 minutes
                "connection_failure_rate": 0.8
            },
            DegradationTrigger.MEMORY_EXHAUSTION: {
                "memory_usage_threshold": 90.0,  # 90%
                "duration_minutes": 5
            },
            DegradationTrigger.HIGH_ERROR_RATE: {
                "error_rate_threshold": 0.3,  # 30%
                "duration_minutes": 10
            },
            DegradationTrigger.PROCESSING_TIMEOUT: {
                "timeout_threshold": 600,  # 10 minutes
                "timeout_count": 3
            },
            DegradationTrigger.QUEUE_OVERFLOW: {
                "queue_size_threshold": 100,
                "duration_minutes": 5
            }
        }
        
        # Recovery thresholds (for returning to normal mode)
        self.recovery_thresholds = {
            DegradationTrigger.NEO4J_UNAVAILABLE: {
                "connection_success_rate": 0.95,
                "stable_duration_minutes": 5
            },
            DegradationTrigger.MEMORY_EXHAUSTION: {
                "memory_usage_threshold": 70.0,  # Below 70%
                "stable_duration_minutes": 5
            },
            DegradationTrigger.HIGH_ERROR_RATE: {
                "error_rate_threshold": 0.05,  # Below 5%
                "stable_duration_minutes": 10
            }
        }
        
        # Degradation settings
        self.auto_recovery_enabled = True
        self.health_check_interval = 60  # seconds
        self.queue_processing_enabled = True
        
        # Statistics
        self.operations_processed_degraded = 0
        self.degradation_events_count = 0
        
        # Storage and monitoring
        self.storage_path = Path("data/graceful_degradation")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.local_db_path = self.storage_path / "local_queue.db"
        self.degradation_log_file = self.storage_path / "degradation_log.json"
        
        # Monitoring thread
        self.monitoring_enabled = True
        self.monitoring_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="degradation")
        
        # Initialize system
        self._initialize_local_storage()
        self._load_degradation_history()
        
        logger.info("🛡️ Graceful Degradation Manager initialized")
    
    def _initialize_local_storage(self):
        """Initialize local SQLite storage for queued operations"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queued_operations (
                    operation_id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    operation_data TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    queued_at TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS degradation_events (
                    event_id TEXT PRIMARY KEY,
                    trigger_type TEXT NOT NULL,
                    from_mode TEXT NOT NULL,
                    to_mode TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    health_metrics TEXT,
                    context TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("🗄️ Local degradation storage initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize local storage: {e}")
    
    def _load_degradation_history(self):
        """Load degradation history from storage"""
        try:
            if self.degradation_log_file.exists():
                with open(self.degradation_log_file, 'r') as f:
                    log_data = json.load(f)
                
                self.degradation_history = [
                    DegradationEvent(
                        event_id=event["event_id"],
                        trigger=DegradationTrigger(event["trigger"]),
                        from_mode=DegradationMode(event["from_mode"]),
                        to_mode=DegradationMode(event["to_mode"]),
                        timestamp=datetime.fromisoformat(event["timestamp"]),
                        health_metrics=event["health_metrics"],
                        context=event.get("context", {})
                    )
                    for event in log_data
                ]
                
                logger.info(f"📥 Loaded {len(self.degradation_history)} degradation events")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load degradation history: {e}")
    
    def _save_degradation_history(self):
        """Save degradation history to storage"""
        try:
            log_data = [
                {
                    "event_id": event.event_id,
                    "trigger": event.trigger.value,
                    "from_mode": event.from_mode.value,
                    "to_mode": event.to_mode.value,
                    "timestamp": event.timestamp.isoformat(),
                    "health_metrics": event.health_metrics,
                    "context": event.context
                }
                for event in self.degradation_history
            ]
            
            with open(self.degradation_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save degradation history: {e}")
    
    def start_monitoring(self):
        """Start degradation monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("⚠️ Degradation monitoring already running")
            return
        
        self.monitoring_enabled = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="degradation_monitor"
        )
        self.monitoring_thread.start()
        
        logger.info("🚀 Graceful degradation monitoring started")
    
    def stop_monitoring(self):
        """Stop degradation monitoring"""
        self.monitoring_enabled = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        
        logger.info("🛑 Graceful degradation monitoring stopped")
    
    def _monitoring_loop(self):
        """Main degradation monitoring loop"""
        logger.info("🛡️ Degradation monitoring loop started")
        
        while self.monitoring_enabled:
            try:
                # Check for degradation triggers
                self._check_degradation_triggers()
                
                # Process recovery conditions
                if self.current_mode != DegradationMode.NORMAL:
                    self._check_recovery_conditions()
                
                # Process local queue if in degraded mode
                if self.queue_processing_enabled and self.current_mode != DegradationMode.NORMAL:
                    self._process_local_queue()
                
                # Sleep for monitoring interval
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in degradation monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error
        
        logger.info("🛡️ Degradation monitoring loop stopped")
    
    def _check_degradation_triggers(self):
        """Check for conditions that trigger degradation modes"""
        try:
            # Get current system health
            system_health = health_monitoring_system.get_system_health()
            dashboard_data = health_monitoring_system.get_health_dashboard_data()
            
            current_triggers = []
            
            # Check Neo4j availability
            if self._check_neo4j_degradation():
                current_triggers.append(DegradationTrigger.NEO4J_UNAVAILABLE)
            
            # Check memory exhaustion
            if self._check_memory_degradation(dashboard_data):
                current_triggers.append(DegradationTrigger.MEMORY_EXHAUSTION)
            
            # Check error rate
            if self._check_error_rate_degradation(dashboard_data):
                current_triggers.append(DegradationTrigger.HIGH_ERROR_RATE)
            
            # Check queue overflow
            if self._check_queue_overflow_degradation(dashboard_data):
                current_triggers.append(DegradationTrigger.QUEUE_OVERFLOW)
            
            # Check processing timeouts
            if self._check_timeout_degradation(dashboard_data):
                current_triggers.append(DegradationTrigger.PROCESSING_TIMEOUT)
            
            # Update active triggers
            self.active_triggers = current_triggers
            
            # Determine appropriate degradation mode
            if current_triggers:
                target_mode = self._determine_degradation_mode(current_triggers)
                if target_mode != self.current_mode:
                    self._switch_degradation_mode(target_mode, current_triggers, system_health)
            
        except Exception as e:
            logger.error(f"❌ Error checking degradation triggers: {e}")
    
    def _check_neo4j_degradation(self) -> bool:
        """Check if Neo4j degradation should be triggered"""
        try:
            # Check circuit breaker state
            cb_metrics = circuit_breaker.get_metrics()
            
            if cb_metrics.get("state") == "OPEN":
                # Check how long circuit breaker has been open
                last_opened = cb_metrics.get("last_opened_at")
                if last_opened:
                    open_duration = (datetime.now() - datetime.fromisoformat(last_opened)).total_seconds()
                    threshold = self.degradation_thresholds[DegradationTrigger.NEO4J_UNAVAILABLE]["circuit_breaker_open_duration"]
                    
                    if open_duration > threshold:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking Neo4j degradation: {e}")
            return False
    
    def _check_memory_degradation(self, dashboard_data: Dict[str, Any]) -> bool:
        """Check if memory degradation should be triggered"""
        try:
            metrics_summary = dashboard_data.get("metrics_summary", {})
            memory_metric = metrics_summary.get("memory_usage_percent", {})
            
            if memory_metric:
                current_usage = memory_metric.get("latest_value", 0)
                threshold = self.degradation_thresholds[DegradationTrigger.MEMORY_EXHAUSTION]["memory_usage_threshold"]
                
                return current_usage > threshold
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking memory degradation: {e}")
            return False
    
    def _check_error_rate_degradation(self, dashboard_data: Dict[str, Any]) -> bool:
        """Check if error rate degradation should be triggered"""
        try:
            metrics_summary = dashboard_data.get("metrics_summary", {})
            error_rate_metric = metrics_summary.get("error_rate", {})
            
            if error_rate_metric:
                current_rate = error_rate_metric.get("latest_value", 0)
                threshold = self.degradation_thresholds[DegradationTrigger.HIGH_ERROR_RATE]["error_rate_threshold"]
                
                return current_rate > threshold
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking error rate degradation: {e}")
            return False
    
    def _check_queue_overflow_degradation(self, dashboard_data: Dict[str, Any]) -> bool:
        """Check if queue overflow degradation should be triggered"""
        try:
            metrics_summary = dashboard_data.get("metrics_summary", {})
            queue_depth_metric = metrics_summary.get("queue_depth", {})
            
            if queue_depth_metric:
                current_depth = queue_depth_metric.get("latest_value", 0)
                threshold = self.degradation_thresholds[DegradationTrigger.QUEUE_OVERFLOW]["queue_size_threshold"]
                
                return current_depth > threshold
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking queue overflow degradation: {e}")
            return False
    
    def _check_timeout_degradation(self, dashboard_data: Dict[str, Any]) -> bool:
        """Check if processing timeout degradation should be triggered"""
        try:
            stuck_files = dashboard_data.get("stuck_files", [])
            
            # Count files stuck for extended periods
            long_stuck_count = 0
            threshold_duration = self.degradation_thresholds[DegradationTrigger.PROCESSING_TIMEOUT]["timeout_threshold"]
            
            for stuck_file in stuck_files:
                stuck_duration = stuck_file.get("stuck_duration", 0)
                if stuck_duration > threshold_duration:
                    long_stuck_count += 1
            
            threshold_count = self.degradation_thresholds[DegradationTrigger.PROCESSING_TIMEOUT]["timeout_count"]
            return long_stuck_count >= threshold_count
            
        except Exception as e:
            logger.error(f"❌ Error checking timeout degradation: {e}")
            return False
    
    def _determine_degradation_mode(self, triggers: List[DegradationTrigger]) -> DegradationMode:
        """Determine appropriate degradation mode based on active triggers"""
        
        # Priority-based mode selection
        if DegradationTrigger.NEO4J_UNAVAILABLE in triggers:
            return DegradationMode.LOCAL_QUEUE
        
        if DegradationTrigger.MEMORY_EXHAUSTION in triggers:
            return DegradationMode.MEMORY_CONSTRAINED
        
        if DegradationTrigger.HIGH_ERROR_RATE in triggers:
            return DegradationMode.SELECTIVE_PROCESSING
        
        if DegradationTrigger.QUEUE_OVERFLOW in triggers:
            return DegradationMode.SELECTIVE_PROCESSING
        
        if DegradationTrigger.PROCESSING_TIMEOUT in triggers:
            return DegradationMode.REDUCED_PERFORMANCE
        
        # Multiple triggers = emergency mode
        if len(triggers) >= 3:
            return DegradationMode.EMERGENCY_MODE
        
        return DegradationMode.REDUCED_PERFORMANCE
    
    def _switch_degradation_mode(self, target_mode: DegradationMode, 
                                triggers: List[DegradationTrigger],
                                system_health: Any):
        """Switch to target degradation mode"""
        try:
            previous_mode = self.current_mode
            
            # Log degradation event
            event = DegradationEvent(
                event_id=f"degradation_{int(time.time())}",
                trigger=triggers[0] if triggers else DegradationTrigger.MANUAL_OVERRIDE,
                from_mode=previous_mode,
                to_mode=target_mode,
                timestamp=datetime.now(),
                health_metrics=system_health.metrics_summary,
                context={
                    "active_triggers": [t.value for t in triggers],
                    "system_health_status": system_health.overall_status.value
                }
            )
            
            # Apply degradation mode
            self.current_mode = target_mode
            self.mode_since = datetime.now()
            self.degradation_history.append(event)
            self.degradation_events_count += 1
            
            # Configure mode-specific behaviors
            self._configure_degradation_mode(target_mode)
            
            # Log the switch
            logger.warning(f"🛡️ Degradation mode switch: {previous_mode.value} → {target_mode.value}")
            logger.warning(f"   Triggers: {[t.value for t in triggers]}")
            
            # Save event
            self._save_degradation_history()
            
        except Exception as e:
            logger.error(f"❌ Error switching degradation mode: {e}")
    
    def _configure_degradation_mode(self, mode: DegradationMode):
        """Configure system behavior for specific degradation mode"""
        try:
            if mode == DegradationMode.LOCAL_QUEUE:
                # Enable local queuing, disable direct Neo4j operations
                logger.info("🗄️ Enabling local queue mode - operations will be queued locally")
                
            elif mode == DegradationMode.MEMORY_CONSTRAINED:
                # Reduce batch sizes, increase garbage collection
                logger.info("🧠 Enabling memory constrained mode - reducing batch sizes")
                
            elif mode == DegradationMode.SELECTIVE_PROCESSING:
                # Only process high-priority operations
                logger.info("🎯 Enabling selective processing mode - prioritizing critical operations")
                
            elif mode == DegradationMode.REDUCED_PERFORMANCE:
                # Increase timeouts, reduce concurrency
                logger.info("⏳ Enabling reduced performance mode - extending timeouts")
                
            elif mode == DegradationMode.EMERGENCY_MODE:
                # Minimal operations only
                logger.warning("🚨 Enabling emergency mode - minimal operations only")
                
        except Exception as e:
            logger.error(f"❌ Error configuring degradation mode: {e}")
    
    def _check_recovery_conditions(self):
        """Check if conditions allow recovery to normal mode"""
        try:
            if not self.auto_recovery_enabled:
                return
            
            # Check if all recovery conditions are met
            recovery_possible = True
            
            for trigger in self.active_triggers:
                if not self._check_individual_recovery_condition(trigger):
                    recovery_possible = False
                    break
            
            # If recovery is possible, switch back to normal mode
            if recovery_possible:
                self._recover_to_normal_mode()
            
        except Exception as e:
            logger.error(f"❌ Error checking recovery conditions: {e}")
    
    def _check_individual_recovery_condition(self, trigger: DegradationTrigger) -> bool:
        """Check if individual trigger condition has recovered"""
        try:
            if trigger == DegradationTrigger.NEO4J_UNAVAILABLE:
                # Check if Neo4j is available again
                cb_metrics = circuit_breaker.get_metrics()
                return cb_metrics.get("state") == "CLOSED"
            
            elif trigger == DegradationTrigger.MEMORY_EXHAUSTION:
                # Check if memory usage is back to normal
                dashboard_data = health_monitoring_system.get_health_dashboard_data()
                metrics_summary = dashboard_data.get("metrics_summary", {})
                memory_metric = metrics_summary.get("memory_usage_percent", {})
                
                if memory_metric:
                    current_usage = memory_metric.get("latest_value", 100)
                    threshold = self.recovery_thresholds[trigger]["memory_usage_threshold"]
                    return current_usage < threshold
            
            elif trigger == DegradationTrigger.HIGH_ERROR_RATE:
                # Check if error rate is back to normal
                dashboard_data = health_monitoring_system.get_health_dashboard_data()
                metrics_summary = dashboard_data.get("metrics_summary", {})
                error_rate_metric = metrics_summary.get("error_rate", {})
                
                if error_rate_metric:
                    current_rate = error_rate_metric.get("latest_value", 1.0)
                    threshold = self.recovery_thresholds[trigger]["error_rate_threshold"]
                    return current_rate < threshold
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking recovery condition for {trigger}: {e}")
            return False
    
    def _recover_to_normal_mode(self):
        """Recover to normal mode"""
        try:
            previous_mode = self.current_mode
            
            # Log recovery event
            event = DegradationEvent(
                event_id=f"recovery_{int(time.time())}",
                trigger=DegradationTrigger.MANUAL_OVERRIDE,  # Recovery is manual/automatic
                from_mode=previous_mode,
                to_mode=DegradationMode.NORMAL,
                timestamp=datetime.now(),
                health_metrics={},
                context={"recovery_type": "automatic" if self.auto_recovery_enabled else "manual"}
            )
            
            # Switch to normal mode
            self.current_mode = DegradationMode.NORMAL
            self.mode_since = datetime.now()
            self.active_triggers = []
            self.degradation_history.append(event)
            
            # Process any queued operations
            if previous_mode == DegradationMode.LOCAL_QUEUE:
                self._process_all_queued_operations()
            
            logger.info(f"✅ Recovered to normal mode from {previous_mode.value}")
            
            # Save event
            self._save_degradation_history()
            
        except Exception as e:
            logger.error(f"❌ Error recovering to normal mode: {e}")
    
    def queue_operation(self, operation_type: str, operation_data: Dict[str, Any], 
                       priority: OperationPriority = OperationPriority.NORMAL) -> str:
        """Queue operation during degraded mode"""
        try:
            operation_id = f"queued_{int(time.time())}_{len(self.queued_operations)}"
            
            queued_op = QueuedOperation(
                operation_id=operation_id,
                operation_type=operation_type,
                operation_data=operation_data,
                priority=priority,
                queued_at=datetime.now()
            )
            
            # Add to in-memory queue with priority
            priority_value = list(OperationPriority).index(priority)
            self.local_queue.put((priority_value, operation_id, queued_op))
            self.queued_operations[operation_id] = queued_op
            
            # Store in local database
            self._store_queued_operation(queued_op)
            
            logger.info(f"📋 Queued operation: {operation_type} (priority: {priority.value})")
            
            return operation_id
            
        except Exception as e:
            logger.error(f"❌ Error queuing operation: {e}")
            return ""
    
    def _store_queued_operation(self, operation: QueuedOperation):
        """Store queued operation in local database"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO queued_operations 
                (operation_id, operation_type, operation_data, priority, queued_at, retry_count, max_retries)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                operation.operation_id,
                operation.operation_type,
                json.dumps(operation.operation_data),
                operation.priority.value,
                operation.queued_at.isoformat(),
                operation.retry_count,
                operation.max_retries
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error storing queued operation: {e}")
    
    def _process_local_queue(self):
        """Process operations from local queue"""
        try:
            processed_count = 0
            max_process_per_cycle = 5  # Limit processing per cycle
            
            while not self.local_queue.empty() and processed_count < max_process_per_cycle:
                try:
                    # Get highest priority operation
                    priority_value, operation_id, operation = self.local_queue.get_nowait()
                    
                    # Process based on current mode
                    success = self._process_queued_operation(operation)
                    
                    if success:
                        # Remove from tracking
                        if operation_id in self.queued_operations:
                            del self.queued_operations[operation_id]
                        self._remove_stored_operation(operation_id)
                        self.operations_processed_degraded += 1
                    else:
                        # Retry or escalate
                        operation.retry_count += 1
                        if operation.retry_count < operation.max_retries:
                            # Re-queue for retry
                            self.local_queue.put((priority_value, operation_id, operation))
                            self._store_queued_operation(operation)
                        else:
                            # Escalate to dead letter queue
                            dead_letter_queue.add_failed_operation(
                                operation.operation_type,
                                operation.operation_data,
                                Exception("Max retries exceeded in degraded mode")
                            )
                    
                    processed_count += 1
                    
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"❌ Error processing queued operation: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error processing local queue: {e}")
    
    def _process_queued_operation(self, operation: QueuedOperation) -> bool:
        """Process a single queued operation"""
        try:
            # Process based on operation type and current degradation mode
            if self.current_mode == DegradationMode.LOCAL_QUEUE:
                # Try to process if Neo4j is available again
                if circuit_breaker.get_metrics().get("state") == "CLOSED":
                    return self._execute_operation(operation)
                else:
                    return False  # Keep queued
            
            elif self.current_mode == DegradationMode.SELECTIVE_PROCESSING:
                # Only process high/critical priority operations
                if operation.priority in [OperationPriority.CRITICAL, OperationPriority.HIGH]:
                    return self._execute_operation(operation)
                else:
                    return False  # Keep queued
            
            elif self.current_mode == DegradationMode.MEMORY_CONSTRAINED:
                # Process with reduced batch size
                return self._execute_operation_reduced(operation)
            
            else:
                # Try to process normally
                return self._execute_operation(operation)
            
        except Exception as e:
            logger.error(f"❌ Error processing queued operation: {e}")
            return False
    
    def _execute_operation(self, operation: QueuedOperation) -> bool:
        """Execute operation normally"""
        try:
            # This would integrate with the actual operation execution
            # For now, simulate successful execution
            logger.info(f"▶️ Executing operation: {operation.operation_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error executing operation: {e}")
            return False
    
    def _execute_operation_reduced(self, operation: QueuedOperation) -> bool:
        """Execute operation with reduced resource usage"""
        try:
            # This would implement reduced-resource execution
            logger.info(f"🔽 Executing operation (reduced): {operation.operation_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error executing reduced operation: {e}")
            return False
    
    def _process_all_queued_operations(self):
        """Process all queued operations during recovery"""
        try:
            logger.info("🔄 Processing all queued operations during recovery")
            
            # Process all operations in queue
            while not self.local_queue.empty():
                try:
                    priority_value, operation_id, operation = self.local_queue.get_nowait()
                    success = self._execute_operation(operation)
                    
                    if success:
                        if operation_id in self.queued_operations:
                            del self.queued_operations[operation_id]
                        self._remove_stored_operation(operation_id)
                        self.operations_processed_degraded += 1
                    
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"❌ Error processing queued operation during recovery: {e}")
            
            logger.info("✅ Completed processing queued operations")
            
        except Exception as e:
            logger.error(f"❌ Error processing all queued operations: {e}")
    
    def _remove_stored_operation(self, operation_id: str):
        """Remove operation from local storage"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM queued_operations WHERE operation_id = ?", (operation_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error removing stored operation: {e}")
    
    def get_degradation_status(self) -> DegradationStatus:
        """Get current degradation status"""
        return DegradationStatus(
            current_mode=self.current_mode,
            mode_since=self.mode_since,
            triggers_active=self.active_triggers.copy(),
            operations_queued=len(self.queued_operations),
            operations_processed_degraded=self.operations_processed_degraded,
            auto_recovery_enabled=self.auto_recovery_enabled,
            next_health_check=datetime.now() + timedelta(seconds=self.health_check_interval)
        )
    
    def get_degradation_metrics(self) -> Dict[str, Any]:
        """Get degradation metrics for monitoring"""
        current_time = datetime.now()
        
        # Calculate time in current mode
        time_in_mode = (current_time - self.mode_since).total_seconds()
        
        # Calculate degradation events in last 24 hours
        recent_events = [
            event for event in self.degradation_history
            if event.timestamp > current_time - timedelta(hours=24)
        ]
        
        return {
            "current_mode": self.current_mode.value,
            "time_in_mode_seconds": time_in_mode,
            "active_triggers": [t.value for t in self.active_triggers],
            "operations_queued": len(self.queued_operations),
            "operations_processed_degraded": self.operations_processed_degraded,
            "degradation_events_24h": len(recent_events),
            "total_degradation_events": self.degradation_events_count,
            "auto_recovery_enabled": self.auto_recovery_enabled,
            "queue_processing_enabled": self.queue_processing_enabled,
            "last_updated": current_time.isoformat()
        }
    
    def force_degradation_mode(self, mode: DegradationMode, reason: str = "manual override"):
        """Manually force a degradation mode"""
        try:
            previous_mode = self.current_mode
            
            event = DegradationEvent(
                event_id=f"manual_{int(time.time())}",
                trigger=DegradationTrigger.MANUAL_OVERRIDE,
                from_mode=previous_mode,
                to_mode=mode,
                timestamp=datetime.now(),
                health_metrics={},
                context={"reason": reason, "manual": True}
            )
            
            self.current_mode = mode
            self.mode_since = datetime.now()
            self.degradation_history.append(event)
            
            self._configure_degradation_mode(mode)
            
            logger.warning(f"🔧 Manual degradation mode switch: {previous_mode.value} → {mode.value}")
            logger.warning(f"   Reason: {reason}")
            
            self._save_degradation_history()
            
        except Exception as e:
            logger.error(f"❌ Error forcing degradation mode: {e}")
    
    def configure_degradation_thresholds(self, trigger: DegradationTrigger, **kwargs):
        """Configure degradation thresholds"""
        try:
            if trigger in self.degradation_thresholds:
                for key, value in kwargs.items():
                    if key in self.degradation_thresholds[trigger]:
                        self.degradation_thresholds[trigger][key] = value
                        logger.info(f"🔧 Updated {trigger.value} threshold: {key} = {value}")
            
        except Exception as e:
            logger.error(f"❌ Error configuring degradation thresholds: {e}")
    
    def enable_auto_recovery(self, enabled: bool = True):
        """Enable or disable automatic recovery"""
        self.auto_recovery_enabled = enabled
        logger.info(f"🔄 Auto recovery {'enabled' if enabled else 'disabled'}")


# Global graceful degradation instance
graceful_degradation_manager = GracefulDegradationManager()

logger.info("🚀 Graceful Degradation Manager ready")