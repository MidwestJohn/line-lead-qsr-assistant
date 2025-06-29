#!/usr/bin/env node

/**
 * 🔍 Comprehensive PDF Preview Debug Test
 * 
 * Tests and diagnoses PDF preview loading issues
 */

const https = require('https');
const fs = require('fs');

const BASE_URL = 'https://line-lead-qsr-backend.onrender.com';

console.log('🔍 COMPREHENSIVE PDF PREVIEW DEBUG TEST');
console.log('=======================================');
console.log(`Testing server: ${BASE_URL}`);
console.log('');

class PDFDebugTester {
    constructor() {
        this.results = {
            timestamp: new Date().toISOString(),
            serverHealth: null,
            documentList: null,
            fileAccessibility: {},
            pdfWorkerTest: null,
            corsConfiguration: null,
            performanceMetrics: {}
        };
    }

    async runAllTests() {
        console.log('🚀 Starting comprehensive PDF debug tests...');
        console.log('');

        try {
            await this.testServerHealth();
            await this.testDocumentList();
            await this.testFileAccessibility();
            await this.testPDFWorkerAccess();
            await this.testCORSConfiguration();
            await this.testFileServing();
            
            this.generateReport();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error);
        }
    }

    async testServerHealth() {
        console.log('🏥 TEST 1: Server Health Check');
        console.log('------------------------------');
        
        try {
            const result = await this.makeRequest('/health', 'GET');
            
            if (result.success) {
                this.results.serverHealth = {
                    status: 'healthy',
                    data: result.data,
                    responseTime: result.responseTime
                };
                
                console.log(`✅ Server healthy (${result.responseTime}ms)`);
                console.log(`   Status: ${result.data.status}`);
                console.log(`   Services: ${JSON.stringify(result.data.services)}`);
                console.log(`   Document count: ${result.data.document_count}`);
                
            } else {
                console.log(`❌ Server health check failed: ${result.error}`);
                this.results.serverHealth = { status: 'unhealthy', error: result.error };
            }
            
        } catch (error) {
            console.log(`❌ Server health test failed: ${error.message}`);
            this.results.serverHealth = { status: 'error', error: error.message };
        }
        
        console.log('');
    }

    async testDocumentList() {
        console.log('📋 TEST 2: Document List');
        console.log('------------------------');
        
        try {
            const result = await this.makeRequest('/documents', 'GET');
            
            if (result.success) {
                this.results.documentList = {
                    success: true,
                    documents: result.data.documents,
                    count: result.data.total_count,
                    responseTime: result.responseTime
                };
                
                console.log(`✅ Document list retrieved (${result.responseTime}ms)`);
                console.log(`   Total documents: ${result.data.total_count}`);
                
                if (result.data.documents.length > 0) {
                    console.log('   Available documents:');
                    result.data.documents.slice(0, 3).forEach(doc => {
                        console.log(`     - ${doc.original_filename} (${doc.file_size} bytes)`);
                        console.log(`       URL: ${doc.url}`);
                    });
                } else {
                    console.log('   ⚠️ No documents available for testing');
                }
                
            } else {
                console.log(`❌ Document list failed: ${result.error}`);
                this.results.documentList = { success: false, error: result.error };
            }
            
        } catch (error) {
            console.log(`❌ Document list test failed: ${error.message}`);
            this.results.documentList = { success: false, error: error.message };
        }
        
        console.log('');
    }

    async testFileAccessibility() {
        console.log('📄 TEST 3: File Accessibility');
        console.log('-----------------------------');
        
        if (!this.results.documentList?.success || !this.results.documentList.documents?.length) {
            console.log('⚠️ Skipping file accessibility test - no documents available');
            console.log('');
            return;
        }

        const testDocuments = this.results.documentList.documents.slice(0, 3);
        
        for (const doc of testDocuments) {
            try {
                console.log(`📋 Testing: ${doc.original_filename}`);
                const fileUrl = doc.url;
                
                const result = await this.testFileAccess(fileUrl);
                this.results.fileAccessibility[doc.filename] = result;
                
                if (result.accessible) {
                    console.log(`   ✅ File accessible (${result.responseTime}ms)`);
                    console.log(`   📊 Content-Type: ${result.contentType}`);
                    console.log(`   📊 Content-Length: ${result.contentLength}`);
                    console.log(`   📊 Content-Disposition: ${result.contentDisposition}`);
                    console.log(`   📊 CORS Headers: ${result.corsHeaders['Access-Control-Allow-Origin']}`);
                    
                    // Test actual PDF content
                    await this.testPDFContent(fileUrl, doc.original_filename);
                    
                } else {
                    console.log(`   ❌ File not accessible: ${result.status} ${result.statusText}`);
                }
                
            } catch (error) {
                console.log(`   ❌ File test error: ${error.message}`);
                this.results.fileAccessibility[doc.filename] = { accessible: false, error: error.message };
            }
            
            console.log('');
        }
    }

    async testPDFContent(fileUrl, filename) {
        try {
            console.log(`   🔍 Testing PDF content structure...`);
            
            // Get first few bytes to check PDF header
            const options = {
                hostname: 'line-lead-qsr-backend.onrender.com',
                path: fileUrl,
                method: 'GET',
                headers: {
                    'Range': 'bytes=0-10'
                }
            };

            const result = await new Promise((resolve, reject) => {
                const req = https.request(options, (res) => {
                    let data = '';
                    
                    res.on('data', chunk => data += chunk);
                    res.on('end', () => {
                        resolve({
                            status: res.statusCode,
                            headers: res.headers,
                            content: data
                        });
                    });
                });
                
                req.on('error', reject);
                req.setTimeout(5000, () => reject(new Error('Timeout')));
                req.end();
            });
            
            if (result.content.startsWith('%PDF-')) {
                console.log(`   ✅ Valid PDF header detected: ${result.content.substring(0, 8)}`);
            } else {
                console.log(`   ⚠️ Invalid PDF header: ${result.content.substring(0, 10)}`);
            }
            
        } catch (error) {
            console.log(`   ⚠️ PDF content test failed: ${error.message}`);
        }
    }

    async testPDFWorkerAccess() {
        console.log('⚙️ TEST 4: PDF.js Worker Accessibility');
        console.log('--------------------------------------');
        
        const workerUrls = [
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
            'https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js'
        ];

        const results = [];
        
        for (const url of workerUrls) {
            try {
                console.log(`📋 Testing worker: ${url}`);
                
                const result = await this.testExternalURL(url);
                results.push({ url, ...result });
                
                if (result.accessible) {
                    console.log(`   ✅ Worker accessible (${result.responseTime}ms)`);
                    console.log(`   📊 Size: ${result.contentLength || 'unknown'} bytes`);
                } else {
                    console.log(`   ❌ Worker not accessible: ${result.status}`);
                }
                
            } catch (error) {
                console.log(`   ❌ Worker test error: ${error.message}`);
                results.push({ url, accessible: false, error: error.message });
            }
        }
        
        this.results.pdfWorkerTest = {
            results,
            anyAccessible: results.some(r => r.accessible)
        };
        
        if (this.results.pdfWorkerTest.anyAccessible) {
            console.log(`✅ At least one PDF.js worker is accessible`);
        } else {
            console.log(`❌ No PDF.js workers are accessible - this will prevent PDF loading`);
        }
        
        console.log('');
    }

    async testCORSConfiguration() {
        console.log('🌐 TEST 5: CORS Configuration');
        console.log('-----------------------------');
        
        if (!this.results.documentList?.documents?.length) {
            console.log('⚠️ Skipping CORS test - no documents available');
            console.log('');
            return;
        }

        const doc = this.results.documentList.documents[0];
        const fileUrl = doc.url;
        
        try {
            console.log(`📋 Testing CORS for: ${doc.original_filename}`);
            
            // Test OPTIONS request
            const optionsResult = await this.makeRequest(fileUrl, 'OPTIONS');
            
            if (optionsResult.success) {
                console.log(`✅ OPTIONS request successful`);
            } else {
                console.log(`⚠️ OPTIONS request failed: ${optionsResult.error}`);
            }
            
            // Test file access with CORS
            const fileResult = await this.testFileAccess(fileUrl);
            
            const corsConfig = {
                optionsWorking: optionsResult.success,
                allowOrigin: fileResult.corsHeaders?.['Access-Control-Allow-Origin'],
                allowMethods: fileResult.corsHeaders?.['Access-Control-Allow-Methods'],
                exposeHeaders: fileResult.corsHeaders?.['Access-Control-Expose-Headers'],
                isConfigured: !!fileResult.corsHeaders?.['Access-Control-Allow-Origin']
            };
            
            this.results.corsConfiguration = corsConfig;
            
            if (corsConfig.isConfigured) {
                console.log(`✅ CORS properly configured`);
                console.log(`   Allow-Origin: ${corsConfig.allowOrigin}`);
                console.log(`   Allow-Methods: ${corsConfig.allowMethods}`);
                console.log(`   Expose-Headers: ${corsConfig.exposeHeaders}`);
            } else {
                console.log(`❌ CORS not configured - this may prevent PDF loading in browsers`);
            }
            
        } catch (error) {
            console.log(`❌ CORS test failed: ${error.message}`);
            this.results.corsConfiguration = { error: error.message };
        }
        
        console.log('');
    }

    async testFileServing() {
        console.log('🚀 TEST 6: File Serving Performance');
        console.log('-----------------------------------');
        
        if (!this.results.documentList?.documents?.length) {
            console.log('⚠️ Skipping performance test - no documents available');
            console.log('');
            return;
        }

        const doc = this.results.documentList.documents[0];
        const fileUrl = doc.url;
        
        try {
            console.log(`📋 Performance testing: ${doc.original_filename} (${doc.file_size} bytes)`);
            
            // Test range request
            const rangeResult = await this.testRangeRequest(fileUrl);
            
            // Test full download speed
            const speedResult = await this.testDownloadSpeed(fileUrl, doc.file_size);
            
            this.results.performanceMetrics = {
                rangeRequestSupported: rangeResult.supported,
                downloadSpeed: speedResult.speed,
                totalTime: speedResult.totalTime,
                fileSize: doc.file_size
            };
            
            console.log(`📊 Range requests: ${rangeResult.supported ? 'Supported' : 'Not supported'}`);
            console.log(`📊 Download speed: ${speedResult.speed.toFixed(2)} KB/s`);
            console.log(`📊 Total download time: ${speedResult.totalTime}ms`);
            
            if (speedResult.speed > 100) {
                console.log(`✅ Good download performance`);
            } else if (speedResult.speed > 50) {
                console.log(`⚠️ Moderate download performance`);
            } else {
                console.log(`❌ Poor download performance - may cause loading issues`);
            }
            
        } catch (error) {
            console.log(`❌ Performance test failed: ${error.message}`);
            this.results.performanceMetrics = { error: error.message };
        }
        
        console.log('');
    }

    // Helper methods
    async makeRequest(endpoint, method = 'GET') {
        return new Promise((resolve) => {
            const startTime = Date.now();
            
            const options = {
                hostname: 'line-lead-qsr-backend.onrender.com',
                path: endpoint,
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'PDFDebugTest/1.0'
                }
            };

            const req = https.request(options, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    const responseTime = Date.now() - startTime;
                    
                    try {
                        const parsedData = JSON.parse(data);
                        resolve({
                            success: res.statusCode >= 200 && res.statusCode < 300,
                            data: parsedData,
                            responseTime: responseTime,
                            statusCode: res.statusCode
                        });
                    } catch (e) {
                        resolve({
                            success: res.statusCode >= 200 && res.statusCode < 300,
                            data: data,
                            responseTime: responseTime,
                            statusCode: res.statusCode
                        });
                    }
                });
            });

            req.on('error', (err) => {
                const responseTime = Date.now() - startTime;
                resolve({
                    success: false,
                    error: err.message,
                    responseTime: responseTime
                });
            });

            req.setTimeout(10000, () => {
                req.destroy();
                resolve({
                    success: false,
                    error: 'Request timeout',
                    responseTime: 10000
                });
            });

            req.end();
        });
    }

    async testFileAccess(fileUrl) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            
            const options = {
                hostname: 'line-lead-qsr-backend.onrender.com',
                path: fileUrl,
                method: 'HEAD'
            };

            const req = https.request(options, (res) => {
                const responseTime = Date.now() - startTime;
                
                const corsHeaders = {
                    'Access-Control-Allow-Origin': res.headers['access-control-allow-origin'],
                    'Access-Control-Allow-Methods': res.headers['access-control-allow-methods'],
                    'Access-Control-Expose-Headers': res.headers['access-control-expose-headers']
                };
                
                resolve({
                    accessible: res.statusCode >= 200 && res.statusCode < 300,
                    status: res.statusCode,
                    statusText: res.statusMessage,
                    responseTime,
                    contentType: res.headers['content-type'],
                    contentLength: res.headers['content-length'],
                    contentDisposition: res.headers['content-disposition'],
                    corsHeaders
                });
            });

            req.on('error', (err) => {
                resolve({
                    accessible: false,
                    error: err.message,
                    responseTime: Date.now() - startTime
                });
            });

            req.setTimeout(10000, () => {
                req.destroy();
                resolve({
                    accessible: false,
                    error: 'Request timeout',
                    responseTime: 10000
                });
            });

            req.end();
        });
    }

    async testExternalURL(url) {
        const urlObj = new URL(url);
        
        return new Promise((resolve) => {
            const startTime = Date.now();
            
            const options = {
                hostname: urlObj.hostname,
                path: urlObj.pathname,
                method: 'HEAD',
                headers: {
                    'User-Agent': 'PDFDebugTest/1.0'
                }
            };

            const req = https.request(options, (res) => {
                const responseTime = Date.now() - startTime;
                
                resolve({
                    accessible: res.statusCode >= 200 && res.statusCode < 300,
                    status: res.statusCode,
                    responseTime,
                    contentLength: res.headers['content-length']
                });
            });

            req.on('error', (err) => {
                resolve({
                    accessible: false,
                    error: err.message,
                    responseTime: Date.now() - startTime
                });
            });

            req.setTimeout(5000, () => {
                req.destroy();
                resolve({
                    accessible: false,
                    error: 'Request timeout',
                    responseTime: 5000
                });
            });

            req.end();
        });
    }

    async testRangeRequest(fileUrl) {
        return new Promise((resolve) => {
            const options = {
                hostname: 'line-lead-qsr-backend.onrender.com',
                path: fileUrl,
                method: 'GET',
                headers: {
                    'Range': 'bytes=0-1023'
                }
            };

            const req = https.request(options, (res) => {
                resolve({
                    supported: res.statusCode === 206,
                    status: res.statusCode,
                    contentRange: res.headers['content-range']
                });
            });

            req.on('error', () => {
                resolve({ supported: false, error: 'Request failed' });
            });

            req.setTimeout(5000, () => {
                req.destroy();
                resolve({ supported: false, error: 'Timeout' });
            });

            req.end();
        });
    }

    async testDownloadSpeed(fileUrl, fileSize) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            let bytesReceived = 0;
            
            const options = {
                hostname: 'line-lead-qsr-backend.onrender.com',
                path: fileUrl,
                method: 'GET'
            };

            const req = https.request(options, (res) => {
                res.on('data', (chunk) => {
                    bytesReceived += chunk.length;
                });
                
                res.on('end', () => {
                    const totalTime = Date.now() - startTime;
                    const speed = (bytesReceived / 1024) / (totalTime / 1000);
                    
                    resolve({
                        speed,
                        totalTime,
                        bytesReceived
                    });
                });
            });

            req.on('error', () => {
                resolve({ speed: 0, totalTime: 0, error: 'Request failed' });
            });

            req.setTimeout(15000, () => {
                req.destroy();
                const totalTime = Date.now() - startTime;
                const speed = (bytesReceived / 1024) / (totalTime / 1000);
                resolve({ speed, totalTime, bytesReceived, timeout: true });
            });

            req.end();
        });
    }

    generateReport() {
        console.log('📊 COMPREHENSIVE PDF DEBUG REPORT');
        console.log('==================================');
        console.log('');

        // Overall status
        const issues = [];
        const warnings = [];
        const successes = [];

        // Server Health
        if (this.results.serverHealth?.status === 'healthy') {
            successes.push('✅ Server is healthy and responsive');
        } else {
            issues.push('❌ Server health issues detected');
        }

        // Document availability
        if (this.results.documentList?.success && this.results.documentList.count > 0) {
            successes.push(`✅ ${this.results.documentList.count} documents available`);
        } else {
            warnings.push('⚠️ No documents available for testing');
        }

        // File accessibility
        const accessibleFiles = Object.values(this.results.fileAccessibility).filter(f => f.accessible).length;
        const totalFiles = Object.keys(this.results.fileAccessibility).length;
        
        if (accessibleFiles === totalFiles && totalFiles > 0) {
            successes.push(`✅ All ${totalFiles} test files accessible`);
        } else if (accessibleFiles > 0) {
            warnings.push(`⚠️ Only ${accessibleFiles}/${totalFiles} files accessible`);
        } else if (totalFiles > 0) {
            issues.push('❌ No files accessible');
        }

        // PDF.js worker
        if (this.results.pdfWorkerTest?.anyAccessible) {
            successes.push('✅ PDF.js worker accessible');
        } else {
            issues.push('❌ PDF.js worker not accessible - critical issue');
        }

        // CORS configuration
        if (this.results.corsConfiguration?.isConfigured) {
            successes.push('✅ CORS properly configured');
        } else {
            issues.push('❌ CORS not configured - will prevent browser PDF loading');
        }

        // Performance
        if (this.results.performanceMetrics?.downloadSpeed > 100) {
            successes.push('✅ Good file serving performance');
        } else if (this.results.performanceMetrics?.downloadSpeed > 50) {
            warnings.push('⚠️ Moderate file serving performance');
        } else if (this.results.performanceMetrics?.downloadSpeed) {
            issues.push('❌ Poor file serving performance');
        }

        // Print results
        console.log('🎉 SUCCESSES:');
        if (successes.length > 0) {
            successes.forEach(s => console.log(`   ${s}`));
        } else {
            console.log('   None');
        }
        console.log('');

        console.log('⚠️ WARNINGS:');
        if (warnings.length > 0) {
            warnings.forEach(w => console.log(`   ${w}`));
        } else {
            console.log('   None');
        }
        console.log('');

        console.log('❌ CRITICAL ISSUES:');
        if (issues.length > 0) {
            issues.forEach(i => console.log(`   ${i}`));
        } else {
            console.log('   None');
        }
        console.log('');

        // Recommendations
        console.log('🔧 RECOMMENDATIONS:');
        
        if (issues.includes('❌ PDF.js worker not accessible - critical issue')) {
            console.log('   1. Add local PDF.js worker fallback to public folder');
            console.log('   2. Test alternative CDN sources for PDF.js worker');
        }
        
        if (issues.includes('❌ CORS not configured - will prevent browser PDF loading')) {
            console.log('   1. Add proper CORS headers to file serving endpoint');
            console.log('   2. Include Access-Control-Allow-Origin: * for development');
        }
        
        if (issues.some(i => i.includes('files accessible'))) {
            console.log('   1. Check backend file serving endpoint configuration');
            console.log('   2. Verify uploaded files exist in the uploads directory');
        }
        
        if (issues.some(i => i.includes('performance'))) {
            console.log('   1. Implement streaming file serving with range requests');
            console.log('   2. Add CDN or file optimization');
        }

        const overallScore = successes.length / (successes.length + warnings.length + issues.length);
        
        console.log('');
        console.log(`📊 OVERALL SCORE: ${(overallScore * 100).toFixed(1)}%`);
        
        if (overallScore > 0.8) {
            console.log('🎉 PDF preview should work well!');
        } else if (overallScore > 0.6) {
            console.log('⚠️ PDF preview may have issues - address warnings');
        } else {
            console.log('❌ PDF preview likely broken - fix critical issues');
        }

        console.log('');
        console.log('🏁 PDF debug testing complete!');
    }
}

// Run the comprehensive test
const tester = new PDFDebugTester();
tester.runAllTests().catch(console.error);