#!/bin/bash

echo "🍔 Line Lead QSR MVP - Real-World Demo Scenarios"
echo "=============================================="
echo ""

# Function to test a QSR question
test_qsr_question() {
    local question="$1"
    local scenario="$2"
    
    echo "🎯 Scenario: $scenario"
    echo "❓ Question: \"$question\""
    echo ""
    
    response=$(curl -s -X POST http://localhost:8000/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$question\"}")
    
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    response = data['response']
    
    if 'Based on your uploaded manuals:' in response:
        print('✅ FOUND RELEVANT MANUAL CONTENT')
        relevance_count = response.count('relevance:')
        print(f'📖 Retrieved {relevance_count} relevant text chunks')
        
        # Extract and display relevance scores
        import re
        scores = re.findall(r'relevance: (\d+\.\d+)', response)
        if scores:
            avg_score = sum(float(s) for s in scores) / len(scores)
            print(f'📊 Average relevance score: {avg_score:.2f}')
        
        # Display the response in a readable format
        print()
        print('📋 ASSISTANT RESPONSE:')
        print('-' * 50)
        
        # Split by manual sections for better readability
        sections = response.split('📖 From ')
        print(sections[0])  # Introduction
        
        for i, section in enumerate(sections[1:], 1):
            if section.strip():
                lines = section.split('\n')
                filename_line = lines[0]
                content_lines = [line for line in lines[1:] if line.strip() and not line.startswith('📖')]
                
                print(f'📖 Source {i}: {filename_line}')
                for line in content_lines[:3]:  # Show first 3 lines of content
                    if line.strip():
                        print(f'   {line.strip()}')
                print()
                
    else:
        print('❌ NO RELEVANT CONTENT FOUND')
        print('💬 Response:', response[:200] + '...' if len(response) > 200 else response)
        
except json.JSONDecodeError:
    print('❌ ERROR: Invalid JSON response')
except Exception as e:
    print(f'❌ ERROR: {e}')
"
    echo ""
    echo "=" * 60
    echo ""
}

# QSR Demo Scenarios
echo "Testing realistic QSR maintenance scenarios..."
echo ""

test_qsr_question "My fryer won't heat up and the oil stays cold" "Equipment Malfunction - Fryer"

test_qsr_question "How do I properly clean the grill at the end of the day?" "Daily Cleaning Procedure - Grill"

test_qsr_question "The oil in my fryer is bubbling and making strange noises" "Equipment Troubleshooting - Fryer"

test_qsr_question "What temperature should I keep the fryer at for french fries?" "Food Safety & Temperature Control"

test_qsr_question "How often should I replace the oil in the fryer?" "Maintenance Schedule - Fryer"

test_qsr_question "My grill has uneven heating, some areas are too hot and others too cold" "Equipment Issue - Grill Temperature"

test_qsr_question "What should I do if I smell gas near the grill?" "Safety Emergency - Gas Leak"

test_qsr_question "How do I know when the grill needs deep cleaning?" "Maintenance Recognition - Grill"

# Test an irrelevant question
test_qsr_question "What time does the restaurant open tomorrow?" "Irrelevant Question Test"

echo "🎉 Demo Complete!"
echo ""
echo "📊 SEARCH ENGINE STATS:"
curl -s http://localhost:8000/search-stats | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'📚 Total Documents: {data[\"total_documents\"]}')
print(f'📄 Total Text Chunks: {data[\"total_chunks\"]}')
print(f'🤖 AI Model: {data[\"model_name\"]}')
"
echo ""
echo "🚀 System Status: OPERATIONAL"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000/docs"