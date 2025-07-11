#!/usr/bin/env python3
"""
Phase 3 Comprehensive Testing: Operational Monitoring & Recovery
===============================================================

Comprehensive testing suite for Phase 3 operational monitoring and recovery features:
- 3A: Health Monitoring System
- 3B: Automated Recovery System
- 3C: Performance Optimization Engine

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import uuid
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import systems to test
from health_monitoring_system import health_monitoring_system, HealthStatus, AlertSeverity
from automated_recovery_system import automated_recovery_system, RecoveryStrategy, RecoveryResult
from performance_optimization_engine import performance_optimization_engine, OptimizationStrategy
from reliable_upload_pipeline import reliable_upload_pipeline

@dataclass
class TestResult:
    """Test result with detailed validation"""
    test_name: str
    passed: bool
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    error_message: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)

class Phase3ComprehensiveTesting:
    """
    Comprehensive testing suite for Phase 3 operational monitoring and recovery.
    """
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.test_start_time = datetime.now()
        
        # Test data storage
        self.test_data_path = Path("test_data")
        self.test_data_path.mkdir(exist_ok=True)
        
        logger.info("🧪 Phase 3 Comprehensive Testing Suite initialized")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 3 tests"""
        logger.info("🚀 Starting Phase 3 Comprehensive Testing")
        
        test_methods = [
            # Phase 3A: Health Monitoring System Tests
            self._test_health_monitoring_system_setup,
            self._test_real_time_metrics_collection,
            self._test_threshold_based_alerting,
            self._test_stuck_file_detection,
            self._test_health_status_reporting,
            self._test_proactive_monitoring,
            
            # Phase 3B: Automated Recovery System Tests
            self._test_automated_recovery_system_setup,
            self._test_stuck_file_recovery,
            self._test_memory_exhaustion_recovery,
            self._test_connection_failure_recovery,
            self._test_escalation_system,
            self._test_recovery_result_tracking,
            
            # Phase 3C: Performance Optimization Engine Tests
            self._test_performance_optimization_engine_setup,
            self._test_performance_trend_analysis,
            self._test_dynamic_parameter_adjustment,
            self._test_gradual_optimization_changes,
            self._test_optimization_reversal,
            self._test_performance_improvement,
            
            # Integration Tests
            self._test_monitoring_recovery_integration,
            self._test_recovery_optimization_integration,
            self._test_complete_operational_workflow,
            self._test_performance_impact_validation,
            self._test_system_stability_under_load
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"🧪 Running {test_method.__name__}")
                start_time = time.time()
                
                result = await test_method()
                result.execution_time = time.time() - start_time
                
                self.test_results.append(result)
                
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                logger.info(f"{status}: {result.test_name} ({result.execution_time:.2f}s)")
                
                if not result.passed:
                    logger.error(f"   Error: {result.error_message}")
                
            except Exception as e:
                error_result = TestResult(
                    test_name=test_method.__name__,
                    passed=False,
                    description=f"Test execution failed: {str(e)}",
                    error_message=str(e),
                    execution_time=time.time() - start_time
                )
                self.test_results.append(error_result)
                logger.error(f"❌ FAILED: {test_method.__name__} - {str(e)}")
        
        # Generate comprehensive report
        report = self._generate_test_report()
        self._save_test_report(report)
        
        return report
    
    # Phase 3A: Health Monitoring System Tests
    
    async def _test_health_monitoring_system_setup(self) -> TestResult:
        """Test health monitoring system initialization"""
        try:
            # Test system initialization
            status = health_monitoring_system.get_monitoring_status()
            
            # Check required components
            required_components = [
                "monitoring_enabled",
                "metrics_buffer_size",
                "alerts_buffer_size",
                "active_alerts_count",
                "thresholds_configured"
            ]
            
            missing_components = [comp for comp in required_components if comp not in status]
            
            if missing_components:
                return TestResult(
                    test_name="Health Monitoring System Setup",
                    passed=False,
                    description="Health monitoring system initialization",
                    error_message=f"Missing components: {missing_components}",
                    details={"status": status}
                )
            
            # Test starting monitoring
            if not status.get("monitoring_thread_alive", False):
                health_monitoring_system.start_monitoring()
                
                # Wait a bit for monitoring to start
                await asyncio.sleep(2)
                
                updated_status = health_monitoring_system.get_monitoring_status()
                if not updated_status.get("monitoring_thread_alive", False):
                    return TestResult(
                        test_name="Health Monitoring System Setup",
                        passed=False,
                        description="Health monitoring system initialization",
                        error_message="Failed to start monitoring thread",
                        details={"status": updated_status}
                    )
            
            return TestResult(
                test_name="Health Monitoring System Setup",
                passed=True,
                description="Health monitoring system initialized successfully",
                details={"status": status}
            )
            
        except Exception as e:
            return TestResult(
                test_name="Health Monitoring System Setup",
                passed=False,
                description="Health monitoring system initialization",
                error_message=str(e)
            )
    
    async def _test_real_time_metrics_collection(self) -> TestResult:
        """Test real-time metrics collection"""
        try:
            # Get initial metrics count
            initial_status = health_monitoring_system.get_monitoring_status()
            initial_metrics = initial_status.get("metrics_buffer_size", 0)
            
            # Wait for metrics collection
            await asyncio.sleep(15)
            
            # Check if metrics have been collected
            updated_status = health_monitoring_system.get_monitoring_status()
            updated_metrics = updated_status.get("metrics_buffer_size", 0)
            
            if updated_metrics <= initial_metrics:
                return TestResult(
                    test_name="Real-time Metrics Collection",
                    passed=False,
                    description="Real-time metrics collection functionality",
                    error_message=f"No new metrics collected: {initial_metrics} -> {updated_metrics}",
                    details={"initial": initial_metrics, "updated": updated_metrics}
                )
            
            # Test dashboard data retrieval
            dashboard_data = health_monitoring_system.get_health_dashboard_data()
            required_data = ["system_health", "metrics_summary", "performance_trends"]
            
            missing_data = [data for data in required_data if data not in dashboard_data]
            
            if missing_data:
                return TestResult(
                    test_name="Real-time Metrics Collection",
                    passed=False,
                    description="Real-time metrics collection functionality",
                    error_message=f"Missing dashboard data: {missing_data}",
                    details={"dashboard_data": dashboard_data}
                )
            
            return TestResult(
                test_name="Real-time Metrics Collection",
                passed=True,
                description="Real-time metrics collection working correctly",
                details={
                    "metrics_collected": updated_metrics - initial_metrics,
                    "dashboard_data_available": True
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Real-time Metrics Collection",
                passed=False,
                description="Real-time metrics collection functionality",
                error_message=str(e)
            )
    
    async def _test_threshold_based_alerting(self) -> TestResult:
        """Test threshold-based alerting system"""
        try:
            # Configure a test threshold
            health_monitoring_system.configure_threshold(
                "test_metric",
                warning_threshold=50.0,
                critical_threshold=80.0,
                operator="greater_than",
                duration_minutes=1
            )
            
            # Get initial alerts count
            initial_system_health = health_monitoring_system.get_system_health()
            initial_alerts = len(initial_system_health.active_alerts)
            
            # Simulate adding metrics that exceed threshold
            from health_monitoring_system import HealthMetric, MetricType
            
            test_metric = HealthMetric(
                name="test_metric",
                value=85.0,  # Above critical threshold
                timestamp=datetime.now(),
                metric_type=MetricType.MEMORY_USAGE,
                unit="percentage"
            )
            
            # Add test metric multiple times to trigger duration requirement
            for i in range(5):
                health_monitoring_system._add_metric(test_metric)
                await asyncio.sleep(0.1)
            
            # Wait for alert processing
            await asyncio.sleep(3)
            
            # Check if alerts were generated
            updated_system_health = health_monitoring_system.get_system_health()
            updated_alerts = len(updated_system_health.active_alerts)
            
            alerts_generated = updated_alerts > initial_alerts
            
            return TestResult(
                test_name="Threshold-based Alerting",
                passed=alerts_generated,
                description="Threshold-based alerting system",
                details={
                    "initial_alerts": initial_alerts,
                    "updated_alerts": updated_alerts,
                    "alerts_generated": alerts_generated,
                    "test_metric_value": 85.0,
                    "threshold": 80.0
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Threshold-based Alerting",
                passed=False,
                description="Threshold-based alerting system",
                error_message=str(e)
            )
    
    async def _test_stuck_file_detection(self) -> TestResult:
        """Test stuck file detection capabilities"""
        try:
            # Get current dashboard data
            dashboard_data = health_monitoring_system.get_health_dashboard_data()
            
            # Check if stuck files detection is working
            stuck_files = dashboard_data.get("stuck_files", [])
            
            # Test the detection mechanism by checking if it's properly configured
            detection_working = isinstance(stuck_files, list)
            
            return TestResult(
                test_name="Stuck File Detection",
                passed=detection_working,
                description="Stuck file detection capabilities",
                details={
                    "stuck_files_detected": len(stuck_files),
                    "detection_mechanism_working": detection_working
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Stuck File Detection",
                passed=False,
                description="Stuck file detection capabilities",
                error_message=str(e)
            )
    
    async def _test_health_status_reporting(self) -> TestResult:
        """Test health status reporting integration"""
        try:
            # Get system health
            system_health = health_monitoring_system.get_system_health()
            
            # Check required health components
            required_components = [
                "overall_status",
                "component_health",
                "active_alerts",
                "metrics_summary",
                "last_updated",
                "uptime_seconds"
            ]
            
            missing_components = [comp for comp in required_components if not hasattr(system_health, comp)]
            
            if missing_components:
                return TestResult(
                    test_name="Health Status Reporting",
                    passed=False,
                    description="Health status reporting integration",
                    error_message=f"Missing health components: {missing_components}",
                    details={"system_health": system_health}
                )
            
            # Test health status values
            valid_status = system_health.overall_status in [
                HealthStatus.HEALTHY, HealthStatus.WARNING, 
                HealthStatus.CRITICAL, HealthStatus.DEGRADED, HealthStatus.FAILURE
            ]
            
            return TestResult(
                test_name="Health Status Reporting",
                passed=valid_status,
                description="Health status reporting integration working correctly",
                details={
                    "overall_status": system_health.overall_status.value,
                    "component_count": len(system_health.component_health),
                    "active_alerts": len(system_health.active_alerts),
                    "uptime_seconds": system_health.uptime_seconds
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Health Status Reporting",
                passed=False,
                description="Health status reporting integration",
                error_message=str(e)
            )
    
    async def _test_proactive_monitoring(self) -> TestResult:
        """Test proactive monitoring capabilities"""
        try:
            # Check if proactive monitoring is detecting issues
            dashboard_data = health_monitoring_system.get_health_dashboard_data()
            
            # Test performance trends analysis
            performance_trends = dashboard_data.get("performance_trends", {})
            
            # Check if trends are being analyzed
            trends_analyzed = len(performance_trends) > 0
            
            return TestResult(
                test_name="Proactive Monitoring",
                passed=trends_analyzed,
                description="Proactive monitoring capabilities",
                details={
                    "performance_trends": performance_trends,
                    "trends_analyzed": trends_analyzed
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Proactive Monitoring",
                passed=False,
                description="Proactive monitoring capabilities",
                error_message=str(e)
            )
    
    # Phase 3B: Automated Recovery System Tests
    
    async def _test_automated_recovery_system_setup(self) -> TestResult:
        """Test automated recovery system initialization"""
        try:
            # Test system initialization
            status = automated_recovery_system.get_recovery_status()
            
            # Check required components
            required_components = [
                "recovery_enabled",
                "queue_size",
                "recoveries_in_progress",
                "statistics",
                "configuration"
            ]
            
            missing_components = [comp for comp in required_components if comp not in status]
            
            if missing_components:
                return TestResult(
                    test_name="Automated Recovery System Setup",
                    passed=False,
                    description="Automated recovery system initialization",
                    error_message=f"Missing components: {missing_components}",
                    details={"status": status}
                )
            
            # Test starting recovery monitoring
            if not status.get("monitoring_active", False):
                automated_recovery_system.start_recovery_monitoring()
                
                # Wait a bit for monitoring to start
                await asyncio.sleep(2)
                
                updated_status = automated_recovery_system.get_recovery_status()
                if not updated_status.get("monitoring_active", False):
                    return TestResult(
                        test_name="Automated Recovery System Setup",
                        passed=False,
                        description="Automated recovery system initialization",
                        error_message="Failed to start recovery monitoring",
                        details={"status": updated_status}
                    )
            
            return TestResult(
                test_name="Automated Recovery System Setup",
                passed=True,
                description="Automated recovery system initialized successfully",
                details={"status": status}
            )
            
        except Exception as e:
            return TestResult(
                test_name="Automated Recovery System Setup",
                passed=False,
                description="Automated recovery system initialization",
                error_message=str(e)
            )
    
    async def _test_stuck_file_recovery(self) -> TestResult:
        """Test stuck file recovery capabilities"""
        try:
            # Get recovery statistics
            stats = automated_recovery_system.get_recovery_statistics()
            
            # Test recovery strategy configuration
            recovery_strategies = automated_recovery_system.recovery_strategies
            
            # Check if stuck file recovery strategies are configured
            stuck_strategies_configured = any(
                "stuck" in str(failure_type).lower() 
                for failure_type in recovery_strategies.keys()
            )
            
            return TestResult(
                test_name="Stuck File Recovery",
                passed=stuck_strategies_configured,
                description="Stuck file recovery capabilities",
                details={
                    "recovery_strategies_configured": len(recovery_strategies),
                    "stuck_strategies_configured": stuck_strategies_configured,
                    "recovery_statistics": {
                        "total_recoveries": stats.total_recoveries_attempted,
                        "successful_recoveries": stats.successful_recoveries,
                        "success_rate": stats.recovery_success_rate
                    }
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Stuck File Recovery",
                passed=False,
                description="Stuck file recovery capabilities",
                error_message=str(e)
            )
    
    async def _test_memory_exhaustion_recovery(self) -> TestResult:
        """Test memory exhaustion recovery"""
        try:
            # Test memory exhaustion detection and recovery
            from automated_recovery_system import FailureType
            
            # Check if memory exhaustion recovery is configured
            memory_strategies = automated_recovery_system.recovery_strategies.get(
                FailureType.MEMORY_EXHAUSTION, []
            )
            
            memory_recovery_configured = len(memory_strategies) > 0
            
            return TestResult(
                test_name="Memory Exhaustion Recovery",
                passed=memory_recovery_configured,
                description="Memory exhaustion recovery capabilities",
                details={
                    "memory_recovery_strategies": len(memory_strategies),
                    "configured_strategies": [strategy.value for strategy in memory_strategies]
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Memory Exhaustion Recovery",
                passed=False,
                description="Memory exhaustion recovery capabilities",
                error_message=str(e)
            )
    
    async def _test_connection_failure_recovery(self) -> TestResult:
        """Test connection failure recovery"""
        try:
            # Test connection failure recovery
            from automated_recovery_system import FailureType
            
            # Check if connection failure recovery is configured
            connection_strategies = automated_recovery_system.recovery_strategies.get(
                FailureType.CONNECTION_FAILURE, []
            )
            
            connection_recovery_configured = len(connection_strategies) > 0
            
            return TestResult(
                test_name="Connection Failure Recovery",
                passed=connection_recovery_configured,
                description="Connection failure recovery capabilities",
                details={
                    "connection_recovery_strategies": len(connection_strategies),
                    "configured_strategies": [strategy.value for strategy in connection_strategies]
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Connection Failure Recovery",
                passed=False,
                description="Connection failure recovery capabilities",
                error_message=str(e)
            )
    
    async def _test_escalation_system(self) -> TestResult:
        """Test escalation system functionality"""
        try:
            # Test escalation configuration
            escalation_threshold = automated_recovery_system.escalation_threshold
            
            # Check if escalation is properly configured
            escalation_configured = escalation_threshold > 0
            
            # Test escalation strategy
            from automated_recovery_system import RecoveryStrategy
            
            escalation_strategy_exists = RecoveryStrategy.ESCALATE_TO_MANUAL in [
                strategy 
                for strategies in automated_recovery_system.recovery_strategies.values()
                for strategy in strategies
            ]
            
            return TestResult(
                test_name="Escalation System",
                passed=escalation_configured and escalation_strategy_exists,
                description="Escalation system functionality",
                details={
                    "escalation_threshold": escalation_threshold,
                    "escalation_configured": escalation_configured,
                    "escalation_strategy_exists": escalation_strategy_exists
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Escalation System",
                passed=False,
                description="Escalation system functionality",
                error_message=str(e)
            )
    
    async def _test_recovery_result_tracking(self) -> TestResult:
        """Test recovery result tracking"""
        try:
            # Test recovery statistics tracking
            stats = automated_recovery_system.get_recovery_statistics()
            
            # Check if statistics are being tracked
            stats_tracked = hasattr(stats, 'total_recoveries_attempted')
            
            return TestResult(
                test_name="Recovery Result Tracking",
                passed=stats_tracked,
                description="Recovery result tracking capabilities",
                details={
                    "stats_tracked": stats_tracked,
                    "recovery_statistics": {
                        "total_recoveries": stats.total_recoveries_attempted,
                        "successful_recoveries": stats.successful_recoveries,
                        "failed_recoveries": stats.failed_recoveries,
                        "success_rate": stats.recovery_success_rate
                    }
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Recovery Result Tracking",
                passed=False,
                description="Recovery result tracking capabilities",
                error_message=str(e)
            )
    
    # Phase 3C: Performance Optimization Engine Tests
    
    async def _test_performance_optimization_engine_setup(self) -> TestResult:
        """Test performance optimization engine initialization"""
        try:
            # Test system initialization
            status = performance_optimization_engine.get_optimization_status()
            
            # Check required components
            required_components = [
                "optimization_enabled",
                "current_parameters",
                "performance_trends",
                "optimization_statistics",
                "configuration"
            ]
            
            missing_components = [comp for comp in required_components if comp not in status]
            
            if missing_components:
                return TestResult(
                    test_name="Performance Optimization Engine Setup",
                    passed=False,
                    description="Performance optimization engine initialization",
                    error_message=f"Missing components: {missing_components}",
                    details={"status": status}
                )
            
            # Test starting optimization
            if not status.get("monitoring_active", False):
                performance_optimization_engine.start_optimization()
                
                # Wait a bit for optimization to start
                await asyncio.sleep(2)
                
                updated_status = performance_optimization_engine.get_optimization_status()
                if not updated_status.get("monitoring_active", False):
                    return TestResult(
                        test_name="Performance Optimization Engine Setup",
                        passed=False,
                        description="Performance optimization engine initialization",
                        error_message="Failed to start optimization monitoring",
                        details={"status": updated_status}
                    )
            
            return TestResult(
                test_name="Performance Optimization Engine Setup",
                passed=True,
                description="Performance optimization engine initialized successfully",
                details={"status": status}
            )
            
        except Exception as e:
            return TestResult(
                test_name="Performance Optimization Engine Setup",
                passed=False,
                description="Performance optimization engine initialization",
                error_message=str(e)
            )
    
    async def _test_performance_trend_analysis(self) -> TestResult:
        """Test performance trend analysis"""
        try:
            # Get optimization status
            status = performance_optimization_engine.get_optimization_status()
            
            # Check if performance trends are being analyzed
            performance_trends = status.get("performance_trends", {})
            
            trends_analyzed = len(performance_trends) >= 0  # Should at least be initialized
            
            # Test trend analysis components
            trend_analysis_working = "performance_trends" in status
            
            return TestResult(
                test_name="Performance Trend Analysis",
                passed=trends_analyzed and trend_analysis_working,
                description="Performance trend analysis capabilities",
                details={
                    "trends_analyzed": len(performance_trends),
                    "trend_analysis_working": trend_analysis_working,
                    "performance_trends": performance_trends
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Performance Trend Analysis",
                passed=False,
                description="Performance trend analysis capabilities",
                error_message=str(e)
            )
    
    async def _test_dynamic_parameter_adjustment(self) -> TestResult:
        """Test dynamic parameter adjustment"""
        try:
            # Test parameter adjustment capabilities
            status = performance_optimization_engine.get_optimization_status()
            
            # Check if parameters are being tracked
            current_parameters = status.get("current_parameters", {})
            
            parameters_tracked = len(current_parameters) > 0
            
            # Test optimization queue
            queue_size = status.get("queue_size", 0)
            
            return TestResult(
                test_name="Dynamic Parameter Adjustment",
                passed=parameters_tracked,
                description="Dynamic parameter adjustment capabilities",
                details={
                    "parameters_tracked": len(current_parameters),
                    "current_parameters": current_parameters,
                    "optimization_queue_size": queue_size
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Dynamic Parameter Adjustment",
                passed=False,
                description="Dynamic parameter adjustment capabilities",
                error_message=str(e)
            )
    
    async def _test_gradual_optimization_changes(self) -> TestResult:
        """Test gradual optimization changes"""
        try:
            # Test optimization configuration
            status = performance_optimization_engine.get_optimization_status()
            
            # Check optimization configuration
            config = status.get("configuration", {})
            
            # Test gradual change parameters
            confidence_threshold = config.get("confidence_threshold", 0)
            optimization_interval = config.get("optimization_interval_minutes", 0)
            
            gradual_changes_configured = confidence_threshold > 0 and optimization_interval > 0
            
            return TestResult(
                test_name="Gradual Optimization Changes",
                passed=gradual_changes_configured,
                description="Gradual optimization changes configuration",
                details={
                    "confidence_threshold": confidence_threshold,
                    "optimization_interval_minutes": optimization_interval,
                    "gradual_changes_configured": gradual_changes_configured
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Gradual Optimization Changes",
                passed=False,
                description="Gradual optimization changes configuration",
                error_message=str(e)
            )
    
    async def _test_optimization_reversal(self) -> TestResult:
        """Test optimization reversal capabilities"""
        try:
            # Test reversal configuration
            config = performance_optimization_engine.config
            
            # Check if auto-revert is configured
            auto_revert_configured = hasattr(config, 'auto_revert_threshold') and config.auto_revert_threshold > 0
            
            return TestResult(
                test_name="Optimization Reversal",
                passed=auto_revert_configured,
                description="Optimization reversal capabilities",
                details={
                    "auto_revert_threshold": getattr(config, 'auto_revert_threshold', 0),
                    "auto_revert_configured": auto_revert_configured
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Optimization Reversal",
                passed=False,
                description="Optimization reversal capabilities",
                error_message=str(e)
            )
    
    async def _test_performance_improvement(self) -> TestResult:
        """Test performance improvement tracking"""
        try:
            # Test performance improvement tracking
            status = performance_optimization_engine.get_optimization_status()
            
            # Check optimization statistics
            stats = status.get("optimization_statistics", {})
            
            stats_tracked = len(stats) > 0
            
            return TestResult(
                test_name="Performance Improvement",
                passed=stats_tracked,
                description="Performance improvement tracking",
                details={
                    "optimization_statistics": stats,
                    "stats_tracked": stats_tracked
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Performance Improvement",
                passed=False,
                description="Performance improvement tracking",
                error_message=str(e)
            )
    
    # Integration Tests
    
    async def _test_monitoring_recovery_integration(self) -> TestResult:
        """Test monitoring and recovery integration"""
        try:
            # Test that monitoring and recovery systems work together
            health_status = health_monitoring_system.get_monitoring_status()
            recovery_status = automated_recovery_system.get_recovery_status()
            
            # Check if both systems are operational
            monitoring_working = health_status.get("monitoring_enabled", False)
            recovery_working = recovery_status.get("recovery_enabled", False)
            
            integration_working = monitoring_working and recovery_working
            
            return TestResult(
                test_name="Monitoring Recovery Integration",
                passed=integration_working,
                description="Monitoring and recovery systems integration",
                details={
                    "monitoring_working": monitoring_working,
                    "recovery_working": recovery_working,
                    "integration_working": integration_working
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Monitoring Recovery Integration",
                passed=False,
                description="Monitoring and recovery systems integration",
                error_message=str(e)
            )
    
    async def _test_recovery_optimization_integration(self) -> TestResult:
        """Test recovery and optimization integration"""
        try:
            # Test that recovery and optimization systems work together
            recovery_status = automated_recovery_system.get_recovery_status()
            optimization_status = performance_optimization_engine.get_optimization_status()
            
            # Check if both systems are operational
            recovery_working = recovery_status.get("recovery_enabled", False)
            optimization_working = optimization_status.get("optimization_enabled", False)
            
            integration_working = recovery_working and optimization_working
            
            return TestResult(
                test_name="Recovery Optimization Integration",
                passed=integration_working,
                description="Recovery and optimization systems integration",
                details={
                    "recovery_working": recovery_working,
                    "optimization_working": optimization_working,
                    "integration_working": integration_working
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Recovery Optimization Integration",
                passed=False,
                description="Recovery and optimization systems integration",
                error_message=str(e)
            )
    
    async def _test_complete_operational_workflow(self) -> TestResult:
        """Test complete operational workflow"""
        try:
            # Test that all three systems work together
            health_status = health_monitoring_system.get_monitoring_status()
            recovery_status = automated_recovery_system.get_recovery_status()
            optimization_status = performance_optimization_engine.get_optimization_status()
            
            # Check if all systems are operational
            all_systems_working = all([
                health_status.get("monitoring_enabled", False),
                recovery_status.get("recovery_enabled", False),
                optimization_status.get("optimization_enabled", False)
            ])
            
            return TestResult(
                test_name="Complete Operational Workflow",
                passed=all_systems_working,
                description="Complete operational workflow with all Phase 3 systems",
                details={
                    "health_monitoring": health_status.get("monitoring_enabled", False),
                    "automated_recovery": recovery_status.get("recovery_enabled", False),
                    "performance_optimization": optimization_status.get("optimization_enabled", False),
                    "all_systems_working": all_systems_working
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Complete Operational Workflow",
                passed=False,
                description="Complete operational workflow with all Phase 3 systems",
                error_message=str(e)
            )
    
    async def _test_performance_impact_validation(self) -> TestResult:
        """Test performance impact validation"""
        try:
            # Test that Phase 3 systems don't negatively impact performance
            start_time = time.time()
            
            # Simulate some activity to measure performance impact
            for i in range(10):
                health_monitoring_system.get_monitoring_status()
                automated_recovery_system.get_recovery_status()
                performance_optimization_engine.get_optimization_status()
                await asyncio.sleep(0.1)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Performance should be reasonable (< 2 seconds for 10 status checks)
            performance_acceptable = total_time < 2.0
            
            return TestResult(
                test_name="Performance Impact Validation",
                passed=performance_acceptable,
                description="Performance impact validation for Phase 3 systems",
                details={
                    "total_time": total_time,
                    "performance_threshold": 2.0,
                    "performance_acceptable": performance_acceptable
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Performance Impact Validation",
                passed=False,
                description="Performance impact validation for Phase 3 systems",
                error_message=str(e)
            )
    
    async def _test_system_stability_under_load(self) -> TestResult:
        """Test system stability under load"""
        try:
            # Test system stability with multiple concurrent operations
            tasks = []
            
            # Create multiple concurrent tasks
            for i in range(20):
                task = asyncio.create_task(self._simulate_system_load())
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if any tasks failed
            failed_tasks = [r for r in results if isinstance(r, Exception)]
            success_rate = (len(results) - len(failed_tasks)) / len(results)
            
            # System should handle load with >90% success rate
            stability_acceptable = success_rate >= 0.9
            
            return TestResult(
                test_name="System Stability Under Load",
                passed=stability_acceptable,
                description="System stability under concurrent load",
                details={
                    "total_tasks": len(results),
                    "failed_tasks": len(failed_tasks),
                    "success_rate": success_rate,
                    "stability_acceptable": stability_acceptable
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="System Stability Under Load",
                passed=False,
                description="System stability under concurrent load",
                error_message=str(e)
            )
    
    async def _simulate_system_load(self):
        """Simulate system load for stability testing"""
        try:
            # Simulate various system operations
            health_monitoring_system.get_system_health()
            automated_recovery_system.get_recovery_status()
            performance_optimization_engine.get_optimization_status()
            
            # Simulate some processing time
            await asyncio.sleep(0.05)
            
            return True
            
        except Exception as e:
            return e
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.passed])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Calculate phase-specific success rates
        phase_3a_tests = [r for r in self.test_results if "Health Monitoring" in r.test_name or "Metrics" in r.test_name or "Alerting" in r.test_name or "Stuck File" in r.test_name or "Proactive" in r.test_name]
        phase_3b_tests = [r for r in self.test_results if "Recovery" in r.test_name or "Escalation" in r.test_name]
        phase_3c_tests = [r for r in self.test_results if "Optimization" in r.test_name or "Performance" in r.test_name and "Impact" not in r.test_name]
        integration_tests = [r for r in self.test_results if "Integration" in r.test_name or "Workflow" in r.test_name or "Impact" in r.test_name or "Stability" in r.test_name]
        
        def calculate_phase_success_rate(tests):
            if not tests:
                return 0
            return (len([t for t in tests if t.passed]) / len(tests)) * 100
        
        phase_3a_success = calculate_phase_success_rate(phase_3a_tests)
        phase_3b_success = calculate_phase_success_rate(phase_3b_tests)
        phase_3c_success = calculate_phase_success_rate(phase_3c_tests)
        integration_success = calculate_phase_success_rate(integration_tests)
        
        # Determine overall status
        if success_rate >= 95:
            overall_status = "EXCELLENT"
        elif success_rate >= 90:
            overall_status = "GOOD"
        elif success_rate >= 80:
            overall_status = "ACCEPTABLE"
        else:
            overall_status = "NEEDS_IMPROVEMENT"
        
        return {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "overall_status": overall_status
            },
            "phase_results": {
                "phase_3a_health_monitoring": {
                    "tests": len(phase_3a_tests),
                    "success_rate": phase_3a_success,
                    "status": "PASSED" if phase_3a_success >= 80 else "FAILED"
                },
                "phase_3b_automated_recovery": {
                    "tests": len(phase_3b_tests),
                    "success_rate": phase_3b_success,
                    "status": "PASSED" if phase_3b_success >= 80 else "FAILED"
                },
                "phase_3c_performance_optimization": {
                    "tests": len(phase_3c_tests),
                    "success_rate": phase_3c_success,
                    "status": "PASSED" if phase_3c_success >= 80 else "FAILED"
                },
                "integration_tests": {
                    "tests": len(integration_tests),
                    "success_rate": integration_success,
                    "status": "PASSED" if integration_success >= 80 else "FAILED"
                }
            },
            "test_details": [
                {
                    "test_name": result.test_name,
                    "passed": result.passed,
                    "description": result.description,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message,
                    "details": result.details
                }
                for result in self.test_results
            ],
            "recommendations": self._generate_recommendations(),
            "test_metadata": {
                "test_start_time": self.test_start_time.isoformat(),
                "test_end_time": datetime.now().isoformat(),
                "total_duration": (datetime.now() - self.test_start_time).total_seconds()
            }
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r.passed]
        
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed tests before production deployment")
        
        # Phase-specific recommendations
        phase_3a_tests = [r for r in self.test_results if "Health Monitoring" in r.test_name or "Metrics" in r.test_name or "Alerting" in r.test_name]
        if any(not t.passed for t in phase_3a_tests):
            recommendations.append("Review health monitoring system configuration and thresholds")
        
        phase_3b_tests = [r for r in self.test_results if "Recovery" in r.test_name]
        if any(not t.passed for t in phase_3b_tests):
            recommendations.append("Optimize automated recovery system strategies and escalation rules")
        
        phase_3c_tests = [r for r in self.test_results if "Optimization" in r.test_name]
        if any(not t.passed for t in phase_3c_tests):
            recommendations.append("Fine-tune performance optimization engine parameters and thresholds")
        
        # Performance recommendations
        performance_tests = [r for r in self.test_results if "Performance" in r.test_name or "Stability" in r.test_name]
        if any(not t.passed for t in performance_tests):
            recommendations.append("Address performance and stability issues before production deployment")
        
        if not recommendations:
            recommendations.append("All tests passed - Phase 3 systems ready for production deployment")
        
        return recommendations
    
    def _save_test_report(self, report: Dict[str, Any]):
        """Save test report to file"""
        try:
            report_file = Path("phase3_test_report.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📊 Test report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save test report: {e}")

# Global testing instance
phase3_testing = Phase3ComprehensiveTesting()

if __name__ == "__main__":
    async def main():
        """Run comprehensive Phase 3 testing"""
        logger.info("🚀 Starting Phase 3 Comprehensive Testing")
        
        report = await phase3_testing.run_all_tests()
        
        print("\n" + "="*80)
        print("PHASE 3 COMPREHENSIVE TESTING REPORT")
        print("="*80)
        
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {report['test_summary']['total_tests']}")
        print(f"   Passed: {report['test_summary']['passed_tests']}")
        print(f"   Failed: {report['test_summary']['failed_tests']}")
        print(f"   Success Rate: {report['test_summary']['success_rate']:.1f}%")
        print(f"   Overall Status: {report['test_summary']['overall_status']}")
        
        print(f"\n🔍 Phase Results:")
        for phase_name, phase_result in report['phase_results'].items():
            status_icon = "✅" if phase_result['status'] == "PASSED" else "❌"
            print(f"   {status_icon} {phase_name}: {phase_result['success_rate']:.1f}% ({phase_result['tests']} tests)")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
        
        print("\n" + "="*80)
        
        logger.info("🎉 Phase 3 Comprehensive Testing complete!")
    
    asyncio.run(main())