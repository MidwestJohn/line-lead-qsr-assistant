#!/usr/bin/env python3
"""
Create a test document for semantic Neo4j integration testing.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_semantic_test_pdf():
    """Create a test PDF with QSR equipment content for semantic relationship testing."""
    
    filename = "semantic_test_manual.pdf"
    filepath = os.path.join("uploaded_docs", filename)
    
    # Ensure directory exists
    os.makedirs("uploaded_docs", exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Taylor C602 Ice Cream Machine - Semantic Test Manual")
    
    # Equipment Section
    y_position = height - 100
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "Equipment Overview")
    y_position -= 30
    
    c.setFont("Helvetica", 12)
    content = [
        "The Taylor C602 is a commercial ice cream machine designed for high-volume production.",
        "This equipment contains several critical components that require regular maintenance.",
        "",
        "Main Components:",
        "• Compressor: The main compressor provides cooling and refrigeration",
        "• Mix Pump: The mix pump circulates ice cream mixture through the system", 
        "• Control Panel: The control panel governs all machine operations",
        "• Temperature Sensor: Temperature sensor monitors freezing temperature",
        "",
        "Daily Cleaning Procedure:",
        "1. Turn off the Taylor C602 machine at the control panel",
        "2. Remove all ice cream mixture from the compressor area",
        "3. Clean the mix pump with sanitizing solution",
        "4. Check temperature control settings",
        "",
        "Safety Guidelines:",
        "• Warning: Never operate equipment without proper safety training",
        "• Caution: The compressor contains refrigerant under high pressure",
        "• Safety protocol requires protective equipment when servicing",
        "",
        "Temperature Parameters:",
        "• Freezing temperature: -5°F to -10°F",
        "• Mix temperature: 36°F to 38°F", 
        "• Service temperature: Room temperature for maintenance",
        "",
        "Maintenance Schedule:",
        "• Daily cleaning procedure must be performed after each shift",
        "• Weekly maintenance requires compressor inspection",
        "• Monthly service includes temperature sensor calibration"
    ]
    
    for line in content:
        if y_position < 100:
            c.showPage()
            y_position = height - 50
        
        if line.startswith("•"):
            c.drawString(70, y_position, line)
        elif line.startswith(("1.", "2.", "3.", "4.")):
            c.drawString(70, y_position, line)
        elif line.endswith(":"):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, line)
            c.setFont("Helvetica", 12)
        else:
            c.drawString(50, y_position, line)
        
        y_position -= 20
    
    c.save()
    print(f"✅ Created semantic test PDF: {filepath}")
    return filepath

if __name__ == "__main__":
    create_semantic_test_pdf()