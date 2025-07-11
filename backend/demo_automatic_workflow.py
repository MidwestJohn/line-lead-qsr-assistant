#!/usr/bin/env python3
"""
Automatic LightRAG → Neo4j Bridge Demo
======================================

Demonstrates the seamless automatic workflow:
User drags PDF → Everything happens automatically → Graph ready for queries

This replaces the 3-step manual process with background automation.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Demo configuration
BACKEND_URL = "http://localhost:8000"
DEMO_PDF_PATH = "demo_qsr_manual.pdf"

def create_demo_pdf():
    """Create a demo QSR manual PDF for testing"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        
        # Create demo PDF content
        pdf_path = DEMO_PDF_PATH
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Page 1: Equipment Overview
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*inch, height-1*inch, "QSR Equipment Manual - Demo")
        
        c.setFont("Helvetica", 12)
        content = [
            "",
            "TAYLOR C602 ICE CREAM MACHINE",
            "",
            "The Taylor C602 is a commercial soft-serve ice cream machine designed for high-volume",
            "restaurant operations. This equipment features a dual-flavor system with mix pump,",
            "compressor, and electronic control panel.",
            "",
            "MAIN COMPONENTS:",
            "• Compressor - Primary cooling system",
            "• Mix Pump - Circulates ice cream mixture",
            "• Control Panel - Digital temperature and consistency controls",
            "• Freezing Cylinder - Where mixture becomes ice cream",
            "• Temperature Sensor - Monitors freezing temperature",
            "",
            "DAILY CLEANING PROCEDURE:",
            "1. Turn off machine and allow to cool completely",
            "2. Remove all mix from the cylinders",
            "3. Remove and disassemble mix pump components", 
            "4. Wash all removable parts with warm soapy water",
            "5. Sanitize all parts with approved sanitizer solution",
            "6. Reassemble components and run cleaning cycle",
            "",
            "SAFETY WARNINGS:",
            "• Always wear safety gloves when handling hot components",
            "• Ensure proper ventilation when using cleaning chemicals",
            "• Never operate machine without proper grounding",
            "• Temperature control settings must be maintained between 18-22°F",
            "",
            "WEEKLY MAINTENANCE:",
            "• Deep clean all internal components",
            "• Check compressor oil levels",
            "• Inspect electrical connections",
            "• Test safety shut-off systems",
            "• Calibrate temperature sensors"
        ]
        
        y_position = height - 2*inch
        for line in content:
            c.drawString(1*inch, y_position, line)
            y_position -= 0.3*inch
            if y_position < 1*inch:
                c.showPage()
                y_position = height - 1*inch
        
        c.save()
        print(f"✅ Created demo PDF: {pdf_path}")
        return pdf_path
        
    except ImportError:
        print("⚠️ ReportLab not available, using text file as demo")
        # Create a simple text file as fallback
        with open("demo_qsr_manual.txt", "w") as f:
            f.write("""QSR Equipment Manual - Demo

TAYLOR C602 ICE CREAM MACHINE

The Taylor C602 is a commercial soft-serve ice cream machine designed for high-volume restaurant operations.

MAIN COMPONENTS:
- Compressor: Primary cooling system
- Mix Pump: Circulates ice cream mixture  
- Control Panel: Digital temperature controls
- Temperature Sensor: Monitors freezing temperature

DAILY CLEANING PROCEDURE:
1. Turn off machine and cool completely
2. Remove mix from cylinders
3. Disassemble mix pump components
4. Wash with warm soapy water
5. Sanitize with approved solution
6. Reassemble and run cleaning cycle

SAFETY WARNINGS:
- Always wear safety gloves
- Ensure proper ventilation
- Maintain temperature 18-22°F
- Never operate without grounding

WEEKLY MAINTENANCE:
- Deep clean internal components
- Check compressor oil levels
- Inspect electrical connections
- Test safety systems""")
        return "demo_qsr_manual.txt"

async def demo_automatic_upload():
    """Demonstrate the automatic upload and processing workflow"""
    
    print("🎯 AUTOMATIC LIGHTRAG → NEO4J BRIDGE DEMO")
    print("=" * 60)
    
    # Step 1: Create demo content
    print("\n📄 Step 1: Preparing demo QSR manual...")
    demo_file = create_demo_pdf()
    
    if not Path(demo_file).exists():
        print(f"❌ Demo file not created: {demo_file}")
        return
    
    # Step 2: Upload with automatic processing
    print(f"\n🚀 Step 2: Uploading {demo_file} with automatic processing...")
    
    try:
        with open(demo_file, 'rb') as f:
            files = {'file': (demo_file, f, 'application/pdf')}
            
            # Use the enhanced upload endpoint
            upload_response = requests.post(
                f"{BACKEND_URL}/api/v2/upload-automatic",
                files=files,
                timeout=30
            )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(upload_response.text)
            return
        
        upload_result = upload_response.json()
        process_id = upload_result["process_id"]
        
        print(f"✅ Upload successful! Automatic processing started.")
        print(f"📋 Process ID: {process_id}")
        print(f"📊 Estimated completion: {upload_result.get('estimated_completion_time', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Step 3: Monitor progress in real-time
    print(f"\n📊 Step 3: Monitoring automatic processing progress...")
    print("=" * 50)
    
    start_time = time.time()
    last_stage = ""
    
    while True:
        try:
            # Get current status
            status_response = requests.get(
                f"{BACKEND_URL}/api/v2/processing-status/{process_id}",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                
                current_stage = status["stage"]
                progress = status["progress_percent"]
                operation = status["current_operation"]
                
                # Show progress update if stage changed
                if current_stage != last_stage:
                    elapsed = time.time() - start_time
                    print(f"\n🔄 [{elapsed:.1f}s] Stage: {current_stage.upper()}")
                    print(f"   Operation: {operation}")
                    last_stage = current_stage
                
                # Show live progress
                print(f"\r   Progress: {progress:.1f}% | Entities: {status['entities_extracted']} | Relationships: {status['relationships_extracted']}", end="", flush=True)
                
                # Check if completed or failed
                if status["completed"]:
                    print(f"\n✅ Processing completed successfully!")
                    print(f"📈 Final Results:")
                    print(f"   - Entities bridged: {status['entities_bridged']}")
                    print(f"   - Relationships bridged: {status['relationships_bridged']}")
                    print(f"   - Total time: {status['total_duration_seconds']:.1f} seconds")
                    print(f"   - Graph ready: {status['graph_ready']}")
                    break
                    
                elif status["failed"]:
                    print(f"\n❌ Processing failed!")
                    print(f"   - Errors: {status['errors_count']}")
                    print(f"   - Stage failed: {current_stage}")
                    break
                
                # Continue monitoring
                await asyncio.sleep(2)
                
            else:
                print(f"\n⚠️ Status check failed: {status_response.status_code}")
                break
                
        except Exception as e:
            print(f"\n⚠️ Monitoring error: {e}")
            break
    
    # Step 4: Get final results
    print(f"\n📋 Step 4: Getting final processing results...")
    
    try:
        result_response = requests.get(
            f"{BACKEND_URL}/api/v2/processing-result/{process_id}",
            timeout=10
        )
        
        if result_response.status_code == 200:
            result = result_response.json()
            
            print(f"🎉 AUTOMATIC PROCESSING COMPLETE!")
            print("=" * 50)
            print(f"✅ Success: {result['success']}")
            print(f"📁 File: {result['filename']}")
            print(f"📊 Total entities: {result['total_entities']}")
            print(f"📊 Total relationships: {result['total_relationships']}")
            print(f"⏱️  Processing time: {result['processing_time_seconds']:.1f} seconds")
            print(f"🔗 Graph ready: {result['graph_ready']}")
            
            if not result['success']:
                print(f"\n❌ Error details:")
                error_details = result.get('error_details', {})
                for error in error_details.get('errors', []):
                    print(f"   - {error}")
        else:
            print(f"❌ Could not get final results: {result_response.status_code}")
            
    except Exception as e:
        print(f"❌ Results check failed: {e}")
    
    # Step 5: Verify Neo4j population
    print(f"\n🔍 Step 5: Verifying Neo4j graph population...")
    
    try:
        neo4j_response = requests.get(f"{BACKEND_URL}/neo4j-stats", timeout=10)
        
        if neo4j_response.status_code == 200:
            neo4j_stats = neo4j_response.json()
            
            print(f"📈 Neo4j Graph Status:")
            print(f"   - Total nodes: {neo4j_stats.get('total_nodes', 0)}")
            print(f"   - Total relationships: {neo4j_stats.get('total_relationships', 0)}")
            print(f"   - Node types: {len(neo4j_stats.get('node_types', {}))}")
            
            # Show node type distribution
            node_types = neo4j_stats.get('node_types', {})
            if node_types:
                print(f"\n📊 Node Type Distribution:")
                for node_type, count in list(node_types.items())[:5]:
                    print(f"   - {node_type}: {count}")
        else:
            print(f"⚠️ Could not verify Neo4j status: {neo4j_response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Neo4j verification failed: {e}")
    
    # Step 6: Test query capabilities
    print(f"\n🔍 Step 6: Testing query capabilities...")
    
    try:
        # Test a simple chat query to see if the graph is queryable
        chat_response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"message": "Tell me about the Taylor ice cream machine cleaning procedure"},
            timeout=15
        )
        
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            print(f"✅ Query test successful!")
            print(f"📝 Response preview: {chat_result['response'][:200]}...")
            
            # Check if parsed steps are available
            if chat_result.get('parsed_steps'):
                steps = chat_result['parsed_steps']
                print(f"📋 Structured steps detected: {steps.get('total_steps', 0)} steps")
        else:
            print(f"⚠️ Query test failed: {chat_response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Query test failed: {e}")
    
    print(f"\n🎉 DEMO COMPLETE!")
    print("=" * 60)
    print("USER EXPERIENCE ACHIEVED:")
    print("✅ User drags PDF → Everything automatic → Graph ready for queries")
    print("")
    print("MANUAL PROCESS ELIMINATED:")
    print("❌ Manual extraction scripts")
    print("❌ Manual bridging commands") 
    print("❌ Manual verification steps")
    print("✅ One-click upload with automatic processing")
    
    # Cleanup
    try:
        Path(demo_file).unlink(missing_ok=True)
        print(f"\n🧹 Cleaned up demo file: {demo_file}")
    except:
        pass

def demo_active_processes():
    """Show all currently active automatic processes"""
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v2/active-processes", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 ACTIVE AUTOMATIC PROCESSES")
            print("=" * 40)
            print(f"Total active: {data['active_process_count']}")
            
            summary = data['summary']
            print(f"Initializing: {summary['initializing']}")
            print(f"Processing: {summary['processing']}")
            print(f"Completed: {summary['completed']}")
            print(f"Failed: {summary['failed']}")
            
            if data['processes']:
                print(f"\nProcess Details:")
                for process_id, status in data['processes'].items():
                    print(f"  {process_id[:20]}... | {status['stage']} | {status['progress_percent']:.1f}%")
        else:
            print(f"Could not get active processes: {response.status_code}")
            
    except Exception as e:
        print(f"Active processes check failed: {e}")

async def main():
    """Main demo function"""
    
    print("🎯 AUTOMATIC LIGHTRAG → NEO4J BRIDGE DEMONSTRATION")
    print("This demo shows how the 3-step manual process becomes seamless automation")
    print("")
    
    # Check if backend is running
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Backend not accessible at {BACKEND_URL}")
            return
    except:
        print(f"❌ Backend not running at {BACKEND_URL}")
        print("Please start the backend with: uvicorn main:app --reload")
        return
    
    # Show active processes first
    demo_active_processes()
    
    # Run the complete automatic workflow demo
    await demo_automatic_upload()

if __name__ == "__main__":
    asyncio.run(main())