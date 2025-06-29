/**
 * 🔥 Keep-Alive Service for Render Cold Start Prevention
 * 
 * Prevents server hibernation by sending periodic keep-alive requests
 * and provides server warm-up functionality for faster recovery.
 */

class KeepAliveService {
    constructor() {
        this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        this.keepAliveInterval = null;
        this.isActive = false;
        this.intervalMinutes = 12; // Keep alive every 12 minutes (Render hibernates after 15)
        this.lastKeepAlive = null;
        this.failureCount = 0;
        this.maxFailures = 3;
        
        // Start automatically if in production
        if (process.env.NODE_ENV === 'production') {
            this.start();
        }
    }

    start() {
        if (this.isActive) {
            console.log('🔥 Keep-alive service already running');
            return;
        }

        console.log(`🔥 Starting keep-alive service (${this.intervalMinutes}min intervals)`);
        this.isActive = true;
        this.failureCount = 0;
        
        // Send initial keep-alive immediately
        this.sendKeepAlive();
        
        // Set up periodic keep-alive
        this.keepAliveInterval = setInterval(() => {
            this.sendKeepAlive();
        }, this.intervalMinutes * 60 * 1000);
    }

    stop() {
        if (!this.isActive) {
            return;
        }

        console.log('🛑 Stopping keep-alive service');
        this.isActive = false;
        
        if (this.keepAliveInterval) {
            clearInterval(this.keepAliveInterval);
            this.keepAliveInterval = null;
        }
    }

    async sendKeepAlive() {
        try {
            console.log('💓 Sending keep-alive ping...');
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
            
            const startTime = Date.now();
            const response = await fetch(`${this.baseURL}/keep-alive`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'X-Keep-Alive': 'true',
                    'Cache-Control': 'no-cache'
                }
            });
            
            clearTimeout(timeoutId);
            const responseTime = Date.now() - startTime;
            
            if (response.ok) {
                const data = await response.json();
                this.lastKeepAlive = Date.now();
                this.failureCount = 0;
                
                console.log(`✅ Keep-alive successful (${responseTime}ms)`, {
                    uptime: data.uptime_seconds,
                    timestamp: data.timestamp
                });
                
                // Trigger warm-up if server was cold (slow response)
                if (responseTime > 5000) {
                    console.log('🐌 Slow keep-alive response, triggering warm-up...');
                    this.warmUpServer();
                }
                
            } else {
                throw new Error(`Keep-alive failed: ${response.status}`);
            }
            
        } catch (error) {
            this.failureCount++;
            console.warn(`❌ Keep-alive failed (${this.failureCount}/${this.maxFailures}):`, error.message);
            
            // If too many failures, try to warm up the server
            if (this.failureCount >= this.maxFailures) {
                console.log('🔥 Multiple keep-alive failures, attempting server warm-up...');
                this.warmUpServer();
                this.failureCount = 0; // Reset after warm-up attempt
            }
        }
    }

    async warmUpServer() {
        try {
            console.log('🔥 Warming up server...');
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout for warm-up
            
            const startTime = Date.now();
            const response = await fetch(`${this.baseURL}/warm-up`, {
                method: 'POST',
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Warm-Up': 'true'
                },
                body: JSON.stringify({
                    timestamp: Date.now(),
                    source: 'keep_alive_service'
                })
            });
            
            clearTimeout(timeoutId);
            const warmUpTime = Date.now() - startTime;
            
            if (response.ok) {
                const data = await response.json();
                console.log(`🎉 Server warm-up completed (${warmUpTime}ms)`, data);
                return { success: true, data, warmUpTime };
            } else {
                throw new Error(`Warm-up failed: ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Server warm-up failed:', error);
            return { success: false, error: error.message };
        }
    }

    // Public methods
    getStatus() {
        return {
            isActive: this.isActive,
            intervalMinutes: this.intervalMinutes,
            lastKeepAlive: this.lastKeepAlive,
            failureCount: this.failureCount,
            nextKeepAlive: this.lastKeepAlive ? 
                this.lastKeepAlive + (this.intervalMinutes * 60 * 1000) : 
                null
        };
    }

    async forceKeepAlive() {
        console.log('🔄 Force keep-alive requested');
        return this.sendKeepAlive();
    }

    async forceWarmUp() {
        console.log('🔥 Force warm-up requested');
        return this.warmUpServer();
    }

    setInterval(minutes) {
        if (minutes < 5 || minutes > 30) {
            console.warn('⚠️ Keep-alive interval should be between 5-30 minutes');
            return;
        }
        
        this.intervalMinutes = minutes;
        console.log(`🔄 Keep-alive interval updated to ${minutes} minutes`);
        
        // Restart with new interval if currently active
        if (this.isActive) {
            this.stop();
            this.start();
        }
    }

    // Browser event handlers
    setupBrowserEventHandlers() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isActive) {
                // Page became visible, send keep-alive to ensure server is awake
                console.log('👁️ Page became visible, sending keep-alive...');
                this.sendKeepAlive();
            }
        });

        // Handle browser back/forward navigation
        window.addEventListener('pageshow', (event) => {
            if (event.persisted && this.isActive) {
                // Page loaded from cache, send keep-alive
                console.log('📄 Page loaded from cache, sending keep-alive...');
                this.sendKeepAlive();
            }
        });

        // Handle network state changes
        window.addEventListener('online', () => {
            if (this.isActive) {
                console.log('🌐 Network came online, sending keep-alive...');
                this.sendKeepAlive();
            }
        });
    }
}

// Singleton instance
export const keepAliveService = new KeepAliveService();

// Auto-setup browser event handlers
if (typeof window !== 'undefined') {
    keepAliveService.setupBrowserEventHandlers();
}

export default KeepAliveService;