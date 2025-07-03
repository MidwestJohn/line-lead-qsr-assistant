"""
Step Parser for QSR Maintenance Instructions
Extracts structured step data from AI responses to prepare for future Playbooks UX
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import re
from enum import Enum

class StepType(str, Enum):
    """Types of maintenance steps for QSR operations"""
    SAFETY = "safety"           # Safety precautions, PPE, power-off
    PREPARATION = "preparation" # Setup, gathering tools/materials
    CLEANING = "cleaning"       # Cleaning and sanitization actions
    MAINTENANCE = "maintenance" # Repair, replacement, adjustment
    INSPECTION = "inspection"   # Checking, testing, verification
    COMPLETION = "completion"   # Final steps, reassembly, testing

class StepObject(BaseModel):
    """Structured data for a single maintenance step"""
    step_number: int = Field(description="Sequential step number (1, 2, 3...)")
    action_description: str = Field(description="Clear action description from AI response")
    step_type: Optional[StepType] = Field(default=None, description="Categorized step type")
    estimated_duration: Optional[str] = Field(default=None, description="Estimated time (e.g., '2 minutes')")
    safety_critical: bool = Field(default=False, description="Whether this step involves safety considerations")
    
    # Future multi-modal graph RAG fields
    image_citation_placeholder: Optional[str] = Field(default=None, description="Future: Image reference from graph RAG")
    video_citation_placeholder: Optional[str] = Field(default=None, description="Future: Video reference from graph RAG")
    diagram_citation_placeholder: Optional[str] = Field(default=None, description="Future: Diagram reference from graph RAG")
    related_equipment: Optional[str] = Field(default=None, description="Equipment referenced in this step")
    
    # Context for future card components
    prerequisites: List[str] = Field(default_factory=list, description="Required before this step")
    warnings: List[str] = Field(default_factory=list, description="Safety warnings for this step")
    tips: List[str] = Field(default_factory=list, description="Helpful tips or best practices")

class ParsedStepsResponse(BaseModel):
    """Complete structured response with parsed steps"""
    original_text: str = Field(description="Original AI response text")
    has_steps: bool = Field(description="Whether structured steps were detected")
    procedure_title: Optional[str] = Field(default=None, description="Inferred procedure name")
    total_steps: int = Field(description="Number of steps detected")
    estimated_total_time: Optional[str] = Field(default=None, description="Total estimated time")
    equipment_involved: List[str] = Field(default_factory=list, description="All equipment mentioned")
    
    steps: List[StepObject] = Field(default_factory=list, description="Parsed step objects")
    
    # Future Playbook UX preparation
    difficulty_level: Optional[str] = Field(default=None, description="Future: beginner/intermediate/advanced")
    required_tools: List[str] = Field(default_factory=list, description="Tools needed for procedure")
    safety_level: Optional[str] = Field(default=None, description="Future: low/medium/high safety requirements")

class StepParser:
    """Robust step detection and extraction system for QSR maintenance instructions"""
    
    def __init__(self):
        # Enhanced regex patterns for step detection (order matters - most specific first)
        self.step_patterns = [
            r'Step\s+(\d+)[,:]\s*(.+?)(?=\n\s*Step\s+\d+|\n\s*$|$)',  # "Step 1, action" or "Step 1: action"
            r'(\d+)\.\s*(.+?)(?=\n\s*\d+\.|\n\s*$|$)',                # "1. action" format
        ]
        
        # Equipment detection patterns
        self.equipment_patterns = [
            r'\b(fryer|deep fryer|fry station)\b',
            r'\b(grill|griddle|flat top|char grill)\b', 
            r'\b(ice cream machine|ice machine|ice maker)\b',
            r'\b(dishwasher|dish machine|warewasher)\b',
            r'\b(oven|convection oven|pizza oven)\b',
            r'\b(refrigerator|fridge|cooler|freezer)\b',
            r'\b(mixer|blender|food processor)\b',
            r'\b(coffee machine|espresso machine)\b'
        ]
        
        # Safety keyword detection
        self.safety_keywords = [
            'turn off', 'power off', 'unplug', 'disconnect', 'safety', 'caution',
            'warning', 'hot', 'electrical', 'chemical', 'ppe', 'gloves', 'goggles'
        ]
        
        # Step type classification keywords
        self.step_type_keywords = {
            StepType.SAFETY: ['turn off', 'power off', 'safety', 'ppe', 'gloves', 'unplug', 'caution'],
            StepType.PREPARATION: ['gather', 'prepare', 'setup', 'collect', 'arrange', 'ready'],
            StepType.CLEANING: ['clean', 'wash', 'rinse', 'sanitize', 'wipe', 'scrub', 'disinfect'],
            StepType.MAINTENANCE: ['replace', 'repair', 'adjust', 'tighten', 'lubricate', 'service'],
            StepType.INSPECTION: ['check', 'inspect', 'test', 'verify', 'examine', 'ensure'],
            StepType.COMPLETION: ['reassemble', 'restart', 'test run', 'final', 'complete', 'finish']
        }
    
    def parse_steps_from_response(self, ai_response: str) -> ParsedStepsResponse:
        """
        Main parsing function - extracts structured steps from AI response
        
        Args:
            ai_response: Raw AI response text containing potential steps
            
        Returns:
            ParsedStepsResponse with structured step data
        """
        
        # Initialize response object
        parsed_response = ParsedStepsResponse(
            original_text=ai_response,
            has_steps=False,
            total_steps=0
        )
        
        # Try each regex pattern to detect steps
        detected_steps = []
        for pattern in self.step_patterns:
            matches = re.finditer(pattern, ai_response, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                step_num = int(match.group(1))
                action_text = match.group(2).strip()
                
                # Clean up action text (remove trailing punctuation, extra whitespace)
                action_text = re.sub(r'\s+', ' ', action_text)
                action_text = action_text.rstrip('.,;')
                
                if len(action_text) > 10:  # Filter out very short/incomplete matches
                    detected_steps.append((step_num, action_text))
        
        # Sort steps by number and remove duplicates
        detected_steps = sorted(list(set(detected_steps)), key=lambda x: x[0])
        
        if detected_steps:
            parsed_response.has_steps = True
            parsed_response.total_steps = len(detected_steps)
            
            # Extract equipment mentioned across all steps
            parsed_response.equipment_involved = self._extract_equipment(ai_response)
            
            # Infer procedure title from context
            parsed_response.procedure_title = self._infer_procedure_title(ai_response, parsed_response.equipment_involved)
            
            # Parse each step into structured object
            for step_num, action_text in detected_steps:
                step_obj = self._create_step_object(step_num, action_text, ai_response)
                parsed_response.steps.append(step_obj)
            
            # Calculate required tools and safety level
            parsed_response.required_tools = self._extract_tools(ai_response)
            parsed_response.safety_level = self._assess_safety_level(parsed_response.steps)
        
        return parsed_response
    
    def _create_step_object(self, step_number: int, action_description: str, full_context: str) -> StepObject:
        """Create a structured StepObject from raw step data"""
        
        step_obj = StepObject(
            step_number=step_number,
            action_description=action_description
        )
        
        # Classify step type based on keywords
        step_obj.step_type = self._classify_step_type(action_description)
        
        # Detect safety criticality
        step_obj.safety_critical = any(keyword in action_description.lower() for keyword in self.safety_keywords)
        
        # Extract equipment for this specific step
        step_obj.related_equipment = self._extract_equipment_from_step(action_description)
        
        # Extract warnings and tips from step text
        step_obj.warnings = self._extract_warnings(action_description)
        step_obj.tips = self._extract_tips(action_description)
        
        # Estimate duration (simple heuristic for now)
        step_obj.estimated_duration = self._estimate_step_duration(action_description, step_obj.step_type)
        
        return step_obj
    
    def _classify_step_type(self, action_text: str) -> Optional[StepType]:
        """Classify step type based on action keywords"""
        action_lower = action_text.lower()
        
        # Score each step type based on keyword matches
        scores = {}
        for step_type, keywords in self.step_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in action_lower)
            if score > 0:
                scores[step_type] = score
        
        # Return the highest scoring type, or None if no matches
        return max(scores.keys(), key=scores.get) if scores else None
    
    def _extract_equipment(self, text: str) -> List[str]:
        """Extract equipment mentions from text"""
        equipment = []
        for pattern in self.equipment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            equipment.extend(matches)
        return list(set(equipment))  # Remove duplicates
    
    def _extract_equipment_from_step(self, step_text: str) -> Optional[str]:
        """Extract primary equipment for a single step"""
        equipment_list = self._extract_equipment(step_text)
        return equipment_list[0] if equipment_list else None
    
    def _infer_procedure_title(self, text: str, equipment: List[str]) -> Optional[str]:
        """Infer procedure title from context"""
        text_lower = text.lower()
        
        # Look for explicit procedure mentions
        if 'cleaning' in text_lower and equipment:
            return f"{equipment[0].title()} Cleaning Procedure"
        elif 'maintenance' in text_lower and equipment:
            return f"{equipment[0].title()} Maintenance"
        elif 'oil change' in text_lower:
            return "Oil Change Procedure"
        elif 'sanitiz' in text_lower:
            return "Sanitization Procedure"
        
        return None
    
    def _extract_tools(self, text: str) -> List[str]:
        """Extract required tools mentioned in the procedure"""
        tool_patterns = [
            r'\b(brush|scraper|cloth|towel|bucket|container)\b',
            r'\b(degreaser|sanitizer|cleaner|solution|soap)\b',
            r'\b(wrench|screwdriver|pliers|filter)\b'
        ]
        
        tools = []
        for pattern in tool_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tools.extend(matches)
        
        return list(set(tools))
    
    def _extract_warnings(self, step_text: str) -> List[str]:
        """Extract safety warnings from step text"""
        warnings = []
        step_lower = step_text.lower()
        
        if any(keyword in step_lower for keyword in ['hot', 'electrical', 'chemical']):
            warnings.append("Use appropriate safety equipment")
        if 'turn off' in step_lower or 'power off' in step_lower:
            warnings.append("Ensure equipment is powered off before proceeding")
        
        return warnings
    
    def _extract_tips(self, step_text: str) -> List[str]:
        """Extract helpful tips from step text"""
        tips = []
        
        # Simple heuristic - look for sentences with certain patterns
        if 'make sure' in step_text.lower():
            tips.append("Double-check this step for best results")
        if 'allow' in step_text.lower() and ('dry' in step_text.lower() or 'cool' in step_text.lower()):
            tips.append("Allow sufficient time for this step")
        
        return tips
    
    def _estimate_step_duration(self, action_text: str, step_type: Optional[StepType]) -> Optional[str]:
        """Estimate duration for step (simple heuristic)"""
        action_lower = action_text.lower()
        
        # Look for explicit time mentions
        time_match = re.search(r'(\d+)\s*(minute|second|hour)', action_lower)
        if time_match:
            return f"{time_match.group(1)} {time_match.group(2)}{'s' if int(time_match.group(1)) != 1 else ''}"
        
        # Default estimates based on step type
        duration_defaults = {
            StepType.SAFETY: "30 seconds",
            StepType.PREPARATION: "1-2 minutes", 
            StepType.CLEANING: "3-5 minutes",
            StepType.MAINTENANCE: "5-10 minutes",
            StepType.INSPECTION: "1 minute",
            StepType.COMPLETION: "2-3 minutes"
        }
        
        return duration_defaults.get(step_type, "2-3 minutes")
    
    def _assess_safety_level(self, steps: List[StepObject]) -> Optional[str]:
        """Assess overall safety level of the procedure"""
        safety_critical_count = sum(1 for step in steps if step.safety_critical)
        total_steps = len(steps)
        
        if safety_critical_count == 0:
            return "low"
        elif safety_critical_count / total_steps < 0.3:
            return "medium"
        else:
            return "high"

# Global step parser instance
step_parser = StepParser()

def parse_ai_response_steps(ai_response: str) -> ParsedStepsResponse:
    """Convenience function to parse steps from AI response"""
    return step_parser.parse_steps_from_response(ai_response)