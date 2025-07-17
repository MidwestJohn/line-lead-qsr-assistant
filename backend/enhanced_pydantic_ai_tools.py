#!/usr/bin/env python3
"""
Enhanced PydanticAI Tools for Multi-Format System
=================================================

Integrates multi-format file capabilities with PydanticAI to provide enhanced
AI-powered assistance for restaurant operations and equipment management.

Features:
- Multi-format document search and retrieval
- File type-specific processing and analysis
- Enhanced equipment guidance with visual support
- Real-time system status integration
- Cross-format knowledge synthesis

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

# Import PydanticAI components
try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.tools import Tool
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False

# Import existing QSR agent
try:
    from agents.qsr_support_agent import support_agent, get_qsr_assistance, QSRTaskResponse
    QSR_AGENT_AVAILABLE = True
except ImportError:
    QSR_AGENT_AVAILABLE = False

# Import our enhanced services
from services.enhanced_qsr_ragie_service import (
    enhanced_qsr_ragie_service,
    search_multi_format_documents,
    get_processing_status
)
from services.enhanced_file_validation import enhanced_validation_service
from enhanced_health_monitoring import enhanced_health_monitor
from main import load_documents_db, simple_progress_store

logger = logging.getLogger(__name__)

class EnhancedQSRTools:
    """
    Enhanced QSR tools with multi-format capabilities
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available = PYDANTIC_AI_AVAILABLE and QSR_AGENT_AVAILABLE
        
        if self.available:
            self.logger.info("✅ Enhanced QSR tools initialized with PydanticAI integration")
        else:
            self.logger.warning("⚠️ Enhanced QSR tools limited - PydanticAI or QSR agent not available")
    
    async def search_multi_format_knowledge(
        self,
        query: str,
        file_types: Optional[List[str]] = None,
        qsr_categories: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search across multi-format documents with enhanced context
        
        Args:
            query: Search query
            file_types: Filter by file types (pdf, jpg, mp4, etc.)
            qsr_categories: Filter by QSR categories (manual, image, video, etc.)
            limit: Maximum results to return
            
        Returns:
            Enhanced search results with multi-format context
        """
        try:
            # Perform multi-format search
            search_results = await search_multi_format_documents(
                query=query,
                file_types=file_types,
                qsr_categories=qsr_categories,
                limit=limit
            )
            
            if not search_results.get("success", False):
                return {
                    "success": False,
                    "error": search_results.get("error", "Search failed"),
                    "results": []
                }
            
            # Enhance results with context
            enhanced_results = []
            for result in search_results.get("results", []):
                enhanced_result = {
                    **result,
                    "context_type": "multi_format_search",
                    "search_query": query,
                    "relevance_score": result.get("score", 0.0),
                    "file_category": self._get_file_category(result.get("file_type", "unknown")),
                    "processing_status": self._get_processing_status(result.get("document_id")),
                    "usage_suggestions": self._get_usage_suggestions(result.get("file_type", "unknown"))
                }
                enhanced_results.append(enhanced_result)
            
            return {
                "success": True,
                "query": query,
                "results": enhanced_results,
                "total_results": len(enhanced_results),
                "file_types_found": search_results.get("file_types_found", []),
                "qsr_categories_found": search_results.get("qsr_categories_found", []),
                "search_context": {
                    "multi_format_enabled": True,
                    "total_searchable_formats": len(enhanced_validation_service.get_supported_extensions()),
                    "ragie_service_available": enhanced_qsr_ragie_service.is_available()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Multi-format search failed: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    def _get_file_category(self, file_type: str) -> str:
        """Get file category for enhanced context"""
        category_map = {
            'pdf': 'manual',
            'docx': 'manual',
            'xlsx': 'spreadsheet',
            'pptx': 'presentation',
            'jpg': 'image',
            'jpeg': 'image',
            'png': 'image',
            'gif': 'image',
            'webp': 'image',
            'mp4': 'video',
            'mov': 'video',
            'avi': 'video',
            'mp3': 'audio',
            'wav': 'audio',
            'm4a': 'audio',
            'txt': 'text',
            'md': 'text',
            'csv': 'data'
        }
        return category_map.get(file_type, 'unknown')
    
    def _get_processing_status(self, document_id: str) -> str:
        """Get processing status for document"""
        if not document_id:
            return "unknown"
        
        # Check Ragie processing status
        ragie_status = get_processing_status(document_id)
        if ragie_status:
            return ragie_status.status
        
        # Check local processing
        for process_data in simple_progress_store.values():
            if process_data.get("file_id") == document_id:
                return process_data.get("status", "unknown")
        
        return "completed"  # Assume completed if not found
    
    def _get_usage_suggestions(self, file_type: str) -> List[str]:
        """Get usage suggestions based on file type"""
        suggestions_map = {
            'pdf': [
                "Read for detailed equipment procedures",
                "Reference for troubleshooting steps",
                "Check for safety warnings and protocols"
            ],
            'jpg': [
                "Visual reference for equipment identification",
                "Compare with actual equipment condition",
                "Use for training and demonstration"
            ],
            'png': [
                "High-quality visual reference",
                "Suitable for detailed equipment diagrams",
                "Use for documentation and reports"
            ],
            'mp4': [
                "Watch for video demonstrations",
                "Review for step-by-step procedures",
                "Share for training purposes"
            ],
            'txt': [
                "Quick reference for key information",
                "Easy to search and extract data",
                "Suitable for notes and summaries"
            ],
            'docx': [
                "Comprehensive documentation",
                "Editable format for updates",
                "Good for detailed procedures"
            ],
            'xlsx': [
                "Data analysis and tracking",
                "Schedule and inventory management",
                "Performance metrics and reporting"
            ]
        }
        return suggestions_map.get(file_type, ["General reference document"])
    
    async def get_system_status_context(self) -> Dict[str, Any]:
        """
        Get comprehensive system status for AI context
        
        Returns:
            System status information for enhanced AI responses
        """
        try:
            # Get health status
            health_status = enhanced_health_monitor.get_current_health_status()
            
            # Get document statistics
            docs_db = load_documents_db()
            
            # Get file type statistics
            file_type_stats = {}
            for doc_info in docs_db.values():
                file_type = doc_info.get('file_type', 'unknown')
                file_type_stats[file_type] = file_type_stats.get(file_type, 0) + 1
            
            # Get processing statistics
            processing_stats = {
                "active_uploads": len(simple_progress_store),
                "total_documents": len(docs_db),
                "supported_formats": len(enhanced_validation_service.get_supported_extensions()),
                "ragie_service_available": enhanced_qsr_ragie_service.is_available()
            }
            
            # Get capabilities information
            capabilities = {
                "multi_format_support": True,
                "real_time_progress": True,
                "websocket_updates": True,
                "health_monitoring": enhanced_health_monitor.monitoring_active,
                "background_processing": True,
                "search_integration": enhanced_qsr_ragie_service.is_available()
            }
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "health_status": health_status,
                "document_statistics": {
                    "total_documents": len(docs_db),
                    "file_type_distribution": file_type_stats
                },
                "processing_statistics": processing_stats,
                "system_capabilities": capabilities,
                "context_type": "system_status"
            }
            
        except Exception as e:
            self.logger.error(f"System status context failed: {e}")
            return {
                "success": False,
                "error": f"System status unavailable: {str(e)}",
                "context_type": "system_status"
            }
    
    async def get_equipment_guidance_enhanced(
        self,
        equipment_name: str,
        issue_description: str,
        include_visuals: bool = True
    ) -> Dict[str, Any]:
        """
        Get enhanced equipment guidance with multi-format support
        
        Args:
            equipment_name: Name of the equipment
            issue_description: Description of the issue
            include_visuals: Whether to include visual references
            
        Returns:
            Enhanced guidance with multi-format references
        """
        try:
            # Search for equipment-related documents
            search_query = f"{equipment_name} {issue_description}"
            
            # Search across all formats
            search_results = await self.search_multi_format_knowledge(
                query=search_query,
                file_types=None,  # Include all types
                qsr_categories=None,  # Include all categories
                limit=20
            )
            
            if not search_results.get("success", False):
                return {
                    "success": False,
                    "error": "Could not search for equipment guidance",
                    "guidance": []
                }
            
            # Categorize results by type
            manuals = []
            images = []
            videos = []
            other_docs = []
            
            for result in search_results.get("results", []):
                file_type = result.get("file_type", "unknown")
                if file_type in ['pdf', 'docx', 'txt', 'md']:
                    manuals.append(result)
                elif file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    images.append(result)
                elif file_type in ['mp4', 'mov', 'avi']:
                    videos.append(result)
                else:
                    other_docs.append(result)
            
            # Generate enhanced guidance
            guidance = {
                "equipment": equipment_name,
                "issue": issue_description,
                "search_query": search_query,
                "total_references": len(search_results.get("results", [])),
                "reference_types": {
                    "manuals": len(manuals),
                    "images": len(images),
                    "videos": len(videos),
                    "other_documents": len(other_docs)
                },
                "recommendations": self._generate_equipment_recommendations(
                    equipment_name, 
                    issue_description, 
                    manuals, 
                    images, 
                    videos
                ),
                "visual_references": images[:5] if include_visuals else [],
                "video_demonstrations": videos[:3],
                "detailed_manuals": manuals[:3],
                "suggested_actions": self._generate_suggested_actions(
                    equipment_name, 
                    issue_description,
                    search_results.get("results", [])
                )
            }
            
            return {
                "success": True,
                "guidance": guidance,
                "context_type": "equipment_guidance_enhanced"
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced equipment guidance failed: {e}")
            return {
                "success": False,
                "error": f"Equipment guidance failed: {str(e)}",
                "guidance": {}
            }
    
    def _generate_equipment_recommendations(
        self,
        equipment_name: str,
        issue_description: str,
        manuals: List[Dict],
        images: List[Dict],
        videos: List[Dict]
    ) -> List[str]:
        """Generate equipment recommendations based on available resources"""
        recommendations = []
        
        # Basic recommendations
        recommendations.append(f"Check the {equipment_name} manual for troubleshooting steps")
        recommendations.append("Ensure all safety protocols are followed")
        
        # Resource-specific recommendations
        if manuals:
            recommendations.append(f"Reference {len(manuals)} available manual(s) for detailed procedures")
        
        if images:
            recommendations.append(f"Use {len(images)} visual reference(s) to identify components")
        
        if videos:
            recommendations.append(f"Watch {len(videos)} demonstration video(s) for step-by-step guidance")
        
        # Issue-specific recommendations
        if "temperature" in issue_description.lower():
            recommendations.append("Check temperature sensors and calibration")
        
        if "noise" in issue_description.lower():
            recommendations.append("Inspect for loose components or worn parts")
        
        if "not working" in issue_description.lower() or "broken" in issue_description.lower():
            recommendations.append("Verify power supply and connections")
            recommendations.append("Check for error codes or warning lights")
        
        return recommendations
    
    def _generate_suggested_actions(
        self,
        equipment_name: str,
        issue_description: str,
        all_results: List[Dict]
    ) -> List[Dict[str, str]]:
        """Generate suggested actions based on search results"""
        actions = []
        
        # Safety first
        actions.append({
            "priority": "high",
            "action": "Ensure equipment is safely shut down",
            "description": "Follow proper shutdown procedures before inspection"
        })
        
        # Document review
        if all_results:
            actions.append({
                "priority": "medium",
                "action": "Review available documentation",
                "description": f"Check {len(all_results)} relevant document(s) for guidance"
            })
        
        # Visual inspection
        actions.append({
            "priority": "medium",
            "action": "Perform visual inspection",
            "description": "Look for obvious signs of damage or wear"
        })
        
        # Issue-specific actions
        if "clean" in issue_description.lower():
            actions.append({
                "priority": "medium",
                "action": "Clean equipment thoroughly",
                "description": "Follow manufacturer's cleaning procedures"
            })
        
        if "calibrat" in issue_description.lower():
            actions.append({
                "priority": "high",
                "action": "Check calibration",
                "description": "Verify equipment calibration and adjust if needed"
            })
        
        # Follow-up
        actions.append({
            "priority": "low",
            "action": "Document the issue",
            "description": "Record the problem and resolution for future reference"
        })
        
        return actions
    
    async def get_file_processing_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get detailed file processing status
        
        Args:
            document_id: Document ID to check
            
        Returns:
            Detailed processing status information
        """
        try:
            # Check Ragie processing status
            ragie_status = get_processing_status(document_id)
            
            # Check local processing
            local_status = None
            for process_data in simple_progress_store.values():
                if process_data.get("file_id") == document_id:
                    local_status = process_data
                    break
            
            # Get document info
            docs_db = load_documents_db()
            doc_info = docs_db.get(document_id)
            
            return {
                "success": True,
                "document_id": document_id,
                "document_info": doc_info,
                "ragie_status": {
                    "status": ragie_status.status if ragie_status else "unknown",
                    "progress_percent": ragie_status.progress_percent if ragie_status else 0,
                    "current_operation": ragie_status.current_operation if ragie_status else "unknown"
                } if ragie_status else None,
                "local_status": local_status,
                "overall_status": self._determine_overall_status(ragie_status, local_status),
                "context_type": "file_processing_status"
            }
            
        except Exception as e:
            self.logger.error(f"File processing status check failed: {e}")
            return {
                "success": False,
                "error": f"Status check failed: {str(e)}",
                "document_id": document_id
            }
    
    def _determine_overall_status(self, ragie_status, local_status) -> str:
        """Determine overall processing status"""
        if ragie_status:
            return ragie_status.status
        elif local_status:
            return local_status.get("status", "unknown")
        else:
            return "unknown"

# Global enhanced tools instance
enhanced_qsr_tools = EnhancedQSRTools()

# PydanticAI tool definitions (if available)
if PYDANTIC_AI_AVAILABLE and QSR_AGENT_AVAILABLE:
    
    @support_agent.tool
    async def search_multi_format_knowledge_tool(
        ctx: RunContext,
        query: str,
        file_types: Optional[List[str]] = None,
        qsr_categories: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search across multi-format documents for QSR assistance
        
        Args:
            query: Search query for equipment, procedures, or information
            file_types: Filter by file types (pdf, jpg, mp4, txt, etc.)
            qsr_categories: Filter by QSR categories (manual, image, video, etc.)
            limit: Maximum number of results to return
        """
        return await enhanced_qsr_tools.search_multi_format_knowledge(
            query=query,
            file_types=file_types,
            qsr_categories=qsr_categories,
            limit=limit
        )
    
    @support_agent.tool
    async def get_system_status_tool(ctx: RunContext) -> Dict[str, Any]:
        """
        Get comprehensive system status for enhanced AI responses
        
        Returns current system health, processing statistics, and capabilities
        """
        return await enhanced_qsr_tools.get_system_status_context()
    
    @support_agent.tool
    async def get_equipment_guidance_tool(
        ctx: RunContext,
        equipment_name: str,
        issue_description: str,
        include_visuals: bool = True
    ) -> Dict[str, Any]:
        """
        Get enhanced equipment guidance with multi-format support
        
        Args:
            equipment_name: Name of the equipment needing assistance
            issue_description: Description of the issue or question
            include_visuals: Whether to include visual references
        """
        return await enhanced_qsr_tools.get_equipment_guidance_enhanced(
            equipment_name=equipment_name,
            issue_description=issue_description,
            include_visuals=include_visuals
        )
    
    @support_agent.tool
    async def get_file_processing_status_tool(
        ctx: RunContext,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed file processing status
        
        Args:
            document_id: Document ID to check processing status
        """
        return await enhanced_qsr_tools.get_file_processing_status(document_id)

# Helper functions for integration
async def search_multi_format_knowledge(
    query: str,
    file_types: Optional[List[str]] = None,
    qsr_categories: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Search multi-format knowledge (convenience function)"""
    return await enhanced_qsr_tools.search_multi_format_knowledge(
        query, file_types, qsr_categories, limit
    )

async def get_system_status_context() -> Dict[str, Any]:
    """Get system status context (convenience function)"""
    return await enhanced_qsr_tools.get_system_status_context()

async def get_equipment_guidance_enhanced(
    equipment_name: str,
    issue_description: str,
    include_visuals: bool = True
) -> Dict[str, Any]:
    """Get enhanced equipment guidance (convenience function)"""
    return await enhanced_qsr_tools.get_equipment_guidance_enhanced(
        equipment_name, issue_description, include_visuals
    )

def is_enhanced_tools_available() -> bool:
    """Check if enhanced tools are available"""
    return enhanced_qsr_tools.available