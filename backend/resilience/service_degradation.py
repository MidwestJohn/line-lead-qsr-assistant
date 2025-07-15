#!/usr/bin/env python3
"""
Service Degradation Management - BaseChat Enterprise Patterns
============================================================

Intelligent service degradation for Line Lead's proven components,
following BaseChat's resilience patterns optimized for production.

Features:
- Performance-based degradation triggers
- Graceful service degradation for all proven components
- Automatic recovery detection and restoration
- User experience protection during failures
- Real-time service health monitoring

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceLevel(Enum):
    """Service level definitions following BaseChat patterns"""
    FULL = "full_service"
    DEGRADED = "degraded_service" 
    MINIMAL = "minimal_service"
    EMERGENCY = "emergency_only"
    UNAVAILABLE = "unavailable"

class ServiceType(Enum):
    """Line Lead service types"""
    PYDANTIC_ORCHESTRATION = "pydantic_orchestration"
    RAGIE_ENHANCEMENT = "ragie_enhancement"
    VISUAL_CITATIONS = "visual_citations"
    VOICE_PROCESSING = "voice_processing"
    DOCUMENT_STORAGE = "document_storage"
    DATABASE = "database"

@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    response_times: List[float] = field(default_factory=list)
    error_count: int = 0
    success_count: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0

@dataclass
class ServiceStatus:
    """Current service status and health"""
    name: str
    service_type: ServiceType
    level: ServiceLevel
    metrics: ServiceMetrics
    last_check: float
    degradation_reason: Optional[str] = None
    recovery_target: Optional[datetime] = None
    user_impact: str = "none"

class ServiceDegradationManager:
    """Manages service degradation for proven Line Lead architecture"""
    
    def __init__(self):
        """Initialize service degradation management"""
        self.service_statuses = self._initialize_services()
        self.degradation_history = []
        
        # Performance thresholds optimized for Line Lead
        self.thresholds = {
            "response_time_warning": 2000,    # 2s warning threshold
            "response_time_critical": 5000,   # 5s critical threshold
            "error_rate_warning": 0.10,       # 10% error rate warning
            "error_rate_critical": 0.25,      # 25% error rate critical
            "consecutive_failures_limit": 3,   # 3 consecutive failures trigger degradation
            "recovery_successes_needed": 5    # 5 consecutive successes for recovery
        }
        
        # Service-specific configuration
        self.service_configs = {
            ServiceType.PYDANTIC_ORCHESTRATION: {
                "critical": True,  # Core functionality
                "fallback_available": False,
                "target_response_time": 3000,  # 3s target
                "priority": 1
            },
            ServiceType.RAGIE_ENHANCEMENT: {
                "critical": False,  # Enhanced functionality
                "fallback_available": True,
                "target_response_time": 800,   # 800ms target
                "priority": 3
            },
            ServiceType.VISUAL_CITATIONS: {
                "critical": False,  # Visual enhancement
                "fallback_available": True,
                "target_response_time": 1000,  # 1s target
                "priority": 4
            },
            ServiceType.VOICE_PROCESSING: {
                "critical": False,  # Alternative input method
                "fallback_available": True,
                "target_response_time": 2000,  # 2s target
                "priority": 5
            },
            ServiceType.DOCUMENT_STORAGE: {
                "critical": True,   # Important for QSR knowledge
                "fallback_available": True,
                "target_response_time": 1000,  # 1s target
                "priority": 2
            }
        }
        
        logger.info("🔄 Service degradation manager initialized for proven Line Lead components")
    
    def _initialize_services(self) -> Dict[ServiceType, ServiceStatus]:
        """Initialize service status tracking"""
        services = {}
        
        for service_type in ServiceType:
            services[service_type] = ServiceStatus(
                name=service_type.value,
                service_type=service_type,
                level=ServiceLevel.FULL,
                metrics=ServiceMetrics(),
                last_check=time.time(),
                user_impact="none"
            )
        
        return services
    
    async def record_service_call(
        self, 
        service_type: ServiceType, 
        response_time_ms: float, 
        success: bool,
        error_details: Optional[str] = None
    ):
        """Record service call results and evaluate health"""
        if service_type not in self.service_statuses:
            logger.warning(f"⚠️ Unknown service type: {service_type}")
            return
        
        status = self.service_statuses[service_type]
        metrics = status.metrics
        
        # Update metrics
        metrics.response_times.append(response_time_ms)
        if len(metrics.response_times) > 100:  # Keep last 100 measurements
            metrics.response_times = metrics.response_times[-100:]
        
        current_time = time.time()
        status.last_check = current_time
        
        if success:
            metrics.success_count += 1
            metrics.last_success = current_time
            metrics.consecutive_successes += 1
            metrics.consecutive_failures = 0
        else:
            metrics.error_count += 1
            metrics.last_failure = current_time
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
        
        # Evaluate service level
        new_level = await self._evaluate_service_level(status, error_details)
        
        # Handle level changes
        if new_level != status.level:
            await self._handle_level_change(status, new_level)
    
    async def _evaluate_service_level(
        self, 
        status: ServiceStatus, 
        error_details: Optional[str] = None
    ) -> ServiceLevel:
        """Evaluate appropriate service level based on metrics"""
        metrics = status.metrics
        config = self.service_configs.get(status.service_type, {})
        
        # Calculate average response time (last 10 calls)
        recent_times = metrics.response_times[-10:] if metrics.response_times else []
        avg_response_time = sum(recent_times) / len(recent_times) if recent_times else 0
        
        # Calculate error rate (last 20 calls)
        total_recent_calls = min(20, metrics.success_count + metrics.error_count)
        recent_errors = min(metrics.error_count, 20)
        error_rate = recent_errors / total_recent_calls if total_recent_calls > 0 else 0
        
        # Critical service failure (multiple consecutive failures)
        if metrics.consecutive_failures >= self.thresholds["consecutive_failures_limit"]:
            if config.get("critical", False):
                return ServiceLevel.EMERGENCY
            else:
                return ServiceLevel.UNAVAILABLE
        
        # Performance-based degradation
        target_time = config.get("target_response_time", 3000)
        
        if avg_response_time > target_time * 2:  # 2x target time
            return ServiceLevel.EMERGENCY
        elif avg_response_time > target_time * 1.5:  # 1.5x target time
            return ServiceLevel.DEGRADED
        elif error_rate > self.thresholds["error_rate_critical"]:
            return ServiceLevel.MINIMAL
        elif error_rate > self.thresholds["error_rate_warning"]:
            return ServiceLevel.DEGRADED
        
        # Check for recovery (consecutive successes)
        if (status.level != ServiceLevel.FULL and 
            metrics.consecutive_successes >= self.thresholds["recovery_successes_needed"]):
            return ServiceLevel.FULL
        
        # Maintain current level if no clear change indicators
        return status.level
    
    async def _handle_level_change(self, status: ServiceStatus, new_level: ServiceLevel):
        """Handle service level changes with appropriate actions"""
        old_level = status.level
        status.level = new_level
        
        # Log the change
        if new_level.value < old_level.value:  # Degradation
            logger.warning(f"🔻 Service {status.name} degraded: {old_level.value} → {new_level.value}")
            await self._activate_degradation_strategy(status)
        else:  # Recovery
            logger.info(f"🔺 Service {status.name} recovered: {old_level.value} → {new_level.value}")
            await self._activate_recovery_strategy(status)
        
        # Record in history
        self.degradation_history.append({
            "timestamp": datetime.now().isoformat(),
            "service": status.name,
            "old_level": old_level.value,
            "new_level": new_level.value,
            "change_type": "degradation" if new_level.value < old_level.value else "recovery"
        })
        
        # Keep history manageable
        if len(self.degradation_history) > 1000:
            self.degradation_history = self.degradation_history[-500:]
    
    async def _activate_degradation_strategy(self, status: ServiceStatus):
        """Activate degradation strategy for specific service"""
        strategies = {
            ServiceType.RAGIE_ENHANCEMENT: self._degrade_ragie_enhancement,
            ServiceType.VISUAL_CITATIONS: self._degrade_visual_citations,
            ServiceType.VOICE_PROCESSING: self._degrade_voice_processing,
            ServiceType.DOCUMENT_STORAGE: self._degrade_document_storage,
            ServiceType.PYDANTIC_ORCHESTRATION: self._degrade_pydantic_orchestration
        }
        
        strategy = strategies.get(status.service_type)
        if strategy:
            await strategy(status)
    
    async def _degrade_ragie_enhancement(self, status: ServiceStatus):
        """Degrade Ragie enhancement service"""
        if status.level == ServiceLevel.DEGRADED:
            # Increase timeout, reduce complexity
            status.degradation_reason = "Increased timeout, simplified queries"
            status.user_impact = "Knowledge enhancement may be slower"
        elif status.level in [ServiceLevel.EMERGENCY, ServiceLevel.UNAVAILABLE]:
            # Disable Ragie, use standard responses only
            status.degradation_reason = "Ragie disabled, using standard responses"
            status.user_impact = "Using standard QSR knowledge only"
        
        logger.info(f"🔄 Ragie enhancement degraded: {status.degradation_reason}")
    
    async def _degrade_visual_citations(self, status: ServiceStatus):
        """Degrade visual citation service"""
        if status.level == ServiceLevel.DEGRADED:
            status.degradation_reason = "Reduced image quality, increased caching"
            status.user_impact = "Visual content may load slower"
        elif status.level in [ServiceLevel.EMERGENCY, ServiceLevel.UNAVAILABLE]:
            status.degradation_reason = "Text-only responses active"
            status.user_impact = "Visual content temporarily unavailable"
        
        logger.info(f"🔄 Visual citations degraded: {status.degradation_reason}")
    
    async def _degrade_voice_processing(self, status: ServiceStatus):
        """Degrade voice processing service"""
        if status.level == ServiceLevel.DEGRADED:
            status.degradation_reason = "Reduced audio quality, increased buffering"
            status.user_impact = "Voice processing may be slower"
        elif status.level in [ServiceLevel.EMERGENCY, ServiceLevel.UNAVAILABLE]:
            status.degradation_reason = "Voice disabled, text-only mode"
            status.user_impact = "Please use text chat only"
        
        logger.info(f"🔄 Voice processing degraded: {status.degradation_reason}")
    
    async def _degrade_pydantic_orchestration(self, status: ServiceStatus):
        """Degrade PydanticAI orchestration (critical service)"""
        if status.level == ServiceLevel.DEGRADED:
            status.degradation_reason = "Simplified agent routing, reduced complexity"
            status.user_impact = "AI responses may be slower or simplified"
        elif status.level in [ServiceLevel.EMERGENCY, ServiceLevel.UNAVAILABLE]:
            status.degradation_reason = "Core AI service degraded"
            status.user_impact = "AI assistant functionality severely limited"
        
        logger.error(f"🚨 PydanticAI orchestration degraded: {status.degradation_reason}")
    
    async def _degrade_document_storage(self, status: ServiceStatus):
        """Degrade document storage service"""
        if status.level == ServiceLevel.DEGRADED:
            status.degradation_reason = "Slower document retrieval, reduced caching"
            status.user_impact = "Document access may be slower"
        elif status.level in [ServiceLevel.EMERGENCY, ServiceLevel.UNAVAILABLE]:
            status.degradation_reason = "Document storage unavailable"
            status.user_impact = "Cannot access uploaded documents temporarily"
        
        logger.warning(f"🔄 Document storage degraded: {status.degradation_reason}")
    
    async def _activate_recovery_strategy(self, status: ServiceStatus):
        """Activate recovery strategy for specific service"""
        status.degradation_reason = None
        status.user_impact = "none"
        status.recovery_target = None
        
        logger.info(f"✅ Service {status.name} recovered to {status.level.value}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Calculate overall system level
        critical_services = [s for s in self.service_statuses.values() 
                           if self.service_configs.get(s.service_type, {}).get("critical", False)]
        
        if any(s.level in [ServiceLevel.EMERGENCY, ServiceLevel.UNAVAILABLE] for s in critical_services):
            overall_level = ServiceLevel.EMERGENCY
        elif any(s.level == ServiceLevel.DEGRADED for s in self.service_statuses.values()):
            overall_level = ServiceLevel.DEGRADED
        else:
            overall_level = ServiceLevel.FULL
        
        # Service details
        service_details = {}
        degraded_services = []
        
        for service_type, status in self.service_statuses.items():
            config = self.service_configs.get(service_type, {})
            
            # Calculate metrics
            metrics = status.metrics
            total_calls = metrics.success_count + metrics.error_count
            error_rate = metrics.error_count / total_calls if total_calls > 0 else 0
            avg_response_time = (sum(metrics.response_times) / len(metrics.response_times) 
                               if metrics.response_times else 0)
            
            service_details[service_type.value] = {
                "level": status.level.value,
                "target_response_time_ms": config.get("target_response_time", 3000),
                "avg_response_time_ms": round(avg_response_time, 2),
                "error_rate": round(error_rate, 3),
                "success_count": metrics.success_count,
                "error_count": metrics.error_count,
                "consecutive_failures": metrics.consecutive_failures,
                "consecutive_successes": metrics.consecutive_successes,
                "last_check": status.last_check,
                "degradation_reason": status.degradation_reason,
                "user_impact": status.user_impact,
                "fallback_available": config.get("fallback_available", False),
                "critical": config.get("critical", False)
            }
            
            if status.level != ServiceLevel.FULL:
                degraded_services.append({
                    "service": service_type.value,
                    "level": status.level.value,
                    "reason": status.degradation_reason,
                    "impact": status.user_impact
                })
        
        return {
            "overall_status": overall_level.value,
            "timestamp": datetime.now().isoformat(),
            "services": service_details,
            "degraded_services": degraded_services,
            "system_health": {
                "total_services": len(self.service_statuses),
                "healthy_services": len([s for s in self.service_statuses.values() if s.level == ServiceLevel.FULL]),
                "degraded_services_count": len(degraded_services),
                "critical_services_affected": len([s for s in degraded_services 
                                                 if self.service_configs.get(ServiceType(s["service"]), {}).get("critical", False)])
            },
            "user_experience_impact": self._describe_user_impact(overall_level, degraded_services)
        }
    
    def _describe_user_impact(self, level: ServiceLevel, degraded_services: List[Dict]) -> str:
        """Describe user impact based on system status"""
        if level == ServiceLevel.FULL:
            return "All features working normally"
        elif level == ServiceLevel.DEGRADED:
            if len(degraded_services) == 1:
                return f"Minor impact: {degraded_services[0]['impact']}"
            else:
                return f"Some features may be slower or unavailable ({len(degraded_services)} services affected)"
        elif level == ServiceLevel.EMERGENCY:
            return "Significant service limitations - core functionality may be impacted"
        else:
            return "Service temporarily unavailable"
    
    def get_degradation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent degradation history"""
        return self.degradation_history[-limit:] if self.degradation_history else []

# Global degradation manager instance
degradation_manager = ServiceDegradationManager()

# Convenience functions for service monitoring
async def record_pydantic_call(response_time_ms: float, success: bool, error: str = None):
    """Record PydanticAI orchestration call"""
    await degradation_manager.record_service_call(
        ServiceType.PYDANTIC_ORCHESTRATION, response_time_ms, success, error
    )

async def record_ragie_call(response_time_ms: float, success: bool, error: str = None):
    """Record Ragie enhancement call"""
    await degradation_manager.record_service_call(
        ServiceType.RAGIE_ENHANCEMENT, response_time_ms, success, error
    )

async def record_voice_call(response_time_ms: float, success: bool, error: str = None):
    """Record voice processing call"""
    await degradation_manager.record_service_call(
        ServiceType.VOICE_PROCESSING, response_time_ms, success, error
    )

async def record_visual_call(response_time_ms: float, success: bool, error: str = None):
    """Record visual citation call"""
    await degradation_manager.record_service_call(
        ServiceType.VISUAL_CITATIONS, response_time_ms, success, error
    )

async def record_document_call(response_time_ms: float, success: bool, error: str = None):
    """Record document storage call"""
    await degradation_manager.record_service_call(
        ServiceType.DOCUMENT_STORAGE, response_time_ms, success, error
    )