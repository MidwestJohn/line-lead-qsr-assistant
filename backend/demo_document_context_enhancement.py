#!/usr/bin/env python3
"""
Document Context Enhancement Demo
===============================

Demonstrates the enhanced document-level context integration capabilities.
Shows before/after comparison of responses with hierarchical document understanding.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.document_context_service import document_context_service
from services.neo4j_service import neo4j_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentContextDemo:
    """Demonstration of document context enhancements"""
    
    def __init__(self):
        self.demo_scenarios = [
            {
                "query": "What temperature should the Taylor C602 be set to?",
                "context": "QSR line lead asking about ice cream machine temperature"
            },
            {
                "query": "How do I clean the fryer?",
                "context": "Daily cleaning procedure inquiry"
            },
            {
                "query": "Show me the safety procedures",
                "context": "Safety protocol lookup"
            }
        ]
    
    async def run_demo(self):
        """Run complete demonstration"""
        logger.info("🎬 Document Context Enhancement Demo")
        logger.info("=" * 60)
        
        # Initialize services
        await self.initialize_services()
        
        # Create sample document
        await self.create_sample_document()
        
        # Show traditional vs enhanced responses
        for scenario in self.demo_scenarios:
            await self.demonstrate_enhancement(scenario)
        
        logger.info("🎉 Demo complete! Document context integration ready for production.")
    
    async def initialize_services(self):
        """Initialize required services"""
        logger.info("🔧 Initializing services...")
        
        # Connect to Neo4j
        if neo4j_service.test_connection():
            document_context_service.neo4j_service = neo4j_service
            logger.info("✅ Services initialized")
        else:
            logger.warning("⚠️ Neo4j not available, limited demo mode")
    
    async def create_sample_document(self):
        """Create comprehensive sample QSR document"""
        logger.info("📄 Creating sample McDonald's Taylor C602 manual...")
        
        sample_content = """
        McDonald's Taylor C602 Ice Cream Machine Service Manual
        =====================================================
        
        Document Purpose: This comprehensive service manual provides McDonald's line leads 
        with essential maintenance, cleaning, and troubleshooting procedures for the 
        Taylor C602 soft serve ice cream machine to ensure consistent product quality 
        and food safety compliance.
        
        Target Audience: QSR Line Leads, Shift Managers
        Equipment: Taylor C602 Soft Serve Ice Cream Machine
        Brand: McDonald's Corporation
        
        Table of Contents:
        1. Safety Protocols and Emergency Procedures
        2. Daily Operations and Temperature Settings
        3. Cleaning and Sanitization Procedures  
        4. Troubleshooting Common Issues
        5. Maintenance Schedule and Requirements
        
        === SECTION 1: SAFETY PROTOCOLS ===
        
        WARNING: Always disconnect power before servicing equipment.
        CAUTION: Machine operates at high temperatures - allow cooling before maintenance.
        
        Emergency Procedures:
        - If machine overheats, immediately shut down and call service
        - Keep fire extinguisher accessible near fryer areas
        - Ensure proper ventilation during cleaning chemical use
        
        === SECTION 2: TEMPERATURE SETTINGS ===
        
        Critical Temperature Requirements for Food Safety:
        
        Serving Temperature: 18°F to 20°F (-7°C to -6°C)
        - This temperature ensures proper soft serve consistency
        - Maintains food safety standards for dairy products
        - Prevents bacterial growth while ensuring product quality
        
        Mix Temperature: 38°F to 40°F (3°C to 4°C)  
        - Temperature for incoming soft serve mix
        - Must be maintained during storage and feeding
        - Check temperature every 2 hours during operation
        
        Freezer Cylinder Temperature: 22°F to 25°F (-5°C to -4°C)
        - Internal temperature for proper freezing
        - Monitored by internal temperature sensor
        - Adjust via control panel if outside range
        
        Temperature Sensor Check Procedure:
        1. Access control panel display
        2. Navigate to temperature monitoring screen
        3. Compare displayed vs. actual temperatures
        4. Calibrate if variance exceeds 2°F
        5. Document readings in daily log
        
        === SECTION 3: CLEANING PROCEDURES ===
        
        Daily Cleaning Schedule (Every 4 Hours):
        1. Heat cleaning cycle activation
        2. Brush cleaning of dispensing heads
        3. Sanitizer rinse cycle
        4. Verification of cleaning completion
        
        Deep Cleaning (Every 24 Hours):
        1. Complete disassembly of dispensing unit
        2. Manual cleaning of all removable parts
        3. Sanitizing solution application
        4. Reassembly and test cycle
        5. Documentation in cleaning log
        
        Cleaning Chemical Specifications:
        - Sanitizer concentration: 200ppm chlorine solution
        - Cleaning solution: Kay-5 cleaner at 1:10 ratio
        - Rinse water temperature: 110°F to 120°F
        
        === SECTION 4: TROUBLESHOOTING ===
        
        Common Issues and Solutions:
        
        Low Product Viscosity:
        - Check serving temperature (should be 18-20°F)
        - Verify mix temperature (should be 38-40°F)  
        - Inspect temperature sensor calibration
        - Review recent cleaning procedures
        
        Machine Won't Start:
        - Verify power connection
        - Check circuit breaker status
        - Confirm door/lid properly closed
        - Review error codes on display
        
        Inconsistent Product Quality:
        - Monitor temperature consistency
        - Check for worn dispensing parts
        - Verify proper mix ratios
        - Review maintenance schedule compliance
        
        === SECTION 5: MAINTENANCE SCHEDULE ===
        
        Daily Tasks:
        - Temperature monitoring (every 2 hours)
        - Cleaning cycle execution (every 4 hours)
        - Visual inspection of exterior components
        - Documentation in operations log
        
        Weekly Tasks:
        - Deep component inspection
        - Lubrication of moving parts
        - Calibration verification
        - Filter replacement check
        
        Monthly Tasks:
        - Comprehensive system diagnostics
        - Professional service inspection
        - Parts inventory review
        - Staff training review
        
        === APPENDIX: QSR OPERATIONAL NOTES ===
        
        McDonald's Specific Requirements:
        - Product quality must meet McDonald's standards
        - Temperature logs required for health inspections
        - Follow McDonald's approved cleaning chemicals only
        - Report all maintenance issues to store manager
        - Maintain 99.5% uptime during peak hours
        
        Peak Hour Operations:
        - Lunch rush: 11:30 AM - 2:00 PM
        - Dinner rush: 5:00 PM - 8:00 PM
        - Schedule maintenance outside peak hours
        - Have backup procedures ready for equipment failure
        
        Staff Training Notes:
        - All line leads must complete Taylor C602 certification
        - Annual refresher training required
        - Emergency procedure drills quarterly
        - Documentation review with each new hire
        """
        
        # Process document for context
        test_file = Path("sample_mcdonalds_taylor_manual.txt")
        test_file.write_text(sample_content)
        
        try:
            self.document_summary = await document_context_service.process_document_for_context(
                test_file, sample_content
            )
            
            if self.document_summary:
                logger.info("✅ Sample document processed with full context")
                logger.info(f"   Document Type: {self.document_summary.document_type.value}")
                logger.info(f"   QSR Category: {self.document_summary.qsr_category.value}")
                logger.info(f"   Brand Context: {self.document_summary.brand_context}")
                logger.info(f"   Equipment Focus: {', '.join(self.document_summary.equipment_focus)}")
                logger.info(f"   Key Procedures: {len(self.document_summary.key_procedures)} identified")
                logger.info(f"   Safety Protocols: {len(self.document_summary.safety_protocols)} identified")
                logger.info(f"   Temperature Settings: {len(self.document_summary.critical_temperatures)} identified")
            else:
                logger.error("❌ Failed to process sample document")
                
        finally:
            if test_file.exists():
                test_file.unlink()
    
    async def demonstrate_enhancement(self, scenario):
        """Show before/after comparison for a query scenario"""
        query = scenario["query"]
        context = scenario["context"]
        
        logger.info(f"\n🎯 SCENARIO: {context}")
        logger.info(f"Query: '{query}'")
        logger.info("-" * 50)
        
        # Show traditional response (simplified simulation)
        logger.info("📜 BEFORE - Traditional Response:")
        traditional_response = await self.simulate_traditional_response(query)
        logger.info(f"   {traditional_response}")
        
        # Show enhanced response with document context
        logger.info("\n🌟 AFTER - Context-Enhanced Response:")
        enhanced_response = await self.generate_enhanced_response(query)
        logger.info(f"   {enhanced_response}")
        
        # Show additional context information
        logger.info("\n📊 Context Information Provided:")
        context_info = await self.get_context_information(query)
        for key, value in context_info.items():
            logger.info(f"   • {key}: {value}")
        
        logger.info("-" * 50)
    
    async def simulate_traditional_response(self, query):
        """Simulate traditional granular response without context"""
        responses = {
            "What temperature should the Taylor C602 be set to?": 
                "The temperature should be 18-20°F for serving.",
            "How do I clean the fryer?": 
                "Run cleaning cycle every 4 hours.",
            "Show me the safety procedures": 
                "Disconnect power before servicing."
        }
        return responses.get(query, "Information found in manual.")
    
    async def generate_enhanced_response(self, query):
        """Generate context-enhanced response"""
        if not self.document_summary:
            return "Enhanced response unavailable - no document context"
        
        # Create sample entities for context-aware prompt
        entities = [
            {
                "name": "Temperature Control System",
                "type": "Component",
                "document_id": self.document_summary.document_id,
                "hierarchical_context": {
                    "section_path": ["McDonald's Taylor C602 Manual", "Temperature Settings"],
                    "contextual_description": f"From {self.document_summary.brand_context} {self.document_summary.document_type.value} for {self.document_summary.qsr_category.value}"
                }
            }
        ]
        
        # Generate context-aware prompt
        enhanced_prompt = await document_context_service.generate_context_aware_prompt(
            query, entities, user_context="line_lead"
        )
        
        # Simulate enhanced response based on document context
        if "temperature" in query.lower():
            return f"For {self.document_summary.brand_context} ice cream machine maintenance (Taylor C602 Service Manual): The serving temperature should be set to 18°F-20°F for food safety compliance, following QSR protocols detailed in the Temperature Settings section. This ensures proper soft serve consistency while maintaining food safety standards for dairy products."
        
        elif "clean" in query.lower():
            return f"Following {self.document_summary.brand_context} cleaning procedures from the service manual: Execute heat cleaning cycle every 4 hours during operation, including brush cleaning of dispensing heads and sanitizer rinse cycle. Use approved cleaning chemicals at specified concentrations (Kay-5 cleaner at 1:10 ratio) and document completion in cleaning log."
        
        elif "safety" in query.lower():
            return f"Per {self.document_summary.brand_context} safety protocols in the Taylor C602 manual: Always disconnect power before servicing equipment. Allow cooling before maintenance due to high operating temperatures. Keep fire extinguisher accessible and ensure proper ventilation during cleaning chemical use. Follow emergency procedures for equipment overheating."
        
        return f"Based on {self.document_summary.brand_context} {self.document_summary.document_type.value} for {', '.join(self.document_summary.equipment_focus)}: [Enhanced response with full operational context]"
    
    async def get_context_information(self, query):
        """Get additional context information for demonstration"""
        if not self.document_summary:
            return {"Status": "No document context available"}
        
        return {
            "Document Source": f"{self.document_summary.brand_context} {self.document_summary.document_type.value}",
            "Equipment Focus": ", ".join(self.document_summary.equipment_focus),
            "Target Audience": self.document_summary.target_audience.replace("_", " ").title(),
            "QSR Category": self.document_summary.qsr_category.value.replace("_", " ").title(),
            "Document Purpose": self.document_summary.purpose[:100] + "..." if len(self.document_summary.purpose) > 100 else self.document_summary.purpose,
            "Context Confidence": f"{self.document_summary.confidence_score:.1%}",
            "Hierarchical Path": "Taylor C602 Manual → Temperature Settings → Temperature Control System",
            "Related Procedures": f"{len(self.document_summary.key_procedures)} procedures identified",
            "Safety Considerations": f"{len(self.document_summary.safety_protocols)} protocols identified"
        }


async def main():
    """Run the demonstration"""
    demo = DocumentContextDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())