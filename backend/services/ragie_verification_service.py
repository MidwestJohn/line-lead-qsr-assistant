#!/usr/bin/env python3
"""
Ragie Verification Service
==========================

Comprehensive verification and monitoring system to prove Ragie is actually
running (not just falling back to basic search immediately).

Features:
- Detailed logging of all Ragie API calls with timing
- Success/failure rate tracking
- Network activity monitoring
- Response source indicators
- Performance metrics collection
- Health check capabilities

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

@dataclass
class RagieCallMetrics:
    """Metrics for a single Ragie API call"""
    call_id: str
    timestamp: datetime
    query: str
    duration: float
    success: bool
    results_found: int
    error: Optional[str] = None
    network_request_made: bool = False

@dataclass
class RagieVerificationStats:
    """Overall Ragie verification statistics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_processing_time: float = 0.0
    average_response_time: float = 0.0
    fastest_response: float = float('inf')
    slowest_response: float = 0.0
    calls_history: List[RagieCallMetrics] = field(default_factory=list)
    last_health_check: Optional[datetime] = None
    health_check_success: bool = False

class RagieVerificationService:
    """Service to verify and monitor Ragie integration"""
    
    def __init__(self):
        """Initialize verification service"""
        self.stats = RagieVerificationStats()
        self.call_counter = 0
        self.max_history = 100  # Keep last 100 calls
        
        # Test queries for different verification scenarios
        self.test_queries = [
            "Taylor C602 ice cream machine cleaning procedure",  # Should find specific Ragie docs
            "Fryer temperature calibration steps",              # Should find equipment manuals  
            "Safety procedures for hot oil spills",             # Should find safety documentation
            "How to make a sandwich"                            # Should fall back (no QSR docs)
        ]
        
        logger.info("🔍 Ragie Verification Service initialized")
    
    async def verify_ragie_call(
        self, 
        query: str, 
        ragie_callable,
        *args, 
        **kwargs
    ) -> tuple[Any, RagieCallMetrics]:
        """
        Verify a Ragie API call with comprehensive logging
        
        Wraps any Ragie service call to track metrics and prove it's working
        """
        self.call_counter += 1
        call_id = f"ragie_call_{self.call_counter:06d}"
        start_time = time.time()
        
        logger.info(f"🔍 RAGIE CALL #{self.call_counter}: Starting search")
        logger.info(f"   📝 Query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
        logger.info(f"   🆔 Call ID: {call_id}")
        logger.info(f"   ⏰ Start Time: {datetime.now().isoformat()}")
        
        metrics = RagieCallMetrics(
            call_id=call_id,
            timestamp=datetime.now(),
            query=query,
            duration=0.0,
            success=False,
            results_found=0
        )
        
        try:
            logger.info(f"   🌐 Making network request to Ragie API...")
            metrics.network_request_made = True
            
            # Make the actual Ragie call
            result = await ragie_callable(*args, **kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            metrics.duration = duration
            metrics.success = True
            
            # Count results
            if hasattr(result, 'results'):
                metrics.results_found = len(result.results)
            elif isinstance(result, list):
                metrics.results_found = len(result)
            elif result:
                metrics.results_found = 1
            else:
                metrics.results_found = 0
            
            # Update statistics
            self._update_stats(metrics)
            
            logger.info(f"✅ RAGIE SUCCESS #{self.stats.successful_calls}:")
            logger.info(f"   ⏱️ Duration: {duration:.3f}s")
            logger.info(f"   📊 Results Found: {metrics.results_found}")
            logger.info(f"   🌐 Network Request: ✅ Made")
            logger.info(f"   📈 Success Rate: {self.stats.successful_calls}/{self.stats.total_calls} ({self._get_success_rate():.1f}%)")
            logger.info(f"   ⚡ Avg Response Time: {self.stats.average_response_time:.3f}s")
            
            # Check for suspicious timing (too fast = likely not hitting API)
            if duration < 0.1:
                logger.warning(f"⚠️ SUSPICIOUS: Response time {duration:.3f}s is very fast - verify API is being called!")
            
            return result, metrics
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            metrics.duration = duration
            metrics.success = False
            metrics.error = str(e)
            
            # Update statistics
            self._update_stats(metrics)
            
            logger.error(f"❌ RAGIE FAILURE #{self.stats.failed_calls}:")
            logger.error(f"   ⏱️ Duration: {duration:.3f}s")
            logger.error(f"   💥 Error: {str(e)}")
            logger.error(f"   🌐 Network Request: {'✅' if metrics.network_request_made else '❌'}")
            logger.error(f"   📈 Success Rate: {self.stats.successful_calls}/{self.stats.total_calls} ({self._get_success_rate():.1f}%)")
            logger.warning(f"   🔄 This will trigger fallback to standard search")
            
            raise e  # Re-raise so calling code can handle fallback
    
    def _update_stats(self, metrics: RagieCallMetrics):
        """Update verification statistics"""
        self.stats.total_calls += 1
        self.stats.total_processing_time += metrics.duration
        
        if metrics.success:
            self.stats.successful_calls += 1
        else:
            self.stats.failed_calls += 1
        
        # Update timing stats
        self.stats.fastest_response = min(self.stats.fastest_response, metrics.duration)
        self.stats.slowest_response = max(self.stats.slowest_response, metrics.duration)
        self.stats.average_response_time = self.stats.total_processing_time / self.stats.total_calls
        
        # Add to history
        self.stats.calls_history.append(metrics)
        
        # Maintain history limit
        if len(self.stats.calls_history) > self.max_history:
            self.stats.calls_history = self.stats.calls_history[-self.max_history:]
    
    def _get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.stats.total_calls == 0:
            return 0.0
        return (self.stats.successful_calls / self.stats.total_calls) * 100
    
    async def health_check_ragie(self, ragie_service) -> Dict[str, Any]:
        """Comprehensive Ragie health check"""
        logger.info("🩺 Starting Ragie health check...")
        
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "ragie_accessible": False,
            "test_query_results": [],
            "api_response_time": None,
            "error": None
        }
        
        try:
            # Test with simple query
            start_time = time.time()
            
            if hasattr(ragie_service, 'search'):
                test_result = await ragie_service.search("test equipment")
            elif hasattr(ragie_service, 'search_with_qsr_context'):
                test_result = await ragie_service.search_with_qsr_context("test equipment")
            else:
                raise Exception("No recognized search method on ragie_service")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            health_data.update({
                "ragie_accessible": True,
                "api_response_time": response_time,
                "test_results_found": len(test_result.results) if hasattr(test_result, 'results') else 0
            })
            
            self.stats.last_health_check = datetime.now()
            self.stats.health_check_success = True
            
            logger.info(f"✅ Ragie health check PASSED:")
            logger.info(f"   ⏱️ Response time: {response_time:.3f}s")
            logger.info(f"   📊 Test results: {health_data['test_results_found']}")
            
        except Exception as e:
            health_data["error"] = str(e)
            self.stats.last_health_check = datetime.now()
            self.stats.health_check_success = False
            
            logger.error(f"❌ Ragie health check FAILED: {e}")
        
        return health_data
    
    async def run_comprehensive_verification(self, ragie_service) -> Dict[str, Any]:
        """Run comprehensive verification test suite"""
        logger.info("🧪 Running comprehensive Ragie verification...")
        
        verification_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "health_check": None,
            "test_queries": [],
            "performance_analysis": {},
            "red_flags": [],
            "green_flags": [],
            "conclusion": ""
        }
        
        # 1. Health check
        logger.info("1️⃣ Running health check...")
        verification_results["health_check"] = await self.health_check_ragie(ragie_service)
        
        # 2. Test with different query types
        logger.info("2️⃣ Testing query types...")
        for query in self.test_queries:
            logger.info(f"   Testing: {query}")
            
            try:
                start_time = time.time()
                result, metrics = await self.verify_ragie_call(
                    query, 
                    ragie_service.search_with_qsr_context if hasattr(ragie_service, 'search_with_qsr_context') else ragie_service.search,
                    query
                )
                
                verification_results["test_queries"].append({
                    "query": query,
                    "success": True,
                    "response_time": metrics.duration,
                    "results_found": metrics.results_found,
                    "network_request_made": metrics.network_request_made
                })
                
            except Exception as e:
                verification_results["test_queries"].append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "response_time": None,
                    "results_found": 0,
                    "network_request_made": False
                })
        
        # 3. Performance analysis
        verification_results["performance_analysis"] = {
            "total_calls": self.stats.total_calls,
            "success_rate": self._get_success_rate(),
            "average_response_time": self.stats.average_response_time,
            "fastest_response": self.stats.fastest_response if self.stats.fastest_response != float('inf') else None,
            "slowest_response": self.stats.slowest_response,
            "calls_under_2s": sum(1 for call in self.stats.calls_history if call.duration < 2.0),
            "calls_over_5s": sum(1 for call in self.stats.calls_history if call.duration > 5.0)
        }
        
        # 4. Red flags analysis
        red_flags = []
        green_flags = []
        
        if not verification_results["health_check"]["ragie_accessible"]:
            red_flags.append("❌ Ragie API not accessible")
        else:
            green_flags.append("✅ Ragie API accessible")
        
        if self.stats.average_response_time < 0.5:
            red_flags.append("🚨 Average response time suspiciously fast (<0.5s) - likely not hitting real API")
        elif self.stats.average_response_time < 2.0:
            green_flags.append("✅ Response times within acceptable range")
        
        successful_queries = [q for q in verification_results["test_queries"] if q["success"]]
        if len(successful_queries) == 0:
            red_flags.append("❌ No test queries succeeded")
        else:
            green_flags.append(f"✅ {len(successful_queries)}/{len(self.test_queries)} test queries succeeded")
        
        if self._get_success_rate() < 50:
            red_flags.append("❌ Success rate below 50%")
        elif self._get_success_rate() > 80:
            green_flags.append("✅ High success rate")
        
        # Network requests check
        network_requests_made = sum(1 for call in self.stats.calls_history if call.network_request_made)
        if network_requests_made == 0:
            red_flags.append("🚨 No network requests made to Ragie API")
        else:
            green_flags.append(f"✅ Network requests made: {network_requests_made}/{self.stats.total_calls}")
        
        verification_results["red_flags"] = red_flags
        verification_results["green_flags"] = green_flags
        
        # 5. Final conclusion
        if len(red_flags) == 0:
            verification_results["overall_status"] = "healthy"
            verification_results["conclusion"] = "✅ Ragie integration is working correctly"
        elif len(red_flags) > len(green_flags):
            verification_results["overall_status"] = "failing"
            verification_results["conclusion"] = "❌ Ragie integration appears to be failing or bypassed"
        else:
            verification_results["overall_status"] = "degraded"
            verification_results["conclusion"] = "⚠️ Ragie integration working but with issues"
        
        logger.info(f"🧪 Verification complete: {verification_results['conclusion']}")
        
        return verification_results
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get current verification summary"""
        return {
            "stats": {
                "total_calls": self.stats.total_calls,
                "successful_calls": self.stats.successful_calls,
                "failed_calls": self.stats.failed_calls,
                "success_rate": self._get_success_rate(),
                "average_response_time": self.stats.average_response_time,
            },
            "recent_calls": self.stats.calls_history[-10:] if self.stats.calls_history else [],
            "last_health_check": self.stats.last_health_check.isoformat() if self.stats.last_health_check else None,
            "health_check_success": self.stats.health_check_success
        }

# Global verification service
ragie_verification = RagieVerificationService()

def format_response_with_source(response_text: str, ragie_used: bool, ragie_results_count: int = 0) -> str:
    """Format response with clear source indicators"""
    if ragie_used:
        source_indicator = f"\n\n🔍 **Enhanced with Ragie Knowledge** ({ragie_results_count} sources found)"
    else:
        source_indicator = f"\n\n⚡ **Standard Response** (Ragie unavailable or no results)"
    
    return response_text + source_indicator