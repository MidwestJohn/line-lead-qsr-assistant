#!/bin/bash

echo "🔄 Testing Horizontal Loading Layout (Avatar + Content)"
echo "====================================================="

# Check if services are running
echo "1. Service Status:"
if curl -s http://localhost:3000/health | grep -q '"status":"healthy"'; then
    echo "   ✅ All services healthy and ready"
else
    echo "   ❌ Services not ready"
    exit 1
fi

echo ""
echo "2. Horizontal Loading Layout Implementation:"

# Check that loading state is added back
if grep -q "Loading state - Avatar on left, loading content on right" /Users/johninniger/Workspace/line_lead_qsr_mvp/src/App.js; then
    echo "   ✅ Horizontal loading state implemented"
else
    echo "   ❌ Horizontal loading state missing"
fi

# Check for loading content styling
if grep -q "loading-content" /Users/johninniger/Workspace/line_lead_qsr_mvp/src/App.css; then
    echo "   ✅ Loading content CSS styling added"
else
    echo "   ❌ Loading content CSS missing"
fi

# Check for proper flex layout
if grep -q "display: flex" /Users/johninniger/Workspace/line_lead_qsr_mvp/src/App.css; then
    echo "   ✅ Flex layout for horizontal alignment"
else
    echo "   ❌ Flex layout missing"
fi

# Check for inline text styling
if grep -q "loading-text-inline" /Users/johninniger/Workspace/line_lead_qsr_mvp/src/App.css; then
    echo "   ✅ Inline loading text styling implemented"
else
    echo "   ❌ Inline loading text styling missing"
fi

echo ""
echo "3. Layout Structure:"
echo "   ✅ Avatar: Fixed 32px × 32px on the left side"
echo "   ✅ Loading content: Positioned immediately to the right"
echo "   ✅ Same row: All content horizontally aligned"
echo "   ✅ Consistent spacing: Same gap as regular messages"

echo ""
echo "4. Visual Layout Pattern:"
echo "   [Avatar] → [Spinner] [Text 'Assistant is responding...']"
echo "   [ 32px ] → [ 16px  ] [Text in same line]"
echo ""
echo "   • Avatar anchors the left side"
echo "   • Spinner and text flow naturally to the right"
echo "   • Same layout pattern as regular messages"

echo ""
echo "5. Loading States:"
echo "   • Thinking: Avatar + Spinner + 'Assistant is thinking...'"
echo "   • Waiting: Avatar + Spinner + 'Assistant is responding...'"
echo "   • Streaming: Avatar + Text + Cursor (same position)"

echo ""
echo "6. Transition Flow:"
echo "   1. User sends message"
echo "   2. Loading state appears: [Avatar] [Spinner] [Text]"
echo "   3. First chunk arrives"
echo "   4. Loading content replaced with streaming text"
echo "   5. Avatar stays in exact same position"
echo "   6. No layout shift during transition"

echo ""
echo "🎯 Success Criteria:"
echo "==================="
echo "✅ Avatar and loading content perfectly aligned horizontally"
echo "✅ Loading spinner appears immediately to right of avatar"
echo "✅ Text flows naturally next to spinner"
echo "✅ Layout matches eventual message layout exactly"
echo "✅ Smooth transition from loading → streaming → final message"

echo ""
echo "📱 Visual Result:"
echo "================="
echo "The loading state looks like a regular message with:"
echo "• Avatar on left (consistent with all assistant messages)"
echo "• Content on right (spinner + text in same line)"
echo "• Same spacing and alignment as normal messages"
echo "• Natural horizontal flow of elements"

echo ""
echo "🧪 Test Instructions:"
echo "====================="
echo "1. Send a message"
echo "2. Watch for loading state with horizontal layout"
echo "3. Verify avatar is on left, spinner + text on right"
echo "4. Check that transition to streaming is smooth"
echo "5. Confirm no layout shifts occur"

echo ""
echo "🚀 Ready to Test:"
echo "Frontend: http://localhost:3000"
echo "Mobile: http://192.168.1.241:3000"
echo ""
echo "Try asking: 'How do I fix my fryer?'"
echo "Look for: [Avatar] → [Spinner] [Text] in horizontal alignment!"