#!/usr/bin/env python3
"""
Ragie Response Post-Processing for Line Lead
===========================================

Text structure normalization module to clean up raw Ragie responses:
- Handle inconsistent step numbering patterns
- Clean up bullet point formatting variations
- Extract and normalize time estimates from text
- Fix headers merged with content
- Standardize verification checkpoint formatting

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types of content that can be identified in QSR responses"""
    STEP = "step"
    SAFETY_WARNING = "safety_warning"
    VERIFICATION = "verification"
    TIME_ESTIMATE = "time_estimate"
    EQUIPMENT = "equipment"
    MEDIA_REFERENCE = "media_reference"

@dataclass
class ExtractedContent:
    """Structured content extracted from raw text"""
    content_type: ContentType
    text: str
    metadata: Dict[str, Any]
    confidence: float = 1.0

class RagieResponseCleaner:
    """
    Comprehensive text cleaning and normalization for Ragie QSR responses
    """
    
    def __init__(self):
        """Initialize with QSR-specific patterns and cleaning rules"""
        
        # Step numbering patterns (various formats from Ragie)
        self.step_patterns = [
            r'(\d+)\.\s*([A-Z][^.]*)',  # "2. Check Cleanliness"
            r'Step\s*(\d+):\s*(.*)',     # "Step 1: Initial Setup"
            r'Procedure\s*(\d+)\.\s*(.*)', # "Procedure 1. Start process"
            r'(\d+)\)\s*([A-Z][^.]*)',   # "1) First task"
            r'Task\s*(\d+):\s*(.*)',     # "Task 1: Complete setup"
        ]
        
        # Time estimate patterns
        self.time_patterns = [
            r'Time\s*Estimate:\s*(\d+(?:\.\d+)?)\s*(minutes?|hours?|mins?|hrs?)',
            r'(\d+(?:\.\d+)?)\s*(minutes?|hours?|mins?|hrs?)\s*(?:before|after|during)',
            r'Estimated\s*time:\s*(\d+(?:\.\d+)?)\s*(minutes?|hours?|mins?|hrs?)',
            r'Duration:\s*(\d+(?:\.\d+)?)\s*(minutes?|hours?|mins?|hrs?)',
            r'Takes?\s*about\s*(\d+(?:\.\d+)?)\s*(minutes?|hours?|mins?|hrs?)',
            r'Allow\s*(\d+(?:\.\d+)?)\s*(minutes?|hours?|mins?|hrs?)',
        ]
        
        # Safety warning indicators
        self.safety_indicators = [
            'warning', 'caution', 'danger', 'hazard', 'safety', 'sanitizing',
            'hot', 'burn', 'electrical', 'chemical', 'toxic', 'harmful'
        ]
        
        # Verification checkpoint patterns
        self.verification_patterns = [
            r'Verification\s*Checkpoint:?\s*(.*)',
            r'Check\s*that\s*(.*)',
            r'Ensure\s*(.*)',
            r'Verify\s*(.*)',
            r'Confirm\s*(.*)',
        ]
        
        # Media reference patterns
        self.media_patterns = [
            r'(?:see|refer to|view)\s*(?:figure|image|diagram|photo|video)\s*(\d+)',
            r'(?:figure|image|diagram|photo|video)\s*(\d+)',
            r'visual\s*aid\s*(\d+)',
            r'illustration\s*(\d+)',
        ]
    
    def clean_step_numbering(self, text: str) -> str:
        """
        Convert various step numbering patterns to structured format
        
        Args:
            text: Raw text with inconsistent step numbering
            
        Returns:
            Text with normalized step numbering
        """
        cleaned_text = text
        
        # Apply each step pattern
        for pattern in self.step_patterns:
            def replace_step(match):
                number = match.group(1)
                content = match.group(2).strip()
                return f'\n## Step {number}: {content}\n'
            
            cleaned_text = re.sub(pattern, replace_step, cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Clean up bullet points with various unicode variations
        bullet_replacements = [
            (r'•\s*', '• '),
            (r'[\u2022\u2023\u25E6]\s*', '• '),
            (r'[\u2043\u204C\u204D]\s*', '• '),
            (r'-\s*', '• '),
            (r'\*\s*', '• '),
        ]
        
        for pattern, replacement in bullet_replacements:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
        # Fix headers merged with content (like "applicable. 2. Check Cleanliness")
        cleaned_text = re.sub(
            r'([a-z])\.\s*(\d+)\.\s*([A-Z][^.]*)',
            r'\1.\n\n## Step \2: \3\n',
            cleaned_text
        )
        
        return cleaned_text
    
    def extract_time_estimates(self, text: str) -> Tuple[Optional[str], str]:
        """
        Extract time estimates from text and clean them from main content
        
        Args:
            text: Text containing time estimates
            
        Returns:
            Tuple of (time_estimate, cleaned_text)
        """
        time_estimate = None
        cleaned_text = text
        
        for pattern in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract time value and unit
                time_value = match.group(1)
                time_unit = match.group(2)
                
                # Normalize unit
                if time_unit.lower().startswith('min'):
                    unit = 'minutes'
                elif time_unit.lower().startswith('hr') or time_unit.lower().startswith('hour'):
                    unit = 'hours'
                else:
                    unit = time_unit.lower()
                
                # Format time estimate
                if float(time_value) == 1:
                    unit = unit.rstrip('s')  # Remove plural for singular
                
                time_estimate = f"{time_value} {unit}"
                
                # Remove the time estimate from the main text
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE).strip()
                break
        
        return time_estimate, cleaned_text
    
    def normalize_section_headers(self, text: str) -> str:
        """
        Normalize section headers and ensure proper markdown formatting
        
        Args:
            text: Raw text with inconsistent headers
            
        Returns:
            Text with normalized section headers
        """
        # Fix "Verification Checkpoint" formatting
        text = re.sub(
            r'Verification\s*Checkpoint:?\s*(.*)',
            r'\n### Verification Checkpoint\n\1\n',
            text,
            flags=re.IGNORECASE
        )
        
        # Normalize numbered procedure headers
        text = re.sub(
            r'^(\d+)\.\s*([A-Z][^.]*)\s*$',
            r'\n## \2\n',
            text,
            flags=re.MULTILINE
        )
        
        # Fix headers that got merged with content
        text = re.sub(
            r'([a-z])\.\s*([A-Z][A-Z\s]+):?\s*',
            r'\1.\n\n### \2\n',
            text
        )
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def extract_safety_warnings(self, text: str) -> List[ExtractedContent]:
        """
        Extract safety warnings from text
        
        Args:
            text: Text containing safety information
            
        Returns:
            List of ExtractedContent objects for safety warnings
        """
        safety_warnings = []
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if line contains safety indicators
            safety_score = sum(1 for indicator in self.safety_indicators if indicator in line_lower)
            
            if safety_score > 0 and len(line.strip()) > 10:  # Minimum length filter
                confidence = min(1.0, safety_score / 3.0)  # Scale confidence
                
                safety_warnings.append(ExtractedContent(
                    content_type=ContentType.SAFETY_WARNING,
                    text=line.strip(),
                    metadata={
                        'keywords_found': [ind for ind in self.safety_indicators if ind in line_lower],
                        'severity': 'high' if safety_score >= 2 else 'medium'
                    },
                    confidence=confidence
                ))
        
        return safety_warnings
    
    def extract_verification_points(self, text: str) -> List[ExtractedContent]:
        """
        Extract verification checkpoints from text
        
        Args:
            text: Text containing verification points
            
        Returns:
            List of ExtractedContent objects for verification points
        """
        verification_points = []
        
        for pattern in self.verification_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                verification_text = match.group(1).strip()
                
                if len(verification_text) > 5:  # Minimum length
                    verification_points.append(ExtractedContent(
                        content_type=ContentType.VERIFICATION,
                        text=verification_text,
                        metadata={
                            'pattern_matched': pattern,
                            'full_match': match.group(0)
                        }
                    ))
        
        return verification_points
    
    def extract_media_references(self, text: str) -> List[ExtractedContent]:
        """
        Extract media references from text
        
        Args:
            text: Text containing media references
            
        Returns:
            List of ExtractedContent objects for media references
        """
        media_references = []
        
        for pattern in self.media_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                media_number = match.group(1)
                
                media_references.append(ExtractedContent(
                    content_type=ContentType.MEDIA_REFERENCE,
                    text=match.group(0),
                    metadata={
                        'media_number': media_number,
                        'media_type': self._identify_media_type(match.group(0))
                    }
                ))
        
        return media_references
    
    def _identify_media_type(self, text: str) -> str:
        """Identify the type of media referenced"""
        text_lower = text.lower()
        
        if 'video' in text_lower:
            return 'video'
        elif 'image' in text_lower or 'photo' in text_lower:
            return 'image'
        elif 'diagram' in text_lower or 'schematic' in text_lower:
            return 'diagram'
        elif 'figure' in text_lower or 'illustration' in text_lower:
            return 'illustration'
        else:
            return 'unknown'
    
    def extract_equipment_mentions(self, text: str) -> List[ExtractedContent]:
        """
        Extract equipment mentions from text
        
        Args:
            text: Text containing equipment references
            
        Returns:
            List of ExtractedContent objects for equipment mentions
        """
        equipment_mentions = []
        
        # Common QSR equipment patterns
        equipment_patterns = [
            r'fryer\s*(?:basket|unit|system)?',
            r'grill\s*(?:top|surface|unit)?',
            r'oven\s*(?:chamber|unit|system)?',
            r'ice\s*machine',
            r'pos\s*system',
            r'drive[- ]?thru',
            r'prep\s*station',
            r'dishwasher',
            r'mixer\s*(?:bowl|unit)?',
            r'baxter\s*\w*',
            r'taylor\s*\w*',
            r'grote\s*\w*',
        ]
        
        for pattern in equipment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                equipment_text = match.group(0)
                
                equipment_mentions.append(ExtractedContent(
                    content_type=ContentType.EQUIPMENT,
                    text=equipment_text,
                    metadata={
                        'equipment_type': self._classify_equipment(equipment_text),
                        'position': match.span()
                    }
                ))
        
        return equipment_mentions
    
    def _classify_equipment(self, equipment_text: str) -> str:
        """Classify equipment into categories"""
        text_lower = equipment_text.lower()
        
        if 'fryer' in text_lower:
            return 'fryer'
        elif 'grill' in text_lower:
            return 'grill'
        elif 'oven' in text_lower:
            return 'oven'
        elif 'ice' in text_lower:
            return 'refrigeration'
        elif 'pos' in text_lower:
            return 'pos_system'
        elif 'drive' in text_lower:
            return 'drive_thru'
        elif any(brand in text_lower for brand in ['baxter', 'taylor', 'grote']):
            return 'commercial_equipment'
        else:
            return 'general_equipment'
    
    def comprehensive_clean(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive cleaning and extraction on text
        
        Args:
            text: Raw text to clean and process
            
        Returns:
            Dictionary containing cleaned text and extracted content
        """
        try:
            # Step 1: Normalize section headers
            normalized_text = self.normalize_section_headers(text)
            
            # Step 2: Clean step numbering
            cleaned_steps = self.clean_step_numbering(normalized_text)
            
            # Step 3: Extract time estimates
            time_estimate, cleaned_text = self.extract_time_estimates(cleaned_steps)
            
            # Step 4: Extract structured content
            safety_warnings = self.extract_safety_warnings(cleaned_text)
            verification_points = self.extract_verification_points(cleaned_text)
            media_references = self.extract_media_references(cleaned_text)
            equipment_mentions = self.extract_equipment_mentions(cleaned_text)
            
            # Step 5: Final cleanup
            final_text = self._final_cleanup(cleaned_text)
            
            return {
                'cleaned_text': final_text,
                'time_estimate': time_estimate,
                'extracted_content': {
                    'safety_warnings': safety_warnings,
                    'verification_points': verification_points,
                    'media_references': media_references,
                    'equipment_mentions': equipment_mentions
                },
                'processing_metadata': {
                    'original_length': len(text),
                    'cleaned_length': len(final_text),
                    'compression_ratio': len(final_text) / len(text) if len(text) > 0 else 0,
                    'safety_warnings_count': len(safety_warnings),
                    'verification_points_count': len(verification_points),
                    'media_references_count': len(media_references),
                    'equipment_mentions_count': len(equipment_mentions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive cleaning: {e}")
            return {
                'cleaned_text': text,  # Return original if cleaning fails
                'time_estimate': None,
                'extracted_content': {
                    'safety_warnings': [],
                    'verification_points': [],
                    'media_references': [],
                    'equipment_mentions': []
                },
                'processing_metadata': {
                    'error': str(e),
                    'fallback_used': True
                }
            }
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass on text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Ensure proper sentence endings
        text = re.sub(r'([a-zA-Z])\s*\n', r'\1.\n', text)
        
        # Clean up bullet points
        text = re.sub(r'•\s*•', '•', text)
        
        return text.strip()
    
    def process_ragie_chunks(self, ragie_results) -> Dict[str, Any]:
        """
        Process raw Ragie chunks into structured CleanedQSRResponse
        
        Args:
            ragie_results: List of Ragie search results
            
        Returns:
            Dictionary ready for CleanedQSRResponse creation
        """
        try:
            # Combine all text from chunks
            if not ragie_results:
                return self._create_empty_response()
            
            # Extract and combine text content
            full_text = ""
            source_documents = []
            
            for chunk in ragie_results:
                if hasattr(chunk, 'text'):
                    full_text += "\n" + chunk.text
                elif hasattr(chunk, 'content'):
                    full_text += "\n" + chunk.content
                
                # Extract source information
                if hasattr(chunk, 'metadata') and chunk.metadata:
                    source_filename = chunk.metadata.get('original_filename') or chunk.metadata.get('filename')
                    if source_filename and source_filename not in source_documents:
                        source_documents.append(source_filename)
            
            # Apply comprehensive cleaning
            cleaned_data = self.comprehensive_clean(full_text)
            
            # Extract structured data
            steps = self.extract_steps(cleaned_data['cleaned_text'])
            title = self.extract_title(cleaned_data['cleaned_text'])
            overall_time = self.calculate_overall_time(steps, cleaned_data['time_estimate'])
            
            # Build structured response
            response_data = {
                'title': title,
                'steps': steps,
                'overall_time': overall_time,
                'safety_notes': self._convert_safety_warnings(cleaned_data['extracted_content']['safety_warnings']),
                'verification_points': self._convert_verification_points(cleaned_data['extracted_content']['verification_points']),
                'media_references': self._convert_media_references(cleaned_data['extracted_content']['media_references']),
                'procedure_type': self._infer_procedure_type(full_text),
                'difficulty_level': self._infer_difficulty_level(steps),
                'frequency': self._infer_frequency(full_text),
                'prerequisites': self._extract_prerequisites(full_text),
                'confidence_score': self._calculate_confidence_score(cleaned_data, ragie_results),
                'source_documents': source_documents
            }
            
            logger.info(f"✅ Processed {len(ragie_results)} Ragie chunks into {len(steps)} structured steps")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error processing Ragie chunks: {e}")
            return self._create_error_response(str(e))
    
    def extract_steps(self, cleaned_text: str) -> List[Dict[str, Any]]:
        """
        Extract structured steps from cleaned text
        
        Args:
            cleaned_text: Cleaned text with normalized headers
            
        Returns:
            List of step dictionaries
        """
        steps = []
        
        # Split text by step headers
        step_sections = re.split(r'\n## Step (\d+):', cleaned_text)
        
        if len(step_sections) > 1:
            # Process each step section
            for i in range(1, len(step_sections), 2):
                if i + 1 < len(step_sections):
                    step_number = int(step_sections[i])
                    step_content = step_sections[i + 1]
                    
                    step_data = self._parse_step_content(step_number, step_content)
                    if step_data:
                        steps.append(step_data)
        else:
            # Fallback: try to extract steps from numbered lists
            steps = self._extract_numbered_steps(cleaned_text)
        
        # Ensure steps are properly numbered
        for i, step in enumerate(steps):
            step['step_number'] = i + 1
        
        return steps
    
    def _parse_step_content(self, step_number: int, content: str) -> Dict[str, Any]:
        """Parse content for a single step"""
        try:
            lines = content.strip().split('\n')
            
            # Extract title (first line)
            title = lines[0].strip() if lines else f"Step {step_number}"
            
            # Extract tasks (bullet points)
            tasks = []
            verification = None
            safety_warning = None
            equipment_needed = []
            tools_needed = []
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # Check for verification
                if any(keyword in line.lower() for keyword in ['verify', 'check', 'ensure', 'confirm']):
                    verification = line
                
                # Check for safety warning
                elif any(keyword in line.lower() for keyword in self.safety_indicators):
                    safety_warning = line
                
                # Check for equipment/tools
                elif any(keyword in line.lower() for keyword in ['equipment', 'tool', 'need', 'require']):
                    if 'equipment' in line.lower():
                        equipment_needed.append(line)
                    else:
                        tools_needed.append(line)
                
                # Otherwise, it's a task
                elif line.startswith('• ') or line.startswith('- '):
                    tasks.append(line)
                elif len(line) > 10:  # Minimum length for a task
                    tasks.append(line)
            
            # Extract time estimate from content
            time_estimate = self._extract_time_from_content(content)
            
            return {
                'step_number': step_number,
                'title': title,
                'time_estimate': time_estimate,
                'tasks': tasks,
                'verification': verification,
                'safety_warning': safety_warning,
                'equipment_needed': equipment_needed,
                'tools_needed': tools_needed
            }
            
        except Exception as e:
            logger.error(f"Error parsing step {step_number}: {e}")
            return None
    
    def _extract_numbered_steps(self, text: str) -> List[Dict[str, Any]]:
        """Fallback method to extract numbered steps"""
        steps = []
        
        # Find numbered patterns
        numbered_patterns = [
            r'(\d+)\.\s*([^\n]+)',
            r'Step\s*(\d+):\s*([^\n]+)',
            r'(\d+)\)\s*([^\n]+)'
        ]
        
        for pattern in numbered_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                for match in matches:
                    step_number = int(match[0])
                    step_content = match[1]
                    
                    steps.append({
                        'step_number': step_number,
                        'title': step_content,
                        'time_estimate': None,
                        'tasks': [step_content],
                        'verification': None,
                        'safety_warning': None,
                        'equipment_needed': [],
                        'tools_needed': []
                    })
                break
        
        return steps
    
    def _extract_time_from_content(self, content: str) -> Optional[str]:
        """Extract time estimate from step content"""
        for pattern in self.time_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                time_value = match.group(1)
                time_unit = match.group(2)
                
                # Normalize unit
                if time_unit.lower().startswith('min'):
                    unit = 'minutes'
                elif time_unit.lower().startswith('hr') or time_unit.lower().startswith('hour'):
                    unit = 'hours'
                else:
                    unit = time_unit.lower()
                
                return f"{time_value} {unit}"
        
        return None
    
    def extract_title(self, text: str) -> str:
        """Extract procedure title from text"""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 5:
                # Clean up title
                title = re.sub(r'^(?:Procedure:?\s*|Process:?\s*|How to:?\s*)', '', line, flags=re.IGNORECASE)
                if title:
                    return title
        
        return "QSR Procedure"
    
    def calculate_overall_time(self, steps: List[Dict[str, Any]], extracted_time: Optional[str]) -> str:
        """Calculate overall time estimate"""
        if extracted_time:
            return extracted_time
        
        # Try to sum up step times
        total_minutes = 0
        has_estimates = False
        
        for step in steps:
            if step.get('time_estimate'):
                time_match = re.search(r'(\d+(?:\.\d+)?)\s*minutes?', step['time_estimate'], re.IGNORECASE)
                if time_match:
                    total_minutes += float(time_match.group(1))
                    has_estimates = True
        
        if has_estimates:
            if total_minutes < 60:
                return f"{int(total_minutes)} minutes"
            else:
                hours = int(total_minutes // 60)
                minutes = int(total_minutes % 60)
                if minutes == 0:
                    return f"{hours} hour{'s' if hours > 1 else ''}"
                else:
                    return f"{hours} hour{'s' if hours > 1 else ''} {minutes} minutes"
        
        # Default estimate based on step count
        step_count = len(steps)
        if step_count <= 3:
            return "15-30 minutes"
        elif step_count <= 6:
            return "30-60 minutes"
        else:
            return "1-2 hours"
    
    def _convert_safety_warnings(self, safety_warnings: List[ExtractedContent]) -> List[Dict[str, Any]]:
        """Convert extracted safety warnings to structured format"""
        return [
            {
                'level': warning.metadata.get('severity', 'medium'),
                'message': warning.text,
                'step_reference': None,
                'keywords': warning.metadata.get('keywords_found', [])
            }
            for warning in safety_warnings
        ]
    
    def _convert_verification_points(self, verification_points: List[ExtractedContent]) -> List[Dict[str, Any]]:
        """Convert extracted verification points to structured format"""
        return [
            {
                'step_reference': None,
                'checkpoint': point.text,
                'expected_result': None
            }
            for point in verification_points
        ]
    
    def _convert_media_references(self, media_references: List[ExtractedContent]) -> List[Dict[str, Any]]:
        """Convert extracted media references to structured format"""
        return [
            {
                'media_type': media.metadata.get('media_type', 'image'),
                'reference_id': media.metadata.get('media_number', '1'),
                'description': media.text,
                'step_reference': None,
                'url': None
            }
            for media in media_references
        ]
    
    def _infer_procedure_type(self, text: str) -> str:
        """Infer procedure type from text content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['clean', 'wash', 'sanitize', 'disinfect']):
            return 'cleaning'
        elif any(word in text_lower for word in ['repair', 'fix', 'maintain', 'service']):
            return 'maintenance'
        elif any(word in text_lower for word in ['troubleshoot', 'diagnose', 'solve', 'problem']):
            return 'troubleshooting'
        elif any(word in text_lower for word in ['setup', 'install', 'configure', 'initialize']):
            return 'setup'
        elif any(word in text_lower for word in ['safety', 'emergency', 'hazard', 'warning']):
            return 'safety'
        else:
            return 'training'
    
    def _infer_difficulty_level(self, steps: List[Dict[str, Any]]) -> str:
        """Infer difficulty level based on step complexity"""
        if not steps:
            return 'beginner'
        
        step_count = len(steps)
        complexity_score = 0
        
        for step in steps:
            # Check for complex indicators
            if step.get('safety_warning'):
                complexity_score += 2
            if step.get('verification'):
                complexity_score += 1
            if len(step.get('tasks', [])) > 3:
                complexity_score += 1
        
        # Determine difficulty
        if step_count <= 3 and complexity_score <= 2:
            return 'beginner'
        elif step_count <= 6 and complexity_score <= 5:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _infer_frequency(self, text: str) -> Optional[str]:
        """Infer how often procedure should be performed"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['daily', 'every day', 'each day']):
            return 'daily'
        elif any(word in text_lower for word in ['weekly', 'every week', 'once a week']):
            return 'weekly'
        elif any(word in text_lower for word in ['monthly', 'every month', 'once a month']):
            return 'monthly'
        elif any(word in text_lower for word in ['as needed', 'when needed', 'occasionally']):
            return 'as needed'
        
        return None
    
    def _extract_prerequisites(self, text: str) -> List[str]:
        """Extract prerequisites from text"""
        prerequisites = []
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['prerequisite', 'requirement', 'before', 'first', 'ensure']):
                cleaned_line = line.strip()
                if len(cleaned_line) > 10:
                    prerequisites.append(cleaned_line)
        
        return prerequisites
    
    def _calculate_confidence_score(self, cleaned_data: Dict[str, Any], ragie_results) -> float:
        """Calculate confidence score for the response"""
        base_score = 0.5
        
        # Factor in content quality
        if cleaned_data.get('extracted_content', {}).get('safety_warnings'):
            base_score += 0.1
        
        if cleaned_data.get('extracted_content', {}).get('verification_points'):
            base_score += 0.1
        
        if cleaned_data.get('time_estimate'):
            base_score += 0.1
        
        # Factor in source quality
        if ragie_results:
            avg_score = sum(getattr(r, 'score', 0.5) for r in ragie_results) / len(ragie_results)
            base_score += avg_score * 0.2
        
        return min(1.0, base_score)
    
    def _create_empty_response(self) -> Dict[str, Any]:
        """Create empty response structure"""
        return {
            'title': 'No Procedure Found',
            'steps': [],
            'overall_time': 'Unknown',
            'safety_notes': [],
            'verification_points': [],
            'media_references': [],
            'procedure_type': 'training',
            'difficulty_level': 'beginner',
            'frequency': None,
            'prerequisites': [],
            'confidence_score': 0.0,
            'source_documents': []
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response structure"""
        return {
            'title': 'Processing Error',
            'steps': [{
                'step_number': 1,
                'title': 'Error',
                'time_estimate': None,
                'tasks': [f"Unable to process procedure: {error_message}"],
                'verification': None,
                'safety_warning': 'Contact technical support',
                'equipment_needed': [],
                'tools_needed': []
            }],
            'overall_time': 'Unknown',
            'safety_notes': [],
            'verification_points': [],
            'media_references': [],
            'procedure_type': 'training',
            'difficulty_level': 'beginner',
            'frequency': None,
            'prerequisites': [],
            'confidence_score': 0.0,
            'source_documents': []
        }

# Global instance for use throughout the application
response_cleaner = RagieResponseCleaner()