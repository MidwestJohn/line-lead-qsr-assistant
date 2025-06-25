#!/usr/bin/env python3

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_test_manual():
    """Create a test equipment manual PDF"""
    filename = "test_fryer_manual.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "COMMERCIAL FRYER MANUAL")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, "Model: QSR-FRYER-2000")
    c.drawString(50, height - 120, "Installation and Maintenance Guide")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 160, "Common Issues and Solutions:")
    
    c.setFont("Helvetica", 11)
    issues = [
        "Problem: Fryer won't heat oil",
        "Solution: Check power connection, inspect heating elements, verify thermostat settings.",
        "If heating elements are damaged, replace immediately.",
        "",
        "Problem: Oil temperature fluctuates",
        "Solution: Clean temperature sensor, check for blockages in oil circulation.",
        "",
        "Problem: Strange noises during operation",
        "Solution: Check oil level, inspect fan motor, lubricate moving parts.",
        "",
        "Cleaning Procedures:",
        "1. Turn off power and allow oil to cool completely",
        "2. Drain oil using proper disposal methods",
        "3. Remove heating elements and clean with degreaser",
        "4. Wipe down interior surfaces with sanitizing solution",
        "5. Replace oil filter and refill with fresh oil"
    ]
    
    y_pos = height - 200
    for issue in issues:
        c.drawString(50, y_pos, issue)
        y_pos -= 20
        if y_pos < 100:  # Start new page
            c.showPage()
            y_pos = height - 50
    
    # Page 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Maintenance Schedule:")
    
    c.setFont("Helvetica", 11)
    maintenance = [
        "Daily:",
        "- Check oil level and quality",
        "- Clean exterior surfaces",
        "- Test temperature controls",
        "",
        "Weekly:", 
        "- Deep clean oil reservoir",
        "- Inspect heating elements",
        "- Check safety systems",
        "",
        "Monthly:",
        "- Replace oil filter",
        "- Calibrate temperature sensors",
        "- Inspect electrical connections",
        "",
        "Emergency Contacts:",
        "Service Hotline: 1-800-FRYER-HELP",
        "Parts Department: 1-800-PARTS-QSR"
    ]
    
    y_pos = height - 100
    for item in maintenance:
        c.drawString(50, y_pos, item)
        y_pos -= 20
    
    c.save()
    print(f"Created test manual: {filename}")
    return filename

if __name__ == "__main__":
    create_test_manual()