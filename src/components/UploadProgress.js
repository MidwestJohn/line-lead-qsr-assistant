import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle2, AlertCircle, Clock, FileText, Search, Network, Database, Zap } from 'lucide-react';
import './UploadProgress.css';

/**
 * QSR Upload Progress Tracker
 * ===========================
 * 
 * Real-time progress tracking for PDF → LightRAG → Neo4j pipeline.
 * Provides professional, transparent upload experience with detailed feedback.
 * 
 * Features:
 * - WebSocket-based real-time updates
 * - 6-stage progress visualization
 * - ETA calculations and success metrics
 * - Error handling with retry options
 * - Professional QSR-focused messaging
 */

const STAGE_CONFIG = {
  upload_received: {
    icon: FileText,
    label: 'File Upload',
    description: 'Uploading manual...',
    color: '#3b82f6'
  },
  text_extraction: {
    icon: Search,
    label: 'Text Extraction',
    description: 'Extracting text and images...',
    color: '#8b5cf6'
  },
  entity_extraction: {
    icon: Zap,
    label: 'Entity Processing',
    description: 'Identifying equipment and procedures...',
    color: '#f59e0b'
  },
  relationship_mapping: {
    icon: Network,
    label: 'Relationship Mapping',
    description: 'Building knowledge connections...',
    color: '#06b6d4'
  },
  graph_population: {
    icon: Database,
    label: 'Graph Population',
    description: 'Saving to knowledge base...',
    color: '#10b981'
  },
  verification: {
    icon: CheckCircle2,
    label: 'Complete',
    description: 'Ready! Processing complete.',
    color: '#22c55e'
  },
  error: {
    icon: AlertCircle,
    label: 'Error',
    description: 'Processing failed',
    color: '#ef4444'
  }
};

const UploadProgress = ({ processId, onComplete, onError }) => {
  const [progress, setProgress] = useState({
    stage: 'upload_received',
    progress_percent: 5,
    message: 'Initializing upload...',
    entities_found: 0,
    relationships_found: 0,
    pages_processed: 0,
    total_pages: 0,
    elapsed_seconds: 0,
    eta_message: null,
    error_message: null,
    success_summary: null
  });
  
  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [useHttpFallback, setUseHttpFallback] = useState(false);
  const [httpPollingInterval, setHttpPollingInterval] = useState(null);
  const wsRef = useRef(null);

  // HTTP fallback mechanism
  const startHttpFallback = async () => {
    if (!processId) return;
    
    console.log('🔄 Starting HTTP polling fallback...');
    setConnectionError('Using HTTP fallback - progress will still update');
    
    const pollProgress = async () => {
      if (!processId) return;
      
      try {
        const response = await fetch(`/ws/progress/${processId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.progress) {
            console.log('📊 HTTP fallback progress:', data.progress);
            
            // Update progress state
            setProgress(prevProgress => ({
              ...prevProgress,
              stage: data.progress.stage || prevProgress.stage,
              progress_percent: data.progress.progress_percent || prevProgress.progress_percent,
              message: data.progress.message || prevProgress.message,
              entities_found: data.progress.entities_found || prevProgress.entities_found,
              relationships_found: data.progress.relationships_found || prevProgress.relationships_found
            }));

            // Check if complete
            if (data.progress.stage === 'verification' && onComplete) {
              onComplete({
                entities: data.progress.entities_found || 0,
                relationships: data.progress.relationships_found || 0
              });
              return; // Stop polling
            }
          }
        }
      } catch (error) {
        console.warn('HTTP fallback request failed:', error);
      }
      
      // Continue polling if not complete
      setTimeout(pollProgress, 3000); // Poll every 3 seconds
    };
    
    // Start polling
    pollProgress();
  };

  useEffect(() => {
    if (!processId) return;

    // Prevent duplicate connections in React Strict Mode
    let isActiveConnection = true;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    // WebSocket connection for real-time progress
    const connectWebSocket = () => {
      try {
        // Check if we already have an active connection
        if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
          console.log('🔄 WebSocket already active, skipping duplicate connection...');
          return;
        }
        
        // Clean up any existing connection
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
        
        const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
        console.log(`🔌 Attempting WebSocket connection to: ${wsUrl}/ws/progress/${processId}`);
        const ws = new WebSocket(`${wsUrl}/ws/progress/${processId}`);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isActiveConnection) {
            console.log('🚫 WebSocket opened but connection is no longer active, closing...');
            ws.close();
            return;
          }
          console.log(`📡 Connected to progress WebSocket for ${processId}`);
          setConnected(true);
          setConnectionError(null);
          reconnectAttempts = 0; // Reset reconnect counter on successful connection
          
          // Send initial ping to verify connection
          try {
            ws.send('ping');
          } catch (error) {
            console.warn('Failed to send initial ping:', error);
          }
        };

        ws.onmessage = (event) => {
          try {
            // Handle text messages (pings)
            if (typeof event.data === 'string' && event.data === 'pong') {
              console.log('🏓 Received pong from server');
              return;
            }
            
            const progressData = JSON.parse(event.data);
            console.log('📊 Progress update:', progressData);
            
            // Handle different message types
            if (progressData.type === 'keepalive') {
              console.log('💓 Received keepalive from server');
              return;
            }
            
            if (progressData.type === 'current_status' || progressData.type === 'status_response') {
              console.log('📊 Received current status from server');
              // Update progress with current status
              setProgress(prevProgress => ({
                ...prevProgress,
                ...progressData.status || progressData,
                entities_found: progressData.entities_found || progressData.entities_extracted || 0,
                relationships_found: progressData.relationships_found || progressData.relationships_extracted || 0,
              }));
              return;
            }
            
            // Handle regular progress updates
            setProgress(prevProgress => ({
              ...prevProgress,
              ...progressData,
              // Ensure we have default values
              entities_found: progressData.entities_found || progressData.entities_extracted || 0,
              relationships_found: progressData.relationships_found || progressData.relationships_extracted || 0,
              pages_processed: progressData.pages_processed || 0,
              total_pages: progressData.total_pages || 0
            }));

            // Handle completion
            if (progressData.stage === 'verification' && onComplete) {
              setTimeout(() => {
                onComplete({
                  entities: progressData.entities_found || 0,
                  relationships: progressData.relationships_found || 0,
                  success_summary: progressData.success_summary
                });
              }, 2000); // Give user time to see completion message
            }

            // Handle errors
            if (progressData.stage === 'error' && onError) {
              onError({
                message: progressData.error_message || 'Processing failed',
                stage: progressData.error_stage,
                retry_available: progressData.retry_available
              });
            }

          } catch (error) {
            console.error('Failed to parse progress update:', error);
          }
        };

        ws.onclose = (event) => {
          console.log(`📡 Progress WebSocket disconnected (Code: ${event.code}, Reason: ${event.reason})`);
          setConnected(false);
          
          // Only attempt reconnect if this is still the active connection and we haven't exceeded max attempts
          if (isActiveConnection && 
              progress.stage !== 'verification' && 
              progress.stage !== 'error' && 
              reconnectAttempts < maxReconnectAttempts &&
              event.code !== 1000) { // 1000 = normal closure
            
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000); // Exponential backoff, max 10s
            console.log(`🔄 Attempting WebSocket reconnection (${reconnectAttempts}/${maxReconnectAttempts}) in ${delay}ms...`);
            
            setTimeout(() => {
              if (isActiveConnection) {
                connectWebSocket();
              }
            }, delay);
          } else if (reconnectAttempts >= maxReconnectAttempts) {
            console.log('❌ Max reconnection attempts reached, giving up');
            setConnectionError('Connection lost after multiple attempts');
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          console.error('WebSocket state:', ws.readyState);
          console.error('Process ID:', processId);
          setConnectionError('Connection failed, switching to HTTP fallback');
          setConnected(false);
          setUseHttpFallback(true);
          // Start HTTP fallback after 2 seconds
          setTimeout(() => {
            startHttpFallback();
          }, 2000);
        };

      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        console.error('Process ID:', processId);
        setConnectionError('Failed to connect');
      }
    };

    // Small delay to avoid React Strict Mode double-mounting issues
    const connectionTimer = setTimeout(() => {
      if (isActiveConnection) {
        connectWebSocket();
      }
    }, 100);

    // Cleanup on unmount
    return () => {
      isActiveConnection = false;
      clearTimeout(connectionTimer);
      
      if (wsRef.current) {
        console.log('🧹 Cleaning up WebSocket connection');
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [processId, onComplete, onError]);

  const renderStageIndicator = (stageKey, index) => {
    const stage = STAGE_CONFIG[stageKey];
    if (!stage) return null;

    const isActive = progress.stage === stageKey;
    const isCompleted = getStageOrder(progress.stage) > getStageOrder(stageKey);
    const isError = progress.stage === 'error';
    
    const IconComponent = stage.icon;
    
    return (
      <div 
        key={stageKey}
        className={`stage-indicator ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${isError ? 'error' : ''}`}
      >
        <div className="stage-icon" style={{ color: isCompleted || isActive ? stage.color : '#6b7280' }}>
          <IconComponent size={20} />
        </div>
        <div className="stage-info">
          <div className="stage-label">{stage.label}</div>
          <div className="stage-description">
            {isActive ? progress.message : stage.description}
          </div>
        </div>
        {index < Object.keys(STAGE_CONFIG).length - 2 && (
          <div className={`stage-connector ${isCompleted ? 'completed' : ''}`} />
        )}
      </div>
    );
  };

  const getStageOrder = (stage) => {
    const stages = ['upload_received', 'text_extraction', 'entity_extraction', 'relationship_mapping', 'graph_population', 'verification'];
    return stages.indexOf(stage);
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    }
  };

  const renderProgressBar = () => {
    const clampedProgress = Math.min(Math.max(progress.progress_percent, 0), 100);
    
    return (
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ 
              width: `${clampedProgress}%`,
              backgroundColor: progress.stage === 'error' ? '#ef4444' : '#22c55e'
            }}
          />
        </div>
        <div className="progress-text">
          {clampedProgress.toFixed(1)}%
        </div>
      </div>
    );
  };

  const renderMetrics = () => {
    if (progress.stage === 'upload_received' || progress.stage === 'text_extraction') {
      return (
        <div className="progress-metrics">
          {progress.total_pages > 0 && (
            <div className="metric">
              <span className="metric-label">Pages:</span>
              <span className="metric-value">{progress.total_pages}</span>
            </div>
          )}
          {progress.elapsed_seconds > 0 && (
            <div className="metric">
              <span className="metric-label">Time:</span>
              <span className="metric-value">{formatDuration(progress.elapsed_seconds)}</span>
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="progress-metrics">
        <div className="metric">
          <span className="metric-label">Entities:</span>
          <span className="metric-value">{progress.entities_found}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Relationships:</span>
          <span className="metric-value">{progress.relationships_found}</span>
        </div>
        {progress.elapsed_seconds > 0 && (
          <div className="metric">
            <span className="metric-label">Time:</span>
            <span className="metric-value">{formatDuration(progress.elapsed_seconds)}</span>
          </div>
        )}
      </div>
    );
  };

  const renderSuccessSummary = () => {
    if (progress.stage !== 'verification' || !progress.success_summary) return null;

    return (
      <div className="success-summary">
        <div className="success-title">
          <CheckCircle2 className="success-icon" />
          Knowledge Graph Updated!
        </div>
        <div className="success-details">
          <div className="success-metric">
            <span>{progress.success_summary.total_entities}</span>
            <span>Equipment & Procedures</span>
          </div>
          <div className="success-metric">
            <span>{progress.success_summary.total_relationships}</span>
            <span>Knowledge Connections</span>
          </div>
          <div className="success-metric">
            <span>{formatDuration(progress.success_summary.processing_time_seconds || progress.elapsed_seconds)}</span>
            <span>Processing Time</span>
          </div>
        </div>
      </div>
    );
  };

  const renderErrorDetails = () => {
    if (progress.stage !== 'error') return null;

    return (
      <div className="error-details">
        <div className="error-title">
          <AlertCircle className="error-icon" />
          Processing Failed
        </div>
        <div className="error-message">
          {progress.error_message || 'An unexpected error occurred during processing.'}
        </div>
        {progress.retry_available && (
          <div className="error-actions">
            <button className="retry-button" onClick={() => window.location.reload()}>
              Try Again
            </button>
          </div>
        )}
      </div>
    );
  };

  if (!processId) {
    return null;
  }

  return (
    <div className="upload-progress">
      <div className="progress-header">
        <h3>Processing QSR Manual</h3>
        {!connected && connectionError && (
          <div className={`connection-status ${useHttpFallback ? 'fallback' : 'error'}`}>
            {useHttpFallback ? 'HTTP Fallback Active' : 'Connection Error'}: {connectionError}
          </div>
        )}
        {connected && (
          <div className="connection-status connected">
            <div className="connection-indicator" />
            Live Updates
          </div>
        )}
      </div>

      {renderProgressBar()}

      <div className="progress-stages">
        {Object.keys(STAGE_CONFIG)
          .filter(key => key !== 'error') // Don't show error in normal flow
          .map((stageKey, index) => renderStageIndicator(stageKey, index))
        }
      </div>

      {renderMetrics()}

      {progress.eta_message && progress.stage !== 'verification' && progress.stage !== 'error' && (
        <div className="eta-display">
          <Clock size={16} />
          {progress.eta_message}
        </div>
      )}

      {renderSuccessSummary()}
      {renderErrorDetails()}
    </div>
  );
};

export default UploadProgress;