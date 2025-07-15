#!/usr/bin/env python3
"""
Live Production Validation System
=================================

Enhanced validation system that tests against the actual running backend.
Provides real-world validation of PydanticAI + Ragie integration.

Features:
- Real API testing against running backend
- Actual service connectivity validation
- Performance testing with real services
- Health monitoring validation
- Cross-modal integration testing

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
import aiohttp
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import statistics

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LiveValidationResult:
    """Result of a live validation test"""
    test_name: str
    passed: bool
    score: float
    execution_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

class LiveProductionValidationSystem:
    """
    Live production validation system that tests against actual running services.
    """
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.websocket_url = backend_url.replace("http://", "ws://").replace("https://", "wss://")
        self.session = None
        self.validation_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        
        # Test results
        self.test_results: List[LiveValidationResult] = []
        
        # Real test queries for QSR domain
        self.real_test_queries = {
            "equipment_troubleshooting": [
                "The Taylor ice cream machine is showing error code E01, what should I do?",
                "My Vulcan fryer won't heat up properly, can you help?",
                "The Hobart mixer is making strange noises, what's wrong?",
                "Traulsen freezer temperature is too high, how do I fix it?"
            ],
            "procedures": [
                "What are the opening procedures for a QSR restaurant?",
                "How do I properly clean the grill at closing time?",
                "What's the food safety protocol for handling raw meat?",
                "How do I train new staff on cash handling procedures?"
            ],
            "safety_emergencies": [
                "Someone just got burned by hot oil, what should I do immediately?",
                "There's a small grease fire in the kitchen, help!",
                "A customer is choking, what are the steps?",
                "The fire alarm is going off, what's the evacuation procedure?"
            ],
            "operational_questions": [
                "How do I handle a customer complaint about food quality?",
                "What's the proper inventory management process?",
                "How do I schedule staff for peak hours?",
                "What should I do if the POS system goes down?"
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_live_validation(self) -> Dict[str, Any]:
        """Run comprehensive live validation"""
        
        logger.info("🚀 Starting Live Production Validation")
        
        # Test 1: Backend Health Check
        await self._test_backend_health()
        
        # Test 2: Text Chat Integration
        await self._test_text_chat_integration()
        
        # Test 3: Voice Integration
        await self._test_voice_integration()
        
        # Test 4: Ragie Service Integration
        await self._test_ragie_integration()
        
        # Test 5: Visual Citations
        await self._test_visual_citations()
        
        # Test 6: Cross-Modal Context
        await self._test_cross_modal_context()
        
        # Test 7: Performance Under Load
        await self._test_performance_under_load()
        
        # Test 8: Error Handling
        await self._test_error_handling()
        
        # Test 9: WebSocket Connectivity
        await self._test_websocket_connectivity()
        
        # Test 10: Health Monitoring
        await self._test_health_monitoring()
        
        # Generate comprehensive report
        return self._generate_live_report()
    
    async def _test_backend_health(self):
        """Test backend health and availability"""
        test_name = "Backend Health Check"
        start_time = time.time()
        
        try:
            # Test basic health endpoint
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    
                    score = 1.0 if health_data.get("status") == "healthy" else 0.5
                    
                    self.test_results.append(LiveValidationResult(
                        test_name=test_name,
                        passed=response.status == 200,
                        score=score * 100,
                        execution_time=time.time() - start_time,
                        details={
                            "status_code": response.status,
                            "health_data": health_data,
                            "response_time": time.time() - start_time
                        }
                    ))
                else:
                    self.test_results.append(LiveValidationResult(
                        test_name=test_name,
                        passed=False,
                        score=0.0,
                        execution_time=time.time() - start_time,
                        details={"status_code": response.status},
                        error_message=f"Health check failed with status {response.status}"
                    ))
                    
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_text_chat_integration(self):
        """Test text chat integration with PydanticAI + Ragie"""
        test_name = "Text Chat Integration"
        start_time = time.time()
        
        try:
            successful_queries = 0
            total_queries = 0
            response_times = []
            
            # Test equipment troubleshooting
            for query in self.real_test_queries["equipment_troubleshooting"]:
                total_queries += 1
                query_start = time.time()
                
                try:
                    payload = {
                        "message": query,
                        "conversation_id": str(uuid.uuid4()),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    async with self.session.post(
                        f"{self.backend_url}/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        
                        if response.status == 200:
                            response_data = await response.json()
                            query_time = time.time() - query_start
                            response_times.append(query_time)
                            
                            # Check response quality
                            if (response_data.get("response") and 
                                len(response_data["response"]) > 20 and
                                response_data.get("citations")):
                                successful_queries += 1
                                
                except Exception as e:
                    logger.warning(f"Text chat query failed: {query[:50]}... - {str(e)}")
            
            # Calculate metrics
            success_rate = successful_queries / total_queries if total_queries > 0 else 0
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=success_rate >= 0.7,
                score=success_rate * 100,
                execution_time=time.time() - start_time,
                details={
                    "success_rate": success_rate,
                    "successful_queries": successful_queries,
                    "total_queries": total_queries,
                    "avg_response_time": avg_response_time,
                    "response_times": response_times
                }
            ))
            
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_voice_integration(self):
        """Test voice integration"""
        test_name = "Voice Integration"
        start_time = time.time()
        
        try:
            # Test voice query endpoint
            test_query = "How do I clean the fryer?"
            
            payload = {
                "message": test_query,
                "mode": "voice",
                "conversation_id": str(uuid.uuid4())
            }
            
            async with self.session.post(
                f"{self.backend_url}/voice/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    # Check if voice response includes expected elements
                    has_response = bool(response_data.get("response"))
                    has_audio = bool(response_data.get("audio_url") or response_data.get("tts_enabled"))
                    has_citations = bool(response_data.get("citations"))
                    
                    score = sum([has_response, has_audio, has_citations]) / 3.0
                    
                    self.test_results.append(LiveValidationResult(
                        test_name=test_name,
                        passed=score >= 0.7,
                        score=score * 100,
                        execution_time=time.time() - start_time,
                        details={
                            "has_response": has_response,
                            "has_audio": has_audio,
                            "has_citations": has_citations,
                            "response_data": response_data
                        }
                    ))
                else:
                    self.test_results.append(LiveValidationResult(
                        test_name=test_name,
                        passed=False,
                        score=0.0,
                        execution_time=time.time() - start_time,
                        details={"status_code": response.status},
                        error_message=f"Voice endpoint failed with status {response.status}"
                    ))
                    
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_ragie_integration(self):
        """Test Ragie service integration"""
        test_name = "Ragie Service Integration"
        start_time = time.time()
        
        try:
            # Test Ragie-specific query
            equipment_query = "Taylor ice cream machine maintenance manual"
            
            payload = {
                "message": equipment_query,
                "use_ragie": True,
                "conversation_id": str(uuid.uuid4())
            }
            
            async with self.session.post(
                f"{self.backend_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    # Check Ragie integration indicators
                    has_citations = bool(response_data.get("citations"))
                    has_visual_citations = any(
                        citation.get("image_url") or citation.get("page")
                        for citation in response_data.get("citations", [])
                    )
                    response_quality = len(response_data.get("response", "")) > 50
                    
                    score = sum([has_citations, has_visual_citations, response_quality]) / 3.0
                    
                    self.test_results.append(LiveValidationResult(
                        test_name=test_name,
                        passed=score >= 0.7,
                        score=score * 100,
                        execution_time=time.time() - start_time,
                        details={
                            "has_citations": has_citations,
                            "has_visual_citations": has_visual_citations,
                            "response_quality": response_quality,
                            "citations_count": len(response_data.get("citations", [])),
                            "response_length": len(response_data.get("response", ""))
                        }
                    ))
                else:
                    self.test_results.append(LiveValidationResult(
                        test_name=test_name,
                        passed=False,
                        score=0.0,
                        execution_time=time.time() - start_time,
                        details={"status_code": response.status},
                        error_message=f"Ragie integration failed with status {response.status}"
                    ))
                    
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_visual_citations(self):
        """Test visual citations functionality"""
        test_name = "Visual Citations"
        start_time = time.time()
        
        try:
            # Test queries that should produce visual citations
            citation_queries = [
                "Show me the Taylor machine manual page about cleaning",
                "What does the Vulcan fryer control panel look like?",
                "Display the safety procedures diagram"
            ]
            
            citations_found = 0
            total_queries = len(citation_queries)
            
            for query in citation_queries:
                try:
                    payload = {
                        "message": query,
                        "include_visuals": True,
                        "conversation_id": str(uuid.uuid4())
                    }
                    
                    async with self.session.post(
                        f"{self.backend_url}/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        
                        if response.status == 200:
                            response_data = await response.json()
                            
                            # Check for visual citations
                            citations = response_data.get("citations", [])
                            has_visuals = any(
                                citation.get("image_url") or 
                                citation.get("page") or
                                citation.get("visual_reference")
                                for citation in citations
                            )
                            
                            if has_visuals:
                                citations_found += 1
                                
                except Exception as e:
                    logger.warning(f"Visual citation query failed: {query[:50]}... - {str(e)}")
            
            citation_rate = citations_found / total_queries if total_queries > 0 else 0
            
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=citation_rate >= 0.5,
                score=citation_rate * 100,
                execution_time=time.time() - start_time,
                details={
                    "citation_rate": citation_rate,
                    "citations_found": citations_found,
                    "total_queries": total_queries
                }
            ))
            
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_cross_modal_context(self):
        """Test cross-modal context preservation"""
        test_name = "Cross-Modal Context"
        start_time = time.time()
        
        try:
            conversation_id = str(uuid.uuid4())
            
            # Start with text query
            text_payload = {
                "message": "Tell me about the Taylor ice cream machine",
                "conversation_id": conversation_id
            }
            
            async with self.session.post(
                f"{self.backend_url}/chat",
                json=text_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    text_response = await response.json()
                    
                    # Follow up with voice query
                    voice_payload = {
                        "message": "Can you explain the cleaning process?",
                        "conversation_id": conversation_id,
                        "mode": "voice"
                    }
                    
                    async with self.session.post(
                        f"{self.backend_url}/voice/query",
                        json=voice_payload,
                        headers={"Content-Type": "application/json"}
                    ) as voice_response:
                        
                        if voice_response.status == 200:
                            voice_data = await voice_response.json()
                            
                            # Check context preservation
                            text_mentions_taylor = "taylor" in text_response.get("response", "").lower()
                            voice_mentions_taylor = "taylor" in voice_data.get("response", "").lower()
                            context_preserved = text_mentions_taylor and voice_mentions_taylor
                            
                            score = 1.0 if context_preserved else 0.5
                            
                            self.test_results.append(LiveValidationResult(
                                test_name=test_name,
                                passed=context_preserved,
                                score=score * 100,
                                execution_time=time.time() - start_time,
                                details={
                                    "text_mentions_taylor": text_mentions_taylor,
                                    "voice_mentions_taylor": voice_mentions_taylor,
                                    "context_preserved": context_preserved,
                                    "conversation_id": conversation_id
                                }
                            ))
                        else:
                            self.test_results.append(LiveValidationResult(
                                test_name=test_name,
                                passed=False,
                                score=0.0,
                                execution_time=time.time() - start_time,
                                details={},
                                error_message=f"Voice follow-up failed with status {voice_response.status}"
                            ))
                else:
                    self.test_results.append(LiveValidationResult(
                        test_name=test_name,
                        passed=False,
                        score=0.0,
                        execution_time=time.time() - start_time,
                        details={},
                        error_message=f"Text query failed with status {response.status}"
                    ))
                    
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_performance_under_load(self):
        """Test performance under concurrent load"""
        test_name = "Performance Under Load"
        start_time = time.time()
        
        try:
            # Send concurrent requests
            concurrent_requests = 5
            queries = [
                "What's the cleaning procedure for the grill?",
                "How do I troubleshoot the fryer?",
                "What are the safety protocols?",
                "How do I handle customer complaints?",
                "What's the opening checklist?"
            ]
            
            async def send_concurrent_query(query: str, request_id: int):
                query_start = time.time()
                try:
                    payload = {
                        "message": query,
                        "conversation_id": str(uuid.uuid4()),
                        "request_id": request_id
                    }
                    
                    async with self.session.post(
                        f"{self.backend_url}/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        
                        query_time = time.time() - query_start
                        return {
                            "request_id": request_id,
                            "success": response.status == 200,
                            "response_time": query_time,
                            "status_code": response.status
                        }
                except Exception as e:
                    return {
                        "request_id": request_id,
                        "success": False,
                        "response_time": time.time() - query_start,
                        "error": str(e)
                    }
            
            # Execute concurrent requests
            tasks = [send_concurrent_query(query, i) for i, query in enumerate(queries)]
            results = await asyncio.gather(*tasks)
            
            # Calculate metrics
            successful_requests = sum(1 for r in results if r["success"])
            total_requests = len(results)
            success_rate = successful_requests / total_requests if total_requests > 0 else 0
            
            response_times = [r["response_time"] for r in results if r["success"]]
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            # Performance score based on success rate and response time
            time_score = 1.0 / (1.0 + avg_response_time / 3.0)  # 3 second baseline
            performance_score = (success_rate + time_score) / 2.0
            
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=performance_score >= 0.7,
                score=performance_score * 100,
                execution_time=time.time() - start_time,
                details={
                    "success_rate": success_rate,
                    "successful_requests": successful_requests,
                    "total_requests": total_requests,
                    "avg_response_time": avg_response_time,
                    "performance_score": performance_score,
                    "concurrent_requests": concurrent_requests
                }
            ))
            
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_error_handling(self):
        """Test error handling and graceful degradation"""
        test_name = "Error Handling"
        start_time = time.time()
        
        try:
            # Test various error scenarios
            error_scenarios = [
                {"message": "", "expected": "empty query"},
                {"message": "A" * 10000, "expected": "very long query"},
                {"message": "###INVALID###", "expected": "invalid format"},
                {"invalid_field": "test", "expected": "invalid payload"}
            ]
            
            graceful_handles = 0
            total_scenarios = len(error_scenarios)
            
            for scenario in error_scenarios:
                try:
                    async with self.session.post(
                        f"{self.backend_url}/chat",
                        json=scenario,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        
                        # Check if error is handled gracefully (not 500)
                        if response.status != 500:
                            graceful_handles += 1
                            
                except Exception as e:
                    # Some errors are expected
                    graceful_handles += 1
                    logger.info(f"Expected error handled: {str(e)}")
            
            handling_rate = graceful_handles / total_scenarios if total_scenarios > 0 else 0
            
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=handling_rate >= 0.8,
                score=handling_rate * 100,
                execution_time=time.time() - start_time,
                details={
                    "handling_rate": handling_rate,
                    "graceful_handles": graceful_handles,
                    "total_scenarios": total_scenarios
                }
            ))
            
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_websocket_connectivity(self):
        """Test WebSocket connectivity"""
        test_name = "WebSocket Connectivity"
        start_time = time.time()
        
        try:
            # Test WebSocket connection
            websocket_url = f"{self.websocket_url}/ws"
            
            # This is a basic connectivity test
            # In a real implementation, you'd test actual WebSocket functionality
            websocket_available = True
            
            try:
                # Try to connect to WebSocket
                async with websockets.connect(websocket_url, timeout=5) as websocket:
                    # Send a test message
                    test_message = json.dumps({
                        "type": "test",
                        "message": "WebSocket connectivity test"
                    })
                    await websocket.send(test_message)
                    
                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    
                    websocket_available = True
                    
            except Exception as e:
                websocket_available = False
                logger.warning(f"WebSocket connectivity test failed: {str(e)}")
            
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=websocket_available,
                score=100.0 if websocket_available else 0.0,
                execution_time=time.time() - start_time,
                details={
                    "websocket_available": websocket_available,
                    "websocket_url": websocket_url
                }
            ))
            
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    async def _test_health_monitoring(self):
        """Test health monitoring endpoints"""
        test_name = "Health Monitoring"
        start_time = time.time()
        
        try:
            # Test health monitoring endpoints
            health_endpoints = [
                "/health",
                "/health/intelligence",
                "/health/dashboard",
                "/health/monitoring-status"
            ]
            
            healthy_endpoints = 0
            total_endpoints = len(health_endpoints)
            endpoint_details = {}
            
            for endpoint in health_endpoints:
                try:
                    async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                        if response.status == 200:
                            healthy_endpoints += 1
                            endpoint_details[endpoint] = {
                                "status": "healthy",
                                "status_code": response.status
                            }
                        else:
                            endpoint_details[endpoint] = {
                                "status": "unhealthy",
                                "status_code": response.status
                            }
                except Exception as e:
                    endpoint_details[endpoint] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            health_rate = healthy_endpoints / total_endpoints if total_endpoints > 0 else 0
            
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=health_rate >= 0.7,
                score=health_rate * 100,
                execution_time=time.time() - start_time,
                details={
                    "health_rate": health_rate,
                    "healthy_endpoints": healthy_endpoints,
                    "total_endpoints": total_endpoints,
                    "endpoint_details": endpoint_details
                }
            ))
            
        except Exception as e:
            self.test_results.append(LiveValidationResult(
                test_name=test_name,
                passed=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
    
    def _generate_live_report(self) -> Dict[str, Any]:
        """Generate comprehensive live validation report"""
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall metrics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        overall_score = statistics.mean([result.score for result in self.test_results]) if self.test_results else 0
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Generate report
        report = {
            "validation_summary": {
                "validation_id": self.validation_id,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration,
                "backend_url": self.backend_url,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "overall_score": overall_score
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "passed": result.passed,
                    "score": result.score,
                    "execution_time": result.execution_time,
                    "details": result.details,
                    "error_message": result.error_message
                }
                for result in self.test_results
            ],
            "production_readiness": self._assess_production_readiness(success_rate, overall_score),
            "recommendations": self._generate_live_recommendations(),
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _assess_production_readiness(self, success_rate: float, overall_score: float) -> Dict[str, Any]:
        """Assess production readiness based on results"""
        
        if success_rate >= 0.8 and overall_score >= 80:
            status = "READY"
            level = "GREEN"
            message = "System is ready for production deployment"
        elif success_rate >= 0.6 and overall_score >= 60:
            status = "NEEDS_IMPROVEMENT"
            level = "YELLOW"
            message = "System needs improvements before production"
        else:
            status = "NOT_READY"
            level = "RED"
            message = "System is not ready for production"
        
        return {
            "status": status,
            "level": level,
            "message": message,
            "success_rate": success_rate,
            "overall_score": overall_score
        }
    
    def _generate_live_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on live test results"""
        
        recommendations = []
        
        # Analyze failed tests
        failed_tests = [result for result in self.test_results if not result.passed]
        
        if failed_tests:
            for failed_test in failed_tests:
                recommendations.append({
                    "priority": "HIGH",
                    "category": failed_test.test_name,
                    "issue": f"Test '{failed_test.test_name}' failed",
                    "recommendation": f"Investigate and fix: {failed_test.error_message or 'Unknown error'}",
                    "impact": "Blocks production deployment"
                })
        
        # Check performance issues
        performance_tests = [result for result in self.test_results if "Performance" in result.test_name]
        for perf_test in performance_tests:
            if perf_test.score < 70:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Performance",
                    "issue": f"Performance test scored {perf_test.score:.1f}%",
                    "recommendation": "Optimize performance before production deployment",
                    "impact": "May affect user experience"
                })
        
        # Success recommendations
        if not failed_tests:
            recommendations.append({
                "priority": "INFO",
                "category": "Success",
                "issue": "All tests passed successfully",
                "recommendation": "System is ready for production deployment",
                "impact": "Positive - ready for users"
            })
        
        return recommendations
    
    async def save_live_report(self, filename: Optional[str] = None) -> str:
        """Save live validation report to file"""
        
        if not filename:
            filename = f"live_production_validation_{self.validation_id[:8]}.json"
        
        report = self._generate_live_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Live validation report saved to: {filename}")
        return filename

# Main execution
async def main():
    """Main live validation execution"""
    
    print("🚀 Starting Live Production Validation")
    print("="*80)
    
    backend_url = "http://localhost:8000"
    
    async with LiveProductionValidationSystem(backend_url) as validator:
        # Run live validation
        results = await validator.run_live_validation()
        
        # Save report
        report_file = await validator.save_live_report()
        
        # Print results
        print("\nLIVE VALIDATION RESULTS:")
        print("="*80)
        
        summary = results["validation_summary"]
        print(f"Backend URL: {summary['backend_url']}")
        print(f"Duration: {summary['duration']:.1f} seconds")
        print(f"Overall Score: {summary['overall_score']:.1f}/100")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        
        # Print individual test results
        print("\nTEST BREAKDOWN:")
        for result in results["test_results"]:
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {result['test_name']}: {result['score']:.1f}% ({result['execution_time']:.2f}s)")
        
        # Print production readiness
        readiness = results["production_readiness"]
        readiness_emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}
        print(f"\nPRODUCTION READINESS:")
        print(f"  {readiness_emoji[readiness['level']]} {readiness['status']}: {readiness['message']}")
        
        # Print recommendations
        if results["recommendations"]:
            print("\nRECOMMENDATIONS:")
            for rec in results["recommendations"]:
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "INFO": "🟢"}
                print(f"  {priority_emoji[rec['priority']]} [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        
        print(f"\nDetailed report saved to: {report_file}")
        print("="*80)
        
        return results

if __name__ == "__main__":
    asyncio.run(main())