#!/usr/bin/env python3
"""
Test Script for Step Parsing System
Verifies step extraction and data structure for future Playbooks UX
"""

import sys
import os
sys.path.append('backend')

from step_parser import parse_ai_response_steps
import json

def test_step_parsing():
    """Test step parsing with sample AI responses"""
    
    # Test case 1: Fryer cleaning procedure
    fryer_response = """
    For the fryer, start by turning off the power and letting it cool completely. Here are the cleaning steps:
    
    Step 1, Turn off the fryer and let it cool down completely for safety.
    
    Step 2, Drain the oil into a safe container for proper disposal.
    
    Step 3, Remove the heating elements and scrub them with a degreaser.
    
    Step 4, Clean the interior surfaces with warm soapy water and rinse thoroughly.
    
    Step 5, Wipe down all surfaces with a sanitizing solution and let air dry.
    
    Step 6, Replace the oil filter and refill with fresh oil before testing.
    
    Need help with any of these steps?
    """
    
    # Test case 2: Ice machine maintenance
    ice_machine_response = """
    For ice machine maintenance, follow these steps:
    
    Step 1, Turn off power and disconnect the water supply.
    Step 2, Remove all ice and clean the ice bin with sanitizer.
    Step 3, Check and clean the water filter.
    Step 4, Inspect the condenser coils for dust buildup.
    Step 5, Reconnect everything and run a test cycle.
    """
    
    # Test case 3: Simple response without steps
    simple_response = """
    The ice cream machine should be cleaned daily. Make sure to turn it off first and use approved sanitizers.
    """
    
    test_cases = [
        ("Fryer Cleaning", fryer_response),
        ("Ice Machine Maintenance", ice_machine_response),
        ("Simple Response", simple_response)
    ]
    
    print("🧪 STEP PARSING TEST RESULTS")
    print("=" * 50)
    
    for test_name, response_text in test_cases:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        # Parse the response
        parsed = parse_ai_response_steps(response_text)
        
        print(f"Has Steps: {parsed.has_steps}")
        print(f"Total Steps: {parsed.total_steps}")
        print(f"Procedure: {parsed.procedure_title}")
        print(f"Equipment: {', '.join(parsed.equipment_involved) if parsed.equipment_involved else 'None'}")
        print(f"Safety Level: {parsed.safety_level}")
        print(f"Required Tools: {', '.join(parsed.required_tools) if parsed.required_tools else 'None'}")
        
        if parsed.has_steps:
            print("\nDetailed Steps:")
            for step in parsed.steps:
                print(f"  {step.step_number}. {step.action_description}")
                print(f"     Type: {step.step_type}")
                print(f"     Duration: {step.estimated_duration}")
                print(f"     Safety Critical: {step.safety_critical}")
                if step.warnings:
                    print(f"     Warnings: {', '.join(step.warnings)}")
                print()
        
        # Show JSON structure for future API integration
        if parsed.has_steps:
            print("📄 JSON Structure (sample):")
            sample_step = parsed.steps[0].model_dump() if parsed.steps else {}
            print(json.dumps(sample_step, indent=2))
        
        print("\n" + "="*50)

if __name__ == "__main__":
    test_step_parsing()