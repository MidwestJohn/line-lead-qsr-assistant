import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';
import ServiceStatus from './ServiceStatus';
import ErrorBoundary from './ErrorBoundary';
import ChatService from './ChatService';
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { Send, Square, Upload, MessageCircle, WifiOff, Copy, RefreshCw, Check, BookOpen } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API_BASE_URL } from './config';
import DebugInfo from './DebugInfo';

function App() {
  
  // Assistant UI Runtime - memoized to prevent infinite re-renders
  const onNewMessage = useCallback(async ({ content }) => {
    // For now, just return a simple response
    return {
      role: "assistant",
      content: [{ type: "text", text: "Assistant UI provider is working! (This is a test response)" }]
    };
  }, []);

  const runtime = useLocalRuntime({
    initialMessages: [],
    onNew: onNewMessage
  });

  // Core state
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! I'm your Line Lead QSR Assistant. Ask me anything about equipment maintenance!",
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [documentsRefresh, setDocumentsRefresh] = useState(0);
  
  // Service status and resilience state
  const [serviceStatus, setServiceStatus] = useState({
    isHealthy: false,
    isReady: false,
    error: null
  });
  const [messageStatus, setMessageStatus] = useState({
    isLoading: false,
    isRetrying: false,
    retryAttempt: 0,
    error: null
  });
  
  // Message queue for offline support
  const [messageQueue, setMessageQueue] = useState([]);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  // Streaming state
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  
  // Message actions state
  const [hoveredMessage, setHoveredMessage] = useState(null);
  const [copiedMessage, setCopiedMessage] = useState(null);
  
  // Performance optimization refs
  const messagesEndRef = useRef(null);
  const streamingTimeoutRef = useRef(null);
  const lastUpdateTimeRef = useRef(0);
  const pendingChunksRef = useRef('');

  // Effects and event handlers
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Throttled scroll to bottom for streaming
  const throttleTimeoutRef = useRef(null);
  const scrollToBottomThrottled = useCallback(() => {
    if (throttleTimeoutRef.current) return;
    throttleTimeoutRef.current = setTimeout(() => {
      scrollToBottom();
      throttleTimeoutRef.current = null;
    }, 100);
  }, [scrollToBottom]);

  useEffect(() => {
    if (!isStreaming) {
      scrollToBottom();
    }
  }, [messages, isStreaming, scrollToBottom]);

  // Check service status on startup and periodically
  useEffect(() => {
    const checkServices = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
          const healthData = await response.json();
          setServiceStatus({
            isHealthy: healthData.status === 'healthy',
            isReady: healthData.search_ready,
            services: healthData.services
          });
        }
      } catch (error) {
        console.error('Service check failed:', error);
        setServiceStatus({
          isHealthy: false,
          isReady: false,
          error: error.message
        });
      }
    };
    
    // Initial check
    checkServices();
    
    // Periodic check every 30 seconds
    const interval = setInterval(checkServices, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Process queued messages when back online
  const processMessageQueue = useCallback(async () => {
    if (messageQueue.length === 0) return;

    for (const queuedMessage of messageQueue) {
      // We'll handle this differently to avoid circular dependencies
      // For now, just clear the queue - could implement proper retry logic later
    }
    setMessageQueue([]);
  }, [messageQueue]);

  // Online/offline detection
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Process queued messages when coming back online
      processMessageQueue();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [processMessageQueue]);

  // Handle service status updates
  const handleServiceStatusChange = (status) => {
    setServiceStatus(status);
  };

  // Throttled update function for smooth streaming
  const updateStreamingMessage = useCallback((messageId, newText) => {
    pendingChunksRef.current = newText;
    
    const updateNow = Date.now();
    const timeSinceLastUpdate = updateNow - lastUpdateTimeRef.current;
    
    if (timeSinceLastUpdate < 50) { // Throttle to max 20fps
      requestAnimationFrame(() => {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, text: pendingChunksRef.current }
            : msg
        ));
        lastUpdateTimeRef.current = Date.now();
        scrollToBottomThrottled();
      });
    } else {
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, text: newText }
          : msg
      ));
      lastUpdateTimeRef.current = updateNow;
      scrollToBottomThrottled();
    }
  }, [scrollToBottomThrottled]);

  // Stop message generation
  const stopMessage = () => {
    setIsStreaming(false);
    setIsThinking(false);
    setIsWaitingForResponse(false);
    setStreamingMessage(null);
    
    // Clear streaming timeout
    if (streamingTimeoutRef.current) {
      clearTimeout(streamingTimeoutRef.current);
      streamingTimeoutRef.current = null;
    }
    
    setMessageStatus({
      isLoading: false,
      isRetrying: false,
      retryAttempt: 0,
      error: null
    });
    
    // Mark any streaming message as complete
    if (streamingMessage) {
      setMessages(prev => prev.map(msg => 
        msg.isStreaming ? { ...msg, isStreaming: false, text: msg.text + ' [stopped]' } : msg
      ));
    }
  };

  // Enhanced message sending with retry logic
  const sendMessage = async () => {
    if (inputText.trim() === '' || messageStatus.isLoading) return;

    // Check if services are ready
    if (!serviceStatus.isHealthy && !serviceStatus.isReady) {
      const warningMessage = {
        id: Date.now(),
        text: "⚠️ Services are starting up. Please wait a moment and try again.",
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, warningMessage]);
      return;
    }

    const currentMessage = inputText;
    const messageId = Date.now();
    setInputText('');

    // If offline, queue the message
    if (!isOnline) {
      const userMessage = {
        id: messageId,
        text: currentMessage,
        sender: 'user',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, userMessage]);
      setMessageQueue(prev => [...prev, { text: currentMessage, id: messageId }]);
      
      const offlineMessage = {
        id: messageId + 1,
        text: "📱 You're offline. Message will be sent when connection is restored.",
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, offlineMessage]);
      return;
    }

    await sendMessageWithRetry(currentMessage, messageId);
  };

  const sendMessageWithRetry = async (messageText, messageId) => {
    const userMessage = {
      id: messageId,
      text: messageText,
      sender: 'user', 
      timestamp: new Date()
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);

    // Show "thinking" state first
    setIsThinking(true);
    setMessageStatus({
      isLoading: true,
      isRetrying: false,
      retryAttempt: 0,
      error: null
    });

    // Prepare streaming message ID but don't add placeholder yet
    const streamingMsgId = messageId + 1000;

    // Set streaming timeout (30 seconds)
    streamingTimeoutRef.current = setTimeout(() => {
      if (isStreaming || isThinking) {
        console.warn('Streaming timeout - falling back to regular API');
        fallbackToRegularAPI(messageText, streamingMsgId);
      }
    }, 30000);

    try {
      // Small delay to show "thinking" state
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setIsThinking(false);
      setIsWaitingForResponse(true);
      setIsStreaming(true);
      
      setStreamingMessage({ id: streamingMsgId });
      
      let accumulatedText = '';
      let messageCreated = false;
      
      const result = await ChatService.sendMessageStream(messageText, {
        onChunk: (chunk) => {
          accumulatedText += chunk;
          
          // Create the message on first chunk
          if (!messageCreated) {
            const initialStreamingMessage = {
              id: streamingMsgId,
              text: accumulatedText,
              sender: 'assistant',
              timestamp: new Date(),
              isStreaming: true
            };
            setMessages(prev => [...prev, initialStreamingMessage]);
            messageCreated = true;
          } else {
            // Update existing message
            updateStreamingMessage(streamingMsgId, accumulatedText);
          }
        },
        onError: (error) => {
          clearTimeout(streamingTimeoutRef.current);
          
          // Create error message if we haven't created a message yet
          if (!messageCreated) {
            const errorMessage = {
              id: streamingMsgId,
              text: `❌ Connection lost. Click to retry.`,
              sender: 'assistant',
              timestamp: new Date(),
              isError: true,
              retryFunction: () => sendMessageWithRetry(messageText, Date.now())
            };
            setMessages(prev => [...prev, errorMessage]);
          } else {
            handleStreamingError(streamingMsgId, error, messageText);
          }
        },
        onComplete: (metadata) => {
          clearTimeout(streamingTimeoutRef.current);
          
          // If no message was created (empty response), create a placeholder
          if (!messageCreated) {
            const completedMessage = {
              id: streamingMsgId,
              text: "I received your message but couldn't generate a response. Please try again.",
              sender: 'assistant',
              timestamp: new Date(),
              isError: true,
              retryFunction: () => sendMessageWithRetry(messageText, Date.now())
            };
            setMessages(prev => [...prev, completedMessage]);
          } else {
            completeStreaming(streamingMsgId, metadata);
          }
        }
      });

      if (!result.success && result.error) {
        clearTimeout(streamingTimeoutRef.current);
        // Try fallback to regular API
        await fallbackToRegularAPI(messageText, streamingMsgId, messageCreated);
      }

    } catch (error) {
      clearTimeout(streamingTimeoutRef.current);
      
      // Create error message since streaming failed to start
      const errorMessage = {
        id: streamingMsgId,
        text: `❌ ${error.message || 'Unable to connect. Please try again.'}`,
        sender: 'assistant',
        timestamp: new Date(),
        isError: true,
        retryFunction: () => sendMessageWithRetry(messageText, Date.now())
      };
      setMessages(prev => [...prev, errorMessage]);
      
      setIsStreaming(false);
      setIsThinking(false);
      setIsWaitingForResponse(false);
      setStreamingMessage(null);
      setMessageStatus({
        isLoading: false,
        isRetrying: false,
        retryAttempt: 0,
        error: { userMessage: error.message }
      });
    }
  };

  const handleStreamingError = (streamingMsgId, error, originalMessage) => {
    setIsStreaming(false);
    setIsThinking(false);
    setIsWaitingForResponse(false);
    setStreamingMessage(null);
    
    // Replace streaming message with error and retry option
    setMessages(prev => prev.map(msg => 
      msg.id === streamingMsgId 
        ? {
            ...msg,
            text: `❌ Connection lost. Click to retry.`,
            isStreaming: false,
            isThinking: false,
            isError: true,
            retryFunction: () => sendMessageWithRetry(originalMessage, Date.now())
          }
        : msg
    ));

    setMessageStatus({
      isLoading: false,
      isRetrying: false,
      retryAttempt: 0,
      error: { userMessage: error }
    });
  };

  const completeStreaming = (streamingMsgId, metadata) => {
    setIsStreaming(false);
    setIsThinking(false);
    setIsWaitingForResponse(false);
    setStreamingMessage(null);
    
    // Mark message as complete
    setMessages(prev => prev.map(msg => 
      msg.id === streamingMsgId 
        ? { ...msg, isStreaming: false, isThinking: false }
        : msg
    ));

    setMessageStatus({
      isLoading: false,
      isRetrying: false,
      retryAttempt: 0,
      error: null
    });
  };

  const fallbackToRegularAPI = async (messageText, streamingMsgId, messageCreated = false) => {
    console.log('Falling back to regular API...');
    
    try {
      // Use the original non-streaming API
      const result = await ChatService.sendMessage(messageText, {
        maxRetries: 2,
        timeout: 15000
      });

      if (result.success) {
        if (messageCreated) {
          // Update existing message
          setMessages(prev => prev.map(msg => 
            msg.id === streamingMsgId 
              ? {
                  ...msg,
                  text: result.data.response,
                  isStreaming: false,
                  isThinking: false,
                  isFallback: true
                }
              : msg
          ));
        } else {
          // Create new message
          const fallbackMessage = {
            id: streamingMsgId,
            text: result.data.response,
            sender: 'assistant',
            timestamp: new Date(),
            isFallback: true
          };
          setMessages(prev => [...prev, fallbackMessage]);
        }
      } else {
        throw new Error(result.error.userMessage);
      }
    } catch (error) {
      handleStreamingError(streamingMsgId, 'Unable to get response. Please try again.', messageText);
    }

    setIsStreaming(false);
    setIsThinking(false);
    setIsWaitingForResponse(false);
    setStreamingMessage(null);
    setMessageStatus({
      isLoading: false,
      isRetrying: false,
      retryAttempt: 0,
      error: null
    });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleUploadSuccess = (result) => {
    // Add a message about successful upload
    const successMessage = {
      id: Date.now(),
      text: `✅ Successfully uploaded "${result.filename}"! I can now help you with questions about this manual. Try asking something specific about the equipment.`,
      sender: 'assistant',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, successMessage]);
  };

  const handleDocumentsUpdate = () => {
    setDocumentsRefresh(prev => prev + 1);
  };

  // Copy message to clipboard
  const handleCopy = async (messageId, messageText) => {
    try {
      // Strip markdown and get plain text for copying
      const plainText = messageText.replace(/\*\*(.*?)\*\*/g, '$1')
                                  .replace(/\*(.*?)\*/g, '$1')
                                  .replace(/`(.*?)`/g, '$1')
                                  .replace(/#{1,6}\s/g, '')
                                  .trim();
      
      await navigator.clipboard.writeText(plainText);
      setCopiedMessage(messageId);
      setTimeout(() => setCopiedMessage(null), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = messageText;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopiedMessage(messageId);
      setTimeout(() => setCopiedMessage(null), 2000);
    }
  };

  // Regenerate response
  const handleRegenerate = (messageId) => {
    // Find the user message that came before this assistant message
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex > 0) {
      const previousMessage = messages[messageIndex - 1];
      if (previousMessage.sender === 'user') {
        // Remove the current assistant message
        setMessages(prev => prev.filter(msg => msg.id !== messageId));
        
        // Resend the user message
        sendMessageWithRetry(previousMessage.text, Date.now());
      }
    }
  };

  // Get loading text based on current state
  const getLoadingText = () => {
    if (messageStatus.isRetrying) {
      return `Retrying connection (${messageStatus.retryAttempt}/3)...`;
    }
    if (isThinking) {
      return "Assistant is thinking...";
    }
    if (isStreaming) {
      return "Assistant is responding...";
    }
    if (messageStatus.isLoading) {
      return "Preparing response...";
    }
    if (!serviceStatus.isReady) {
      return "Services starting up...";
    }
    if (!isOnline) {
      return "You're offline - connect to send messages";
    }
    return "Ask about equipment maintenance...";
  };

  const isInputDisabled = (messageStatus.isLoading || isStreaming || isThinking || isWaitingForResponse) || !serviceStatus.isHealthy || !isOnline;

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ErrorBoundary>
        <div className="app">
        <header className="app-header">
          <div className="header-content">
            <div className="logo-container">
              <img 
                src="/LineLead_Logo.png" 
                alt="Line Lead" 
                className="line-lead-logo"
              />
            </div>
            <div className="header-controls">
              {!isOnline && (
                <span className="offline-indicator">
                  <WifiOff className="offline-icon" />
                  Offline
                </span>
              )}
              <button 
                className="upload-toggle-btn"
                onClick={() => setShowUpload(!showUpload)}
                title={showUpload ? "Hide Upload" : "Upload Manual"}
                aria-label={showUpload ? "Show chat" : "Show documents"}
              >
                {showUpload ? (
                  <MessageCircle className="toggle-icon" />
                ) : (
                  <BookOpen className="toggle-icon" />
                )}
              </button>
            </div>
          </div>
        </header>

        <div className="messages-container">
          {showUpload ? (
            <div className="upload-section">
              <ErrorBoundary>
                {/* Service Status Card - Only shown on documents page */}
                <div className="service-status-card">
                  <ServiceStatus onStatusChange={handleServiceStatusChange} />
                </div>


                
                <FileUpload 
                  onUploadSuccess={handleUploadSuccess}
                  onDocumentsUpdate={handleDocumentsUpdate}
                />
                <DocumentList refreshTrigger={documentsRefresh} />
              </ErrorBoundary>
            </div>
          ) : (
            <div className="messages-scroll aui-thread-viewport">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message aui-message ${message.sender === 'user' ? 'user-message aui-user-message' : 'assistant-message aui-assistant-message'} ${message.isError ? 'error-message' : ''} ${message.isStreaming ? 'streaming-message' : ''} message-container`}
                  onMouseEnter={() => message.sender === 'assistant' && !message.isStreaming && setHoveredMessage(message.id)}
                  onMouseLeave={() => setHoveredMessage(null)}
                >
                  {/* Assistant Avatar - only for assistant messages */}
                  {message.sender === 'assistant' && (
                    <img 
                      src="/images/assistant-avatar.png" 
                      alt="Line Lead Assistant"
                      className="assistant-avatar"
                    />
                  )}
                  
                  {/* Message Content */}
                  <div className="message-content-wrapper">
                    <div className="message-bubble aui-message-content">
                      <div className="message-text">
                        {message.sender === 'assistant' ? (
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              // Custom styling for lists
                              ul: ({children}) => <ul className="markdown-ul">{children}</ul>,
                              ol: ({children}) => <ol className="markdown-ol">{children}</ol>,
                              li: ({children}) => <li className="markdown-li">{children}</li>,
                              // Preserve bold formatting
                              strong: ({children}) => <strong className="markdown-strong">{children}</strong>,
                              // Add spacing for paragraphs
                              p: ({children}) => <p className="markdown-p">{children}</p>,
                              // Ensure line breaks are preserved
                              br: () => <br />,
                              // Code formatting
                              code: ({children}) => <code className="markdown-code">{children}</code>,
                              // Headers
                              h1: ({children}) => <h1 className="markdown-h1">{children}</h1>,
                              h2: ({children}) => <h2 className="markdown-h2">{children}</h2>,
                              h3: ({children}) => <h3 className="markdown-h3">{children}</h3>,
                            }}
                          >
                            {message.text}
                          </ReactMarkdown>
                        ) : (
                          message.text
                        )}
                        {message.isStreaming && <span className="streaming-cursor"></span>}
                        {message.isFallback && <span className="fallback-indicator"> (via fallback)</span>}
                      </div>
                      <div className="message-time">{formatTime(message.timestamp)}</div>
                      {message.isError && message.retryFunction && (
                        <button 
                          className="retry-message-btn"
                          onClick={message.retryFunction}
                        >
                          Try Again
                        </button>
                      )}
                    </div>
                    
                    {/* Message Actions - always render for assistant messages to prevent layout shift */}
                    {message.sender === 'assistant' && !message.isStreaming && (
                      <div className={`message-actions ${hoveredMessage === message.id ? 'visible' : 'hidden'}`}>
                        <button 
                          onClick={() => handleCopy(message.id, message.text)}
                          className="action-button"
                          aria-label="Copy message"
                          title="Copy"
                          disabled={hoveredMessage !== message.id}
                        >
                          {copiedMessage === message.id ? (
                            <Check className="action-icon copied" />
                          ) : (
                            <Copy className="action-icon" />
                          )}
                        </button>
                        
                        <button 
                          onClick={() => handleRegenerate(message.id)}
                          className="action-button"
                          aria-label="Regenerate response"
                          title="Regenerate"
                          disabled={hoveredMessage !== message.id}
                        >
                          <RefreshCw className="action-icon" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {/* Loading state - Avatar on left, loading content on right */}
              {(isThinking || isWaitingForResponse) && (
                <div className="message aui-message assistant-message aui-assistant-message">
                  {/* Avatar on the left */}
                  <img 
                    src="/images/assistant-avatar.png" 
                    alt="Line Lead Assistant"
                    className="assistant-avatar"
                  />
                  
                  {/* Loading content directly to the right of avatar */}
                  <div className="loading-content">
                    <div className="aui-loading-spinner" />
                    <span className="loading-text-inline">
                      {isThinking ? "Assistant is thinking..." : "Assistant is responding..."}
                    </span>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="input-container aui-composer">
          <div className="input-wrapper">
            <textarea
              className="message-input aui-composer-input"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={getLoadingText()}
              rows="1"
              disabled={isInputDisabled}
            />
            <button
              className="send-button aui-composer-send"
              onClick={(messageStatus.isLoading || isStreaming || isThinking || isWaitingForResponse) ? stopMessage : sendMessage}
              disabled={!(messageStatus.isLoading || isStreaming || isThinking || isWaitingForResponse) && (inputText.trim() === '' || !serviceStatus.isHealthy || !isOnline)}
              aria-label={(messageStatus.isLoading || isStreaming || isThinking || isWaitingForResponse) ? 'Stop generation' : 'Send message'}
            >
              {(messageStatus.isLoading || isStreaming || isThinking || isWaitingForResponse) ? (
                <Square className="send-icon" />
              ) : (
                <Send className="send-icon" />
              )}
            </button>
          </div>
          


          {/* Message queue indicator */}
          {messageQueue.length > 0 && (
            <div className="queue-indicator">
              📤 {messageQueue.length} message{messageQueue.length > 1 ? 's' : ''} queued
            </div>
          )}
        </div>
        </div>
        <DebugInfo />
      </ErrorBoundary>
    </AssistantRuntimeProvider>
  );
}

export default App;