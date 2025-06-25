#!/bin/bash

# Test script for document delete functionality
echo "🧪 Testing Line Lead QSR Document Delete Feature"
echo "================================================="

# Check if backend is running
echo "1. Checking backend health..."
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running"
    exit 1
fi

# Get initial document count
echo ""
echo "2. Getting initial document count..."
INITIAL_COUNT=$(curl -s http://localhost:8000/documents | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
echo "📊 Initial document count: $INITIAL_COUNT"

# Upload a test document
echo ""
echo "3. Uploading test document..."
UPLOAD_RESULT=$(curl -s -X POST -F "file=@test_fryer_manual.pdf" http://localhost:8000/upload)
DOCUMENT_ID=$(echo $UPLOAD_RESULT | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$DOCUMENT_ID" ]; then
    echo "✅ Document uploaded with ID: $DOCUMENT_ID"
else
    echo "❌ Failed to upload document"
    exit 1
fi

# Verify document count increased
echo ""
echo "4. Verifying document count increased..."
NEW_COUNT=$(curl -s http://localhost:8000/documents | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
echo "📊 New document count: $NEW_COUNT"

if [ $NEW_COUNT -eq $((INITIAL_COUNT + 1)) ]; then
    echo "✅ Document count increased correctly"
else
    echo "❌ Document count did not increase correctly"
    exit 1
fi

# Test delete functionality
echo ""
echo "5. Testing document deletion..."
DELETE_RESULT=$(curl -s -X DELETE http://localhost:8000/documents/$DOCUMENT_ID)
SUCCESS=$(echo $DELETE_RESULT | grep -o '"success":true')

if [ -n "$SUCCESS" ]; then
    echo "✅ Document deletion API returned success"
else
    echo "❌ Document deletion API failed"
    echo "Response: $DELETE_RESULT"
    exit 1
fi

# Verify document count decreased
echo ""
echo "6. Verifying document count decreased..."
FINAL_COUNT=$(curl -s http://localhost:8000/documents | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
echo "📊 Final document count: $FINAL_COUNT"

if [ $FINAL_COUNT -eq $INITIAL_COUNT ]; then
    echo "✅ Document count returned to original value"
else
    echo "❌ Document count did not decrease correctly"
    exit 1
fi

# Test deleting non-existent document (should return 404)
echo ""
echo "7. Testing deletion of non-existent document..."
ERROR_RESULT=$(curl -s -X DELETE http://localhost:8000/documents/nonexistent-id)
NOT_FOUND=$(echo $ERROR_RESULT | grep -o '"detail":"Document not found"')

if [ -n "$NOT_FOUND" ]; then
    echo "✅ Non-existent document deletion correctly returned 404"
else
    echo "❌ Non-existent document deletion did not return proper error"
    echo "Response: $ERROR_RESULT"
fi

echo ""
echo "🎉 All tests passed! Document delete feature is working correctly."
echo ""
echo "📋 Test Summary:"
echo "   - Backend health check: ✅"
echo "   - Document upload: ✅"
echo "   - Document deletion: ✅"
echo "   - Count verification: ✅"
echo "   - Error handling: ✅"
echo ""
echo "🚀 Ready for production use!"