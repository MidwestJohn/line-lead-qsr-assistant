import { API_BASE_URL } from './config';

/**
 * Sleep utility for retry delays
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Enhanced API utility with retry logic and exponential backoff
 */
export const makeAPICall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const maxRetries = options.maxRetries || 3;
  const baseDelay = options.baseDelay || 1000;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`API Call (attempt ${attempt}): ${options.method || 'GET'} ${url}`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: controller.signal,
        ...options,
      });
      
      clearTimeout(timeoutId);
      
      // Log response details for debugging
      console.log(`API Response: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        // Try to get error details from response
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.error || errorMessage;
        } catch (e) {
          // If JSON parsing fails, use the default error message
        }
        
        const error = new Error(errorMessage);
        error.status = response.status;
        error.statusText = response.statusText;
        
        // Don't retry client errors (4xx)
        if (response.status >= 400 && response.status < 500) {
          throw error;
        }
        
        // Retry server errors (5xx) and network errors
        if (attempt === maxRetries) {
          throw error;
        }
        
        console.log(`Retrying in ${baseDelay * attempt}ms...`);
        await sleep(baseDelay * attempt);
        continue;
      }
      
      const data = await response.json();
      console.log('API Success:', endpoint, data);
      return data;
      
    } catch (error) {
      console.error(`API call failed (attempt ${attempt}):`, {
        endpoint,
        url,
        error: error.message,
        status: error.status,
        options
      });
      
      // Don't retry AbortError or client errors
      if (error.name === 'AbortError' || (error.status >= 400 && error.status < 500)) {
        const enhancedError = new Error(
          error.message || `Failed to connect to ${url}`
        );
        enhancedError.originalError = error;
        enhancedError.endpoint = endpoint;
        enhancedError.url = url;
        throw enhancedError;
      }
      
      // If this was the last attempt, throw the error
      if (attempt === maxRetries) {
        const enhancedError = new Error(
          error.message || `Failed to connect to ${url} after ${maxRetries} attempts`
        );
        enhancedError.originalError = error;
        enhancedError.endpoint = endpoint;
        enhancedError.url = url;
        throw enhancedError;
      }
      
      // Wait before retrying (exponential backoff)
      console.log(`Retrying in ${baseDelay * attempt}ms...`);
      await sleep(baseDelay * attempt);
    }
  }
};

/**
 * Specific API call helpers
 */
export const apiUtils = {
  // Health check
  healthCheck: () => makeAPICall('/health'),
  
  // Chat
  sendMessage: (message) => makeAPICall('/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  }),
  
  // Documents
  getDocuments: () => makeAPICall('/documents'),
  deleteDocument: (documentId) => makeAPICall(`/documents/${documentId}`, {
    method: 'DELETE',
  }),
  
  // Upload file (FormData requires special handling)
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return makeAPICall('/upload', {
      method: 'POST',
      headers: {}, // Don't set Content-Type for FormData
      body: formData,
    });
  },
  
  // AI Status
  getAIStatus: () => makeAPICall('/ai-status'),
  
  // Search stats
  getSearchStats: () => makeAPICall('/search-stats'),
};

export default apiUtils;