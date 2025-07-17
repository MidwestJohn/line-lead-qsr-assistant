#!/usr/bin/env python3
"""
Test Ragie Client Initialization
================================

Debug script to test Ragie client initialization
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append('backend')

from services.ragie_service_clean import clean_ragie_service

def test_ragie_client():
    """Test Ragie client initialization"""
    print("Testing Ragie client initialization...")
    
    # Check environment variables
    api_key = os.getenv("RAGIE_API_KEY")
    partition = os.getenv("RAGIE_PARTITION", "qsr_manuals")
    
    print(f"API Key: {'SET' if api_key else 'NOT SET'}")
    print(f"Partition: {partition}")
    
    # Test service availability
    print(f"Service available: {clean_ragie_service.is_available()}")
    print(f"Client object: {clean_ragie_service.client}")
    
    # Test basic functionality
    try:
        if clean_ragie_service.client:
            print("✅ Client is initialized")
            # Try to access client properties
            print(f"Client type: {type(clean_ragie_service.client)}")
        else:
            print("❌ Client is None")
    except Exception as e:
        print(f"❌ Error testing client: {e}")

if __name__ == "__main__":
    test_ragie_client()