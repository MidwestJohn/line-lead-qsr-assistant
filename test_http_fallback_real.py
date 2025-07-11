#!/usr/bin/env python3

"""
Real HTTP Fallback Test

This script tests the HTTP fallback with a real file upload to verify the system works end-to-end.
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
    p.drawString(100, 750, "QSR Equipment Manual")
    p.drawString(100, 720, "Ice Cream Machine Maintenance Guide")
    p.drawString(100, 690, "Temperature should be set to 18-20°F for optimal operation.")
    p.drawString(100, 660, "Clean the equipment daily using approved sanitizers.")
    p.drawString(100, 630, "For McDonald's locations, follow corporate standards.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer.getvalue()

def test_real_upload_with_fallback():
    """Test real upload and monitor progress via HTTP fallback."""
    
    print("🧪 Real Upload HTTP Fallback Test")
    print("=" * 50)
    
    # Create test PDF
    print("📄 Creating test PDF...")
    pdf_content = create_test_pdf()
    
    # Upload the file
    print("📤 Uploading file...")
    
    files = {
        'file': ('test_qsr_manual.pdf', pdf_content, 'application/pdf')
    }
    
    try:
        upload_response = requests.post(
            "http://localhost:8000/upload-files",
            files=files,
            timeout=30
        )
        
        print(f"📡 Upload Response Status: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            response_data = upload_response.json()
            print(f"✅ Upload successful!")
            
            # Look for process_id in response
            process_id = None
            if 'process_id' in response_data:
                process_id = response_data['process_id']
            elif 'upload_result' in response_data and 'process_id' in response_data['upload_result']:
                process_id = response_data['upload_result']['process_id']
            
            if process_id:
                print(f"🆔 Process ID: {process_id}")
                
                # Monitor progress via HTTP fallback
                print(f"📊 Monitoring progress via HTTP fallback...")
                
                for attempt in range(15):  # Monitor for 45 seconds
                    time.sleep(3)
                    
                    try:
                        progress_response = requests.get(
                            f"http://localhost:8000/ws/progress/{process_id}",
                            timeout=5
                        )
                        
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            
                            print(f"🔍 Attempt {attempt + 1}:")
                            print(f"   Success: {progress_data.get('success')}")
                            print(f"   Fallback Mode: {progress_data.get('fallback_mode')}")
                            
                            if progress_data.get('success') and progress_data.get('progress'):
                                progress = progress_data['progress']
                                print(f"   Stage: {progress.get('stage')}")
                                print(f"   Progress: {progress.get('progress_percent', 0)}%")
                                print(f"   Message: {progress.get('message', 'No message')}")
                                print(f"   Entities: {progress.get('entities_found', 0)}")
                                print(f"   Relationships: {progress.get('relationships_found', 0)}")
                                
                                # Check if complete
                                if progress.get('stage') == 'verification' and progress.get('progress_percent', 0) >= 100:
                                    print("🎉 Upload processing complete!")
                                    break
                            else:
                                print(f"   Error: {progress_data.get('error', 'Unknown error')}")
                        else:
                            print(f"❌ HTTP fallback failed: {progress_response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ HTTP fallback request failed: {e}")
                
                print("✅ HTTP fallback monitoring complete")
                
            else:
                print("❌ No process_id found in upload response")
                print(f"Response data: {response_data}")
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")

if __name__ == "__main__":
    test_real_upload_with_fallback()