#!/bin/bash

echo "🔍 Testing Service Status Detection"
echo "=================================="

# Test health endpoint from both perspectives
echo "1. Backend health endpoint (direct):"
curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"'

echo ""
echo "2. Frontend health endpoint (proxied):"
curl -s http://localhost:3000/health | grep -o '"status":"[^"]*"'

echo ""
echo "3. Service readiness details:"
curl -s http://localhost:3000/health | grep -o '"search_ready":[^,]*'

echo ""
echo "4. Testing frontend service status logic..."

# Check if the health endpoint returns what the frontend expects
HEALTH_RESPONSE=$(curl -s http://localhost:3000/health)
STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
SEARCH_READY=$(echo "$HEALTH_RESPONSE" | grep -o '"search_ready":[^,}]*' | cut -d':' -f2)

echo "   Status: $STATUS"
echo "   Search Ready: $SEARCH_READY"

if [ "$STATUS" = "healthy" ] && [ "$SEARCH_READY" = "true" ]; then
    echo "   ✅ Services should be detected as ready"
    echo ""
    echo "💡 If the frontend still shows 'Services starting up':"
    echo "   1. Hard refresh the browser (Cmd+Shift+R)"
    echo "   2. Check browser console for errors"
    echo "   3. Wait 30 seconds for automatic status update"
else
    echo "   ❌ Services not fully ready"
    echo "   Backend needs to be healthy and search_ready must be true"
fi

echo ""
echo "🌐 Frontend URL: http://localhost:3000"
echo "🔧 Backend URL: http://localhost:8000"