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
            r"show\s+me\s+(?:an?\s+)?(?:image|diagram|picture|photo)",
            r"display\s+(?:an?\s+)?(?:image|diagram|picture|photo)",
            r"picture\s+of",
            r"diagram\s+of",
            r"photo\s+of",
            r"visual\s+of",
            r"see\s+(?:an?\s+)?(?:image|diagram|picture|photo)",
            r"view\s+(?:an?\s+)?(?:image|diagram|picture|photo)",
            r"show\s+me\s+(?:a|the)?\s*diagram",
            r"display\s+(?:a|the)?\s*diagram",
            r"what\s+does\s+(?:it|this|that)\s+look\s+like",
            r"(?:the\s+)?image",
            r"(?:the\s+)?diagram",
            r"(?:the\s+)?picture"
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
    
    def generate_image_response(self, equipment_name: str, document_results: List[Dict] = None) -> Dict[str, Any]:
        """Generate appropriate response for image requests with actual image display"""
        
        # Search for matching images in the document library
        matching_images = []
        if document_results:
            for doc in document_results:
                if doc.get('name', '').lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    # Check if image matches equipment
                    if equipment_name and equipment_name.lower() in doc.get('name', '').lower():
                        matching_images.append(doc)
        
        # If we have matching images, show them
        if matching_images:
            primary_image = matching_images[0]
            
            # Format response to work with visual citations
            image_display = f"""I found an image of the {equipment_name or 'equipment'} for you!

**Equipment Image Available:**
- {primary_image.get('name', 'Equipment Image')}
- The image will be displayed below with zoom/pan controls
- Use the image viewer to see component details"""
            
            additional_images = ""
            if len(matching_images) > 1:
                additional_images = f"\n\n**Additional images available:** {len(matching_images) - 1} more images in the results"
            
            return {
                "response": f"""{image_display}{additional_images}

**About the {equipment_name or 'equipment'}:**
- Review the image(s) for visual reference
- Use zoom controls to see details
- Check component locations and connections

**Need more help with this equipment?**
- Operating procedures
- Troubleshooting steps  
- Maintenance guidance
- Technical specifications

What specific information do you need about this equipment?""",
                "equipment_context": equipment_name,
                "image_request": True,
                "image_results": matching_images,
                "suggestions": [
                    "Operating procedures",
                    "Troubleshooting guide", 
                    "Maintenance checklist",
                    "Technical specifications"
                ]
            }
        
        # If no matching images found, offer to search
        if equipment_name and "baxter" in equipment_name.lower():
            return {
                "response": f"""I'm searching for an image of the {equipment_name}...

**About the Baxter OV520E1:**
- Single rack rotating oven
- Electric operation
- Commercial-grade QSR equipment
- Known for even heat distribution

Let me check our equipment documentation for visual diagrams. In the meantime, I can help with:

**What specific information about the {equipment_name} do you need?**
- Operating procedures
- Troubleshooting steps
- Maintenance schedule
- Technical specifications

I'll search for any available images or diagrams in our system.""",
                "equipment_context": equipment_name,
                "image_request": True,
                "search_needed": True,
                "suggestions": [
                    "Operating procedures",
                    "Troubleshooting guide", 
                    "Maintenance checklist",
                    "Technical specifications"
                ]
            }
        else:
            return {
                "response": f"""I'm searching for an image of {equipment_name or 'that equipment'}...

Let me check our equipment documentation for visual references. I can help with:

**Equipment information:**
- Operating procedures
- Troubleshooting steps
- Maintenance guidance
- Technical specifications

What specific information do you need about this equipment?""",
                "equipment_context": equipment_name,
                "image_request": True,
                "search_needed": True
            }

# Global instance
image_request_handler = ImageRequestHandler()