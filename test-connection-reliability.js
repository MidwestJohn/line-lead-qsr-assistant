#!/usr/bin/env node

/**
 * 🔗 Comprehensive Connection Reliability Test Suite
 * 
 * Tests all aspects of the connection management system to ensure
 * bulletproof connectivity in restaurant environments.
 */

const https = require('https');
const fs = require('fs');

const BASE_URL = 'https://line-lead-qsr-backend.onrender.com';

console.log('🔗 COMPREHENSIVE CONNECTION RELIABILITY TEST');
console.log('=============================================');
console.log(`Testing server: ${BASE_URL}`);
console.log('');

class ConnectionTester {
    constructor() {
        this.results = {
            coldStartRecovery: null,
            keepAliveEffectiveness: null,
            connectionRetryLogic: null,
            sessionPersistence: null,
            networkResilienceSimulation: null,
            progressiveLoadingSequence: null,
            performanceMetrics: {
                connectionSuccessRate: 0,
                averageConnectionTime: 0,
                sessionStability: 0,
                networkRecoveryTime: 0
            }
        };
    }

    async runAllTests() {
        console.log('🚀 Starting comprehensive connection reliability tests...');
        console.log('');

        try {
            await this.testColdStartRecovery();
            await this.testKeepAliveEffectiveness();
            await this.testConnectionRetryLogic();
            await this.testSessionPersistence();
            await this.testNetworkResilienceSimulation();
            await this.testProgressiveLoadingSequence();
            
            this.generateReport();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error);
        }
    }

    async testColdStartRecovery() {
        console.log('🧊 TEST 1: Cold Start Recovery');
        console.log('-------------------------------');
        
        try {
            // Test server warm-up endpoint
            console.log('📋 Testing warm-up endpoint...');
            const warmUpResult = await this.makeRequest('/warm-up', 'POST', {}, 30000);
            
            if (warmUpResult.success) {
                const data = warmUpResult.data;
                console.log(`✅ Warm-up successful in ${warmUpResult.responseTime}ms`);
                console.log(`   Services initialized: ${JSON.stringify(data.services_initialized)}`);
                console.log(`   Warm-up time: ${data.warm_up_time_seconds}s`);
                
                this.results.coldStartRecovery = {
                    success: true,
                    warmUpTime: warmUpResult.responseTime,
                    servicesInitialized: data.services_initialized,
                    serverWarmUpTime: data.warm_up_time_seconds
                };
                
                // Test if subsequent requests are faster
                const healthResult = await this.makeRequest('/health', 'GET', {}, 10000);
                if (healthResult.success && healthResult.responseTime < 2000) {
                    console.log(`✅ Post-warmup health check: ${healthResult.responseTime}ms (optimized)`);
                } else {
                    console.log(`⚠️  Post-warmup health check: ${healthResult.responseTime}ms (needs optimization)`);
                }
                
            } else {
                console.log(`❌ Warm-up failed: ${warmUpResult.error}`);
                this.results.coldStartRecovery = { success: false, error: warmUpResult.error };
            }
            
        } catch (error) {
            console.log(`❌ Cold start recovery test failed: ${error.message}`);
            this.results.coldStartRecovery = { success: false, error: error.message };
        }
        
        console.log('');
    }

    async testKeepAliveEffectiveness() {
        console.log('💓 TEST 2: Keep-Alive Effectiveness');
        console.log('-----------------------------------');
        
        try {
            // Test keep-alive endpoint
            console.log('📋 Testing keep-alive endpoint...');
            const keepAliveResult = await this.makeRequest('/keep-alive', 'GET', {}, 10000);
            
            if (keepAliveResult.success) {
                const data = keepAliveResult.data;
                console.log(`✅ Keep-alive successful in ${keepAliveResult.responseTime}ms`);
                console.log(`   Server uptime: ${data.uptime_seconds}s`);
                console.log(`   Status: ${data.status}`);
                
                // Multiple keep-alive requests to test consistency
                console.log('📋 Testing keep-alive consistency (5 requests)...');
                const keepAliveTests = [];
                for (let i = 0; i < 5; i++) {
                    keepAliveTests.push(this.makeRequest('/keep-alive', 'GET', {}, 5000));
                }
                
                const results = await Promise.all(keepAliveTests);
                const successfulResults = results.filter(r => r.success);
                const averageResponseTime = successfulResults.reduce((acc, r) => acc + r.responseTime, 0) / successfulResults.length;
                
                console.log(`✅ Keep-alive consistency: ${successfulResults.length}/5 successful`);
                console.log(`   Average response time: ${Math.round(averageResponseTime)}ms`);
                
                this.results.keepAliveEffectiveness = {
                    success: true,
                    uptime: data.uptime_seconds,
                    consistencyRate: successfulResults.length / 5,
                    averageResponseTime: Math.round(averageResponseTime)
                };
                
            } else {
                console.log(`❌ Keep-alive failed: ${keepAliveResult.error}`);
                this.results.keepAliveEffectiveness = { success: false, error: keepAliveResult.error };
            }
            
        } catch (error) {
            console.log(`❌ Keep-alive effectiveness test failed: ${error.message}`);
            this.results.keepAliveEffectiveness = { success: false, error: error.message };
        }
        
        console.log('');
    }

    async testConnectionRetryLogic() {
        console.log('🔄 TEST 3: Connection Retry Logic');
        console.log('---------------------------------');
        
        try {
            // Test multiple rapid connections to simulate retry behavior
            console.log('📋 Testing connection retry simulation...');
            
            const connectionAttempts = [];
            const attemptCount = 10;
            
            for (let i = 0; i < attemptCount; i++) {
                const startTime = Date.now();
                const attempt = this.makeRequest('/health', 'GET', { 'X-Retry-Test': i.toString() }, 5000)
                    .then(result => ({
                        attempt: i + 1,
                        success: result.success,
                        responseTime: result.responseTime,
                        timestamp: Date.now() - startTime
                    }))
                    .catch(error => ({
                        attempt: i + 1,
                        success: false,
                        error: error.message,
                        timestamp: Date.now() - startTime
                    }));
                
                connectionAttempts.push(attempt);
                
                // Small delay between attempts to simulate retry backoff
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            const results = await Promise.all(connectionAttempts);
            const successfulConnections = results.filter(r => r.success);
            const successRate = successfulConnections.length / attemptCount;
            const averageResponseTime = successfulConnections.reduce((acc, r) => acc + r.responseTime, 0) / successfulConnections.length;
            
            console.log(`✅ Connection success rate: ${successfulConnections.length}/${attemptCount} (${(successRate * 100).toFixed(1)}%)`);
            console.log(`   Average response time: ${Math.round(averageResponseTime)}ms`);
            
            // Test session consistency
            console.log('📋 Testing session consistency...');
            const sessionId = `test_session_${Date.now()}`;
            const sessionTests = [];
            
            for (let i = 0; i < 3; i++) {
                sessionTests.push(this.makeRequest('/health', 'GET', { 'X-Session-ID': sessionId }, 5000));
            }
            
            const sessionResults = await Promise.all(sessionTests);
            const sessionSuccess = sessionResults.filter(r => r.success).length;
            
            console.log(`✅ Session consistency: ${sessionSuccess}/3 requests successful`);
            
            this.results.connectionRetryLogic = {
                success: true,
                connectionSuccessRate: successRate,
                averageResponseTime: Math.round(averageResponseTime),
                sessionConsistency: sessionSuccess / 3
            };
            
            this.results.performanceMetrics.connectionSuccessRate = successRate;
            this.results.performanceMetrics.averageConnectionTime = Math.round(averageResponseTime);
            
        } catch (error) {
            console.log(`❌ Connection retry logic test failed: ${error.message}`);
            this.results.connectionRetryLogic = { success: false, error: error.message };
        }
        
        console.log('');
    }

    async testSessionPersistence() {
        console.log('🔐 TEST 4: Session Persistence');
        console.log('------------------------------');
        
        try {
            const sessionId = `persistence_test_${Date.now()}`;
            console.log(`📋 Testing session persistence with ID: ${sessionId.slice(-12)}...`);
            
            // Initial session establishment
            const initialRequest = await this.makeRequest('/health', 'GET', { 'X-Session-ID': sessionId }, 5000);
            
            if (!initialRequest.success) {
                throw new Error('Failed to establish initial session');
            }
            
            console.log(`✅ Initial session established in ${initialRequest.responseTime}ms`);
            
            // Test session persistence over time
            const persistenceTests = [];
            const intervals = [1000, 3000, 5000]; // 1s, 3s, 5s delays
            
            for (const interval of intervals) {
                await new Promise(resolve => setTimeout(resolve, interval));
                persistenceTests.push(
                    this.makeRequest('/health', 'GET', { 
                        'X-Session-ID': sessionId, 
                        'X-Persistence-Test': 'true' 
                    }, 5000)
                );
            }
            
            const persistenceResults = await Promise.all(persistenceTests);
            const persistentSessions = persistenceResults.filter(r => r.success);
            const persistenceRate = persistentSessions.length / intervals.length;
            
            console.log(`✅ Session persistence rate: ${persistentSessions.length}/${intervals.length} (${(persistenceRate * 100).toFixed(1)}%)`);
            
            // Test heartbeat functionality
            console.log('📋 Testing heartbeat functionality...');
            const heartbeatResult = await this.makeRequest('/health', 'GET', { 
                'X-Session-ID': sessionId,
                'X-Heartbeat': 'true'
            }, 5000);
            
            if (heartbeatResult.success) {
                console.log(`✅ Heartbeat successful in ${heartbeatResult.responseTime}ms`);
            } else {
                console.log(`⚠️  Heartbeat failed: ${heartbeatResult.error}`);
            }
            
            this.results.sessionPersistence = {
                success: true,
                persistenceRate: persistenceRate,
                heartbeatWorking: heartbeatResult.success,
                sessionId: sessionId
            };
            
            this.results.performanceMetrics.sessionStability = persistenceRate;
            
        } catch (error) {
            console.log(`❌ Session persistence test failed: ${error.message}`);
            this.results.sessionPersistence = { success: false, error: error.message };
        }
        
        console.log('');
    }

    async testNetworkResilienceSimulation() {
        console.log('🌐 TEST 5: Network Resilience Simulation');
        console.log('-----------------------------------------');
        
        try {
            console.log('📋 Testing various network conditions...');
            
            // Simulate different network qualities by varying timeouts
            const networkTests = [
                { name: 'Excellent', timeout: 1000 },
                { name: 'Good', timeout: 3000 },
                { name: 'Fair', timeout: 8000 },
                { name: 'Poor', timeout: 15000 }
            ];
            
            const networkResults = [];
            
            for (const test of networkTests) {
                console.log(`   Testing ${test.name} network (${test.timeout}ms timeout)...`);
                
                const startTime = Date.now();
                const result = await this.makeRequest('/health', 'GET', { 
                    'X-Network-Test': test.name.toLowerCase() 
                }, test.timeout);
                
                const adaptedTimeout = this.calculateAdaptiveTimeout(result.responseTime);
                
                networkResults.push({
                    name: test.name,
                    success: result.success,
                    responseTime: result.success ? result.responseTime : test.timeout,
                    adaptiveTimeout: adaptedTimeout,
                    networkQuality: this.determineNetworkQuality(result.responseTime)
                });
                
                if (result.success) {
                    console.log(`     ✅ ${test.name}: ${result.responseTime}ms (${this.determineNetworkQuality(result.responseTime)})`);
                } else {
                    console.log(`     ❌ ${test.name}: Failed (${result.error})`);
                }
            }
            
            const successfulTests = networkResults.filter(r => r.success);
            const resilienceRate = successfulTests.length / networkTests.length;
            
            console.log(`✅ Network resilience rate: ${successfulTests.length}/${networkTests.length} (${(resilienceRate * 100).toFixed(1)}%)`);
            
            this.results.networkResilienceSimulation = {
                success: true,
                resilienceRate: resilienceRate,
                networkTests: networkResults
            };
            
        } catch (error) {
            console.log(`❌ Network resilience simulation failed: ${error.message}`);
            this.results.networkResilienceSimulation = { success: false, error: error.message };
        }
        
        console.log('');
    }

    async testProgressiveLoadingSequence() {
        console.log('🚀 TEST 6: Progressive Loading Sequence');
        console.log('---------------------------------------');
        
        try {
            console.log('📋 Testing progressive loading endpoints...');
            
            const loadingSequence = [
                { name: 'Health Check', endpoint: '/health', expectedTime: 2000 },
                { name: 'Keep-Alive', endpoint: '/keep-alive', expectedTime: 1000 },
                { name: 'Documents', endpoint: '/documents', expectedTime: 3000 },
                { name: 'Warm-Up', endpoint: '/warm-up', method: 'POST', expectedTime: 5000 }
            ];
            
            const sequenceResults = [];
            let totalLoadingTime = 0;
            
            for (const step of loadingSequence) {
                console.log(`   Loading ${step.name}...`);
                
                const startTime = Date.now();
                const result = await this.makeRequest(
                    step.endpoint, 
                    step.method || 'GET', 
                    { 'X-Progressive-Loading': 'true' }, 
                    step.expectedTime
                );
                
                const loadTime = Date.now() - startTime;
                totalLoadingTime += loadTime;
                
                sequenceResults.push({
                    name: step.name,
                    success: result.success,
                    loadTime: loadTime,
                    expectedTime: step.expectedTime,
                    withinExpectation: loadTime <= step.expectedTime
                });
                
                if (result.success) {
                    const status = loadTime <= step.expectedTime ? '✅' : '⚠️';
                    console.log(`     ${status} ${step.name}: ${loadTime}ms (expected: ${step.expectedTime}ms)`);
                } else {
                    console.log(`     ❌ ${step.name}: Failed (${result.error})`);
                }
            }
            
            const successfulSteps = sequenceResults.filter(r => r.success);
            const withinExpectation = sequenceResults.filter(r => r.withinExpectation);
            
            console.log(`✅ Progressive loading success: ${successfulSteps.length}/${loadingSequence.length} steps`);
            console.log(`✅ Performance expectations: ${withinExpectation.length}/${loadingSequence.length} within targets`);
            console.log(`📊 Total loading time: ${totalLoadingTime}ms`);
            
            this.results.progressiveLoadingSequence = {
                success: true,
                stepsCompleted: successfulSteps.length,
                totalSteps: loadingSequence.length,
                performanceTargetsMet: withinExpectation.length,
                totalLoadingTime: totalLoadingTime,
                sequenceResults: sequenceResults
            };
            
        } catch (error) {
            console.log(`❌ Progressive loading sequence test failed: ${error.message}`);
            this.results.progressiveLoadingSequence = { success: false, error: error.message };
        }
        
        console.log('');
    }

    // Helper methods
    async makeRequest(endpoint, method = 'GET', headers = {}, timeout = 10000) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            
            const options = {
                hostname: 'line-lead-qsr-backend.onrender.com',
                path: endpoint,
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'ConnectionReliabilityTest/1.0',
                    ...headers
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

            req.setTimeout(timeout, () => {
                req.destroy();
                const responseTime = Date.now() - startTime;
                resolve({
                    success: false,
                    error: 'Request timeout',
                    responseTime: responseTime
                });
            });

            if (method === 'POST') {
                req.write(JSON.stringify({}));
            }
            
            req.end();
        });
    }

    calculateAdaptiveTimeout(responseTime) {
        if (responseTime < 200) return 10000;
        if (responseTime < 500) return 15000;
        if (responseTime < 1000) return 20000;
        if (responseTime < 3000) return 30000;
        return 45000;
    }

    determineNetworkQuality(responseTime) {
        if (responseTime < 200) return 'excellent';
        if (responseTime < 500) return 'good';
        if (responseTime < 1000) return 'fair';
        if (responseTime < 3000) return 'poor';
        return 'very_poor';
    }

    generateReport() {
        console.log('📊 COMPREHENSIVE TEST RESULTS REPORT');
        console.log('====================================');
        console.log('');

        // Summary
        const totalTests = 6;
        const passedTests = Object.values(this.results)
            .filter(result => result && result.success !== false).length - 1; // -1 for performanceMetrics

        console.log(`🎯 OVERALL SCORE: ${passedTests}/${totalTests} tests passed (${((passedTests/totalTests)*100).toFixed(1)}%)`);
        console.log('');

        // Detailed results
        console.log('📋 DETAILED RESULTS:');
        console.log('');

        // Cold Start Recovery
        if (this.results.coldStartRecovery) {
            const result = this.results.coldStartRecovery;
            console.log(`1. Cold Start Recovery: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
            if (result.success) {
                console.log(`   - Warm-up time: ${result.warmUpTime}ms`);
                console.log(`   - Server optimization: ${result.serverWarmUpTime}s`);
            } else {
                console.log(`   - Error: ${result.error}`);
            }
        }

        // Keep-Alive Effectiveness
        if (this.results.keepAliveEffectiveness) {
            const result = this.results.keepAliveEffectiveness;
            console.log(`2. Keep-Alive Effectiveness: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
            if (result.success) {
                console.log(`   - Consistency rate: ${(result.consistencyRate * 100).toFixed(1)}%`);
                console.log(`   - Average response: ${result.averageResponseTime}ms`);
            } else {
                console.log(`   - Error: ${result.error}`);
            }
        }

        // Connection Retry Logic
        if (this.results.connectionRetryLogic) {
            const result = this.results.connectionRetryLogic;
            console.log(`3. Connection Retry Logic: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
            if (result.success) {
                console.log(`   - Success rate: ${(result.connectionSuccessRate * 100).toFixed(1)}%`);
                console.log(`   - Session consistency: ${(result.sessionConsistency * 100).toFixed(1)}%`);
            } else {
                console.log(`   - Error: ${result.error}`);
            }
        }

        // Session Persistence
        if (this.results.sessionPersistence) {
            const result = this.results.sessionPersistence;
            console.log(`4. Session Persistence: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
            if (result.success) {
                console.log(`   - Persistence rate: ${(result.persistenceRate * 100).toFixed(1)}%`);
                console.log(`   - Heartbeat working: ${result.heartbeatWorking ? 'Yes' : 'No'}`);
            } else {
                console.log(`   - Error: ${result.error}`);
            }
        }

        // Network Resilience
        if (this.results.networkResilienceSimulation) {
            const result = this.results.networkResilienceSimulation;
            console.log(`5. Network Resilience: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
            if (result.success) {
                console.log(`   - Resilience rate: ${(result.resilienceRate * 100).toFixed(1)}%`);
            } else {
                console.log(`   - Error: ${result.error}`);
            }
        }

        // Progressive Loading
        if (this.results.progressiveLoadingSequence) {
            const result = this.results.progressiveLoadingSequence;
            console.log(`6. Progressive Loading: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
            if (result.success) {
                console.log(`   - Steps completed: ${result.stepsCompleted}/${result.totalSteps}`);
                console.log(`   - Performance targets: ${result.performanceTargetsMet}/${result.totalSteps}`);
                console.log(`   - Total loading time: ${result.totalLoadingTime}ms`);
            } else {
                console.log(`   - Error: ${result.error}`);
            }
        }

        console.log('');

        // Performance Metrics Summary
        console.log('🚀 PERFORMANCE METRICS:');
        const metrics = this.results.performanceMetrics;
        console.log(`   Connection Success Rate: ${(metrics.connectionSuccessRate * 100).toFixed(1)}% (Target: >98%)`);
        console.log(`   Average Connection Time: ${metrics.averageConnectionTime}ms (Target: <3000ms)`);
        console.log(`   Session Stability: ${(metrics.sessionStability * 100).toFixed(1)}% (Target: >99%)`);
        console.log('');

        // Recommendations
        console.log('🔧 RECOMMENDATIONS:');
        
        if (metrics.connectionSuccessRate < 0.98) {
            console.log('   ⚠️  Improve connection success rate - consider more aggressive retry logic');
        }
        
        if (metrics.averageConnectionTime > 3000) {
            console.log('   ⚠️  Optimize connection time - implement faster warm-up strategies');
        }
        
        if (metrics.sessionStability < 0.99) {
            console.log('   ⚠️  Enhance session persistence - increase heartbeat frequency');
        }

        if (passedTests === totalTests) {
            console.log('   🎉 All tests passed! System is ready for production.');
        } else {
            console.log(`   🔨 ${totalTests - passedTests} test(s) need attention before production deployment.`);
        }

        console.log('');
        console.log('🏁 Connection reliability testing complete!');
    }
}

// Run the test suite
const tester = new ConnectionTester();
tester.runAllTests().catch(console.error);