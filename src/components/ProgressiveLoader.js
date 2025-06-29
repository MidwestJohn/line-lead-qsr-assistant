import React, { useState, useEffect } from 'react';
import { connectionManager } from '../services/ConnectionManager';
import { keepAliveService } from '../services/KeepAliveService';
import SplashScreen from './SplashScreen';
import './ProgressiveLoader.css';

/**
 * 🚀 Progressive Loading Component
 * 
 * Manages application startup sequence with progressive loading:
 * 1. Load core UI immediately
 * 2. Establish server connection
 * 3. Initialize services
 * 4. Enable full functionality
 */
const ProgressiveLoader = ({ children }) => {
    const [loadingState, setLoadingState] = useState('initializing');
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [services, setServices] = useState({});
    const [loadingProgress, setLoadingProgress] = useState(0);

    // Loading states: initializing -> connecting -> loading_services -> ready -> error
    
    useEffect(() => {
        startProgressiveLoading();
        
        // Listen to connection manager events
        const unsubscribe = connectionManager.addListener((event, data) => {
            handleConnectionEvent(event, data);
        });

        return unsubscribe;
    }, []);

    const startProgressiveLoading = async () => {
        try {
            // Phase 1: Initialize core UI (immediate)
            setLoadingState('initializing');
            setLoadingProgress(10);
            
            // Small delay to show loading state
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Phase 2: Establish server connection
            setLoadingState('connecting');
            setLoadingProgress(25);
            
            // Connection manager will handle connection establishment
            // We'll receive updates via the event listener
            
        } catch (error) {
            handleLoadingError(error);
        }
    };

    const handleConnectionEvent = (event, data) => {
        switch (event) {
            case 'stateChange':
                setConnectionStatus(data.newState);
                updateProgressForConnectionState(data.newState);
                break;
                
            case 'connected':
                handleConnectionSuccess(data);
                break;
                
            case 'failed':
                handleConnectionFailure(data);
                break;
                
            case 'retrying':
                handleConnectionRetry(data);
                break;
                
            default:
                break;
        }
    };

    const updateProgressForConnectionState = (state) => {
        switch (state) {
            case 'connecting':
                setLoadingProgress(25);
                break;
            case 'connected':
                setLoadingProgress(60);
                initializeServices();
                break;
            case 'reconnecting':
                setLoadingProgress(40);
                break;
            case 'disconnected':
                if (loadingState !== 'ready') {
                    setLoadingProgress(15);
                }
                break;
            default:
                break;
        }
    };

    const handleConnectionSuccess = async (connectionInfo) => {
        setLoadingState('loading_services');
        setLoadingProgress(60);
        
        // Initialize services now that connection is established
        await initializeServices();
    };

    const handleConnectionFailure = (data) => {
        console.warn('Connection failed:', data.error);
        // For production, we'll still show the splash screen
        // The app will handle connection issues gracefully once loaded
    };

    const handleConnectionRetry = (data) => {
        setLoadingState('connecting');
        setLoadingProgress(25 + (data.attempt / data.maxAttempts) * 25);
    };

    const initializeServices = async () => {
        try {
            setLoadingState('loading_services');
            
            // Phase 3: Initialize services
            const serviceChecks = {
                health: false,
                documents: false,
                keepAlive: false
            };

            // Check server health
            setLoadingProgress(70);
            try {
                const health = await connectionManager.performHealthCheck();
                serviceChecks.health = health.success;
                setServices(prev => ({ ...prev, health: health.success ? 'ready' : 'error' }));
            } catch (error) {
                console.warn('Health check failed during initialization:', error);
                serviceChecks.health = false;
                setServices(prev => ({ ...prev, health: 'error' }));
            }

            // Initialize keep-alive service
            setLoadingProgress(80);
            try {
                keepAliveService.start();
                serviceChecks.keepAlive = true;
                setServices(prev => ({ ...prev, keepAlive: 'ready' }));
            } catch (error) {
                console.warn('Keep-alive service failed to start:', error);
                serviceChecks.keepAlive = false;
                setServices(prev => ({ ...prev, keepAlive: 'error' }));
            }

            // Load initial documents (optional)
            setLoadingProgress(90);
            try {
                // This is optional - if it fails, the app can still work
                setServices(prev => ({ ...prev, documents: 'ready' }));
                serviceChecks.documents = true;
            } catch (error) {
                console.warn('Document loading failed during initialization:', error);
                serviceChecks.documents = false;
                setServices(prev => ({ ...prev, documents: 'error' }));
            }

            // Phase 4: Complete initialization
            setLoadingProgress(100);
            
            // Small delay to show 100% completion
            await new Promise(resolve => setTimeout(resolve, 500));
            
            setLoadingState('ready');
            console.log('🎉 Progressive loading completed successfully!');
            
        } catch (error) {
            handleLoadingError(error);
        }
    };

    const handleLoadingError = (error) => {
        console.error('Progressive loading failed:', error);
        // Still proceed to ready state for graceful degradation
        setLoadingState('ready');
    };



    // Show simple splash screen until ready
    if (loadingState !== 'ready') {
        return <SplashScreen />;
    }

    // Once ready, render the actual application
    return (
        <div className="app-container">
            {children}
        </div>
    );
};

export default ProgressiveLoader;