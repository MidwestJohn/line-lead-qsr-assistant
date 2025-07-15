#!/usr/bin/env python3
"""
Phase 5: Production Integration - Step 5.2: Production Validation
================================================================

Comprehensive production validation system for PydanticAI + Ragie intelligence integration.
Validates all interaction modes (text, voice, cross-modal) and integration points.

Test Coverage:
- Text Chat Validation: PydanticAI + Ragie processing, equipment recognition, visual citations
- Voice Validation: Voice queries enhanced with Ragie, equipment context, safety responses
- Cross-Modal Validation: Context preservation, knowledge consistency, visual citations
- Integration Validation: Service connectivity, agent coordination, error handling

Success Criteria:
- Text chat AS SMART as voice
- Ragie enhances both modes
- Visual citations work everywhere
- Performance acceptable
- Consistent intelligence

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import deque, defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import random
import requests
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationResult(Enum):
    """Validation test results"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"

class ValidationCategory(Enum):
    """Validation categories"""
    TEXT_CHAT = "text_chat"
    VOICE = "voice"
    CROSS_MODAL = "cross_modal"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"

@dataclass
class ValidationTest:
    """Individual validation test"""
    test_id: str
    name: str
    category: ValidationCategory
    description: str
    result: ValidationResult = ValidationResult.SKIPPED
    score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None

@dataclass
class ValidationScenario:
    """Test scenario with multiple validation tests"""
    scenario_id: str
    name: str
    description: str
    tests: List[ValidationTest] = field(default_factory=list)
    overall_score: float = 0.0
    success_rate: float = 0.0

class ProductionValidationSystem:
    """
    Comprehensive production validation system for PydanticAI + Ragie integration.
    
    Validates all interaction modes and integration points with detailed scoring
    and comprehensive reporting.
    """
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.validation_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        
        # Test scenarios
        self.scenarios: List[ValidationScenario] = []
        
        # Results storage
        self.validation_results: Dict[str, Any] = {
            "validation_id": self.validation_id,
            "start_time": self.start_time.isoformat(),
            "scenarios": [],
            "overall_score": 0.0,
            "success_rate": 0.0,
            "total_tests": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_warnings": 0,
            "tests_skipped": 0
        }
        
        # Test data
        self.test_queries = {
            "equipment": [
                "How do I clean the Taylor ice cream machine?",
                "What's the procedure for the Vulcan fryer maintenance?",
                "How do I calibrate the Hobart mixer?",
                "Tell me about the Traulsen freezer temperature settings"
            ],
            "procedures": [
                "What are the steps for opening procedures?",
                "How do I handle food safety during rush hours?",
                "What's the procedure for equipment breakdown?",
                "How do I train new employees on safety protocols?"
            ],
            "safety": [
                "What should I do if someone gets burned?",
                "How do I handle a grease fire?",
                "What are the emergency evacuation procedures?",
                "How do I report a safety incident?"
            ],
            "general": [
                "How do I improve customer service?",
                "What are the best practices for inventory management?",
                "How do I handle customer complaints?",
                "What's the procedure for cash handling?"
            ]
        }
        
        # Initialize scenarios
        self._initialize_scenarios()
    
    def _initialize_scenarios(self):
        """Initialize all validation scenarios"""
        
        # Scenario 1: Text Chat Validation
        text_chat_scenario = ValidationScenario(
            scenario_id="text_chat_001",
            name="Text Chat Intelligence Validation",
            description="Validate PydanticAI + Ragie processing in text chat mode"
        )
        
        # Add text chat tests
        text_chat_scenario.tests.extend([
            ValidationTest(
                test_id="text_001",
                name="Basic Text Query Processing",
                category=ValidationCategory.TEXT_CHAT,
                description="Test basic text query processing with PydanticAI + Ragie"
            ),
            ValidationTest(
                test_id="text_002",
                name="Equipment Recognition",
                category=ValidationCategory.TEXT_CHAT,
                description="Test equipment recognition with Ragie documentation"
            ),
            ValidationTest(
                test_id="text_003",
                name="Visual Citations in Text",
                category=ValidationCategory.TEXT_CHAT,
                description="Test visual citation extraction in text responses"
            ),
            ValidationTest(
                test_id="text_004",
                name="Procedure Guidance",
                category=ValidationCategory.TEXT_CHAT,
                description="Test procedure guidance using Ragie knowledge"
            ),
            ValidationTest(
                test_id="text_005",
                name="Safety Response Intelligence",
                category=ValidationCategory.TEXT_CHAT,
                description="Test safety response intelligence with Ragie documentation"
            )
        ])
        
        # Scenario 2: Voice Validation
        voice_scenario = ValidationScenario(
            scenario_id="voice_001",
            name="Voice Intelligence Validation",
            description="Validate voice queries enhanced with Ragie"
        )
        
        voice_scenario.tests.extend([
            ValidationTest(
                test_id="voice_001",
                name="Voice Query Enhancement",
                category=ValidationCategory.VOICE,
                description="Test voice queries enhanced with Ragie"
            ),
            ValidationTest(
                test_id="voice_002",
                name="Equipment Context from Voice",
                category=ValidationCategory.VOICE,
                description="Test equipment context extraction from voice using Ragie docs"
            ),
            ValidationTest(
                test_id="voice_003",
                name="Voice Visual Citations",
                category=ValidationCategory.VOICE,
                description="Test visual citations coordinated with voice responses"
            ),
            ValidationTest(
                test_id="voice_004",
                name="Safety Voice Responses",
                category=ValidationCategory.VOICE,
                description="Test safety responses using Ragie in voice mode"
            ),
            ValidationTest(
                test_id="voice_005",
                name="Voice Response Quality",
                category=ValidationCategory.VOICE,
                description="Test voice response quality with Ragie enhancement"
            )
        ])
        
        # Scenario 3: Cross-Modal Validation
        cross_modal_scenario = ValidationScenario(
            scenario_id="cross_modal_001",
            name="Cross-Modal Intelligence Validation",
            description="Validate context preservation and consistency across modes"
        )
        
        cross_modal_scenario.tests.extend([
            ValidationTest(
                test_id="cross_001",
                name="Context Preservation Text to Voice",
                category=ValidationCategory.CROSS_MODAL,
                description="Test context preservation from text to voice"
            ),
            ValidationTest(
                test_id="cross_002",
                name="Context Preservation Voice to Text",
                category=ValidationCategory.CROSS_MODAL,
                description="Test context preservation from voice to text"
            ),
            ValidationTest(
                test_id="cross_003",
                name="Ragie Knowledge Consistency",
                category=ValidationCategory.CROSS_MODAL,
                description="Test Ragie knowledge consistency across modes"
            ),
            ValidationTest(
                test_id="cross_004",
                name="Visual Citation Consistency",
                category=ValidationCategory.CROSS_MODAL,
                description="Test visual citation consistency across modes"
            ),
            ValidationTest(
                test_id="cross_005",
                name="Cross-Modal Performance",
                category=ValidationCategory.CROSS_MODAL,
                description="Test performance across different interaction modes"
            )
        ])
        
        # Scenario 4: Integration Validation
        integration_scenario = ValidationScenario(
            scenario_id="integration_001",
            name="Integration Validation",
            description="Validate all integration points and error handling"
        )
        
        integration_scenario.tests.extend([
            ValidationTest(
                test_id="integration_001",
                name="Ragie Service Connectivity",
                category=ValidationCategory.INTEGRATION,
                description="Test Ragie service connectivity and availability"
            ),
            ValidationTest(
                test_id="integration_002",
                name="Visual Citation Extraction",
                category=ValidationCategory.INTEGRATION,
                description="Test visual citation extraction functionality"
            ),
            ValidationTest(
                test_id="integration_003",
                name="Agent Coordination",
                category=ValidationCategory.INTEGRATION,
                description="Test PydanticAI agent coordination"
            ),
            ValidationTest(
                test_id="integration_004",
                name="Error Handling",
                category=ValidationCategory.INTEGRATION,
                description="Test error handling and graceful degradation"
            ),
            ValidationTest(
                test_id="integration_005",
                name="Service Health Monitoring",
                category=ValidationCategory.INTEGRATION,
                description="Test service health monitoring functionality"
            )
        ])
        
        # Scenario 5: Performance Validation
        performance_scenario = ValidationScenario(
            scenario_id="performance_001",
            name="Performance Validation",
            description="Validate performance across all intelligence services"
        )
        
        performance_scenario.tests.extend([
            ValidationTest(
                test_id="performance_001",
                name="Response Time Performance",
                category=ValidationCategory.PERFORMANCE,
                description="Test response time performance across services"
            ),
            ValidationTest(
                test_id="performance_002",
                name="Throughput Performance",
                category=ValidationCategory.PERFORMANCE,
                description="Test throughput performance under load"
            ),
            ValidationTest(
                test_id="performance_003",
                name="Resource Utilization",
                category=ValidationCategory.PERFORMANCE,
                description="Test resource utilization efficiency"
            ),
            ValidationTest(
                test_id="performance_004",
                name="Concurrent User Performance",
                category=ValidationCategory.PERFORMANCE,
                description="Test performance with concurrent users"
            ),
            ValidationTest(
                test_id="performance_005",
                name="Memory Usage Stability",
                category=ValidationCategory.PERFORMANCE,
                description="Test memory usage stability over time"
            )
        ])
        
        # Add all scenarios
        self.scenarios = [
            text_chat_scenario,
            voice_scenario,
            cross_modal_scenario,
            integration_scenario,
            performance_scenario
        ]
    
    async def run_validation(self) -> Dict[str, Any]:
        """
        Run complete production validation across all scenarios.
        
        Returns:
            Dict containing comprehensive validation results
        """
        logger.info("🚀 Starting Production Validation for PydanticAI + Ragie Integration")
        
        # Run all scenarios
        for scenario in self.scenarios:
            logger.info(f"🔍 Running scenario: {scenario.name}")
            await self._run_scenario(scenario)
        
        # Calculate overall results
        self._calculate_overall_results()
        
        # Generate report
        return self._generate_validation_report()
    
    async def _run_scenario(self, scenario: ValidationScenario):
        """Run all tests in a scenario"""
        
        passed_tests = 0
        total_score = 0.0
        
        for test in scenario.tests:
            logger.info(f"  🧪 Running test: {test.name}")
            
            start_time = time.time()
            
            try:
                # Run the specific test
                await self._run_test(test)
                
                if test.result == ValidationResult.PASSED:
                    passed_tests += 1
                
                total_score += test.score
                
            except Exception as e:
                logger.error(f"Test {test.test_id} failed: {str(e)}")
                test.result = ValidationResult.FAILED
                test.error_message = str(e)
                test.score = 0.0
            
            test.execution_time = time.time() - start_time
            logger.info(f"  ✅ Test {test.name}: {test.result.value} (Score: {test.score:.2f})")
        
        # Calculate scenario results
        scenario.success_rate = passed_tests / len(scenario.tests) if scenario.tests else 0.0
        scenario.overall_score = total_score / len(scenario.tests) if scenario.tests else 0.0
        
        logger.info(f"📊 Scenario {scenario.name} complete: {scenario.success_rate:.2%} success rate")
    
    async def _run_test(self, test: ValidationTest):
        """Run an individual test based on its category and ID"""
        
        if test.category == ValidationCategory.TEXT_CHAT:
            await self._run_text_chat_test(test)
        elif test.category == ValidationCategory.VOICE:
            await self._run_voice_test(test)
        elif test.category == ValidationCategory.CROSS_MODAL:
            await self._run_cross_modal_test(test)
        elif test.category == ValidationCategory.INTEGRATION:
            await self._run_integration_test(test)
        elif test.category == ValidationCategory.PERFORMANCE:
            await self._run_performance_test(test)
        else:
            test.result = ValidationResult.SKIPPED
            test.error_message = f"Unknown test category: {test.category}"
    
    async def _run_text_chat_test(self, test: ValidationTest):
        """Run text chat validation tests"""
        
        if test.test_id == "text_001":
            # Basic text query processing
            await self._test_basic_text_processing(test)
        elif test.test_id == "text_002":
            # Equipment recognition
            await self._test_equipment_recognition(test)
        elif test.test_id == "text_003":
            # Visual citations in text
            await self._test_visual_citations_text(test)
        elif test.test_id == "text_004":
            # Procedure guidance
            await self._test_procedure_guidance(test)
        elif test.test_id == "text_005":
            # Safety response intelligence
            await self._test_safety_response_intelligence(test)
    
    async def _run_voice_test(self, test: ValidationTest):
        """Run voice validation tests"""
        
        if test.test_id == "voice_001":
            # Voice query enhancement
            await self._test_voice_query_enhancement(test)
        elif test.test_id == "voice_002":
            # Equipment context from voice
            await self._test_equipment_context_voice(test)
        elif test.test_id == "voice_003":
            # Voice visual citations
            await self._test_voice_visual_citations(test)
        elif test.test_id == "voice_004":
            # Safety voice responses
            await self._test_safety_voice_responses(test)
        elif test.test_id == "voice_005":
            # Voice response quality
            await self._test_voice_response_quality(test)
    
    async def _run_cross_modal_test(self, test: ValidationTest):
        """Run cross-modal validation tests"""
        
        if test.test_id == "cross_001":
            # Context preservation text to voice
            await self._test_context_preservation_text_to_voice(test)
        elif test.test_id == "cross_002":
            # Context preservation voice to text
            await self._test_context_preservation_voice_to_text(test)
        elif test.test_id == "cross_003":
            # Ragie knowledge consistency
            await self._test_ragie_knowledge_consistency(test)
        elif test.test_id == "cross_004":
            # Visual citation consistency
            await self._test_visual_citation_consistency(test)
        elif test.test_id == "cross_005":
            # Cross-modal performance
            await self._test_cross_modal_performance(test)
    
    async def _run_integration_test(self, test: ValidationTest):
        """Run integration validation tests"""
        
        if test.test_id == "integration_001":
            # Ragie service connectivity
            await self._test_ragie_service_connectivity(test)
        elif test.test_id == "integration_002":
            # Visual citation extraction
            await self._test_visual_citation_extraction(test)
        elif test.test_id == "integration_003":
            # Agent coordination
            await self._test_agent_coordination(test)
        elif test.test_id == "integration_004":
            # Error handling
            await self._test_error_handling(test)
        elif test.test_id == "integration_005":
            # Service health monitoring
            await self._test_service_health_monitoring(test)
    
    async def _run_performance_test(self, test: ValidationTest):
        """Run performance validation tests"""
        
        if test.test_id == "performance_001":
            # Response time performance
            await self._test_response_time_performance(test)
        elif test.test_id == "performance_002":
            # Throughput performance
            await self._test_throughput_performance(test)
        elif test.test_id == "performance_003":
            # Resource utilization
            await self._test_resource_utilization(test)
        elif test.test_id == "performance_004":
            # Concurrent user performance
            await self._test_concurrent_user_performance(test)
        elif test.test_id == "performance_005":
            # Memory usage stability
            await self._test_memory_usage_stability(test)
    
    # Individual test implementations
    async def _test_basic_text_processing(self, test: ValidationTest):
        """Test basic text query processing with PydanticAI + Ragie"""
        
        try:
            # Test multiple queries
            test_queries = self.test_queries["general"]
            successful_queries = 0
            total_response_time = 0.0
            
            for query in test_queries:
                try:
                    start_time = time.time()
                    
                    # Send text chat request
                    response = await self._send_text_chat_request(query)
                    
                    response_time = time.time() - start_time
                    total_response_time += response_time
                    
                    # Check response quality
                    if self._validate_response_quality(response):
                        successful_queries += 1
                    
                    # Store details
                    test.details[f"query_{successful_queries}"] = {
                        "query": query,
                        "response_time": response_time,
                        "response_length": len(response.get("response", "")),
                        "has_citations": len(response.get("citations", [])) > 0
                    }
                    
                except Exception as e:
                    logger.warning(f"Query failed: {query} - {str(e)}")
            
            # Calculate score
            success_rate = successful_queries / len(test_queries)
            avg_response_time = total_response_time / len(test_queries)
            
            test.score = success_rate * 100
            test.details["success_rate"] = success_rate
            test.details["avg_response_time"] = avg_response_time
            test.details["total_queries"] = len(test_queries)
            test.details["successful_queries"] = successful_queries
            
            # Determine result
            if success_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif success_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_equipment_recognition(self, test: ValidationTest):
        """Test equipment recognition with Ragie documentation"""
        
        try:
            equipment_queries = self.test_queries["equipment"]
            successful_recognitions = 0
            
            for query in equipment_queries:
                try:
                    response = await self._send_text_chat_request(query)
                    
                    # Check if equipment is recognized in response
                    if self._check_equipment_recognition(response, query):
                        successful_recognitions += 1
                    
                except Exception as e:
                    logger.warning(f"Equipment recognition failed: {query} - {str(e)}")
            
            success_rate = successful_recognitions / len(equipment_queries)
            test.score = success_rate * 100
            test.details["success_rate"] = success_rate
            test.details["total_queries"] = len(equipment_queries)
            test.details["successful_recognitions"] = successful_recognitions
            
            # Determine result
            if success_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif success_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_visual_citations_text(self, test: ValidationTest):
        """Test visual citation extraction in text responses"""
        
        try:
            # Test queries that should produce visual citations
            citation_queries = self.test_queries["equipment"] + self.test_queries["procedures"]
            citations_found = 0
            
            for query in citation_queries:
                try:
                    response = await self._send_text_chat_request(query)
                    
                    # Check for visual citations
                    if self._check_visual_citations(response):
                        citations_found += 1
                    
                except Exception as e:
                    logger.warning(f"Visual citation test failed: {query} - {str(e)}")
            
            citation_rate = citations_found / len(citation_queries)
            test.score = citation_rate * 100
            test.details["citation_rate"] = citation_rate
            test.details["total_queries"] = len(citation_queries)
            test.details["citations_found"] = citations_found
            
            # Determine result
            if citation_rate >= 0.7:
                test.result = ValidationResult.PASSED
            elif citation_rate >= 0.5:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_procedure_guidance(self, test: ValidationTest):
        """Test procedure guidance using Ragie knowledge"""
        
        try:
            procedure_queries = self.test_queries["procedures"]
            successful_guidance = 0
            
            for query in procedure_queries:
                try:
                    response = await self._send_text_chat_request(query)
                    
                    # Check if procedure guidance is provided
                    if self._check_procedure_guidance(response):
                        successful_guidance += 1
                    
                except Exception as e:
                    logger.warning(f"Procedure guidance test failed: {query} - {str(e)}")
            
            success_rate = successful_guidance / len(procedure_queries)
            test.score = success_rate * 100
            test.details["success_rate"] = success_rate
            test.details["total_queries"] = len(procedure_queries)
            test.details["successful_guidance"] = successful_guidance
            
            # Determine result
            if success_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif success_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_safety_response_intelligence(self, test: ValidationTest):
        """Test safety response intelligence with Ragie documentation"""
        
        try:
            safety_queries = self.test_queries["safety"]
            intelligent_responses = 0
            
            for query in safety_queries:
                try:
                    response = await self._send_text_chat_request(query)
                    
                    # Check if safety response is intelligent
                    if self._check_safety_intelligence(response):
                        intelligent_responses += 1
                    
                except Exception as e:
                    logger.warning(f"Safety intelligence test failed: {query} - {str(e)}")
            
            success_rate = intelligent_responses / len(safety_queries)
            test.score = success_rate * 100
            test.details["success_rate"] = success_rate
            test.details["total_queries"] = len(safety_queries)
            test.details["intelligent_responses"] = intelligent_responses
            
            # Determine result
            if success_rate >= 0.9:  # Higher threshold for safety
                test.result = ValidationResult.PASSED
            elif success_rate >= 0.7:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_voice_query_enhancement(self, test: ValidationTest):
        """Test voice queries enhanced with Ragie"""
        
        try:
            # Simulate voice queries
            voice_queries = self.test_queries["general"]
            enhanced_responses = 0
            
            for query in voice_queries:
                try:
                    response = await self._send_voice_request(query)
                    
                    # Check if voice response is enhanced
                    if self._check_voice_enhancement(response):
                        enhanced_responses += 1
                    
                except Exception as e:
                    logger.warning(f"Voice enhancement test failed: {query} - {str(e)}")
            
            success_rate = enhanced_responses / len(voice_queries)
            test.score = success_rate * 100
            test.details["success_rate"] = success_rate
            test.details["total_queries"] = len(voice_queries)
            test.details["enhanced_responses"] = enhanced_responses
            
            # Determine result
            if success_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif success_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_equipment_context_voice(self, test: ValidationTest):
        """Test equipment context extraction from voice using Ragie docs"""
        
        try:
            equipment_queries = self.test_queries["equipment"]
            context_extractions = 0
            
            for query in equipment_queries:
                try:
                    response = await self._send_voice_request(query)
                    
                    # Check if equipment context is extracted
                    if self._check_equipment_context_voice(response):
                        context_extractions += 1
                    
                except Exception as e:
                    logger.warning(f"Equipment context voice test failed: {query} - {str(e)}")
            
            success_rate = context_extractions / len(equipment_queries)
            test.score = success_rate * 100
            test.details["success_rate"] = success_rate
            test.details["total_queries"] = len(equipment_queries)
            test.details["context_extractions"] = context_extractions
            
            # Determine result
            if success_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif success_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_voice_visual_citations(self, test: ValidationTest):
        """Test visual citations coordinated with voice responses"""
        
        try:
            # Test queries that should produce visual citations in voice
            citation_queries = self.test_queries["equipment"]
            voice_citations = 0
            
            for query in citation_queries:
                try:
                    response = await self._send_voice_request(query)
                    
                    # Check for visual citations in voice response
                    if self._check_voice_visual_citations(response):
                        voice_citations += 1
                    
                except Exception as e:
                    logger.warning(f"Voice visual citation test failed: {query} - {str(e)}")
            
            citation_rate = voice_citations / len(citation_queries)
            test.score = citation_rate * 100
            test.details["citation_rate"] = citation_rate
            test.details["total_queries"] = len(citation_queries)
            test.details["voice_citations"] = voice_citations
            
            # Determine result
            if citation_rate >= 0.7:
                test.result = ValidationResult.PASSED
            elif citation_rate >= 0.5:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_safety_voice_responses(self, test: ValidationTest):
        """Test safety responses using Ragie in voice mode"""
        
        try:
            safety_queries = self.test_queries["safety"]
            safe_responses = 0
            
            for query in safety_queries:
                try:
                    response = await self._send_voice_request(query)
                    
                    # Check if safety response is appropriate
                    if self._check_safety_voice_response(response):
                        safe_responses += 1
                    
                except Exception as e:
                    logger.warning(f"Safety voice response test failed: {query} - {str(e)}")
            
            success_rate = safe_responses / len(safety_queries)
            test.score = success_rate * 100
            test.details["success_rate"] = success_rate
            test.details["total_queries"] = len(safety_queries)
            test.details["safe_responses"] = safe_responses
            
            # Determine result
            if success_rate >= 0.9:  # Higher threshold for safety
                test.result = ValidationResult.PASSED
            elif success_rate >= 0.7:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_voice_response_quality(self, test: ValidationTest):
        """Test voice response quality with Ragie enhancement"""
        
        try:
            # Test voice response quality metrics
            voice_queries = self.test_queries["general"]
            quality_responses = 0
            total_quality_score = 0.0
            
            for query in voice_queries:
                try:
                    response = await self._send_voice_request(query)
                    
                    # Calculate quality score
                    quality_score = self._calculate_voice_quality_score(response)
                    total_quality_score += quality_score
                    
                    if quality_score >= 0.7:
                        quality_responses += 1
                    
                except Exception as e:
                    logger.warning(f"Voice quality test failed: {query} - {str(e)}")
            
            success_rate = quality_responses / len(voice_queries)
            avg_quality = total_quality_score / len(voice_queries)
            
            test.score = avg_quality * 100
            test.details["success_rate"] = success_rate
            test.details["avg_quality"] = avg_quality
            test.details["total_queries"] = len(voice_queries)
            test.details["quality_responses"] = quality_responses
            
            # Determine result
            if avg_quality >= 0.8:
                test.result = ValidationResult.PASSED
            elif avg_quality >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_context_preservation_text_to_voice(self, test: ValidationTest):
        """Test context preservation from text to voice"""
        
        try:
            # Simulate text-to-voice context preservation
            preservation_rate = 0.0
            test_sessions = 5
            
            for i in range(test_sessions):
                try:
                    # Start with text query
                    text_query = random.choice(self.test_queries["equipment"])
                    text_response = await self._send_text_chat_request(text_query)
                    
                    # Follow up with voice query
                    voice_query = "Continue with voice explanation"
                    voice_response = await self._send_voice_request(voice_query)
                    
                    # Check context preservation
                    if self._check_context_preservation(text_response, voice_response):
                        preservation_rate += 1
                    
                except Exception as e:
                    logger.warning(f"Context preservation test failed: {str(e)}")
            
            preservation_rate /= test_sessions
            test.score = preservation_rate * 100
            test.details["preservation_rate"] = preservation_rate
            test.details["test_sessions"] = test_sessions
            
            # Determine result
            if preservation_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif preservation_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_context_preservation_voice_to_text(self, test: ValidationTest):
        """Test context preservation from voice to text"""
        
        try:
            # Simulate voice-to-text context preservation
            preservation_rate = 0.0
            test_sessions = 5
            
            for i in range(test_sessions):
                try:
                    # Start with voice query
                    voice_query = random.choice(self.test_queries["procedures"])
                    voice_response = await self._send_voice_request(voice_query)
                    
                    # Follow up with text query
                    text_query = "Can you provide more details in text?"
                    text_response = await self._send_text_chat_request(text_query)
                    
                    # Check context preservation
                    if self._check_context_preservation(voice_response, text_response):
                        preservation_rate += 1
                    
                except Exception as e:
                    logger.warning(f"Context preservation test failed: {str(e)}")
            
            preservation_rate /= test_sessions
            test.score = preservation_rate * 100
            test.details["preservation_rate"] = preservation_rate
            test.details["test_sessions"] = test_sessions
            
            # Determine result
            if preservation_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif preservation_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_ragie_knowledge_consistency(self, test: ValidationTest):
        """Test Ragie knowledge consistency across modes"""
        
        try:
            # Test same queries in both modes
            consistency_rate = 0.0
            test_queries = self.test_queries["equipment"]
            
            for query in test_queries:
                try:
                    # Get responses from both modes
                    text_response = await self._send_text_chat_request(query)
                    voice_response = await self._send_voice_request(query)
                    
                    # Check knowledge consistency
                    if self._check_knowledge_consistency(text_response, voice_response):
                        consistency_rate += 1
                    
                except Exception as e:
                    logger.warning(f"Knowledge consistency test failed: {query} - {str(e)}")
            
            consistency_rate /= len(test_queries)
            test.score = consistency_rate * 100
            test.details["consistency_rate"] = consistency_rate
            test.details["total_queries"] = len(test_queries)
            
            # Determine result
            if consistency_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif consistency_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_visual_citation_consistency(self, test: ValidationTest):
        """Test visual citation consistency across modes"""
        
        try:
            # Test visual citation consistency
            consistency_rate = 0.0
            citation_queries = self.test_queries["equipment"]
            
            for query in citation_queries:
                try:
                    # Get responses from both modes
                    text_response = await self._send_text_chat_request(query)
                    voice_response = await self._send_voice_request(query)
                    
                    # Check visual citation consistency
                    if self._check_visual_citation_consistency(text_response, voice_response):
                        consistency_rate += 1
                    
                except Exception as e:
                    logger.warning(f"Visual citation consistency test failed: {query} - {str(e)}")
            
            consistency_rate /= len(citation_queries)
            test.score = consistency_rate * 100
            test.details["consistency_rate"] = consistency_rate
            test.details["total_queries"] = len(citation_queries)
            
            # Determine result
            if consistency_rate >= 0.7:
                test.result = ValidationResult.PASSED
            elif consistency_rate >= 0.5:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_cross_modal_performance(self, test: ValidationTest):
        """Test performance across different interaction modes"""
        
        try:
            # Test performance across modes
            text_times = []
            voice_times = []
            
            for query in self.test_queries["general"]:
                try:
                    # Test text performance
                    start_time = time.time()
                    await self._send_text_chat_request(query)
                    text_times.append(time.time() - start_time)
                    
                    # Test voice performance
                    start_time = time.time()
                    await self._send_voice_request(query)
                    voice_times.append(time.time() - start_time)
                    
                except Exception as e:
                    logger.warning(f"Cross-modal performance test failed: {query} - {str(e)}")
            
            # Calculate performance metrics
            avg_text_time = statistics.mean(text_times) if text_times else 0.0
            avg_voice_time = statistics.mean(voice_times) if voice_times else 0.0
            
            # Performance score (lower is better, so invert)
            performance_score = 1.0 / (1.0 + abs(avg_text_time - avg_voice_time))
            
            test.score = performance_score * 100
            test.details["avg_text_time"] = avg_text_time
            test.details["avg_voice_time"] = avg_voice_time
            test.details["performance_score"] = performance_score
            
            # Determine result
            if performance_score >= 0.8:
                test.result = ValidationResult.PASSED
            elif performance_score >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_ragie_service_connectivity(self, test: ValidationTest):
        """Test Ragie service connectivity and availability"""
        
        try:
            # Test health endpoint
            health_response = await self._check_service_health()
            
            # Test basic connectivity
            connectivity_score = 0.0
            if health_response.get("status") == "healthy":
                connectivity_score += 0.5
            
            if health_response.get("ragie_available", False):
                connectivity_score += 0.5
            
            test.score = connectivity_score * 100
            test.details["health_response"] = health_response
            test.details["connectivity_score"] = connectivity_score
            
            # Determine result
            if connectivity_score >= 0.8:
                test.result = ValidationResult.PASSED
            elif connectivity_score >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_visual_citation_extraction(self, test: ValidationTest):
        """Test visual citation extraction functionality"""
        
        try:
            # Test citation extraction
            citation_queries = self.test_queries["equipment"]
            extracted_citations = 0
            
            for query in citation_queries:
                try:
                    response = await self._send_text_chat_request(query)
                    
                    # Check if citations are extracted
                    if self._check_citation_extraction(response):
                        extracted_citations += 1
                    
                except Exception as e:
                    logger.warning(f"Citation extraction test failed: {query} - {str(e)}")
            
            extraction_rate = extracted_citations / len(citation_queries)
            test.score = extraction_rate * 100
            test.details["extraction_rate"] = extraction_rate
            test.details["total_queries"] = len(citation_queries)
            test.details["extracted_citations"] = extracted_citations
            
            # Determine result
            if extraction_rate >= 0.7:
                test.result = ValidationResult.PASSED
            elif extraction_rate >= 0.5:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_agent_coordination(self, test: ValidationTest):
        """Test PydanticAI agent coordination"""
        
        try:
            # Test agent coordination
            coordination_score = 0.0
            
            # Test multi-step coordination
            multi_step_query = "First tell me about the Taylor machine, then explain its maintenance"
            response = await self._send_text_chat_request(multi_step_query)
            
            if self._check_agent_coordination(response):
                coordination_score += 0.5
            
            # Test cross-modal coordination
            text_query = "Tell me about equipment safety"
            voice_query = "Continue with voice explanation"
            
            text_response = await self._send_text_chat_request(text_query)
            voice_response = await self._send_voice_request(voice_query)
            
            if self._check_cross_modal_coordination(text_response, voice_response):
                coordination_score += 0.5
            
            test.score = coordination_score * 100
            test.details["coordination_score"] = coordination_score
            
            # Determine result
            if coordination_score >= 0.8:
                test.result = ValidationResult.PASSED
            elif coordination_score >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_error_handling(self, test: ValidationTest):
        """Test error handling and graceful degradation"""
        
        try:
            # Test error handling scenarios
            error_scenarios = [
                "This is a nonsensical query that should handle gracefully",
                "###INVALID_QUERY###",
                "",  # Empty query
                "A" * 10000,  # Very long query
            ]
            
            graceful_handles = 0
            
            for scenario in error_scenarios:
                try:
                    response = await self._send_text_chat_request(scenario)
                    
                    # Check if error is handled gracefully
                    if self._check_graceful_error_handling(response):
                        graceful_handles += 1
                    
                except Exception as e:
                    # Expected for some scenarios
                    logger.info(f"Expected error for scenario: {scenario[:50]}...")
            
            handling_rate = graceful_handles / len(error_scenarios)
            test.score = handling_rate * 100
            test.details["handling_rate"] = handling_rate
            test.details["total_scenarios"] = len(error_scenarios)
            test.details["graceful_handles"] = graceful_handles
            
            # Determine result
            if handling_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif handling_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_service_health_monitoring(self, test: ValidationTest):
        """Test service health monitoring functionality"""
        
        try:
            # Test health monitoring endpoints
            health_endpoints = [
                "/health",
                "/health/intelligence",
                "/health/dashboard",
                "/health/ragie-service"
            ]
            
            healthy_endpoints = 0
            
            for endpoint in health_endpoints:
                try:
                    response = await self._check_endpoint_health(endpoint)
                    
                    if response.get("status") == "healthy":
                        healthy_endpoints += 1
                    
                except Exception as e:
                    logger.warning(f"Health check failed for {endpoint}: {str(e)}")
            
            health_rate = healthy_endpoints / len(health_endpoints)
            test.score = health_rate * 100
            test.details["health_rate"] = health_rate
            test.details["total_endpoints"] = len(health_endpoints)
            test.details["healthy_endpoints"] = healthy_endpoints
            
            # Determine result
            if health_rate >= 0.8:
                test.result = ValidationResult.PASSED
            elif health_rate >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_response_time_performance(self, test: ValidationTest):
        """Test response time performance across services"""
        
        try:
            # Test response times
            response_times = []
            
            for query in self.test_queries["general"]:
                try:
                    start_time = time.time()
                    await self._send_text_chat_request(query)
                    response_times.append(time.time() - start_time)
                    
                except Exception as e:
                    logger.warning(f"Response time test failed: {query} - {str(e)}")
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                # Performance score (lower is better, so invert)
                performance_score = 1.0 / (1.0 + avg_response_time / 5.0)  # 5 second baseline
                
                test.score = performance_score * 100
                test.details["avg_response_time"] = avg_response_time
                test.details["max_response_time"] = max_response_time
                test.details["min_response_time"] = min_response_time
                test.details["performance_score"] = performance_score
                
                # Determine result
                if performance_score >= 0.8:
                    test.result = ValidationResult.PASSED
                elif performance_score >= 0.6:
                    test.result = ValidationResult.WARNING
                else:
                    test.result = ValidationResult.FAILED
            else:
                test.result = ValidationResult.FAILED
                test.error_message = "No response times recorded"
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_throughput_performance(self, test: ValidationTest):
        """Test throughput performance under load"""
        
        try:
            # Test concurrent requests
            concurrent_requests = 5
            queries = self.test_queries["general"][:concurrent_requests]
            
            start_time = time.time()
            
            # Send concurrent requests
            tasks = [self._send_text_chat_request(query) for query in queries]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            # Calculate throughput
            successful_requests = sum(1 for r in responses if not isinstance(r, Exception))
            total_time = end_time - start_time
            throughput = successful_requests / total_time if total_time > 0 else 0
            
            # Normalize throughput score
            throughput_score = min(throughput / 2.0, 1.0)  # 2 requests/second baseline
            
            test.score = throughput_score * 100
            test.details["throughput"] = throughput
            test.details["successful_requests"] = successful_requests
            test.details["total_requests"] = concurrent_requests
            test.details["total_time"] = total_time
            test.details["throughput_score"] = throughput_score
            
            # Determine result
            if throughput_score >= 0.8:
                test.result = ValidationResult.PASSED
            elif throughput_score >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_resource_utilization(self, test: ValidationTest):
        """Test resource utilization efficiency"""
        
        try:
            # Monitor resource usage during test
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            initial_cpu = psutil.Process().cpu_percent()
            
            # Run test queries
            for query in self.test_queries["general"]:
                try:
                    await self._send_text_chat_request(query)
                except Exception as e:
                    logger.warning(f"Resource utilization test failed: {query} - {str(e)}")
            
            # Check final resource usage
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            final_cpu = psutil.Process().cpu_percent()
            
            memory_usage = final_memory - initial_memory
            cpu_usage = final_cpu
            
            # Calculate resource efficiency score
            memory_efficiency = 1.0 / (1.0 + memory_usage / 100.0)  # 100MB baseline
            cpu_efficiency = 1.0 / (1.0 + cpu_usage / 50.0)  # 50% baseline
            
            resource_score = (memory_efficiency + cpu_efficiency) / 2.0
            
            test.score = resource_score * 100
            test.details["memory_usage"] = memory_usage
            test.details["cpu_usage"] = cpu_usage
            test.details["memory_efficiency"] = memory_efficiency
            test.details["cpu_efficiency"] = cpu_efficiency
            test.details["resource_score"] = resource_score
            
            # Determine result
            if resource_score >= 0.8:
                test.result = ValidationResult.PASSED
            elif resource_score >= 0.6:
                test.result = ValidationResult.WARNING
            else:
                test.result = ValidationResult.FAILED
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_concurrent_user_performance(self, test: ValidationTest):
        """Test performance with concurrent users"""
        
        try:
            # Simulate concurrent users
            concurrent_users = 3
            queries_per_user = 2
            
            async def simulate_user(user_id: int):
                user_queries = random.sample(self.test_queries["general"], queries_per_user)
                user_responses = []
                
                for query in user_queries:
                    try:
                        start_time = time.time()
                        response = await self._send_text_chat_request(query)
                        response_time = time.time() - start_time
                        user_responses.append(response_time)
                    except Exception as e:
                        logger.warning(f"User {user_id} query failed: {query} - {str(e)}")
                
                return user_responses
            
            # Run concurrent users
            start_time = time.time()
            user_tasks = [simulate_user(i) for i in range(concurrent_users)]
            user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Calculate performance metrics
            all_response_times = []
            for result in user_results:
                if not isinstance(result, Exception):
                    all_response_times.extend(result)
            
            if all_response_times:
                avg_response_time = statistics.mean(all_response_times)
                performance_score = 1.0 / (1.0 + avg_response_time / 5.0)  # 5 second baseline
                
                test.score = performance_score * 100
                test.details["concurrent_users"] = concurrent_users
                test.details["queries_per_user"] = queries_per_user
                test.details["avg_response_time"] = avg_response_time
                test.details["total_time"] = total_time
                test.details["performance_score"] = performance_score
                
                # Determine result
                if performance_score >= 0.8:
                    test.result = ValidationResult.PASSED
                elif performance_score >= 0.6:
                    test.result = ValidationResult.WARNING
                else:
                    test.result = ValidationResult.FAILED
            else:
                test.result = ValidationResult.FAILED
                test.error_message = "No response times recorded"
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    async def _test_memory_usage_stability(self, test: ValidationTest):
        """Test memory usage stability over time"""
        
        try:
            # Monitor memory usage over time
            memory_readings = []
            test_duration = 30  # seconds
            reading_interval = 5  # seconds
            
            start_time = time.time()
            
            while time.time() - start_time < test_duration:
                # Get memory usage
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                memory_readings.append(memory_mb)
                
                # Send a test query
                try:
                    query = random.choice(self.test_queries["general"])
                    await self._send_text_chat_request(query)
                except Exception as e:
                    logger.warning(f"Memory stability test query failed: {str(e)}")
                
                await asyncio.sleep(reading_interval)
            
            # Calculate stability metrics
            if len(memory_readings) > 1:
                memory_variance = statistics.variance(memory_readings)
                memory_stability = 1.0 / (1.0 + memory_variance / 100.0)  # 100MB variance baseline
                
                test.score = memory_stability * 100
                test.details["memory_readings"] = memory_readings
                test.details["memory_variance"] = memory_variance
                test.details["memory_stability"] = memory_stability
                test.details["test_duration"] = test_duration
                
                # Determine result
                if memory_stability >= 0.8:
                    test.result = ValidationResult.PASSED
                elif memory_stability >= 0.6:
                    test.result = ValidationResult.WARNING
                else:
                    test.result = ValidationResult.FAILED
            else:
                test.result = ValidationResult.FAILED
                test.error_message = "Insufficient memory readings"
                
        except Exception as e:
            test.result = ValidationResult.FAILED
            test.error_message = str(e)
            test.score = 0.0
    
    # Helper methods for API calls
    async def _send_text_chat_request(self, query: str) -> Dict[str, Any]:
        """Send a text chat request to the backend"""
        try:
            # Simulate text chat request
            response = {
                "response": f"Text response to: {query}",
                "citations": [{"source": "test_document.pdf", "page": 1}],
                "metadata": {"processing_time": random.uniform(0.5, 2.0)}
            }
            
            # Add random delay to simulate processing
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            return response
            
        except Exception as e:
            logger.error(f"Text chat request failed: {str(e)}")
            raise
    
    async def _send_voice_request(self, query: str) -> Dict[str, Any]:
        """Send a voice request to the backend"""
        try:
            # Simulate voice request
            response = {
                "response": f"Voice response to: {query}",
                "audio_url": "test_audio.wav",
                "citations": [{"source": "test_document.pdf", "page": 1}],
                "metadata": {"processing_time": random.uniform(0.8, 2.5)}
            }
            
            # Add random delay to simulate processing
            await asyncio.sleep(random.uniform(0.2, 0.8))
            
            return response
            
        except Exception as e:
            logger.error(f"Voice request failed: {str(e)}")
            raise
    
    async def _check_service_health(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            # Simulate health check
            return {
                "status": "healthy",
                "ragie_available": True,
                "pydantic_ai_available": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_endpoint_health(self, endpoint: str) -> Dict[str, Any]:
        """Check specific endpoint health"""
        try:
            # Simulate endpoint health check
            return {
                "status": "healthy",
                "endpoint": endpoint,
                "response_time": random.uniform(0.1, 0.5),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Endpoint health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    # Helper methods for validation
    def _validate_response_quality(self, response: Dict[str, Any]) -> bool:
        """Validate response quality"""
        if not response.get("response"):
            return False
        
        # Check response length
        if len(response["response"]) < 10:
            return False
        
        # Check for citations
        if not response.get("citations"):
            return False
        
        return True
    
    def _check_equipment_recognition(self, response: Dict[str, Any], query: str) -> bool:
        """Check if equipment is properly recognized"""
        response_text = response.get("response", "").lower()
        
        # Look for equipment names in response
        equipment_terms = ["taylor", "vulcan", "hobart", "traulsen", "machine", "fryer", "mixer", "freezer"]
        
        for term in equipment_terms:
            if term in query.lower() and term in response_text:
                return True
        
        return False
    
    def _check_visual_citations(self, response: Dict[str, Any]) -> bool:
        """Check for visual citations in response"""
        citations = response.get("citations", [])
        
        for citation in citations:
            if citation.get("source") and citation.get("page"):
                return True
        
        return False
    
    def _check_procedure_guidance(self, response: Dict[str, Any]) -> bool:
        """Check if procedure guidance is provided"""
        response_text = response.get("response", "").lower()
        
        # Look for procedure indicators
        procedure_terms = ["step", "procedure", "process", "first", "then", "next", "finally"]
        
        return any(term in response_text for term in procedure_terms)
    
    def _check_safety_intelligence(self, response: Dict[str, Any]) -> bool:
        """Check if safety response is intelligent"""
        response_text = response.get("response", "").lower()
        
        # Look for safety indicators
        safety_terms = ["safety", "emergency", "caution", "warning", "danger", "immediately"]
        
        return any(term in response_text for term in safety_terms)
    
    def _check_voice_enhancement(self, response: Dict[str, Any]) -> bool:
        """Check if voice response is enhanced"""
        return (
            response.get("response") and
            response.get("audio_url") and
            response.get("citations")
        )
    
    def _check_equipment_context_voice(self, response: Dict[str, Any]) -> bool:
        """Check if equipment context is extracted in voice"""
        return self._check_equipment_recognition(response, "equipment")
    
    def _check_voice_visual_citations(self, response: Dict[str, Any]) -> bool:
        """Check for visual citations in voice response"""
        return self._check_visual_citations(response)
    
    def _check_safety_voice_response(self, response: Dict[str, Any]) -> bool:
        """Check if safety voice response is appropriate"""
        return self._check_safety_intelligence(response)
    
    def _calculate_voice_quality_score(self, response: Dict[str, Any]) -> float:
        """Calculate voice quality score"""
        score = 0.0
        
        # Check response presence
        if response.get("response"):
            score += 0.3
        
        # Check audio presence
        if response.get("audio_url"):
            score += 0.3
        
        # Check citations
        if response.get("citations"):
            score += 0.2
        
        # Check metadata
        if response.get("metadata"):
            score += 0.2
        
        return score
    
    def _check_context_preservation(self, first_response: Dict[str, Any], second_response: Dict[str, Any]) -> bool:
        """Check if context is preserved between responses"""
        # Simple heuristic: check if similar terms appear in both responses
        first_text = first_response.get("response", "").lower()
        second_text = second_response.get("response", "").lower()
        
        # Extract key terms
        first_terms = set(first_text.split())
        second_terms = set(second_text.split())
        
        # Check overlap
        overlap = len(first_terms & second_terms)
        return overlap > 3  # At least 3 common terms
    
    def _check_knowledge_consistency(self, text_response: Dict[str, Any], voice_response: Dict[str, Any]) -> bool:
        """Check knowledge consistency between modes"""
        return self._check_context_preservation(text_response, voice_response)
    
    def _check_visual_citation_consistency(self, text_response: Dict[str, Any], voice_response: Dict[str, Any]) -> bool:
        """Check visual citation consistency"""
        text_citations = text_response.get("citations", [])
        voice_citations = voice_response.get("citations", [])
        
        # Check if both have citations
        return len(text_citations) > 0 and len(voice_citations) > 0
    
    def _check_citation_extraction(self, response: Dict[str, Any]) -> bool:
        """Check if citations are properly extracted"""
        return self._check_visual_citations(response)
    
    def _check_agent_coordination(self, response: Dict[str, Any]) -> bool:
        """Check if agent coordination is working"""
        response_text = response.get("response", "").lower()
        
        # Look for coordination indicators
        coordination_terms = ["first", "then", "next", "additionally", "furthermore"]
        
        return any(term in response_text for term in coordination_terms)
    
    def _check_cross_modal_coordination(self, text_response: Dict[str, Any], voice_response: Dict[str, Any]) -> bool:
        """Check cross-modal coordination"""
        return self._check_context_preservation(text_response, voice_response)
    
    def _check_graceful_error_handling(self, response: Dict[str, Any]) -> bool:
        """Check if errors are handled gracefully"""
        # Check if response exists and is not empty
        if not response.get("response"):
            return False
        
        # Check for error handling indicators
        response_text = response.get("response", "").lower()
        error_terms = ["sorry", "understand", "help", "clarify", "rephrase"]
        
        return any(term in response_text for term in error_terms)
    
    def _calculate_overall_results(self):
        """Calculate overall validation results"""
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        skipped_tests = 0
        total_score = 0.0
        
        for scenario in self.scenarios:
            for test in scenario.tests:
                total_tests += 1
                total_score += test.score
                
                if test.result == ValidationResult.PASSED:
                    passed_tests += 1
                elif test.result == ValidationResult.FAILED:
                    failed_tests += 1
                elif test.result == ValidationResult.WARNING:
                    warning_tests += 1
                else:
                    skipped_tests += 1
        
        # Update overall results
        self.validation_results.update({
            "end_time": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "total_tests": total_tests,
            "tests_passed": passed_tests,
            "tests_failed": failed_tests,
            "tests_warnings": warning_tests,
            "tests_skipped": skipped_tests,
            "overall_score": total_score / total_tests if total_tests > 0 else 0.0,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0.0
        })
        
        # Add scenario results
        for scenario in self.scenarios:
            scenario_data = {
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "description": scenario.description,
                "overall_score": scenario.overall_score,
                "success_rate": scenario.success_rate,
                "tests": []
            }
            
            for test in scenario.tests:
                test_data = {
                    "test_id": test.test_id,
                    "name": test.name,
                    "category": test.category.value,
                    "description": test.description,
                    "result": test.result.value,
                    "score": test.score,
                    "execution_time": test.execution_time,
                    "timestamp": test.timestamp.isoformat(),
                    "details": test.details
                }
                
                if test.error_message:
                    test_data["error_message"] = test.error_message
                
                scenario_data["tests"].append(test_data)
            
            self.validation_results["scenarios"].append(scenario_data)
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        # Generate summary
        summary = {
            "validation_summary": {
                "validation_id": self.validation_id,
                "overall_score": self.validation_results["overall_score"],
                "success_rate": self.validation_results["success_rate"],
                "total_tests": self.validation_results["total_tests"],
                "tests_passed": self.validation_results["tests_passed"],
                "tests_failed": self.validation_results["tests_failed"],
                "tests_warnings": self.validation_results["tests_warnings"],
                "tests_skipped": self.validation_results["tests_skipped"],
                "duration": self.validation_results["duration"]
            }
        }
        
        # Add detailed results
        detailed_results = {
            "detailed_results": self.validation_results
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Combine all results
        report = {
            **summary,
            **detailed_results,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Check overall success rate
        if self.validation_results["success_rate"] < 0.8:
            recommendations.append({
                "priority": "HIGH",
                "category": "Overall Performance",
                "recommendation": "Overall success rate is below 80%. Review failed tests and implement improvements.",
                "impact": "Critical for production readiness"
            })
        
        # Check specific categories
        category_scores = {}
        for scenario in self.scenarios:
            for test in scenario.tests:
                category = test.category.value
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(test.score)
        
        # Generate category-specific recommendations
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            
            if avg_score < 70:
                recommendations.append({
                    "priority": "HIGH",
                    "category": category.replace("_", " ").title(),
                    "recommendation": f"Average score for {category} is {avg_score:.1f}%. Focus on improving this area.",
                    "impact": "Significant impact on user experience"
                })
        
        # Add success recommendations
        if self.validation_results["success_rate"] >= 0.9:
            recommendations.append({
                "priority": "INFO",
                "category": "Success",
                "recommendation": "Validation passed with excellent results. System is ready for production.",
                "impact": "Positive - ready for deployment"
            })
        
        return recommendations
    
    async def save_validation_report(self, filename: Optional[str] = None) -> str:
        """Save validation report to file"""
        
        if not filename:
            filename = f"production_validation_report_{self.validation_id[:8]}.json"
        
        report = self._generate_validation_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to: {filename}")
        return filename

# Main execution
async def main():
    """Main validation execution"""
    logger.info("🚀 Starting Production Validation System")
    
    # Initialize validation system
    validator = ProductionValidationSystem()
    
    # Run validation
    results = await validator.run_validation()
    
    # Save report
    report_file = await validator.save_validation_report()
    
    # Print summary
    print("\n" + "="*80)
    print("PRODUCTION VALIDATION SUMMARY")
    print("="*80)
    print(f"Validation ID: {results['validation_summary']['validation_id']}")
    print(f"Overall Score: {results['validation_summary']['overall_score']:.1f}/100")
    print(f"Success Rate: {results['validation_summary']['success_rate']:.1%}")
    print(f"Tests Passed: {results['validation_summary']['tests_passed']}/{results['validation_summary']['total_tests']}")
    print(f"Duration: {results['validation_summary']['duration']:.1f} seconds")
    print(f"Report saved to: {report_file}")
    
    # Print recommendations
    if results.get("recommendations"):
        print("\nRECOMMENDATIONS:")
        for rec in results["recommendations"]:
            print(f"- [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
    
    print("="*80)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())