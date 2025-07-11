import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Upload, 
  FileText, 
  Search, 
  Network, 
  Database, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  Wifi,
  WifiOff,
  RefreshCw,
  Zap
} from 'lucide-react';
import './UploadProgress.css';

/**
 * Robust Upload Progress Component
 * ================================
 * 
 * Enhanced version with comprehensive error handling, graceful degradation,
 * and fallback mechanisms when WebSocket fails.
 * 
 * Key Features:
 * - WebSocket connection with automatic retry and fallback
 * - HTTP polling fallback when WebSocket fails
 * - Connection state management and user feedback
 * - Error recovery and retry mechanisms
 * - Memory leak prevention
 * - React Strict Mode compatibility
 */

const UploadProgressRobust = ({ 
  processId, 
  filename, 
  onComplete, 
  onError,
  autoRetry = true,
  maxRetries = 3,
  retryDelay = 2000,
  httpFallbackInterval = 3000
}) => {
  // Progress state
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('initializing');
  const [message, setMessage] = useState('Preparing upload...');
  const [entitiesFound, setEntitiesFound] = useState(0);
  const [relationshipsFound, setRelationshipsFound] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Connection state
  const [connectionMode, setConnectionMode] = useState('websocket'); // 'websocket' | 'http_fallback'
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // 'connected' | 'connecting' | 'disconnected' | 'error'
  const [retryCount, setRetryCount] = useState(0);
  
  // Refs for cleanup and state management
  const wsRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  const httpPollingRef = useRef(null);
  const isActiveRef = useRef(true);
  const lastProgressRef = useRef({ stage: '', progress: 0 });
  
  // Stage configuration (matching existing UploadProgress styling)
  const stageConfig = {
    initializing: { icon: Upload, label: 'Initializing...', color: '#6b7280' },
    upload_received: { icon: FileText, label: 'File Upload', color: '#3b82f6' },
    text_extraction: { icon: Search, label: 'Text Extraction', color: '#8b5cf6' },
    entity_extraction: { icon: Zap, label: 'Entity Processing', color: '#f59e0b' },
    relationship_mapping: { icon: Network, label: 'Relationship Mapping', color: '#06b6d4' },
    graph_population: { icon: Database, label: 'Graph Population', color: '#10b981' },
    verification: { icon: CheckCircle2, label: 'Complete!', color: '#22c55e' },
    error: { icon: XCircle, label: 'Error', color: '#ef4444' }
  };
  
  const currentStageConfig = stageConfig[stage] || stageConfig.initializing;
  const StageIcon = currentStageConfig.icon;
  
  // WebSocket connection with robust error handling
  const connectWebSocket = useCallback(() => {
    if (!isActiveRef.current || !processId) return;
    
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setConnectionStatus('connecting');
    
    try {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
      const ws = new WebSocket(`${wsUrl}/ws/progress/${processId}`);
      wsRef.current = ws;
      
      // Connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.warn('🕐 WebSocket connection timeout, falling back to HTTP');
          ws.close();
          fallbackToHttp();
        }
      }, 10000); // 10 second timeout
      
      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        if (!isActiveRef.current) {
          ws.close();
          return;
        }
        
        console.log(`✅ WebSocket connected for ${processId}`);
        setConnectionStatus('connected');
        setConnectionMode('websocket');
        setRetryCount(0);
        
        // Send initial ping
        try {
          ws.send('ping');
        } catch (error) {
          console.warn('Failed to send initial ping:', error);
        }
      };
      
      ws.onmessage = (event) => {
        if (!isActiveRef.current) return;
        
        try {
          // Handle text messages (pongs)
          if (typeof event.data === 'string') {
            if (event.data === 'pong') {
              console.log('🏓 Received pong from server');
              return;
            }
          }
          
          const data = JSON.parse(event.data);
          console.log('📊 Progress update:', data);
          
          // Handle different message types
          if (data.type === 'keepalive') {
            console.log('💓 Received keepalive');
            return;
          }
          
          if (data.type === 'cached_progress' || data.type === 'current_status') {
            console.log('📤 Received cached/current progress');
          }
          
          // Update progress state
          updateProgressFromData(data);
          
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error, event.data);
        }
      };
      
      ws.onerror = (error) => {
        clearTimeout(connectionTimeout);
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        
        if (autoRetry && retryCount < maxRetries) {
          console.log(`🔄 Retrying WebSocket connection (${retryCount + 1}/${maxRetries})`);
          scheduleRetry();
        } else {
          console.log('🔄 Max retries reached, falling back to HTTP polling');
          fallbackToHttp();
        }
      };
      
      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        console.log(`🔌 WebSocket closed (Code: ${event.code})`);
        setConnectionStatus('disconnected');
        
        if (!isActiveRef.current) return;
        
        if (event.code !== 1000 && autoRetry && retryCount < maxRetries) { // Not normal closure
          console.log(`🔄 Unexpected close, retrying (${retryCount + 1}/${maxRetries})`);
          scheduleRetry();
        } else if (event.code !== 1000) {
          console.log('🔄 Connection lost, falling back to HTTP polling');
          fallbackToHttp();
        }
      };
      
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnectionStatus('error');
      fallbackToHttp();
    }
  }, [processId, autoRetry, retryCount, maxRetries]);
  
  // Schedule retry with exponential backoff
  const scheduleRetry = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    
    const delay = retryDelay * Math.pow(2, retryCount); // Exponential backoff
    console.log(`⏳ Scheduling retry in ${delay}ms`);
    
    retryTimeoutRef.current = setTimeout(() => {
      setRetryCount(prev => prev + 1);
      connectWebSocket();
    }, delay);
  }, [retryCount, retryDelay, connectWebSocket]);
  
  // HTTP polling fallback
  const fallbackToHttp = useCallback(() => {
    if (!isActiveRef.current || !processId) return;
    
    console.log('🔄 Switching to HTTP polling fallback');
    setConnectionMode('http_fallback');
    setConnectionStatus('connected'); // HTTP polling is "connected"
    
    // Clean up WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Start HTTP polling
    const pollProgress = async () => {
      if (!isActiveRef.current) return;
      
      try {
        const response = await fetch(`/ws/progress/${processId}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('📊 HTTP progress update:', data);
          
          if (data.success && data.progress) {
            updateProgressFromData(data.progress);
          }
        } else {
          console.warn('HTTP progress request failed:', response.status);
        }
        
      } catch (error) {
        console.error('HTTP polling error:', error);
      }
      
      // Schedule next poll
      if (isActiveRef.current && !isComplete && !hasError) {
        httpPollingRef.current = setTimeout(pollProgress, httpFallbackInterval);
      }
    };
    
    // Start polling immediately
    pollProgress();
  }, [processId, httpFallbackInterval, isComplete, hasError]);
  
  // Update progress from data
  const updateProgressFromData = useCallback((data) => {
    // Prevent duplicate updates
    if (data.stage === lastProgressRef.current.stage && 
        data.progress_percent === lastProgressRef.current.progress) {
      return;
    }
    
    lastProgressRef.current = { stage: data.stage, progress: data.progress_percent };
    
    setProgress(data.progress_percent || 0);
    setStage(data.stage || 'initializing');
    setMessage(data.message || 'Processing...');
    setEntitiesFound(data.entities_found || 0);
    setRelationshipsFound(data.relationships_found || 0);
    
    // Handle completion
    if (data.stage === 'verification' && data.progress_percent >= 100) {
      setIsComplete(true);
      if (onComplete) {
        onComplete({
          entities: data.entities_found || 0,
          relationships: data.relationships_found || 0,
          success_summary: data.success_summary
        });
      }
    }
    
    // Handle errors
    if (data.stage === 'error' || data.error_message) {
      setHasError(true);
      setErrorMessage(data.error_message || 'Processing failed');
      if (onError) {
        onError(data.error_message || 'Processing failed');
      }
    }
  }, [onComplete, onError]);
  
  // Manual retry function
  const manualRetry = useCallback(() => {
    setRetryCount(0);
    setHasError(false);
    setErrorMessage('');
    setConnectionStatus('disconnected');
    
    if (connectionMode === 'websocket') {
      connectWebSocket();
    } else {
      fallbackToHttp();
    }
  }, [connectionMode, connectWebSocket, fallbackToHttp]);
  
  // Initialize connection
  useEffect(() => {
    if (!processId) return;
    
    isActiveRef.current = true;
    connectWebSocket();
    
    return () => {
      isActiveRef.current = false;
      
      // Clean up WebSocket
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      // Clear timeouts
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      
      if (httpPollingRef.current) {
        clearTimeout(httpPollingRef.current);
      }
    };
  }, [processId, connectWebSocket]);
  
  // Connection status indicator
  const ConnectionIndicator = () => {
    const getIndicatorConfig = () => {
      switch (connectionStatus) {
        case 'connected':
          return {
            icon: connectionMode === 'websocket' ? Wifi : RefreshCw,
            color: 'text-green-500',
            label: connectionMode === 'websocket' ? 'WebSocket Connected' : 'HTTP Polling Active'
          };
        case 'connecting':
          return {
            icon: RefreshCw,
            color: 'text-yellow-500',
            label: 'Connecting...'
          };
        case 'error':
          return {
            icon: WifiOff,
            color: 'text-red-500',
            label: 'Connection Error'
          };
        default:
          return {
            icon: WifiOff,
            color: 'text-gray-500',
            label: 'Disconnected'
          };
      }
    };
    
    const config = getIndicatorConfig();
    const IndicatorIcon = config.icon;
    
    return (
      <div className="flex items-center gap-2 text-sm">
        <IndicatorIcon 
          className={`h-4 w-4 ${config.color} ${connectionStatus === 'connecting' ? 'animate-spin' : ''}`} 
        />
        <span className={config.color}>{config.label}</span>
      </div>
    );
  };
  
  if (!processId) {
    return null;
  }
  
  return (
    <div className="upload-progress-container">
      <div className="upload-progress-card">
        {/* Header */}
        <div className="progress-header">
          <h3 className="progress-title">Processing {filename}</h3>
          <ConnectionIndicator />
        </div>
        
        {/* Progress bar */}
        <div className="progress-section">
          <div className="progress-bar-container">
            <div 
              className="progress-bar" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="progress-stats">
            <span>{progress.toFixed(0)}%</span>
            <span>{entitiesFound} entities, {relationshipsFound} relationships</span>
          </div>
        </div>
        
        {/* Current stage */}
        <div className="stage-display">
          <StageIcon 
            className="stage-icon" 
            style={{ color: currentStageConfig.color }}
          />
          <div className="stage-info">
            <div className="stage-label">{currentStageConfig.label}</div>
            <div className="stage-message">{message}</div>
          </div>
        </div>
        
        {/* Error state */}
        {hasError && (
          <div className="alert alert-error">
            <AlertTriangle className="alert-icon" />
            <div className="alert-content">
              <span>{errorMessage}</span>
              <button 
                className="retry-button"
                onClick={manualRetry}
              >
                <RefreshCw className="retry-icon" />
                Retry
              </button>
            </div>
          </div>
        )}
        
        {/* Connection issues warning */}
        {connectionStatus === 'error' && !hasError && (
          <div className="alert alert-warning">
            <WifiOff className="alert-icon" />
            <div className="alert-content">
              <span>
                Connection issues detected. 
                {connectionMode === 'http_fallback' ? ' Using HTTP polling fallback.' : ' Retrying...'}
              </span>
              <button 
                className="retry-button"
                onClick={manualRetry}
              >
                <RefreshCw className="retry-icon" />
                Reconnect
              </button>
            </div>
          </div>
        )}
        
        {/* Success state */}
        {isComplete && !hasError && (
          <div className="alert alert-success">
            <CheckCircle2 className="alert-icon" />
            <div className="alert-content">
              Processing completed successfully! Found {entitiesFound} entities and {relationshipsFound} relationships.
            </div>
          </div>
        )}
        
        {/* Debug info (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <details className="debug-info">
            <summary>Debug Info</summary>
            <div className="debug-content">
              <div>Process ID: {processId}</div>
              <div>Connection Mode: {connectionMode}</div>
              <div>Connection Status: {connectionStatus}</div>
              <div>Retry Count: {retryCount}/{maxRetries}</div>
              <div>Stage: {stage}</div>
            </div>
          </details>
        )}
      </div>
    </div>
  );
};

export default UploadProgressRobust;