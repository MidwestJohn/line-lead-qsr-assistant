#!/usr/bin/env python3
"""
Phase 2C: Data Integrity Verification System
============================================

Comprehensive data integrity verification system that validates Enterprise Bridge
operations after completion with auto-repair capabilities.

Features:
- Integrity checks for entity-relationship consistency
- Visual citation links verification  
- Entity deduplication success validation
- Document completeness verification
- Auto-repair capabilities for minor integrity issues
- Integration as final step in bridge processing workflow

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from reliability_infrastructure import (
    circuit_breaker,
    transaction_manager,
    dead_letter_queue
)

logger = logging.getLogger(__name__)

class IntegrityCheckType(Enum):
    """Types of integrity checks"""
    ENTITY_RELATIONSHIP_CONSISTENCY = "entity_relationship_consistency"
    VISUAL_CITATION_LINKS = "visual_citation_links"
    ENTITY_DEDUPLICATION_SUCCESS = "entity_deduplication_success"
    DOCUMENT_COMPLETENESS = "document_completeness"
    NODE_COUNT_VERIFICATION = "node_count_verification"
    RELATIONSHIP_COUNT_VERIFICATION = "relationship_count_verification"
    ORPHANED_ENTITIES = "orphaned_entities"
    DUPLICATE_RELATIONSHIPS = "duplicate_relationships"
    REFERENTIAL_INTEGRITY = "referential_integrity"

class IntegrityStatus(Enum):
    """Integrity check status"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    REPAIRED = "repaired"

class RepairAction(Enum):
    """Auto-repair actions"""
    DELETE_ORPHANED = "delete_orphaned"
    MERGE_DUPLICATES = "merge_duplicates"
    CREATE_MISSING_LINKS = "create_missing_links"
    UPDATE_REFERENCES = "update_references"
    RESTORE_FROM_BACKUP = "restore_from_backup"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class IntegrityIssue:
    """Integrity issue found during verification"""
    issue_id: str
    check_type: IntegrityCheckType
    severity: str  # "critical", "major", "minor"
    description: str
    affected_entities: List[str]
    suggested_repair: RepairAction
    repair_data: Dict[str, Any] = field(default_factory=dict)
    auto_repairable: bool = True

@dataclass
class IntegrityCheckResult:
    """Result of a single integrity check"""
    check_type: IntegrityCheckType
    status: IntegrityStatus
    message: str
    details: Dict[str, Any]
    issues_found: List[IntegrityIssue] = field(default_factory=list)
    execution_time: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)

@dataclass
class IntegrityReport:
    """Comprehensive integrity verification report"""
    report_id: str
    bridge_operation_id: str
    verification_timestamp: datetime
    overall_status: IntegrityStatus
    check_results: List[IntegrityCheckResult]
    total_issues: int
    critical_issues: int
    repaired_issues: int
    processing_metadata: Dict[str, Any] = field(default_factory=dict)

class DataIntegrityVerificationSystem:
    """
    Comprehensive data integrity verification system that validates all aspects
    of Enterprise Bridge operations and provides auto-repair capabilities.
    """
    
    def __init__(self):
        self.verification_history: List[IntegrityReport] = []
        self.repair_rules: Dict[RepairAction, callable] = {}
        self.check_configurations: Dict[IntegrityCheckType, Dict[str, Any]] = {}
        
        # Storage for verification data
        self.storage_path = Path("data/integrity_verification")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.reports_file = self.storage_path / "verification_reports.json"
        self.config_file = self.storage_path / "verification_config.json"
        
        # Initialize verification system
        self._initialize_check_configurations()
        self._initialize_repair_rules()
        self._load_verification_history()
        
        logger.info("🔍 Data Integrity Verification System initialized")
    
    def _initialize_check_configurations(self):
        """Initialize configuration for each integrity check type"""
        self.check_configurations = {
            IntegrityCheckType.ENTITY_RELATIONSHIP_CONSISTENCY: {
                "timeout": 30,
                "max_orphaned_entities": 5,
                "check_relationship_targets": True,
                "validate_bidirectional": False
            },
            
            IntegrityCheckType.VISUAL_CITATION_LINKS: {
                "timeout": 20,
                "check_file_existence": True,
                "validate_content_hash": True,
                "check_neo4j_nodes": True
            },
            
            IntegrityCheckType.ENTITY_DEDUPLICATION_SUCCESS: {
                "timeout": 25,
                "max_duplicate_threshold": 0.1,  # 10% duplicates allowed
                "check_canonical_names": True,
                "validate_merge_metadata": True
            },
            
            IntegrityCheckType.DOCUMENT_COMPLETENESS: {
                "timeout": 15,
                "check_page_coverage": True,
                "validate_text_extraction": True,
                "minimum_entities_per_page": 1
            },
            
            IntegrityCheckType.NODE_COUNT_VERIFICATION: {
                "timeout": 10,
                "expected_count_tolerance": 0.15,  # 15% tolerance
                "check_node_types": True
            },
            
            IntegrityCheckType.RELATIONSHIP_COUNT_VERIFICATION: {
                "timeout": 10,
                "expected_count_tolerance": 0.2,  # 20% tolerance
                "check_relationship_types": True
            },
            
            IntegrityCheckType.ORPHANED_ENTITIES: {
                "timeout": 20,
                "max_orphaned_percentage": 5.0,  # 5% orphaned allowed
                "exclude_document_nodes": True
            },
            
            IntegrityCheckType.DUPLICATE_RELATIONSHIPS: {
                "timeout": 25,
                "max_duplicate_percentage": 2.0,  # 2% duplicates allowed
                "check_identical_properties": True
            },
            
            IntegrityCheckType.REFERENTIAL_INTEGRITY: {
                "timeout": 30,
                "check_foreign_keys": True,
                "validate_constraint_violations": True
            }
        }
    
    def _initialize_repair_rules(self):
        """Initialize auto-repair rules for different issue types"""
        self.repair_rules = {
            RepairAction.DELETE_ORPHANED: self._repair_delete_orphaned,
            RepairAction.MERGE_DUPLICATES: self._repair_merge_duplicates,
            RepairAction.CREATE_MISSING_LINKS: self._repair_create_missing_links,
            RepairAction.UPDATE_REFERENCES: self._repair_update_references,
            RepairAction.RESTORE_FROM_BACKUP: self._repair_restore_from_backup
        }
    
    def _load_verification_history(self):
        """Load verification history from storage"""
        try:
            if self.reports_file.exists():
                with open(self.reports_file, 'r') as f:
                    reports_data = json.load(f)
                    
                self.verification_history = [
                    IntegrityReport(
                        report_id=report["report_id"],
                        bridge_operation_id=report["bridge_operation_id"],
                        verification_timestamp=datetime.fromisoformat(report["verification_timestamp"]),
                        overall_status=IntegrityStatus(report["overall_status"]),
                        check_results=[
                            IntegrityCheckResult(
                                check_type=IntegrityCheckType(result["check_type"]),
                                status=IntegrityStatus(result["status"]),
                                message=result["message"],
                                details=result["details"],
                                issues_found=[
                                    IntegrityIssue(
                                        issue_id=issue["issue_id"],
                                        check_type=IntegrityCheckType(issue["check_type"]),
                                        severity=issue["severity"],
                                        description=issue["description"],
                                        affected_entities=issue["affected_entities"],
                                        suggested_repair=RepairAction(issue["suggested_repair"]),
                                        repair_data=issue.get("repair_data", {}),
                                        auto_repairable=issue.get("auto_repairable", True)
                                    )
                                    for issue in result.get("issues_found", [])
                                ],
                                execution_time=result.get("execution_time"),
                                recommendations=result.get("recommendations", [])
                            )
                            for result in report["check_results"]
                        ],
                        total_issues=report["total_issues"],
                        critical_issues=report["critical_issues"],
                        repaired_issues=report["repaired_issues"],
                        processing_metadata=report.get("processing_metadata", {})
                    )
                    for report in reports_data
                ]
                
                logger.info(f"📥 Loaded {len(self.verification_history)} verification reports")
                
        except Exception as e:
            logger.error(f"❌ Failed to load verification history: {e}")
    
    def _save_verification_history(self):
        """Save verification history to storage"""
        try:
            reports_data = []
            
            for report in self.verification_history:
                report_data = {
                    "report_id": report.report_id,
                    "bridge_operation_id": report.bridge_operation_id,
                    "verification_timestamp": report.verification_timestamp.isoformat(),
                    "overall_status": report.overall_status.value,
                    "check_results": [
                        {
                            "check_type": result.check_type.value,
                            "status": result.status.value,
                            "message": result.message,
                            "details": result.details,
                            "issues_found": [
                                {
                                    "issue_id": issue.issue_id,
                                    "check_type": issue.check_type.value,
                                    "severity": issue.severity,
                                    "description": issue.description,
                                    "affected_entities": issue.affected_entities,
                                    "suggested_repair": issue.suggested_repair.value,
                                    "repair_data": issue.repair_data,
                                    "auto_repairable": issue.auto_repairable
                                }
                                for issue in result.issues_found
                            ],
                            "execution_time": result.execution_time,
                            "recommendations": result.recommendations
                        }
                        for result in report.check_results
                    ],
                    "total_issues": report.total_issues,
                    "critical_issues": report.critical_issues,
                    "repaired_issues": report.repaired_issues,
                    "processing_metadata": report.processing_metadata
                }
                reports_data.append(report_data)
            
            with open(self.reports_file, 'w') as f:
                json.dump(reports_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save verification history: {e}")
    
    async def verify_bridge_operation(self, bridge_operation_id: str, 
                                    expected_counts: Optional[Dict[str, int]] = None,
                                    auto_repair: bool = True) -> IntegrityReport:
        """
        Perform comprehensive integrity verification of a bridge operation.
        """
        logger.info(f"🔍 Starting integrity verification for operation: {bridge_operation_id}")
        
        report_id = f"integrity_{bridge_operation_id}_{int(datetime.now().timestamp())}"
        verification_start = datetime.now()
        
        try:
            # Use circuit breaker protection for verification
            check_results = await circuit_breaker.call(
                self._execute_all_integrity_checks,
                bridge_operation_id,
                expected_counts
            )
            
            # Calculate issue statistics
            all_issues = []
            for result in check_results:
                all_issues.extend(result.issues_found)
            
            total_issues = len(all_issues)
            critical_issues = len([i for i in all_issues if i.severity == "critical"])
            
            # Perform auto-repair if enabled
            repaired_issues = 0
            if auto_repair and total_issues > 0:
                repaired_issues = await self._perform_auto_repairs(all_issues)
            
            # Determine overall status
            overall_status = self._determine_overall_status(check_results, repaired_issues)
            
            # Create integrity report
            report = IntegrityReport(
                report_id=report_id,
                bridge_operation_id=bridge_operation_id,
                verification_timestamp=verification_start,
                overall_status=overall_status,
                check_results=check_results,
                total_issues=total_issues,
                critical_issues=critical_issues,
                repaired_issues=repaired_issues,
                processing_metadata={
                    "verification_duration": (datetime.now() - verification_start).total_seconds(),
                    "auto_repair_enabled": auto_repair,
                    "expected_counts": expected_counts or {},
                    "checks_performed": len(check_results)
                }
            )
            
            # Save report
            self.verification_history.append(report)
            self._save_verification_history()
            
            logger.info(f"✅ Integrity verification complete: {overall_status.value}")
            logger.info(f"   Issues found: {total_issues} (Critical: {critical_issues}, Repaired: {repaired_issues})")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Integrity verification failed: {e}")
            
            # Add to dead letter queue
            dead_letter_queue.add_failed_operation(
                "integrity_verification",
                {"bridge_operation_id": bridge_operation_id},
                e
            )
            
            # Return error report
            error_report = IntegrityReport(
                report_id=report_id,
                bridge_operation_id=bridge_operation_id,
                verification_timestamp=verification_start,
                overall_status=IntegrityStatus.ERROR,
                check_results=[],
                total_issues=0,
                critical_issues=0,
                repaired_issues=0,
                processing_metadata={"error": str(e)}
            )
            
            return error_report
    
    async def _execute_all_integrity_checks(self, bridge_operation_id: str,
                                          expected_counts: Optional[Dict[str, int]]) -> List[IntegrityCheckResult]:
        """Execute all configured integrity checks"""
        check_results = []
        
        check_functions = {
            IntegrityCheckType.ENTITY_RELATIONSHIP_CONSISTENCY: self._check_entity_relationship_consistency,
            IntegrityCheckType.VISUAL_CITATION_LINKS: self._check_visual_citation_links,
            IntegrityCheckType.ENTITY_DEDUPLICATION_SUCCESS: self._check_entity_deduplication_success,
            IntegrityCheckType.DOCUMENT_COMPLETENESS: self._check_document_completeness,
            IntegrityCheckType.NODE_COUNT_VERIFICATION: self._check_node_count_verification,
            IntegrityCheckType.RELATIONSHIP_COUNT_VERIFICATION: self._check_relationship_count_verification,
            IntegrityCheckType.ORPHANED_ENTITIES: self._check_orphaned_entities,
            IntegrityCheckType.DUPLICATE_RELATIONSHIPS: self._check_duplicate_relationships,
            IntegrityCheckType.REFERENTIAL_INTEGRITY: self._check_referential_integrity
        }
        
        for check_type, check_function in check_functions.items():
            try:
                logger.debug(f"🔍 Running {check_type.value} check")
                
                start_time = datetime.now()
                result = await check_function(bridge_operation_id, expected_counts)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result.execution_time = execution_time
                check_results.append(result)
                
                logger.debug(f"✅ {check_type.value}: {result.status.value} ({execution_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"❌ {check_type.value} check failed: {e}")
                
                error_result = IntegrityCheckResult(
                    check_type=check_type,
                    status=IntegrityStatus.ERROR,
                    message=f"Check failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
                check_results.append(error_result)
        
        return check_results
    
    async def _check_entity_relationship_consistency(self, bridge_operation_id: str,
                                                   expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Check entity-relationship consistency"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Check for relationships pointing to non-existent entities
            orphaned_relationships = await enhanced_neo4j_service.execute_query("""
                MATCH ()-[r]->(target)
                WHERE NOT EXISTS((target))
                RETURN count(r) as orphaned_count, collect(type(r))[0..10] as sample_types
            """)
            
            if orphaned_relationships and orphaned_relationships[0]["orphaned_count"] > 0:
                orphaned_count = orphaned_relationships[0]["orphaned_count"]
                issues.append(IntegrityIssue(
                    issue_id=f"orphaned_rel_{bridge_operation_id}",
                    check_type=IntegrityCheckType.ENTITY_RELATIONSHIP_CONSISTENCY,
                    severity="major",
                    description=f"Found {orphaned_count} relationships pointing to non-existent entities",
                    affected_entities=[],
                    suggested_repair=RepairAction.DELETE_ORPHANED,
                    repair_data={"orphaned_count": orphaned_count}
                ))
            
            # Check for entities without required relationships
            isolated_entities = await enhanced_neo4j_service.execute_query("""
                MATCH (n)
                WHERE NOT EXISTS((n)-[]-())
                RETURN count(n) as isolated_count, collect(labels(n))[0..10] as sample_labels
            """)
            
            isolated_count = isolated_entities[0]["isolated_count"] if isolated_entities else 0
            details["isolated_entities"] = isolated_count
            
            if isolated_count > self.check_configurations[IntegrityCheckType.ENTITY_RELATIONSHIP_CONSISTENCY]["max_orphaned_entities"]:
                issues.append(IntegrityIssue(
                    issue_id=f"isolated_entities_{bridge_operation_id}",
                    check_type=IntegrityCheckType.ENTITY_RELATIONSHIP_CONSISTENCY,
                    severity="minor",
                    description=f"Found {isolated_count} isolated entities without relationships",
                    affected_entities=[],
                    suggested_repair=RepairAction.CREATE_MISSING_LINKS,
                    repair_data={"isolated_count": isolated_count}
                ))
            
            # Determine status
            if any(issue.severity == "critical" for issue in issues):
                status = IntegrityStatus.FAIL
            elif any(issue.severity == "major" for issue in issues):
                status = IntegrityStatus.WARNING
            elif issues:
                status = IntegrityStatus.WARNING
            else:
                status = IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.ENTITY_RELATIONSHIP_CONSISTENCY,
                status=status,
                message=f"Entity-relationship consistency check: {len(issues)} issues found",
                details=details,
                issues_found=issues,
                recommendations=[
                    "Review orphaned relationships for cleanup",
                    "Consider creating missing entity links"
                ] if issues else []
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.ENTITY_RELATIONSHIP_CONSISTENCY,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_visual_citation_links(self, bridge_operation_id: str,
                                         expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Check visual citation links integrity"""
        try:
            from visual_citation_preservation import visual_citation_preservation
            
            # Get visual citation preservation status
            preservation_status = visual_citation_preservation.get_preservation_status()
            
            issues = []
            details = preservation_status
            
            # Check preservation success rate
            total_citations = preservation_status["total_citations"]
            preserved_count = preservation_status["preservation_status_breakdown"].get("preserved", 0)
            
            if total_citations > 0:
                preservation_rate = preserved_count / total_citations
                details["preservation_rate"] = preservation_rate
                
                if preservation_rate < 0.9:  # 90% preservation threshold
                    issues.append(IntegrityIssue(
                        issue_id=f"low_preservation_{bridge_operation_id}",
                        check_type=IntegrityCheckType.VISUAL_CITATION_LINKS,
                        severity="major",
                        description=f"Low visual citation preservation rate: {preservation_rate:.1%}",
                        affected_entities=[],
                        suggested_repair=RepairAction.RESTORE_FROM_BACKUP,
                        repair_data={"preservation_rate": preservation_rate}
                    ))
            
            # Check Neo4j node creation
            neo4j_nodes = preservation_status["neo4j_nodes_created"]
            if neo4j_nodes < preserved_count:
                issues.append(IntegrityIssue(
                    issue_id=f"missing_neo4j_nodes_{bridge_operation_id}",
                    check_type=IntegrityCheckType.VISUAL_CITATION_LINKS,
                    severity="major",
                    description=f"Missing Neo4j nodes: {preserved_count - neo4j_nodes} citations not in Neo4j",
                    affected_entities=[],
                    suggested_repair=RepairAction.CREATE_MISSING_LINKS,
                    repair_data={"missing_nodes": preserved_count - neo4j_nodes}
                ))
            
            # Determine status
            if any(issue.severity == "critical" for issue in issues):
                status = IntegrityStatus.FAIL
            elif any(issue.severity == "major" for issue in issues):
                status = IntegrityStatus.WARNING
            else:
                status = IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.VISUAL_CITATION_LINKS,
                status=status,
                message=f"Visual citation links check: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.VISUAL_CITATION_LINKS,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_entity_deduplication_success(self, bridge_operation_id: str,
                                                expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Check entity deduplication success"""
        try:
            from qsr_entity_deduplication import qsr_entity_deduplication
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Get deduplication statistics
            dedup_stats = qsr_entity_deduplication.get_deduplication_stats()
            details["deduplication_stats"] = dedup_stats
            
            # Check for potential duplicates that weren't caught
            potential_duplicates = await enhanced_neo4j_service.execute_query("""
                MATCH (n1), (n2)
                WHERE id(n1) < id(n2)
                AND n1.canonical_name = n2.canonical_name
                AND n1.canonical_name IS NOT NULL
                RETURN count(*) as duplicate_count,
                       collect(DISTINCT n1.canonical_name)[0..10] as sample_names
            """)
            
            duplicate_count = potential_duplicates[0]["duplicate_count"] if potential_duplicates else 0
            details["potential_duplicates"] = duplicate_count
            
            # Check total entity count for duplicate percentage
            total_entities = await enhanced_neo4j_service.execute_query("""
                MATCH (n) RETURN count(n) as total_count
            """)
            
            total_count = total_entities[0]["total_count"] if total_entities else 0
            
            if total_count > 0:
                duplicate_percentage = (duplicate_count / total_count) * 100
                details["duplicate_percentage"] = duplicate_percentage
                
                max_allowed = self.check_configurations[IntegrityCheckType.ENTITY_DEDUPLICATION_SUCCESS]["max_duplicate_threshold"] * 100
                
                if duplicate_percentage > max_allowed:
                    issues.append(IntegrityIssue(
                        issue_id=f"excess_duplicates_{bridge_operation_id}",
                        check_type=IntegrityCheckType.ENTITY_DEDUPLICATION_SUCCESS,
                        severity="major",
                        description=f"High duplicate percentage: {duplicate_percentage:.1f}% (max allowed: {max_allowed}%)",
                        affected_entities=[],
                        suggested_repair=RepairAction.MERGE_DUPLICATES,
                        repair_data={"duplicate_count": duplicate_count, "duplicate_percentage": duplicate_percentage}
                    ))
            
            # Determine status
            status = IntegrityStatus.FAIL if any(issue.severity == "critical" for issue in issues) else \
                    IntegrityStatus.WARNING if issues else IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.ENTITY_DEDUPLICATION_SUCCESS,
                status=status,
                message=f"Entity deduplication check: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.ENTITY_DEDUPLICATION_SUCCESS,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_document_completeness(self, bridge_operation_id: str,
                                         expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Check document completeness"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Check for documents in database vs Neo4j
            documents_in_db = await enhanced_neo4j_service.execute_query("""
                MATCH (d:Document)
                RETURN count(d) as document_count,
                       collect(d.source_document)[0..10] as sample_documents
            """)
            
            doc_count = documents_in_db[0]["document_count"] if documents_in_db else 0
            details["documents_in_neo4j"] = doc_count
            
            # Load documents from file system for comparison
            try:
                from main import load_documents_db
                file_docs = load_documents_db()
                file_doc_count = len(file_docs)
                details["documents_in_filesystem"] = file_doc_count
                
                # Check for discrepancy
                if abs(doc_count - file_doc_count) > 1:  # Allow for 1 document difference
                    issues.append(IntegrityIssue(
                        issue_id=f"doc_count_mismatch_{bridge_operation_id}",
                        check_type=IntegrityCheckType.DOCUMENT_COMPLETENESS,
                        severity="major",
                        description=f"Document count mismatch: Neo4j={doc_count}, Filesystem={file_doc_count}",
                        affected_entities=[],
                        suggested_repair=RepairAction.UPDATE_REFERENCES,
                        repair_data={"neo4j_count": doc_count, "file_count": file_doc_count}
                    ))
                    
            except Exception as doc_error:
                logger.warning(f"Could not check filesystem documents: {doc_error}")
            
            # Check for entities per document (should have reasonable coverage)
            entity_coverage = await enhanced_neo4j_service.execute_query("""
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[r]-(e)
                WITH d, count(e) as entity_count
                RETURN avg(entity_count) as avg_entities_per_doc,
                       min(entity_count) as min_entities,
                       max(entity_count) as max_entities
            """)
            
            if entity_coverage:
                avg_entities = entity_coverage[0]["avg_entities_per_doc"] or 0
                min_entities = entity_coverage[0]["min_entities"] or 0
                
                details["avg_entities_per_document"] = avg_entities
                details["min_entities_per_document"] = min_entities
                
                min_expected = self.check_configurations[IntegrityCheckType.DOCUMENT_COMPLETENESS]["minimum_entities_per_page"]
                
                if min_entities < min_expected:
                    issues.append(IntegrityIssue(
                        issue_id=f"low_entity_coverage_{bridge_operation_id}",
                        check_type=IntegrityCheckType.DOCUMENT_COMPLETENESS,
                        severity="minor",
                        description=f"Low entity coverage: minimum {min_entities} entities per document (expected: {min_expected})",
                        affected_entities=[],
                        suggested_repair=RepairAction.CREATE_MISSING_LINKS,
                        repair_data={"min_entities": min_entities, "expected": min_expected}
                    ))
            
            # Determine status
            status = IntegrityStatus.FAIL if any(issue.severity == "critical" for issue in issues) else \
                    IntegrityStatus.WARNING if issues else IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.DOCUMENT_COMPLETENESS,
                status=status,
                message=f"Document completeness check: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.DOCUMENT_COMPLETENESS,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_node_count_verification(self, bridge_operation_id: str,
                                           expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Verify node counts against expected values"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Get actual node counts
            actual_counts = await enhanced_neo4j_service.execute_query("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            
            total_actual = sum(result["count"] for result in actual_counts)
            details["actual_total_nodes"] = total_actual
            details["node_breakdown"] = {str(result["labels"]): result["count"] for result in actual_counts}
            
            # Compare with expected counts if provided
            if expected_counts and "total_nodes" in expected_counts:
                expected_total = expected_counts["total_nodes"]
                details["expected_total_nodes"] = expected_total
                
                tolerance = self.check_configurations[IntegrityCheckType.NODE_COUNT_VERIFICATION]["expected_count_tolerance"]
                allowed_variance = expected_total * tolerance
                
                if abs(total_actual - expected_total) > allowed_variance:
                    issues.append(IntegrityIssue(
                        issue_id=f"node_count_variance_{bridge_operation_id}",
                        check_type=IntegrityCheckType.NODE_COUNT_VERIFICATION,
                        severity="major",
                        description=f"Node count variance: expected {expected_total}, actual {total_actual} (tolerance: ±{allowed_variance:.0f})",
                        affected_entities=[],
                        suggested_repair=RepairAction.MANUAL_INTERVENTION,
                        repair_data={"expected": expected_total, "actual": total_actual, "variance": abs(total_actual - expected_total)}
                    ))
            
            # Check for empty database
            if total_actual == 0:
                issues.append(IntegrityIssue(
                    issue_id=f"empty_database_{bridge_operation_id}",
                    check_type=IntegrityCheckType.NODE_COUNT_VERIFICATION,
                    severity="critical",
                    description="Database is empty - no nodes found",
                    affected_entities=[],
                    suggested_repair=RepairAction.RESTORE_FROM_BACKUP,
                    repair_data={"actual_count": 0}
                ))
            
            # Determine status
            status = IntegrityStatus.FAIL if any(issue.severity == "critical" for issue in issues) else \
                    IntegrityStatus.WARNING if issues else IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.NODE_COUNT_VERIFICATION,
                status=status,
                message=f"Node count verification: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.NODE_COUNT_VERIFICATION,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_relationship_count_verification(self, bridge_operation_id: str,
                                                   expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Verify relationship counts against expected values"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Get actual relationship counts
            actual_counts = await enhanced_neo4j_service.execute_query("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
            
            total_actual = sum(result["count"] for result in actual_counts)
            details["actual_total_relationships"] = total_actual
            details["relationship_breakdown"] = {result["relationship_type"]: result["count"] for result in actual_counts}
            
            # Compare with expected counts if provided
            if expected_counts and "total_relationships" in expected_counts:
                expected_total = expected_counts["total_relationships"]
                details["expected_total_relationships"] = expected_total
                
                tolerance = self.check_configurations[IntegrityCheckType.RELATIONSHIP_COUNT_VERIFICATION]["expected_count_tolerance"]
                allowed_variance = expected_total * tolerance
                
                if abs(total_actual - expected_total) > allowed_variance:
                    issues.append(IntegrityIssue(
                        issue_id=f"relationship_count_variance_{bridge_operation_id}",
                        check_type=IntegrityCheckType.RELATIONSHIP_COUNT_VERIFICATION,
                        severity="major",
                        description=f"Relationship count variance: expected {expected_total}, actual {total_actual} (tolerance: ±{allowed_variance:.0f})",
                        affected_entities=[],
                        suggested_repair=RepairAction.MANUAL_INTERVENTION,
                        repair_data={"expected": expected_total, "actual": total_actual, "variance": abs(total_actual - expected_total)}
                    ))
            
            # Determine status
            status = IntegrityStatus.WARNING if issues else IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.RELATIONSHIP_COUNT_VERIFICATION,
                status=status,
                message=f"Relationship count verification: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.RELATIONSHIP_COUNT_VERIFICATION,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_orphaned_entities(self, bridge_operation_id: str,
                                     expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Check for orphaned entities"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Find orphaned entities (no relationships)
            orphaned_query = """
                MATCH (n)
                WHERE NOT (n)-[]-() 
                AND NOT 'Document' IN labels(n)  // Exclude documents as they may legitimately have no relationships
                RETURN count(n) as orphaned_count,
                       collect(DISTINCT labels(n))[0..10] as sample_labels,
                       collect(n.name)[0..10] as sample_names
            """
            
            orphaned_result = await enhanced_neo4j_service.execute_query(orphaned_query)
            orphaned_count = orphaned_result[0]["orphaned_count"] if orphaned_result else 0
            
            details["orphaned_entities"] = orphaned_count
            details["sample_orphaned_labels"] = orphaned_result[0]["sample_labels"] if orphaned_result else []
            
            # Get total entity count for percentage calculation
            total_entities = await enhanced_neo4j_service.execute_query("MATCH (n) RETURN count(n) as total")
            total_count = total_entities[0]["total"] if total_entities else 0
            
            if total_count > 0:
                orphaned_percentage = (orphaned_count / total_count) * 100
                details["orphaned_percentage"] = orphaned_percentage
                
                max_allowed = self.check_configurations[IntegrityCheckType.ORPHANED_ENTITIES]["max_orphaned_percentage"]
                
                if orphaned_percentage > max_allowed:
                    issues.append(IntegrityIssue(
                        issue_id=f"excess_orphaned_{bridge_operation_id}",
                        check_type=IntegrityCheckType.ORPHANED_ENTITIES,
                        severity="minor",
                        description=f"High orphaned entity percentage: {orphaned_percentage:.1f}% (max allowed: {max_allowed}%)",
                        affected_entities=[],
                        suggested_repair=RepairAction.DELETE_ORPHANED,
                        repair_data={"orphaned_count": orphaned_count, "orphaned_percentage": orphaned_percentage}
                    ))
            
            # Determine status
            status = IntegrityStatus.WARNING if issues else IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.ORPHANED_ENTITIES,
                status=status,
                message=f"Orphaned entities check: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.ORPHANED_ENTITIES,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_duplicate_relationships(self, bridge_operation_id: str,
                                           expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Check for duplicate relationships"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Find duplicate relationships (same source, target, type)
            duplicate_query = """
                MATCH (a)-[r1]->(b), (a)-[r2]->(b)
                WHERE id(r1) < id(r2) AND type(r1) = type(r2)
                RETURN count(*) as duplicate_count,
                       collect(DISTINCT type(r1))[0..10] as sample_types
            """
            
            duplicate_result = await enhanced_neo4j_service.execute_query(duplicate_query)
            duplicate_count = duplicate_result[0]["duplicate_count"] if duplicate_result else 0
            
            details["duplicate_relationships"] = duplicate_count
            details["sample_types"] = duplicate_result[0]["sample_types"] if duplicate_result else []
            
            # Get total relationship count for percentage calculation
            total_relationships = await enhanced_neo4j_service.execute_query("MATCH ()-[r]->() RETURN count(r) as total")
            total_count = total_relationships[0]["total"] if total_relationships else 0
            
            if total_count > 0:
                duplicate_percentage = (duplicate_count / total_count) * 100
                details["duplicate_percentage"] = duplicate_percentage
                
                max_allowed = self.check_configurations[IntegrityCheckType.DUPLICATE_RELATIONSHIPS]["max_duplicate_percentage"]
                
                if duplicate_percentage > max_allowed:
                    issues.append(IntegrityIssue(
                        issue_id=f"excess_duplicate_rels_{bridge_operation_id}",
                        check_type=IntegrityCheckType.DUPLICATE_RELATIONSHIPS,
                        severity="major",
                        description=f"High duplicate relationship percentage: {duplicate_percentage:.1f}% (max allowed: {max_allowed}%)",
                        affected_entities=[],
                        suggested_repair=RepairAction.MERGE_DUPLICATES,
                        repair_data={"duplicate_count": duplicate_count, "duplicate_percentage": duplicate_percentage}
                    ))
            
            # Determine status
            status = IntegrityStatus.WARNING if issues else IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.DUPLICATE_RELATIONSHIPS,
                status=status,
                message=f"Duplicate relationships check: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.DUPLICATE_RELATIONSHIPS,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_referential_integrity(self, bridge_operation_id: str,
                                         expected_counts: Optional[Dict[str, int]]) -> IntegrityCheckResult:
        """Check referential integrity constraints"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            issues = []
            details = {}
            
            # Check for relationships with missing source or target properties
            missing_refs = await enhanced_neo4j_service.execute_query("""
                MATCH (a)-[r]->(b)
                WHERE r.source_id IS NOT NULL AND NOT EXISTS((x {id: r.source_id}))
                   OR r.target_id IS NOT NULL AND NOT EXISTS((y {id: r.target_id}))
                RETURN count(r) as missing_ref_count
            """)
            
            missing_count = missing_refs[0]["missing_ref_count"] if missing_refs else 0
            details["missing_references"] = missing_count
            
            if missing_count > 0:
                issues.append(IntegrityIssue(
                    issue_id=f"missing_refs_{bridge_operation_id}",
                    check_type=IntegrityCheckType.REFERENTIAL_INTEGRITY,
                    severity="major",
                    description=f"Found {missing_count} relationships with missing reference targets",
                    affected_entities=[],
                    suggested_repair=RepairAction.UPDATE_REFERENCES,
                    repair_data={"missing_count": missing_count}
                ))
            
            # Check for entities with invalid document references
            invalid_doc_refs = await enhanced_neo4j_service.execute_query("""
                MATCH (e)
                WHERE e.document_id IS NOT NULL 
                AND NOT EXISTS((d:Document {id: e.document_id}))
                RETURN count(e) as invalid_doc_count
            """)
            
            invalid_doc_count = invalid_doc_refs[0]["invalid_doc_count"] if invalid_doc_refs else 0
            details["invalid_document_references"] = invalid_doc_count
            
            if invalid_doc_count > 0:
                issues.append(IntegrityIssue(
                    issue_id=f"invalid_doc_refs_{bridge_operation_id}",
                    check_type=IntegrityCheckType.REFERENTIAL_INTEGRITY,
                    severity="major",
                    description=f"Found {invalid_doc_count} entities with invalid document references",
                    affected_entities=[],
                    suggested_repair=RepairAction.UPDATE_REFERENCES,
                    repair_data={"invalid_count": invalid_doc_count}
                ))
            
            # Determine status
            status = IntegrityStatus.FAIL if any(issue.severity == "critical" for issue in issues) else \
                    IntegrityStatus.WARNING if issues else IntegrityStatus.PASS
            
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.REFERENTIAL_INTEGRITY,
                status=status,
                message=f"Referential integrity check: {len(issues)} issues found",
                details=details,
                issues_found=issues
            )
            
        except Exception as e:
            return IntegrityCheckResult(
                check_type=IntegrityCheckType.REFERENTIAL_INTEGRITY,
                status=IntegrityStatus.ERROR,
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def _determine_overall_status(self, check_results: List[IntegrityCheckResult], 
                                repaired_issues: int) -> IntegrityStatus:
        """Determine overall verification status"""
        
        # Count status types
        failed_checks = len([r for r in check_results if r.status == IntegrityStatus.FAIL])
        error_checks = len([r for r in check_results if r.status == IntegrityStatus.ERROR])
        warning_checks = len([r for r in check_results if r.status == IntegrityStatus.WARNING])
        
        # Determine overall status
        if error_checks > 0:
            return IntegrityStatus.ERROR
        elif failed_checks > 0:
            return IntegrityStatus.FAIL
        elif warning_checks > 0:
            return IntegrityStatus.WARNING if repaired_issues == 0 else IntegrityStatus.REPAIRED
        else:
            return IntegrityStatus.PASS
    
    async def _perform_auto_repairs(self, issues: List[IntegrityIssue]) -> int:
        """Perform automatic repairs for repairable issues"""
        repaired_count = 0
        
        for issue in issues:
            if issue.auto_repairable and issue.suggested_repair in self.repair_rules:
                try:
                    logger.info(f"🔧 Auto-repairing issue: {issue.issue_id}")
                    
                    repair_function = self.repair_rules[issue.suggested_repair]
                    success = await repair_function(issue)
                    
                    if success:
                        repaired_count += 1
                        logger.info(f"✅ Repaired issue: {issue.issue_id}")
                    else:
                        logger.warning(f"⚠️ Failed to repair issue: {issue.issue_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error repairing issue {issue.issue_id}: {e}")
        
        return repaired_count
    
    async def _repair_delete_orphaned(self, issue: IntegrityIssue) -> bool:
        """Delete orphaned entities/relationships"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            if issue.check_type == IntegrityCheckType.ORPHANED_ENTITIES:
                # Delete orphaned entities
                result = await enhanced_neo4j_service.execute_query("""
                    MATCH (n)
                    WHERE NOT (n)-[]-() AND NOT 'Document' IN labels(n)
                    DELETE n
                    RETURN count(n) as deleted_count
                """)
                
                deleted_count = result[0]["deleted_count"] if result else 0
                logger.info(f"🗑️ Deleted {deleted_count} orphaned entities")
                return deleted_count > 0
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to delete orphaned entities: {e}")
            return False
    
    async def _repair_merge_duplicates(self, issue: IntegrityIssue) -> bool:
        """Merge duplicate entities/relationships"""
        try:
            from enhanced_neo4j_service import enhanced_neo4j_service
            
            if issue.check_type == IntegrityCheckType.DUPLICATE_RELATIONSHIPS:
                # Delete duplicate relationships
                result = await enhanced_neo4j_service.execute_query("""
                    MATCH (a)-[r1]->(b), (a)-[r2]->(b)
                    WHERE id(r1) < id(r2) AND type(r1) = type(r2)
                    DELETE r2
                    RETURN count(r2) as deleted_count
                """)
                
                deleted_count = result[0]["deleted_count"] if result else 0
                logger.info(f"🔗 Deleted {deleted_count} duplicate relationships")
                return deleted_count > 0
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to merge duplicates: {e}")
            return False
    
    async def _repair_create_missing_links(self, issue: IntegrityIssue) -> bool:
        """Create missing links/relationships"""
        # This would require more complex logic to determine what links should be created
        logger.info(f"🔗 Creating missing links repair not implemented for issue: {issue.issue_id}")
        return False
    
    async def _repair_update_references(self, issue: IntegrityIssue) -> bool:
        """Update invalid references"""
        # This would require complex logic to determine correct references
        logger.info(f"📝 Update references repair not implemented for issue: {issue.issue_id}")
        return False
    
    async def _repair_restore_from_backup(self, issue: IntegrityIssue) -> bool:
        """Restore data from backup"""
        # This would require backup system integration
        logger.info(f"💾 Restore from backup repair not implemented for issue: {issue.issue_id}")
        return False
    
    def get_verification_summary(self, limit: int = 10) -> Dict[str, Any]:
        """Get summary of recent verification results"""
        recent_reports = sorted(self.verification_history, 
                              key=lambda r: r.verification_timestamp, 
                              reverse=True)[:limit]
        
        if not recent_reports:
            return {
                "recent_reports": [],
                "summary_stats": {"total_reports": 0},
                "overall_health": "no_data"
            }
        
        # Calculate summary statistics
        total_reports = len(recent_reports)
        passed_reports = len([r for r in recent_reports if r.overall_status == IntegrityStatus.PASS])
        failed_reports = len([r for r in recent_reports if r.overall_status == IntegrityStatus.FAIL])
        
        success_rate = (passed_reports / total_reports) * 100 if total_reports > 0 else 0
        
        # Determine overall health
        if success_rate >= 90:
            overall_health = "excellent"
        elif success_rate >= 70:
            overall_health = "good"
        elif success_rate >= 50:
            overall_health = "fair"
        else:
            overall_health = "poor"
        
        return {
            "recent_reports": [
                {
                    "report_id": report.report_id,
                    "bridge_operation_id": report.bridge_operation_id,
                    "verification_timestamp": report.verification_timestamp.isoformat(),
                    "overall_status": report.overall_status.value,
                    "total_issues": report.total_issues,
                    "critical_issues": report.critical_issues,
                    "repaired_issues": report.repaired_issues
                }
                for report in recent_reports
            ],
            "summary_stats": {
                "total_reports": total_reports,
                "passed_reports": passed_reports,
                "failed_reports": failed_reports,
                "success_rate": success_rate
            },
            "overall_health": overall_health,
            "last_updated": datetime.now().isoformat()
        }


# Global instance
data_integrity_verification = DataIntegrityVerificationSystem()

logger.info("🚀 Data Integrity Verification System ready")