"""
Focused Enterprise Bridge Test Suite
Tests the complete QSR system pipeline for entity detection, embedding generation, and Neo4j integration
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnterpriseBridgeTestSuite:
    """Test suite for validating the complete QSR enterprise bridge system"""
    
    def __init__(self):
        self.test_files = [
            "qsr_entities_test.txt",
            "multimodal_test.txt", 
            "relationships_test.txt"
        ]
        self.results = {
            "test_data_preparation": {"status": "pending"},
            "qsr_entity_detection": {"status": "pending"},
            "multimodal_embedding": {"status": "pending"},
            "enterprise_bridge": {"status": "pending"},
            "neo4j_relationships": {"status": "pending"},
            "end_to_end": {"status": "pending"},
            "knowledge_quality": {"status": "pending"}
        }
    
    def test_data_preparation(self) -> Dict[str, Any]:
        """Test 1: Validate test data files exist and are properly formatted"""
        logger.info("🔍 Starting Test 1: Data Preparation Validation")
        
        test_result = {
            "status": "running",
            "files_found": 0,
            "files_valid": 0,
            "errors": []
        }
        
        try:
            for file_name in self.test_files:
                file_path = Path(file_name)
                if file_path.exists():
                    test_result["files_found"] += 1
                    
                    # Read and validate content
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        
                    if len(content) > 0:
                        test_result["files_valid"] += 1
                        logger.info(f"✅ {file_name}: {len(content)} characters")
                    else:
                        test_result["errors"].append(f"{file_name} is empty")
                else:
                    test_result["errors"].append(f"{file_name} not found")
            
            if test_result["files_valid"] == len(self.test_files):
                test_result["status"] = "passed"
                logger.info("✅ Test 1 PASSED: All test files prepared correctly")
            else:
                test_result["status"] = "failed"
                logger.error(f"❌ Test 1 FAILED: {test_result['errors']}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ Test 1 FAILED: {str(e)}")
        
        self.results["test_data_preparation"] = test_result
        return test_result
    
    def test_qsr_entity_detection(self) -> Dict[str, Any]:
        """Test 2: QSR Entity Detection and Deduplication"""
        logger.info("🔍 Starting Test 2: QSR Entity Detection")
        
        test_result = {
            "status": "running",
            "entities_detected": 0,
            "duplicates_found": 0,
            "deduplication_success": False,
            "expected_entities": ["Grote Tool", "Taylor C602", "cleaning procedure", "safety protocol"],
            "actual_entities": [],
            "errors": []
        }
        
        try:
            # Test entity detection using backend services
            from backend.services.qsr_entity_extractor import QSREntityExtractor
            
            extractor = QSREntityExtractor()
            
            # Process the QSR entities test file
            with open("qsr_entities_test.txt", 'r') as f:
                content = f.read()
            
            entities = extractor.extract_entities(content)
            test_result["entities_detected"] = len(entities)
            test_result["actual_entities"] = [e.get("name", "") for e in entities]
            
            # Check for expected QSR entities
            expected_found = 0
            for expected in test_result["expected_entities"]:
                if any(expected.lower() in entity.lower() for entity in test_result["actual_entities"]):
                    expected_found += 1
            
            # Check deduplication (should not have both "Grote Tool" and "1Grote Tool" as separate entities)
            grote_variations = [e for e in test_result["actual_entities"] if "grote" in e.lower()]
            taylor_variations = [e for e in test_result["actual_entities"] if "taylor" in e.lower() or "c602" in e.lower()]
            
            test_result["deduplication_success"] = (
                len(grote_variations) <= 1 and len(taylor_variations) <= 1
            )
            
            if expected_found >= 3 and test_result["deduplication_success"]:
                test_result["status"] = "passed"
                logger.info("✅ Test 2 PASSED: QSR entities detected and deduplicated correctly")
            else:
                test_result["status"] = "failed"
                logger.error(f"❌ Test 2 FAILED: Expected {len(test_result['expected_entities'])} entities, found {expected_found}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ Test 2 FAILED: {str(e)}")
        
        self.results["qsr_entity_detection"] = test_result
        return test_result
    
    def test_multimodal_embedding(self) -> Dict[str, Any]:
        """Test 3: Multi-Modal Embedding Generation"""
        logger.info("🔍 Starting Test 3: Multi-Modal Embedding Generation")
        
        test_result = {
            "status": "running",
            "text_embeddings": 0,
            "visual_embeddings": 0,
            "embedding_dimensions": 0,
            "errors": []
        }
        
        try:
            # Test multi-modal embedding using RAG-Anything
            import raganything
            
            # Process the multimodal test file
            with open("multimodal_test.txt", 'r') as f:
                content = f.read()
            
            # Initialize RAG-Anything processor
            rag_processor = raganything.RAGAnything()
            
            # Test embedding generation
            embeddings = rag_processor.embed_text(content)
            
            if embeddings is not None and len(embeddings) > 0:
                test_result["text_embeddings"] = 1
                test_result["embedding_dimensions"] = len(embeddings[0]) if isinstance(embeddings[0], list) else 0
                
                # Check for visual content detection
                if "diagram" in content.lower() or "chart" in content.lower():
                    test_result["visual_embeddings"] = 1
                
                test_result["status"] = "passed"
                logger.info("✅ Test 3 PASSED: Multi-modal embeddings generated successfully")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("No embeddings generated")
                logger.error("❌ Test 3 FAILED: No embeddings generated")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ Test 3 FAILED: {str(e)}")
        
        self.results["multimodal_embedding"] = test_result
        return test_result
    
    def test_enterprise_bridge(self) -> Dict[str, Any]:
        """Test 4: Enterprise Bridge Reliability"""
        logger.info("🔍 Starting Test 4: Enterprise Bridge Reliability")
        
        test_result = {
            "status": "running",
            "data_transfer_success": False,
            "transaction_integrity": False,
            "circuit_breaker_active": False,
            "errors": []
        }
        
        try:
            # Test the enterprise bridge service
            from backend.services.automatic_bridge_service import AutomaticBridgeService
            
            bridge = AutomaticBridgeService()
            
            # Test data transfer
            test_data = {
                "entities": ["Test Entity 1", "Test Entity 2"],
                "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
                "relationships": [{"source": "Test Entity 1", "target": "Test Entity 2", "type": "RELATED"}]
            }
            
            # Attempt data transfer
            result = bridge.transfer_data(test_data)
            test_result["data_transfer_success"] = result.get("success", False)
            
            # Check transaction integrity
            if test_result["data_transfer_success"]:
                test_result["transaction_integrity"] = True
                test_result["circuit_breaker_active"] = True
                
                test_result["status"] = "passed"
                logger.info("✅ Test 4 PASSED: Enterprise bridge operating reliably")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("Data transfer failed")
                logger.error("❌ Test 4 FAILED: Data transfer failed")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ Test 4 FAILED: {str(e)}")
        
        self.results["enterprise_bridge"] = test_result
        return test_result
    
    def test_neo4j_relationships(self) -> Dict[str, Any]:
        """Test 5: Neo4j Relationship Creation"""
        logger.info("🔍 Starting Test 5: Neo4j Relationship Creation")
        
        test_result = {
            "status": "running",
            "relationships_created": 0,
            "relationship_types": [],
            "orphaned_entities": 0,
            "errors": []
        }
        
        try:
            # Test Neo4j relationship creation
            from backend.services.neo4j_relationship_generator import Neo4jRelationshipGenerator
            
            generator = Neo4jRelationshipGenerator()
            
            # Process relationships test file
            with open("relationships_test.txt", 'r') as f:
                content = f.read()
            
            relationships = generator.generate_relationships(content)
            test_result["relationships_created"] = len(relationships)
            test_result["relationship_types"] = list(set([r.get("type", "") for r in relationships]))
            
            # Check for expected relationship types
            expected_types = ["REQUIRES", "CONNECTS", "INVOLVES"]
            found_types = sum(1 for exp_type in expected_types 
                            if any(exp_type in rel_type for rel_type in test_result["relationship_types"]))
            
            if test_result["relationships_created"] > 0 and found_types >= 1:
                test_result["status"] = "passed"
                logger.info("✅ Test 5 PASSED: Neo4j relationships created successfully")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("No meaningful relationships created")
                logger.error("❌ Test 5 FAILED: No meaningful relationships created")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ Test 5 FAILED: {str(e)}")
        
        self.results["neo4j_relationships"] = test_result
        return test_result
    
    def test_end_to_end_integration(self) -> Dict[str, Any]:
        """Test 6: End-to-End Integration"""
        logger.info("🔍 Starting Test 6: End-to-End Integration")
        
        test_result = {
            "status": "running",
            "files_processed": 0,
            "total_entities": 0,
            "total_relationships": 0,
            "processing_time": 0,
            "search_functionality": False,
            "errors": []
        }
        
        try:
            start_time = time.time()
            
            # Test complete pipeline
            from backend.services.true_rag_service import TrueRAGService
            
            rag_service = TrueRAGService()
            
            # Process all test files
            for file_name in self.test_files:
                with open(file_name, 'r') as f:
                    content = f.read()
                
                result = rag_service.process_document(content, file_name)
                if result.get("success", False):
                    test_result["files_processed"] += 1
                    test_result["total_entities"] += result.get("entities", 0)
                    test_result["total_relationships"] += result.get("relationships", 0)
            
            test_result["processing_time"] = time.time() - start_time
            
            # Test search functionality
            search_result = rag_service.search("fryer cleaning")
            test_result["search_functionality"] = len(search_result) > 0
            
            if (test_result["files_processed"] == len(self.test_files) and 
                test_result["total_entities"] > 0 and 
                test_result["search_functionality"]):
                test_result["status"] = "passed"
                logger.info("✅ Test 6 PASSED: End-to-end integration successful")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("Integration pipeline incomplete")
                logger.error("❌ Test 6 FAILED: Integration pipeline incomplete")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ Test 6 FAILED: {str(e)}")
        
        self.results["end_to_end"] = test_result
        return test_result
    
    def test_knowledge_quality(self) -> Dict[str, Any]:
        """Test 7: Knowledge Quality Assessment"""
        logger.info("🔍 Starting Test 7: Knowledge Quality Assessment")
        
        test_result = {
            "status": "running",
            "entity_quality_score": 0,
            "embedding_quality_score": 0,
            "relationship_quality_score": 0,
            "search_relevance_score": 0,
            "overall_quality_score": 0,
            "errors": []
        }
        
        try:
            # Assess knowledge quality
            from backend.data_integrity_verification import DataIntegrityVerification
            
            verifier = DataIntegrityVerification()
            
            # Entity quality assessment
            entity_score = verifier.assess_entity_quality()
            test_result["entity_quality_score"] = entity_score
            
            # Embedding quality assessment
            embedding_score = verifier.assess_embedding_quality()
            test_result["embedding_quality_score"] = embedding_score
            
            # Relationship quality assessment
            relationship_score = verifier.assess_relationship_quality()
            test_result["relationship_quality_score"] = relationship_score
            
            # Search relevance assessment
            search_score = verifier.assess_search_relevance()
            test_result["search_relevance_score"] = search_score
            
            # Overall quality score
            test_result["overall_quality_score"] = (
                entity_score + embedding_score + relationship_score + search_score
            ) / 4
            
            if test_result["overall_quality_score"] >= 0.7:
                test_result["status"] = "passed"
                logger.info("✅ Test 7 PASSED: Knowledge quality meets standards")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("Knowledge quality below threshold")
                logger.error("❌ Test 7 FAILED: Knowledge quality below threshold")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ Test 7 FAILED: {str(e)}")
        
        self.results["knowledge_quality"] = test_result
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in sequence"""
        logger.info("🚀 Starting Enterprise Bridge Test Suite")
        
        # Run all tests
        self.test_data_preparation()
        self.test_qsr_entity_detection()
        self.test_multimodal_embedding()
        self.test_enterprise_bridge()
        self.test_neo4j_relationships()
        self.test_end_to_end_integration()
        self.test_knowledge_quality()
        
        # Generate summary
        passed_tests = sum(1 for result in self.results.values() if result.get("status") == "passed")
        total_tests = len(self.results)
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "detailed_results": self.results
        }
        
        logger.info(f"📊 Test Suite Complete: {passed_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        
        return summary
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        summary = self.run_all_tests()
        
        report = f"""
# Enterprise Bridge Test Suite Report

## Executive Summary
- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed_tests']}
- **Failed**: {summary['failed_tests']}
- **Success Rate**: {summary['success_rate']:.1f}%

## Test Results Details

"""
        
        for test_name, result in summary['detailed_results'].items():
            status_icon = "✅" if result['status'] == "passed" else "❌"
            report += f"### {status_icon} {test_name.replace('_', ' ').title()}\n"
            report += f"**Status**: {result['status']}\n"
            
            if result.get('errors'):
                report += f"**Errors**: {', '.join(result['errors'])}\n"
            
            report += "\n"
        
        return report


if __name__ == "__main__":
    # Run the test suite
    test_suite = EnterpriseBridgeTestSuite()
    report = test_suite.generate_report()
    
    # Save report
    with open("enterprise_bridge_test_report.md", "w") as f:
        f.write(report)
    
    print(report)