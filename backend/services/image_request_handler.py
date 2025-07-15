"""
Image Request Handler for QSR Assistant
Handles requests for equipment images and diagrams
"""

import re
from typing import Optional, Dict, Any, List

class ImageRequestHandler:
    """Detects and handles requests for equipment images and diagrams"""
    
    def __init__(self):
        self.image_request_patterns = [
            r"show\s+me\s+(?:an?\s+)?image",
            r"display\s+(?:an?\s+)?image",
            r"picture\s+of",
            r"diagram\s+of",
            r"photo\s+of",
            r"visual\s+of",
            r"see\s+(?:an?\s+)?image",
            r"view\s+(?:an?\s+)?image"
        ]
        
        self.equipment_patterns = [
            r"baxter\s+ov520e1",
            r"ov520e1",
            r"baxter.*oven",
            r"rotating.*rack.*oven",
            r"single.*rack.*oven"
        ]
    
    def is_image_request(self, message: str) -> bool:
        """Check if the message is requesting an image"""
        message_lower = message.lower()
        
        for pattern in self.image_request_patterns:
            if re.search(pattern, message_lower):
                return True
        return False
    
    def extract_equipment_name(self, message: str) -> Optional[str]:
        """Extract equipment name from the message"""
        message_lower = message.lower()
        
        # Check for specific equipment patterns
        for pattern in self.equipment_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if "baxter" in match.group() or "ov520e1" in match.group():
                    return "Baxter OV520E1"
        
        # Generic equipment extraction
        # Look for model numbers or equipment names
        model_pattern = r"([A-Z]+\d+[A-Z]*\d*)"
        match = re.search(model_pattern, message)
        if match:
            return match.group(1)
        
        return None
    
    def generate_image_response(self, equipment_name: str) -> Dict[str, Any]:
        """Generate appropriate response for image requests"""
        
        if equipment_name and "baxter" in equipment_name.lower():
            return {
                "response": f"""I understand you're looking for an image of the {equipment_name}. While I can't display images directly in this chat, I can help you with:

**About the Baxter OV520E1:**
- Single rack rotating oven
- Electric operation
- Commercial-grade QSR equipment
- Known for even heat distribution

**To find the diagram:**
- Check your equipment documentation folder
- Look for maintenance manuals
- Contact your equipment supplier
- The electric diagram should show wiring and component layout

**What specific information about the {equipment_name} do you need?**
- Operating procedures?
- Troubleshooting steps?
- Maintenance schedule?
- Technical specifications?

Let me know how I can help with the technical details!""",
                "equipment_context": equipment_name,
                "image_request": True,
                "suggestions": [
                    "Operating procedures",
                    "Troubleshooting guide", 
                    "Maintenance checklist",
                    "Technical specifications"
                ]
            }
        else:
            return {
                "response": f"""I understand you're looking for an image of {equipment_name or 'that equipment'}. While I can't display images directly, I can help with:

**For equipment visuals:**
- Check your equipment documentation
- Look in maintenance manuals  
- Contact your equipment supplier

**How else can I help?**
- Operating procedures
- Troubleshooting steps
- Maintenance guidance
- Technical specifications

What specific information do you need about this equipment?""",
                "equipment_context": equipment_name,
                "image_request": True
            }

# Global instance
image_request_handler = ImageRequestHandler()