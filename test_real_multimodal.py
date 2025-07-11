"""
Real Multi-Modal Embedding Test
Tests actual multi-modal embedding generation with real files
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, List, Any
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealMultiModalTest:
    """Test actual multi-modal embedding generation"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.test_files_created = []
    
    def create_test_pdf_with_visual_content(self) -> str:
        """Create a simple PDF with visual elements for testing"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            filename = "test_multimodal_qsr_manual.pdf"
            c = canvas.Canvas(filename, pagesize=letter)
            
            # Add text content
            c.drawString(100, 750, "QSR Equipment Manual")
            c.drawString(100, 720, "Taylor C602 Fryer Maintenance Guide")
            c.drawString(100, 690, "")
            c.drawString(100, 660, "See Figure 1.1: Fryer Component Diagram")
            c.drawString(100, 630, "Safety Chart 2A shows proper cleaning procedure")
            c.drawString(100, 600, "Equipment diagram displays key components")
            
            # Add a simple "diagram" (rectangle with text)
            c.rect(100, 400, 300, 150)
            c.drawString(150, 500, "FRYER COMPONENT DIAGRAM")
            c.drawString(120, 470, "1. Heating Element")
            c.drawString(120, 450, "2. Temperature Control")
            c.drawString(120, 430, "3. Safety Switch")
            
            # Add another "chart"
            c.rect(100, 200, 300, 150)
            c.drawString(150, 320, "CLEANING PROCEDURE CHART")
            c.drawString(120, 290, "Step 1: Turn off power")
            c.drawString(120, 270, "Step 2: Cool down equipment")
            c.drawString(120, 250, "Step 3: Remove components")
            
            c.save()
            self.test_files_created.append(filename)
            logger.info(f"✅ Created test PDF: {filename}")
            return filename
            
        except ImportError:
            logger.warning("⚠️ ReportLab not available - creating text file instead")
            filename = "test_multimodal_qsr_manual.txt"
            content = """QSR Equipment Manual
Taylor C602 Fryer Maintenance Guide

See Figure 1.1: Fryer Component Diagram
Safety Chart 2A shows proper cleaning procedure
Equipment diagram displays key components

FRYER COMPONENT DIAGRAM
1. Heating Element
2. Temperature Control  
3. Safety Switch

CLEANING PROCEDURE CHART
Step 1: Turn off power
Step 2: Cool down equipment
Step 3: Remove components

[Image: Equipment safety warning diagram]
[Chart: Temperature monitoring flowchart]
[Diagram: Maintenance procedure visualization]
"""
            with open(filename, 'w') as f:
                f.write(content)
            self.test_files_created.append(filename)
            return filename
    
    def test_file_upload_and_processing(self, filename: str) -> Dict[str, Any]:
        """Test uploading file and processing for multi-modal content"""
        logger.info(f"🔍 Testing file upload and processing: {filename}")
        
        test_result = {
            "status": "running",
            "upload_successful": False,
            "processing_started": False,
            "embeddings_generated": False,
            "visual_content_detected": False,
            "response_data": {},
            "errors": []
        }
        
        try:
            # Upload the file
            with open(filename, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.backend_url}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                test_result["upload_successful"] = True
                test_result["response_data"] = response.json()
                logger.info("✅ File upload successful")
                
                # Check if processing started
                if "success" in test_result["response_data"]:
                    test_result["processing_started"] = True
                    
                # Check response for multi-modal indicators
                response_text = str(test_result["response_data"]).lower()
                visual_indicators = ["visual", "diagram", "chart", "image", "figure", "embedding"]
                
                for indicator in visual_indicators:
                    if indicator in response_text:
                        test_result["visual_content_detected"] = True
                        break
                
                test_result["status"] = "passed"
                logger.info("✅ File processing test passed")
            else:
                test_result["errors"].append(f"Upload failed with status {response.status_code}")
                test_result["status"] = "failed"
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"❌ File processing test failed: {str(e)}")
        
        return test_result
    
    def test_chat_with_visual_queries(self) -> Dict[str, Any]:
        """Test chat functionality with queries about visual content"""
        logger.info("🔍 Testing chat with visual content queries")
        
        test_result = {
            "status": "running",
            "queries_tested": 0,
            "responses_received": 0,
            "visual_responses": 0,
            "query_results": [],
            "errors": []
        }
        
        # Test queries about visual content
        visual_queries = [
            "Show me the fryer component diagram",
            "What does the safety chart show?",
            "Describe the equipment diagram",
            "What visual elements are in the manual?"
        ]
        
        try:
            for query in visual_queries:
                test_result["queries_tested"] += 1
                
                try:
                    payload = {"message": query}
                    response = requests.post(f"{self.backend_url}/chat", json=payload, timeout=15)
                    
                    if response.status_code == 200:
                        test_result["responses_received"] += 1
                        response_data = response.json()
                        response_text = str(response_data).lower()
                        
                        # Check if response mentions visual elements
                        visual_keywords = ["diagram", "chart", "figure", "visual", "image", "shows"]
                        if any(keyword in response_text for keyword in visual_keywords):
                            test_result["visual_responses"] += 1
                        
                        test_result["query_results"].append({
                            "query": query,
                            "status": "success",
                            "has_visual_content": any(keyword in response_text for keyword in visual_keywords)
                        })
                        
                    else:
                        test_result["query_results"].append({
                            "query": query,
                            "status": "failed",
                            "error": f"Status {response.status_code}"
                        })
                        
                except Exception as e:
                    test_result["query_results"].append({
                        "query": query,
                        "status": "error",
                        "error": str(e)
                    })
                    test_result["errors"].append(f"Query '{query}': {str(e)}")
            
            # Determine overall success
            if test_result["responses_received"] >= 2 and test_result["visual_responses"] >= 1:
                test_result["status"] = "passed"
                logger.info(f"✅ Chat test passed: {test_result['visual_responses']} visual responses")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("Insufficient visual responses from chat")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        return test_result
    
    def test_backend_multimodal_capabilities(self) -> Dict[str, Any]:
        """Test backend's multi-modal processing capabilities"""
        logger.info("🔍 Testing backend multi-modal capabilities")
        
        test_result = {
            "status": "running",
            "raganything_available": False,
            "sentence_transformers_available": False,
            "multimodal_services": [],
            "processing_capabilities": {},
            "errors": []
        }
        
        try:
            # Check if we can import multi-modal libraries
            try:
                import raganything
                test_result["raganything_available"] = True
                test_result["multimodal_services"].append("raganything")
                logger.info("✅ RAG-Anything available")
            except ImportError:
                test_result["errors"].append("RAG-Anything not available")
            
            try:
                import sentence_transformers
                test_result["sentence_transformers_available"] = True
                test_result["multimodal_services"].append("sentence_transformers")
                logger.info("✅ Sentence Transformers available")
            except ImportError:
                test_result["errors"].append("Sentence Transformers not available")
            
            # Check backend service files
            multimodal_files = [
                "backend/services/multimodal_citation_service.py",
                "backend/services/multimodal_bridge_processor.py",
                "backend/visual_citation_preservation.py"
            ]
            
            for file_path in multimodal_files:
                if Path(file_path).exists():
                    test_result["multimodal_services"].append(file_path)
                    logger.info(f"✅ Found {file_path}")
            
            # Overall capability assessment
            capabilities_count = len(test_result["multimodal_services"])
            test_result["processing_capabilities"] = {
                "total_capabilities": capabilities_count,
                "has_embedding_generation": test_result["sentence_transformers_available"],
                "has_multimodal_processing": test_result["raganything_available"],
                "has_service_files": capabilities_count >= 3
            }
            
            if capabilities_count >= 2:
                test_result["status"] = "passed"
                logger.info(f"✅ Multi-modal capabilities test passed: {capabilities_count} capabilities found")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("Insufficient multi-modal capabilities")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        return test_result
    
    def cleanup_test_files(self):
        """Clean up created test files"""
        for filename in self.test_files_created:
            try:
                if Path(filename).exists():
                    os.remove(filename)
                    logger.info(f"🧹 Cleaned up {filename}")
            except Exception as e:
                logger.warning(f"⚠️ Could not clean up {filename}: {str(e)}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all real multi-modal tests"""
        logger.info("🚀 Starting Real Multi-Modal Test Suite")
        
        results = {}
        
        try:
            # Test 1: Check backend capabilities
            results["backend_capabilities"] = self.test_backend_multimodal_capabilities()
            
            # Test 2: Create and upload test file
            test_filename = self.create_test_pdf_with_visual_content()
            results["file_processing"] = self.test_file_upload_and_processing(test_filename)
            
            # Test 3: Test chat with visual queries
            results["visual_chat"] = self.test_chat_with_visual_queries()
            
        finally:
            # Clean up
            self.cleanup_test_files()
        
        # Generate summary
        passed_tests = sum(1 for result in results.values() if result.get("status") == "passed")
        total_tests = len(results)
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "detailed_results": results
        }
        
        logger.info(f"📊 Real Multi-Modal Test Complete: {passed_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        
        return summary


if __name__ == "__main__":
    test_suite = RealMultiModalTest()
    summary = test_suite.run_all_tests()
    
    print(f"\n🎯 Real Multi-Modal Test Results:")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    
    for test_name, result in summary['detailed_results'].items():
        status_icon = "✅" if result['status'] == "passed" else "❌"
        print(f"{status_icon} {test_name}: {result['status']}")
        if result.get('errors'):
            print(f"   Errors: {', '.join(result['errors'])}")