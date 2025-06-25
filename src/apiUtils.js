import { API_BASE_URL } from './config';

/**
 * Enhanced API utility with better error handling and debugging
 */
export const makeAPICall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    console.log(`API Call: ${options.method || 'GET'} ${url}`);
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    
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
      throw error;
    }
    
    const data = await response.json();
    console.log('API Success:', endpoint, data);
    return data;
    
  } catch (error) {
    console.error('API call failed:', {
      endpoint,
      url,
      error: error.message,
      status: error.status,
      options
    });
    
    // Re-throw with enhanced error information
    const enhancedError = new Error(
      error.message || `Failed to connect to ${url}`
    );
    enhancedError.originalError = error;
    enhancedError.endpoint = endpoint;
    enhancedError.url = url;
    
    throw enhancedError;
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