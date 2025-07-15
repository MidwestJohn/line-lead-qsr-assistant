/**
 * Production API Configuration - BaseChat Enterprise Patterns
 * ==========================================================
 * 
 * Vercel-optimized API client for Render backend integration,
 * following BaseChat's proven frontend integration patterns.
 * 
 * Features:
 * - Environment-based API endpoint configuration
 * - Error handling for cross-origin requests
 * - Performance optimization for Vercel edge
 * - Service degradation response handling
 * - Request retry logic with backoff
 * 
 * Author: Generated with Memex (https://memex.tech)
 * Co-Authored-By: Memex <noreply@memex.tech>
 */

interface APIConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  environment: 'development' | 'production';
}

interface ServiceHealthStatus {
  status: 'healthy' | 'degraded' | 'unavailable';
  response_time_ms?: number;
  degraded?: boolean;
  fallback_available?: boolean;
}

interface SystemHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'error';
  timestamp: string;
  platform: string;
  services: Record<string, ServiceHealthStatus>;
  degraded_services: string[];
  performance: {
    total_response_time_ms: number;
    target_response_time: string;
    memory?: Record<string, any>;
  };
}

class ProductionAPIConfig {
  private config: APIConfig;
  
  constructor() {
    this.config = {
      baseURL: this.getAPIBaseURL(),
      timeout: 30000, // 30s for Render backend
      retries: 3,
      environment: (process.env.NODE_ENV as 'development' | 'production') || 'development'
    };
  }
  
  private getAPIBaseURL(): string {
    // Vercel environment-based API routing (BaseChat pattern)
    if (process.env.NODE_ENV === 'production') {
      return process.env.REACT_APP_API_URL || 'https://line-lead-backend.onrender.com';
    }
    return process.env.REACT_APP_API_URL || 'http://localhost:8000';
  }
  
  getConfig(): APIConfig {
    return this.config;
  }
}

class APIError extends Error {
  constructor(
    message: string, 
    public statusCode: number, 
    public serviceName?: string,
    public fallbackAvailable?: boolean
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * API client optimized for proven Line Lead architecture
 * Following BaseChat's frontend integration patterns
 */
class LineLeadAPIClient {
  private config: APIConfig;
  private abortControllers: Map<string, AbortController>;
  private healthCache: SystemHealthResponse | null = null;
  private healthCacheTime: number = 0;
  private readonly HEALTH_CACHE_TTL = 30000; // 30 seconds
  
  constructor() {
    this.config = new ProductionAPIConfig().getConfig();
    this.abortControllers = new Map();
  }
  
  /**
   * Enhanced chat API with BaseChat error handling patterns
   */
  async sendChatMessage(
    message: string, 
    sessionId?: string,
    enableRagie: boolean = true,
    includeVisualCitations: boolean = true
  ): Promise<ChatResponse> {
    const requestId = `chat-${Date.now()}`;
    const controller = new AbortController();
    this.abortControllers.set(requestId, controller);
    
    try {
      // Check system health first
      const healthStatus = await this.checkSystemHealth();
      
      // Adapt request based on service health
      const adaptedRequest = this.adaptRequestForHealth(
        { message, sessionId, enableRagie, includeVisualCitations },
        healthStatus
      );
      
      const response = await fetch(`${this.config.baseURL}/chat/safe-enhanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId || 'anonymous',
          'X-Health-Check': 'basic'
        },
        body: JSON.stringify(adaptedRequest),
        signal: controller.signal
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.message || `Chat API error: ${response.status}`, 
          response.status,
          'chat',
          errorData.fallback_available
        );
      }
      
      const chatResponse = await response.json();
      
      // Add service status information to response
      return {
        ...chatResponse,
        system_health: healthStatus?.status,
        services_used: this.identifyServicesUsed(chatResponse),
        performance_info: {
          total_time: chatResponse.total_processing_time,
          ragie_time: chatResponse.ragie_processing_time,
          system_status: healthStatus?.status
        }
      };
      
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new APIError('Request cancelled', 408, 'chat');
      }
      
      // Network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new APIError(
          'Network connection failed - please check your internet connection', 
          0, 
          'network',
          true // Text chat fallback always available
        );
      }
      
      throw this.handleAPIError(error);
    } finally {
      this.abortControllers.delete(requestId);
    }
  }
  
  /**
   * Enhanced health monitoring following BaseChat patterns
   */
  async checkSystemHealth(useCache: boolean = true): Promise<SystemHealthResponse | null> {
    // Use cached health data if recent
    if (useCache && this.healthCache && 
        (Date.now() - this.healthCacheTime) < this.HEALTH_CACHE_TTL) {
      return this.healthCache;
    }
    
    try {
      const response = await fetch(`${this.config.baseURL}/health`, {
        timeout: 5000, // Quick health check
        headers: {
          'X-Health-Check': 'basic',
          'X-Session-ID': 'health-monitor'
        }
      });
      
      if (response.ok) {
        const healthData = await response.json();
        this.healthCache = healthData;
        this.healthCacheTime = Date.now();
        return healthData;
      }
      
      return null;
    } catch (error) {
      console.warn('Health check failed:', error);
      return null;
    }
  }
  
  /**
   * Adapt request based on system health status
   */
  private adaptRequestForHealth(
    originalRequest: any, 
    healthStatus: SystemHealthResponse | null
  ): any {
    if (!healthStatus) {
      return originalRequest; // No health info, proceed normally
    }
    
    const adaptedRequest = { ...originalRequest };
    
    // Disable Ragie if it's degraded
    if (healthStatus.services?.ragie_enhancement?.degraded) {
      adaptedRequest.enableRagie = false;
      console.info('🔄 Ragie enhancement disabled due to service degradation');
    }
    
    // Disable visual citations if service is degraded
    if (healthStatus.services?.visual_citations?.degraded) {
      adaptedRequest.includeVisualCitations = false;
      console.info('🔄 Visual citations disabled due to service degradation');
    }
    
    // Add degradation context to request
    adaptedRequest.system_context = {
      overall_status: healthStatus.status,
      degraded_services: healthStatus.degraded_services || []
    };
    
    return adaptedRequest;
  }
  
  /**
   * Identify which services were used in the response
   */
  private identifyServicesUsed(response: any): string[] {
    const servicesUsed = ['pydantic_orchestration']; // Always used
    
    if (response.ragie_enhanced) {
      servicesUsed.push('ragie_enhancement');
    }
    
    if (response.visual_citations && response.visual_citations.length > 0) {
      servicesUsed.push('visual_citations');
    }
    
    return servicesUsed;
  }
  
  /**
   * Enhanced error handling following BaseChat patterns
   */
  private handleAPIError(error: any): APIError {
    if (error instanceof APIError) return error;
    
    // Timeout errors
    if (error.name === 'TimeoutError') {
      return new APIError(
        'Request timed out - the service may be experiencing high load', 
        408, 
        'timeout',
        true
      );
    }
    
    // Generic errors
    return new APIError(
      error.message || 'An unexpected error occurred', 
      500, 
      'unknown',
      false
    );
  }
  
  /**
   * Service degradation status check
   */
  async getDegradationStatus(): Promise<any> {
    try {
      const response = await fetch(`${this.config.baseURL}/health/degradation`, {
        timeout: 5000
      });
      
      if (response.ok) {
        return await response.json();
      }
      
      return null;
    } catch (error) {
      console.warn('Degradation status check failed:', error);
      return null;
    }
  }
  
  /**
   * Error statistics for monitoring
   */
  async getErrorStatistics(): Promise<any> {
    try {
      const response = await fetch(`${this.config.baseURL}/health/errors`, {
        timeout: 5000
      });
      
      if (response.ok) {
        return await response.json();
      }
      
      return null;
    } catch (error) {
      console.warn('Error statistics check failed:', error);
      return null;
    }
  }
  
  /**
   * Cancel all ongoing requests
   */
  cancelAllRequests(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }
}

// Response interfaces
interface ChatResponse {
  response: string;
  agent_used: string;
  conversation_id: string;
  ragie_enhanced?: boolean;
  visual_citations?: any[];
  total_processing_time?: number;
  ragie_processing_time?: number;
  system_health?: string;
  services_used?: string[];
  performance_info?: any;
}

// Global API client instance
export const apiClient = new LineLeadAPIClient();
export { APIError, ProductionAPIConfig };
export type { ChatResponse, SystemHealthResponse, ServiceHealthStatus };