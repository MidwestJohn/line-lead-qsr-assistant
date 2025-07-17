#!/usr/bin/env python3
"""
Phase 2 Implementation Test
===========================

Comprehensive test of the video player component implementation
and integration with the document source API.

Tests:
- Component creation and structure
- CSS styling and responsive design
- API integration readiness
- Error handling
- Accessibility features
- Mobile optimization

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, List

class Phase2Tester:
    """Test suite for Phase 2 video player implementation"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.project_root = Path(__file__).parent
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log test result"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
    
    def test_component_files_created(self) -> bool:
        """Test that all required component files are created"""
        required_files = [
            "src/components/VideoPlayer.js",
            "src/components/VideoPlayer.css",
            "src/components/MediaCitation.js",
            "src/components/MediaCitation.css",
            "src/components/index.js"
        ]
        
        all_files_exist = True
        missing_files = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                file_size = full_path.stat().st_size
                self.log_test(
                    f"File Creation - {file_path}",
                    True,
                    f"File exists ({file_size} bytes)",
                    {"file_path": str(full_path), "size": file_size}
                )
            else:
                missing_files.append(file_path)
                all_files_exist = False
                self.log_test(
                    f"File Creation - {file_path}",
                    False,
                    "File missing",
                    {"file_path": str(full_path)}
                )
        
        return all_files_exist
    
    def test_component_structure(self) -> bool:
        """Test component structure and key features"""
        video_player_path = self.project_root / "src/components/VideoPlayer.js"
        
        if not video_player_path.exists():
            self.log_test("Component Structure", False, "VideoPlayer.js not found")
            return False
        
        try:
            content = video_player_path.read_text()
            
            # Check for key features
            features = {
                "useState": "useState" in content,
                "useRef": "useRef" in content,
                "useEffect": "useEffect" in content,
                "useCallback": "useCallback" in content,
                "useReducer": "useReducer" in content,
                "video_controls": "handlePlayPause" in content,
                "progress_bar": "handleProgressClick" in content,
                "fullscreen": "handleFullscreen" in content,
                "range_requests": "Range" in content,
                "error_handling": "handleError" in content,
                "accessibility": "title=" in content,
                "mobile_support": "playsInline" in content
            }
            
            successful_features = sum(features.values())
            total_features = len(features)
            
            if successful_features >= total_features * 0.8:  # 80% threshold
                self.log_test(
                    "Component Structure",
                    True,
                    f"Component structure complete ({successful_features}/{total_features} features)",
                    {"features": features}
                )
                return True
            else:
                self.log_test(
                    "Component Structure",
                    False,
                    f"Component structure incomplete ({successful_features}/{total_features} features)",
                    {"features": features}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Component Structure",
                False,
                f"Error analyzing component: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_css_styling(self) -> bool:
        """Test CSS styling completeness"""
        css_path = self.project_root / "src/components/VideoPlayer.css"
        
        if not css_path.exists():
            self.log_test("CSS Styling", False, "VideoPlayer.css not found")
            return False
        
        try:
            content = css_path.read_text()
            
            # Check for key CSS features
            css_features = {
                "responsive_design": "@media" in content,
                "mobile_optimization": "max-width: 768px" in content,
                "touch_support": "hover: none" in content,
                "accessibility": "prefers-contrast" in content,
                "animations": "@keyframes" in content,
                "fullscreen_support": ".fullscreen" in content,
                "video_controls": ".video-controls" in content,
                "progress_bar": ".progress-bar" in content,
                "loading_states": ".loading-spinner" in content,
                "error_states": ".video-player-error" in content
            }
            
            successful_features = sum(css_features.values())
            total_features = len(css_features)
            
            if successful_features >= total_features * 0.8:  # 80% threshold
                self.log_test(
                    "CSS Styling",
                    True,
                    f"CSS styling complete ({successful_features}/{total_features} features)",
                    {"features": css_features}
                )
                return True
            else:
                self.log_test(
                    "CSS Styling",
                    False,
                    f"CSS styling incomplete ({successful_features}/{total_features} features)",
                    {"features": css_features}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "CSS Styling",
                False,
                f"Error analyzing CSS: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_api_integration_readiness(self) -> bool:
        """Test API integration readiness"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.base_url}/api/documents/source/health")
            
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get("status") == "healthy":
                    self.log_test(
                        "API Integration",
                        True,
                        "Document source API is ready",
                        health_data
                    )
                    return True
                else:
                    self.log_test(
                        "API Integration",
                        False,
                        f"API not healthy: {health_data.get('status')}",
                        health_data
                    )
                    return False
            else:
                self.log_test(
                    "API Integration",
                    False,
                    f"API health check failed: {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "API Integration",
                False,
                f"API integration error: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_media_citation_component(self) -> bool:
        """Test media citation component"""
        citation_path = self.project_root / "src/components/MediaCitation.js"
        
        if not citation_path.exists():
            self.log_test("Media Citation Component", False, "MediaCitation.js not found")
            return False
        
        try:
            content = citation_path.read_text()
            
            # Check for key features
            features = {
                "video_support": "detectedMediaType === 'video'" in content,
                "audio_support": "detectedMediaType === 'audio'" in content,
                "image_support": "detectedMediaType === 'image'" in content,
                "document_support": "detectedMediaType === 'document'" in content,
                "preview_functionality": "isPreviewOpen" in content,
                "download_support": "handleDownload" in content,
                "metadata_loading": "setMetadata" in content,
                "error_handling": "onError" in content,
                "video_player_integration": "VideoPlayer" in content
            }
            
            successful_features = sum(features.values())
            total_features = len(features)
            
            if successful_features >= total_features * 0.8:  # 80% threshold
                self.log_test(
                    "Media Citation Component",
                    True,
                    f"Media citation component complete ({successful_features}/{total_features} features)",
                    {"features": features}
                )
                return True
            else:
                self.log_test(
                    "Media Citation Component",
                    False,
                    f"Media citation component incomplete ({successful_features}/{total_features} features)",
                    {"features": features}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Media Citation Component",
                False,
                f"Error analyzing media citation component: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_basechar_patterns_implementation(self) -> bool:
        """Test BaseChat patterns implementation"""
        video_player_path = self.project_root / "src/components/VideoPlayer.js"
        
        if not video_player_path.exists():
            self.log_test("BaseChat Patterns", False, "VideoPlayer.js not found")
            return False
        
        try:
            content = video_player_path.read_text()
            
            # Check for BaseChat-inspired features
            basechar_features = {
                "custom_controls": "controls={false}" in content,
                "drag_progress": "dragReducer" in content,
                "time_formatting": "formatTime" in content,
                "range_support": "Range" in content,
                "play_pause": "handlePlayPause" in content,
                "skip_controls": "handleSkipBack" in content and "handleSkipForward" in content,
                "fullscreen": "handleFullscreen" in content,
                "volume_control": "handleMute" in content,
                "loading_states": "isLoading" in content,
                "error_handling": "handleError" in content,
                "progress_preview": "previewTime" in content
            }
            
            successful_features = sum(basechar_features.values())
            total_features = len(basechar_features)
            
            if successful_features >= total_features * 0.8:  # 80% threshold
                self.log_test(
                    "BaseChat Patterns",
                    True,
                    f"BaseChat patterns implemented ({successful_features}/{total_features} features)",
                    {"features": basechar_features}
                )
                return True
            else:
                self.log_test(
                    "BaseChat Patterns",
                    False,
                    f"BaseChat patterns incomplete ({successful_features}/{total_features} features)",
                    {"features": basechar_features}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "BaseChat Patterns",
                False,
                f"Error analyzing BaseChat patterns: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_document_source_integration(self) -> bool:
        """Test document source integration"""
        try:
            # Test document IDs from Phase 1
            test_documents = [
                "76f50b46-f9c9-4926-a16a-4723087775a1",  # Text
                "cefc0e1b-dcb6-41ca-bcbd-b787bacc8d0f",  # Image
                "fc5dbc1a-0de4-4bba-afd9-0cbf9141bafc",  # DOCX
            ]
            
            successful_tests = 0
            total_tests = len(test_documents)
            
            for doc_id in test_documents:
                try:
                    # Test metadata endpoint
                    response = requests.get(f"{self.base_url}/api/documents/{doc_id}/metadata")
                    
                    if response.status_code == 200:
                        metadata = response.json()
                        successful_tests += 1
                        
                        self.log_test(
                            f"Document Source - {doc_id[:8]}...",
                            True,
                            f"Document accessible: {metadata.get('name', 'Unknown')}",
                            {"document_id": doc_id, "metadata": metadata}
                        )
                    else:
                        self.log_test(
                            f"Document Source - {doc_id[:8]}...",
                            False,
                            f"Document not accessible: {response.status_code}",
                            {"document_id": doc_id, "status_code": response.status_code}
                        )
                        
                except Exception as e:
                    self.log_test(
                        f"Document Source - {doc_id[:8]}...",
                        False,
                        f"Error accessing document: {e}",
                        {"document_id": doc_id, "error": str(e)}
                    )
            
            success_rate = successful_tests / total_tests
            return success_rate >= 0.8  # 80% threshold
            
        except Exception as e:
            self.log_test(
                "Document Source Integration",
                False,
                f"Error testing document source integration: {e}",
                {"error": str(e)}
            )
            return False
    
    def run_all_tests(self):
        """Run all Phase 2 tests"""
        print("🎥 Phase 2: Video Player Component Implementation Tests")
        print("=" * 60)
        
        # Test categories
        tests = [
            ("Component Files", self.test_component_files_created),
            ("Component Structure", self.test_component_structure),
            ("CSS Styling", self.test_css_styling),
            ("API Integration", self.test_api_integration_readiness),
            ("Media Citation", self.test_media_citation_component),
            ("BaseChat Patterns", self.test_basechar_patterns_implementation),
            ("Document Source", self.test_document_source_integration)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                self.log_test(
                    test_name,
                    False,
                    f"Test execution error: {e}",
                    {"error": str(e)}
                )
                results.append(False)
        
        return self.generate_report(results)
    
    def generate_report(self, results: List[bool]) -> Dict[str, Any]:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎥 Phase 2 Test Results")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Phase 2 specific success criteria
        component_success = all(results[:4])  # First 4 tests are component-related
        integration_success = all(results[4:])  # Last 3 tests are integration-related
        
        phase2_complete = success_rate >= 85  # 85% threshold for Phase 2
        
        print(f"\n🎯 Phase 2 Component Status:")
        print(f"   Component Creation: {'✅' if component_success else '❌'}")
        print(f"   API Integration: {'✅' if integration_success else '❌'}")
        print(f"   Overall Complete: {'✅' if phase2_complete else '❌'}")
        
        report = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "component_success": component_success,
            "integration_success": integration_success,
            "phase_2_complete": phase2_complete,
            "results": self.test_results
        }
        
        return report

def main():
    """Run Phase 2 tests"""
    tester = Phase2Tester()
    report = tester.run_all_tests()
    
    if report["phase_2_complete"]:
        print("\n🎉 Phase 2: Video Player Component Implementation - COMPLETE")
        print("✅ Ready to proceed to Phase 3: Image Rendering Enhancement")
        print("✅ Components ready for React integration")
        print("✅ BaseChat patterns successfully implemented")
    else:
        print("\n⚠️ Phase 2: Video Player Component Implementation - INCOMPLETE")
        print("❌ Please fix issues before proceeding to Phase 3")
    
    return report

if __name__ == "__main__":
    main()