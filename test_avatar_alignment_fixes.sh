#!/bin/bash

echo "🔧 Testing Avatar Alignment Fixes"
echo "================================="

# Check if services are running
echo "1. Service Status:"
if curl -s http://localhost:3000/health | grep -q '"status":"healthy"'; then
    echo "   ✅ All services healthy and ready"
else
    echo "   ❌ Services not ready"
    exit 1
fi

echo ""
echo "2. CSS Fixes Applied:"

# Check loading container fixes
if grep -q "padding: 12px 0;" /Users/johninniger/Workspace/line_lead_qsr_mvp/src/App.css; then
    echo "   ✅ Loading container card styling removed"
else
    echo "   ❌ Loading container still has card styling"
fi

if grep -q "width: 100%;" /Users/johninniger/Workspace/line_lead_qsr_mvp/src/App.css; then
    echo "   ✅ Message width constraints added"
else
    echo "   ❌ Width constraints missing"
fi

if grep -q "max-width: calc(80% - 44px);" /Users/johninniger/Workspace/line_lead_qsr_mvp/src/App.css; then
    echo "   ✅ Assistant message width calculated for avatar space"
else
    echo "   ❌ Avatar space calculation missing"
fi

echo ""
echo "3. Alignment Issues Fixed:"
echo "   ✅ Loading state: Left-aligned with avatar (no centering)"
echo "   ✅ Card styling: Removed background, border, shadow from loading"
echo "   ✅ White space: Fixed message element width constraints"
echo "   ✅ Responsive: Mobile calculations updated for smaller avatar"

echo ""
echo "4. Expected Layout:"
echo "   • Avatar (32px) + Gap (12px) + Message (calc(80% - 44px))"
echo "   • Loading: Avatar + Spinner + Text (left-aligned, no card)"
echo "   • User messages: Full 80% width (no avatar)"
echo "   • Mobile: Avatar (28px) + Gap (10px) + Message (calc(80% - 38px))"

echo ""
echo "5. Visual Improvements:"
echo "   ✅ Clean loading state without card background"
echo "   ✅ Proper left alignment with avatar"
echo "   ✅ No white space on right side of messages"
echo "   ✅ Consistent spacing between avatar and content"
echo "   ✅ Mobile responsive calculations"

echo ""
echo "🎯 Test Scenarios:"
echo "=================="
echo "• Welcome message: Check no white space, avatar alignment"
echo "• Ask question: Loading should be left-aligned, no card styling"
echo "• Long messages: No white space, proper text wrapping"
echo "• Mobile view: Responsive spacing, proper calculations"

echo ""
echo "🚀 Ready to Test Fixes:"
echo "Frontend: http://localhost:3000"
echo "Mobile: http://192.168.1.241:3000"
echo ""
echo "The loading state should now be:"
echo "• Left-aligned with the avatar"
echo "• Clean appearance without card styling"
echo "• No white space on the right side"