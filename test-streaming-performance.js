#!/usr/bin/env node

/**
 * 📊 PDF Streaming Performance Test
 * Tests the optimized file serving endpoint for performance improvements
 */

const https = require('https');
const fs = require('fs');

const BASE_URL = 'https://line-lead-qsr-backend.onrender.com';
const TEST_FILENAME = 'd000a756-acdd-46a1-b7e1-1b0b0548e754_HhC-Owners-Manual-English.pdf';  // 8.3MB file

console.log('🚀 PDF STREAMING PERFORMANCE TEST');
console.log('=====================================');
console.log(`Testing: ${BASE_URL}/files/${TEST_FILENAME}`);
console.log('');

// Test 1: Check if range requests are supported
function testRangeSupport() {
    return new Promise((resolve, reject) => {
        console.log('📡 Test 1: Range Request Support');
        
        const options = {
            hostname: 'line-lead-qsr-backend.onrender.com',
            path: `/files/${TEST_FILENAME}`,
            method: 'HEAD',
            headers: {
                'Range': 'bytes=0-1023'  // Request first 1KB
            }
        };

        const req = https.request(options, (res) => {
            console.log(`   Status: ${res.statusCode}`);
            console.log(`   Accept-Ranges: ${res.headers['accept-ranges'] || 'not set'}`);
            console.log(`   Content-Range: ${res.headers['content-range'] || 'not set'}`);
            console.log(`   Content-Length: ${res.headers['content-length'] || 'not set'}`);
            
            if (res.statusCode === 206 && res.headers['accept-ranges'] === 'bytes') {
                console.log('   ✅ Range requests supported!');
                resolve(true);
            } else if (res.statusCode === 200) {
                console.log('   ⚠️  Range requests not supported, but file accessible');
                resolve(false);
            } else {
                console.log('   ❌ File not accessible');
                resolve(false);
            }
        });

        req.on('error', (err) => {
            console.log(`   ❌ Error: ${err.message}`);
            resolve(false);
        });

        req.setTimeout(10000, () => {
            console.log('   ❌ Request timeout');
            resolve(false);
        });

        req.end();
    });
}

// Test 2: Measure streaming performance
function testStreamingPerformance() {
    return new Promise((resolve, reject) => {
        console.log('');
        console.log('⚡ Test 2: Streaming Performance');
        
        const startTime = Date.now();
        let firstByteTime = null;
        let bytesReceived = 0;
        
        const options = {
            hostname: 'line-lead-qsr-backend.onrender.com',
            path: `/files/${TEST_FILENAME}`,
            method: 'GET'
        };

        const req = https.request(options, (res) => {
            console.log(`   Status: ${res.statusCode}`);
            console.log(`   Content-Type: ${res.headers['content-type']}`);
            console.log(`   Content-Length: ${res.headers['content-length'] || 'chunked'}`);
            
            res.on('data', (chunk) => {
                if (!firstByteTime) {
                    firstByteTime = Date.now();
                    const ttfb = firstByteTime - startTime;
                    console.log(`   📈 Time to First Byte: ${ttfb}ms`);
                }
                
                bytesReceived += chunk.length;
                
                // Log progress every 100KB
                if (bytesReceived % (100 * 1024) === 0 || bytesReceived < 100 * 1024) {
                    const elapsed = Date.now() - startTime;
                    const speed = (bytesReceived / 1024 / (elapsed / 1000)).toFixed(2);
                    console.log(`   📊 Progress: ${(bytesReceived / 1024).toFixed(1)}KB in ${elapsed}ms (${speed} KB/s)`);
                }
            });

            res.on('end', () => {
                const totalTime = Date.now() - startTime;
                const avgSpeed = (bytesReceived / 1024 / (totalTime / 1000)).toFixed(2);
                
                console.log(`   ✅ Download complete!`);
                console.log(`   📊 Total: ${(bytesReceived / 1024).toFixed(1)}KB in ${totalTime}ms`);
                console.log(`   📊 Average speed: ${avgSpeed} KB/s`);
                
                // Performance evaluation
                if (firstByteTime && (firstByteTime - startTime) < 3000) {
                    console.log('   🎉 EXCELLENT: Fast initial response!');
                } else if (firstByteTime && (firstByteTime - startTime) < 10000) {
                    console.log('   ✅ GOOD: Acceptable initial response');
                } else {
                    console.log('   ⚠️  SLOW: Long time to first byte');
                }
                
                resolve({
                    success: true,
                    ttfb: firstByteTime ? firstByteTime - startTime : null,
                    totalTime,
                    bytesReceived,
                    avgSpeed: parseFloat(avgSpeed)
                });
            });
        });

        req.on('error', (err) => {
            console.log(`   ❌ Error: ${err.message}`);
            resolve({ success: false, error: err.message });
        });

        req.setTimeout(60000, () => {
            console.log('   ❌ Request timeout (60s)');
            resolve({ success: false, error: 'timeout' });
        });

        req.end();
    });
}

// Test 3: Check caching headers
function testCachingHeaders() {
    return new Promise((resolve, reject) => {
        console.log('');
        console.log('🗂️  Test 3: Caching Headers');
        
        const options = {
            hostname: 'line-lead-qsr-backend.onrender.com',
            path: `/files/${TEST_FILENAME}`,
            method: 'HEAD'
        };

        const req = https.request(options, (res) => {
            console.log(`   Cache-Control: ${res.headers['cache-control'] || 'not set'}`);
            console.log(`   ETag: ${res.headers['etag'] || 'not set'}`);
            console.log(`   Last-Modified: ${res.headers['last-modified'] || 'not set'}`);
            
            const hasCaching = res.headers['cache-control'] || res.headers['etag'];
            if (hasCaching) {
                console.log('   ✅ Caching headers present');
                resolve(true);
            } else {
                console.log('   ⚠️  No caching headers');
                resolve(false);
            }
        });

        req.on('error', (err) => {
            console.log(`   ❌ Error: ${err.message}`);
            resolve(false);
        });

        req.setTimeout(10000, () => {
            console.log('   ❌ Request timeout');
            resolve(false);
        });

        req.end();
    });
}

// Run all tests
async function runTests() {
    try {
        const rangeSupport = await testRangeSupport();
        const performance = await testStreamingPerformance();
        const caching = await testCachingHeaders();
        
        console.log('');
        console.log('📋 SUMMARY');
        console.log('==========');
        console.log(`Range Requests: ${rangeSupport ? '✅ Supported' : '❌ Not supported'}`);
        console.log(`Performance: ${performance.success ? '✅ Working' : '❌ Failed'}`);
        console.log(`Caching: ${caching ? '✅ Enabled' : '❌ Disabled'}`);
        
        if (performance.success) {
            console.log(`Time to First Byte: ${performance.ttfb}ms`);
            console.log(`Average Speed: ${performance.avgSpeed} KB/s`);
            
            // Performance scoring
            let score = 0;
            if (performance.ttfb < 3000) score += 3;
            else if (performance.ttfb < 10000) score += 2;
            else score += 1;
            
            if (performance.avgSpeed > 100) score += 2;
            else if (performance.avgSpeed > 50) score += 1;
            
            if (rangeSupport) score += 2;
            if (caching) score += 1;
            
            console.log('');
            console.log(`📊 Performance Score: ${score}/8`);
            if (score >= 7) console.log('🎉 EXCELLENT performance!');
            else if (score >= 5) console.log('✅ GOOD performance');
            else if (score >= 3) console.log('⚠️  FAIR performance');
            else console.log('❌ POOR performance - needs optimization');
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    }
}

// Start tests
runTests();