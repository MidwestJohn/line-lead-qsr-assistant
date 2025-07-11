#!/usr/bin/env python3
"""
Phase 4B: Security and Compliance Layer
=======================================

Comprehensive security and compliance framework for Enterprise Bridge operations.
Implements audit logging, data sanitization, access control, compliance reporting,
data privacy protection, and security monitoring.

Features:
- Audit logging system tracking all bridge operations with user context and results
- Data sanitization for input validation and error message cleaning
- Access control validation for bridge operations based on user permissions
- Compliance reporting meeting enterprise audit requirements
- Data privacy protection for sensitive QSR operational information
- Security monitoring detecting suspicious operation patterns
- Seamless integration without changing functional behavior

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import re
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque
import threading
import sqlite3
import uuid
from functools import wraps

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for operations"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class AuditEventType(Enum):
    """Types of audit events"""
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_PROCESS = "document_process"
    DOCUMENT_QUERY = "document_query"
    DOCUMENT_DELETE = "document_delete"
    SYSTEM_CONFIG = "system_config"
    USER_ACCESS = "user_access"
    DATA_EXPORT = "data_export"
    SECURITY_VIOLATION = "security_violation"

class ComplianceFramework(Enum):
    """Compliance frameworks supported"""
    SOC2 = "soc2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"

class AccessLevel(Enum):
    """User access levels"""
    READ_ONLY = "read_only"
    STANDARD_USER = "standard_user"
    POWER_USER = "power_user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class UserContext:
    """User context for audit logging"""
    user_id: str
    username: str
    email: str
    access_level: AccessLevel
    roles: List[str] = field(default_factory=list)
    department: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None

@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    event_type: AuditEventType
    user_context: UserContext
    timestamp: datetime
    operation: str
    resource: str
    result: str  # success, failure, partial
    data_summary: Dict[str, Any]
    security_level: SecurityLevel
    compliance_tags: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityViolation:
    """Security violation record"""
    violation_id: str
    violation_type: str
    user_context: UserContext
    timestamp: datetime
    severity: str  # low, medium, high, critical
    description: str
    detection_method: str
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceReport:
    """Compliance report"""
    report_id: str
    framework: ComplianceFramework
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    compliance_score: float
    audit_events: int
    violations: int
    recommendations: List[str]
    details: Dict[str, Any] = field(default_factory=dict)

class SecurityComplianceLayer:
    """
    Comprehensive security and compliance framework that provides audit logging,
    data sanitization, access control, and compliance reporting.
    """
    
    def __init__(self):
        self.audit_events: deque = deque(maxlen=100000)  # Keep last 100k events
        self.security_violations: deque = deque(maxlen=10000)  # Keep last 10k violations
        self.active_sessions: Dict[str, UserContext] = {}
        
        # Security patterns for detection
        self.suspicious_patterns = {
            "sql_injection": re.compile(r"(?i)(union|select|insert|delete|update|drop|exec|script)", re.IGNORECASE),
            "path_traversal": re.compile(r"\.\.[\\/]"),
            "xss_attempt": re.compile(r"<script|javascript:|onerror|onload", re.IGNORECASE),
            "data_exfiltration": re.compile(r"(password|token|key|secret|credential)", re.IGNORECASE)
        }
        
        # Data sanitization patterns
        self.sanitization_patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
            "api_key": re.compile(r"\b[A-Za-z0-9]{32,}\b"),
            "password_field": re.compile(r"(password|pwd|pass|secret|token|key)", re.IGNORECASE)
        }
        
        # Access control matrix
        self.access_permissions = {
            AccessLevel.READ_ONLY: {
                "document_query": True,
                "document_upload": False,
                "document_delete": False,
                "system_config": False,
                "data_export": False
            },
            AccessLevel.STANDARD_USER: {
                "document_query": True,
                "document_upload": True,
                "document_delete": False,
                "system_config": False,
                "data_export": True
            },
            AccessLevel.POWER_USER: {
                "document_query": True,
                "document_upload": True,
                "document_delete": True,
                "system_config": False,
                "data_export": True
            },
            AccessLevel.ADMIN: {
                "document_query": True,
                "document_upload": True,
                "document_delete": True,
                "system_config": True,
                "data_export": True
            },
            AccessLevel.SUPER_ADMIN: {
                "document_query": True,
                "document_upload": True,
                "document_delete": True,
                "system_config": True,
                "data_export": True
            }
        }
        
        # Compliance configurations
        self.compliance_configs = {
            ComplianceFramework.SOC2: {
                "audit_retention_days": 2555,  # 7 years
                "required_fields": ["user_id", "timestamp", "operation", "result"],
                "risk_thresholds": {"high": 7.0, "medium": 4.0, "low": 2.0}
            },
            ComplianceFramework.GDPR: {
                "audit_retention_days": 1095,  # 3 years
                "data_anonymization": True,
                "right_to_deletion": True,
                "consent_tracking": True
            },
            ComplianceFramework.HIPAA: {
                "audit_retention_days": 2190,  # 6 years
                "encryption_required": True,
                "access_logging": True,
                "data_minimization": True
            }
        }
        
        # Storage for security data
        self.storage_path = Path("data/security_compliance")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.audit_db_path = self.storage_path / "audit_log.db"
        self.security_config_file = self.storage_path / "security_config.json"
        self.compliance_reports_path = self.storage_path / "compliance_reports"
        self.compliance_reports_path.mkdir(exist_ok=True)
        
        # Security monitoring
        self.monitoring_enabled = True
        self.violation_detection_enabled = True
        self.data_sanitization_enabled = True
        
        # Rate limiting for security
        self.rate_limits = defaultdict(lambda: defaultdict(list))
        self.rate_limit_windows = {
            "document_upload": (10, 300),    # 10 uploads per 5 minutes
            "document_query": (100, 60),     # 100 queries per minute
            "system_config": (5, 3600),      # 5 config changes per hour
            "data_export": (3, 3600)         # 3 exports per hour
        }
        
        # Initialize system
        self._initialize_audit_database()
        self._load_security_configuration()
        
        logger.info("🔒 Security and Compliance Layer initialized")
    
    def _initialize_audit_database(self):
        """Initialize audit database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            # Audit events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL,
                    access_level TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    result TEXT NOT NULL,
                    data_summary TEXT,
                    security_level TEXT NOT NULL,
                    compliance_tags TEXT,
                    risk_score REAL DEFAULT 0.0,
                    metadata TEXT,
                    ip_address TEXT,
                    session_id TEXT
                )
            """)
            
            # Security violations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_violations (
                    violation_id TEXT PRIMARY KEY,
                    violation_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detection_method TEXT NOT NULL,
                    context TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT,
                    resolved_by TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_events(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_operation ON audit_events(operation)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_user_id ON security_violations(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON security_violations(timestamp)")
            
            conn.commit()
            conn.close()
            
            logger.info("🗄️ Audit database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize audit database: {e}")
    
    def _load_security_configuration(self):
        """Load security configuration"""
        try:
            if self.security_config_file.exists():
                with open(self.security_config_file, 'r') as f:
                    config = json.load(f)
                
                self.monitoring_enabled = config.get("monitoring_enabled", self.monitoring_enabled)
                self.violation_detection_enabled = config.get("violation_detection_enabled", self.violation_detection_enabled)
                self.data_sanitization_enabled = config.get("data_sanitization_enabled", self.data_sanitization_enabled)
                
                # Update rate limits if provided
                if "rate_limits" in config:
                    self.rate_limit_windows.update(config["rate_limits"])
                
                logger.info("📥 Loaded security configuration")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load security configuration: {e}")
    
    def _save_security_configuration(self):
        """Save security configuration"""
        try:
            config = {
                "monitoring_enabled": self.monitoring_enabled,
                "violation_detection_enabled": self.violation_detection_enabled,
                "data_sanitization_enabled": self.data_sanitization_enabled,
                "rate_limits": self.rate_limit_windows,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.security_config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save security configuration: {e}")
    
    def audit_operation(self, event_type: AuditEventType, user_context: UserContext,
                       operation: str, resource: str, result: str,
                       data_summary: Dict[str, Any] = None,
                       security_level: SecurityLevel = SecurityLevel.INTERNAL,
                       compliance_tags: List[str] = None) -> str:
        """Log audit event for operation"""
        try:
            event_id = str(uuid.uuid4())
            
            # Sanitize data summary
            sanitized_summary = self._sanitize_data(data_summary or {})
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(event_type, user_context, operation, result)
            
            # Create audit event
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                user_context=user_context,
                timestamp=datetime.now(),
                operation=operation,
                resource=resource,
                result=result,
                data_summary=sanitized_summary,
                security_level=security_level,
                compliance_tags=compliance_tags or [],
                risk_score=risk_score,
                metadata={
                    "user_agent": user_context.metadata.get("user_agent", ""),
                    "request_id": user_context.metadata.get("request_id", "")
                }
            )
            
            # Store audit event
            self._store_audit_event(event)
            
            # Add to in-memory buffer
            self.audit_events.append(event)
            
            # Check for security violations
            if self.violation_detection_enabled:
                self._check_security_violations(event)
            
            logger.debug(f"📋 Audit logged: {operation} by {user_context.username} - {result}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Error logging audit event: {e}")
            return ""
    
    def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_events (
                    event_id, event_type, user_id, username, email, access_level,
                    timestamp, operation, resource, result, data_summary,
                    security_level, compliance_tags, risk_score, metadata,
                    ip_address, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type.value,
                event.user_context.user_id,
                event.user_context.username,
                event.user_context.email,
                event.user_context.access_level.value,
                event.timestamp.isoformat(),
                event.operation,
                event.resource,
                event.result,
                json.dumps(event.data_summary),
                event.security_level.value,
                json.dumps(event.compliance_tags),
                event.risk_score,
                json.dumps(event.metadata),
                event.user_context.ip_address,
                event.user_context.session_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error storing audit event: {e}")
    
    def _calculate_risk_score(self, event_type: AuditEventType, user_context: UserContext,
                            operation: str, result: str) -> float:
        """Calculate risk score for operation"""
        try:
            risk_score = 0.0
            
            # Base risk by event type
            event_risk = {
                AuditEventType.DOCUMENT_UPLOAD: 3.0,
                AuditEventType.DOCUMENT_DELETE: 7.0,
                AuditEventType.SYSTEM_CONFIG: 8.0,
                AuditEventType.DATA_EXPORT: 5.0,
                AuditEventType.SECURITY_VIOLATION: 9.0,
                AuditEventType.DOCUMENT_QUERY: 1.0,
                AuditEventType.DOCUMENT_PROCESS: 2.0,
                AuditEventType.USER_ACCESS: 4.0
            }
            
            risk_score += event_risk.get(event_type, 2.0)
            
            # Adjust for user access level
            if user_context.access_level == AccessLevel.READ_ONLY:
                risk_score *= 0.5
            elif user_context.access_level == AccessLevel.ADMIN:
                risk_score *= 1.5
            elif user_context.access_level == AccessLevel.SUPER_ADMIN:
                risk_score *= 2.0
            
            # Adjust for result
            if result == "failure":
                risk_score *= 1.8
            elif result == "partial":
                risk_score *= 1.3
            
            # Check for suspicious patterns in operation
            for pattern_name, pattern in self.suspicious_patterns.items():
                if pattern.search(operation):
                    risk_score += 5.0
                    break
            
            # Time-based risk (operations outside business hours)
            current_hour = datetime.now().hour
            if current_hour < 6 or current_hour > 22:  # Outside 6 AM - 10 PM
                risk_score *= 1.2
            
            return min(risk_score, 10.0)  # Cap at 10.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating risk score: {e}")
            return 5.0
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data for logging"""
        if not self.data_sanitization_enabled:
            return data
        
        try:
            if isinstance(data, dict):
                sanitized = {}
                for key, value in data.items():
                    # Check if key contains sensitive information
                    if any(pattern.search(key) for pattern in self.sanitization_patterns.values()):
                        sanitized[key] = "[REDACTED]"
                    else:
                        sanitized[key] = self._sanitize_data(value)
                return sanitized
            
            elif isinstance(data, list):
                return [self._sanitize_data(item) for item in data]
            
            elif isinstance(data, str):
                sanitized_str = data
                
                # Sanitize known patterns
                for pattern_name, pattern in self.sanitization_patterns.items():
                    if pattern_name == "email":
                        sanitized_str = pattern.sub("[EMAIL_REDACTED]", sanitized_str)
                    elif pattern_name == "phone":
                        sanitized_str = pattern.sub("[PHONE_REDACTED]", sanitized_str)
                    elif pattern_name == "ssn":
                        sanitized_str = pattern.sub("[SSN_REDACTED]", sanitized_str)
                    elif pattern_name == "credit_card":
                        sanitized_str = pattern.sub("[CC_REDACTED]", sanitized_str)
                    elif pattern_name == "api_key":
                        sanitized_str = pattern.sub("[API_KEY_REDACTED]", sanitized_str)
                
                return sanitized_str
            
            else:
                return data
                
        except Exception as e:
            logger.error(f"❌ Error sanitizing data: {e}")
            return "[SANITIZATION_ERROR]"
    
    def _check_security_violations(self, event: AuditEvent):
        """Check for security violations in audit event"""
        try:
            violations = []
            
            # Check for suspicious patterns
            for pattern_name, pattern in self.suspicious_patterns.items():
                if pattern.search(event.operation) or pattern.search(str(event.data_summary)):
                    violations.append({
                        "type": f"suspicious_pattern_{pattern_name}",
                        "severity": "high",
                        "description": f"Detected {pattern_name} pattern in operation",
                        "detection_method": "pattern_matching"
                    })
            
            # Check for unusual access patterns
            if self._check_unusual_access_pattern(event):
                violations.append({
                    "type": "unusual_access_pattern",
                    "severity": "medium",
                    "description": "Unusual access pattern detected",
                    "detection_method": "behavioral_analysis"
                })
            
            # Check for privilege escalation attempts
            if self._check_privilege_escalation(event):
                violations.append({
                    "type": "privilege_escalation",
                    "severity": "high",
                    "description": "Potential privilege escalation attempt",
                    "detection_method": "access_control_analysis"
                })
            
            # Check rate limiting violations
            if self._check_rate_limit_violation(event):
                violations.append({
                    "type": "rate_limit_violation",
                    "severity": "medium",
                    "description": "Rate limit exceeded",
                    "detection_method": "rate_limiting"
                })
            
            # Create violation records
            for violation_info in violations:
                self._create_security_violation(event, violation_info)
            
        except Exception as e:
            logger.error(f"❌ Error checking security violations: {e}")
    
    def _check_unusual_access_pattern(self, event: AuditEvent) -> bool:
        """Check for unusual access patterns"""
        try:
            current_time = datetime.now()
            user_id = event.user_context.user_id
            
            # Check recent events for this user
            recent_events = [
                e for e in self.audit_events
                if e.user_context.user_id == user_id and
                e.timestamp > current_time - timedelta(hours=1)
            ]
            
            # Check for rapid-fire operations
            if len(recent_events) > 50:  # More than 50 operations in an hour
                return True
            
            # Check for operations outside normal hours
            if current_time.hour < 6 or current_time.hour > 22:
                # Check if user normally works these hours
                normal_hour_events = [
                    e for e in self.audit_events
                    if e.user_context.user_id == user_id and
                    6 <= e.timestamp.hour <= 22 and
                    e.timestamp > current_time - timedelta(days=30)
                ]
                
                off_hour_events = [
                    e for e in self.audit_events
                    if e.user_context.user_id == user_id and
                    (e.timestamp.hour < 6 or e.timestamp.hour > 22) and
                    e.timestamp > current_time - timedelta(days=30)
                ]
                
                # If user rarely works off hours but is doing so now
                if len(normal_hour_events) > 10 and len(off_hour_events) < 3:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking unusual access pattern: {e}")
            return False
    
    def _check_privilege_escalation(self, event: AuditEvent) -> bool:
        """Check for privilege escalation attempts"""
        try:
            # Check if user is attempting operations beyond their access level
            operation_type = event.operation.lower()
            user_permissions = self.access_permissions.get(event.user_context.access_level, {})
            
            # Map operations to permission keys
            permission_mapping = {
                "upload": "document_upload",
                "delete": "document_delete",
                "config": "system_config",
                "export": "data_export",
                "query": "document_query"
            }
            
            for op_key, permission_key in permission_mapping.items():
                if op_key in operation_type and not user_permissions.get(permission_key, False):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking privilege escalation: {e}")
            return False
    
    def _check_rate_limit_violation(self, event: AuditEvent) -> bool:
        """Check for rate limit violations"""
        try:
            current_time = datetime.now()
            user_id = event.user_context.user_id
            operation_type = event.operation.lower()
            
            # Find applicable rate limit
            rate_limit_config = None
            for op_pattern, config in self.rate_limit_windows.items():
                if op_pattern in operation_type:
                    rate_limit_config = config
                    break
            
            if not rate_limit_config:
                return False
            
            max_operations, window_seconds = rate_limit_config
            window_start = current_time - timedelta(seconds=window_seconds)
            
            # Count recent operations of this type by this user
            recent_operations = [
                e for e in self.audit_events
                if e.user_context.user_id == user_id and
                e.timestamp > window_start and
                operation_type in e.operation.lower()
            ]
            
            return len(recent_operations) >= max_operations
            
        except Exception as e:
            logger.error(f"❌ Error checking rate limit violation: {e}")
            return False
    
    def _create_security_violation(self, event: AuditEvent, violation_info: Dict[str, Any]):
        """Create security violation record"""
        try:
            violation_id = str(uuid.uuid4())
            
            violation = SecurityViolation(
                violation_id=violation_id,
                violation_type=violation_info["type"],
                user_context=event.user_context,
                timestamp=datetime.now(),
                severity=violation_info["severity"],
                description=violation_info["description"],
                detection_method=violation_info["detection_method"],
                context={
                    "audit_event_id": event.event_id,
                    "operation": event.operation,
                    "resource": event.resource,
                    "risk_score": event.risk_score
                }
            )
            
            # Store violation
            self._store_security_violation(violation)
            
            # Add to in-memory buffer
            self.security_violations.append(violation)
            
            logger.warning(f"🚨 Security violation: {violation_info['type']} by {event.user_context.username}")
            
        except Exception as e:
            logger.error(f"❌ Error creating security violation: {e}")
    
    def _store_security_violation(self, violation: SecurityViolation):
        """Store security violation in database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO security_violations (
                    violation_id, violation_type, user_id, username, timestamp,
                    severity, description, detection_method, context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation.violation_id,
                violation.violation_type,
                violation.user_context.user_id,
                violation.user_context.username,
                violation.timestamp.isoformat(),
                violation.severity,
                violation.description,
                violation.detection_method,
                json.dumps(violation.context)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error storing security violation: {e}")
    
    def check_access_permission(self, user_context: UserContext, operation: str) -> bool:
        """Check if user has permission for operation"""
        try:
            user_permissions = self.access_permissions.get(user_context.access_level, {})
            
            # Map operation to permission key
            permission_mapping = {
                "document_upload": ["upload", "create", "add"],
                "document_delete": ["delete", "remove"],
                "system_config": ["config", "configure", "settings"],
                "data_export": ["export", "download", "extract"],
                "document_query": ["query", "search", "read", "view"]
            }
            
            operation_lower = operation.lower()
            
            for permission_key, operation_patterns in permission_mapping.items():
                if any(pattern in operation_lower for pattern in operation_patterns):
                    return user_permissions.get(permission_key, False)
            
            # Default to allow for operations not explicitly defined
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking access permission: {e}")
            return False
    
    def sanitize_error_message(self, error_message: str) -> str:
        """Sanitize error message to prevent information leakage"""
        try:
            if not self.data_sanitization_enabled:
                return error_message
            
            sanitized = error_message
            
            # Remove sensitive patterns from error messages
            for pattern_name, pattern in self.sanitization_patterns.items():
                if pattern_name == "email":
                    sanitized = pattern.sub("[EMAIL]", sanitized)
                elif pattern_name == "api_key":
                    sanitized = pattern.sub("[KEY]", sanitized)
                elif pattern_name == "password_field":
                    sanitized = pattern.sub("[CREDENTIAL]", sanitized)
            
            # Remove file paths
            sanitized = re.sub(r'/[^\s]*', '[PATH]', sanitized)
            sanitized = re.sub(r'C:\\[^\s]*', '[PATH]', sanitized)
            
            # Remove database connection strings
            sanitized = re.sub(r'(mongodb|mysql|postgresql|oracle)://[^\s]*', '[CONNECTION]', sanitized)
            
            # Remove IP addresses (but keep localhost)
            sanitized = re.sub(r'\b(?!127\.0\.0\.1)(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP]', sanitized)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"❌ Error sanitizing error message: {e}")
            return "[ERROR_SANITIZATION_FAILED]"
    
    def generate_compliance_report(self, framework: ComplianceFramework,
                                 period_start: datetime, period_end: datetime) -> ComplianceReport:
        """Generate compliance report for specified framework and period"""
        try:
            report_id = str(uuid.uuid4())
            
            # Get audit events for period
            period_events = self._get_audit_events_for_period(period_start, period_end)
            
            # Get violations for period
            period_violations = self._get_violations_for_period(period_start, period_end)
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(framework, period_events, period_violations)
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(framework, period_events, period_violations)
            
            # Create detailed analysis
            details = self._analyze_compliance_details(framework, period_events, period_violations)
            
            report = ComplianceReport(
                report_id=report_id,
                framework=framework,
                period_start=period_start,
                period_end=period_end,
                generated_at=datetime.now(),
                compliance_score=compliance_score,
                audit_events=len(period_events),
                violations=len(period_violations),
                recommendations=recommendations,
                details=details
            )
            
            # Save report
            self._save_compliance_report(report)
            
            logger.info(f"📊 Generated {framework.value} compliance report: {compliance_score:.1f}% compliance")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating compliance report: {e}")
            return None
    
    def _get_audit_events_for_period(self, start: datetime, end: datetime) -> List[AuditEvent]:
        """Get audit events for specified period"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM audit_events 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start.isoformat(), end.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to AuditEvent objects
            events = []
            for row in rows:
                user_context = UserContext(
                    user_id=row[2],
                    username=row[3],
                    email=row[4],
                    access_level=AccessLevel(row[5]),
                    ip_address=row[15],
                    session_id=row[16]
                )
                
                event = AuditEvent(
                    event_id=row[0],
                    event_type=AuditEventType(row[1]),
                    user_context=user_context,
                    timestamp=datetime.fromisoformat(row[6]),
                    operation=row[7],
                    resource=row[8],
                    result=row[9],
                    data_summary=json.loads(row[10]) if row[10] else {},
                    security_level=SecurityLevel(row[11]),
                    compliance_tags=json.loads(row[12]) if row[12] else [],
                    risk_score=row[13] or 0.0,
                    metadata=json.loads(row[14]) if row[14] else {}
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error getting audit events for period: {e}")
            return []
    
    def _get_violations_for_period(self, start: datetime, end: datetime) -> List[SecurityViolation]:
        """Get security violations for specified period"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM security_violations 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start.isoformat(), end.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to SecurityViolation objects
            violations = []
            for row in rows:
                user_context = UserContext(
                    user_id=row[2],
                    username=row[3],
                    email="",  # Not stored in violations table
                    access_level=AccessLevel.STANDARD_USER  # Default
                )
                
                violation = SecurityViolation(
                    violation_id=row[0],
                    violation_type=row[1],
                    user_context=user_context,
                    timestamp=datetime.fromisoformat(row[4]),
                    severity=row[5],
                    description=row[6],
                    detection_method=row[7],
                    context=json.loads(row[8]) if row[8] else {}
                )
                violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"❌ Error getting violations for period: {e}")
            return []
    
    def _calculate_compliance_score(self, framework: ComplianceFramework,
                                  events: List[AuditEvent], violations: List[SecurityViolation]) -> float:
        """Calculate compliance score based on framework requirements"""
        try:
            score = 100.0
            
            if framework == ComplianceFramework.SOC2:
                # SOC2 focuses on security controls
                if violations:
                    # Deduct points for violations
                    high_severity = len([v for v in violations if v.severity == "high"])
                    medium_severity = len([v for v in violations if v.severity == "medium"])
                    low_severity = len([v for v in violations if v.severity == "low"])
                    
                    score -= (high_severity * 15 + medium_severity * 8 + low_severity * 3)
                
                # Check for required audit coverage
                required_events = ["document_upload", "document_delete", "system_config"]
                for required_event in required_events:
                    if not any(e.event_type.value == required_event for e in events):
                        score -= 10
            
            elif framework == ComplianceFramework.GDPR:
                # GDPR focuses on data protection
                data_processing_events = [e for e in events if "data" in e.operation.lower()]
                
                if data_processing_events:
                    # Check for consent tracking
                    consent_events = [e for e in events if "consent" in str(e.compliance_tags)]
                    if len(consent_events) < len(data_processing_events) * 0.8:
                        score -= 20
                
                # Check for data minimization
                high_risk_events = [e for e in events if e.risk_score > 7.0]
                if len(high_risk_events) > len(events) * 0.1:
                    score -= 15
            
            elif framework == ComplianceFramework.HIPAA:
                # HIPAA focuses on healthcare data protection
                if violations:
                    # HIPAA has stricter violation penalties
                    critical_violations = len([v for v in violations if v.severity in ["high", "critical"]])
                    score -= critical_violations * 25
                
                # Check for access logging
                access_events = [e for e in events if e.event_type == AuditEventType.USER_ACCESS]
                if len(access_events) < len(events) * 0.1:
                    score -= 20
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"❌ Error calculating compliance score: {e}")
            return 0.0
    
    def _generate_compliance_recommendations(self, framework: ComplianceFramework,
                                           events: List[AuditEvent], violations: List[SecurityViolation]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        try:
            if violations:
                recommendations.append(f"Address {len(violations)} security violations identified in the audit period")
                
                high_severity_violations = [v for v in violations if v.severity == "high"]
                if high_severity_violations:
                    recommendations.append(f"Prioritize resolution of {len(high_severity_violations)} high-severity violations")
            
            if framework == ComplianceFramework.SOC2:
                recommendations.extend([
                    "Implement regular security awareness training",
                    "Review and update access control policies",
                    "Establish incident response procedures"
                ])
            
            elif framework == ComplianceFramework.GDPR:
                recommendations.extend([
                    "Enhance consent tracking mechanisms",
                    "Implement data retention policies",
                    "Conduct privacy impact assessments"
                ])
            
            elif framework == ComplianceFramework.HIPAA:
                recommendations.extend([
                    "Strengthen access controls for healthcare data",
                    "Implement encryption for data at rest and in transit",
                    "Conduct regular risk assessments"
                ])
            
            # Add general recommendations based on audit analysis
            if events:
                failed_events = [e for e in events if e.result == "failure"]
                if len(failed_events) > len(events) * 0.1:
                    recommendations.append("Investigate high failure rate in operations")
                
                high_risk_events = [e for e in events if e.risk_score > 8.0]
                if high_risk_events:
                    recommendations.append("Review high-risk operations and implement additional controls")
            
        except Exception as e:
            logger.error(f"❌ Error generating compliance recommendations: {e}")
        
        return recommendations
    
    def _analyze_compliance_details(self, framework: ComplianceFramework,
                                  events: List[AuditEvent], violations: List[SecurityViolation]) -> Dict[str, Any]:
        """Analyze compliance details"""
        try:
            details = {
                "audit_summary": {
                    "total_events": len(events),
                    "event_types": {},
                    "user_activity": {},
                    "risk_distribution": {}
                },
                "violation_summary": {
                    "total_violations": len(violations),
                    "by_severity": {},
                    "by_type": {},
                    "by_user": {}
                },
                "compliance_metrics": {}
            }
            
            # Analyze audit events
            for event in events:
                # Event types
                event_type = event.event_type.value
                details["audit_summary"]["event_types"][event_type] = details["audit_summary"]["event_types"].get(event_type, 0) + 1
                
                # User activity
                user_id = event.user_context.user_id
                details["audit_summary"]["user_activity"][user_id] = details["audit_summary"]["user_activity"].get(user_id, 0) + 1
                
                # Risk distribution
                risk_level = "low" if event.risk_score < 3 else "medium" if event.risk_score < 7 else "high"
                details["audit_summary"]["risk_distribution"][risk_level] = details["audit_summary"]["risk_distribution"].get(risk_level, 0) + 1
            
            # Analyze violations
            for violation in violations:
                # By severity
                severity = violation.severity
                details["violation_summary"]["by_severity"][severity] = details["violation_summary"]["by_severity"].get(severity, 0) + 1
                
                # By type
                v_type = violation.violation_type
                details["violation_summary"]["by_type"][v_type] = details["violation_summary"]["by_type"].get(v_type, 0) + 1
                
                # By user
                user_id = violation.user_context.user_id
                details["violation_summary"]["by_user"][user_id] = details["violation_summary"]["by_user"].get(user_id, 0) + 1
            
            # Framework-specific metrics
            if framework == ComplianceFramework.SOC2:
                details["compliance_metrics"]["security_controls"] = {
                    "access_logging": len([e for e in events if e.event_type == AuditEventType.USER_ACCESS]),
                    "configuration_changes": len([e for e in events if e.event_type == AuditEventType.SYSTEM_CONFIG]),
                    "data_access": len([e for e in events if e.event_type in [AuditEventType.DOCUMENT_QUERY, AuditEventType.DATA_EXPORT]])
                }
            
            elif framework == ComplianceFramework.GDPR:
                details["compliance_metrics"]["data_protection"] = {
                    "consent_events": len([e for e in events if "consent" in str(e.compliance_tags)]),
                    "data_processing": len([e for e in events if "data" in e.operation.lower()]),
                    "deletion_requests": len([e for e in events if e.event_type == AuditEventType.DOCUMENT_DELETE])
                }
            
            return details
            
        except Exception as e:
            logger.error(f"❌ Error analyzing compliance details: {e}")
            return {}
    
    def _save_compliance_report(self, report: ComplianceReport):
        """Save compliance report to file"""
        try:
            report_filename = f"{report.framework.value}_report_{report.period_start.strftime('%Y%m%d')}_{report.period_end.strftime('%Y%m%d')}.json"
            report_path = self.compliance_reports_path / report_filename
            
            report_data = {
                "report_id": report.report_id,
                "framework": report.framework.value,
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "generated_at": report.generated_at.isoformat(),
                "compliance_score": report.compliance_score,
                "audit_events": report.audit_events,
                "violations": report.violations,
                "recommendations": report.recommendations,
                "details": report.details
            }
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"💾 Saved compliance report: {report_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving compliance report: {e}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        current_time = datetime.now()
        
        # Recent violations (last 24 hours)
        recent_violations = [
            v for v in self.security_violations
            if v.timestamp > current_time - timedelta(hours=24)
        ]
        
        # Recent high-risk events (last 24 hours)
        recent_high_risk_events = [
            e for e in self.audit_events
            if e.timestamp > current_time - timedelta(hours=24) and e.risk_score > 7.0
        ]
        
        return {
            "monitoring_enabled": self.monitoring_enabled,
            "violation_detection_enabled": self.violation_detection_enabled,
            "data_sanitization_enabled": self.data_sanitization_enabled,
            "audit_events_total": len(self.audit_events),
            "violations_total": len(self.security_violations),
            "recent_violations_24h": len(recent_violations),
            "recent_high_risk_events_24h": len(recent_high_risk_events),
            "active_sessions": len(self.active_sessions),
            "last_updated": current_time.isoformat()
        }
    
    def enable_security_feature(self, feature: str, enabled: bool = True):
        """Enable or disable security features"""
        try:
            if feature == "monitoring":
                self.monitoring_enabled = enabled
            elif feature == "violation_detection":
                self.violation_detection_enabled = enabled
            elif feature == "data_sanitization":
                self.data_sanitization_enabled = enabled
            
            self._save_security_configuration()
            logger.info(f"🔧 Security feature '{feature}' {'enabled' if enabled else 'disabled'}")
            
        except Exception as e:
            logger.error(f"❌ Error configuring security feature: {e}")


# Decorator for automatic audit logging
def audit_operation(event_type: AuditEventType, operation: str, resource: str = "",
                   security_level: SecurityLevel = SecurityLevel.INTERNAL,
                   compliance_tags: List[str] = None):
    """Decorator for automatic audit logging of operations"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract user context from kwargs or set default
            user_context = kwargs.get('user_context') or UserContext(
                user_id="system",
                username="system",
                email="system@localhost",
                access_level=AccessLevel.ADMIN
            )
            
            try:
                # Check access permission
                if not security_compliance_layer.check_access_permission(user_context, operation):
                    security_compliance_layer.audit_operation(
                        AuditEventType.SECURITY_VIOLATION,
                        user_context,
                        operation,
                        resource,
                        "failure",
                        {"error": "access_denied"},
                        security_level,
                        compliance_tags
                    )
                    raise PermissionError("Access denied for operation")
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Log successful operation
                security_compliance_layer.audit_operation(
                    event_type,
                    user_context,
                    operation,
                    resource,
                    "success",
                    {"result_type": type(result).__name__},
                    security_level,
                    compliance_tags
                )
                
                return result
                
            except Exception as e:
                # Log failed operation
                error_message = security_compliance_layer.sanitize_error_message(str(e))
                security_compliance_layer.audit_operation(
                    event_type,
                    user_context,
                    operation,
                    resource,
                    "failure",
                    {"error": error_message},
                    security_level,
                    compliance_tags
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, similar logic but without await
            user_context = kwargs.get('user_context') or UserContext(
                user_id="system",
                username="system", 
                email="system@localhost",
                access_level=AccessLevel.ADMIN
            )
            
            try:
                if not security_compliance_layer.check_access_permission(user_context, operation):
                    security_compliance_layer.audit_operation(
                        AuditEventType.SECURITY_VIOLATION,
                        user_context,
                        operation,
                        resource,
                        "failure",
                        {"error": "access_denied"},
                        security_level,
                        compliance_tags
                    )
                    raise PermissionError("Access denied for operation")
                
                result = func(*args, **kwargs)
                
                security_compliance_layer.audit_operation(
                    event_type,
                    user_context,
                    operation,
                    resource,
                    "success",
                    {"result_type": type(result).__name__},
                    security_level,
                    compliance_tags
                )
                
                return result
                
            except Exception as e:
                error_message = security_compliance_layer.sanitize_error_message(str(e))
                security_compliance_layer.audit_operation(
                    event_type,
                    user_context,
                    operation,
                    resource,
                    "failure",
                    {"error": error_message},
                    security_level,
                    compliance_tags
                )
                raise
        
        # Return appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global security compliance instance
security_compliance_layer = SecurityComplianceLayer()

logger.info("🚀 Security and Compliance Layer ready")