#!/usr/bin/env python3
"""
StepCard Component Formatter
============================

Formatting layer specifically for StepCard component consumption.
Converts CleanedQSRResponse to StepCard-compatible format with
proper IDs, metadata, and mobile-optimized text formatting.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class StepCardFormatter:
    """
    Formats cleaned QSR responses for StepCard component consumption
    """
    
    def __init__(self):
        """Initialize with StepCard-specific formatting rules"""
        
        # Safety highlighting patterns
        self.safety_patterns = [
            r'\b(warning|caution|danger|hazard|safety|hot|electrical|chemical)\b',
            r'\b(do not|never|avoid|prevent|stop)\b',
            r'\b(emergency|urgent|critical|important)\b'
        ]
        
        # Time-sensitive instruction patterns
        self.time_sensitive_patterns = [
            r'\b(immediately|quickly|slowly|wait|pause|delay)\b',
            r'\b(before|after|during|while|until)\b',
            r'\b(\d+\s*(?:minutes?|seconds?|hours?))\b'
        ]
        
        # Completion requirement patterns
        self.completion_patterns = [
            r'\b(complete|finish|done|ready|fully|totally|entirely)\b',
            r'\b(must|required|necessary|essential|crucial)\b'
        ]
    
    def format_for_stepcard(self, cleaned_response) -> Dict[str, Any]:
        """
        Convert CleanedQSRResponse to StepCard-compatible format
        
        Args:
            cleaned_response: CleanedQSRResponse object or dict
            
        Returns:
            Dictionary formatted for StepCard component
        """
        try:
            # Handle both object and dict inputs
            if hasattr(cleaned_response, 'dict'):
                response_data = cleaned_response.dict()
            else:
                response_data = cleaned_response
            
            # Format main structure
            formatted_response = {
                'id': response_data.get('response_id', f"qsr_{int(datetime.now().timestamp())}"),
                'title': self._format_title(response_data.get('title', 'QSR Procedure')),
                'overall_time': response_data.get('overall_time', 'Time not specified'),
                'difficulty': response_data.get('difficulty_level', 'intermediate'),
                'procedure_type': response_data.get('procedure_type', 'training'),
                'frequency': response_data.get('frequency'),
                'prerequisites': response_data.get('prerequisites', []),
                
                # Format steps for StepCard
                'steps': self._format_steps(response_data.get('steps', [])),
                
                # Format safety information
                'safety_notes': self._format_safety_notes(response_data.get('safety_notes', [])),
                
                # Format verification points
                'verification_points': self._format_verification_points(response_data.get('verification_points', [])),
                
                # Format media references
                'media_references': self._format_media_references(response_data.get('media_references', [])),
                
                # Enhanced metadata for StepCard
                'display_metadata': self._create_display_metadata(response_data),
                
                # Voice integration support
                'voice_support': self._create_voice_support(response_data),
                
                # Mobile optimization
                'mobile_optimized': True,
                'responsive_breakpoints': {
                    'mobile': 480,
                    'tablet': 768,
                    'desktop': 1024
                }
            }
            
            logger.info(f"✅ Formatted {len(formatted_response['steps'])} steps for StepCard component")
            return formatted_response
            
        except Exception as e:
            logger.error(f"❌ Error formatting for StepCard: {e}")
            return self._create_error_stepcard(str(e))
    
    def _format_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format steps for StepCard display"""
        formatted_steps = []
        
        for step in steps:
            formatted_step = {
                'id': f"step_{step.get('step_number', len(formatted_steps) + 1)}",
                'number': step.get('step_number', len(formatted_steps) + 1),
                'title': self._format_step_title(step.get('title', 'Step')),
                'time_estimate': step.get('time_estimate'),
                'description': self._format_step_description(step),
                'tasks': self._format_step_tasks(step.get('tasks', [])),
                'verification': self._format_verification(step.get('verification')),
                'safety_warning': self._format_safety_warning(step.get('safety_warning')),
                'equipment_needed': step.get('equipment_needed', []),
                'tools_needed': step.get('tools_needed', []),
                'media_reference': self._format_media_reference(step.get('media_reference')),
                
                # StepCard-specific enhancements
                'display_priority': self._calculate_display_priority(step),
                'mobile_summary': self._create_mobile_summary(step),
                'voice_description': self._create_voice_description(step),
                'completion_indicator': self._create_completion_indicator(step)
            }
            
            formatted_steps.append(formatted_step)
        
        return formatted_steps
    
    def _format_step_title(self, title: str) -> str:
        """Format step title for mobile display"""
        if not title:
            return "Step"
        
        # Truncate long titles for mobile
        if len(title) > 50:
            title = title[:47] + "..."
        
        # Apply QSR-specific highlighting
        highlighted_title = self._apply_safety_highlighting(title)
        
        return highlighted_title
    
    def _format_step_description(self, step: Dict[str, Any]) -> str:
        """Create formatted description from step data"""
        description_parts = []
        
        # Add main tasks
        tasks = step.get('tasks', [])
        if tasks:
            description_parts.append('. '.join(tasks))
        
        # Add verification if present
        verification = step.get('verification')
        if verification:
            description_parts.append(f"Verification: {verification}")
        
        # Add safety warning if present
        safety_warning = step.get('safety_warning')
        if safety_warning:
            description_parts.append(f"⚠️ Safety: {safety_warning}")
        
        return ' '.join(description_parts)
    
    def _format_step_tasks(self, tasks: List[str]) -> List[Dict[str, Any]]:
        """Format tasks for card display"""
        formatted_tasks = []
        
        for i, task in enumerate(tasks):
            formatted_task = {
                'id': f"task_{i + 1}",
                'text': self._format_task_text(task),
                'highlighted_text': self._apply_highlighting(task),
                'mobile_text': self._format_for_mobile(task),
                'voice_text': self._format_for_voice(task),
                'completion_checkable': True,
                'estimated_duration': self._extract_task_duration(task)
            }
            
            formatted_tasks.append(formatted_task)
        
        return formatted_tasks
    
    def _format_task_text(self, task: str) -> str:
        """Format individual task text"""
        if not task:
            return ""
        
        # Remove bullet points if present
        cleaned_task = re.sub(r'^[•\-\*\u2022\u2023\u25E6]\s*', '', task.strip())
        
        # Ensure proper sentence ending
        if cleaned_task and not cleaned_task.endswith(('.', '!', '?', ':')):
            cleaned_task += '.'
        
        return cleaned_task
    
    def _apply_highlighting(self, text: str) -> str:
        """Apply QSR-specific highlighting to text"""
        highlighted_text = text
        
        # Apply safety highlighting
        highlighted_text = self._apply_safety_highlighting(highlighted_text)
        
        # Apply time-sensitive highlighting
        highlighted_text = self._apply_time_highlighting(highlighted_text)
        
        # Apply completion requirement highlighting
        highlighted_text = self._apply_completion_highlighting(highlighted_text)
        
        return highlighted_text
    
    def _apply_safety_highlighting(self, text: str) -> str:
        """Apply safety term highlighting"""
        for pattern in self.safety_patterns:
            text = re.sub(pattern, r'<strong class="safety-highlight">\1</strong>', text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_time_highlighting(self, text: str) -> str:
        """Apply time-sensitive instruction highlighting"""
        for pattern in self.time_sensitive_patterns:
            text = re.sub(pattern, r'<em class="time-sensitive">\1</em>', text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_completion_highlighting(self, text: str) -> str:
        """Apply completion requirement highlighting"""
        for pattern in self.completion_patterns:
            text = re.sub(pattern, r'<span class="completion-required">\1</span>', text, flags=re.IGNORECASE)
        
        return text
    
    def _format_for_mobile(self, text: str) -> str:
        """Format text for mobile display"""
        if not text:
            return ""
        
        # Truncate long text for mobile
        if len(text) > 120:
            text = text[:117] + "..."
        
        # Remove complex formatting for mobile
        mobile_text = re.sub(r'<[^>]+>', '', text)
        
        return mobile_text
    
    def _format_for_voice(self, text: str) -> str:
        """Format text for voice/TTS readability"""
        if not text:
            return ""
        
        # Remove HTML tags
        voice_text = re.sub(r'<[^>]+>', '', text)
        
        # Add pauses for better TTS
        voice_text = re.sub(r'[.!?]', r'\0 ... ', voice_text)
        
        # Expand abbreviations
        voice_text = re.sub(r'\bmin\b', 'minutes', voice_text, flags=re.IGNORECASE)
        voice_text = re.sub(r'\bhr\b', 'hours', voice_text, flags=re.IGNORECASE)
        voice_text = re.sub(r'\btemp\b', 'temperature', voice_text, flags=re.IGNORECASE)
        
        return voice_text
    
    def _extract_task_duration(self, task: str) -> Optional[str]:
        """Extract duration estimate from task text"""
        time_match = re.search(r'(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)', task, re.IGNORECASE)
        if time_match:
            value = time_match.group(1)
            unit = time_match.group(2)
            
            # Normalize unit
            if unit.lower().startswith('min'):
                unit = 'minutes'
            elif unit.lower().startswith('hr') or unit.lower().startswith('hour'):
                unit = 'hours'
            elif unit.lower().startswith('sec'):
                unit = 'seconds'
            
            return f"{value} {unit}"
        
        return None
    
    def _calculate_display_priority(self, step: Dict[str, Any]) -> int:
        """Calculate display priority for step (1-5, 5 being highest)"""
        priority = 3  # Default priority
        
        # Increase priority for safety warnings
        if step.get('safety_warning'):
            priority += 2
        
        # Increase priority for verification steps
        if step.get('verification'):
            priority += 1
        
        # Increase priority for steps with many tasks
        task_count = len(step.get('tasks', []))
        if task_count > 3:
            priority += 1
        
        return min(5, priority)
    
    def _create_mobile_summary(self, step: Dict[str, Any]) -> str:
        """Create mobile-optimized summary"""
        title = step.get('title', 'Step')
        time_estimate = step.get('time_estimate')
        
        summary = title
        if time_estimate:
            summary += f" ({time_estimate})"
        
        return summary
    
    def _create_voice_description(self, step: Dict[str, Any]) -> str:
        """Create voice-optimized description"""
        parts = []
        
        # Add step title
        title = step.get('title', 'Step')
        parts.append(f"Step {step.get('step_number', 1)}: {title}")
        
        # Add time estimate
        time_estimate = step.get('time_estimate')
        if time_estimate:
            parts.append(f"This step takes approximately {time_estimate}")
        
        # Add main tasks
        tasks = step.get('tasks', [])
        if tasks:
            parts.append("Instructions: " + '. '.join(tasks))
        
        # Add safety warning
        safety_warning = step.get('safety_warning')
        if safety_warning:
            parts.append(f"Important safety note: {safety_warning}")
        
        return '. '.join(parts)
    
    def _create_completion_indicator(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create completion indicator for step"""
        verification = step.get('verification')
        
        return {
            'has_verification': bool(verification),
            'verification_text': verification,
            'completion_criteria': verification or "Mark as complete when finished",
            'visual_indicator': "checkmark" if verification else "progress",
            'voice_confirmation': f"Say 'step {step.get('step_number', 1)} complete' when finished"
        }
    
    def _format_title(self, title: str) -> str:
        """Format main procedure title"""
        if not title:
            return "QSR Procedure"
        
        # Remove common prefixes
        cleaned_title = re.sub(r'^(?:Procedure:?\s*|Process:?\s*|How to:?\s*)', '', title, flags=re.IGNORECASE)
        
        # Apply highlighting
        highlighted_title = self._apply_highlighting(cleaned_title)
        
        return highlighted_title
    
    def _format_safety_notes(self, safety_notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format safety notes for StepCard display"""
        formatted_notes = []
        
        for note in safety_notes:
            formatted_note = {
                'id': f"safety_{len(formatted_notes) + 1}",
                'level': note.get('level', 'medium'),
                'message': self._apply_highlighting(note.get('message', '')),
                'mobile_message': self._format_for_mobile(note.get('message', '')),
                'voice_message': self._format_for_voice(note.get('message', '')),
                'step_reference': note.get('step_reference'),
                'icon': self._get_safety_icon(note.get('level', 'medium')),
                'priority': self._get_safety_priority(note.get('level', 'medium'))
            }
            
            formatted_notes.append(formatted_note)
        
        return formatted_notes
    
    def _get_safety_icon(self, level: str) -> str:
        """Get appropriate icon for safety level"""
        icons = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': 'ℹ️'
        }
        return icons.get(level, '⚠️')
    
    def _get_safety_priority(self, level: str) -> int:
        """Get numeric priority for safety level"""
        priorities = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2
        }
        return priorities.get(level, 3)
    
    def _format_verification_points(self, verification_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format verification points for StepCard"""
        formatted_points = []
        
        for point in verification_points:
            formatted_point = {
                'id': f"verification_{len(formatted_points) + 1}",
                'checkpoint': self._apply_highlighting(point.get('checkpoint', '')),
                'mobile_checkpoint': self._format_for_mobile(point.get('checkpoint', '')),
                'voice_checkpoint': self._format_for_voice(point.get('checkpoint', '')),
                'step_reference': point.get('step_reference'),
                'expected_result': point.get('expected_result'),
                'completion_method': 'visual_check'
            }
            
            formatted_points.append(formatted_point)
        
        return formatted_points
    
    def _format_media_references(self, media_references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format media references for StepCard"""
        formatted_media = []
        
        for media in media_references:
            formatted_media_item = {
                'id': f"media_{media.get('reference_id', len(formatted_media) + 1)}",
                'type': media.get('media_type', 'image'),
                'reference_id': media.get('reference_id'),
                'description': media.get('description', ''),
                'mobile_description': self._format_for_mobile(media.get('description', '')),
                'step_reference': media.get('step_reference'),
                'url': media.get('url'),
                'placeholder_url': self._get_placeholder_url(media.get('media_type', 'image')),
                'accessibility_text': self._create_accessibility_text(media)
            }
            
            formatted_media.append(formatted_media_item)
        
        return formatted_media
    
    def _get_placeholder_url(self, media_type: str) -> str:
        """Get placeholder URL for media type"""
        placeholders = {
            'image': '/assets/placeholder-image.png',
            'video': '/assets/placeholder-video.png',
            'diagram': '/assets/placeholder-diagram.png',
            'illustration': '/assets/placeholder-illustration.png',
            'chart': '/assets/placeholder-chart.png'
        }
        return placeholders.get(media_type, '/assets/placeholder-image.png')
    
    def _create_accessibility_text(self, media: Dict[str, Any]) -> str:
        """Create accessibility text for media"""
        media_type = media.get('media_type', 'image')
        description = media.get('description', '')
        
        if description:
            return f"{media_type.title()}: {description}"
        else:
            return f"{media_type.title()} reference {media.get('reference_id', '1')}"
    
    def _create_display_metadata(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced metadata for StepCard display"""
        return {
            'total_steps': len(response_data.get('steps', [])),
            'estimated_duration': response_data.get('overall_time', 'Time not specified'),
            'difficulty_level': response_data.get('difficulty_level', 'intermediate'),
            'safety_warnings_count': len(response_data.get('safety_notes', [])),
            'verification_points_count': len(response_data.get('verification_points', [])),
            'media_references_count': len(response_data.get('media_references', [])),
            'confidence_score': response_data.get('confidence_score', 0.8),
            'last_updated': response_data.get('processed_at', datetime.now().isoformat()),
            'responsive_design': True,
            'accessibility_compliant': True
        }
    
    def _create_voice_support(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create voice integration support data"""
        return {
            'voice_enabled': True,
            'tts_optimized': True,
            'voice_commands': [
                "next step",
                "previous step",
                "repeat step",
                "safety information",
                "verification points",
                "complete step"
            ],
            'audio_descriptions': True,
            'hands_free_navigation': True,
            'voice_confirmation': True
        }
    
    def _format_verification(self, verification: Optional[str]) -> Optional[Dict[str, Any]]:
        """Format verification for StepCard"""
        if not verification:
            return None
        
        return {
            'text': self._apply_highlighting(verification),
            'mobile_text': self._format_for_mobile(verification),
            'voice_text': self._format_for_voice(verification),
            'completion_method': 'visual_check',
            'required': True
        }
    
    def _format_safety_warning(self, safety_warning: Optional[str]) -> Optional[Dict[str, Any]]:
        """Format safety warning for StepCard"""
        if not safety_warning:
            return None
        
        return {
            'text': self._apply_safety_highlighting(safety_warning),
            'mobile_text': self._format_for_mobile(safety_warning),
            'voice_text': self._format_for_voice(safety_warning),
            'level': 'high',
            'icon': '⚠️',
            'prominent_display': True
        }
    
    def _format_media_reference(self, media_reference: Optional[str]) -> Optional[Dict[str, Any]]:
        """Format media reference for StepCard"""
        if not media_reference:
            return None
        
        return {
            'text': media_reference,
            'type': 'reference',
            'placeholder_available': True,
            'accessibility_text': f"Media reference: {media_reference}"
        }
    
    def _create_error_stepcard(self, error_message: str) -> Dict[str, Any]:
        """Create error StepCard format"""
        return {
            'id': f"error_{int(datetime.now().timestamp())}",
            'title': 'Processing Error',
            'overall_time': 'Unknown',
            'difficulty': 'beginner',
            'procedure_type': 'error',
            'steps': [{
                'id': 'step_error',
                'number': 1,
                'title': 'Error',
                'description': f"Unable to process procedure: {error_message}",
                'tasks': [{
                    'id': 'task_error',
                    'text': f"Error: {error_message}",
                    'highlighted_text': f"<strong class='error'>Error: {error_message}</strong>",
                    'mobile_text': f"Error: {error_message}",
                    'voice_text': f"An error occurred: {error_message}"
                }],
                'safety_warning': {
                    'text': 'Contact technical support for assistance',
                    'level': 'high',
                    'icon': '🚨'
                }
            }],
            'safety_notes': [],
            'verification_points': [],
            'media_references': [],
            'display_metadata': {
                'total_steps': 1,
                'error_state': True
            }
        }

# Global instance for use throughout the application
stepcard_formatter = StepCardFormatter()