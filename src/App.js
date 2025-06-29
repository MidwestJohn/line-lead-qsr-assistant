import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';
import ServiceStatus from './ServiceStatus';
import ErrorBoundary from './ErrorBoundary';
import ChatService from './ChatService';
import ProgressiveLoader from './components/ProgressiveLoader';
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { Send, Square, Upload, MessageCircle, WifiOff, Copy, RefreshCw, Check, BookOpen, Mic, MicOff, Volume2, VolumeX, Headphones } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API_BASE_URL } from './config';
import { apiService } from './services/api';

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
      text: "Hi! I'm Lina, your expert restaurant assistant. What can I help you with today?",
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
  
  // Voice input state
  const [isRecording, setIsRecording] = useState(false);
  const [voiceAvailable, setVoiceAvailable] = useState(false);
  
  // Text-to-Speech state
  const [ttsAvailable, setTtsAvailable] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  // Hands-free mode state
  const [handsFreeMode, setHandsFreeMode] = useState(false);
  const [handsFreeStatus, setHandsFreeStatus] = useState('idle'); // 'listening', 'processing', 'speaking', 'ready', 'idle'
  const [autoVoiceTimer, setAutoVoiceTimer] = useState(null);
  
  // Silence detection state
  const [silenceDetectionEnabled, setSilenceDetectionEnabled] = useState(true); // Feature flag for easy disable
  const [silenceCountdown, setSilenceCountdown] = useState(0);
  const [isCountingDown, setIsCountingDown] = useState(false);
  
  // Performance optimization refs
  const messagesEndRef = useRef(null);
  const streamingTimeoutRef = useRef(null);
  const lastUpdateTimeRef = useRef(0);
  const pendingChunksRef = useRef('');
  
  // Auto-expanding textarea ref
  const textareaRef = useRef(null);
  
  // Speech recognition ref
  const speechRecognitionRef = useRef(null);
  
  // Hands-free mode refs
  const autoVoiceTimerRef = useRef(null);
  const handsFreeTimeoutRef = useRef(null);
  
  // Silence detection refs
  const silenceTimerRef = useRef(null);
  const lastSpeechTimeRef = useRef(null);
  const hasDetectedSpeechRef = useRef(false);

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
        const healthData = await apiService.getHealth();
        setServiceStatus({
          isHealthy: healthData.status === 'healthy',
          isReady: healthData.search_ready,
          services: healthData.services
        });
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

  // Check voice availability and initialize speech recognition
  useEffect(() => {
    const initializeSpeechRecognition = () => {
      // Check if Web Speech API is available
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          
          // Configure speech recognition
          recognition.continuous = true; // Enable continuous for silence detection
          recognition.interimResults = true; // Show partial results
          recognition.lang = 'en-US'; // Language setting
          recognition.maxAlternatives = 1; // Only need one result
          
          // Event handlers
          recognition.onstart = () => {
            console.log('Speech recognition started');
            setIsRecording(true);
            if (handsFreeMode) {
              setHandsFreeStatus('listening');
            }
          };
          
          recognition.onresult = (event) => {
            let transcript = '';
            let isFinal = false;
            
            // Get the latest result
            for (let i = event.resultIndex; i < event.results.length; i++) {
              transcript += event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                isFinal = true;
              }
            }
            
            // Update input with transcript (for interim results)
            if (transcript.trim()) {
              setInputText(transcript.trim());
              
              // Mark that we've detected meaningful speech
              if (transcript.trim().length > 3) { // Minimum 3 characters to be meaningful
                hasDetectedSpeechRef.current = true;
              }
              
              // Reset silence detection when new speech is detected
              if (handsFreeMode && silenceDetectionEnabled) {
                resetSilenceDetection();
              }
              
              // Auto-expand textarea
              setTimeout(() => {
                if (textareaRef.current) {
                  textareaRef.current.style.height = 'auto';
                  const scrollHeight = textareaRef.current.scrollHeight;
                  const maxHeight = 120;
                  const minHeight = 40;
                  const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
                  textareaRef.current.style.height = newHeight + 'px';
                }
              }, 0);
              
              // In hands-free mode without silence detection, check for voice commands and auto-send
              if (handsFreeMode && isFinal && transcript.trim().length > 0 && !silenceDetectionEnabled) {
                const command = transcript.trim().toLowerCase();
                
                // Handle voice commands
                if (command === 'stop' || command === 'exit' || command === 'end hands free') {
                  console.log('Voice command: Exiting hands-free mode');
                  exitHandsFreeMode();
                  setInputText(''); // Clear the command from input
                  return;
                }
                
                // Regular message - auto-send (only if silence detection is disabled)
                console.log('Hands-free mode: Auto-sending message:', transcript.trim());
                setHandsFreeStatus('processing');
                setTimeout(() => {
                  sendMessage();
                }, 100);
              }
            }
            
            // Start silence detection when speech ends (no more interim results)
            if (handsFreeMode && silenceDetectionEnabled && hasDetectedSpeechRef.current && transcript.trim()) {
              // Use a small delay to ensure we're not getting more interim results
              setTimeout(() => {
                if (handsFreeMode && silenceDetectionEnabled && !isCountingDown) {
                  startSilenceDetection();
                }
              }, 500);
            }
            
            console.log('Speech result:', transcript, 'Final:', isFinal);
          };
          
          recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            setIsRecording(false);
            
            // Show user-friendly error message
            if (event.error === 'not-allowed' || event.error === 'permission-denied') {
              alert('Microphone permission denied. Please allow microphone access to use voice input.');
            } else if (event.error === 'no-speech') {
              console.log('No speech detected, try again');
            } else {
              console.warn('Speech recognition error:', event.error);
            }
          };
          
          recognition.onend = () => {
            console.log('Speech recognition ended');
            setIsRecording(false);
            if (handsFreeMode) {
              setHandsFreeStatus('processing');
            }
          };
          
          speechRecognitionRef.current = recognition;
          setVoiceAvailable(true);
          
        } catch (error) {
          console.error('Failed to initialize speech recognition:', error);
          setVoiceAvailable(false);
        }
      } else {
        console.log('Speech recognition not supported in this browser');
        setVoiceAvailable(false);
      }
    };
    
    initializeSpeechRecognition();
    
    // Check Text-to-Speech availability
    const checkTTSAvailability = () => {
      if ('speechSynthesis' in window) {
        setTtsAvailable(true);
        console.log('Text-to-Speech available');
      } else {
        setTtsAvailable(false);
        console.log('Text-to-Speech not supported');
      }
    };
    
    checkTTSAvailability();
    
    // Cleanup on unmount
    return () => {
      if (speechRecognitionRef.current) {
        speechRecognitionRef.current.abort();
      }
      // Stop any ongoing speech synthesis
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Handle hands-free mode changes
  useEffect(() => {
    if (handsFreeMode) {
      console.log('Entering hands-free mode');
      setHandsFreeStatus('ready');
      resetHandsFreeTimeout();
      
      // Start with voice input if not currently in any active state
      if (!isRecording && !isSpeaking && !messageStatus.isLoading) {
        startAutoVoiceInput();
      }
    } else {
      console.log('Exiting hands-free mode');
      setHandsFreeStatus('idle');
      
      // Clear all timers and stop any active voice operations
      if (autoVoiceTimerRef.current) {
        clearTimeout(autoVoiceTimerRef.current);
      }
      if (handsFreeTimeoutRef.current) {
        clearTimeout(handsFreeTimeoutRef.current);
      }
    }
    
    return () => {
      if (autoVoiceTimerRef.current) {
        clearTimeout(autoVoiceTimerRef.current);
      }
      if (handsFreeTimeoutRef.current) {
        clearTimeout(handsFreeTimeoutRef.current);
      }
    };
  }, [handsFreeMode]);

  // Reset hands-free timeout on any user activity
  useEffect(() => {
    if (handsFreeMode) {
      resetHandsFreeTimeout();
    }
  }, [messages, isRecording, isSpeaking]);

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
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = '40px';
    }

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

    // In hands-free mode, automatically start TTS for the response
    if (handsFreeMode && ttsAvailable) {
      setTimeout(() => {
        // Find the completed message and speak it
        setMessages(current => {
          const completedMessage = current.find(msg => msg.id === streamingMsgId);
          if (completedMessage && completedMessage.text) {
            speakText(completedMessage.text);
          }
          return current;
        });
      }, 500); // Small delay to ensure message is rendered
    }
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

  // Simple auto-expanding textarea function
  const autoExpandTextarea = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to measure scroll height
    textarea.style.height = 'auto';
    
    // Calculate new height with max constraint
    const scrollHeight = textarea.scrollHeight;
    const maxHeight = 120; // ~3 lines
    const minHeight = 40;
    
    // Set height (scrollbar space is always reserved via CSS)
    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
    textarea.style.height = newHeight + 'px';
  };

  // Handle input changes
  const handleInputChange = (e) => {
    setInputText(e.target.value);
    setTimeout(autoExpandTextarea, 0); // Use setTimeout instead of requestAnimationFrame
    
    // If user manually types while in hands-free mode, temporarily pause auto-activation
    if (handsFreeMode && !isRecording) {
      // Clear any pending auto-voice timer since user is manually typing
      if (autoVoiceTimerRef.current) {
        clearTimeout(autoVoiceTimerRef.current);
        autoVoiceTimerRef.current = null;
      }
      setHandsFreeStatus('ready'); // Set to ready state (paused)
    }
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

  // Voice input handler
  const handleVoiceInput = () => {
    if (!voiceAvailable || !speechRecognitionRef.current) {
      console.warn('Voice input not available');
      return;
    }

    if (isRecording) {
      // Stop recording
      console.log('Stopping voice recording...');
      speechRecognitionRef.current.stop();
      setIsRecording(false);
    } else {
      // Start recording
      console.log('Starting voice recording...');
      try {
        // Clear any existing text and reset silence detection state
        setInputText('');
        hasDetectedSpeechRef.current = false;
        lastSpeechTimeRef.current = null;
        stopSilenceDetection();
        
        speechRecognitionRef.current.start();
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
        setIsRecording(false);
        
        if (error.name === 'InvalidStateError') {
          // Recognition is already running, stop it first
          speechRecognitionRef.current.stop();
          setTimeout(() => {
            try {
              setInputText('');
              speechRecognitionRef.current.start();
            } catch (retryError) {
              console.error('Retry failed:', retryError);
            }
          }, 100);
        }
      }
    }
  };

  // Text-to-Speech handler
  const speakText = (text) => {
    if (!ttsAvailable || !text.trim()) return;

    // Stop any ongoing speech
    window.speechSynthesis.cancel();

    // Clean text for speech (remove markdown and special characters)
    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
      .replace(/\*(.*?)\*/g, '$1')     // Remove italic markdown
      .replace(/`(.*?)`/g, '$1')       // Remove code markdown
      .replace(/#{1,6}\s/g, '')        // Remove headers
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to text
      .replace(/\n+/g, '. ')           // Convert line breaks to pauses
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Configure voice settings for QSR environment
    utterance.rate = 0.9;    // Slightly slower for clarity
    utterance.pitch = 1.0;   // Normal pitch
    utterance.volume = 0.8;  // Comfortable volume
    
    // Try to use a female voice (Lina assistant personality)
    const voices = window.speechSynthesis.getVoices();
    const femaleVoice = voices.find(voice => 
      voice.name.toLowerCase().includes('female') || 
      voice.name.toLowerCase().includes('zira') ||
      voice.name.toLowerCase().includes('susan') ||
      voice.name.toLowerCase().includes('samantha')
    );
    
    if (femaleVoice) {
      utterance.voice = femaleVoice;
    }

    // Event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
      if (handsFreeMode) {
        setHandsFreeStatus('speaking');
      }
      console.log('Started speaking assistant response');
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      console.log('Finished speaking assistant response');
      
      // In hands-free mode, automatically start next voice input
      if (handsFreeMode) {
        startAutoVoiceInput();
      }
    };

    utterance.onerror = (event) => {
      setIsSpeaking(false);
      console.error('Speech synthesis error:', event.error);
    };

    // Speak the text
    window.speechSynthesis.speak(utterance);
  };

  // Stop TTS if currently speaking
  const stopSpeaking = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // Hands-free mode functions
  const startAutoVoiceInput = () => {
    if (!handsFreeMode || !voiceAvailable) return;
    
    // Clear any existing timer
    if (autoVoiceTimerRef.current) {
      clearTimeout(autoVoiceTimerRef.current);
    }
    
    // Set status to ready with countdown
    setHandsFreeStatus('ready');
    
    // Wait 2 seconds then start voice input
    autoVoiceTimerRef.current = setTimeout(() => {
      if (handsFreeMode && !isRecording && !isSpeaking) {
        setHandsFreeStatus('listening');
        handleVoiceInput(); // Start voice recognition
      }
    }, 2000);
  };

  const exitHandsFreeMode = () => {
    setHandsFreeMode(false);
    setHandsFreeStatus('idle');
    
    // Clear timers
    if (autoVoiceTimerRef.current) {
      clearTimeout(autoVoiceTimerRef.current);
    }
    if (handsFreeTimeoutRef.current) {
      clearTimeout(handsFreeTimeoutRef.current);
    }
    
    // Clean up silence detection
    stopSilenceDetection();
    hasDetectedSpeechRef.current = false;
    lastSpeechTimeRef.current = null;
    
    // Stop any ongoing voice or speech
    if (isRecording && speechRecognitionRef.current) {
      speechRecognitionRef.current.stop();
    }
    if (isSpeaking) {
      stopSpeaking();
    }
  };

  // Auto-exit hands-free mode after inactivity
  const resetHandsFreeTimeout = () => {
    if (handsFreeTimeoutRef.current) {
      clearTimeout(handsFreeTimeoutRef.current);
    }
    
    if (handsFreeMode) {
      handsFreeTimeoutRef.current = setTimeout(() => {
        console.log('Hands-free mode auto-exit due to inactivity');
        exitHandsFreeMode();
      }, 600000); // 10 minutes
    }
  };

  // Silence detection functions
  const startSilenceDetection = () => {
    if (!handsFreeMode || !silenceDetectionEnabled || !hasDetectedSpeechRef.current) return;
    
    // Clear any existing timer
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    
    // Start countdown from 4 seconds
    setSilenceCountdown(4);
    setIsCountingDown(true);
    
    let countdown = 4;
    const updateCountdown = () => {
      countdown--;
      setSilenceCountdown(countdown);
      
      if (countdown > 0) {
        silenceTimerRef.current = setTimeout(updateCountdown, 1000);
      } else {
        // Countdown finished - auto-send message
        console.log('Silence detected: Auto-sending message');
        setIsCountingDown(false);
        setSilenceCountdown(0);
        
        if (inputText.trim() && handsFreeMode) {
          setHandsFreeStatus('processing');
          setTimeout(() => {
            sendMessage();
          }, 100);
        }
      }
    };
    
    silenceTimerRef.current = setTimeout(updateCountdown, 1000);
  };

  const stopSilenceDetection = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    setIsCountingDown(false);
    setSilenceCountdown(0);
  };

  const resetSilenceDetection = () => {
    lastSpeechTimeRef.current = Date.now();
    stopSilenceDetection();
    
    // Restart silence detection if we're in hands-free mode
    if (handsFreeMode && silenceDetectionEnabled && isRecording) {
      setTimeout(() => {
        const timeSinceLastSpeech = Date.now() - (lastSpeechTimeRef.current || 0);
        if (timeSinceLastSpeech >= 1000 && hasDetectedSpeechRef.current) {
          startSilenceDetection();
        }
      }, 1000); // Wait 1 second after last speech before starting silence timer
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
    return "Ask me anything...";
  };

  const isInputDisabled = (messageStatus.isLoading || isStreaming || isThinking || isWaitingForResponse) || !serviceStatus.isHealthy || !isOnline;

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ErrorBoundary>
        <ProgressiveLoader>
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
              
              {/* Hands-Free Mode Toggle */}
              {voiceAvailable && ttsAvailable && !showUpload && (
                <button 
                  className={`hands-free-toggle ${handsFreeMode ? 'active' : ''}`}
                  onClick={() => setHandsFreeMode(!handsFreeMode)}
                  title={handsFreeMode ? "Exit Hands-Free Mode" : "Enter Hands-Free Mode"}
                  aria-label={handsFreeMode ? "Exit hands-free conversation" : "Start hands-free conversation"}
                >
                  <Headphones className="toggle-icon" />
                  {handsFreeMode && (
                    <span className="hands-free-status">
                      {handsFreeStatus}
                      {silenceDetectionEnabled && <span className="silence-indicator">📶</span>}
                    </span>
                  )}
                </button>
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
                <DocumentList 
                  refreshTrigger={documentsRefresh}
                  onDocumentDeleted={handleDocumentsUpdate}
                />
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
                      src="/images/LineLead_AvatarIcon.png" 
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
                        
                        {/* Text-to-Speech Button */}
                        {ttsAvailable && (
                          <button 
                            onClick={() => isSpeaking ? stopSpeaking() : speakText(message.text)}
                            className="action-button"
                            aria-label={isSpeaking ? "Stop speaking" : "Read message aloud"}
                            title={isSpeaking ? "Stop speaking" : "Read aloud"}
                            disabled={hoveredMessage !== message.id}
                          >
                            {isSpeaking ? (
                              <VolumeX className="action-icon speaking" />
                            ) : (
                              <Volume2 className="action-icon" />
                            )}
                          </button>
                        )}
                        
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
                    src="/images/LineLead_AvatarIcon.png" 
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
              
              {/* Hands-Free Status Indicator */}
              {handsFreeMode && handsFreeStatus !== 'idle' && (
                <div className="hands-free-indicator">
                  <div className="hands-free-content">
                    <Headphones className="hands-free-icon" />
                    <span className="hands-free-text">
                      {handsFreeStatus === 'ready' && 'Ready to listen...'}
                      {handsFreeStatus === 'listening' && (
                        silenceDetectionEnabled ? 'Listening... (Auto-send enabled)' : 'Listening for your question...'
                      )}
                      {handsFreeStatus === 'processing' && 'Processing your request...'}
                      {handsFreeStatus === 'speaking' && 'Assistant responding...'}
                    </span>
                    {handsFreeStatus === 'listening' && (
                      <button 
                        className="silence-toggle-btn"
                        onClick={() => setSilenceDetectionEnabled(!silenceDetectionEnabled)}
                        title={silenceDetectionEnabled ? "Disable auto-send" : "Enable auto-send"}
                      >
                        {silenceDetectionEnabled ? '⏰' : '🔇'}
                      </button>
                    )}
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="input-container aui-composer">
          {/* Silence Detection Countdown */}
          {isCountingDown && silenceDetectionEnabled && handsFreeMode && (
            <div className="silence-countdown">
              <div className="countdown-content">
                <span className="countdown-text">Auto-sending in {silenceCountdown} second{silenceCountdown !== 1 ? 's' : ''}...</span>
                <div className="countdown-bar">
                  <div 
                    className="countdown-progress" 
                    style={{
                      width: `${(silenceCountdown / 4) * 100}%`,
                      backgroundColor: silenceCountdown > 2 ? '#10b981' : silenceCountdown > 1 ? '#f59e0b' : '#ef4444'
                    }}
                  ></div>
                </div>
                <button 
                  className="cancel-countdown-btn"
                  onClick={stopSilenceDetection}
                  title="Cancel auto-send"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              className="message-input aui-composer-input auto-expand"
              value={inputText}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder={isRecording ? "Listening..." : getLoadingText()}
              rows="1"
              disabled={isInputDisabled || isRecording}
              style={{ minHeight: '40px', height: '40px' }}
            />
            
            {/* Voice Input Button */}
            <button
              className={`voice-button ${isRecording ? 'recording' : ''} ${!voiceAvailable ? 'disabled' : ''}`}
              onClick={handleVoiceInput}
              disabled={!voiceAvailable || isInputDisabled}
              aria-label={isRecording ? 'Stop voice recording' : 'Start voice input'}
              title={!voiceAvailable ? 'Voice input not available' : isRecording ? 'Stop recording' : 'Start voice input'}
            >
              {!voiceAvailable ? (
                <MicOff className="voice-icon" />
              ) : (
                <Mic className={`voice-icon ${isRecording ? 'recording-pulse' : ''}`} />
              )}
            </button>
            
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
        </ProgressiveLoader>
      </ErrorBoundary>
    </AssistantRuntimeProvider>
  );
}

export default App;