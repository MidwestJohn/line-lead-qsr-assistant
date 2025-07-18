import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';
import ServiceStatus from './ServiceStatus';
import ErrorBoundary from './ErrorBoundary';
import ChatService from './ChatService';
import ProgressiveLoader from './components/ProgressiveLoader';
import ImageCitation from './components/ImageCitation';

import ProcessingDashboard from './components/ProcessingDashboard';
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { Send, Square, MessageCircle, WifiOff, Copy, RefreshCw, Check, BookOpen, Mic, MicOff, Volume2, VolumeX, Headphones } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { apiService } from './services/api';
import Phase3IntegrationTest from './pages/Phase3IntegrationTest';
import Phase4AudioTest from './pages/Phase4AudioTest';


function App() {
  
  // Check for test mode
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('test') === 'phase3') {
    return <Phase3IntegrationTest />;
  }
  if (urlParams.get('test') === 'phase4') {
    return <Phase4AudioTest />;
  }
  
  // Assistant UI Runtime - memoized to prevent infinite re-renders
  const onNewMessage = useCallback(async () => {
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
  const [showProcessing, setShowProcessing] = useState(false);
  const [documentsRefresh, setDocumentsRefresh] = useState(0);
  
  // Service status and resilience state
  const [serviceStatus, setServiceStatus] = useState({
    isHealthy: false,
    isReady: false,
    error: null
  });
  
  // Debug service status changes
  useEffect(() => {
    console.log('🔄 Service status changed:', serviceStatus);
  }, [serviceStatus]);
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
  const speechRecognitionRunningRef = useRef(false);
  const messageBeingSentRef = useRef(false);
  const lastSentTranscriptRef = useRef('');
  
  // Multimodal citations state (always enabled)
  const [currentEquipment, setCurrentEquipment] = useState(null);

  
  // Text-to-Speech state
  const [ttsAvailable, setTtsAvailable] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  // Hands-free mode state
  const [handsFreeMode, setHandsFreeMode] = useState(false);
  const [handsFreeStatus, setHandsFreeStatus] = useState('idle'); // 'listening', 'processing', 'speaking', 'ready', 'idle'

  
  // Silence detection state
  const [silenceDetectionEnabled] = useState(true); // Feature flag for easy disable

  const [isCountingDown, setIsCountingDown] = useState(false);
  
  // Keep silence detection ref in sync
  useEffect(() => {
    silenceDetectionStateRef.current = silenceDetectionEnabled;
  }, [silenceDetectionEnabled]);
  
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
  const handsFreeStateRef = useRef(false);
  const silenceDetectionStateRef = useRef(true);
  const ttsAvailableRef = useRef(false);
  const voiceAvailableRef = useRef(false);
  const currentTTSMessageIdRef = useRef(null);
  const messageSentRef = useRef(false);
  const streamingTTSRef = useRef({ isActive: false, spokenText: '', remainingText: '', isCompleting: false });
  
  // Transcript-based silence detection refs
  const silenceTimerRef = useRef(null);
  const transcriptDebounceTimerRef = useRef(null);
  const lastTranscriptUpdateRef = useRef(null);
  const currentTranscriptRef = useRef('');
  const transcriptWordCountRef = useRef(0);

  // ElevenLabs API configuration
  const elevenlabsApiKey = process.env.REACT_APP_ELEVENLABS_API_KEY;
  const currentElevenLabsAudioRef = useRef(null);
  
  // TTS Queue system with rate-limited audio pre-loading
  const ttsQueueRef = useRef([]);
  const ttsPlayingRef = useRef(false);
  const audioBufferRef = useRef(new Map()); // Pre-generated audio blobs
  const apiCallsInProgressRef = useRef(0);
  const maxConcurrentCalls = 2; // Limit concurrent ElevenLabs API calls
  
  // ElevenLabs API function with retry logic for rate limits
  const generateElevenLabsAudio = async (text, retryCount = 0) => {
    if (!elevenlabsApiKey) {
      throw new Error('ElevenLabs API key not available');
    }

    try {
      const response = await fetch('https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM', {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': elevenlabsApiKey
        },
        body: JSON.stringify({
          text: text,
          model_id: "eleven_multilingual_v2",
          voice_settings: {
            stability: 0.8,        // High for reliability and no hallucinations
            similarity_boost: 0.9, // High for voice consistency
            style: 0.4,           // TEST: Upper limit of safe range for maximum personality
            use_speaker_boost: true
          }
        })
      });

      if (response.status === 429 && retryCount < 3) {
        // Rate limited - wait and retry with exponential backoff
        const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
        console.log(`🔄 Rate limited, retrying in ${delay}ms (attempt ${retryCount + 1}/3)`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return generateElevenLabsAudio(text, retryCount + 1);
      }

      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.status} ${response.statusText}`);
      }

      return response.blob();
    } catch (error) {
      if (retryCount < 3 && (error.message.includes('429') || error.message.includes('rate'))) {
        const delay = Math.pow(2, retryCount) * 1000;
        console.log(`🔄 API error, retrying in ${delay}ms (attempt ${retryCount + 1}/3):`, error.message);
        await new Promise(resolve => setTimeout(resolve, delay));
        return generateElevenLabsAudio(text, retryCount + 1);
      }
      throw error;
    }
  };

  const playElevenLabsAudio = (audioBlob) => {
    return new Promise((resolve, reject) => {
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      currentElevenLabsAudioRef.current = audio;
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        currentElevenLabsAudioRef.current = null;
        resolve();
      };
      
      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        currentElevenLabsAudioRef.current = null;
        reject(new Error('Audio playback failed'));
      };
      
      audio.play().catch(reject);
    });
  };

  // Rate-limited pre-generation to avoid 429 errors
  const preGenerateAudio = async (queueId, text) => {
    // Wait if too many concurrent API calls
    while (apiCallsInProgressRef.current >= maxConcurrentCalls) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    apiCallsInProgressRef.current++;
    
    try {
      console.log(`🎵 Pre-generating audio for queue item ${queueId} (concurrent: ${apiCallsInProgressRef.current}):`, text.substring(0, 30) + '...');
      const audioBlob = await generateElevenLabsAudio(text);
      audioBufferRef.current.set(queueId, audioBlob);
      console.log(`🎵 Pre-generation complete for queue item ${queueId}`);
    } catch (error) {
      console.error(`🔊 Pre-generation failed for queue item ${queueId}:`, error.message);
      audioBufferRef.current.set(queueId, null); // Mark as failed
    } finally {
      apiCallsInProgressRef.current--;
    }
  };

  // TTS Queue processor with pre-loading for gap-free playback
  const processTTSQueue = async () => {
    if (ttsPlayingRef.current || ttsQueueRef.current.length === 0) {
      return;
    }

    ttsPlayingRef.current = true;
    console.log('🎵 Processing TTS queue, items:', ttsQueueRef.current.length);

    // Start pre-generating items with rate limiting (max 2 concurrent)
    const queueItems = [...ttsQueueRef.current];
    queueItems.slice(0, maxConcurrentCalls).forEach((item) => {
      if (!audioBufferRef.current.has(item.queueId)) {
        preGenerateAudio(item.queueId, item.text);
      }
    });

    while (ttsQueueRef.current.length > 0) {
      const queueItem = ttsQueueRef.current.shift();
      const { text, type, resolve, reject, queueId } = queueItem;

      try {
        console.log(`🎵 Playing ${type}:`, text.substring(0, 30) + '...');
        
        // Set speaking state
        setIsSpeaking(true);
        if (handsFreeStateRef.current) {
          setHandsFreeStatus('speaking');
        }

        // Optimized audio retrieval with reduced wait time
        let audioBlob = audioBufferRef.current.get(queueId);
        
        if (audioBlob === undefined) {
          // Still generating - wait with shorter intervals for faster response
          console.log(`🎵 Waiting for pre-generation of queue item ${queueId}...`);
          let attempts = 0;
          while (audioBlob === undefined && attempts < 30) { // Reduced from 50 to 30 (3s max)
            await new Promise(resolve => setTimeout(resolve, 50)); // Reduced from 100ms to 50ms
            audioBlob = audioBufferRef.current.get(queueId);
            attempts++;
          }
        }
        
        if (audioBlob === null) {
          // Pre-generation failed (likely rate limited) - generate now
          console.log(`🔄 Pre-generation failed, generating now for queue item ${queueId}`);
          audioBlob = await generateElevenLabsAudio(text);
        }
        
        if (audioBlob === undefined) {
          // Still generating or timeout - fallback generation
          console.log(`⏰ Pre-generation timeout, fallback generation for queue item ${queueId}`);
          audioBlob = await generateElevenLabsAudio(text);
        }

        // Clean up buffer
        audioBufferRef.current.delete(queueId);
        
        // Play immediately - no generation delay!
        await playElevenLabsAudio(audioBlob);
        
        console.log(`🎵 Completed ${type} (gap-free)`);
        resolve();
      } catch (error) {
        console.error(`🔊 ${type} failed:`, error.message);
        audioBufferRef.current.delete(queueItem.queueId);
        reject(error);
      }
    }

    // Reset speaking state after queue is empty
    setIsSpeaking(false);
    ttsPlayingRef.current = false;

    // In hands-free mode, restart voice input after all TTS completes
    if (handsFreeStateRef.current) {
      console.log('🎵 All TTS completed, restarting voice input');
      setHandsFreeStatus('ready');
      // Reduced delay for faster conversation flow
      setTimeout(() => startAutoVoiceInput(), 500); // Reduced from 1000ms to 500ms
    }
  };

  // Add TTS to queue with pre-generation for gap-free playback
  const queueTTS = (text, type = 'chunk') => {
    return new Promise((resolve, reject) => {
      const queueId = `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const queueItem = { text, type, resolve, reject, queueId };
      
      ttsQueueRef.current.push(queueItem);
      console.log(`🎵 Queued ${type} (ID: ${queueId}), queue length:`, ttsQueueRef.current.length);
      
      // Start pre-generating immediately for this item
      if (!audioBufferRef.current.has(queueId)) {
        preGenerateAudio(queueId, text);
      }
      
      processTTSQueue().catch(console.error);
    });
  };

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
        console.log('🔍 Health data received:', {
          status: healthData.status,
          search_ready: healthData.search_ready,
          services: Object.keys(healthData.services || {})
        });
        
        const newServiceStatus = {
          isHealthy: healthData.status === 'healthy' || healthData.status === 'degraded',
          isReady: healthData.search_ready,
          services: healthData.services
        };
        
        console.log('📊 Setting service status:', newServiceStatus);
        setServiceStatus(newServiceStatus);
      } catch (error) {
        console.error('Service check failed:', error);
        setServiceStatus({
          isHealthy: false,
          isReady: false,
          error: error.message
        });
      }
    };
    
    // Initial check with a small delay to ensure connection is established
    setTimeout(() => {
      console.log('🚀 Starting initial service check...');
      checkServices();
    }, 1000);
    
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
            console.log('📢 Speech recognition started - handsFreeMode:', handsFreeStateRef.current, 'silenceDetectionEnabled:', silenceDetectionStateRef.current);
            speechRecognitionRunningRef.current = true;
            setIsRecording(true);
            messageSentRef.current = false; // Reset message sent flag for new session
            streamingTTSRef.current = { isActive: false, spokenText: '', remainingText: '' }; // Reset streaming TTS
            if (handsFreeStateRef.current) {
              setHandsFreeStatus('listening');
            }
          };
          
          recognition.onresult = (event) => {
            let transcript = '';
            let isFinal = false;
            
            // Get ALL results to build complete transcript
            for (let i = 0; i < event.results.length; i++) {
              transcript += event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                isFinal = true;
              }
            }
            
            console.log('🎙️ Raw transcript accumulation:', transcript, 'isFinal:', isFinal, 'resultIndex:', event.resultIndex, 'totalResults:', event.results.length);
            
            // Update input with transcript (for interim results)
            if (transcript.trim()) {
              setInputText(transcript.trim());
              
              // If user continues speaking with NEW content during countdown, cancel the auto-send
              if (!isFinal && isCountingDown) {
                const currentLength = currentTranscriptRef.current.length;
                const newLength = transcript.trim().length;
                
                // Only cancel if transcript is significantly longer (user added new words)
                if (newLength > currentLength + 5) { // 5+ new characters = continuing sentence
                  console.log('🗣️ User continuing sentence - canceling countdown. Old:', currentLength, 'New:', newLength);
                  stopTranscriptTimer();
                  setIsCountingDown(false);
                  messageSentRef.current = false; // Reset send flag
                } else {
                  console.log('📝 Minor transcript update during countdown, not canceling');
                }
              }
              
              // Update transcript timestamp for silence detection
              if (handsFreeStateRef.current && silenceDetectionStateRef.current) {
                updateTranscriptTimestamp(transcript.trim(), isFinal);
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
              
              // Handle voice commands and auto-send (only when silence detection is disabled)
              if (handsFreeStateRef.current && isFinal && transcript.trim().length > 0 && !silenceDetectionStateRef.current) {
                const command = transcript.trim().toLowerCase();
                
                // Handle voice commands
                if (command === 'stop' || command === 'exit' || command === 'end hands free') {
                  console.log('Voice command: Exiting hands-free mode');
                  exitHandsFreeMode();
                  setInputText(''); // Clear the command from input
                  return;
                }
                
                // Regular message - auto-send (only if silence detection is disabled)
                console.log('Hands-free mode (no silence detection): Auto-sending message:', transcript.trim());
                setHandsFreeStatus('processing');
                setTimeout(() => {
                  sendMessage();
                }, 100);
              }
              
              // Handle voice commands even with silence detection enabled
              if (handsFreeStateRef.current && isFinal && silenceDetectionStateRef.current) {
                const command = transcript.trim().toLowerCase();
                if (command === 'stop' || command === 'exit' || command === 'end hands free') {
                  console.log('Voice command detected: Exiting hands-free mode');
                  exitHandsFreeMode();
                  setInputText(''); // Clear the command from input
                  return;
                }
                
                // SMART DELAY: 2-second countdown on final result (allows thinking time)
                if (transcriptWordCountRef.current >= 2 && !messageSentRef.current && !messageBeingSentRef.current) {
                  const finalResultTime = performance.now();
                  console.log('⏱️ Final result received at:', finalResultTime);
                  console.log('⏱️ Starting 2-second smart delay for FULL transcript:', currentTranscriptRef.current);
                  
                  // Clear any existing timers
                  stopTranscriptTimer();
                  
                  // Start 2-second countdown with visual feedback

                  setIsCountingDown(true);
                  
                  let countdown = 2;
                  const smartDelayTimer = () => {
                    countdown--;

                    
                    if (countdown > 0) {
                      silenceTimerRef.current = setTimeout(smartDelayTimer, 1000);
                    } else {
                      // 2 seconds elapsed - now send the FULL accumulated message
                      if (!messageSentRef.current && !messageBeingSentRef.current && handsFreeStateRef.current) {
                        const fullTranscript = currentTranscriptRef.current.trim();
                        console.log('⚡ Smart delay complete - sending FULL message:', fullTranscript);
                        
                        messageSentRef.current = true;
                        setIsCountingDown(false);
                        
                        // Stop speech recognition
                        if (speechRecognitionRef.current) {
                          speechRecognitionRef.current.stop();
                        }
                        
                        setIsRecording(false);
                        setHandsFreeStatus('processing');
                        
                        // Send the FULL accumulated message
                        sendMessageWithText(fullTranscript);
                      }
                    }
                  };
                  
                  // Start the countdown
                  smartDelayTimer();
                  return; // Exit early to prevent other processing
                }
              }
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
            const speechEndTime = performance.now();
            console.log('🎤 Speech ended at:', speechEndTime);
            speechRecognitionRunningRef.current = false;
            setIsRecording(false);
            
            // Enhanced deduplication check
            if (messageSentRef.current || messageBeingSentRef.current) {
              console.log('📤 Message already sent/being sent, skipping onend send');
              return;
            }
            
            // FALLBACK auto-send on speech end if we have enough content (only if not already sent)
            if (handsFreeStateRef.current && silenceDetectionStateRef.current && transcriptWordCountRef.current >= 2) {
              console.log('⚡ FALLBACK auto-send path (onend):', currentTranscriptRef.current);
              
              // Clear any countdown since we're auto-sending immediately
              stopTranscriptTimer();
              
              const transcriptToSend = currentTranscriptRef.current.trim();
              if (transcriptToSend && !messageBeingSentRef.current) {
                const sendStartTime = performance.now();
                console.log('📤 Message send start at:', sendStartTime, 'Delay from speech end:', sendStartTime - speechEndTime, 'ms');
                
                messageSentRef.current = true; // Mark as sent to prevent further duplicates
                setHandsFreeStatus('processing');
                // Send immediately without any delays
                sendMessageWithText(transcriptToSend);
              }
            } else if (handsFreeMode) {
              setHandsFreeStatus('processing');
            }
          };
          
          speechRecognitionRef.current = recognition;
          setVoiceAvailable(true);
          voiceAvailableRef.current = true;
          
        } catch (error) {
          console.error('Failed to initialize speech recognition:', error);
          setVoiceAvailable(false);
          voiceAvailableRef.current = false;
        }
      } else {
        console.log('Speech recognition not supported in this browser');
        setVoiceAvailable(false);
        voiceAvailableRef.current = false;
      }
    };
    
    initializeSpeechRecognition();
    
    // Check Text-to-Speech availability
    const checkTTSAvailability = () => {
      if ('speechSynthesis' in window) {
        setTtsAvailable(true);
        ttsAvailableRef.current = true;
        console.log('Text-to-Speech available');
      } else {
        setTtsAvailable(false);
        ttsAvailableRef.current = false;
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
    console.log('🎧 Hands-free mode useEffect triggered. handsFreeMode:', handsFreeMode);
    handsFreeStateRef.current = handsFreeMode; // Keep ref in sync
    
    if (handsFreeMode) {
      console.log('✅ Entering hands-free mode');
      setHandsFreeStatus('ready');
      resetHandsFreeTimeout();
      
      // Start with voice input if not currently in any active state
      if (!isRecording && !isSpeaking && !messageStatus.isLoading) {
        console.log('🎤 Auto-starting voice input');
        startAutoVoiceInput();
      } else {
        console.log('⏸️ Not auto-starting voice input - isRecording:', isRecording, 'isSpeaking:', isSpeaking, 'isLoading:', messageStatus.isLoading);
      }
    } else {
      console.log('❌ Exiting hands-free mode');
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

    // We'll handle this differently to avoid circular dependencies
    // For now, just clear the queue - could implement proper retry logic later
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

  // Helper function to send message with specific text (for auto-send from speech recognition)
  const sendMessageWithText = async (messageText) => {
    const functionStartTime = performance.now();
    console.log('📤 sendMessageWithText start at:', functionStartTime);
    
    // Enhanced deduplication: Check multiple conditions
    if (messageBeingSentRef.current) {
      console.log('⏸️ Message already being sent, skipping:', messageText);
      return;
    }
    
    if (messageText === lastSentTranscriptRef.current) {
      console.log('⏸️ Duplicate transcript detected, skipping:', messageText);
      return;
    }
    
    if (!messageText || messageText.trim() === '' || messageStatus.isLoading) {
      console.log('⏸️ Invalid message or loading state, skipping');
      return;
    }
    
    // Mark as being sent and store transcript
    messageBeingSentRef.current = true;
    lastSentTranscriptRef.current = messageText;
    
    // Additional safety: Set timeout to reset deduplication flag
    setTimeout(() => {
      messageBeingSentRef.current = false;
    }, 2000); // Reset after 2 seconds if something goes wrong

    // Check if services are ready (more lenient for auto-send when online)
    if (!serviceStatus.isHealthy && !serviceStatus.isReady && !isOnline) {
      const warningMessage = {
        id: Date.now(),
        text: "⚠️ Services are starting up. Please wait a moment and try again.",
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, warningMessage]);
      return;
    }

    const currentMessage = messageText.trim();
    const messageId = Date.now();
    
    // Clear input text (in case it was set)
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
    
    // Reset deduplication flag after successful send
    messageBeingSentRef.current = false;
  };

  // Enhanced message sending with retry logic
  const sendMessage = async () => {
    console.log('📤 sendMessage called - inputText:', inputText.trim(), 'isLoading:', messageStatus.isLoading);
    if (inputText.trim() === '' || messageStatus.isLoading) {
      console.log('❌ sendMessage early return - empty text or loading');
      return;
    }

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
    
    // Reset deduplication flag after successful send
    messageBeingSentRef.current = false;
  };

  const sendMessageWithRetry = async (messageText, messageId) => {
    const retryFunctionStart = performance.now();
    console.log('🚀 sendMessageWithRetry function start at:', retryFunctionStart);
    
    const userMessage = {
      id: messageId,
      text: messageText,
      sender: 'user', 
      timestamp: new Date()
    };

    // Add user message immediately and force React to flush
    const messageAddTime = performance.now();
    console.log('💬 Adding user message to UI at:', messageAddTime);
    setMessages(prev => [...prev, userMessage]);
    
    // For hands-free mode, show user message instantly with immediate feedback
    if (handsFreeStateRef.current) {
      // Skip the thinking state entirely for faster perceived response
      console.log('⚡ Skipping thinking state for hands-free mode');
      
      // Show immediate processing feedback
      setHandsFreeStatus('processing');
      setIsWaitingForResponse(true);
      
      // Show immediate processing feedback without interrupting streaming UX
      setHandsFreeStatus('processing');
      setIsWaitingForResponse(true);
    } else {
      setIsThinking(true);
    }
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
      // For hands-free mode, skip delay for faster response
      const delay = handsFreeStateRef.current ? 0 : 200; // Much shorter delay, none for hands-free
      if (delay > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      setIsThinking(false);
      setIsWaitingForResponse(true);
      setIsStreaming(true);
      
      setStreamingMessage({ id: streamingMsgId });
      
      let accumulatedText = '';
      let messageCreated = false;
      
      const apiCallStart = performance.now();
      console.log('🌐 Starting API call at:', apiCallStart);
      
      const result = await ChatService.sendMessageStream(messageText, {
        onChunk: (chunk, visualCitations = []) => {
          if (!messageCreated) {
            const firstChunkTime = performance.now();
            console.log('📨 First chunk received at:', firstChunkTime);
            
            // Log visual citations if received in first chunk
            if (visualCitations && visualCitations.length > 0) {
              console.log('🖼️ Visual citations received in first chunk:', visualCitations);
            }
            
            // CRITICAL FIX: Clear inline loading state IMMEDIATELY when first chunk arrives

            setIsWaitingForResponse(false); // Clear waiting state - this hides the inline "Assistant is responding..." overlay
            
            // Update hands-free status to show proper streaming state in chip
            if (handsFreeStateRef.current) {
              setHandsFreeStatus('speaking'); // Show that assistant is now speaking/responding
            }
          }
          
          accumulatedText += chunk;
          
          // Create the message on first chunk (original behavior)
          if (!messageCreated) {
            const initialStreamingMessage = {
              id: streamingMsgId,
              text: accumulatedText,
              sender: 'assistant',
              timestamp: new Date(),
              isStreaming: true,
              visualCitations: visualCitations  // Include visual citations from first chunk
            };
            setMessages(prev => [...prev, initialStreamingMessage]);
            messageCreated = true;
            
            // Initialize streaming TTS for hands-free mode
            if (handsFreeStateRef.current && ttsAvailableRef.current) {
              streamingTTSRef.current = { isActive: true, spokenText: '', remainingText: accumulatedText };
              console.log('🔊 Streaming TTS initialized');
            }
          } else {
            // Update existing message
            updateStreamingMessage(streamingMsgId, accumulatedText);
          }
          
          // Handle streaming TTS if active
          if (streamingTTSRef.current.isActive) {
            handleStreamingTTS(accumulatedText);
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
        onComplete: (completionData) => {
          clearTimeout(streamingTimeoutRef.current);
          
          // Extract visual citations from completion data
          const visualCitations = completionData?.visual_citations || [];
          const metadata = completionData?.metadata;
          
          console.log('🔍 Stream completion with visual citations:', visualCitations?.length || 0);
          if (visualCitations.length > 0) {
            console.log('📊 Visual citations from stream:', visualCitations);
          }
          
          // If no message was created (empty response), create a placeholder
          if (!messageCreated) {
            const completedMessage = {
              id: streamingMsgId,
              text: "I received your message but couldn't generate a response. Please try again.",
              sender: 'assistant',
              timestamp: new Date(),
              isError: true,
              retryFunction: () => sendMessageWithRetry(messageText, Date.now()),
              visualCitations: visualCitations
            };
            setMessages(prev => [...prev, completedMessage]);
          } else {
            // Update the existing message, preserving existing visual citations if new ones aren't provided
            setMessages(prev => prev.map(msg => 
              msg.id === streamingMsgId 
                ? { 
                    ...msg, 
                    visualCitations: visualCitations?.length > 0 ? visualCitations : (msg.visualCitations || []), 
                    isStreaming: false 
                  }
                : msg
            ));
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

    
    // Reset deduplication flags on error
    messageBeingSentRef.current = false;
    messageSentRef.current = false;
    
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

  const completeStreaming = (streamingMsgId) => {
    const completionTime = performance.now();
    console.log('🎯 Stream completion at:', completionTime, 'for message:', streamingMsgId);
    
    // Reset all deduplication flags
    messageBeingSentRef.current = false;
    messageSentRef.current = false;
    
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

    // Handle final TTS completion for hands-free mode
    if (handsFreeStateRef.current && ttsAvailableRef.current) {
      // Prevent duplicate processing - check both message ID and completing state
      if (currentTTSMessageIdRef.current === streamingMsgId || streamingTTSRef.current.isCompleting) {
        console.log('🔊 TTS completion already processed for message:', streamingMsgId, 'isCompleting:', streamingTTSRef.current.isCompleting);
        return;
      }
      
      // Mark as completing FIRST to prevent race conditions
      streamingTTSRef.current.isCompleting = true;
      currentTTSMessageIdRef.current = streamingMsgId;
      
      console.log('🔊 Processing final TTS for message:', streamingMsgId, 'isActive:', streamingTTSRef.current.isActive);
      
      if (streamingTTSRef.current.isActive) {
        // Add a processed flag to prevent multiple executions
        let ttsProcessed = false;
        
        // Use setMessages to get the current state reliably
        setMessages(current => {
          // Prevent multiple executions within the same callback
          if (ttsProcessed) {
            console.log('🔊 TTS already processed in this callback, skipping');
            return current;
          }
          ttsProcessed = true;
          
          const completedMessage = current.find(msg => msg.id === streamingMsgId);
          console.log('🔊 Found completed message:', !!completedMessage, 'text length:', completedMessage?.text?.length);
          
          if (completedMessage && completedMessage.text) {
            const fullText = cleanTextForSpeech(completedMessage.text);
            const remainingText = fullText.substring(streamingTTSRef.current.spokenText.length).trim();
            
            console.log('🔊 Full text length:', fullText.length, 'Spoken length:', streamingTTSRef.current.spokenText.length, 'Remaining:', remainingText.length);
            
            if (remainingText) {
              console.log('🔊 Speaking final remaining text with ElevenLabs:', remainingText.substring(0, 50) + '...');
              
              // Use the main speakText function which handles ElevenLabs + fallback
              speakText(remainingText, streamingMsgId).then(() => {
                console.log('🔊 Final TTS chunk completed');
                setIsSpeaking(false);
                streamingTTSRef.current = { isActive: false, spokenText: '', remainingText: '', isCompleting: false };
                currentTTSMessageIdRef.current = null;
                
                if (handsFreeStateRef.current) {
                  console.log('🔊 Streaming TTS complete, restarting voice input');
                  setHandsFreeStatus('listening'); // Go directly to listening
                  startAutoVoiceInput();
                }
              }).catch((error) => {
                console.error('Final TTS error:', error);
                setIsSpeaking(false);
                streamingTTSRef.current = { isActive: false, spokenText: '', remainingText: '', isCompleting: false };
                currentTTSMessageIdRef.current = null;
                
                if (handsFreeStateRef.current) {
                  setTimeout(() => {
                    if (handsFreeStateRef.current) {
                      setHandsFreeStatus('listening');
                      startAutoVoiceInput();
                    }
                  }, 1000);
                }
              });
            } else {
              // No remaining text - streaming TTS already completed everything
              console.log('🔊 All text already spoken via streaming TTS');
              setIsSpeaking(false);
              streamingTTSRef.current = { isActive: false, spokenText: '', remainingText: '' };
              currentTTSMessageIdRef.current = null;
              
              if (handsFreeStateRef.current) {
                setHandsFreeStatus('listening'); // Go directly to listening
                startAutoVoiceInput();
              }
            }
          } else {
            console.log('🔊 No completed message found for ID:', streamingMsgId);
            streamingTTSRef.current.isCompleting = false;
            currentTTSMessageIdRef.current = null;
          }
          return current;
        });
      } else {
        // Fallback to regular TTS if streaming wasn't active
        console.log('🔊 Fallback to regular TTS (streaming not active)');
        setMessages(current => {
          const completedMessage = current.find(msg => msg.id === streamingMsgId);
          if (completedMessage && completedMessage.text) {
            speakText(completedMessage.text, streamingMsgId);
          } else {
            currentTTSMessageIdRef.current = null;
          }
          return current;
        });
      }
    }
  };

  const fallbackToRegularAPI = async (messageText, streamingMsgId, messageCreated = false) => {
    console.log('Falling back to regular API...');
    
    try {
      // Detect if this should use multimodal endpoint (always check for citations)
      const shouldUseMultiModal = (
        // Equipment-related keywords
        /(?:taylor|hobart|fryer|grill|oven|ice cream|machine|equipment|compressor|temperature|safety|diagram|manual|page|section)/i.test(messageText) ||
        // Current equipment context exists
        currentEquipment ||
        // Citation-triggering phrases
        /(?:show|see|check|refer to|diagram|table|chart|safety|warning)/i.test(messageText)
      );

      console.log(`Using ${shouldUseMultiModal ? 'multimodal' : 'regular'} API for: "${messageText}"`);

      let result;
      if (shouldUseMultiModal) {
        // Use multimodal API with citations
        result = await ChatService.sendMultiModalMessage(messageText, {
          currentEquipment: currentEquipment,
          enableCitations: true,
          maxRetries: 2,
          timeout: 15000
        });
      } else {
        // Use regular API
        result = await ChatService.sendMessage(messageText, {
          maxRetries: 2,
          timeout: 15000
        });
      }

      if (result.success) {
        // Extract response data (handle both regular and multimodal responses)
        const responseText = result.data.response;
        const visualCitations = result.data.visual_citations || [];
        const manualReferences = result.data.manual_references || [];
        const equipmentContext = result.data.equipment_context;
        
        // Enhanced debug logging for citations
        console.log('🔍 Response data:', {
          responseText: responseText?.length + ' chars',
          visualCitations: visualCitations?.length || 0,
          manualReferences: manualReferences?.length || 0,
          fullData: result.data
        });

        // Debug: Log visual citations in detail
        if (visualCitations && visualCitations.length > 0) {
          console.log('📊 Visual citations detailed:');
          visualCitations.forEach((citation, index) => {
            console.log(`   Visual Citation ${index + 1}:`, citation);
          });
        } else {
          console.log('⚠️ No visual citations in API response');
        }

        // Update current equipment context if provided
        if (equipmentContext && equipmentContext !== currentEquipment) {
          setCurrentEquipment(equipmentContext);
          console.log(`Updated equipment context: ${equipmentContext}`);
        }

        // Store citations for display
        if (visualCitations.length > 0 || manualReferences.length > 0) {
          console.log(`Found ${visualCitations.length} visual citations and ${manualReferences.length} manual references`);
        }

        if (messageCreated) {
          // Update existing message
          setMessages(prev => prev.map(msg => 
            msg.id === streamingMsgId 
              ? {
                  ...msg,
                  text: responseText,
                  isStreaming: false,
                  isThinking: false,
                  isFallback: true,
                  visualCitations: visualCitations,
                  manualReferences: manualReferences,
                  equipmentContext: equipmentContext
                }
              : msg
          ));
          console.log('🔄 Updated existing message with visual citations:', visualCitations?.length || 0);
        } else {
          // Create new message
          const fallbackMessage = {
            id: streamingMsgId,
            text: responseText,
            sender: 'assistant',
            timestamp: new Date(),
            isFallback: true,
            visualCitations: visualCitations,
            manualReferences: manualReferences,
            equipmentContext: equipmentContext
          };
          setMessages(prev => [...prev, fallbackMessage]);
          console.log('✨ Created new message with visual citations:', visualCitations?.length || 0);
          console.log('📋 Full message object:', fallbackMessage);
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
    
    // If user manually types while in hands-free mode, cancel any pending auto-send
    if (handsFreeMode && !isRecording) {
      // Clear any pending auto-voice timer since user is manually typing
      if (autoVoiceTimerRef.current) {
        clearTimeout(autoVoiceTimerRef.current);
        autoVoiceTimerRef.current = null;
      }
      
      // Cancel transcript-based auto-send since user is manually editing
      stopTranscriptTimer();
      
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
    if (!voiceAvailableRef.current || !speechRecognitionRef.current) {
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
      console.log('Starting voice recording... handsFreeMode:', handsFreeStateRef.current);
      
      // Enhanced check: Prevent overlapping voice sessions
      if (speechRecognitionRunningRef.current || isRecording) {
        console.log('🎤 Speech recognition already active, preventing overlap');
        return;
      }
      
      // Check if message is being processed to avoid conflicts
      if (messageBeingSentRef.current || messageStatus.isLoading) {
        console.log('🎤 Message being processed, delaying voice input');
        return;
      }
      
      try {
        // Clear any existing text and reset transcript-based detection state
        setInputText('');
        currentTranscriptRef.current = '';
        transcriptWordCountRef.current = 0;
        lastTranscriptUpdateRef.current = null;
        lastSentTranscriptRef.current = ''; // Clear last sent transcript
        messageSentRef.current = false; // Reset message sent flag
        stopTranscriptTimer();
        
        console.log('🚀 About to start speech recognition - handsFreeMode:', handsFreeStateRef.current);
        speechRecognitionRunningRef.current = true;
        speechRecognitionRef.current.start();
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
        speechRecognitionRunningRef.current = false;
        setIsRecording(false);
        
        if (error.name === 'InvalidStateError') {
          // Recognition is already running, stop it first and retry
          console.log('🔄 Stopping existing recognition and retrying...');
          speechRecognitionRef.current.stop();
          setTimeout(() => {
            if (!speechRecognitionRunningRef.current) {
              try {
                setInputText('');
                speechRecognitionRunningRef.current = true;
                speechRecognitionRef.current.start();
              } catch (retryError) {
                console.error('Retry failed:', retryError);
                speechRecognitionRunningRef.current = false;
              }
            }
          }, 250); // Longer delay for proper cleanup
        }
      }
    }
  };

  // Text-to-Speech handler
  // Streaming TTS handler - speaks text as it arrives in chunks
  const handleStreamingTTS = (fullText) => {
    if (!streamingTTSRef.current.isActive || !handsFreeStateRef.current) return;
    
    const cleanFullText = cleanTextForSpeech(fullText);
    const alreadySpoken = streamingTTSRef.current.spokenText;
    
    // Find new text that hasn't been spoken yet
    const newText = cleanFullText.substring(alreadySpoken.length);
    
    // Only speak if we have a complete sentence or significant chunk
    const sentenceEnders = /^.*?[.!?]\s+/;
    const completeSentences = newText.match(sentenceEnders);
    
    if (completeSentences) {
      const textToSpeak = completeSentences[0];
      console.log('🔊 Streaming TTS chunk:', textToSpeak.substring(0, 50) + '...');
      
      // Speak this chunk (async - don't block streaming)
      speakTextChunk(textToSpeak).catch(error => {
        console.error('Streaming TTS chunk error:', error);
      });
      
      // Update what we've spoken
      streamingTTSRef.current.spokenText = alreadySpoken + textToSpeak;
    }
    // Buffer threshold: start speaking after 100+ characters even without sentence end
    else if (newText.length > 100 && !window.speechSynthesis.speaking) {
      // Find a good breaking point (word boundary)
      const lastSpace = newText.lastIndexOf(' ', 100);
      if (lastSpace > 50) {
        const textToSpeak = newText.substring(0, lastSpace + 1);
        console.log('🔊 Streaming TTS buffer chunk:', textToSpeak.substring(0, 50) + '...');
        
        speakTextChunk(textToSpeak).catch(error => {
          console.error('Streaming TTS buffer chunk error:', error);
        });
        streamingTTSRef.current.spokenText = alreadySpoken + textToSpeak;
      }
    }
  };

  // Helper function to clean text for speech
  const cleanTextForSpeech = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
      .replace(/\*(.*?)\*/g, '$1')     // Remove italic markdown
      .replace(/`(.*?)`/g, '$1')       // Remove code markdown
      .replace(/#{1,6}\s/g, '')        // Remove headers
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to text
      .replace(/\n+/g, '. ')           // Convert line breaks to pauses
      .trim();
  };

  // Speak a chunk of text using queue system - ElevenLabs or Web Speech API fallback
  const speakTextChunk = async (text) => {
    if (!ttsAvailableRef.current || !text.trim()) return;
    
    if (!elevenlabsApiKey) {
      // Fallback to Web Speech API
      console.log('🔊 Using Web Speech API fallback for TTS chunk');
      try {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;
        window.speechSynthesis.speak(utterance);
      } catch (error) {
        console.error('🔊 Web Speech API failed:', error.message);
      }
      return;
    }

    try {
      await queueTTS(text, 'streaming-chunk');
    } catch (error) {
      console.error('🔊 TTS chunk failed:', error.message);
    }
  };

  // Main TTS function using queue system - ElevenLabs or Web Speech API fallback
  const speakText = async (text, messageId = null) => {
    if (!ttsAvailableRef.current || !text.trim()) {
      if (messageId) currentTTSMessageIdRef.current = null;
      return;
    }

    // Clean text for speech
    const cleanText = cleanTextForSpeech(text);
    if (!cleanText) return;

    if (!elevenlabsApiKey) {
      // Fallback to Web Speech API
      console.log('🔊 Using Web Speech API fallback for full message');
      try {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;
        utterance.onend = () => {
          console.log('🔊 Web Speech API TTS completed');
          if (messageId) currentTTSMessageIdRef.current = null;
        };
        window.speechSynthesis.speak(utterance);
      } catch (error) {
        console.error('🔊 Web Speech API failed:', error.message);
        if (messageId) currentTTSMessageIdRef.current = null;
      }
      return;
    }

    try {
      await queueTTS(cleanText, 'full-message');
      console.log('🎵 Full message TTS completed successfully');
    } catch (error) {
      console.error('🔊 Full message TTS failed:', error.message);
      if (messageId) currentTTSMessageIdRef.current = null;
    }
  };

  // Stop TTS if currently speaking - ElevenLabs and Web Speech API
  const stopSpeaking = () => {
    // Stop current ElevenLabs audio
    if (currentElevenLabsAudioRef.current) {
      currentElevenLabsAudioRef.current.pause();
      currentElevenLabsAudioRef.current = null;
    }
    
    // Stop Web Speech API
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    
    // Clear TTS queue, audio buffer, and reset API call counter
    ttsQueueRef.current = [];
    ttsPlayingRef.current = false;
    audioBufferRef.current.clear();
    apiCallsInProgressRef.current = 0;
    
    setIsSpeaking(false);
    currentTTSMessageIdRef.current = null;
  };

  // Hands-free mode functions
  const startAutoVoiceInput = () => {
    if (!handsFreeStateRef.current || !voiceAvailableRef.current) {
      return;
    }
    
    // Prevent multiple restarts - enhanced safety
    if (autoVoiceTimerRef.current || speechRecognitionRunningRef.current || isRecording || messageBeingSentRef.current) {
      console.log('🎤 Auto voice input already in progress or blocked, skipping restart');
      return;
    }
    
    // Clear any existing timer
    if (autoVoiceTimerRef.current) {
      clearTimeout(autoVoiceTimerRef.current);
    }
    
    // Go directly to listening - no need for "ready" state after initial setup
    console.log('Voice input restarted');
    setHandsFreeStatus('listening');
    
    // Brief delay to allow TTS to fully complete, then start voice recognition
    autoVoiceTimerRef.current = setTimeout(() => {
      if (handsFreeStateRef.current && !isRecording && !isSpeaking && !messageBeingSentRef.current) {
        autoVoiceTimerRef.current = null; // Clear timer reference
        handleVoiceInput(); // Start voice recognition
      } else {
        autoVoiceTimerRef.current = null; // Clear timer reference even if conditions not met
        console.log('🎤 Auto voice input conditions not met - isRecording:', isRecording, 'isSpeaking:', isSpeaking, 'messageBeingSent:', messageBeingSentRef.current);
      }
    }, 750); // Slightly longer delay for proper TTS cleanup
  };

  const exitHandsFreeMode = () => {
    console.log('🚨 exitHandsFreeMode called! Stack trace:');
    console.trace();
    setHandsFreeMode(false);
    setHandsFreeStatus('idle');
    
    // Clear timers
    if (autoVoiceTimerRef.current) {
      clearTimeout(autoVoiceTimerRef.current);
    }
    if (handsFreeTimeoutRef.current) {
      clearTimeout(handsFreeTimeoutRef.current);
    }
    
    // Clean up transcript-based silence detection
    stopTranscriptTimer();
    currentTranscriptRef.current = '';
    transcriptWordCountRef.current = 0;
    lastTranscriptUpdateRef.current = null;
    
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

  // Transcript-based silence detection functions
  const startTranscriptTimer = () => {
    if (!handsFreeStateRef.current || !silenceDetectionStateRef.current) {
      return;
    }
    
    // Check if we have minimum speech (2+ words)
    if (transcriptWordCountRef.current < 2) {
      return;
    }
    
    // Clear any existing timer
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    
    // Aggressive timing: only 1.5 seconds total silence detection
    // Wait 200ms buffer, then 1.3s countdown = 1.5s total
    silenceTimerRef.current = setTimeout(() => {
      if (!handsFreeStateRef.current || !silenceDetectionStateRef.current) {
        return;
      }
      
      // Start visual countdown from 1 second (1.5s total delay)

      setIsCountingDown(true);
      
      // Much faster countdown
      silenceTimerRef.current = setTimeout(() => {
        setIsCountingDown(false);

        setHandsFreeStatus('processing');
        
        const transcriptToSend = currentTranscriptRef.current.trim();
        if (transcriptToSend && transcriptWordCountRef.current >= 2) {
          console.log('Silence timer auto-send:', transcriptToSend);
          sendMessageWithText(transcriptToSend);
        }
      }, 1300); // 1.3 second countdown
    }, 200); // Reduced buffer to 200ms
  };

  const stopTranscriptTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (transcriptDebounceTimerRef.current) {
      clearTimeout(transcriptDebounceTimerRef.current);
      transcriptDebounceTimerRef.current = null;
    }
    setIsCountingDown(false);

    messageSentRef.current = false; // Reset send flag to allow future sends
    console.log('Transcript timer and debounce timer stopped');
  };

  const updateTranscriptTimestamp = (transcript, isFinal) => {
    const words = transcript.trim().split(' ').filter(word => word.length > 0);
    const wordCount = words.length;
    
    // Update refs
    lastTranscriptUpdateRef.current = Date.now();
    currentTranscriptRef.current = transcript;
    transcriptWordCountRef.current = wordCount;
    
    // Clear any existing timers
    stopTranscriptTimer();
    if (transcriptDebounceTimerRef.current) {
      clearTimeout(transcriptDebounceTimerRef.current);
    }
    
    // Only proceed if we have enough words
    if (!handsFreeStateRef.current || !silenceDetectionStateRef.current || wordCount < 2) {
      return;
    }
    
    // Use debounced approach: wait for transcript updates to stop
    const debounceDelay = isFinal ? 100 : 300; // Extremely aggressive timing for fast response
    
    transcriptDebounceTimerRef.current = setTimeout(() => {
      // Double-check we still meet conditions
      if (handsFreeStateRef.current && silenceDetectionStateRef.current && transcriptWordCountRef.current >= 2 && isRecording) {
        startTranscriptTimer();
      }
    }, debounceDelay);
  };

  // Get loading text based on current state
  const getLoadingText = () => {
    console.log('🔤 getLoadingText called with serviceStatus:', {
      isHealthy: serviceStatus.isHealthy,
      isReady: serviceStatus.isReady,
      isOnline: isOnline,
      messageStatus: messageStatus.isLoading
    });
    
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
      console.log('⚠️ Services not ready - showing startup message. serviceStatus:', serviceStatus);
      return "Services starting up...";
    }
    if (!isOnline) {
      return "You're offline - connect to send messages";
    }
    return "Ask me anything...";
  };

  const isInputDisabled = (messageStatus.isLoading || isStreaming || isThinking || isWaitingForResponse) || !serviceStatus.isReady || !isOnline;
  
  console.log('🔐 Input disabled check:', {
    messageStatus: messageStatus.isLoading,
    isStreaming,
    isThinking,
    isWaitingForResponse,
    isHealthy: serviceStatus.isHealthy,
    isOnline,
    finalDisabled: isInputDisabled
  });

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
              {voiceAvailable && ttsAvailable && !showUpload && !showProcessing && (
                <button 
                  className={`hands-free-toggle ${handsFreeMode ? 'active' : ''}`}
                  onClick={() => {
                    console.log('🎧 Hands-free toggle clicked. Current state:', handsFreeMode, '→ New state:', !handsFreeMode);
                    setHandsFreeMode(!handsFreeMode);
                  }}
                  title={handsFreeMode ? "Exit Hands-Free Mode" : "Enter Hands-Free Mode"}
                  aria-label={handsFreeMode ? "Exit hands-free conversation" : "Start hands-free conversation"}
                >
                  <Headphones className="toggle-icon" />
                </button>
              )}
              
              <button 
                className="upload-toggle-btn"
                onClick={() => {
                  setShowUpload(!showUpload);
                  setShowProcessing(false);
                }}
                title={showUpload ? "Hide Upload" : "Upload Manual"}
                aria-label={showUpload ? "Show chat" : "Show documents"}
              >
                {showUpload ? (
                  <MessageCircle className="toggle-icon" />
                ) : (
                  <BookOpen className="toggle-icon" />
                )}
              </button>
              
              {/* Processing Dashboard temporarily hidden - keeping for troubleshooting */}
              {/*
              <button 
                className={`processing-toggle-btn ${showProcessing ? 'active' : ''}`}
                onClick={() => {
                  setShowProcessing(!showProcessing);
                  setShowUpload(false);
                }}
                title={showProcessing ? "Hide Processing Dashboard" : "Show Processing Dashboard"}
                aria-label={showProcessing ? "Show chat" : "Show processing status"}
              >
                <Activity className="toggle-icon" />
                {showProcessing && <span className="active-indicator">Processing</span>}
              </button>
              */}
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
          ) : showProcessing ? (
            /* Processing Dashboard temporarily hidden - keeping for troubleshooting */
            <div className="processing-section">
              <ErrorBoundary>
                <ProcessingDashboard />
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
                      {/* Display Images First */}
                      {message.sender === 'assistant' && message.visualCitations && (
                        <ImageCitation visualCitations={message.visualCitations} />
                      )}
                      
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
              
              {/* Persistent bottom spacer - provides clearance for chip overlay */}
              <div className="bottom-spacer" />
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="input-container aui-composer">
          {/* Countdown UI removed - 2 second delay is too short to be useful */}
          
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

          {/* Hands-Free Status Chip - Positioned relative to input container wrapper */}
          {handsFreeMode && handsFreeStatus !== 'idle' && (
            <div className="hands-free-status-chip">
              <Headphones className="chip-icon" />
              <span className="chip-label">
                {handsFreeStatus === 'ready' && 'Starting up...'}
                {handsFreeStatus === 'listening' && 'Listening...'}
                {handsFreeStatus === 'processing' && 'Assistant responding...'}
                {handsFreeStatus === 'speaking' && 'Assistant responding...'}
              </span>
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