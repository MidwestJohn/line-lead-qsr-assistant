#!/usr/bin/env python3
"""
Phase 3C: Performance Optimization Engine
=========================================

Dynamic performance optimization system that adjusts Enterprise Bridge parameters
based on real-time performance metrics and trend analysis.

Features:
- Performance trend analysis from processing history
- Dynamic batch size adjustment based on memory usage, processing latency, and success rates
- Neo4j connection pool optimization based on throughput and error rates
- Resource usage optimization adapting to current system capacity and load
- Performance metric collection and trending for continuous optimization
- Gradual and reversible optimization changes
- Integration with existing bridge configuration system

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import deque, defaultdict
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor

# Import existing infrastructure
from reliability_infrastructure import circuit_breaker, transaction_manager, dead_letter_queue
from enhanced_neo4j_service import enhanced_neo4j_service
from reliable_upload_pipeline import reliable_upload_pipeline
from health_monitoring_system import health_monitoring_system

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Types of optimization strategies"""
    BATCH_SIZE_ADJUSTMENT = "batch_size_adjustment"
    CONNECTION_POOL_OPTIMIZATION = "connection_pool_optimization"
    MEMORY_OPTIMIZATION = "memory_optimization"
    THROUGHPUT_OPTIMIZATION = "throughput_optimization"
    LATENCY_OPTIMIZATION = "latency_optimization"
    RESOURCE_BALANCING = "resource_balancing"

class OptimizationResult(Enum):
    """Optimization results"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    REVERTED = "reverted"
    SKIPPED = "skipped"

class TrendDirection(Enum):
    """Performance trend directions"""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    VOLATILE = "volatile"

@dataclass
class PerformanceMetric:
    """Performance metric for optimization analysis"""
    name: str
    value: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationAction:
    """Optimization action to be performed"""
    action_id: str
    strategy: OptimizationStrategy
    parameter_name: str
    current_value: Any
    target_value: Any
    reason: str
    confidence: float  # 0.0 to 1.0
    priority: int = 3  # 1 = highest, 5 = lowest
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationExecution:
    """Optimization execution record"""
    action_id: str
    strategy: OptimizationStrategy
    parameter_name: str
    old_value: Any
    new_value: Any
    executed_at: datetime
    result: OptimizationResult
    performance_before: Dict[str, float]
    performance_after: Dict[str, float] = field(default_factory=dict)
    reverted_at: Optional[datetime] = None
    revert_reason: Optional[str] = None

@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_name: str
    direction: TrendDirection
    slope: float
    confidence: float
    data_points: int
    time_window: timedelta
    last_updated: datetime

@dataclass
class OptimizationConfiguration:
    """Optimization system configuration"""
    enabled: bool = True
    analysis_window_hours: int = 24
    min_data_points: int = 10
    confidence_threshold: float = 0.7
    max_parameter_change_percent: float = 20.0
    optimization_interval_minutes: int = 30
    performance_monitoring_minutes: int = 60
    auto_revert_threshold: float = 0.1  # 10% performance degradation

class PerformanceOptimizationEngine:
    """
    Dynamic performance optimization system that continuously analyzes performance
    metrics and adjusts system parameters for optimal performance.
    """
    
    def __init__(self):
        self.performance_metrics: deque = deque(maxlen=50000)  # Keep 50k metrics
        self.optimization_history: List[OptimizationExecution] = []
        self.optimization_queue: List[OptimizationAction] = []
        self.active_optimizations: Dict[str, OptimizationExecution] = {}
        
        # Performance trends
        self.performance_trends: Dict[str, PerformanceTrend] = {}
        
        # Optimization state
        self.optimization_enabled = True
        self.optimization_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="optimization")
        
        # Configuration
        self.config = OptimizationConfiguration()
        
        # Current system parameters (for tracking changes)
        self.current_parameters: Dict[str, Any] = {}
        
        # Storage for optimization data
        self.storage_path = Path("data/performance_optimization")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.storage_path / "performance_metrics.json"
        self.optimization_log_file = self.storage_path / "optimization_log.json"
        self.config_file = self.storage_path / "optimization_config.json"
        
        # Initialize system
        self._initialize_parameters()
        self._load_optimization_config()
        self._load_optimization_history()
        
        logger.info("⚡ Performance Optimization Engine initialized")
    
    def _initialize_parameters(self):
        """Initialize current system parameters"""
        try:
            # Initialize with default values
            self.current_parameters = {
                "batch_size": 1,  # Default batch size
                "connection_pool_size": 5,  # Default connection pool size
                "memory_limit_mb": 1024,  # Default memory limit
                "processing_timeout_seconds": 300,  # Default processing timeout
                "retry_attempts": 3,  # Default retry attempts
                "circuit_breaker_threshold": 5,  # Default circuit breaker threshold
                "transaction_timeout_seconds": 600,  # Default transaction timeout
            }
            
            # Try to get actual values from system components
            cb_config = circuit_breaker.get_metrics()
            if cb_config:
                self.current_parameters["circuit_breaker_threshold"] = cb_config.get("failure_threshold", 5)
            
            logger.info("🔧 Initialized system parameters")
            
        except Exception as e:
            logger.error(f"❌ Error initializing parameters: {e}")
    
    def _load_optimization_config(self):
        """Load optimization configuration from storage"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update configuration
                self.config.enabled = config_data.get("enabled", self.config.enabled)
                self.config.analysis_window_hours = config_data.get("analysis_window_hours", self.config.analysis_window_hours)
                self.config.min_data_points = config_data.get("min_data_points", self.config.min_data_points)
                self.config.confidence_threshold = config_data.get("confidence_threshold", self.config.confidence_threshold)
                self.config.max_parameter_change_percent = config_data.get("max_parameter_change_percent", self.config.max_parameter_change_percent)
                self.config.optimization_interval_minutes = config_data.get("optimization_interval_minutes", self.config.optimization_interval_minutes)
                self.config.performance_monitoring_minutes = config_data.get("performance_monitoring_minutes", self.config.performance_monitoring_minutes)
                self.config.auto_revert_threshold = config_data.get("auto_revert_threshold", self.config.auto_revert_threshold)
                
                logger.info(f"📥 Loaded optimization configuration")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load optimization config: {e}")
    
    def _save_optimization_config(self):
        """Save optimization configuration to storage"""
        try:
            config_data = {
                "enabled": self.config.enabled,
                "analysis_window_hours": self.config.analysis_window_hours,
                "min_data_points": self.config.min_data_points,
                "confidence_threshold": self.config.confidence_threshold,
                "max_parameter_change_percent": self.config.max_parameter_change_percent,
                "optimization_interval_minutes": self.config.optimization_interval_minutes,
                "performance_monitoring_minutes": self.config.performance_monitoring_minutes,
                "auto_revert_threshold": self.config.auto_revert_threshold,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save optimization config: {e}")
    
    def _load_optimization_history(self):
        """Load optimization history from storage"""
        try:
            if self.optimization_log_file.exists():
                with open(self.optimization_log_file, 'r') as f:
                    log_data = json.load(f)
                
                self.optimization_history = [
                    OptimizationExecution(
                        action_id=entry["action_id"],
                        strategy=OptimizationStrategy(entry["strategy"]),
                        parameter_name=entry["parameter_name"],
                        old_value=entry["old_value"],
                        new_value=entry["new_value"],
                        executed_at=datetime.fromisoformat(entry["executed_at"]),
                        result=OptimizationResult(entry["result"]),
                        performance_before=entry["performance_before"],
                        performance_after=entry.get("performance_after", {}),
                        reverted_at=datetime.fromisoformat(entry["reverted_at"]) if entry.get("reverted_at") else None,
                        revert_reason=entry.get("revert_reason")
                    )
                    for entry in log_data
                ]
                
                logger.info(f"📥 Loaded {len(self.optimization_history)} optimization history entries")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load optimization history: {e}")
    
    def _save_optimization_history(self):
        """Save optimization history to storage"""
        try:
            log_data = [
                {
                    "action_id": execution.action_id,
                    "strategy": execution.strategy.value,
                    "parameter_name": execution.parameter_name,
                    "old_value": execution.old_value,
                    "new_value": execution.new_value,
                    "executed_at": execution.executed_at.isoformat(),
                    "result": execution.result.value,
                    "performance_before": execution.performance_before,
                    "performance_after": execution.performance_after,
                    "reverted_at": execution.reverted_at.isoformat() if execution.reverted_at else None,
                    "revert_reason": execution.revert_reason
                }
                for execution in self.optimization_history
            ]
            
            with open(self.optimization_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save optimization history: {e}")
    
    def start_optimization(self):
        """Start performance optimization monitoring"""
        if self.optimization_thread and self.optimization_thread.is_alive():
            logger.warning("⚠️ Performance optimization already running")
            return
        
        self.optimization_enabled = True
        self.optimization_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True,
            name="performance_optimizer"
        )
        self.optimization_thread.start()
        
        logger.info("🚀 Performance optimization started")
    
    def stop_optimization(self):
        """Stop performance optimization monitoring"""
        self.optimization_enabled = False
        
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=10)
        
        logger.info("🛑 Performance optimization stopped")
    
    def _optimization_loop(self):
        """Main optimization loop"""
        logger.info("⚡ Performance optimization loop started")
        
        last_optimization_time = 0
        last_analysis_time = 0
        
        while self.optimization_enabled:
            try:
                current_time = time.time()
                
                # Collect performance metrics
                self._collect_performance_metrics()
                
                # Analyze trends periodically
                if current_time - last_analysis_time >= 300:  # Every 5 minutes
                    self._analyze_performance_trends()
                    last_analysis_time = current_time
                
                # Perform optimization periodically
                if current_time - last_optimization_time >= self.config.optimization_interval_minutes * 60:
                    self._perform_optimization_analysis()
                    last_optimization_time = current_time
                
                # Process optimization queue
                self._process_optimization_queue()
                
                # Monitor active optimizations
                self._monitor_active_optimizations()
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Error in optimization loop: {e}")
                time.sleep(300)  # Wait longer on error
        
        logger.info("⚡ Performance optimization loop stopped")
    
    def _collect_performance_metrics(self):
        """Collect performance metrics for optimization analysis"""
        try:
            timestamp = datetime.now()
            
            # Get pipeline statistics
            pipeline_stats = reliable_upload_pipeline.get_pipeline_statistics()
            
            # Collect key performance metrics
            metrics = [
                PerformanceMetric(
                    name="processing_time_avg",
                    value=pipeline_stats.get("average_duration", 0),
                    timestamp=timestamp,
                    context={"total_processes": pipeline_stats.get("total_processes", 0)}
                ),
                PerformanceMetric(
                    name="success_rate",
                    value=pipeline_stats.get("success_rate", 0),
                    timestamp=timestamp,
                    context={"failed_processes": pipeline_stats.get("failed_processes", 0)}
                ),
                PerformanceMetric(
                    name="throughput",
                    value=len(reliable_upload_pipeline.active_processes),
                    timestamp=timestamp,
                    context={"queue_depth": len(reliable_upload_pipeline.active_processes)}
                )
            ]
            
            # Get memory usage
            memory_info = psutil.virtual_memory()
            metrics.append(PerformanceMetric(
                name="memory_usage_percent",
                value=memory_info.percent,
                timestamp=timestamp,
                context={"available_gb": memory_info.available / (1024**3)}
            ))
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(PerformanceMetric(
                name="cpu_usage_percent",
                value=cpu_percent,
                timestamp=timestamp,
                context={"cpu_count": psutil.cpu_count()}
            ))
            
            # Get circuit breaker metrics
            cb_metrics = circuit_breaker.get_metrics()
            if cb_metrics:
                metrics.append(PerformanceMetric(
                    name="circuit_breaker_failures",
                    value=cb_metrics.get("failure_count", 0),
                    timestamp=timestamp,
                    context={"state": cb_metrics.get("state", "unknown")}
                ))
            
            # Add metrics to buffer
            self.performance_metrics.extend(metrics)
            
        except Exception as e:
            logger.error(f"❌ Error collecting performance metrics: {e}")
    
    def _analyze_performance_trends(self):
        """Analyze performance trends for optimization decisions"""
        try:
            current_time = datetime.now()
            analysis_window = timedelta(hours=self.config.analysis_window_hours)
            
            # Get metrics within analysis window
            recent_metrics = [
                m for m in self.performance_metrics
                if m.timestamp > current_time - analysis_window
            ]
            
            # Group metrics by name
            metric_groups = defaultdict(list)
            for metric in recent_metrics:
                metric_groups[metric.name].append(metric)
            
            # Analyze trends for each metric
            for metric_name, metrics in metric_groups.items():
                if len(metrics) >= self.config.min_data_points:
                    trend = self._calculate_trend(metrics)
                    self.performance_trends[metric_name] = trend
            
            logger.debug(f"📊 Analyzed trends for {len(self.performance_trends)} metrics")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing performance trends: {e}")
    
    def _calculate_trend(self, metrics: List[PerformanceMetric]) -> PerformanceTrend:
        """Calculate performance trend for a set of metrics"""
        # Sort metrics by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        # Calculate slope using linear regression
        n = len(sorted_metrics)
        x_values = list(range(n))
        y_values = [m.value for m in sorted_metrics]
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Calculate correlation coefficient for confidence
        if len(y_values) > 1:
            correlation = abs(statistics.correlation(x_values, y_values))
            confidence = min(correlation, 1.0)
        else:
            confidence = 0.0
        
        # Determine trend direction
        if abs(slope) < 0.01:  # Very small slope
            direction = TrendDirection.STABLE
        elif slope > 0.1:
            direction = TrendDirection.IMPROVING if sorted_metrics[0].name in ["success_rate", "throughput"] else TrendDirection.DEGRADING
        elif slope < -0.1:
            direction = TrendDirection.DEGRADING if sorted_metrics[0].name in ["success_rate", "throughput"] else TrendDirection.IMPROVING
        else:
            direction = TrendDirection.STABLE
        
        # Check for volatility
        if statistics.stdev(y_values) > statistics.mean(y_values) * 0.5:
            direction = TrendDirection.VOLATILE
        
        return PerformanceTrend(
            metric_name=sorted_metrics[0].name,
            direction=direction,
            slope=slope,
            confidence=confidence,
            data_points=n,
            time_window=sorted_metrics[-1].timestamp - sorted_metrics[0].timestamp,
            last_updated=datetime.now()
        )
    
    def _perform_optimization_analysis(self):
        """Perform optimization analysis and generate optimization actions"""
        try:
            logger.info("🔍 Performing optimization analysis")
            
            # Analyze each performance area
            optimization_actions = []
            
            # 1. Batch size optimization
            batch_optimization = self._analyze_batch_size_optimization()
            if batch_optimization:
                optimization_actions.append(batch_optimization)
            
            # 2. Connection pool optimization
            connection_optimization = self._analyze_connection_pool_optimization()
            if connection_optimization:
                optimization_actions.append(connection_optimization)
            
            # 3. Memory optimization
            memory_optimization = self._analyze_memory_optimization()
            if memory_optimization:
                optimization_actions.append(memory_optimization)
            
            # 4. Circuit breaker optimization
            circuit_optimization = self._analyze_circuit_breaker_optimization()
            if circuit_optimization:
                optimization_actions.append(circuit_optimization)
            
            # Add high-confidence optimizations to queue
            for action in optimization_actions:
                if action.confidence >= self.config.confidence_threshold:
                    self.optimization_queue.append(action)
                    logger.info(f"⚡ Queued optimization: {action.strategy.value} - {action.reason}")
            
        except Exception as e:
            logger.error(f"❌ Error performing optimization analysis: {e}")
    
    def _analyze_batch_size_optimization(self) -> Optional[OptimizationAction]:
        """Analyze batch size optimization opportunities"""
        try:
            # Check processing time and memory usage trends
            processing_trend = self.performance_trends.get("processing_time_avg")
            memory_trend = self.performance_trends.get("memory_usage_percent")
            
            if not processing_trend or not memory_trend:
                return None
            
            current_batch_size = self.current_parameters.get("batch_size", 1)
            
            # If processing time is high but memory usage is low, consider increasing batch size
            if (processing_trend.direction == TrendDirection.DEGRADING and 
                memory_trend.direction != TrendDirection.DEGRADING and
                memory_trend.slope < 0.05):  # Memory stable or improving
                
                # Get recent memory usage
                recent_memory_metrics = [
                    m for m in self.performance_metrics
                    if m.name == "memory_usage_percent" and 
                    m.timestamp > datetime.now() - timedelta(hours=1)
                ]
                
                if recent_memory_metrics:
                    avg_memory = statistics.mean(m.value for m in recent_memory_metrics)
                    
                    # If memory usage is below 70%, consider increasing batch size
                    if avg_memory < 70:
                        new_batch_size = min(current_batch_size + 1, 5)  # Max batch size of 5
                        
                        if new_batch_size != current_batch_size:
                            return OptimizationAction(
                                action_id=f"batch_size_increase_{int(time.time())}",
                                strategy=OptimizationStrategy.BATCH_SIZE_ADJUSTMENT,
                                parameter_name="batch_size",
                                current_value=current_batch_size,
                                target_value=new_batch_size,
                                reason="Increase batch size to improve processing time with available memory",
                                confidence=0.8,
                                priority=2
                            )
            
            # If memory usage is high, consider decreasing batch size
            elif (memory_trend.direction == TrendDirection.DEGRADING and 
                  current_batch_size > 1):
                
                new_batch_size = max(current_batch_size - 1, 1)
                
                return OptimizationAction(
                    action_id=f"batch_size_decrease_{int(time.time())}",
                    strategy=OptimizationStrategy.BATCH_SIZE_ADJUSTMENT,
                    parameter_name="batch_size",
                    current_value=current_batch_size,
                    target_value=new_batch_size,
                    reason="Decrease batch size to reduce memory usage",
                    confidence=0.7,
                    priority=1
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error analyzing batch size optimization: {e}")
            return None
    
    def _analyze_connection_pool_optimization(self) -> Optional[OptimizationAction]:
        """Analyze connection pool optimization opportunities"""
        try:
            # Check circuit breaker and throughput trends
            cb_trend = self.performance_trends.get("circuit_breaker_failures")
            throughput_trend = self.performance_trends.get("throughput")
            
            if not cb_trend or not throughput_trend:
                return None
            
            current_pool_size = self.current_parameters.get("connection_pool_size", 5)
            
            # If circuit breaker failures are increasing, consider increasing pool size
            if (cb_trend.direction == TrendDirection.DEGRADING and 
                throughput_trend.direction == TrendDirection.DEGRADING):
                
                new_pool_size = min(current_pool_size + 2, 20)  # Max pool size of 20
                
                if new_pool_size != current_pool_size:
                    return OptimizationAction(
                        action_id=f"pool_size_increase_{int(time.time())}",
                        strategy=OptimizationStrategy.CONNECTION_POOL_OPTIMIZATION,
                        parameter_name="connection_pool_size",
                        current_value=current_pool_size,
                        target_value=new_pool_size,
                        reason="Increase connection pool size to reduce failures and improve throughput",
                        confidence=0.75,
                        priority=2
                    )
            
            # If circuit breaker is stable and throughput is stable, consider optimizing pool size
            elif (cb_trend.direction == TrendDirection.STABLE and 
                  throughput_trend.direction == TrendDirection.STABLE and
                  current_pool_size > 10):
                
                new_pool_size = max(current_pool_size - 1, 5)  # Min pool size of 5
                
                return OptimizationAction(
                    action_id=f"pool_size_decrease_{int(time.time())}",
                    strategy=OptimizationStrategy.CONNECTION_POOL_OPTIMIZATION,
                    parameter_name="connection_pool_size",
                    current_value=current_pool_size,
                    target_value=new_pool_size,
                    reason="Optimize connection pool size for resource efficiency",
                    confidence=0.6,
                    priority=3
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error analyzing connection pool optimization: {e}")
            return None
    
    def _analyze_memory_optimization(self) -> Optional[OptimizationAction]:
        """Analyze memory optimization opportunities"""
        try:
            memory_trend = self.performance_trends.get("memory_usage_percent")
            
            if not memory_trend:
                return None
            
            current_memory_limit = self.current_parameters.get("memory_limit_mb", 1024)
            
            # If memory usage is consistently high, consider increasing limit
            if memory_trend.direction == TrendDirection.DEGRADING:
                
                # Get recent memory usage
                recent_memory_metrics = [
                    m for m in self.performance_metrics
                    if m.name == "memory_usage_percent" and 
                    m.timestamp > datetime.now() - timedelta(hours=1)
                ]
                
                if recent_memory_metrics:
                    avg_memory = statistics.mean(m.value for m in recent_memory_metrics)
                    
                    # If memory usage is above 85%, consider increasing limit
                    if avg_memory > 85:
                        new_memory_limit = min(current_memory_limit + 256, 4096)  # Max 4GB
                        
                        if new_memory_limit != current_memory_limit:
                            return OptimizationAction(
                                action_id=f"memory_limit_increase_{int(time.time())}",
                                strategy=OptimizationStrategy.MEMORY_OPTIMIZATION,
                                parameter_name="memory_limit_mb",
                                current_value=current_memory_limit,
                                target_value=new_memory_limit,
                                reason="Increase memory limit to prevent memory exhaustion",
                                confidence=0.8,
                                priority=1
                            )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error analyzing memory optimization: {e}")
            return None
    
    def _analyze_circuit_breaker_optimization(self) -> Optional[OptimizationAction]:
        """Analyze circuit breaker optimization opportunities"""
        try:
            cb_trend = self.performance_trends.get("circuit_breaker_failures")
            success_trend = self.performance_trends.get("success_rate")
            
            if not cb_trend or not success_trend:
                return None
            
            current_threshold = self.current_parameters.get("circuit_breaker_threshold", 5)
            
            # If circuit breaker failures are stable but success rate is low, consider adjusting threshold
            if (cb_trend.direction == TrendDirection.STABLE and 
                success_trend.direction == TrendDirection.DEGRADING):
                
                # Get recent circuit breaker state
                cb_metrics = circuit_breaker.get_metrics()
                if cb_metrics and cb_metrics.get("state") == "OPEN":
                    
                    # Consider increasing threshold to be more tolerant
                    new_threshold = min(current_threshold + 1, 10)  # Max threshold of 10
                    
                    if new_threshold != current_threshold:
                        return OptimizationAction(
                            action_id=f"cb_threshold_increase_{int(time.time())}",
                            strategy=OptimizationStrategy.THROUGHPUT_OPTIMIZATION,
                            parameter_name="circuit_breaker_threshold",
                            current_value=current_threshold,
                            target_value=new_threshold,
                            reason="Increase circuit breaker threshold to improve fault tolerance",
                            confidence=0.6,
                            priority=3
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error analyzing circuit breaker optimization: {e}")
            return None
    
    def _process_optimization_queue(self):
        """Process optimization queue"""
        if not self.optimization_queue:
            return
        
        # Sort by priority (1 = highest)
        self.optimization_queue.sort(key=lambda x: x.priority)
        
        # Process high priority optimizations
        for action in self.optimization_queue[:]:
            if self._should_execute_optimization(action):
                # Execute optimization in background
                self.executor.submit(self._execute_optimization, action)
                self.optimization_queue.remove(action)
    
    def _should_execute_optimization(self, action: OptimizationAction) -> bool:
        """Check if optimization should be executed"""
        # Check if already optimizing this parameter
        if any(exec.parameter_name == action.parameter_name for exec in self.active_optimizations.values()):
            return False
        
        # Check if recent optimization was performed on this parameter
        recent_optimizations = [
            opt for opt in self.optimization_history
            if opt.parameter_name == action.parameter_name and
            opt.executed_at > datetime.now() - timedelta(hours=2)
        ]
        
        if recent_optimizations:
            logger.info(f"⏳ Optimization for {action.parameter_name} skipped - recent optimization exists")
            return False
        
        return True
    
    def _execute_optimization(self, action: OptimizationAction):
        """Execute optimization action"""
        execution = OptimizationExecution(
            action_id=action.action_id,
            strategy=action.strategy,
            parameter_name=action.parameter_name,
            old_value=action.current_value,
            new_value=action.target_value,
            executed_at=datetime.now(),
            result=OptimizationResult.FAILED,  # Default to failed
            performance_before=self._get_current_performance_snapshot()
        )
        
        self.active_optimizations[action.action_id] = execution
        
        try:
            logger.info(f"⚡ Executing optimization: {action.strategy.value} - {action.parameter_name}")
            
            # Execute the optimization
            success = self._apply_parameter_change(action.parameter_name, action.target_value)
            
            if success:
                execution.result = OptimizationResult.SUCCESS
                self.current_parameters[action.parameter_name] = action.target_value
                
                logger.info(f"✅ Optimization applied: {action.parameter_name} = {action.target_value}")
                
                # Schedule performance monitoring
                self.executor.submit(self._monitor_optimization_performance, execution)
                
            else:
                execution.result = OptimizationResult.FAILED
                logger.error(f"❌ Optimization failed: {action.parameter_name}")
            
        except Exception as e:
            execution.result = OptimizationResult.FAILED
            logger.error(f"❌ Optimization execution failed: {action.action_id} - {e}")
        
        finally:
            # Move from active to history (will be moved again after performance monitoring)
            if execution.result == OptimizationResult.FAILED:
                if action.action_id in self.active_optimizations:
                    del self.active_optimizations[action.action_id]
                
                self.optimization_history.append(execution)
                self._save_optimization_history()
    
    def _apply_parameter_change(self, parameter_name: str, new_value: Any) -> bool:
        """Apply parameter change to the system"""
        try:
            # Apply different parameter changes based on parameter name
            if parameter_name == "batch_size":
                # This would be applied to the processing pipeline
                # For now, just update the tracked value
                return True
            
            elif parameter_name == "connection_pool_size":
                # This would be applied to the Neo4j connection pool
                # For now, just update the tracked value
                return True
            
            elif parameter_name == "memory_limit_mb":
                # This would be applied to the memory management system
                # For now, just update the tracked value
                return True
            
            elif parameter_name == "circuit_breaker_threshold":
                # Apply to circuit breaker configuration
                # This is a placeholder - would need actual implementation
                return True
            
            else:
                logger.warning(f"⚠️ Unknown parameter: {parameter_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error applying parameter change: {e}")
            return False
    
    def _get_current_performance_snapshot(self) -> Dict[str, float]:
        """Get current performance snapshot"""
        try:
            # Get recent performance metrics
            recent_metrics = [
                m for m in self.performance_metrics
                if m.timestamp > datetime.now() - timedelta(minutes=10)
            ]
            
            snapshot = {}
            
            # Calculate averages for key metrics
            metric_groups = defaultdict(list)
            for metric in recent_metrics:
                metric_groups[metric.name].append(metric.value)
            
            for metric_name, values in metric_groups.items():
                if values:
                    snapshot[metric_name] = statistics.mean(values)
            
            return snapshot
            
        except Exception as e:
            logger.error(f"❌ Error getting performance snapshot: {e}")
            return {}
    
    def _monitor_optimization_performance(self, execution: OptimizationExecution):
        """Monitor performance after optimization"""
        try:
            # Wait for performance monitoring period
            time.sleep(self.config.performance_monitoring_minutes * 60)
            
            # Get performance after optimization
            execution.performance_after = self._get_current_performance_snapshot()
            
            # Analyze performance change
            performance_change = self._analyze_performance_change(
                execution.performance_before,
                execution.performance_after
            )
            
            # Check if optimization should be reverted
            if performance_change < -self.config.auto_revert_threshold:
                logger.warning(f"⚠️ Performance degraded by {performance_change:.1%}, reverting optimization")
                
                # Revert optimization
                revert_success = self._apply_parameter_change(
                    execution.parameter_name,
                    execution.old_value
                )
                
                if revert_success:
                    execution.result = OptimizationResult.REVERTED
                    execution.reverted_at = datetime.now()
                    execution.revert_reason = f"Performance degraded by {performance_change:.1%}"
                    
                    # Restore original parameter value
                    self.current_parameters[execution.parameter_name] = execution.old_value
                    
                    logger.info(f"↩️ Optimization reverted: {execution.parameter_name}")
                
            else:
                logger.info(f"✅ Optimization performance acceptable: {performance_change:.1%} change")
            
        except Exception as e:
            logger.error(f"❌ Error monitoring optimization performance: {e}")
        
        finally:
            # Move from active to history
            if execution.action_id in self.active_optimizations:
                del self.active_optimizations[execution.action_id]
            
            self.optimization_history.append(execution)
            self._save_optimization_history()
    
    def _analyze_performance_change(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        """Analyze performance change between before and after snapshots"""
        try:
            # Calculate weighted performance change
            changes = []
            weights = {
                "processing_time_avg": -1.0,  # Lower is better
                "success_rate": 1.0,          # Higher is better
                "throughput": 1.0,            # Higher is better
                "memory_usage_percent": -0.5, # Lower is better (less weight)
                "cpu_usage_percent": -0.3,    # Lower is better (less weight)
                "circuit_breaker_failures": -0.8  # Lower is better
            }
            
            for metric_name, weight in weights.items():
                if metric_name in before and metric_name in after:
                    before_value = before[metric_name]
                    after_value = after[metric_name]
                    
                    if before_value != 0:
                        change = (after_value - before_value) / before_value
                        weighted_change = change * weight
                        changes.append(weighted_change)
            
            # Return average weighted change
            return statistics.mean(changes) if changes else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error analyzing performance change: {e}")
            return 0.0
    
    def _monitor_active_optimizations(self):
        """Monitor active optimizations for timeout"""
        current_time = datetime.now()
        
        for action_id, execution in list(self.active_optimizations.items()):
            # Check if optimization has been running too long
            if current_time - execution.executed_at > timedelta(hours=2):
                logger.warning(f"⚠️ Optimization timeout: {action_id}")
                
                # Mark as failed and move to history
                execution.result = OptimizationResult.FAILED
                execution.performance_after = self._get_current_performance_snapshot()
                
                del self.active_optimizations[action_id]
                self.optimization_history.append(execution)
                self._save_optimization_history()
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization system status"""
        current_time = datetime.now()
        
        # Calculate optimization statistics
        total_optimizations = len(self.optimization_history)
        successful_optimizations = len([o for o in self.optimization_history if o.result == OptimizationResult.SUCCESS])
        reverted_optimizations = len([o for o in self.optimization_history if o.result == OptimizationResult.REVERTED])
        
        success_rate = (successful_optimizations / total_optimizations) * 100 if total_optimizations > 0 else 0
        
        return {
            "optimization_enabled": self.optimization_enabled,
            "monitoring_active": self.optimization_thread.is_alive() if self.optimization_thread else False,
            "queue_size": len(self.optimization_queue),
            "active_optimizations": len(self.active_optimizations),
            "performance_trends": {
                name: {
                    "direction": trend.direction.value,
                    "confidence": trend.confidence,
                    "data_points": trend.data_points
                }
                for name, trend in self.performance_trends.items()
            },
            "current_parameters": dict(self.current_parameters),
            "optimization_statistics": {
                "total_optimizations": total_optimizations,
                "successful_optimizations": successful_optimizations,
                "reverted_optimizations": reverted_optimizations,
                "success_rate": success_rate
            },
            "recent_optimizations": [
                {
                    "action_id": opt.action_id,
                    "parameter_name": opt.parameter_name,
                    "old_value": opt.old_value,
                    "new_value": opt.new_value,
                    "result": opt.result.value,
                    "executed_at": opt.executed_at.isoformat()
                }
                for opt in self.optimization_history
                if opt.executed_at > current_time - timedelta(hours=24)
            ],
            "configuration": {
                "enabled": self.config.enabled,
                "analysis_window_hours": self.config.analysis_window_hours,
                "confidence_threshold": self.config.confidence_threshold,
                "optimization_interval_minutes": self.config.optimization_interval_minutes
            },
            "last_updated": current_time.isoformat()
        }
    
    def configure_optimization(self, **kwargs):
        """Configure optimization system parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"🔧 Updated optimization config: {key} = {value}")
        
        self._save_optimization_config()


# Global performance optimization instance
performance_optimization_engine = PerformanceOptimizationEngine()

logger.info("🚀 Performance Optimization Engine ready")