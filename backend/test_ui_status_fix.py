#!/usr/bin/env python3
"""
Test UI Status Fix
==================

This script verifies that the UI will now receive the correct "COMPLETED" status
for all documents instead of "PROCESSING".
"""

import requests
import json
import sys

def test_ui_status_fix():
    """Test that UI gets correct document status"""
    
    print("🧪 Testing UI Status Fix")
    print("=" * 40)
    
    try:
        # Test the diagnostics endpoint that the UI uses
        response = requests.get('http://localhost:8000/diagnostics/processing-status', timeout=15)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return False
        
        data = response.json()
        
        print("📊 Processing Progress Summary:")
        sm = data.get('system_metrics', {})
        
        total = sm.get('total_documents', 0)
        processing = sm.get('documents_processing', 0) 
        completed = sm.get('documents_completed', 0)
        failed = sm.get('documents_failed', 0)
        
        print(f"  Processing: {processing}")
        print(f"  Completed: {completed}")
        print(f"  Failed: {failed}")
        print()
        
        print("📄 Document Status Details:")
        all_completed = True
        
        for doc in data.get('documents', []):
            filename = doc.get('original_filename', 'unknown')
            status = doc.get('status', 'unknown')
            entities = doc.get('entities_extracted', 0)
            
            if status.lower() == 'completed':
                print(f"  ✅ {filename}: COMPLETED ({entities} entities)")
            else:
                print(f"  ❌ {filename}: {status.upper()} ({entities} entities)")
                all_completed = False
        
        print()
        
        if all_completed and completed == total and processing == 0:
            print("🎉 SUCCESS! All documents show as COMPLETED")
            print("💡 The UI should now show:")
            print("   - Processing: 0")
            print("   - Completed: 5") 
            print("   - Failed: 0")
            print("   - All document cards should show 'COMPLETED' status")
            return True
        else:
            print("❌ FAILED! Some documents still show as processing")
            print(f"   Expected: 0 processing, {total} completed")
            print(f"   Actual: {processing} processing, {completed} completed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing status fix: {e}")
        return False

def main():
    success = test_ui_status_fix()
    
    if success:
        print("\n✅ UI Status Fix Test PASSED!")
        print("🚀 The UI health assessment should now show all files as 'COMPLETED'")
        print("\nServers Running:")
        print("  - Backend: http://localhost:8000")
        print("  - Frontend: http://localhost:3000")
        print("\nRefresh your browser to see the updated status!")
    else:
        print("\n❌ UI Status Fix Test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()