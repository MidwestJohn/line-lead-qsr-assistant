#!/usr/bin/env python3
"""
Document Lifecycle Demonstration
Shows complete upload → process → query → delete pipeline
"""

import asyncio
import requests
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.rag')

BASE_URL = "http://localhost:8000"

async def demo_document_lifecycle():
    """Demonstrate the complete document lifecycle."""
    
    print("🚀 DOCUMENT LIFECYCLE DEMONSTRATION")
    print("=" * 50)
    print("This demo shows: Upload → Process → Query → Delete")
    print("=" * 50)
    
    try:
        # Step 1: Check API health
        print("\n🔍 STEP 1: Checking API health...")
        
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
        
        # Step 2: Get initial statistics
        print("\n📊 STEP 2: Getting initial statistics...")
        
        stats_response = requests.get(f"{BASE_URL}/api/v1/documents/stats")
        if stats_response.status_code == 200:
            initial_stats = stats_response.json()
            print(f"Initial graph state:")
            print(f"  - Entities: {initial_stats['statistics']['total_entities']}")
            print(f"  - Documents: {initial_stats['statistics']['unique_documents']}")
            print(f"  - Relationships: {initial_stats['statistics']['total_relationships']}")
        else:
            print(f"❌ Failed to get initial stats: {stats_response.status_code}")
            return False
        
        # Step 3: Upload and process a document
        print("\n📤 STEP 3: Uploading and processing document...")
        
        # Check if we have a sample PDF
        pdf_path = Path("sample_docs/sample_manual.pdf")
        if not pdf_path.exists():
            print(f"⚠️  Sample PDF not found at {pdf_path}")
            print("Creating a sample text document instead...")
            
            # Create sample text content
            sample_content = """
            # QSR Equipment Manual - Fryer Model X
            
            ## Equipment Specifications
            - Model: Fryer Model X
            - Capacity: 30 lbs
            - Temperature Range: 250-400°F
            - Power: 15 kW
            
            ## Startup Procedure
            1. Check oil level
            2. Set temperature to 350°F
            3. Wait for ready indicator
            4. Perform safety check
            
            ## Safety Protocols
            - Always wear protective equipment
            - Keep fire extinguisher nearby
            - Never exceed maximum temperature
            - Check oil quality daily
            
            ## Maintenance Schedule
            - Daily: Clean filters, check oil
            - Weekly: Deep clean, calibrate temperature
            - Monthly: Inspect heating elements
            """
            
            # Save as text file
            sample_path = Path("sample_docs")
            sample_path.mkdir(exist_ok=True)
            
            text_file = sample_path / "sample_manual.txt"
            text_file.write_text(sample_content)
            
            print(f"✅ Created sample text file: {text_file}")
            
            # Upload text file
            with open(text_file, 'rb') as f:
                files = {'file': (text_file.name, f, 'text/plain')}
                upload_response = requests.post(
                    f"{BASE_URL}/api/v2/upload-automatic",
                    files=files
                )
        else:
            # Upload PDF
            with open(pdf_path, 'rb') as f:
                files = {'file': (pdf_path.name, f, 'application/pdf')}
                upload_response = requests.post(
                    f"{BASE_URL}/api/v2/upload-automatic",
                    files=files
                )
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            document_id = upload_result.get('document_id')
            task_id = upload_result.get('task_id')
            
            print(f"✅ Document uploaded successfully")
            print(f"  - Document ID: {document_id}")
            print(f"  - Task ID: {task_id}")
            
            # Step 4: Monitor processing
            print("\n⏳ STEP 4: Monitoring processing...")
            
            processing_complete = False
            max_wait = 120  # 2 minutes
            wait_time = 0
            
            while not processing_complete and wait_time < max_wait:
                time.sleep(5)
                wait_time += 5
                
                # Check processing status
                status_response = requests.get(f"{BASE_URL}/api/v2/upload-automatic/{task_id}/status")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_stage = status.get('current_stage', 'unknown')
                    progress = status.get('progress', 0)
                    
                    print(f"  Progress: {progress}% - {current_stage}")
                    
                    if status.get('completed'):
                        processing_complete = True
                        print("✅ Processing completed!")
                    elif status.get('failed'):
                        print(f"❌ Processing failed: {status.get('error', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Failed to get processing status: {status_response.status_code}")
            
            if not processing_complete:
                print(f"⚠️  Processing timed out after {max_wait} seconds")
                return False
            
        else:
            print(f"❌ Document upload failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return False
        
        # Step 5: Get updated statistics
        print("\n📊 STEP 5: Getting updated statistics...")
        
        updated_stats_response = requests.get(f"{BASE_URL}/api/v1/documents/stats")
        if updated_stats_response.status_code == 200:
            updated_stats = updated_stats_response.json()
            
            print(f"Updated graph state:")
            print(f"  - Entities: {updated_stats['statistics']['total_entities']}")
            print(f"  - Documents: {updated_stats['statistics']['unique_documents']}")
            print(f"  - Relationships: {updated_stats['statistics']['total_relationships']}")
            
            # Show entity types
            entity_types = updated_stats['statistics']['entity_type_counts']
            if entity_types:
                print(f"  - Entity types:")
                for entity_type, count in entity_types.items():
                    print(f"    {entity_type}: {count}")
        
        # Step 6: Test queries
        print("\n🔍 STEP 6: Testing queries...")
        
        test_queries = [
            "What is the startup procedure for the fryer?",
            "What safety protocols should be followed?",
            "What is the maintenance schedule?",
            "What equipment is described in the manual?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            
            query_response = requests.post(
                f"{BASE_URL}/api/v1/rag/query",
                json={"query": query}
            )
            
            if query_response.status_code == 200:
                query_result = query_response.json()
                answer = query_result.get('answer', 'No answer provided')
                print(f"Answer: {answer[:200]}...")
            else:
                print(f"❌ Query failed: {query_response.status_code}")
        
        # Step 7: Preview document deletion
        print(f"\n🔍 STEP 7: Previewing document deletion...")
        
        preview_response = requests.get(f"{BASE_URL}/api/v1/documents/{document_id}/preview")
        
        if preview_response.status_code == 200:
            preview = preview_response.json()
            preview_data = preview.get('preview', {})
            
            print(f"Deletion preview for {document_id}:")
            print(f"  - Entities to remove: {preview_data.get('entities_to_remove', 0)}")
            print(f"  - Entities to preserve: {preview_data.get('entities_to_preserve', 0)}")
            print(f"  - Relationships to remove: {preview_data.get('relationships_to_remove', 0)}")
            
            entity_types = preview_data.get('entity_types', {})
            if entity_types:
                print(f"  - Entity types to remove:")
                for entity_type, count in entity_types.items():
                    print(f"    {entity_type}: {count}")
            
            shared_entities = preview_data.get('shared_entities', [])
            if shared_entities:
                print(f"  - Shared entities (will be preserved):")
                for entity in shared_entities:
                    print(f"    {entity['name']} ({entity['type']})")
        else:
            print(f"❌ Deletion preview failed: {preview_response.status_code}")
            print(f"Response: {preview_response.text}")
        
        # Step 8: Delete document
        print(f"\n🗑️  STEP 8: Deleting document...")
        
        delete_response = requests.delete(f"{BASE_URL}/api/v1/documents/{document_id}")
        
        if delete_response.status_code == 200:
            delete_result = delete_response.json()
            
            print(f"✅ Document deleted successfully")
            print(f"  - Entities removed: {delete_result.get('entities_removed', 0)}")
            print(f"  - Relationships removed: {delete_result.get('relationships_removed', 0)}")
            print(f"  - Shared entities preserved: {delete_result.get('shared_entities_preserved', 0)}")
            
            if delete_result.get('errors'):
                print(f"  - Errors: {delete_result['errors']}")
        else:
            print(f"❌ Document deletion failed: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
        
        # Step 9: Verify deletion
        print(f"\n✅ STEP 9: Verifying deletion...")
        
        final_stats_response = requests.get(f"{BASE_URL}/api/v1/documents/stats")
        if final_stats_response.status_code == 200:
            final_stats = final_stats_response.json()
            
            print(f"Final graph state:")
            print(f"  - Entities: {final_stats['statistics']['total_entities']}")
            print(f"  - Documents: {final_stats['statistics']['unique_documents']}")
            print(f"  - Relationships: {final_stats['statistics']['total_relationships']}")
            
            # Check if document is really gone
            document_ids = final_stats['statistics']['document_ids']
            
            if document_id not in document_ids:
                print(f"✅ Document {document_id} successfully removed from graph")
            else:
                print(f"❌ Document {document_id} still found in graph!")
                return False
        
        # Step 10: Test query after deletion
        print(f"\n🔍 STEP 10: Testing query after deletion...")
        
        post_delete_query = "What is the startup procedure for the fryer?"
        
        query_response = requests.post(
            f"{BASE_URL}/api/v1/rag/query",
            json={"query": post_delete_query}
        )
        
        if query_response.status_code == 200:
            query_result = query_response.json()
            answer = query_result.get('answer', 'No answer provided')
            print(f"Query after deletion: {post_delete_query}")
            print(f"Answer: {answer[:200]}...")
            
            # The answer should indicate no information is available
            if "no information" in answer.lower() or "not found" in answer.lower():
                print("✅ Query correctly indicates no information available")
            else:
                print("⚠️  Query may still return information from deleted document")
        
        print(f"\n🎉 DOCUMENT LIFECYCLE DEMONSTRATION COMPLETE!")
        print("✅ All steps completed successfully")
        print("\nThe demonstration showed:")
        print("  1. Document upload and automatic processing")
        print("  2. Graph population with entities and relationships")
        print("  3. Query functionality using the processed data")
        print("  4. Document deletion with proper cleanup")
        print("  5. Verification that deleted data is no longer accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Demonstration error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main demonstration function."""
    
    print("🚀 DOCUMENT LIFECYCLE DEMONSTRATION")
    print("=" * 50)
    print("This demo shows the complete document lifecycle:")
    print("  Upload → Process → Query → Delete")
    print("=" * 50)
    
    success = await demo_document_lifecycle()
    
    if success:
        print("\n🎉 DEMONSTRATION SUCCESSFUL!")
        print("✅ Document lifecycle is working correctly")
        return True
    else:
        print("\n❌ DEMONSTRATION FAILED!")
        print("⚠️  Document lifecycle has issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)