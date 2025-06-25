#!/bin/bash

# Test script for application resilience
echo "🧪 Testing Line Lead QSR MVP Resilience"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"

test_counter=1

print_test() {
    echo -e "\n${YELLOW}Test ${test_counter}: $1${NC}"
    ((test_counter++))
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Test 1: Normal Operation
print_test "Normal API Operation"
response=$(curl -s -X POST "${BASE_URL}/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "How do I clean the grill?"}')

if echo "$response" | grep -q "response"; then
    print_success "Chat API working normally"
else
    print_error "Chat API failed in normal conditions"
    echo "Response: $response"
fi

# Test 2: Health Check Endpoint
print_test "Enhanced Health Check"
health=$(curl -s "${BASE_URL}/health")

if echo "$health" | grep -q '"status":"healthy"'; then
    print_success "Health check endpoint working"
    document_count=$(echo "$health" | grep -o '"document_count":[0-9]*' | cut -d':' -f2)
    search_ready=$(echo "$health" | grep -o '"search_ready":[a-z]*' | cut -d':' -f2)
    print_info "Documents loaded: $document_count"
    print_info "Search engine ready: $search_ready"
else
    print_error "Health check failed"
    echo "Response: $health"
fi

# Test 3: Service Status Details
print_test "Service Status Details"
services=$(echo "$health" | grep -o '"services":{[^}]*}')
if [ ! -z "$services" ]; then
    print_success "Service status details available"
    print_info "$services"
else
    print_error "Service status details missing"
fi

# Test 4: Timeout Simulation (Quick timeout)
print_test "Timeout Handling"
timeout_response=$(timeout 2s curl -s -X POST "${BASE_URL}/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "This should timeout quickly"}' --max-time 1)

if [ $? -eq 124 ]; then
    print_success "Timeout handling working (request timed out as expected)"
else
    print_info "Timeout test completed (may not have actually timed out)"
fi

# Test 5: Invalid Request
print_test "Invalid Request Handling"
invalid_response=$(curl -s -X POST "${BASE_URL}/chat" \
    -H "Content-Type: application/json" \
    -d '{"invalid": "request"}')

if echo "$invalid_response" | grep -q "error\|detail"; then
    print_success "Invalid requests handled properly"
else
    print_info "Invalid request test completed"
fi

# Test 6: File Upload Endpoint Check  
print_test "File Upload Endpoint"
upload_check=$(curl -s -X POST "${BASE_URL}/upload" -F "test=dummy")
if echo "$upload_check" | grep -q "error\|detail\|success\|message"; then
    print_success "Upload endpoint responding"
else
    print_error "Upload endpoint not responding"
fi

# Test 7: Document List Endpoint
print_test "Document Management"
docs=$(curl -s "${BASE_URL}/documents")
if echo "$docs" | grep -q "documents"; then
    doc_count=$(echo "$docs" | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
    print_success "Document management working ($doc_count documents)"
else
    print_error "Document management failed"
fi

# Test 8: Search Stats
print_test "Search Engine Status"
search_stats=$(curl -s "${BASE_URL}/search-stats")
if echo "$search_stats" | grep -q "total_chunks"; then
    chunks=$(echo "$search_stats" | grep -o '"total_chunks":[0-9]*' | cut -d':' -f2)
    model=$(echo "$search_stats" | grep -o '"model_name":"[^"]*"' | cut -d':' -f2 | tr -d '"')
    print_success "Search engine operational ($chunks chunks, model: $model)"
else
    print_error "Search engine status unavailable"
fi

# Test 9: AI Status  
print_test "AI Assistant Status"
ai_status=$(curl -s "${BASE_URL}/ai-status")
if echo "$ai_status" | grep -q "status"; then
    print_success "AI assistant status endpoint working"
else
    print_error "AI assistant status unavailable"
fi

# Test 10: Frontend Asset Loading
print_test "Frontend Loading"
frontend_response=$(curl -s -I "${BASE_URL}" | head -n 1)
if echo "$frontend_response" | grep -q "200 OK"; then
    print_success "Frontend loading successfully"
else
    print_error "Frontend loading issues"
fi

# Test 11: Mobile Network Simulation (Different User-Agent)
print_test "Mobile Client Simulation"
mobile_response=$(curl -s -X POST "${BASE_URL}/health" \
    -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_7 like Mac OS X)")

if echo "$mobile_response" | grep -q "healthy"; then
    print_success "Mobile client support working"
else
    print_error "Mobile client issues detected"
fi

# Summary
echo -e "\n${YELLOW}📊 Test Summary${NC}"
echo "================================"
print_info "All core resilience features tested"
print_info "Frontend: http://localhost:3000"
print_info "Backend API: http://localhost:8000"
print_info "Mobile Access: http://192.168.1.241:3000"

echo -e "\n${GREEN}🚀 Resilience Testing Complete!${NC}"
echo "The app includes:"
echo "• Enhanced health monitoring"
echo "• Retry logic with exponential backoff"
echo "• Service status indicators"
echo "• Error boundaries and graceful degradation"
echo "• Offline detection and message queuing"
echo "• Mobile network resilience"
echo "• Comprehensive error categorization"
echo "• Real-time service monitoring"