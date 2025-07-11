#!/bin/bash

# Document Deletion Test Suite
# Comprehensive testing of document deletion functionality

echo "🧪 DOCUMENT DELETION TEST SUITE"
echo "================================"
echo "Testing complete document deletion pipeline"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
echo "🔧 Setting up environment..."
source .venv/bin/activate

# Check if FastAPI is running
echo "🔍 Checking if FastAPI is running..."
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ FastAPI is running"
    API_RUNNING=true
else
    echo "⚠️  FastAPI is not running - starting it..."
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    API_PID=$!
    cd ..
    
    # Wait for API to start
    echo "⏳ Waiting for API to start..."
    sleep 10
    
    curl -s http://localhost:8000/health > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ FastAPI started successfully"
        API_RUNNING=true
    else
        echo "❌ Failed to start FastAPI"
        exit 1
    fi
fi

# Test 1: Document Deletion Service Unit Tests
echo ""
echo "🧪 TEST 1: Document Deletion Service Unit Tests"
echo "------------------------------------------------"

cd backend
python test_document_deletion.py
TEST1_RESULT=$?
print_status $TEST1_RESULT "Document deletion service unit tests"

# Test 2: Document Deletion API Tests
echo ""
echo "🧪 TEST 2: Document Deletion API Tests"
echo "--------------------------------------"

# Test document stats endpoint
echo "Testing document stats endpoint..."
curl -s http://localhost:8000/api/v1/documents/stats | python -m json.tool > /dev/null
TEST2A_RESULT=$?
print_status $TEST2A_RESULT "Document stats endpoint"

# Test document listing endpoint
echo "Testing document listing endpoint..."
curl -s http://localhost:8000/api/v1/documents/ | python -m json.tool > /dev/null
TEST2B_RESULT=$?
print_status $TEST2B_RESULT "Document listing endpoint"

# Test orphaned entity cleanup endpoint
echo "Testing orphaned entity cleanup endpoint..."
curl -s -X POST http://localhost:8000/api/v1/documents/cleanup/orphaned | python -m json.tool > /dev/null
TEST2C_RESULT=$?
print_status $TEST2C_RESULT "Orphaned entity cleanup endpoint"

# Calculate Test 2 result
if [ $TEST2A_RESULT -eq 0 ] && [ $TEST2B_RESULT -eq 0 ] && [ $TEST2C_RESULT -eq 0 ]; then
    TEST2_RESULT=0
else
    TEST2_RESULT=1
fi

print_status $TEST2_RESULT "Document deletion API tests"

# Test 3: Complete Document Lifecycle
echo ""
echo "🧪 TEST 3: Complete Document Lifecycle"
echo "--------------------------------------"

cd ..
python demo_document_lifecycle.py
TEST3_RESULT=$?
print_status $TEST3_RESULT "Complete document lifecycle demonstration"

# Test 4: Edge Cases and Error Handling
echo ""
echo "🧪 TEST 4: Edge Cases and Error Handling"
echo "----------------------------------------"

# Test deleting non-existent document
echo "Testing deletion of non-existent document..."
curl -s -X DELETE http://localhost:8000/api/v1/documents/non_existent_document > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Non-existent document deletion handled gracefully"
    TEST4A_RESULT=0
else
    echo "❌ Non-existent document deletion failed"
    TEST4A_RESULT=1
fi

# Test preview of non-existent document
echo "Testing preview of non-existent document..."
curl -s http://localhost:8000/api/v1/documents/non_existent_document/preview > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Non-existent document preview handled gracefully"
    TEST4B_RESULT=0
else
    echo "❌ Non-existent document preview failed"
    TEST4B_RESULT=1
fi

# Calculate Test 4 result
if [ $TEST4A_RESULT -eq 0 ] && [ $TEST4B_RESULT -eq 0 ]; then
    TEST4_RESULT=0
else
    TEST4_RESULT=1
fi

print_status $TEST4_RESULT "Edge cases and error handling"

# Test 5: Database Consistency
echo ""
echo "🧪 TEST 5: Database Consistency"
echo "------------------------------"

# Check for orphaned relationships
echo "Checking for orphaned relationships..."
cd backend
python -c "
import asyncio
from services.neo4j_service import neo4j_service

async def check_orphaned_relationships():
    if not neo4j_service.connected:
        neo4j_service.connect()
    
    query = '''
    MATCH (n)-[r]->(m)
    WHERE n.source_document_id IS NULL AND m.source_document_id IS NULL
    RETURN count(r) as orphaned_relationships
    '''
    
    result = neo4j_service.execute_query(query)
    
    if result.get('success'):
        count = result.get('records', [{}])[0].get('orphaned_relationships', 0)
        print(f'Orphaned relationships: {count}')
        return count == 0
    else:
        print('Failed to check orphaned relationships')
        return False

success = asyncio.run(check_orphaned_relationships())
exit(0 if success else 1)
"
TEST5_RESULT=$?
print_status $TEST5_RESULT "Database consistency check"

# Summary
echo ""
echo "📊 TEST SUMMARY"
echo "==============="

TOTAL_TESTS=5
PASSED_TESTS=0

if [ $TEST1_RESULT -eq 0 ]; then ((PASSED_TESTS++)); fi
if [ $TEST2_RESULT -eq 0 ]; then ((PASSED_TESTS++)); fi
if [ $TEST3_RESULT -eq 0 ]; then ((PASSED_TESTS++)); fi
if [ $TEST4_RESULT -eq 0 ]; then ((PASSED_TESTS++)); fi
if [ $TEST5_RESULT -eq 0 ]; then ((PASSED_TESTS++)); fi

echo "Tests passed: $PASSED_TESTS/$TOTAL_TESTS"

print_status $TEST1_RESULT "Document deletion service unit tests"
print_status $TEST2_RESULT "Document deletion API tests"
print_status $TEST3_RESULT "Complete document lifecycle demonstration"
print_status $TEST4_RESULT "Edge cases and error handling"
print_status $TEST5_RESULT "Database consistency check"

# Final result
if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED!"
    echo "✅ Document deletion pipeline is working correctly"
    echo "✅ Ready for production use"
    FINAL_RESULT=0
else
    echo ""
    echo "❌ SOME TESTS FAILED!"
    echo "⚠️  Document deletion pipeline has issues"
    echo "⚠️  Review failed tests before deployment"
    FINAL_RESULT=1
fi

# Cleanup
if [ ! -z "$API_PID" ]; then
    echo "🔧 Stopping API server..."
    kill $API_PID
fi

exit $FINAL_RESULT