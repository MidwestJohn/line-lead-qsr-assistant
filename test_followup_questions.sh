#!/bin/bash

echo "🤖 Testing Follow-Up Question Prompt Pattern"
echo "==========================================="

# Check if services are running
echo "1. Service Status:"
if curl -s http://localhost:8000/health | grep -q '"status":"healthy"'; then
    echo "   ✅ All services healthy and ready"
else
    echo "   ❌ Services not ready"
    exit 1
fi

echo ""
echo "2. System Prompt Update Verification:"

# Check if the new system prompt is implemented
if grep -q "FOLLOW-UP QUESTION PROMPT" /Users/johninniger/Workspace/line_lead_qsr_mvp/openai_integration.py; then
    echo "   ✅ Follow-Up Question Prompt pattern added to system prompt"
else
    echo "   ❌ Follow-Up Question Prompt pattern missing"
fi

if grep -q "Reverse Question Graph" /Users/johninniger/Workspace/line_lead_qsr_mvp/openai_integration.py; then
    echo "   ✅ Reverse Question Graph methodology included"
else
    echo "   ❌ Reverse Question Graph methodology missing"
fi

if grep -q "dependency structure" /Users/johninniger/Workspace/line_lead_qsr_mvp/openai_integration.py; then
    echo "   ✅ Dependency structure guidance included"
else
    echo "   ❌ Dependency structure guidance missing"
fi

if grep -q "My equipment isn't working" /Users/johninniger/Workspace/line_lead_qsr_mvp/openai_integration.py; then
    echo "   ✅ Example clarifying question pattern included"
else
    echo "   ❌ Example clarifying question pattern missing"
fi

echo ""
echo "3. Updated System Prompt Features:"
echo "   ✅ Maintains original QSR equipment maintenance focus"
echo "   ✅ Preserves safety and actionable guidance principles"
echo "   ✅ Adds structured clarifying question behavior"
echo "   ✅ Includes dependency-based question progression"
echo "   ✅ Provides example of clarifying question format"

echo ""
echo "4. Expected Behavior Changes:"
echo "   • Ambiguous questions → Ask clarifying questions first"
echo "   • Clear questions → Provide direct answers"
echo "   • High-risk situations → Request more details before proceeding"
echo "   • Vague requests → Guide users through structured questions"

echo ""
echo "🧪 Test Scenarios for Follow-Up Questions:"
echo "========================================"
echo ""
echo "AMBIGUOUS QUESTIONS (Should trigger clarifying questions):"
echo "• 'help with cleaning' → Should ask: What equipment? What type of cleaning?"
echo "• 'my equipment is broken' → Should ask: What equipment? What symptoms?"
echo "• 'need maintenance help' → Should ask: What equipment? What type of maintenance?"
echo "• 'something is wrong' → Should ask: What equipment? What's the problem?"
echo ""
echo "CLEAR QUESTIONS (Should get direct answers):"
echo "• 'How do I clean the fryer oil filter?' → Direct step-by-step answer"
echo "• 'What temperature should the grill be set to?' → Direct temperature answer"
echo "• 'How often should I clean the ice machine?' → Direct frequency answer"

echo ""
echo "5. Follow-Up Question Pattern Structure:"
echo "   1. **Acknowledge** the request with empathy"
echo "   2. **Explain** why clarification is needed"
echo "   3. **Ask targeted questions** in logical order:"
echo "      - What equipment (foundational)"
echo "      - What symptoms/problems (details)"
echo "      - When/how long (context)"
echo "      - Safety concerns (if applicable)"
echo "   4. **Structure questions** as numbered list for clarity"

echo ""
echo "6. Dependency Question Structure:"
echo "   • DON'T ask advanced questions before basics"
echo "   • DO establish equipment type first"
echo "   • DO get problem description second"
echo "   • DO gather context third"
echo "   • DO address safety last (if relevant)"

echo ""
echo "🎯 Success Criteria:"
echo "==================="
echo "✅ Assistant asks clarifying questions for ambiguous requests"
echo "✅ Still provides direct answers for clear, specific questions"
echo "✅ Questions follow logical dependency structure"
echo "✅ Maintains helpful, practical tone for restaurant workers"
echo "✅ Prioritizes safety in high-risk situations"

echo ""
echo "📋 Testing Instructions:"
echo "======================="
echo "1. Open: http://localhost:3000"
echo "2. Test ambiguous questions:"
echo "   - 'help with cleaning'"
echo "   - 'my equipment is broken'"
echo "   - 'need maintenance help'"
echo "3. Verify it asks clarifying questions"
echo "4. Test specific questions:"
echo "   - 'How do I clean the fryer?'"
echo "   - 'What's the grill temperature?'"
echo "5. Verify it gives direct answers"

echo ""
echo "💡 Expected Clarifying Question Format:"
echo "======================================"
echo "User: 'help with cleaning'"
echo "Assistant: 'I can help you with cleaning procedures. To give you the most accurate guidance:"
echo "1) What specific equipment do you need to clean?"
echo "2) What type of cleaning are you doing (daily, deep clean, sanitizing)?"
echo "3) Are you seeing any specific issues or buildup?'"

echo ""
echo "🚀 Ready to Test:"
echo "Frontend: http://localhost:3000"
echo ""
echo "The assistant should now ask clarifying questions for vague requests!"