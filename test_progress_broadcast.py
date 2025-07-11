import sys
import os
import asyncio
import json

# Add paths
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp')
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

async def test_progress_broadcast():
    """Test broadcasting progress updates"""
    try:
        # Import the progress manager
        from websocket_progress import progress_manager, ProgressUpdate
        
        print("🔍 Testing progress broadcast system...")
        
        # Create a test progress update
        test_process_id = "test_process_12345"
        
        progress_update = ProgressUpdate(
            process_id=test_process_id,
            stage="text_extraction",
            progress_percent=25.0,
            message="Testing progress broadcast",
            entities_found=5,
            relationships_found=3
        )
        
        print(f"📡 Broadcasting test progress for {test_process_id}")
        await progress_manager.broadcast_progress(progress_update)
        print("✅ Progress broadcast test completed")
        
    except Exception as e:
        print(f"❌ Progress broadcast test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_progress_broadcast())
