import React, { useState, useEffect } from 'react';
import { connectionManager } from '../services/ConnectionManager';
import './ConnectionStatus.css';

/**
 * 📡 Connection Status Component
 * 
 * Displays connection status and provides user controls for connection management
 */
const ConnectionStatus = ({ compact = false }) => {
    const [status, setStatus] = useState(connectionManager.getStatus());
    const [showDetails, setShowDetails] = useState(false);
    const [retryInfo, setRetryInfo] = useState(null);

    useEffect(() => {
        const unsubscribe = connectionManager.addListener((event, data) => {
            setStatus(connectionManager.getStatus());
            
            if (event === 'retrying') {
                setRetryInfo(data);
                // Clear retry info after delay
                setTimeout(() => setRetryInfo(null), data.delay + 1000);
            }
        });

        return unsubscribe;
    }, []);

    const getStatusIcon = () => {
        const { connectionState, networkQuality } = status;
        
        if (connectionState === 'connected') {
            return networkQuality === 'excellent' ? '🟢' : 
                   networkQuality === 'good' ? '🟡' : 
                   networkQuality === 'fair' ? '🟠' : '🔴';
        } else if (connectionState === 'connecting' || connectionState === 'reconnecting') {
            return '🔄';
        } else {
            return '⚫';
        }
    };

    const getStatusText = () => {
        const { connectionState, networkQuality } = status;
        
        if (connectionState === 'connected') {
            return `Connected (${networkQuality})`;
        } else if (connectionState === 'connecting') {
            return 'Connecting...';
        } else if (connectionState === 'reconnecting') {
            return 'Reconnecting...';
        } else {
            return 'Disconnected';
        }
    };

    const getStatusColor = () => {
        const { connectionState, networkQuality } = status;
        
        if (connectionState === 'connected') {
            return networkQuality === 'excellent' || networkQuality === 'good' ? 'success' : 'warning';
        } else if (connectionState === 'connecting' || connectionState === 'reconnecting') {
            return 'connecting';
        } else {
            return 'error';
        }
    };

    const handleRetryClick = () => {
        connectionManager.forceReconnect();
    };

    const handleToggleDetails = () => {
        setShowDetails(!showDetails);
    };

    if (compact) {
        return (
            <div className={`connection-status-compact ${getStatusColor()}`}>
                <span className="status-icon">{getStatusIcon()}</span>
                <span className="status-text">{getStatusText()}</span>
            </div>
        );
    }

    return (
        <div className={`connection-status ${getStatusColor()}`}>
            <div className="status-header" onClick={handleToggleDetails}>
                <span className="status-icon">{getStatusIcon()}</span>
                <span className="status-text">{getStatusText()}</span>
                {status.queuedRequests > 0 && (
                    <span className="queued-requests">
                        ({status.queuedRequests} queued)
                    </span>
                )}
                <button className="details-toggle">
                    {showDetails ? '▼' : '▶'}
                </button>
            </div>

            {retryInfo && (
                <div className="retry-info">
                    <span>Retry {retryInfo.attempt}/{retryInfo.maxAttempts} in {Math.ceil(retryInfo.delay/1000)}s</span>
                </div>
            )}

            {status.connectionState === 'disconnected' && (
                <div className="connection-actions">
                    <button onClick={handleRetryClick} className="retry-button">
                        🔄 Retry Connection
                    </button>
                </div>
            )}

            {showDetails && (
                <div className="status-details">
                    <div className="detail-row">
                        <span className="detail-label">Session ID:</span>
                        <span className="detail-value">{status.sessionId}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Network Quality:</span>
                        <span className="detail-value">{status.networkQuality}</span>
                    </div>
                    {status.lastHealthCheck && (
                        <>
                            <div className="detail-row">
                                <span className="detail-label">Last Health Check:</span>
                                <span className="detail-value">
                                    {new Date(status.lastHealthCheck.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Response Time:</span>
                                <span className="detail-value">
                                    {status.lastHealthCheck.responseTime}ms
                                </span>
                            </div>
                        </>
                    )}
                    {status.queuedRequests > 0 && (
                        <div className="detail-row">
                            <span className="detail-label">Queued Requests:</span>
                            <span className="detail-value">{status.queuedRequests}</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ConnectionStatus;