import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Download, ExternalLink, Wifi, WifiOff } from 'lucide-react';
import { pdfDebugLog, runComprehensiveDebug, testFileAccess } from './PDFDebugHelper';
import './PDFViewerComponent.css';

// Use the enhanced debug logger from PDFDebugHelper
const debugLog = pdfDebugLog;

// Test PDF.js worker accessibility
const testWorkerAccess = async () => {
  const workerUrls = [
    `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`,
    `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`,
    `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`,
    '/pdf.worker.min.js' // Local fallback
  ];

  for (const url of workerUrls) {
    try {
      debugLog('WORKER-TEST', `Testing worker URL: ${url}`);
      const response = await fetch(url, { method: 'HEAD' });
      if (response.ok) {
        debugLog('WORKER-TEST', `✅ Worker accessible: ${url}`);
        return url;
      } else {
        debugLog('WORKER-TEST', `❌ Worker failed (${response.status}): ${url}`);
      }
    } catch (error) {
      debugLog('WORKER-TEST', `❌ Worker error: ${url}`, error);
    }
  }
  
  debugLog('WORKER-TEST', '❌ No working PDF.js worker found!');
  return null;
};

// Initialize PDF.js worker with fallback
const initializePDFWorker = async () => {
  debugLog('WORKER-INIT', 'Starting PDF.js worker initialization...');
  debugLog('WORKER-INIT', `PDF.js version: ${pdfjs.version}`);
  
  const workingWorkerUrl = await testWorkerAccess();
  if (workingWorkerUrl) {
    pdfjs.GlobalWorkerOptions.workerSrc = workingWorkerUrl;
    debugLog('WORKER-INIT', `✅ PDF.js worker configured: ${workingWorkerUrl}`);
  } else {
    debugLog('WORKER-INIT', '❌ PDF.js worker initialization failed!');
    throw new Error('PDF.js worker could not be initialized');
  }
};

// Initialize worker immediately
initializePDFWorker().catch(error => {
  debugLog('WORKER-INIT', '❌ Critical: PDF.js worker initialization failed', error);
});

// Enhanced PDF options with debugging
const PDF_OPTIONS = {
  cMapUrl: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/cmaps/`,
  cMapPacked: true,
  standardFontDataUrl: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/standard_fonts/`,
  // Enable worker for better performance
  useOnlyCssZoom: true,
  // Enable features for better loading
  disableAutoFetch: false,
  disableStream: false,
  disableRange: false,
  // Memory management
  maxImageSize: 1024 * 1024, // 1MB max image size
  // Debugging - enable verbose logging for debugging
  verbosity: 1, // Enable logging for debugging
  // Timeout settings
  httpHeaders: {
    'Cache-Control': 'no-cache'
  }
};

// File URL testing is now imported from PDFDebugHelper

export const PDFViewerComponent = ({ 
  fileUrl, 
  filename, 
  pageNumber: externalPageNumber = 1,
  scale: externalScale = 1.0,
  onLoadSuccess, 
  onLoadError 
}) => {
  const [numPages, setNumPages] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [retryCount, setRetryCount] = useState(0);
  const [documentLoadTime, setDocumentLoadTime] = useState(null);
  
  // Use external props for page and scale
  const pageNumber = externalPageNumber;
  const scale = externalScale;
  
  // Refs for cleanup and performance
  const documentRef = useRef(null);
  const pageRef = useRef(null);
  const loadStartTimeRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  const loadingTimeoutRef = useRef(null);
  
  // Initialize debugging for this component instance
  useEffect(() => {
    debugLog('COMPONENT-INIT', `PDFViewerComponent initialized`, {
      fileUrl,
      filename,
      pageNumber,
      scale,
      isOnline: navigator.onLine,
      userAgent: navigator.userAgent
    });
    
    // Run comprehensive debugging
    runComprehensiveDebug(fileUrl).then(results => {
      debugLog('COMPREHENSIVE-DEBUG', 'Debug suite completed', results);
    });
  }, [fileUrl, filename, pageNumber, scale]);

  // Calculate optimal scale for mobile devices (informational only since scale is external)
  const getOptimalScale = useCallback(() => {
    const isMobile = window.innerWidth <= 768;
    const isSmallMobile = window.innerWidth <= 480;
    
    if (isSmallMobile) {
      return 0.8;
    } else if (isMobile) {
      return 0.9;
    }
    return 1.0;
  }, []);

  // Online/offline detection
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Handle orientation change (scale is managed externally)
  useEffect(() => {
    const handleOrientationChange = () => {
      // Force re-render of PDF page on orientation change
      setTimeout(() => {
        if (pageRef.current) {
          pageRef.current = null;
        }
      }, 100);
    };

    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('resize', handleOrientationChange);

    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
      window.removeEventListener('resize', handleOrientationChange);
    };
  }, []);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (documentRef.current) {
      try {
        documentRef.current.destroy();
      } catch (e) {
        console.warn('Error destroying PDF document:', e);
      }
      documentRef.current = null;
    }

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }

    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
      loadingTimeoutRef.current = null;
    }

    // Clear any cached pages
    if (pageRef.current) {
      pageRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  const onDocumentLoadSuccess = useCallback((pdf) => {
    const loadTime = Date.now() - loadStartTimeRef.current;
    
    // Clear loading timeout
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
      loadingTimeoutRef.current = null;
    }
    
    debugLog('LOAD-SUCCESS', `✅ PDF loaded successfully!`, {
      numPages: pdf.numPages,
      loadTime: `${loadTime}ms`,
      fileSize: pdf._pdfInfo?.length || 0,
      fingerprint: pdf.fingerprint,
      pdfInfo: pdf._pdfInfo
    });
    
    setNumPages(pdf.numPages);
    setLoading(false);
    setError(null);
    setLoadingProgress(100);
    setDocumentLoadTime(loadTime);
    setRetryCount(0);
    
    documentRef.current = pdf;
    
    console.log(`PDF loaded successfully: ${pdf.numPages} pages in ${loadTime}ms`);
    
    if (onLoadSuccess) {
      onLoadSuccess({ 
        numPages: pdf.numPages, 
        loadTime,
        fileSize: pdf._pdfInfo?.length || 0
      });
    }
  }, [onLoadSuccess]);

  const onDocumentLoadError = useCallback((loadError) => {
    // Clear loading timeout
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
      loadingTimeoutRef.current = null;
    }
    
    debugLog('LOAD-ERROR', `❌ PDF load failed!`, {
      error: loadError,
      errorName: loadError.name,
      errorMessage: loadError.message,
      errorStack: loadError.stack,
      fileUrl,
      retryCount,
      isOnline,
      loadTime: Date.now() - loadStartTimeRef.current
    });
    
    setLoading(false);
    setLoadingProgress(0);
    
    let errorMessage = 'Failed to load PDF document';
    let errorType = 'unknown';
    
    // Categorize different types of errors with enhanced debugging
    if (!isOnline) {
      errorType = 'network';
      errorMessage = 'No internet connection. Please check your network and try again.';
      debugLog('ERROR-ANALYSIS', 'Offline error detected');
    } else if (loadError.name === 'InvalidPDFException') {
      errorType = 'invalid';
      errorMessage = 'This PDF file is corrupted or invalid.';
      debugLog('ERROR-ANALYSIS', 'Invalid PDF format detected');
    } else if (loadError.name === 'MissingPDFException') {
      errorType = 'missing';
      errorMessage = 'PDF file not found on server.';
      debugLog('ERROR-ANALYSIS', 'PDF file not found on server');
    } else if (loadError.name === 'UnexpectedResponseException') {
      errorType = 'server';
      errorMessage = 'Server error while loading PDF.';
      debugLog('ERROR-ANALYSIS', 'Server response error');
    } else if (loadError.message?.includes('fetch')) {
      errorType = 'network';
      errorMessage = 'Network error while loading PDF.';
      debugLog('ERROR-ANALYSIS', 'Network fetch error');
    } else if (loadError.message?.includes('memory') || loadError.message?.includes('Memory')) {
      errorType = 'memory';
      errorMessage = 'PDF file is too large for this device.';
      debugLog('ERROR-ANALYSIS', 'Memory/size error');
    } else if (loadError.message?.includes('worker')) {
      errorType = 'worker';
      errorMessage = 'PDF.js worker failed to load.';
      debugLog('ERROR-ANALYSIS', 'PDF.js worker error');
    } else if (loadError.message?.includes('CORS')) {
      errorType = 'cors';
      errorMessage = 'Cross-origin request blocked.';
      debugLog('ERROR-ANALYSIS', 'CORS error detected');
    }

    const errorInfo = {
      type: errorType,
      message: errorMessage,
      originalError: loadError,
      retryCount,
      isOnline
    };

    setError(errorInfo);
    
    console.error('PDF load error:', {
      error: loadError,
      type: errorType,
      message: errorMessage,
      retryCount,
      fileUrl
    });

    if (onLoadError) {
      onLoadError(errorInfo);
    }
  }, [isOnline, retryCount, fileUrl, onLoadError]);

  const onDocumentLoadProgress = useCallback(({ loaded, total }) => {
    if (total > 0) {
      const progress = Math.round((loaded / total) * 100);
      setLoadingProgress(progress);
      
      debugLog('LOAD-PROGRESS', `Loading progress: ${progress}%`, {
        loaded,
        total,
        percentage: progress,
        remainingBytes: total - loaded
      });
    } else {
      debugLog('LOAD-PROGRESS', 'Loading progress: unknown total size', { loaded });
    }
  }, []);

  const onDocumentLoadStart = useCallback(() => {
    loadStartTimeRef.current = Date.now();
    setLoading(true);
    setError(null);
    setLoadingProgress(0);
    
    debugLog('LOAD-START', `📄 Starting PDF document load`, {
      fileUrl,
      timestamp: new Date().toISOString(),
      retryCount
    });
    
    // Set loading timeout (30 seconds)
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }
    
    loadingTimeoutRef.current = setTimeout(() => {
      debugLog('LOAD-TIMEOUT', 'PDF loading timeout reached (30s)');
      setLoading(false);
      setError({
        type: 'timeout',
        message: 'PDF loading timed out. The file may be too large or the connection is slow.',
        originalError: new Error('Loading timeout'),
        retryCount,
        isOnline
      });
    }, 30000); // 30 second timeout
  }, [fileUrl, retryCount, isOnline]);

  const handleRetry = useCallback(() => {
    if (retryCount >= 3) {
      debugLog('RETRY-LIMIT', 'Maximum retry attempts reached', { retryCount });
      return;
    }
    
    debugLog('RETRY-ATTEMPT', `Attempting retry ${retryCount + 1}/3`, {
      currentRetryCount: retryCount,
      fileUrl,
      lastError: error
    });
    
    setRetryCount(prev => prev + 1);
    setLoading(true);
    setError(null);
    setLoadingProgress(0);
    loadStartTimeRef.current = Date.now();
    
    // Test file access before retry
    testFileAccess(fileUrl).then(result => {
      if (!result.accessible) {
        debugLog('RETRY-ABORT', 'File not accessible, aborting retry', result);
        setError({
          type: 'network',
          message: 'File is not accessible from the server',
          originalError: new Error('File accessibility check failed'),
          retryCount: retryCount + 1,
          isOnline
        });
        setLoading(false);
        return;
      }
      
      // Add delay before retry to avoid hammering the server
      retryTimeoutRef.current = setTimeout(() => {
        debugLog('RETRY-EXECUTE', 'Executing retry after delay');
        // Force re-render by updating the key in the Document component
      }, 1000 * (retryCount + 1));
    });
  }, [retryCount, fileUrl, error, isOnline]);

  const handleDownload = useCallback(() => {
    if (fileUrl) {
      const link = document.createElement('a');
      link.href = fileUrl;
      link.download = filename || 'document.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, [fileUrl, filename]);

  const handleOpenInNewTab = useCallback(() => {
    if (fileUrl) {
      window.open(fileUrl, '_blank', 'noopener,noreferrer');
    }
  }, [fileUrl]);

  // Initialize load start time
  useEffect(() => {
    loadStartTimeRef.current = Date.now();
    setLoading(true);
    setError(null);
    setLoadingProgress(0);
  }, [fileUrl]);

  // Error state rendering
  if (error) {
    return (
      <div className="pdf-viewer-error">
        <div className="pdf-error-content">
          <div className="pdf-error-icon">
            {!isOnline ? <WifiOff className="error-icon offline" /> : <Wifi className="error-icon" />}
          </div>
          
          <h3 className="pdf-error-title">
            {error.type === 'network' ? 'Connection Problem' : 'PDF Load Error'}
          </h3>
          
          <p className="pdf-error-message">{error.message}</p>
          
          <div className="pdf-error-actions">
            {retryCount < 3 && (
              <button 
                onClick={handleRetry}
                className="pdf-error-btn pdf-error-btn-primary"
                aria-label={`Retry loading PDF (attempt ${retryCount + 1} of 3)`}
              >
                Retry ({3 - retryCount} left)
              </button>
            )}
            
            <button 
              onClick={handleDownload}
              className="pdf-error-btn pdf-error-btn-secondary"
              aria-label="Download PDF file"
            >
              <Download className="btn-icon" />
              Download
            </button>
            
            <button 
              onClick={handleOpenInNewTab}
              className="pdf-error-btn pdf-error-btn-secondary"
              aria-label="Open PDF in new tab"
            >
              <ExternalLink className="btn-icon" />
              New Tab
            </button>
          </div>
          
          <div className="pdf-error-details">
            <small>
              Error type: {error.type} | Attempts: {retryCount + 1}
              {documentLoadTime && ` | Last load: ${documentLoadTime}ms`}
            </small>
          </div>
        </div>
      </div>
    );
  }

  // Loading state rendering
  if (loading) {
    return (
      <div className="pdf-viewer-loading">
        <div className="pdf-loading-content">
          <div className="pdf-loading-spinner">
            <div className="spinner-ring"></div>
          </div>
          
          <h3 className="pdf-loading-title">Loading PDF...</h3>
          
          <div className="pdf-loading-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${loadingProgress}%` }}
                role="progressbar"
                aria-valuenow={loadingProgress}
                aria-valuemin="0"
                aria-valuemax="100"
                aria-label={`Loading progress: ${loadingProgress}%`}
              ></div>
            </div>
            <span className="progress-text">{loadingProgress}%</span>
          </div>
          
          <p className="pdf-loading-subtitle">
            {loadingProgress < 20 ? 'Connecting to server...' :
             loadingProgress < 50 ? 'Downloading document...' :
             loadingProgress < 80 ? 'Processing PDF...' : 'Almost ready...'}
          </p>
          
          {retryCount > 0 && (
            <p className="pdf-loading-retry-info">
              Retry attempt {retryCount} of 3
            </p>
          )}
        </div>
      </div>
    );
  }

  // Successful PDF rendering
  return (
    <div className="pdf-viewer-content">
      <div className="pdf-document-container">
        <Document
          key={`${fileUrl}-${retryCount}`} // Force re-render on retry
          file={fileUrl}
          onLoadStart={onDocumentLoadStart}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          onLoadProgress={onDocumentLoadProgress}
          loading=""
          error=""
          noData=""
          options={PDF_OPTIONS}
        >
          <Page
            key={`page-${pageNumber}-${scale}`}
            pageNumber={pageNumber}
            scale={scale}
            renderTextLayer={false}
            renderAnnotationLayer={false}
            className="pdf-page"
            loading=""
            error=""
            noData=""
            canvasRef={pageRef}
          />
        </Document>
      </div>
      
      {documentLoadTime && (
        <div className="pdf-performance-info" aria-hidden="true">
          <small>
            Loaded {numPages} pages in {documentLoadTime}ms
          </small>
        </div>
      )}
    </div>
  );
};