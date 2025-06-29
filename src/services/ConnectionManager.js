/**
 * 🔗 Comprehensive Connection Management System
 * 
 * Handles all server connectivity, session persistence, and network resilience
 * for reliable operation in restaurant environments with poor network conditions.
 */

class ConnectionManager {
    constructor() {
        this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        this.connectionState = 'disconnected'; // disconnected, connecting, connected, reconnecting
        this.networkQuality = 'unknown'; // unknown, poor, fair, good, excellent
        this.lastHealthCheck = null;
        this.sessionId = this.generateSessionId();
        this.listeners = new Set();
        this.requestQueue = [];
        this.connectionAttempts = 0;
        this.maxRetries = 5;
        this.retryDelays = [100, 500, 1000, 3000, 8000]; // Exponential backoff
        
        // Keep-alive and monitoring
        this.healthCheckInterval = null;
        this.keepAliveInterval = null;
        this.connectionTimeout = 15000; // 15 seconds initial timeout
        this.adaptiveTimeout = 15000;
        
        // Session state
        this.sessionData = this.loadSessionFromStorage();
        this.heartbeatInterval = null;
        this.lastActivity = Date.now();
        
        // Network monitoring
        this.onlineHandler = this.handleOnlineStateChange.bind(this);
        this.offlineHandler = this.handleOfflineStateChange.bind(this);
        
        this.initializeConnection();
        this.setupEventListeners();
        this.startPeriodicHealthChecks();
    }

    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    initializeConnection() {
        console.log('🔄 Initializing connection manager...');
        this.setState('connecting');
        this.attemptConnection();
    }

    async attemptConnection(retryAttempt = 0) {
        try {
            console.log(`🔗 Connection attempt ${retryAttempt + 1}/${this.maxRetries + 1}`);
            
            // Pre-connection server ping
            const pingSuccess = await this.pingServer();
            if (!pingSuccess && retryAttempt < this.maxRetries) {
                await this.retryWithBackoff(retryAttempt);
                return;
            }

            // Warm up server if cold
            await this.warmUpServer();
            
            // Verify full health
            const healthCheck = await this.performHealthCheck();
            if (healthCheck.success) {
                this.onConnectionSuccess();
                this.connectionAttempts = 0;
            } else {
                throw new Error('Health check failed after ping success');
            }
            
        } catch (error) {
            console.error(`❌ Connection attempt ${retryAttempt + 1} failed:`, error.message);
            
            if (retryAttempt < this.maxRetries) {
                await this.retryWithBackoff(retryAttempt);
            } else {
                this.onConnectionFailure(error);
            }
        }
    }

    async retryWithBackoff(retryAttempt) {
        const delay = this.retryDelays[retryAttempt] || 8000;
        console.log(`⏳ Retrying connection in ${delay}ms...`);
        
        this.notifyListeners('retrying', { 
            attempt: retryAttempt + 1, 
            maxAttempts: this.maxRetries + 1,
            delay 
        });
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.attemptConnection(retryAttempt + 1);
    }

    async pingServer() {
        try {
            console.log('🏓 Pinging server...');
            const startTime = Date.now();
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s ping timeout
            
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Cache-Control': 'no-cache',
                    'X-Session-ID': this.sessionId
                }
            });
            
            clearTimeout(timeoutId);
            const pingTime = Date.now() - startTime;
            
            if (response.ok) {
                this.updateNetworkQuality(pingTime);
                console.log(`✅ Server ping successful (${pingTime}ms)`);
                return true;
            } else {
                console.log(`⚠️ Server ping returned ${response.status}`);
                return false;
            }
            
        } catch (error) {
            console.log(`❌ Server ping failed: ${error.message}`);
            return false;
        }
    }

    async warmUpServer() {
        try {
            console.log('🔥 Warming up server...');
            const warmupRequests = [
                fetch(`${this.baseURL}/health`),
                fetch(`${this.baseURL}/documents`),
            ];
            
            // Wait for at least one to succeed
            await Promise.race(warmupRequests);
            console.log('✅ Server warmed up successfully');
            
        } catch (error) {
            console.warn('⚠️ Server warmup failed, continuing anyway:', error.message);
        }
    }

    async performHealthCheck() {
        try {
            const startTime = Date.now();
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: {
                    'X-Session-ID': this.sessionId,
                    'X-Health-Check': 'full'
                },
                timeout: this.adaptiveTimeout
            });

            if (!response.ok) {
                throw new Error(`Health check failed with status ${response.status}`);
            }

            const data = await response.json();
            const responseTime = Date.now() - startTime;
            
            this.lastHealthCheck = {
                timestamp: Date.now(),
                responseTime,
                status: data.status,
                services: data.services
            };

            console.log(`✅ Health check passed (${responseTime}ms)`, data);
            return { success: true, data, responseTime };
            
        } catch (error) {
            console.error('❌ Health check failed:', error);
            return { success: false, error: error.message };
        }
    }

    updateNetworkQuality(responseTime) {
        if (responseTime < 200) {
            this.networkQuality = 'excellent';
            this.adaptiveTimeout = 10000;
        } else if (responseTime < 500) {
            this.networkQuality = 'good';
            this.adaptiveTimeout = 15000;
        } else if (responseTime < 1000) {
            this.networkQuality = 'fair';
            this.adaptiveTimeout = 20000;
        } else if (responseTime < 3000) {
            this.networkQuality = 'poor';
            this.adaptiveTimeout = 30000;
        } else {
            this.networkQuality = 'very_poor';
            this.adaptiveTimeout = 45000;
        }
        
        console.log(`📶 Network quality: ${this.networkQuality} (${responseTime}ms)`);
    }

    onConnectionSuccess() {
        console.log('🎉 Connection established successfully!');
        this.setState('connected');
        this.processQueuedRequests();
        this.startHeartbeat();
        this.saveSessionToStorage();
        this.notifyListeners('connected', this.getConnectionInfo());
    }

    onConnectionFailure(error) {
        console.error('💥 All connection attempts failed:', error);
        this.setState('disconnected');
        this.notifyListeners('failed', { error: error.message });
    }

    setState(newState) {
        const oldState = this.connectionState;
        this.connectionState = newState;
        console.log(`🔄 Connection state: ${oldState} → ${newState}`);
        this.notifyListeners('stateChange', { oldState, newState });
    }

    getConnectionInfo() {
        return {
            state: this.connectionState,
            networkQuality: this.networkQuality,
            sessionId: this.sessionId,
            lastHealthCheck: this.lastHealthCheck,
            adaptiveTimeout: this.adaptiveTimeout
        };
    }

    // Session Management
    saveSessionToStorage() {
        try {
            const sessionData = {
                sessionId: this.sessionId,
                timestamp: Date.now(),
                connectionInfo: this.getConnectionInfo()
            };
            localStorage.setItem('linelead_session', JSON.stringify(sessionData));
        } catch (error) {
            console.warn('⚠️ Failed to save session to storage:', error);
        }
    }

    loadSessionFromStorage() {
        try {
            const stored = localStorage.getItem('linelead_session');
            if (stored) {
                const sessionData = JSON.parse(stored);
                // Restore session if less than 1 hour old
                if (Date.now() - sessionData.timestamp < 3600000) {
                    console.log('📂 Restored session from storage');
                    return sessionData;
                }
            }
        } catch (error) {
            console.warn('⚠️ Failed to load session from storage:', error);
        }
        return null;
    }

    // Heartbeat System
    startHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        this.heartbeatInterval = setInterval(() => {
            this.sendHeartbeat();
        }, 30000); // 30-second heartbeat
    }

    async sendHeartbeat() {
        try {
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: {
                    'X-Session-ID': this.sessionId,
                    'X-Heartbeat': 'true'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Heartbeat failed: ${response.status}`);
            }
            
            this.lastActivity = Date.now();
            
        } catch (error) {
            console.warn('💓 Heartbeat failed, checking connection:', error);
            this.handleConnectionLoss();
        }
    }

    // Network Event Handling
    setupEventListeners() {
        window.addEventListener('online', this.onlineHandler);
        window.addEventListener('offline', this.offlineHandler);
        
        // Visibility change handling (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.connectionState !== 'connected') {
                console.log('👁️ Tab became visible, checking connection...');
                this.attemptConnection();
            }
        });
    }

    handleOnlineStateChange() {
        console.log('🌐 Network came online');
        if (this.connectionState !== 'connected') {
            this.attemptConnection();
        }
    }

    handleOfflineStateChange() {
        console.log('📴 Network went offline');
        this.setState('disconnected');
        this.notifyListeners('offline');
    }

    handleConnectionLoss() {
        if (this.connectionState === 'connected') {
            console.log('📡 Connection lost, attempting to reconnect...');
            this.setState('reconnecting');
            this.attemptConnection();
        }
    }

    // Request Queue Management
    async makeRequest(url, options = {}) {
        return new Promise((resolve, reject) => {
            const request = {
                url,
                options: {
                    ...options,
                    headers: {
                        ...options.headers,
                        'X-Session-ID': this.sessionId
                    }
                },
                resolve,
                reject,
                timestamp: Date.now(),
                retries: 0
            };

            if (this.connectionState === 'connected') {
                this.executeRequest(request);
            } else {
                console.log('📥 Queuing request until connection is established');
                this.requestQueue.push(request);
                if (this.connectionState === 'disconnected') {
                    this.attemptConnection();
                }
            }
        });
    }

    async executeRequest(request) {
        try {
            const response = await fetch(`${this.baseURL}${request.url}`, request.options);
            
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status} ${response.statusText}`);
            }
            
            request.resolve(response);
            
        } catch (error) {
            if (request.retries < 3 && this.isRetryableError(error)) {
                request.retries++;
                console.log(`🔄 Retrying request (attempt ${request.retries})`);
                setTimeout(() => this.executeRequest(request), 1000 * request.retries);
            } else {
                request.reject(error);
            }
        }
    }

    isRetryableError(error) {
        return error.name === 'TypeError' || // Network error
               error.message.includes('fetch') ||
               error.message.includes('timeout');
    }

    processQueuedRequests() {
        console.log(`📤 Processing ${this.requestQueue.length} queued requests`);
        const queue = [...this.requestQueue];
        this.requestQueue = [];
        
        queue.forEach(request => {
            // Only process requests that aren't too old (5 minutes)
            if (Date.now() - request.timestamp < 300000) {
                this.executeRequest(request);
            } else {
                request.reject(new Error('Request timeout: queued too long'));
            }
        });
    }

    // Health Check Monitoring
    startPeriodicHealthChecks() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        
        // Health check every 2 minutes when connected
        this.healthCheckInterval = setInterval(async () => {
            if (this.connectionState === 'connected') {
                const health = await this.performHealthCheck();
                if (!health.success) {
                    this.handleConnectionLoss();
                }
            }
        }, 120000);
    }

    // Event Listener Management
    addListener(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    notifyListeners(event, data = null) {
        this.listeners.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('❌ Error in connection listener:', error);
            }
        });
    }

    // Cleanup
    destroy() {
        window.removeEventListener('online', this.onlineHandler);
        window.removeEventListener('offline', this.offlineHandler);
        
        if (this.healthCheckInterval) clearInterval(this.healthCheckInterval);
        if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
        if (this.keepAliveInterval) clearInterval(this.keepAliveInterval);
        
        this.listeners.clear();
        this.requestQueue = [];
    }

    // Public API
    getStatus() {
        return {
            connectionState: this.connectionState,
            networkQuality: this.networkQuality,
            sessionId: this.sessionId,
            queuedRequests: this.requestQueue.length,
            lastHealthCheck: this.lastHealthCheck
        };
    }

    async forceReconnect() {
        console.log('🔄 Force reconnect requested');
        this.connectionAttempts = 0;
        this.setState('connecting');
        return this.attemptConnection();
    }
}

// Singleton instance
export const connectionManager = new ConnectionManager();
export default ConnectionManager;