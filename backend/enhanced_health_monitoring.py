#!/usr/bin/env python3
"""
Enhanced Health Monitoring for Multi-Format System
==================================================

Integrates multi-format upload system with existing health monitoring infrastructure.
Provides comprehensive monitoring for file upload, processing, and system health.

Features:
- Multi-format upload metrics
- Real-time performance monitoring
- File type-specific health tracking
- Ragie service integration monitoring
- WebSocket connection health
- System resource monitoring
- Error rate and success rate tracking

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
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import threading

# Import existing health monitoring
try:
    from health_monitoring_system import (
        HealthStatus,
        AlertSeverity,
        MetricType,
        HealthMetric,
        HealthAlert,
        HealthThreshold
    )
    HEALTH_MONITORING_AVAILABLE = True
except ImportError:
    HEALTH_MONITORING_AVAILABLE = False
    
    # Define fallback enums and classes
    class HealthStatus(Enum):
        HEALTHY = "healthy"
        WARNING = "warning"
        CRITICAL = "critical"
        DEGRADED = "degraded"
        FAILURE = "failure"
    
    class AlertSeverity(Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"
    
    class MetricType(Enum):
        PROCESSING_TIME = "processing_time"
        SUCCESS_RATE = "success_rate"
        ERROR_RATE = "error_rate"
    
    @dataclass
    class HealthMetric:
        name: str
        value: float
        timestamp: datetime
        metric_type: MetricType
        unit: str = ""
        context: Dict[str, Any] = field(default_factory=dict)
    
    @dataclass
    class HealthAlert:
        alert_id: str
        severity: AlertSeverity
        message: str
        metric_name: str
        threshold_value: float
        actual_value: float
        timestamp: datetime
        context: Dict[str, Any] = field(default_factory=dict)
        resolved: bool = False
        resolution_time: Optional[datetime] = None
    
    @dataclass
    class HealthThreshold:
        metric_name: str
        warning_threshold: float

# Import our enhanced services
from services.enhanced_file_validation import enhanced_validation_service
from services.enhanced_qsr_ragie_service import enhanced_qsr_ragie_service
from enhanced_websocket_progress import websocket_manager
from main import simple_progress_store

logger = logging.getLogger(__name__)

@dataclass
class MultiFormatHealthMetrics:
    """Health metrics for multi-format system"""
    upload_success_rate: float
    processing_success_rate: float
    average_processing_time: float
    file_type_distribution: Dict[str, int]
    active_uploads: int
    active_websocket_connections: int
    ragie_service_health: str
    validation_service_health: str
    system_resource_usage: Dict[str, float]
    error_rate_last_hour: float
    timestamp: datetime

@dataclass
class FileTypeMetrics:
    """Metrics for specific file types"""
    file_type: str
    total_uploads: int
    successful_uploads: int
    failed_uploads: int
    average_processing_time: float
    average_file_size: float
    error_rate: float
    last_updated: datetime

class EnhancedHealthMonitor:
    """
    Enhanced health monitoring system for multi-format uploads
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history = deque(maxlen=1000)  # Store last 1000 metrics
        self.file_type_metrics = {}  # Track metrics by file type
        self.alert_history = deque(maxlen=100)  # Store last 100 alerts
        self.monitoring_active = False
        self.monitoring_task = None
        self.lock = threading.Lock()
        
        # Health thresholds
        self.thresholds = {
            "upload_success_rate": 0.95,  # 95% success rate
            "processing_success_rate": 0.90,  # 90% processing success
            "average_processing_time": 60.0,  # 60 seconds max
            "error_rate_last_hour": 0.05,  # 5% error rate max
            "memory_usage": 0.85,  # 85% memory usage max
            "active_uploads": 50,  # 50 concurrent uploads max
            "websocket_connections": 100,  # 100 WebSocket connections max
        }
    
    def start_monitoring(self):
        """Start health monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("✅ Enhanced health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
            self.logger.info("🛑 Enhanced health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.monitoring_active:
                # Collect metrics
                metrics = await self._collect_metrics()
                
                # Store metrics
                with self.lock:
                    self.metrics_history.append(metrics)
                
                # Check thresholds and generate alerts
                await self._check_thresholds(metrics)
                
                # Update file type metrics
                await self._update_file_type_metrics()
                
                # Log health summary
                self._log_health_summary(metrics)
                
                # Wait before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds
                
        except asyncio.CancelledError:
            self.logger.info("Health monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Health monitoring error: {e}")
    
    async def _collect_metrics(self) -> MultiFormatHealthMetrics:
        """Collect comprehensive system metrics"""
        try:
            # Upload metrics
            upload_success_rate = self._calculate_upload_success_rate()
            processing_success_rate = self._calculate_processing_success_rate()
            average_processing_time = self._calculate_average_processing_time()
            
            # File type distribution
            file_type_distribution = self._get_file_type_distribution()
            
            # Active process counts
            active_uploads = len(simple_progress_store)
            active_websocket_connections = len(websocket_manager.active_connections)
            
            # Service health
            ragie_service_health = "healthy" if enhanced_qsr_ragie_service.is_available() else "degraded"
            validation_service_health = "healthy" if enhanced_validation_service else "degraded"
            
            # System resources
            system_resource_usage = self._get_system_resource_usage()
            
            # Error rate
            error_rate_last_hour = self._calculate_error_rate_last_hour()
            
            return MultiFormatHealthMetrics(
                upload_success_rate=upload_success_rate,
                processing_success_rate=processing_success_rate,
                average_processing_time=average_processing_time,
                file_type_distribution=file_type_distribution,
                active_uploads=active_uploads,
                active_websocket_connections=active_websocket_connections,
                ragie_service_health=ragie_service_health,
                validation_service_health=validation_service_health,
                system_resource_usage=system_resource_usage,
                error_rate_last_hour=error_rate_last_hour,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Metric collection failed: {e}")
            return self._get_default_metrics()
    
    def _calculate_upload_success_rate(self) -> float:
        """Calculate upload success rate"""
        if not simple_progress_store:
            return 1.0
        
        successful = 0
        failed = 0
        
        for process_data in simple_progress_store.values():
            status = process_data.get("status", "unknown")
            if status == "completed":
                successful += 1
            elif status == "failed":
                failed += 1
        
        total = successful + failed
        return successful / total if total > 0 else 1.0
    
    def _calculate_processing_success_rate(self) -> float:
        """Calculate processing success rate"""
        # Get Ragie processing status if available
        if enhanced_qsr_ragie_service.is_available():
            try:
                all_statuses = enhanced_qsr_ragie_service.get_all_processing_statuses()
                if not all_statuses:
                    return 1.0
                
                completed = sum(1 for s in all_statuses.values() if s.status == "completed")
                failed = sum(1 for s in all_statuses.values() if s.status == "failed")
                total = completed + failed
                
                return completed / total if total > 0 else 1.0
            except:
                pass
        
        # Fallback to local processing
        return self._calculate_upload_success_rate()
    
    def _calculate_average_processing_time(self) -> float:
        """Calculate average processing time"""
        # Estimate based on recent metrics
        if len(self.metrics_history) < 2:
            return 30.0  # Default estimate
        
        # Calculate from recent history
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 metrics
        times = [m.average_processing_time for m in recent_metrics if m.average_processing_time > 0]
        
        return sum(times) / len(times) if times else 30.0
    
    def _get_file_type_distribution(self) -> Dict[str, int]:
        """Get file type distribution"""
        distribution = {}
        
        for process_data in simple_progress_store.values():
            file_type = process_data.get("file_type", "unknown")
            distribution[file_type] = distribution.get(file_type, 0) + 1
        
        return distribution
    
    def _get_system_resource_usage(self) -> Dict[str, float]:
        """Get system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O (if available)
            try:
                net_io = psutil.net_io_counters()
                network_bytes_sent = net_io.bytes_sent
                network_bytes_recv = net_io.bytes_recv
            except:
                network_bytes_sent = 0
                network_bytes_recv = 0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network_bytes_sent": network_bytes_sent,
                "network_bytes_recv": network_bytes_recv
            }
            
        except Exception as e:
            self.logger.error(f"Resource usage collection failed: {e}")
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": 0.0,
                "network_bytes_sent": 0,
                "network_bytes_recv": 0
            }
    
    def _calculate_error_rate_last_hour(self) -> float:
        """Calculate error rate in the last hour"""
        if not self.metrics_history:
            return 0.0
        
        # Get metrics from last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= one_hour_ago]
        
        if not recent_metrics:
            return 0.0
        
        # Calculate average error rate
        error_rates = [1.0 - m.upload_success_rate for m in recent_metrics]
        return sum(error_rates) / len(error_rates)
    
    async def _check_thresholds(self, metrics: MultiFormatHealthMetrics):
        """Check thresholds and generate alerts"""
        alerts = []
        
        # Check upload success rate
        if metrics.upload_success_rate < self.thresholds["upload_success_rate"]:
            alerts.append(self._create_alert(
                "upload_success_rate",
                AlertSeverity.WARNING,
                f"Upload success rate ({metrics.upload_success_rate:.2%}) below threshold ({self.thresholds['upload_success_rate']:.2%})",
                self.thresholds["upload_success_rate"],
                metrics.upload_success_rate
            ))
        
        # Check processing success rate
        if metrics.processing_success_rate < self.thresholds["processing_success_rate"]:
            alerts.append(self._create_alert(
                "processing_success_rate",
                AlertSeverity.WARNING,
                f"Processing success rate ({metrics.processing_success_rate:.2%}) below threshold ({self.thresholds['processing_success_rate']:.2%})",
                self.thresholds["processing_success_rate"],
                metrics.processing_success_rate
            ))
        
        # Check average processing time
        if metrics.average_processing_time > self.thresholds["average_processing_time"]:
            alerts.append(self._create_alert(
                "average_processing_time",
                AlertSeverity.WARNING,
                f"Average processing time ({metrics.average_processing_time:.1f}s) above threshold ({self.thresholds['average_processing_time']:.1f}s)",
                self.thresholds["average_processing_time"],
                metrics.average_processing_time
            ))
        
        # Check error rate
        if metrics.error_rate_last_hour > self.thresholds["error_rate_last_hour"]:
            alerts.append(self._create_alert(
                "error_rate_last_hour",
                AlertSeverity.ERROR,
                f"Error rate ({metrics.error_rate_last_hour:.2%}) above threshold ({self.thresholds['error_rate_last_hour']:.2%})",
                self.thresholds["error_rate_last_hour"],
                metrics.error_rate_last_hour
            ))
        
        # Check memory usage
        memory_usage = metrics.system_resource_usage.get("memory_percent", 0) / 100
        if memory_usage > self.thresholds["memory_usage"]:
            alerts.append(self._create_alert(
                "memory_usage",
                AlertSeverity.CRITICAL,
                f"Memory usage ({memory_usage:.1%}) above threshold ({self.thresholds['memory_usage']:.1%})",
                self.thresholds["memory_usage"],
                memory_usage
            ))
        
        # Check active uploads
        if metrics.active_uploads > self.thresholds["active_uploads"]:
            alerts.append(self._create_alert(
                "active_uploads",
                AlertSeverity.WARNING,
                f"Active uploads ({metrics.active_uploads}) above threshold ({self.thresholds['active_uploads']})",
                self.thresholds["active_uploads"],
                metrics.active_uploads
            ))
        
        # Check WebSocket connections
        if metrics.active_websocket_connections > self.thresholds["websocket_connections"]:
            alerts.append(self._create_alert(
                "websocket_connections",
                AlertSeverity.WARNING,
                f"WebSocket connections ({metrics.active_websocket_connections}) above threshold ({self.thresholds['websocket_connections']})",
                self.thresholds["websocket_connections"],
                metrics.active_websocket_connections
            ))
        
        # Store alerts
        with self.lock:
            self.alert_history.extend(alerts)
        
        # Log alerts
        for alert in alerts:
            self.logger.warning(f"🚨 ALERT: {alert.message}")
    
    def _create_alert(self, metric_name: str, severity: AlertSeverity, message: str, threshold: float, actual: float) -> HealthAlert:
        """Create health alert"""
        return HealthAlert(
            alert_id=f"alert_{int(time.time())}_{metric_name}",
            severity=severity,
            message=message,
            metric_name=metric_name,
            threshold_value=threshold,
            actual_value=actual,
            timestamp=datetime.now()
        )
    
    async def _update_file_type_metrics(self):
        """Update file type specific metrics"""
        file_type_counts = {}
        
        # Count by file type
        for process_data in simple_progress_store.values():
            file_type = process_data.get("file_type", "unknown")
            status = process_data.get("status", "unknown")
            
            if file_type not in file_type_counts:
                file_type_counts[file_type] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0
                }
            
            file_type_counts[file_type]["total"] += 1
            if status == "completed":
                file_type_counts[file_type]["successful"] += 1
            elif status == "failed":
                file_type_counts[file_type]["failed"] += 1
        
        # Update metrics
        for file_type, counts in file_type_counts.items():
            total = counts["total"]
            successful = counts["successful"]
            failed = counts["failed"]
            
            error_rate = failed / total if total > 0 else 0.0
            
            self.file_type_metrics[file_type] = FileTypeMetrics(
                file_type=file_type,
                total_uploads=total,
                successful_uploads=successful,
                failed_uploads=failed,
                average_processing_time=30.0,  # Placeholder
                average_file_size=1024000,  # Placeholder
                error_rate=error_rate,
                last_updated=datetime.now()
            )
    
    def _log_health_summary(self, metrics: MultiFormatHealthMetrics):
        """Log health summary"""
        self.logger.info(f"📊 Health Summary: "
                        f"Uploads: {metrics.active_uploads}, "
                        f"Success: {metrics.upload_success_rate:.1%}, "
                        f"Processing: {metrics.processing_success_rate:.1%}, "
                        f"AvgTime: {metrics.average_processing_time:.1f}s, "
                        f"WebSockets: {metrics.active_websocket_connections}, "
                        f"Memory: {metrics.system_resource_usage.get('memory_percent', 0):.1f}%")
    
    def _get_default_metrics(self) -> MultiFormatHealthMetrics:
        """Get default metrics when collection fails"""
        return MultiFormatHealthMetrics(
            upload_success_rate=0.0,
            processing_success_rate=0.0,
            average_processing_time=0.0,
            file_type_distribution={},
            active_uploads=0,
            active_websocket_connections=0,
            ragie_service_health="unknown",
            validation_service_health="unknown",
            system_resource_usage={},
            error_rate_last_hour=0.0,
            timestamp=datetime.now()
        )
    
    def get_current_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        if not self.metrics_history:
            return {
                "status": "unknown",
                "message": "No metrics available",
                "timestamp": datetime.now().isoformat()
            }
        
        latest_metrics = self.metrics_history[-1]
        recent_alerts = [a for a in self.alert_history if not a.resolved]
        
        # Determine overall status
        if recent_alerts:
            critical_alerts = [a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]
            error_alerts = [a for a in recent_alerts if a.severity == AlertSeverity.ERROR]
            
            if critical_alerts:
                status = "critical"
            elif error_alerts:
                status = "error"
            else:
                status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "message": f"System health: {status}",
            "timestamp": latest_metrics.timestamp.isoformat(),
            "metrics": {
                "upload_success_rate": latest_metrics.upload_success_rate,
                "processing_success_rate": latest_metrics.processing_success_rate,
                "average_processing_time": latest_metrics.average_processing_time,
                "active_uploads": latest_metrics.active_uploads,
                "active_websocket_connections": latest_metrics.active_websocket_connections,
                "error_rate_last_hour": latest_metrics.error_rate_last_hour,
                "system_resource_usage": latest_metrics.system_resource_usage
            },
            "services": {
                "ragie_service": latest_metrics.ragie_service_health,
                "validation_service": latest_metrics.validation_service_health
            },
            "recent_alerts": len(recent_alerts),
            "file_type_distribution": latest_metrics.file_type_distribution,
            "file_type_metrics": {
                file_type: {
                    "total_uploads": metrics.total_uploads,
                    "success_rate": (metrics.successful_uploads / metrics.total_uploads) if metrics.total_uploads > 0 else 0.0,
                    "error_rate": metrics.error_rate
                }
                for file_type, metrics in self.file_type_metrics.items()
            }
        }
    
    def get_metrics_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get metrics history"""
        with self.lock:
            recent_metrics = list(self.metrics_history)[-limit:]
        
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "upload_success_rate": m.upload_success_rate,
                "processing_success_rate": m.processing_success_rate,
                "average_processing_time": m.average_processing_time,
                "active_uploads": m.active_uploads,
                "active_websocket_connections": m.active_websocket_connections,
                "error_rate_last_hour": m.error_rate_last_hour,
                "system_resource_usage": m.system_resource_usage
            }
            for m in recent_metrics
        ]
    
    def get_alert_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get alert history"""
        with self.lock:
            recent_alerts = list(self.alert_history)[-limit:]
        
        return [
            {
                "alert_id": a.alert_id,
                "severity": a.severity.value,
                "message": a.message,
                "metric_name": a.metric_name,
                "threshold_value": a.threshold_value,
                "actual_value": a.actual_value,
                "timestamp": a.timestamp.isoformat(),
                "resolved": a.resolved
            }
            for a in recent_alerts
        ]

# Global health monitor instance
enhanced_health_monitor = EnhancedHealthMonitor()

# Helper functions for integration
def start_health_monitoring():
    """Start health monitoring"""
    enhanced_health_monitor.start_monitoring()

def stop_health_monitoring():
    """Stop health monitoring"""
    enhanced_health_monitor.stop_monitoring()

def get_health_status():
    """Get current health status"""
    return enhanced_health_monitor.get_current_health_status()

def get_metrics_history(limit: int = 50):
    """Get metrics history"""
    return enhanced_health_monitor.get_metrics_history(limit)

def get_alert_history(limit: int = 20):
    """Get alert history"""
    return enhanced_health_monitor.get_alert_history(limit)

def is_health_monitoring_active():
    """Check if health monitoring is active"""
    return enhanced_health_monitor.monitoring_active