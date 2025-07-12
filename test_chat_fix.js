// Test script to verify chat API is working
// Run with: node test_chat_fix.js

const fetch = require('node-fetch');

async function testChatAPI() {
    console.log('🔍 Testing Chat API after CORS fix...\n');
    
    const API_BASE = 'http://localhost:8000';
    const tests = [
        {
            name: 'Health Check',
            method: 'GET',
            endpoint: '/health',
            data: null
        },
        {
            name: 'Regular Chat',
            method: 'POST',
            endpoint: '/chat',
            data: { message: 'How do I start the grill?' }
        },
        {
            name: 'Streaming Chat',
            method: 'POST',
            endpoint: '/chat/stream',
            data: { message: 'What are grill safety procedures?' }
        }
    ];
    
    for (const test of tests) {
        try {
            console.log(`\n📤 Testing: ${test.name}`);
            console.log(`   Endpoint: ${test.method} ${test.endpoint}`);
            
            const options = {
                method: test.method,
                headers: {
                    'Content-Type': 'application/json',
                    'Origin': 'http://localhost:3000'  // Simulate frontend origin
                }
            };
            
            if (test.data) {
                options.body = JSON.stringify(test.data);
            }
            
            const startTime = Date.now();
            const response = await fetch(`${API_BASE}${test.endpoint}`, options);
            const responseTime = Date.now() - startTime;
            
            if (!response.ok) {
                console.log(`   ❌ Failed: ${response.status} ${response.statusText}`);
                continue;
            }
            
            const data = await response.json();
            console.log(`   ✅ Success: ${response.status} (${responseTime}ms)`);
            
            if (test.endpoint === '/health') {
                console.log(`   📊 Status: ${data.status}, Documents: ${data.document_count}`);
            } else if (data.response) {
                const preview = data.response.substring(0, 100) + (data.response.length > 100 ? '...' : '');
                console.log(`   💬 Response: ${preview}`);
                console.log(`   🔍 Method: ${data.retrieval_method}`);
                
                if (data.manual_references && data.manual_references.length > 0) {
                    console.log(`   📚 References: ${data.manual_references.length} sources`);
                }
            }
            
        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
        }
    }
    
    console.log('\n🎯 Test Summary:');
    console.log('   If all tests show ✅ Success, the CORS fix worked!');
    console.log('   The frontend should now be able to send chat messages.');
}

// Run the test
testChatAPI().catch(console.error);