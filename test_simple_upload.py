#!/usr/bin/env python3

"""
Test the simple upload system to verify it works reliably.
"""

import requests
import time
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf():
    """Create a simple test PDF for upload."""
    
    # Create PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add some QSR-related content
    p.drawString(100, 750, "QSR Test Manual")
    p.drawString(100, 720, "Temperature Control Guide")
    p.drawString(100, 690, "Keep refrigeration at 32-40°F")
    p.drawString(100, 660, "Clean equipment after each shift")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer.getvalue()

def test_simple_upload():
    """Test the simple upload system."""
    
    print("🧪 Testing Simple Upload System")
    print("=" * 50)
    
    # Create test PDF
    print("📄 Creating test PDF...")
    pdf_content = create_test_pdf()
    
    # Upload the file
    print("📤 Uploading to simple system...")
    
    files = {
        'file': ('test_qsr_guide.pdf', pdf_content, 'application/pdf')
    }
    
    try:
        upload_response = requests.post(
            "http://localhost:8001/simple-upload",
            files=files,
            timeout=10
        )
        
        print(f"📡 Upload Response Status: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            response_data = upload_response.json()
            print(f"✅ Upload successful!")
            print(f"   Process ID: {response_data.get('process_id')}")
            print(f"   Filename: {response_data.get('filename')}")
            print(f"   Progress Endpoint: {response_data.get('progress_endpoint')}")
            
            process_id = response_data.get('process_id')
            
            if process_id:
                # Monitor progress via HTTP
                print(f"📊 Monitoring progress...")
                
                for attempt in range(10):  # Monitor for 30 seconds
                    time.sleep(3)
                    
                    try:
                        progress_response = requests.get(
                            f"http://localhost:8001/simple-progress/{process_id}",
                            timeout=5
                        )
                        
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            
                            print(f"🔍 Attempt {attempt + 1}:")
                            print(f"   Success: {progress_data.get('success')}")
                            print(f"   Status: {progress_data.get('status', 'unknown')}")
                            
                            if 'progress' in progress_data:
                                progress = progress_data['progress']
                                print(f"   Stage: {progress.get('stage')}")
                                print(f"   Progress: {progress.get('progress_percent', 0)}%")
                                print(f"   Message: {progress.get('message', 'No message')}")
                                print(f"   Entities: {progress.get('entities_found', 0)}")
                                print(f"   Relationships: {progress.get('relationships_found', 0)}")
                                
                                # Check if complete
                                if progress.get('stage') == 'verification' and progress.get('progress_percent', 0) >= 100:
                                    print("🎉 Processing complete!")
                                    break
                            
                        else:
                            print(f"❌ Progress request failed: {progress_response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ Progress request failed: {e}")
                
                print("✅ Simple upload test complete")
                
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")

if __name__ == "__main__":
    test_simple_upload()