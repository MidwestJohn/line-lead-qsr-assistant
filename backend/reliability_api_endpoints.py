#!/usr/bin/env python3
"""
Reliability API Endpoints for 99%+ Upload-to-Retrieval Pipeline
===============================================================

API endpoints that expose the reliability infrastructure:
- Circuit breaker monitoring and control
- Transaction management and status
- Dead letter queue management
- Reliable upload pipeline with real-time tracking
- Comprehensive health checks and diagnostics

These endpoints provide full visibility and control over the reliability
infrastructure while maintaining seamless integration with existing features.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from reliability_infrastructure import (
    circuit_breaker,
    transaction_manager,
    dead_letter_queue,
    CircuitBreakerOpenError
)
from enhanced_neo4j_service import enhanced_neo4j_service
from reliable_upload_pipeline import reliable_upload_pipeline

logger = logging.getLogger(__name__)

# ============================================================================
# Request/Response Models
# ============================================================================

class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status response"""
    name: str
    state: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    failure_rate: float
    consecutive_failures: int
    consecutive_successes: int
    last_failure_time: Optional[str]
    last_success_time: Optional[str]
    state_changes: int

class TransactionStatus(BaseModel):
    """Transaction status response"""
    transaction_id: str
    start_time: str
    end_time: Optional[str]
    operations_count: int
    operations_executed: int
    completed: bool
    committed: bool
    rolled_back: bool
    error: Optional[str]

class DeadLetterQueueStatus(BaseModel):
    """Dead letter queue status response"""
    failed_operations: int
    manual_review_queue: int
    ready_for_retry: int
    processing_enabled: bool
    background_processor_running: bool

class ReliabilityHealthCheck(BaseModel):
    """Comprehensive reliability health check"""
    overall_status: str
    circuit_breaker: CircuitBreakerStatus
    transaction_manager: Dict[str, Any]
    dead_letter_queue: DeadLetterQueueStatus
    neo4j_connection: Dict[str, Any]
    pipeline_statistics: Dict[str, Any]
    recommendations: List[str]

class ProcessingStatusResponse(BaseModel):
    """Real-time processing status"""
    process_id: str
    filename: str
    document_id: str
    active: bool
    success: bool
    current_stage: str
    progress_percent: float
    stages: List[Dict[str, Any]]
    entities_created: int
    relationships_created: int
    total_duration: float
    error_details: Optional[Dict[str, Any]]
    recovery_actions: List[str]
    reliability_status: Dict[str, Any]

class ManualReviewOperation(BaseModel):
    """Manual review operation"""
    operation_id: str
    operation_type: str
    error_message: str
    error_type: str
    failure_time: str
    retry_count: int
    operation_data: Dict[str, Any]

# ============================================================================
# API Router
# ============================================================================

reliability_router = APIRouter(prefix="/api/v3/reliability", tags=["Reliability Infrastructure"])

# ============================================================================
# Circuit Breaker Endpoints
# ============================================================================

@reliability_router.get("/circuit-breaker/status", response_model=CircuitBreakerStatus)
async def get_circuit_breaker_status():
    """Get current circuit breaker status and metrics"""
    try:
        metrics = circuit_breaker.get_metrics()
        return CircuitBreakerStatus(**metrics)
    except Exception as e:
        logger.error(f"❌ Failed to get circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.post("/circuit-breaker/reset")
async def reset_circuit_breaker():
    """Manually reset circuit breaker to CLOSED state"""
    try:
        circuit_breaker.reset()
        return {
            "success": True,
            "message": "Circuit breaker reset to CLOSED state",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to reset circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.post("/circuit-breaker/test")
async def test_circuit_breaker():
    """Test circuit breaker with a controlled operation"""
    try:
        # Test with a simple Neo4j operation
        result = await circuit_breaker.call(
            enhanced_neo4j_service.execute_query,
            "RETURN 'Circuit breaker test' as message, timestamp() as time"
        )
        
        return {
            "success": True,
            "message": "Circuit breaker test passed",
            "result": result,
            "circuit_breaker_state": circuit_breaker.state.value,
            "timestamp": datetime.now().isoformat()
        }
    except CircuitBreakerOpenError:
        return {
            "success": False,
            "message": "Circuit breaker is OPEN",
            "circuit_breaker_state": circuit_breaker.state.value,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Circuit breaker test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Transaction Management Endpoints
# ============================================================================

@reliability_router.get("/transactions/active")
async def get_active_transactions():
    """Get all active transactions"""
    try:
        active_transactions = []
        for transaction_id, transaction in transaction_manager.active_transactions.items():
            status = transaction_manager.get_transaction_status(transaction_id)
            active_transactions.append(status)
        
        return {
            "active_transactions": active_transactions,
            "count": len(active_transactions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get active transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.get("/transactions/{transaction_id}", response_model=TransactionStatus)
async def get_transaction_status(transaction_id: str):
    """Get status of specific transaction"""
    try:
        status = transaction_manager.get_transaction_status(transaction_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return TransactionStatus(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get transaction status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.post("/transactions/{transaction_id}/rollback")
async def rollback_transaction(transaction_id: str):
    """Manually rollback a transaction"""
    try:
        success = await transaction_manager.rollback_transaction(transaction_id)
        
        return {
            "success": success,
            "transaction_id": transaction_id,
            "message": "Transaction rolled back successfully" if success else "Rollback failed",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to rollback transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Dead Letter Queue Endpoints
# ============================================================================

@reliability_router.get("/dead-letter-queue/status", response_model=DeadLetterQueueStatus)
async def get_dead_letter_queue_status():
    """Get dead letter queue status"""
    try:
        status = dead_letter_queue.get_queue_status()
        return DeadLetterQueueStatus(**status)
    except Exception as e:
        logger.error(f"❌ Failed to get dead letter queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.get("/dead-letter-queue/manual-review", response_model=List[ManualReviewOperation])
async def get_manual_review_operations():
    """Get operations requiring manual review"""
    try:
        operations = dead_letter_queue.get_manual_review_operations()
        return [ManualReviewOperation(**op) for op in operations]
    except Exception as e:
        logger.error(f"❌ Failed to get manual review operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.post("/dead-letter-queue/manual-review/{operation_id}/resolve")
async def resolve_manual_review_operation(operation_id: str, resolution: str):
    """Resolve manual review operation"""
    try:
        success = dead_letter_queue.resolve_manual_operation(operation_id, resolution)
        
        if not success:
            raise HTTPException(status_code=404, detail="Operation not found")
        
        return {
            "success": True,
            "operation_id": operation_id,
            "resolution": resolution,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resolve manual review operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.post("/dead-letter-queue/retry-all")
async def retry_all_failed_operations():
    """Manually trigger retry of all ready operations"""
    try:
        # This will trigger the background processor to check all operations
        dead_letter_queue._process_ready_operations()
        
        status = dead_letter_queue.get_queue_status()
        
        return {
            "success": True,
            "message": "Retry triggered for all ready operations",
            "queue_status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to retry failed operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Reliable Upload Pipeline Endpoints
# ============================================================================

@reliability_router.post("/upload")
async def reliable_upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload file through reliable pipeline with 99%+ success rate"""
    try:
        result = await reliable_upload_pipeline.process_upload(file, background_tasks)
        return result
    except Exception as e:
        logger.error(f"❌ Reliable upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.get("/upload/status/{process_id}", response_model=ProcessingStatusResponse)
async def get_upload_status(process_id: str):
    """Get real-time upload processing status"""
    try:
        status = reliable_upload_pipeline.get_process_status(process_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return ProcessingStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get upload status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.get("/upload/statistics")
async def get_upload_statistics():
    """Get upload pipeline statistics"""
    try:
        stats = reliable_upload_pipeline.get_pipeline_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to get upload statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Comprehensive Health Check Endpoints
# ============================================================================

@reliability_router.get("/health", response_model=ReliabilityHealthCheck)
async def comprehensive_health_check():
    """Comprehensive reliability health check"""
    try:
        # Circuit breaker status
        cb_metrics = circuit_breaker.get_metrics()
        cb_status = CircuitBreakerStatus(**cb_metrics)
        
        # Transaction manager status
        tm_status = {
            "active_transactions": len(transaction_manager.active_transactions),
            "total_history": len(transaction_manager.transaction_history)
        }
        
        # Dead letter queue status
        dlq_status_data = dead_letter_queue.get_queue_status()
        dlq_status = DeadLetterQueueStatus(**dlq_status_data)
        
        # Neo4j connection status
        neo4j_status = await enhanced_neo4j_service.get_health_status()
        
        # Pipeline statistics
        pipeline_stats = reliable_upload_pipeline.get_pipeline_statistics()
        
        # Determine overall status
        issues = []
        if cb_status.state != "closed":
            issues.append("Circuit breaker not closed")
        if not neo4j_status.get("healthy", False):
            issues.append("Neo4j connection unhealthy")
        if dlq_status.failed_operations > 10:
            issues.append("High number of failed operations")
        if pipeline_stats.get("success_rate", 0) < 90:
            issues.append("Low pipeline success rate")
        
        overall_status = "healthy" if not issues else "degraded" if len(issues) <= 2 else "critical"
        
        # Generate recommendations
        recommendations = []
        if cb_status.state == "open":
            recommendations.append("Reset circuit breaker if Neo4j is available")
        if dlq_status.failed_operations > 0:
            recommendations.append("Review and resolve failed operations")
        if not neo4j_status.get("connected", False):
            recommendations.append("Check Neo4j connection and credentials")
        if pipeline_stats.get("success_rate", 100) < 95:
            recommendations.append("Investigate pipeline failures")
        
        return ReliabilityHealthCheck(
            overall_status=overall_status,
            circuit_breaker=cb_status,
            transaction_manager=tm_status,
            dead_letter_queue=dlq_status,
            neo4j_connection=neo4j_status,
            pipeline_statistics=pipeline_stats,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.get("/health/summary")
async def health_summary():
    """Quick health summary for dashboard"""
    try:
        cb_metrics = circuit_breaker.get_metrics()
        dlq_status = dead_letter_queue.get_queue_status()
        pipeline_stats = reliable_upload_pipeline.get_pipeline_statistics()
        neo4j_status = await enhanced_neo4j_service.get_health_status()
        
        return {
            "overall_healthy": (
                cb_metrics["state"] == "closed" and
                neo4j_status.get("healthy", False) and
                dlq_status["failed_operations"] < 10 and
                pipeline_stats.get("success_rate", 0) >= 90
            ),
            "circuit_breaker_state": cb_metrics["state"],
            "neo4j_connected": neo4j_status.get("connected", False),
            "failed_operations": dlq_status["failed_operations"],
            "pipeline_success_rate": pipeline_stats.get("success_rate", 0),
            "active_uploads": pipeline_stats.get("active_processes", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Health summary failed: {e}")
        return {
            "overall_healthy": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# Diagnostic and Testing Endpoints
# ============================================================================

@reliability_router.post("/test/end-to-end")
async def test_end_to_end_reliability():
    """Test end-to-end reliability features"""
    try:
        results = {}
        
        # Test circuit breaker
        try:
            await circuit_breaker.call(
                enhanced_neo4j_service.execute_query,
                "RETURN 'test' as result"
            )
            results["circuit_breaker"] = {"status": "passed", "state": circuit_breaker.state.value}
        except Exception as e:
            results["circuit_breaker"] = {"status": "failed", "error": str(e)}
        
        # Test transaction manager
        try:
            transaction = transaction_manager.begin_transaction("test_e2e")
            await transaction_manager.rollback_transaction(transaction.transaction_id)
            results["transaction_manager"] = {"status": "passed"}
        except Exception as e:
            results["transaction_manager"] = {"status": "failed", "error": str(e)}
        
        # Test dead letter queue
        try:
            op_id = dead_letter_queue.add_failed_operation(
                "test_operation",
                {"test": "data"},
                Exception("Test error")
            )
            results["dead_letter_queue"] = {"status": "passed", "operation_id": op_id}
        except Exception as e:
            results["dead_letter_queue"] = {"status": "failed", "error": str(e)}
        
        # Test Neo4j service
        try:
            health = await enhanced_neo4j_service.get_health_status()
            results["neo4j_service"] = {"status": "passed" if health.get("healthy") else "failed", "health": health}
        except Exception as e:
            results["neo4j_service"] = {"status": "failed", "error": str(e)}
        
        # Overall result
        all_passed = all(result.get("status") == "passed" for result in results.values())
        
        return {
            "overall_result": "passed" if all_passed else "failed",
            "component_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ End-to-end test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.post("/test/simulate-failure")
async def simulate_failure(failure_type: str = "circuit_breaker"):
    """Simulate different types of failures for testing"""
    try:
        if failure_type == "circuit_breaker":
            # Force circuit breaker failures
            for _ in range(6):  # Exceed threshold
                try:
                    await circuit_breaker.call(lambda: (_ for _ in ()).throw(Exception("Simulated failure")))
                except:
                    pass
            
            return {
                "success": True,
                "message": "Circuit breaker failure simulated",
                "circuit_breaker_state": circuit_breaker.state.value
            }
        
        elif failure_type == "transaction":
            # Create and rollback transaction
            transaction = transaction_manager.begin_transaction("simulated_failure")
            await transaction_manager.rollback_transaction(transaction.transaction_id)
            
            return {
                "success": True,
                "message": "Transaction failure simulated",
                "transaction_id": transaction.transaction_id
            }
        
        elif failure_type == "dead_letter":
            # Add failed operation
            op_id = dead_letter_queue.add_failed_operation(
                "simulated_failure",
                {"simulation": True},
                Exception("Simulated failure for testing")
            )
            
            return {
                "success": True,
                "message": "Dead letter queue failure simulated",
                "operation_id": op_id
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid failure type")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failure simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Metrics and Monitoring Endpoints
# ============================================================================

@reliability_router.get("/metrics")
async def get_reliability_metrics():
    """Get comprehensive reliability metrics for monitoring"""
    try:
        return {
            "circuit_breaker": circuit_breaker.get_metrics(),
            "transaction_manager": {
                "active_transactions": len(transaction_manager.active_transactions),
                "total_history": len(transaction_manager.transaction_history)
            },
            "dead_letter_queue": dead_letter_queue.get_queue_status(),
            "pipeline": reliable_upload_pipeline.get_pipeline_statistics(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get reliability metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reliability_router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get metrics in Prometheus format"""
    try:
        cb_metrics = circuit_breaker.get_metrics()
        dlq_status = dead_letter_queue.get_queue_status()
        pipeline_stats = reliable_upload_pipeline.get_pipeline_statistics()
        
        prometheus_metrics = f"""
# HELP circuit_breaker_requests_total Total number of requests through circuit breaker
# TYPE circuit_breaker_requests_total counter
circuit_breaker_requests_total{{state="total"}} {cb_metrics['total_requests']}
circuit_breaker_requests_total{{state="successful"}} {cb_metrics['successful_requests']}
circuit_breaker_requests_total{{state="failed"}} {cb_metrics['failed_requests']}

# HELP circuit_breaker_state Current state of circuit breaker (0=closed, 1=half_open, 2=open)
# TYPE circuit_breaker_state gauge
circuit_breaker_state {0 if cb_metrics['state'] == 'closed' else 1 if cb_metrics['state'] == 'half_open' else 2}

# HELP dead_letter_queue_operations Operations in dead letter queue
# TYPE dead_letter_queue_operations gauge
dead_letter_queue_operations{{state="failed"}} {dlq_status['failed_operations']}
dead_letter_queue_operations{{state="manual_review"}} {dlq_status['manual_review_queue']}

# HELP pipeline_success_rate Success rate of upload pipeline
# TYPE pipeline_success_rate gauge
pipeline_success_rate {pipeline_stats.get('success_rate', 0) / 100}

# HELP pipeline_active_processes Active upload processes
# TYPE pipeline_active_processes gauge
pipeline_active_processes {pipeline_stats.get('active_processes', 0)}
        """.strip()
        
        return prometheus_metrics
        
    except Exception as e:
        logger.error(f"❌ Failed to generate Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("🚀 Reliability API endpoints initialized")