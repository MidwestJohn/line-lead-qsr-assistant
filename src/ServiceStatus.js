import React, { useState, useEffect } from 'react';
import './ServiceStatus.css';
import { API_BASE_URL } from './config';

const ServiceStatus = ({ onStatusChange }) => {
  const [status, setStatus] = useState({
    overall: 'checking',
    services: {},
    lastCheck: null,
    error: null,
    retryCount: 0
  });

  const checkHealth = async (retryAttempt = 0) => {
    try {
      setStatus(prev => ({ 
        ...prev, 
        overall: 'checking',
        retryCount: retryAttempt 
      }));

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

      const response = await fetch(`${API_BASE_URL}/health`, {
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache'
        }
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      const healthData = await response.json();
      
      setStatus({
        overall: healthData.status,
        services: healthData.services || {},
        documentCount: healthData.document_count || 0,
        searchReady: healthData.search_ready || false,
        lastCheck: new Date(),
        error: null,
        retryCount: 0
      });

      // Notify parent component of status change
      if (onStatusChange) {
        onStatusChange({
          isHealthy: healthData.status === 'healthy',
          isReady: healthData.search_ready,
          services: healthData.services
        });
      }

    } catch (error) {
      console.error('Health check failed:', error);
      
      const isNetworkError = error.name === 'AbortError' || 
                           error.name === 'TypeError' ||
                           error.message.includes('fetch');
      
      const errorMessage = isNetworkError ? 
        'Network connection failed' : 
        error.message;

      setStatus(prev => ({
        ...prev,
        overall: 'error',
        error: errorMessage,
        lastCheck: new Date(),
        retryCount: retryAttempt
      }));

      // Retry logic with exponential backoff
      if (retryAttempt < 3) {
        const delay = Math.pow(2, retryAttempt) * 1000; // 1s, 2s, 4s
        setTimeout(() => {
          checkHealth(retryAttempt + 1);
        }, delay);
      }

      // Notify parent of error state
      if (onStatusChange) {
        onStatusChange({
          isHealthy: false,
          isReady: false,
          error: errorMessage
        });
      }
    }
  };

  useEffect(() => {
    // Initial health check
    checkHealth();

    // Set up periodic health checks every 30 seconds
    const interval = setInterval(() => {
      checkHealth();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (serviceStatus) => {
    switch (serviceStatus) {
      case 'ready': return '#10b981'; // green
      case 'initializing': return '#f59e0b'; // yellow
      case 'error': return '#ef4444'; // red
      case 'checking': return '#6b7280'; // gray
      default: return '#6b7280';
    }
  };

  // Green dot when all services are healthy
  const getOverallStatusColor = () => {
    if (status.overall === 'healthy') return '#10b981'; // green
    if (status.overall === 'degraded') return '#f59e0b'; // yellow  
    if (status.overall === 'error') return '#ef4444'; // red
    return '#6b7280'; // gray for checking/unknown
  };

  const getOverallStatusText = () => {
    switch (status.overall) {
      case 'healthy': return 'Services Ready';
      case 'degraded': return 'Limited Service';
      case 'error': return 'Service Error';
      case 'checking': return 'Checking Services...';
      default: return 'Unknown Status';
    }
  };

  const handleRetry = () => {
    checkHealth();
  };

  return (
    <div className="service-status">
      <div className="status-indicator">
        <div 
          className={`status-dot ${status.overall}`}
          style={{ backgroundColor: getOverallStatusColor() }}
        />
        <span className="status-text">{getOverallStatusText()}</span>
        
        {status.retryCount > 0 && (
          <span className="retry-text">
            (Retry {status.retryCount}/3)
          </span>
        )}

        {/* Inline timestamp */}
        {status.lastCheck && (
          <span className="last-check-inline">
            Last check: {status.lastCheck.toLocaleTimeString()}
          </span>
        )}
      </div>

      {status.error && (
        <div className="error-message">
          <span>{status.error}</span>
          <button onClick={handleRetry} className="retry-button">
            Try Again
          </button>
        </div>
      )}

      {status.overall === 'healthy' && status.documentCount > 0 && (
        <div className="ready-info">
          {status.documentCount} documents ready • Search enabled
        </div>
      )}

      {/* Detailed service status (collapsed by default, expandable) */}
      {Object.keys(status.services).length > 0 && (
        <details className="service-details">
          <summary>Service Details</summary>
          <div className="services-list">
            {Object.entries(status.services).map(([service, serviceStatus]) => (
              <div key={service} className="service-item">
                <div 
                  className="service-dot"
                  style={{ backgroundColor: getStatusColor(serviceStatus) }}
                />
                <span className="service-name">{service.replace('_', ' ')}</span>
                <span className="service-status">{serviceStatus}</span>
              </div>
            ))}
          </div>
        </details>
      )}


    </div>
  );
};

export default ServiceStatus;