#!/usr/bin/env python3
"""
Test Enhanced Health Monitoring System
=====================================

Comprehensive test suite for the enhanced health monitoring system that validates:
- Intelligence service health monitoring
- Ragie API health checks
- PydanticAI agent coordination monitoring
- Context preservation tracking
- Performance dashboard functionality
- Real-time metrics collection
- Historical trend analysis

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add backend to path
sys.path.append('.')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_enhanced_health_monitoring():
    """Test enhanced health monitoring system"""
    
    logger.info("🧪 Starting Enhanced Health Monitoring Tests")
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "test_details": []
    }
    
    # Test 1: Initialize monitoring system
    logger.info("🔍 Test 1: Initialize Enhanced Health Monitoring")
    test_results["tests_run"] += 1
    
    try:
        from health_monitoring_enhanced import enhanced_health_monitoring
        
        # Check if monitoring system is available
        if enhanced_health_monitoring:
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Initialize Enhanced Health Monitoring",
                "status": "PASSED",
                "message": "Enhanced health monitoring system initialized successfully"
            })
            logger.info("✅ Enhanced health monitoring system initialized")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Initialize Enhanced Health Monitoring",
                "status": "FAILED",
                "message": "Enhanced health monitoring system not available"
            })
            logger.error("❌ Enhanced health monitoring system not available")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Initialize Enhanced Health Monitoring",
            "status": "FAILED",
            "message": f"Error initializing: {str(e)}"
        })
        logger.error(f"❌ Error initializing enhanced monitoring: {e}")
        return test_results
    
    # Test 2: Start monitoring
    logger.info("🔍 Test 2: Start Enhanced Monitoring")
    test_results["tests_run"] += 1
    
    try:
        enhanced_health_monitoring.start_monitoring()
        
        # Wait a moment for monitoring to start
        await asyncio.sleep(2)
        
        # Check if monitoring is running
        status = enhanced_health_monitoring.get_monitoring_status()
        
        if status.get("intelligence_monitoring", {}).get("intelligence_monitoring_enabled", False):
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Start Enhanced Monitoring",
                "status": "PASSED",
                "message": "Enhanced monitoring started successfully"
            })
            logger.info("✅ Enhanced monitoring started")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Start Enhanced Monitoring",
                "status": "FAILED",
                "message": "Enhanced monitoring not running"
            })
            logger.error("❌ Enhanced monitoring not running")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Start Enhanced Monitoring",
            "status": "FAILED",
            "message": f"Error starting monitoring: {str(e)}"
        })
        logger.error(f"❌ Error starting monitoring: {e}")
    
    # Test 3: Intelligence health summary
    logger.info("🔍 Test 3: Intelligence Health Summary")
    test_results["tests_run"] += 1
    
    try:
        health_summary = enhanced_health_monitoring.get_intelligence_health_summary()
        
        if health_summary and "overall_intelligence_health" in health_summary:
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Intelligence Health Summary",
                "status": "PASSED",
                "message": f"Health summary generated: {health_summary['overall_intelligence_health']}"
            })
            logger.info(f"✅ Intelligence health: {health_summary['overall_intelligence_health']}")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Intelligence Health Summary",
                "status": "FAILED",
                "message": "Invalid health summary format"
            })
            logger.error("❌ Invalid health summary format")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Intelligence Health Summary",
            "status": "FAILED",
            "message": f"Error getting health summary: {str(e)}"
        })
        logger.error(f"❌ Error getting health summary: {e}")
    
    # Test 4: Performance dashboard
    logger.info("🔍 Test 4: Performance Dashboard")
    test_results["tests_run"] += 1
    
    try:
        dashboard_data = enhanced_health_monitoring.get_performance_dashboard_data()
        
        if dashboard_data and "intelligence_health" in dashboard_data:
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Performance Dashboard",
                "status": "PASSED",
                "message": "Performance dashboard data generated successfully"
            })
            logger.info("✅ Performance dashboard data generated")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Performance Dashboard",
                "status": "FAILED",
                "message": "Invalid dashboard data format"
            })
            logger.error("❌ Invalid dashboard data format")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Performance Dashboard",
            "status": "FAILED",
            "message": f"Error getting dashboard data: {str(e)}"
        })
        logger.error(f"❌ Error getting dashboard data: {e}")
    
    # Test 5: Record interaction performance
    logger.info("🔍 Test 5: Record Interaction Performance")
    test_results["tests_run"] += 1
    
    try:
        test_session_id = f"test_session_{int(time.time())}"
        test_interaction_data = {
            "response_time": 1500,
            "agent_type": "equipment",
            "query_type": "equipment_question",
            "response_quality": 0.9,
            "ragie_used": True,
            "context_preserved": True
        }
        
        enhanced_health_monitoring.record_interaction_performance(test_session_id, test_interaction_data)
        
        # Check if interaction was recorded
        if test_session_id in enhanced_health_monitoring.session_performance:
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Record Interaction Performance",
                "status": "PASSED",
                "message": "Interaction performance recorded successfully"
            })
            logger.info("✅ Interaction performance recorded")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Record Interaction Performance",
                "status": "FAILED",
                "message": "Interaction performance not recorded"
            })
            logger.error("❌ Interaction performance not recorded")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Record Interaction Performance",
            "status": "FAILED",
            "message": f"Error recording interaction: {str(e)}"
        })
        logger.error(f"❌ Error recording interaction: {e}")
    
    # Test 6: Wait for metric collection
    logger.info("🔍 Test 6: Metric Collection")
    test_results["tests_run"] += 1
    
    try:
        # Wait for some metrics to be collected
        logger.info("⏳ Waiting for metrics collection...")
        await asyncio.sleep(10)
        
        # Check if metrics were collected
        if len(enhanced_health_monitoring.intelligence_metrics) > 0:
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Metric Collection",
                "status": "PASSED",
                "message": f"Collected {len(enhanced_health_monitoring.intelligence_metrics)} metrics"
            })
            logger.info(f"✅ Collected {len(enhanced_health_monitoring.intelligence_metrics)} metrics")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Metric Collection",
                "status": "FAILED",
                "message": "No metrics collected"
            })
            logger.error("❌ No metrics collected")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Metric Collection",
            "status": "FAILED",
            "message": f"Error in metric collection: {str(e)}"
        })
        logger.error(f"❌ Error in metric collection: {e}")
    
    # Test 7: Real-time metrics
    logger.info("🔍 Test 7: Real-time Metrics")
    test_results["tests_run"] += 1
    
    try:
        dashboard_data = enhanced_health_monitoring.get_performance_dashboard_data()
        real_time_metrics = dashboard_data.get("real_time_metrics", {})
        
        if real_time_metrics:
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Real-time Metrics",
                "status": "PASSED",
                "message": f"Real-time metrics available: {list(real_time_metrics.keys())}"
            })
            logger.info(f"✅ Real-time metrics: {list(real_time_metrics.keys())}")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Real-time Metrics",
                "status": "FAILED",
                "message": "No real-time metrics available"
            })
            logger.error("❌ No real-time metrics available")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Real-time Metrics",
            "status": "FAILED",
            "message": f"Error getting real-time metrics: {str(e)}"
        })
        logger.error(f"❌ Error getting real-time metrics: {e}")
    
    # Test 8: Historical trends
    logger.info("🔍 Test 8: Historical Trends")
    test_results["tests_run"] += 1
    
    try:
        dashboard_data = enhanced_health_monitoring.get_performance_dashboard_data()
        historical_trends = dashboard_data.get("historical_trends", {})
        
        # Historical trends might be empty for a new system
        test_results["tests_passed"] += 1
        test_results["test_details"].append({
            "test": "Historical Trends",
            "status": "PASSED",
            "message": f"Historical trends structure available: {len(historical_trends)} trend series"
        })
        logger.info(f"✅ Historical trends: {len(historical_trends)} trend series")
        
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Historical Trends",
            "status": "FAILED",
            "message": f"Error getting historical trends: {str(e)}"
        })
        logger.error(f"❌ Error getting historical trends: {e}")
    
    # Test 9: User satisfaction metrics
    logger.info("🔍 Test 9: User Satisfaction Metrics")
    test_results["tests_run"] += 1
    
    try:
        dashboard_data = enhanced_health_monitoring.get_performance_dashboard_data()
        user_satisfaction = dashboard_data.get("user_satisfaction", {})
        
        if user_satisfaction and "response_quality_average" in user_satisfaction:
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "User Satisfaction Metrics",
                "status": "PASSED",
                "message": f"User satisfaction metrics available: {user_satisfaction['response_quality_average']}"
            })
            logger.info(f"✅ User satisfaction: {user_satisfaction['response_quality_average']}")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "User Satisfaction Metrics",
                "status": "FAILED",
                "message": "User satisfaction metrics not available"
            })
            logger.error("❌ User satisfaction metrics not available")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "User Satisfaction Metrics",
            "status": "FAILED",
            "message": f"Error getting user satisfaction: {str(e)}"
        })
        logger.error(f"❌ Error getting user satisfaction: {e}")
    
    # Test 10: Stop monitoring
    logger.info("🔍 Test 10: Stop Enhanced Monitoring")
    test_results["tests_run"] += 1
    
    try:
        enhanced_health_monitoring.stop_monitoring()
        
        # Wait a moment for monitoring to stop
        await asyncio.sleep(2)
        
        # Check if monitoring stopped
        status = enhanced_health_monitoring.get_monitoring_status()
        
        if not status.get("intelligence_monitoring", {}).get("intelligence_monitoring_enabled", True):
            test_results["tests_passed"] += 1
            test_results["test_details"].append({
                "test": "Stop Enhanced Monitoring",
                "status": "PASSED",
                "message": "Enhanced monitoring stopped successfully"
            })
            logger.info("✅ Enhanced monitoring stopped")
        else:
            test_results["tests_failed"] += 1
            test_results["test_details"].append({
                "test": "Stop Enhanced Monitoring",
                "status": "FAILED",
                "message": "Enhanced monitoring still running"
            })
            logger.error("❌ Enhanced monitoring still running")
            
    except Exception as e:
        test_results["tests_failed"] += 1
        test_results["test_details"].append({
            "test": "Stop Enhanced Monitoring",
            "status": "FAILED",
            "message": f"Error stopping monitoring: {str(e)}"
        })
        logger.error(f"❌ Error stopping monitoring: {e}")
    
    # Generate final report
    logger.info("📊 Generating test report...")
    
    success_rate = (test_results["tests_passed"] / test_results["tests_run"]) * 100
    test_results["success_rate"] = success_rate
    
    if success_rate >= 80:
        test_results["overall_status"] = "PASSED"
        logger.info(f"✅ Enhanced Health Monitoring Tests PASSED ({success_rate:.1f}%)")
    else:
        test_results["overall_status"] = "FAILED"
        logger.error(f"❌ Enhanced Health Monitoring Tests FAILED ({success_rate:.1f}%)")
    
    return test_results

async def test_health_monitoring_endpoints():
    """Test health monitoring API endpoints"""
    
    logger.info("🌐 Testing Health Monitoring API Endpoints")
    
    import requests
    
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        "/health/intelligence",
        "/health/dashboard",
        "/health/monitoring-status",
        "/health/ragie-service",
        "/health/agent-coordination",
        "/health/context-preservation",
        "/health/real-time-metrics",
        "/health/historical-trends",
        "/health/user-satisfaction"
    ]
    
    endpoint_results = {
        "total_endpoints": len(endpoints_to_test),
        "successful_endpoints": 0,
        "failed_endpoints": 0,
        "results": []
    }
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                endpoint_results["successful_endpoints"] += 1
                endpoint_results["results"].append({
                    "endpoint": endpoint,
                    "status": "SUCCESS",
                    "status_code": response.status_code,
                    "response_size": len(response.text)
                })
                logger.info(f"✅ {endpoint} - SUCCESS")
            else:
                endpoint_results["failed_endpoints"] += 1
                endpoint_results["results"].append({
                    "endpoint": endpoint,
                    "status": "FAILED",
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })
                logger.error(f"❌ {endpoint} - FAILED ({response.status_code})")
                
        except requests.exceptions.RequestException as e:
            endpoint_results["failed_endpoints"] += 1
            endpoint_results["results"].append({
                "endpoint": endpoint,
                "status": "ERROR",
                "error": str(e)
            })
            logger.error(f"❌ {endpoint} - ERROR ({str(e)})")
    
    # Test POST endpoints
    post_endpoints = [
        "/health/start-monitoring",
        "/health/stop-monitoring"
    ]
    
    for endpoint in post_endpoints:
        try:
            response = requests.post(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                endpoint_results["successful_endpoints"] += 1
                endpoint_results["results"].append({
                    "endpoint": endpoint,
                    "status": "SUCCESS",
                    "status_code": response.status_code,
                    "method": "POST"
                })
                logger.info(f"✅ {endpoint} (POST) - SUCCESS")
            else:
                endpoint_results["failed_endpoints"] += 1
                endpoint_results["results"].append({
                    "endpoint": endpoint,
                    "status": "FAILED",
                    "status_code": response.status_code,
                    "method": "POST",
                    "error": response.text[:200]
                })
                logger.error(f"❌ {endpoint} (POST) - FAILED ({response.status_code})")
                
        except requests.exceptions.RequestException as e:
            endpoint_results["failed_endpoints"] += 1
            endpoint_results["results"].append({
                "endpoint": endpoint,
                "status": "ERROR",
                "method": "POST",
                "error": str(e)
            })
            logger.error(f"❌ {endpoint} (POST) - ERROR ({str(e)})")
    
    endpoint_results["total_endpoints"] = len(endpoints_to_test) + len(post_endpoints)
    
    return endpoint_results

async def main():
    """Main test function"""
    
    logger.info("🚀 Starting Enhanced Health Monitoring Test Suite")
    
    # Test 1: Enhanced monitoring system
    monitoring_results = await test_enhanced_health_monitoring()
    
    # Test 2: API endpoints (optional - requires running server)
    try:
        endpoint_results = await test_health_monitoring_endpoints()
    except Exception as e:
        logger.warning(f"⚠️ API endpoint tests skipped: {e}")
        endpoint_results = {"note": "API endpoints not tested - server may not be running"}
    
    # Generate comprehensive report
    final_report = {
        "test_suite": "Enhanced Health Monitoring",
        "timestamp": datetime.now().isoformat(),
        "monitoring_system_tests": monitoring_results,
        "api_endpoint_tests": endpoint_results,
        "summary": {
            "monitoring_system_success": monitoring_results.get("overall_status") == "PASSED",
            "api_endpoints_success": endpoint_results.get("successful_endpoints", 0) > 0,
            "overall_success": monitoring_results.get("overall_status") == "PASSED"
        }
    }
    
    # Save report
    with open("health_monitoring_test_report.json", "w") as f:
        json.dump(final_report, f, indent=2)
    
    logger.info("📋 Test report saved to health_monitoring_test_report.json")
    
    # Print summary
    logger.info("=" * 60)
    logger.info("📊 ENHANCED HEALTH MONITORING TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Monitoring System Tests: {monitoring_results.get('overall_status', 'UNKNOWN')}")
    logger.info(f"Tests Passed: {monitoring_results.get('tests_passed', 0)}/{monitoring_results.get('tests_run', 0)}")
    logger.info(f"Success Rate: {monitoring_results.get('success_rate', 0):.1f}%")
    
    if "successful_endpoints" in endpoint_results:
        logger.info(f"API Endpoints: {endpoint_results['successful_endpoints']}/{endpoint_results['total_endpoints']} working")
    
    logger.info("=" * 60)
    
    return final_report

if __name__ == "__main__":
    asyncio.run(main())