#!/usr/bin/env python3
"""
Ragie Response Parser with Multi-Modal Support
==============================================

Parses Ragie responses and converts them to Line Lead's expected format.
Handles multi-modal content including videos, images, and structured text.
Maintains compatibility with existing frontend while adding rich media support.

Key Features:
- Multi-modal content detection and formatting
- Step-by-step procedure extraction
- Visual citation generation
- Quality score filtering
- QSR-specific content optimization

Author: Generated with Memex (https://memex.tech)
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Content type classification for multi-modal handling"""
    TEXT = "text"
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    PDF = "pdf"
    UNKNOWN = "unknown"

@dataclass
class ParsedStep:
    """Parsed step from procedure text"""
    step_number: int
    instruction: str
    estimated_time: Optional[str] = None
    equipment_needed: Optional[List[str]] = None
    safety_warning: Optional[str] = None
    media_reference: Optional[str] = None

@dataclass
class MediaContent:
    """Multi-modal media content"""
    media_url: str
    content_type: ContentType
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None

class RagieResponseParser:
    """Parser for converting Ragie responses to Line Lead format"""
    
    def __init__(self):
        """Initialize parser with QSR-specific patterns"""
        self.step_patterns = [
            r'(?:step\s*)?(\d+)[\.:]\s*(.+?)(?=(?:\n|$|\d+\.|step\s*\d+))',
            r'(\d+)\.\s*(.+?)(?=(?:\n|$|\d+\.))',
            r'first[,:]?\s*(.+?)(?=(?:\n|second|then|next))',
            r'then[,:]?\s*(.+?)(?=(?:\n|next|finally))',
            r'next[,:]?\s*(.+?)(?=(?:\n|then|finally))',
            r'finally[,:]?\s*(.+?)(?=(?:\n|$))'
        ]
        
        self.equipment_keywords = {
            'fryer', 'grill', 'oven', 'mixer', 'ice machine', 'pos system',
            'drive-thru', 'prep station', 'dishwasher', 'freezer', 'cooler'
        }
        
        self.safety_keywords = {
            'warning', 'caution', 'danger', 'hot', 'sharp', 'electrical',
            'safety', 'hazard', 'risk', 'avoid', 'never', 'always'
        }
        
        self.time_patterns = [
            r'(\d+)\s*(?:minutes?|mins?)',
            r'(\d+)\s*(?:seconds?|secs?)',
            r'(\d+)\s*(?:hours?|hrs?)',
            r'(\d+)-(\d+)\s*(?:minutes?|mins?)'
        ]
    
    def parse_ragie_response(self, ragie_chunks: List[Dict[str, Any]], 
                           original_query: str) -> Dict[str, Any]:
        """
        Parse Ragie response into Line Lead's ChatResponse format
        
        Args:
            ragie_chunks: List of chunks from Ragie search
            original_query: Original user query for context
            
        Returns:
            Parsed response in ChatResponse format
        """
        try:
            # Filter high-quality chunks
            quality_chunks = self._filter_quality_chunks(ragie_chunks)
            
            # Detect content types and extract media
            content_analysis = self._analyze_content_types(quality_chunks)
            
            # Generate main response text
            response_text = self._generate_response_text(quality_chunks, original_query)
            
            # Parse step-by-step procedures
            parsed_steps = self._parse_steps_from_chunks(quality_chunks)
            
            # Generate visual citations
            visual_citations = self._generate_visual_citations(quality_chunks)
            
            # Generate manual references
            manual_references = self._generate_manual_references(quality_chunks)
            
            # Extract document context
            document_context = self._extract_document_context(quality_chunks)
            
            # Generate recommendations
            recommendations = self._generate_qsr_recommendations(quality_chunks, original_query)
            
            return {
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "parsed_steps": parsed_steps,
                "visual_citations": visual_citations,
                "manual_references": manual_references,
                "document_context": document_context,
                "hierarchical_path": self._generate_hierarchical_path(quality_chunks),
                "contextual_recommendations": recommendations,
                "retrieval_method": "ragie_integration",
                "content_analysis": content_analysis,  # Additional metadata
                "quality_score": self._calculate_overall_quality(quality_chunks)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Ragie response: {e}")
            return self._generate_fallback_response(original_query, str(e))
    
    def _filter_quality_chunks(self, chunks: List[Dict[str, Any]], 
                              min_score: float = 0.5) -> List[Dict[str, Any]]:
        """Filter chunks by quality score and relevance"""
        quality_chunks = []
        
        for chunk in chunks:
            score = chunk.get("similarity", 0.0)
            
            # Filter by minimum score
            if score < min_score:
                continue
            
            # Filter out very short chunks (likely noise)
            text = chunk.get("text", "")
            if len(text.strip()) < 20:
                continue
            
            # Boost chunks with QSR-relevant content
            boost_score = self._calculate_qsr_relevance_boost(chunk)
            chunk["adjusted_score"] = score + boost_score
            
            quality_chunks.append(chunk)
        
        # Sort by adjusted score
        quality_chunks.sort(key=lambda x: x.get("adjusted_score", 0), reverse=True)
        
        # Return top 6 chunks for processing
        return quality_chunks[:6]
    
    def _analyze_content_types(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content types and extract multi-modal elements"""
        content_analysis = {
            "has_video": False,
            "has_images": False,
            "has_audio": False,
            "has_steps": False,
            "media_content": [],
            "content_distribution": {"text": 0, "video": 0, "image": 0, "audio": 0}
        }
        
        for chunk in chunks:
            # Check for media URLs in metadata
            metadata = chunk.get("metadata", {})
            media_url = metadata.get("media_url")
            
            if media_url:
                content_type = self._detect_media_type(media_url, metadata)
                
                media_content = MediaContent(
                    media_url=media_url,
                    content_type=content_type,
                    start_time=metadata.get("start_time"),
                    end_time=metadata.get("end_time"),
                    caption=chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", ""),
                    thumbnail_url=metadata.get("thumbnail_url")
                )
                
                content_analysis["media_content"].append(media_content)
                
                # Update flags
                if content_type == ContentType.VIDEO:
                    content_analysis["has_video"] = True
                    content_analysis["content_distribution"]["video"] += 1
                elif content_type == ContentType.IMAGE:
                    content_analysis["has_images"] = True
                    content_analysis["content_distribution"]["image"] += 1
                elif content_type == ContentType.AUDIO:
                    content_analysis["has_audio"] = True
                    content_analysis["content_distribution"]["audio"] += 1
            else:
                content_analysis["content_distribution"]["text"] += 1
            
            # Check for step-by-step content
            if self._contains_steps(chunk.get("text", "")):
                content_analysis["has_steps"] = True
        
        return content_analysis
    
    def _generate_response_text(self, chunks: List[Dict[str, Any]], 
                               original_query: str) -> str:
        """Generate main response text with multi-modal integration"""
        if not chunks:
            return "I couldn't find specific information for your query. Please try rephrasing or contact your supervisor."
        
        # Detect query intent
        is_how_to = any(word in original_query.lower() for word in ["how", "what", "steps", "process"])
        
        response_parts = []
        
        # Add introductory context
        primary_chunk = chunks[0]
        equipment_mentioned = primary_chunk.get("equipment_mentioned", [])
        
        if equipment_mentioned:
            response_parts.append(f"For {', '.join(equipment_mentioned)} operations:")
        
        # Process chunks and integrate media
        for i, chunk in enumerate(chunks[:3]):  # Use top 3 chunks
            text = chunk.get("text", "").strip()
            
            # Clean up text for better readability
            text = self._clean_chunk_text(text)
            
            # Add media references if available
            metadata = chunk.get("metadata", {})
            if metadata.get("media_url"):
                media_type = self._detect_media_type(metadata.get("media_url"), metadata)
                
                if media_type == ContentType.VIDEO:
                    if metadata.get("start_time") and metadata.get("end_time"):
                        response_parts.append(f"📹 **Video Guide** ({metadata['start_time']:.1f}s - {metadata['end_time']:.1f}s):")
                    else:
                        response_parts.append(f"📹 **Video Guide**:")
                elif media_type == ContentType.IMAGE:
                    response_parts.append(f"🖼️ **Visual Guide**:")
            
            response_parts.append(text)
            
            # Add safety warnings if detected
            if chunk.get("safety_warning"):
                safety_text = self._extract_safety_warnings(text)
                if safety_text:
                    response_parts.append(f"⚠️ **Safety Warning**: {safety_text}")
        
        # Add source attribution
        unique_sources = set(chunk.get("source", "Unknown") for chunk in chunks)
        if unique_sources:
            source_text = ", ".join(sorted(unique_sources))
            response_parts.append(f"\n📚 Sources: {source_text}")
        
        return "\n\n".join(response_parts)
    
    def _parse_steps_from_chunks(self, chunks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Parse step-by-step procedures from chunks"""
        all_steps = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            chunk_steps = self._extract_steps_from_text(text)
            all_steps.extend(chunk_steps)
        
        if not all_steps:
            return None
        
        # Deduplicate and sort steps
        unique_steps = {}
        for step in all_steps:
            key = f"{step.step_number}_{step.instruction[:50]}"
            if key not in unique_steps or len(step.instruction) > len(unique_steps[key].instruction):
                unique_steps[key] = step
        
        sorted_steps = sorted(unique_steps.values(), key=lambda x: x.step_number)
        
        # Calculate total estimated time
        total_time = self._calculate_total_time(sorted_steps)
        
        return {
            "has_steps": True,
            "procedure_title": self._generate_procedure_title(chunks),
            "total_steps": len(sorted_steps),
            "estimated_total_time": total_time,
            "steps": [
                {
                    "step": step.step_number,
                    "instruction": step.instruction,
                    "estimated_time": step.estimated_time,
                    "equipment_needed": step.equipment_needed,
                    "safety_warning": step.safety_warning,
                    "media_reference": step.media_reference
                }
                for step in sorted_steps
            ],
            "equipment_involved": self._extract_equipment_list(chunks),
            "difficulty_level": self._assess_difficulty_level(sorted_steps),
            "safety_level": self._assess_safety_level(sorted_steps)
        }
    
    def _generate_visual_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate visual citations from Ragie chunks"""
        citations = []
        
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            
            citation = {
                "citation_id": f"ragie_{chunk.get('chunk_id', i)}",
                "source": chunk.get("source", "Unknown Manual"),
                "page": metadata.get("page_number", "N/A"),
                "manual": chunk.get("source", "Equipment Manual"),
                "confidence": chunk.get("similarity", 0.0),
                "chunk_index": chunk.get("chunk_index", i),
                "media_url": metadata.get("media_url"),
                "content_type": str(self._detect_media_type(metadata.get("media_url", ""), metadata).value)
            }
            
            citations.append(citation)
        
        return citations[:5]  # Limit to top 5 citations
    
    def _generate_manual_references(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate manual references for source attribution"""
        references = {}
        
        for chunk in chunks:
            source = chunk.get("source", "Unknown Manual")
            metadata = chunk.get("metadata", {})
            
            if source not in references:
                references[source] = {
                    "manual_name": source,
                    "page_reference": f"Multiple pages",
                    "document_type": metadata.get("qsr_document_type", "manual"),
                    "equipment_type": metadata.get("equipment_type"),
                    "confidence": chunk.get("similarity", 0.0),
                    "chunk_count": 0
                }
            
            references[source]["chunk_count"] += 1
            references[source]["confidence"] = max(
                references[source]["confidence"], 
                chunk.get("similarity", 0.0)
            )
        
        # Sort by confidence and return as list
        sorted_refs = sorted(references.values(), key=lambda x: x["confidence"], reverse=True)
        return sorted_refs[:3]  # Top 3 manuals
    
    def _extract_document_context(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract document-level context information"""
        if not chunks:
            return {}
        
        # Aggregate metadata across chunks
        equipment_types = set()
        document_types = set()
        procedure_types = set()
        avg_confidence = 0.0
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            
            if metadata.get("equipment_type"):
                equipment_types.add(metadata["equipment_type"])
            if metadata.get("qsr_document_type"):
                document_types.add(metadata["qsr_document_type"])
            if metadata.get("procedure_type"):
                procedure_types.add(metadata["procedure_type"])
            
            avg_confidence += chunk.get("similarity", 0.0)
        
        avg_confidence /= len(chunks) if chunks else 1
        
        return {
            "summary": {
                "equipment_types": list(equipment_types),
                "document_types": list(document_types),
                "procedure_types": list(procedure_types),
                "total_sources": len(set(chunk.get("source") for chunk in chunks))
            },
            "confidence_score": round(avg_confidence, 2),
            "coverage": "comprehensive" if len(chunks) >= 4 else "partial",
            "media_available": any(chunk.get("metadata", {}).get("media_url") for chunk in chunks)
        }
    
    def _generate_hierarchical_path(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Generate hierarchical path for navigation context"""
        path = ["QSR Operations"]
        
        # Extract common themes from chunks
        equipment_types = set()
        procedure_types = set()
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            equipment_mentioned = chunk.get("equipment_mentioned", [])
            
            equipment_types.update(equipment_mentioned)
            if metadata.get("equipment_type"):
                equipment_types.add(metadata["equipment_type"])
            if metadata.get("procedure_type"):
                procedure_types.add(metadata["procedure_type"])
        
        # Build path based on most common elements
        if equipment_types:
            primary_equipment = max(equipment_types, key=lambda x: sum(
                1 for chunk in chunks 
                if x in chunk.get("equipment_mentioned", []) or x in chunk.get("metadata", {}).get("equipment_type", "")
            ))
            path.append(primary_equipment.replace("_", " ").title())
        
        if procedure_types:
            primary_procedure = list(procedure_types)[0]
            path.append(primary_procedure.replace("_", " ").title())
        
        return path
    
    # Helper methods continue...
    def _calculate_qsr_relevance_boost(self, chunk: Dict[str, Any]) -> float:
        """Calculate relevance boost for QSR-specific content"""
        boost = 0.0
        text = chunk.get("text", "").lower()
        metadata = chunk.get("metadata", {})
        
        # Equipment-specific boost
        if any(eq in text for eq in self.equipment_keywords):
            boost += 0.1
        
        # Safety content boost
        if any(safety in text for safety in self.safety_keywords):
            boost += 0.15
        
        # Step-by-step procedure boost
        if self._contains_steps(text):
            boost += 0.2
        
        # QSR metadata boost
        if metadata.get("industry") == "qsr":
            boost += 0.1
        
        return boost
    
    def _detect_media_type(self, media_url: str, metadata: Dict[str, Any]) -> ContentType:
        """Detect media type from URL and metadata"""
        if not media_url:
            return ContentType.TEXT
        
        # Check file extension
        url_lower = media_url.lower()
        
        if any(ext in url_lower for ext in ['.mp4', '.avi', '.mov', '.webm']):
            return ContentType.VIDEO
        elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
            return ContentType.IMAGE
        elif any(ext in url_lower for ext in ['.mp3', '.wav', '.ogg']):
            return ContentType.AUDIO
        elif '.pdf' in url_lower:
            return ContentType.PDF
        
        # Check metadata
        file_type = metadata.get("file_type", "").lower()
        if "video" in file_type:
            return ContentType.VIDEO
        elif "image" in file_type:
            return ContentType.IMAGE
        elif "audio" in file_type:
            return ContentType.AUDIO
        elif "pdf" in file_type:
            return ContentType.PDF
        
        return ContentType.UNKNOWN
    
    def _contains_steps(self, text: str) -> bool:
        """Check if text contains step-by-step instructions"""
        for pattern in self.step_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                return True
        return False
    
    def _extract_steps_from_text(self, text: str) -> List[ParsedStep]:
        """Extract steps from text using various patterns"""
        steps = []
        
        for pattern in self.step_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            
            for match in matches:
                if len(match.groups()) >= 2:
                    step_num = int(match.group(1)) if match.group(1).isdigit() else len(steps) + 1
                    instruction = match.group(2).strip()
                    
                    # Extract additional information
                    estimated_time = self._extract_time_estimate(instruction)
                    equipment_needed = self._extract_equipment_mentions(instruction)
                    safety_warning = self._extract_safety_warnings(instruction)
                    
                    step = ParsedStep(
                        step_number=step_num,
                        instruction=instruction,
                        estimated_time=estimated_time,
                        equipment_needed=equipment_needed,
                        safety_warning=safety_warning
                    )
                    
                    steps.append(step)
        
        return steps
    
    def _extract_time_estimate(self, text: str) -> Optional[str]:
        """Extract time estimates from instruction text"""
        for pattern in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _extract_equipment_mentions(self, text: str) -> List[str]:
        """Extract equipment mentions from text"""
        mentioned = []
        text_lower = text.lower()
        
        for equipment in self.equipment_keywords:
            if equipment in text_lower:
                mentioned.append(equipment)
        
        return mentioned
    
    def _extract_safety_warnings(self, text: str) -> Optional[str]:
        """Extract safety warnings from text"""
        text_lower = text.lower()
        
        for keyword in self.safety_keywords:
            if keyword in text_lower:
                # Extract sentence containing safety keyword
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        
        return None
    
    def _clean_chunk_text(self, text: str) -> str:
        """Clean chunk text for better readability"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = text.replace(' .', '.').replace(' ,', ',')
        
        # Ensure proper sentence endings
        if text and not text.endswith(('.', '!', '?', ':')):
            text += '.'
        
        return text.strip()
    
    def _calculate_total_time(self, steps: List[ParsedStep]) -> Optional[str]:
        """Calculate total estimated time for all steps"""
        total_minutes = 0
        
        for step in steps:
            if step.estimated_time:
                # Extract minutes from time estimate
                match = re.search(r'(\d+)\s*(?:minutes?|mins?)', step.estimated_time, re.IGNORECASE)
                if match:
                    total_minutes += int(match.group(1))
        
        if total_minutes > 0:
            if total_minutes >= 60:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            else:
                return f"{total_minutes} minutes"
        
        return None
    
    def _generate_procedure_title(self, chunks: List[Dict[str, Any]]) -> Optional[str]:
        """Generate a title for the procedure"""
        equipment_types = set()
        procedure_types = set()
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if metadata.get("equipment_type"):
                equipment_types.add(metadata["equipment_type"])
            if metadata.get("procedure_type"):
                procedure_types.add(metadata["procedure_type"])
        
        parts = []
        if procedure_types:
            parts.append(list(procedure_types)[0].replace("_", " ").title())
        if equipment_types:
            parts.append(list(equipment_types)[0].replace("_", " ").title())
        
        return " - ".join(parts) if parts else None
    
    def _extract_equipment_list(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract equipment list from chunks"""
        equipment = set()
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            equipment_mentioned = chunk.get("equipment_mentioned", [])
            
            equipment.update(equipment_mentioned)
            if metadata.get("equipment_type"):
                equipment.add(metadata["equipment_type"])
        
        return sorted(list(equipment))
    
    def _assess_difficulty_level(self, steps: List[ParsedStep]) -> str:
        """Assess difficulty level based on steps"""
        if len(steps) <= 3:
            return "easy"
        elif len(steps) <= 7:
            return "medium"
        else:
            return "hard"
    
    def _assess_safety_level(self, steps: List[ParsedStep]) -> str:
        """Assess safety level based on steps"""
        safety_mentions = sum(1 for step in steps if step.safety_warning)
        
        if safety_mentions >= 2:
            return "critical"
        elif safety_mentions >= 1:
            return "high"
        else:
            return "medium"
    
    def _generate_qsr_recommendations(self, chunks: List[Dict[str, Any]], 
                                    original_query: str) -> List[str]:
        """Generate QSR-specific recommendations"""
        recommendations = []
        
        # Equipment-specific recommendations
        equipment_types = set()
        for chunk in chunks:
            equipment_mentioned = chunk.get("equipment_mentioned", [])
            equipment_types.update(equipment_mentioned)
        
        for equipment in equipment_types:
            if equipment == "fryer":
                recommendations.append("Always check oil temperature before use")
            elif equipment == "grill":
                recommendations.append("Clean grill grates regularly for food safety")
            elif equipment == "ice_machine":
                recommendations.append("Monitor ice quality and sanitation daily")
        
        # Safety recommendations
        has_safety_content = any(chunk.get("safety_warning") for chunk in chunks)
        if has_safety_content:
            recommendations.append("Review safety protocols before starting")
        
        # Procedure-specific recommendations
        if "cleaning" in original_query.lower():
            recommendations.append("Use only approved cleaning chemicals")
            recommendations.append("Follow sanitization guidelines")
        
        return recommendations[:3]  # Limit to top 3
    
    def _calculate_overall_quality(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score for the response"""
        if not chunks:
            return 0.0
        
        scores = [chunk.get("similarity", 0.0) for chunk in chunks]
        avg_score = sum(scores) / len(scores)
        
        # Boost for multi-modal content
        has_media = any(chunk.get("metadata", {}).get("media_url") for chunk in chunks)
        if has_media:
            avg_score += 0.1
        
        # Boost for step-by-step content
        has_steps = any(self._contains_steps(chunk.get("text", "")) for chunk in chunks)
        if has_steps:
            avg_score += 0.1
        
        return min(1.0, avg_score)
    
    def _generate_fallback_response(self, original_query: str, error_msg: str) -> Dict[str, Any]:
        """Generate fallback response when parsing fails"""
        return {
            "response": f"I encountered an issue processing your request about '{original_query}'. Please try rephrasing your question or contact your supervisor for assistance.",
            "timestamp": datetime.now().isoformat(),
            "parsed_steps": None,
            "visual_citations": None,
            "manual_references": None,
            "document_context": {"error": error_msg},
            "hierarchical_path": ["QSR Operations", "Error"],
            "contextual_recommendations": ["Try rephrasing your question", "Contact supervisor if issue persists"],
            "retrieval_method": "fallback",
            "quality_score": 0.0
        }

# Global instance
ragie_parser = RagieResponseParser()