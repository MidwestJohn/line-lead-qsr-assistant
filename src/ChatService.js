import { apiService } from './services/api';

// Centralized chat service with retry logic and error handling
class ChatService {
  constructor() {
    this.baseURL = apiService.baseURL;
    this.defaultTimeout = 30000; // 30 seconds
  }

  async sendMessage(message, options = {}) {
    const {
      maxRetries = 3,
      timeout = this.defaultTimeout,
      onRetry = null,
      onProgress = null
    } = options;

    let lastError = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          // Exponential backoff: 1s, 2s, 4s
          const delay = Math.pow(2, attempt - 1) * 1000;
          
          if (onRetry) {
            onRetry(attempt, maxRetries, delay);
          }
          
          await this.delay(delay);
        }

        if (onProgress) {
          onProgress('sending');
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        // Use the connection-aware API service
        const data = await apiService.sendChatMessage(message);
        clearTimeout(timeoutId);

        if (onProgress) {
          onProgress('processing');
        }

        if (onProgress) {
          onProgress('complete');
        }

        return {
          success: true,
          data: data,
          attempt: attempt + 1
        };

      } catch (error) {
        lastError = this.categorizeError(error);
        
        // Don't retry on certain types of errors
        if (lastError.type === 'validation' || lastError.type === 'auth') {
          break;
        }

        // Last attempt reached
        if (attempt === maxRetries) {
          break;
        }
      }
    }

    return {
      success: false,
      error: lastError,
      attempts: maxRetries + 1
    };
  }

  categorizeError(error) {
    if (error.name === 'AbortError') {
      return {
        type: 'timeout',
        message: 'Request timed out. Please try again.',
        userMessage: 'Request took too long - the assistant might be processing a complex question.'
      };
    }

    if (error.name === 'TypeError' || error.message.includes('fetch')) {
      return {
        type: 'network',
        message: 'Network connection failed',
        userMessage: 'Unable to connect to the assistant. Check your internet connection.'
      };
    }

    if (error.message.includes('500')) {
      return {
        type: 'server',
        message: 'Server error',
        userMessage: 'The assistant is experiencing technical difficulties.'
      };
    }

    if (error.message.includes('503') || error.message.includes('504')) {
      return {
        type: 'unavailable',
        message: 'Service temporarily unavailable',
        userMessage: 'The assistant is temporarily unavailable. Please try again in a moment.'
      };
    }

    if (error.message.includes('400')) {
      return {
        type: 'validation',
        message: 'Invalid request',
        userMessage: 'There was an issue with your message. Please try rephrasing.'
      };
    }

    if (error.message.includes('401') || error.message.includes('403')) {
      return {
        type: 'auth',
        message: 'Authentication failed',
        userMessage: 'Authentication issue. Please refresh the page.'
      };
    }

    return {
      type: 'unknown',
      message: error.message || 'Unknown error occurred',
      userMessage: 'Something went wrong. Please try again.'
    };
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Streaming message support with enhanced error handling
  async sendMessageStream(message, options = {}) {
    const {
      onChunk = null,
      onError = null,
      onComplete = null,
      timeout = 30000
    } = options;

    let timeoutId = null;
    let reader = null;

    try {
      // Create abort controller for timeout
      const controller = new AbortController();
      timeoutId = setTimeout(() => {
        controller.abort();
        if (onError) onError('Response timeout - please try again');
      }, timeout);

      const response = await fetch(`${this.baseURL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify({ message }),
        signal: controller.signal
      });

      if (!response.ok) {
        clearTimeout(timeoutId);
        throw new Error(`Streaming request failed: ${response.status} ${response.statusText}`);
      }

      // Check if response is actually a streaming response or regular JSON
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        // Response is regular JSON, not streaming - simulate streaming animation
        clearTimeout(timeoutId);
        const data = await response.json();
        
        // Simulate streaming by chunking the response incrementally
        if (onChunk && data.response) {
          const fullText = data.response;
          const words = fullText.split(' ');
          const chunkSize = Math.max(1, Math.floor(words.length / 8)); // ~8 chunks
          
          let sentWords = 0;
          for (let i = 0; i < words.length; i += chunkSize) {
            // Send only the NEW words in this chunk, not accumulative
            const chunkWords = words.slice(sentWords, sentWords + chunkSize);
            const incrementalChunk = chunkWords.join(' ') + ' ';
            
            await new Promise(resolve => setTimeout(resolve, 50)); // 50ms delay between chunks
            onChunk(incrementalChunk);
            
            sentWords += chunkSize;
          }
          
          // Send any remaining words
          if (sentWords < words.length) {
            const remainingWords = words.slice(sentWords);
            onChunk(remainingWords.join(' '));
          }
        } else if (onChunk) {
          onChunk(data.response || 'No response received');
        }
        
        if (onComplete) {
          onComplete(data);
        }
        
        return { success: true, data };
      }

      // Handle actual streaming response
      reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let lastChunkTime = Date.now();

      try {
        // eslint-disable-next-line no-constant-condition
        while (true) {
          // Check for data timeout (no chunks received for 10 seconds)
          if (Date.now() - lastChunkTime > 10000) {
            throw new Error('No data received for 10 seconds');
          }

          const { done, value } = await reader.read();
          
          if (done) {
            clearTimeout(timeoutId);
            break;
          }
          
          lastChunkTime = Date.now();
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete lines
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer
          
          for (const line of lines) {
            if (line.startsWith('data: ') && line.length > 6) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.error) {
                  clearTimeout(timeoutId);
                  if (onError) onError(data.chunk || 'Streaming error occurred');
                  return { success: false, error: data.chunk };
                }
                
                if (data.done) {
                  clearTimeout(timeoutId);
                  if (onComplete) onComplete(data.metadata);
                  return { success: true, metadata: data.metadata };
                }
                
                if (data.chunk && onChunk) {
                  onChunk(data.chunk);
                }
                
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line);
              }
            }
          }
        }

        clearTimeout(timeoutId);
        return { success: true };

      } finally {
        if (reader) {
          try {
            reader.releaseLock();
          } catch (e) {
            // Reader already released
          }
        }
      }

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (reader) {
        try {
          reader.releaseLock();
        } catch (e) {
          // Reader already released
        }
      }

      const categorizedError = this.categorizeError(error);
      if (onError) onError(categorizedError.userMessage);
      return { success: false, error: categorizedError };
    }
  }

  // Upload file with progress and retry
  async uploadFile(file, options = {}) {
    const {
      maxRetries = 2,
      onProgress = null,
      onRetry = null
    } = options;

    let lastError = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          const delay = Math.pow(2, attempt - 1) * 1000;
          
          if (onRetry) {
            onRetry(attempt, maxRetries, delay);
          }
          
          await this.delay(delay);
        }

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseURL}/upload`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.status}`);
        }

        const data = await response.json();

        if (onProgress) {
          onProgress(100); // Complete
        }

        return {
          success: true,
          data: data,
          attempt: attempt + 1
        };

      } catch (error) {
        lastError = this.categorizeError(error);
        
        if (attempt === maxRetries) {
          break;
        }
      }
    }

    return {
      success: false,
      error: lastError,
      attempts: maxRetries + 1
    };
  }

  // Send multimodal message with visual citations
  async sendMultiModalMessage(message, options = {}) {
    const {
      currentEquipment = null,
      enableCitations = true,
      maxRetries = 3,
      timeout = this.defaultTimeout,
      onRetry = null,
      onProgress = null
    } = options;

    let lastError = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          const delay = Math.pow(2, attempt - 1) * 1000;
          
          if (onRetry) {
            onRetry(attempt, maxRetries, delay);
          }
          
          await this.delay(delay);
        }

        if (onProgress) {
          onProgress('sending');
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        // Use the multimodal API service
        const data = await apiService.sendMultiModalMessage(message, currentEquipment, enableCitations);
        clearTimeout(timeoutId);

        if (onProgress) {
          onProgress('processing');
        }

        if (onProgress) {
          onProgress('complete');
        }

        return {
          success: true,
          data: data,
          attempts: attempt + 1
        };

      } catch (error) {
        lastError = error;
        console.error(`MultiModal message attempt ${attempt + 1} failed:`, error);

        const errorDetails = this.parseError(error);
        if (errorDetails.type === 'network' && attempt < maxRetries) {
          // Retry network errors
          continue;
        } else {
          // Don't retry other types of errors
          break;
        }
      }
    }

    return {
      success: false,
      error: lastError,
      attempts: maxRetries + 1
    };
  }
}

export default new ChatService();