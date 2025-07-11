#!/usr/bin/env python3
"""
Phase 4C: Enterprise Configuration Management
=============================================

Enterprise-grade configuration management system for Bridge operations with
environment-specific settings, dynamic loading, validation, change tracking,
and rollback capabilities.

Features:
- Dynamic configuration loading adapting to deployment environment (dev/staging/production)
- Configuration validation preventing invalid settings that could cause operational issues
- Configuration change tracking and rollback capabilities for safe configuration updates
- Configuration templates for different deployment scenarios and load patterns
- Configuration monitoring with alerts on configuration drift or invalid settings
- Hot configuration reload without requiring bridge restart or service interruption

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import time
import copy
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import threading
import weakref

# Optional imports
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from jsonschema import validate, ValidationError, draft7_format_checker
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class ConfigChangeType(Enum):
    """Types of configuration changes"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ROLLBACK = "rollback"
    TEMPLATE_APPLY = "template_apply"

class ValidationSeverity(Enum):
    """Configuration validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ConfigurationChange:
    """Configuration change record"""
    change_id: str
    change_type: ConfigChangeType
    environment: Environment
    user_id: str
    timestamp: datetime
    key_path: str
    old_value: Any
    new_value: Any
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    applied: bool = False
    rollback_available: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Configuration validation result"""
    key_path: str
    severity: ValidationSeverity
    message: str
    suggestion: Optional[str] = None
    valid: bool = True

@dataclass
class ConfigurationTemplate:
    """Configuration template for deployment scenarios"""
    template_id: str
    name: str
    description: str
    environment: Environment
    load_pattern: str  # low, medium, high, auto_scaling
    config_overrides: Dict[str, Any]
    created_at: datetime
    version: str = "1.0"

class ConfigurationManager:
    """
    Enterprise-grade configuration management system with environment-specific
    settings, validation, change tracking, and hot reload capabilities.
    """
    
    def __init__(self):
        self.current_environment = self._detect_environment()
        self.configurations: Dict[str, Any] = {}
        self.configuration_history: List[ConfigurationChange] = []
        self.configuration_templates: Dict[str, ConfigurationTemplate] = {}
        self.validation_rules: Dict[str, Dict] = {}
        
        # Configuration watchers (for hot reload)
        self.config_watchers: Dict[str, List[Callable]] = defaultdict(list)
        self.change_callbacks: List[Callable] = []
        
        # Configuration monitoring
        self.monitoring_enabled = True
        self.validation_enabled = True
        self.change_tracking_enabled = True
        self.hot_reload_enabled = True
        
        # Storage paths
        self.storage_path = Path("data/enterprise_configuration")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.storage_path / f"config_{self.current_environment.value}.json"
        self.history_file = self.storage_path / "configuration_history.json"
        self.templates_file = self.storage_path / "configuration_templates.json"
        self.validation_rules_file = self.storage_path / "validation_rules.json"
        self.schema_file = self.storage_path / "configuration_schema.json"
        
        # Configuration schema
        self.configuration_schema = self._get_configuration_schema()
        
        # Environment-specific defaults
        self.environment_defaults = self._get_environment_defaults()
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_enabled = True
        
        # Initialize system
        self._initialize_configuration_system()
        
        logger.info(f"🔧 Enterprise Configuration Manager initialized for {self.current_environment.value}")
    
    def _detect_environment(self) -> Environment:
        """Detect current deployment environment"""
        try:
            # Check environment variable
            env_var = os.getenv("DEPLOYMENT_ENV", "").lower()
            
            if env_var in ["prod", "production"]:
                return Environment.PRODUCTION
            elif env_var in ["stage", "staging"]:
                return Environment.STAGING
            elif env_var in ["test", "testing"]:
                return Environment.TESTING
            elif env_var in ["dev", "development"]:
                return Environment.DEVELOPMENT
            
            # Check for common production indicators
            if os.getenv("NODE_ENV") == "production":
                return Environment.PRODUCTION
            
            # Check hostname patterns
            hostname = os.getenv("HOSTNAME", "").lower()
            if "prod" in hostname:
                return Environment.PRODUCTION
            elif "stage" in hostname:
                return Environment.STAGING
            elif "test" in hostname:
                return Environment.TESTING
            
            # Default to development
            return Environment.DEVELOPMENT
            
        except Exception as e:
            logger.warning(f"⚠️ Error detecting environment, defaulting to development: {e}")
            return Environment.DEVELOPMENT
    
    def _get_environment_defaults(self) -> Dict[str, Dict[str, Any]]:
        """Get environment-specific default configurations"""
        return {
            Environment.DEVELOPMENT.value: {
                "processing": {
                    "batch_size": 1,
                    "timeout_seconds": 300,
                    "retry_attempts": 2,
                    "concurrent_processes": 2
                },
                "database": {
                    "connection_pool_size": 3,
                    "query_timeout": 30,
                    "max_retries": 2
                },
                "monitoring": {
                    "metrics_collection_interval": 60,
                    "health_check_interval": 30,
                    "alert_thresholds": {
                        "memory_usage": 85.0,
                        "error_rate": 0.1,
                        "response_time": 10.0
                    }
                },
                "security": {
                    "audit_logging": True,
                    "data_sanitization": True,
                    "rate_limiting": False
                },
                "degradation": {
                    "auto_recovery": True,
                    "queue_mode_threshold": 300,
                    "memory_threshold": 80.0
                }
            },
            Environment.STAGING.value: {
                "processing": {
                    "batch_size": 2,
                    "timeout_seconds": 600,
                    "retry_attempts": 3,
                    "concurrent_processes": 3
                },
                "database": {
                    "connection_pool_size": 5,
                    "query_timeout": 45,
                    "max_retries": 3
                },
                "monitoring": {
                    "metrics_collection_interval": 30,
                    "health_check_interval": 60,
                    "alert_thresholds": {
                        "memory_usage": 80.0,
                        "error_rate": 0.05,
                        "response_time": 5.0
                    }
                },
                "security": {
                    "audit_logging": True,
                    "data_sanitization": True,
                    "rate_limiting": True
                },
                "degradation": {
                    "auto_recovery": True,
                    "queue_mode_threshold": 180,
                    "memory_threshold": 75.0
                }
            },
            Environment.PRODUCTION.value: {
                "processing": {
                    "batch_size": 3,
                    "timeout_seconds": 900,
                    "retry_attempts": 5,
                    "concurrent_processes": 5
                },
                "database": {
                    "connection_pool_size": 10,
                    "query_timeout": 60,
                    "max_retries": 5
                },
                "monitoring": {
                    "metrics_collection_interval": 15,
                    "health_check_interval": 30,
                    "alert_thresholds": {
                        "memory_usage": 75.0,
                        "error_rate": 0.02,
                        "response_time": 3.0
                    }
                },
                "security": {
                    "audit_logging": True,
                    "data_sanitization": True,
                    "rate_limiting": True
                },
                "degradation": {
                    "auto_recovery": True,
                    "queue_mode_threshold": 120,
                    "memory_threshold": 70.0
                }
            },
            Environment.TESTING.value: {
                "processing": {
                    "batch_size": 1,
                    "timeout_seconds": 180,
                    "retry_attempts": 1,
                    "concurrent_processes": 1
                },
                "database": {
                    "connection_pool_size": 2,
                    "query_timeout": 15,
                    "max_retries": 1
                },
                "monitoring": {
                    "metrics_collection_interval": 120,
                    "health_check_interval": 60,
                    "alert_thresholds": {
                        "memory_usage": 90.0,
                        "error_rate": 0.2,
                        "response_time": 15.0
                    }
                },
                "security": {
                    "audit_logging": False,
                    "data_sanitization": False,
                    "rate_limiting": False
                },
                "degradation": {
                    "auto_recovery": False,
                    "queue_mode_threshold": 600,
                    "memory_threshold": 85.0
                }
            }
        }
    
    def _get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration validation schema"""
        return {
            "type": "object",
            "properties": {
                "processing": {
                    "type": "object",
                    "properties": {
                        "batch_size": {"type": "integer", "minimum": 1, "maximum": 10},
                        "timeout_seconds": {"type": "integer", "minimum": 30, "maximum": 3600},
                        "retry_attempts": {"type": "integer", "minimum": 0, "maximum": 10},
                        "concurrent_processes": {"type": "integer", "minimum": 1, "maximum": 20}
                    },
                    "required": ["batch_size", "timeout_seconds", "retry_attempts", "concurrent_processes"]
                },
                "database": {
                    "type": "object",
                    "properties": {
                        "connection_pool_size": {"type": "integer", "minimum": 1, "maximum": 50},
                        "query_timeout": {"type": "integer", "minimum": 5, "maximum": 300},
                        "max_retries": {"type": "integer", "minimum": 0, "maximum": 10}
                    },
                    "required": ["connection_pool_size", "query_timeout", "max_retries"]
                },
                "monitoring": {
                    "type": "object",
                    "properties": {
                        "metrics_collection_interval": {"type": "integer", "minimum": 10, "maximum": 300},
                        "health_check_interval": {"type": "integer", "minimum": 10, "maximum": 300},
                        "alert_thresholds": {
                            "type": "object",
                            "properties": {
                                "memory_usage": {"type": "number", "minimum": 50.0, "maximum": 95.0},
                                "error_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "response_time": {"type": "number", "minimum": 0.1, "maximum": 60.0}
                            }
                        }
                    }
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "audit_logging": {"type": "boolean"},
                        "data_sanitization": {"type": "boolean"},
                        "rate_limiting": {"type": "boolean"}
                    }
                },
                "degradation": {
                    "type": "object",
                    "properties": {
                        "auto_recovery": {"type": "boolean"},
                        "queue_mode_threshold": {"type": "integer", "minimum": 60, "maximum": 3600},
                        "memory_threshold": {"type": "number", "minimum": 50.0, "maximum": 95.0}
                    }
                }
            },
            "required": ["processing", "database", "monitoring", "security", "degradation"]
        }
    
    def _initialize_configuration_system(self):
        """Initialize configuration management system"""
        try:
            # Load or create default configuration
            self._load_configuration()
            
            # Load validation rules
            self._load_validation_rules()
            
            # Load configuration templates
            self._load_configuration_templates()
            
            # Load change history
            self._load_configuration_history()
            
            # Start monitoring if enabled
            if self.monitoring_enabled:
                self._start_configuration_monitoring()
            
            logger.info("✅ Configuration system initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing configuration system: {e}")
    
    def _load_configuration(self):
        """Load configuration for current environment"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.configurations = json.load(f)
                logger.info(f"📥 Loaded configuration for {self.current_environment.value}")
            else:
                # Use environment defaults
                self.configurations = self.environment_defaults.get(
                    self.current_environment.value, 
                    self.environment_defaults[Environment.DEVELOPMENT.value]
                )
                self._save_configuration()
                logger.info(f"🔧 Created default configuration for {self.current_environment.value}")
            
            # Validate loaded configuration
            self._validate_configuration(self.configurations)
            
        except Exception as e:
            logger.error(f"❌ Error loading configuration: {e}")
            # Fall back to defaults
            self.configurations = self.environment_defaults[Environment.DEVELOPMENT.value]
    
    def _save_configuration(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configurations, f, indent=2)
            
            # Calculate configuration hash for drift detection
            config_hash = hashlib.sha256(
                json.dumps(self.configurations, sort_keys=True).encode()
            ).hexdigest()
            
            # Save hash for monitoring
            hash_file = self.storage_path / f"config_hash_{self.current_environment.value}.txt"
            with open(hash_file, 'w') as f:
                f.write(config_hash)
            
        except Exception as e:
            logger.error(f"❌ Error saving configuration: {e}")
    
    def _load_validation_rules(self):
        """Load configuration validation rules"""
        try:
            if self.validation_rules_file.exists():
                with open(self.validation_rules_file, 'r') as f:
                    self.validation_rules = json.load(f)
            else:
                # Create default validation rules
                self.validation_rules = {
                    "processing.batch_size": {
                        "min": 1,
                        "max": 10,
                        "warning_threshold": 5,
                        "performance_impact": "high"
                    },
                    "database.connection_pool_size": {
                        "min": 1,
                        "max": 50,
                        "recommended_min": 3,
                        "recommended_max": 20
                    },
                    "monitoring.metrics_collection_interval": {
                        "min": 10,
                        "max": 300,
                        "production_max": 60
                    }
                }
                self._save_validation_rules()
            
        except Exception as e:
            logger.error(f"❌ Error loading validation rules: {e}")
    
    def _save_validation_rules(self):
        """Save validation rules to file"""
        try:
            with open(self.validation_rules_file, 'w') as f:
                json.dump(self.validation_rules, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Error saving validation rules: {e}")
    
    def _load_configuration_templates(self):
        """Load configuration templates"""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r') as f:
                    template_data = json.load(f)
                
                for template_info in template_data:
                    template = ConfigurationTemplate(
                        template_id=template_info["template_id"],
                        name=template_info["name"],
                        description=template_info["description"],
                        environment=Environment(template_info["environment"]),
                        load_pattern=template_info["load_pattern"],
                        config_overrides=template_info["config_overrides"],
                        created_at=datetime.fromisoformat(template_info["created_at"]),
                        version=template_info.get("version", "1.0")
                    )
                    self.configuration_templates[template.template_id] = template
            else:
                # Create default templates
                self._create_default_templates()
            
        except Exception as e:
            logger.error(f"❌ Error loading configuration templates: {e}")
    
    def _create_default_templates(self):
        """Create default configuration templates"""
        try:
            templates = [
                {
                    "template_id": "low_load_production",
                    "name": "Low Load Production",
                    "description": "Production configuration for low traffic scenarios",
                    "environment": Environment.PRODUCTION,
                    "load_pattern": "low",
                    "config_overrides": {
                        "processing.concurrent_processes": 3,
                        "database.connection_pool_size": 5,
                        "monitoring.metrics_collection_interval": 30
                    }
                },
                {
                    "template_id": "high_load_production",
                    "name": "High Load Production", 
                    "description": "Production configuration for high traffic scenarios",
                    "environment": Environment.PRODUCTION,
                    "load_pattern": "high",
                    "config_overrides": {
                        "processing.concurrent_processes": 10,
                        "database.connection_pool_size": 20,
                        "monitoring.metrics_collection_interval": 15,
                        "processing.batch_size": 5
                    }
                },
                {
                    "template_id": "auto_scaling_production",
                    "name": "Auto-scaling Production",
                    "description": "Production configuration with auto-scaling support",
                    "environment": Environment.PRODUCTION,
                    "load_pattern": "auto_scaling",
                    "config_overrides": {
                        "processing.concurrent_processes": 8,
                        "database.connection_pool_size": 15,
                        "monitoring.metrics_collection_interval": 10,
                        "degradation.auto_recovery": True,
                        "degradation.memory_threshold": 65.0
                    }
                }
            ]
            
            for template_data in templates:
                template = ConfigurationTemplate(
                    template_id=template_data["template_id"],
                    name=template_data["name"],
                    description=template_data["description"],
                    environment=template_data["environment"],
                    load_pattern=template_data["load_pattern"],
                    config_overrides=template_data["config_overrides"],
                    created_at=datetime.now()
                )
                self.configuration_templates[template.template_id] = template
            
            self._save_configuration_templates()
            
        except Exception as e:
            logger.error(f"❌ Error creating default templates: {e}")
    
    def _save_configuration_templates(self):
        """Save configuration templates to file"""
        try:
            template_data = [
                {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "environment": template.environment.value,
                    "load_pattern": template.load_pattern,
                    "config_overrides": template.config_overrides,
                    "created_at": template.created_at.isoformat(),
                    "version": template.version
                }
                for template in self.configuration_templates.values()
            ]
            
            with open(self.templates_file, 'w') as f:
                json.dump(template_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error saving configuration templates: {e}")
    
    def _load_configuration_history(self):
        """Load configuration change history"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                
                self.configuration_history = [
                    ConfigurationChange(
                        change_id=change["change_id"],
                        change_type=ConfigChangeType(change["change_type"]),
                        environment=Environment(change["environment"]),
                        user_id=change["user_id"],
                        timestamp=datetime.fromisoformat(change["timestamp"]),
                        key_path=change["key_path"],
                        old_value=change["old_value"],
                        new_value=change["new_value"],
                        validation_results=change.get("validation_results", []),
                        applied=change.get("applied", False),
                        rollback_available=change.get("rollback_available", False),
                        metadata=change.get("metadata", {})
                    )
                    for change in history_data
                ]
                
                logger.info(f"📥 Loaded {len(self.configuration_history)} configuration changes")
                
        except Exception as e:
            logger.error(f"❌ Error loading configuration history: {e}")
    
    def _save_configuration_history(self):
        """Save configuration change history"""
        try:
            history_data = [
                {
                    "change_id": change.change_id,
                    "change_type": change.change_type.value,
                    "environment": change.environment.value,
                    "user_id": change.user_id,
                    "timestamp": change.timestamp.isoformat(),
                    "key_path": change.key_path,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "validation_results": change.validation_results,
                    "applied": change.applied,
                    "rollback_available": change.rollback_available,
                    "metadata": change.metadata
                }
                for change in self.configuration_history
            ]
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error saving configuration history: {e}")
    
    def _start_configuration_monitoring(self):
        """Start configuration monitoring thread"""
        try:
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                return
            
            self.monitoring_thread = threading.Thread(
                target=self._configuration_monitoring_loop,
                daemon=True,
                name="config_monitor"
            )
            self.monitoring_thread.start()
            
            logger.info("👀 Configuration monitoring started")
            
        except Exception as e:
            logger.error(f"❌ Error starting configuration monitoring: {e}")
    
    def _configuration_monitoring_loop(self):
        """Configuration monitoring loop"""
        while self.monitoring_enabled:
            try:
                # Check for configuration drift
                self._check_configuration_drift()
                
                # Validate current configuration
                validation_results = self._validate_configuration(self.configurations)
                
                # Check for invalid settings
                if any(not result.valid for result in validation_results):
                    logger.warning("⚠️ Invalid configuration settings detected")
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Error in configuration monitoring: {e}")
                time.sleep(60)
    
    def _check_configuration_drift(self):
        """Check for configuration file changes outside the system"""
        try:
            hash_file = self.storage_path / f"config_hash_{self.current_environment.value}.txt"
            
            if not hash_file.exists():
                return
            
            # Get stored hash
            with open(hash_file, 'r') as f:
                stored_hash = f.read().strip()
            
            # Calculate current hash
            current_hash = hashlib.sha256(
                json.dumps(self.configurations, sort_keys=True).encode()
            ).hexdigest()
            
            if stored_hash != current_hash:
                logger.warning("🔄 Configuration drift detected - reloading configuration")
                self._load_configuration()
                
                # Notify watchers
                self._notify_configuration_change("drift_detected", self.configurations)
                
        except Exception as e:
            logger.error(f"❌ Error checking configuration drift: {e}")
    
    def get_configuration(self, key_path: str = None) -> Any:
        """Get configuration value by key path"""
        try:
            if key_path is None:
                return copy.deepcopy(self.configurations)
            
            # Navigate through nested keys
            keys = key_path.split('.')
            value = self.configurations
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return copy.deepcopy(value)
            
        except Exception as e:
            logger.error(f"❌ Error getting configuration: {e}")
            return None
    
    def set_configuration(self, key_path: str, new_value: Any, user_id: str = "system") -> bool:
        """Set configuration value with validation and change tracking"""
        try:
            # Get current value
            current_value = self.get_configuration(key_path)
            
            # Create proposed configuration
            proposed_config = copy.deepcopy(self.configurations)
            self._set_nested_value(proposed_config, key_path, new_value)
            
            # Validate proposed configuration
            validation_results = self._validate_configuration(proposed_config)
            
            # Check for critical validation errors
            critical_errors = [r for r in validation_results if r.severity == ValidationSeverity.CRITICAL]
            if critical_errors:
                logger.error(f"❌ Configuration change rejected due to critical errors: {[e.message for e in critical_errors]}")
                return False
            
            # Create change record
            change = ConfigurationChange(
                change_id=f"config_change_{int(time.time())}",
                change_type=ConfigChangeType.UPDATE,
                environment=self.current_environment,
                user_id=user_id,
                timestamp=datetime.now(),
                key_path=key_path,
                old_value=current_value,
                new_value=new_value,
                validation_results=[
                    {
                        "key_path": r.key_path,
                        "severity": r.severity.value,
                        "message": r.message,
                        "suggestion": r.suggestion,
                        "valid": r.valid
                    }
                    for r in validation_results
                ],
                applied=False,
                rollback_available=current_value is not None
            )
            
            # Apply configuration change
            self._set_nested_value(self.configurations, key_path, new_value)
            change.applied = True
            
            # Save configuration
            self._save_configuration()
            
            # Add to history
            self.configuration_history.append(change)
            self._save_configuration_history()
            
            # Notify watchers
            self._notify_configuration_change(key_path, new_value)
            
            logger.info(f"🔧 Configuration updated: {key_path} = {new_value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting configuration: {e}")
            return False
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any):
        """Set nested configuration value"""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _validate_configuration(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate configuration against schema and rules"""
        results = []
        
        try:
            # Schema validation (if jsonschema is available)
            if JSONSCHEMA_AVAILABLE:
                try:
                    validate(instance=config, schema=self.configuration_schema, format_checker=draft7_format_checker)
                except ValidationError as e:
                    results.append(ValidationResult(
                        key_path=e.absolute_path[-1] if e.absolute_path else "root",
                        severity=ValidationSeverity.ERROR,
                        message=f"Schema validation error: {e.message}",
                        valid=False
                    ))
            else:
                # Basic validation without jsonschema
                self._basic_schema_validation(config, results)
            
            # Custom validation rules
            for key_path, rule in self.validation_rules.items():
                value = self.get_configuration(key_path)
                if value is not None:
                    rule_results = self._validate_against_rule(key_path, value, rule)
                    results.extend(rule_results)
            
            # Environment-specific validation
            env_results = self._validate_environment_specific(config)
            results.extend(env_results)
            
        except Exception as e:
            logger.error(f"❌ Error during configuration validation: {e}")
            results.append(ValidationResult(
                key_path="system",
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation system error: {str(e)}",
                valid=False
            ))
        
        return results
    
    def _basic_schema_validation(self, config: Dict[str, Any], results: List[ValidationResult]):
        """Basic schema validation without jsonschema"""
        try:
            # Check required sections
            required_sections = ["processing", "database", "monitoring", "security", "degradation"]
            
            for section in required_sections:
                if section not in config:
                    results.append(ValidationResult(
                        key_path=section,
                        severity=ValidationSeverity.ERROR,
                        message=f"Required section '{section}' is missing",
                        valid=False
                    ))
                    continue
                
                # Basic type checking
                if not isinstance(config[section], dict):
                    results.append(ValidationResult(
                        key_path=section,
                        severity=ValidationSeverity.ERROR,
                        message=f"Section '{section}' must be an object",
                        valid=False
                    ))
            
            # Check processing section specifics
            if "processing" in config:
                processing = config["processing"]
                if "batch_size" in processing:
                    batch_size = processing["batch_size"]
                    if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 10:
                        results.append(ValidationResult(
                            key_path="processing.batch_size",
                            severity=ValidationSeverity.ERROR,
                            message="batch_size must be an integer between 1 and 10",
                            valid=False
                        ))
                        
        except Exception as e:
            logger.error(f"❌ Error in basic schema validation: {e}")
    
    def _validate_against_rule(self, key_path: str, value: Any, rule: Dict[str, Any]) -> List[ValidationResult]:
        """Validate value against specific rule"""
        results = []
        
        try:
            # Min/max validation
            if "min" in rule and isinstance(value, (int, float)) and value < rule["min"]:
                results.append(ValidationResult(
                    key_path=key_path,
                    severity=ValidationSeverity.ERROR,
                    message=f"Value {value} is below minimum {rule['min']}",
                    suggestion=f"Set value to at least {rule['min']}",
                    valid=False
                ))
            
            if "max" in rule and isinstance(value, (int, float)) and value > rule["max"]:
                results.append(ValidationResult(
                    key_path=key_path,
                    severity=ValidationSeverity.ERROR,
                    message=f"Value {value} exceeds maximum {rule['max']}",
                    suggestion=f"Set value to at most {rule['max']}",
                    valid=False
                ))
            
            # Warning thresholds
            if "warning_threshold" in rule and isinstance(value, (int, float)) and value > rule["warning_threshold"]:
                results.append(ValidationResult(
                    key_path=key_path,
                    severity=ValidationSeverity.WARNING,
                    message=f"Value {value} exceeds recommended threshold {rule['warning_threshold']}",
                    suggestion=f"Consider reducing value below {rule['warning_threshold']}"
                ))
            
            # Performance impact warnings
            if rule.get("performance_impact") == "high" and isinstance(value, (int, float)) and value > rule.get("warning_threshold", 5):
                results.append(ValidationResult(
                    key_path=key_path,
                    severity=ValidationSeverity.WARNING,
                    message=f"High performance impact setting: {value}",
                    suggestion="Monitor system performance after this change"
                ))
            
        except Exception as e:
            logger.error(f"❌ Error validating against rule: {e}")
        
        return results
    
    def _validate_environment_specific(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate environment-specific constraints"""
        results = []
        
        try:
            if self.current_environment == Environment.PRODUCTION:
                # Production-specific validations
                
                # Check batch size for production
                batch_size = self.get_configuration("processing.batch_size")
                if batch_size and batch_size > 5:
                    results.append(ValidationResult(
                        key_path="processing.batch_size",
                        severity=ValidationSeverity.WARNING,
                        message=f"Large batch size {batch_size} in production may impact performance",
                        suggestion="Consider batch sizes 3-5 for production"
                    ))
                
                # Check metrics collection interval
                metrics_interval = self.get_configuration("monitoring.metrics_collection_interval")
                if metrics_interval and metrics_interval > 60:
                    results.append(ValidationResult(
                        key_path="monitoring.metrics_collection_interval",
                        severity=ValidationSeverity.WARNING,
                        message=f"Long metrics interval {metrics_interval}s may delay issue detection",
                        suggestion="Use intervals ≤60s in production"
                    ))
                
                # Ensure security features are enabled
                if not self.get_configuration("security.audit_logging"):
                    results.append(ValidationResult(
                        key_path="security.audit_logging",
                        severity=ValidationSeverity.CRITICAL,
                        message="Audit logging must be enabled in production",
                        suggestion="Set security.audit_logging to true",
                        valid=False
                    ))
            
            elif self.current_environment == Environment.DEVELOPMENT:
                # Development-specific validations
                
                # Warn about production-level settings in development
                concurrent_processes = self.get_configuration("processing.concurrent_processes")
                if concurrent_processes and concurrent_processes > 3:
                    results.append(ValidationResult(
                        key_path="processing.concurrent_processes",
                        severity=ValidationSeverity.INFO,
                        message=f"High concurrency {concurrent_processes} in development",
                        suggestion="Consider lower values for development environment"
                    ))
            
        except Exception as e:
            logger.error(f"❌ Error in environment-specific validation: {e}")
        
        return results
    
    def apply_template(self, template_id: str, user_id: str = "system") -> bool:
        """Apply configuration template"""
        try:
            if template_id not in self.configuration_templates:
                logger.error(f"❌ Template {template_id} not found")
                return False
            
            template = self.configuration_templates[template_id]
            
            # Check environment compatibility
            if template.environment != self.current_environment:
                logger.warning(f"⚠️ Template {template_id} is for {template.environment.value}, current is {self.current_environment.value}")
            
            # Create backup of current configuration
            backup_config = copy.deepcopy(self.configurations)
            
            # Apply template overrides
            for key_path, value in template.config_overrides.items():
                old_value = self.get_configuration(key_path)
                
                # Create change record
                change = ConfigurationChange(
                    change_id=f"template_{template_id}_{int(time.time())}",
                    change_type=ConfigChangeType.TEMPLATE_APPLY,
                    environment=self.current_environment,
                    user_id=user_id,
                    timestamp=datetime.now(),
                    key_path=key_path,
                    old_value=old_value,
                    new_value=value,
                    applied=True,
                    rollback_available=True,
                    metadata={
                        "template_id": template_id,
                        "template_name": template.name,
                        "load_pattern": template.load_pattern
                    }
                )
                
                # Apply configuration change
                self._set_nested_value(self.configurations, key_path, value)
                self.configuration_history.append(change)
            
            # Validate final configuration
            validation_results = self._validate_configuration(self.configurations)
            critical_errors = [r for r in validation_results if r.severity == ValidationSeverity.CRITICAL]
            
            if critical_errors:
                # Rollback on critical errors
                self.configurations = backup_config
                logger.error(f"❌ Template application failed due to critical errors: {[e.message for e in critical_errors]}")
                return False
            
            # Save configuration
            self._save_configuration()
            self._save_configuration_history()
            
            # Notify watchers
            self._notify_configuration_change("template_applied", template.config_overrides)
            
            logger.info(f"✅ Applied template: {template.name} ({template_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error applying template: {e}")
            return False
    
    def rollback_change(self, change_id: str, user_id: str = "system") -> bool:
        """Rollback a configuration change"""
        try:
            # Find the change
            target_change = None
            for change in self.configuration_history:
                if change.change_id == change_id:
                    target_change = change
                    break
            
            if not target_change:
                logger.error(f"❌ Change {change_id} not found")
                return False
            
            if not target_change.rollback_available:
                logger.error(f"❌ Change {change_id} is not eligible for rollback")
                return False
            
            # Create rollback change record
            rollback_change = ConfigurationChange(
                change_id=f"rollback_{change_id}_{int(time.time())}",
                change_type=ConfigChangeType.ROLLBACK,
                environment=self.current_environment,
                user_id=user_id,
                timestamp=datetime.now(),
                key_path=target_change.key_path,
                old_value=target_change.new_value,
                new_value=target_change.old_value,
                applied=True,
                rollback_available=False,
                metadata={
                    "original_change_id": change_id,
                    "rollback_reason": "manual_rollback"
                }
            )
            
            # Apply rollback
            self._set_nested_value(self.configurations, target_change.key_path, target_change.old_value)
            
            # Save configuration
            self._save_configuration()
            
            # Add rollback to history
            self.configuration_history.append(rollback_change)
            self._save_configuration_history()
            
            # Notify watchers
            self._notify_configuration_change(target_change.key_path, target_change.old_value)
            
            logger.info(f"↩️ Rolled back change: {change_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error rolling back change: {e}")
            return False
    
    def watch_configuration(self, key_path: str, callback: Callable[[str, Any], None]):
        """Register callback for configuration changes"""
        try:
            self.config_watchers[key_path].append(callback)
            logger.debug(f"👀 Registered watcher for {key_path}")
        except Exception as e:
            logger.error(f"❌ Error registering configuration watcher: {e}")
    
    def _notify_configuration_change(self, key_path: str, new_value: Any):
        """Notify configuration watchers of changes"""
        try:
            # Notify specific key watchers
            for callback in self.config_watchers.get(key_path, []):
                try:
                    callback(key_path, new_value)
                except Exception as e:
                    logger.error(f"❌ Error in configuration callback: {e}")
            
            # Notify general change callbacks
            for callback in self.change_callbacks:
                try:
                    callback(key_path, new_value)
                except Exception as e:
                    logger.error(f"❌ Error in configuration change callback: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error notifying configuration change: {e}")
    
    def reload_configuration(self) -> bool:
        """Hot reload configuration from file"""
        try:
            logger.info("🔄 Hot reloading configuration")
            
            # Store current configuration for comparison
            old_config = copy.deepcopy(self.configurations)
            
            # Reload from file
            self._load_configuration()
            
            # Find what changed
            changes = self._compare_configurations(old_config, self.configurations)
            
            # Notify watchers of changes
            for key_path, (old_value, new_value) in changes.items():
                self._notify_configuration_change(key_path, new_value)
            
            logger.info(f"✅ Configuration reloaded with {len(changes)} changes")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error reloading configuration: {e}")
            return False
    
    def _compare_configurations(self, old_config: Dict, new_config: Dict, prefix: str = "") -> Dict[str, Tuple[Any, Any]]:
        """Compare two configurations and return differences"""
        changes = {}
        
        try:
            all_keys = set(old_config.keys()) | set(new_config.keys())
            
            for key in all_keys:
                key_path = f"{prefix}.{key}" if prefix else key
                
                old_value = old_config.get(key)
                new_value = new_config.get(key)
                
                if isinstance(old_value, dict) and isinstance(new_value, dict):
                    # Recursively compare nested dictionaries
                    nested_changes = self._compare_configurations(old_value, new_value, key_path)
                    changes.update(nested_changes)
                elif old_value != new_value:
                    changes[key_path] = (old_value, new_value)
            
        except Exception as e:
            logger.error(f"❌ Error comparing configurations: {e}")
        
        return changes
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get configuration management status"""
        current_time = datetime.now()
        
        # Recent changes (last 24 hours)
        recent_changes = [
            change for change in self.configuration_history
            if change.timestamp > current_time - timedelta(hours=24)
        ]
        
        # Validation status
        validation_results = self._validate_configuration(self.configurations)
        validation_summary = {
            "total_issues": len(validation_results),
            "critical": len([r for r in validation_results if r.severity == ValidationSeverity.CRITICAL]),
            "errors": len([r for r in validation_results if r.severity == ValidationSeverity.ERROR]),
            "warnings": len([r for r in validation_results if r.severity == ValidationSeverity.WARNING]),
            "info": len([r for r in validation_results if r.severity == ValidationSeverity.INFO])
        }
        
        return {
            "environment": self.current_environment.value,
            "monitoring_enabled": self.monitoring_enabled,
            "validation_enabled": self.validation_enabled,
            "hot_reload_enabled": self.hot_reload_enabled,
            "configuration_hash": hashlib.sha256(
                json.dumps(self.configurations, sort_keys=True).encode()
            ).hexdigest()[:16],
            "recent_changes_24h": len(recent_changes),
            "total_changes": len(self.configuration_history),
            "templates_available": len(self.configuration_templates),
            "validation_summary": validation_summary,
            "watchers_registered": sum(len(watchers) for watchers in self.config_watchers.values()),
            "last_updated": current_time.isoformat()
        }
    
    def export_configuration(self, format: str = "json") -> str:
        """Export current configuration"""
        try:
            if format.lower() == "yaml" and YAML_AVAILABLE:
                return yaml.dump(self.configurations, default_flow_style=False)
            else:
                return json.dumps(self.configurations, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error exporting configuration: {e}")
            return ""
    
    def import_configuration(self, config_data: str, format: str = "json", user_id: str = "system") -> bool:
        """Import configuration from string"""
        try:
            if format.lower() == "yaml" and YAML_AVAILABLE:
                imported_config = yaml.safe_load(config_data)
            else:
                imported_config = json.loads(config_data)
            
            # Validate imported configuration
            validation_results = self._validate_configuration(imported_config)
            critical_errors = [r for r in validation_results if r.severity == ValidationSeverity.CRITICAL]
            
            if critical_errors:
                logger.error(f"❌ Import failed due to critical errors: {[e.message for e in critical_errors]}")
                return False
            
            # Create backup and import
            backup_config = copy.deepcopy(self.configurations)
            self.configurations = imported_config
            
            # Save configuration
            self._save_configuration()
            
            # Create change record
            change = ConfigurationChange(
                change_id=f"import_{int(time.time())}",
                change_type=ConfigChangeType.CREATE,
                environment=self.current_environment,
                user_id=user_id,
                timestamp=datetime.now(),
                key_path="root",
                old_value=backup_config,
                new_value=imported_config,
                applied=True,
                rollback_available=True,
                metadata={"import_format": format}
            )
            
            self.configuration_history.append(change)
            self._save_configuration_history()
            
            # Notify watchers
            self._notify_configuration_change("configuration_imported", imported_config)
            
            logger.info(f"✅ Configuration imported from {format}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importing configuration: {e}")
            return False


# Global configuration manager instance
enterprise_configuration_manager = ConfigurationManager()

logger.info("🚀 Enterprise Configuration Manager ready")