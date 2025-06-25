#!/usr/bin/env python3

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_grill_manual():
    """Create a test grill manual PDF"""
    filename = "test_grill_manual.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "COMMERCIAL GRILL MAINTENANCE MANUAL")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, "Model: QSR-GRILL-3000")
    c.drawString(50, height - 120, "Professional Cleaning and Maintenance Guide")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 160, "Grill Cleaning Procedures:")
    
    c.setFont("Helvetica", 11)
    procedures = [
        "Daily Cleaning (End of Service):",
        "1. Turn off grill and allow to cool to safe temperature",
        "2. Remove cooking grates and drip pans",
        "3. Scrape grease and food debris from cooking surface",
        "4. Clean grates with grill brush and degreasing solution",
        "5. Wipe down exterior surfaces with sanitizing solution",
        "",
        "Deep Cleaning (Weekly):",
        "1. Remove all internal components (grates, heat tents, etc.)",
        "2. Soak removable parts in degreasing solution",
        "3. Clean interior walls with approved cleaning agents",
        "4. Inspect and clean gas burners",
        "5. Check gas connections for leaks",
        "6. Clean grease collection system thoroughly",
        "",
        "Temperature Issues:",
        "Problem: Grill won't reach desired temperature",
        "Solution: Check gas supply, clean burner orifices, verify thermostat calibration",
        "",
        "Problem: Uneven heating across cooking surface",
        "Solution: Clean heat distribution system, check for blocked vents"
    ]
    
    y_pos = height - 200
    for procedure in procedures:
        c.drawString(50, y_pos, procedure)
        y_pos -= 20
        if y_pos < 100:  # Start new page
            c.showPage()
            y_pos = height - 50
    
    # Add maintenance schedule
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Maintenance Schedule:")
    
    c.setFont("Helvetica", 11)
    schedule = [
        "After Each Use:",
        "- Scrape cooking surface",
        "- Empty grease tray",
        "- Check for any visible damage",
        "",
        "Daily:",
        "- Deep clean cooking grates",
        "- Sanitize all surfaces",
        "- Check gas connections",
        "",
        "Weekly:",
        "- Complete disassembly and cleaning",
        "- Inspect all components",
        "- Test safety systems",
        "",
        "Safety Reminders:",
        "- Always ensure gas is turned off before cleaning",
        "- Use only approved cleaning chemicals",
        "- Wear protective equipment when handling degreasers",
        "- Never use water on hot surfaces"
    ]
    
    y_pos = height - 100
    for item in schedule:
        c.drawString(50, y_pos, item)
        y_pos -= 20
    
    c.save()
    print(f"Created grill manual: {filename}")
    return filename

if __name__ == "__main__":
    create_grill_manual()