#!/bin/bash

echo "🧪 Testing Line Lead QSR MVP File Upload..."
echo ""

# Test 1: Upload a valid PDF
echo "Test 1: Upload valid PDF"
curl -X POST -F "file=@test_fryer_manual.pdf" http://localhost:8000/upload
echo ""
echo ""

# Test 2: List documents
echo "Test 2: List uploaded documents"
curl http://localhost:8000/documents | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total documents: {data[\"total_count\"]}')
for doc in data['documents']:
    print(f'- {doc[\"original_filename\"]} ({doc[\"pages_count\"]} pages, {doc[\"file_size\"]} bytes)')
"
echo ""
echo ""

# Test 3: Chat functionality
echo "Test 3: Chat functionality"
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I fix my fryer that wont heat oil?"}' | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Response: {data[\"response\"]}')
"
echo ""
echo ""

# Test 4: Invalid file type
echo "Test 4: Invalid file type (should fail)"
echo "This is not a PDF" > test_invalid.txt
curl -X POST -F "file=@test_invalid.txt" http://localhost:8000/upload
rm test_invalid.txt
echo ""
echo ""

echo "✅ All tests completed!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000/docs"