import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Download, ExternalLink, Wifi, WifiOff } from 'lucide-react';
import './PDFViewerComponent.css';

// Configure PDF.js worker to use CDN
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

// Enhanced PDF options for mobile performance
const PDF_OPTIONS = {
  cMapUrl: `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/cmaps/`,
  cMapPacked: true,
  standardFontDataUrl: `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/standard_fonts/`,
  // Enable worker for better performance
  useOnlyCssZoom: true,
  // Disable features for performance
  disableAutoFetch: false,
  disableStream: false,
  // Memory management
  maxImageSize: 1024 * 1024, // 1MB max image size
  // Performance optimization
  verbosity: 0 // Reduce console output
};

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
    setLoading(false);
    setLoadingProgress(0);
    
    let errorMessage = 'Failed to load PDF document';
    let errorType = 'unknown';
    
    // Categorize different types of errors
    if (!isOnline) {
      errorType = 'network';
      errorMessage = 'No internet connection. Please check your network and try again.';
    } else if (loadError.name === 'InvalidPDFException') {
      errorType = 'invalid';
      errorMessage = 'This PDF file is corrupted or invalid.';
    } else if (loadError.name === 'MissingPDFException') {
      errorType = 'missing';
      errorMessage = 'PDF file not found on server.';
    } else if (loadError.name === 'UnexpectedResponseException') {
      errorType = 'server';
      errorMessage = 'Server error while loading PDF.';
    } else if (loadError.message?.includes('fetch')) {
      errorType = 'network';
      errorMessage = 'Network error while loading PDF.';
    } else if (loadError.message?.includes('memory') || loadError.message?.includes('Memory')) {
      errorType = 'memory';
      errorMessage = 'PDF file is too large for this device.';
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
    }
  }, []);

  const handleRetry = useCallback(() => {
    if (retryCount >= 3) return;
    
    setRetryCount(prev => prev + 1);
    setLoading(true);
    setError(null);
    setLoadingProgress(0);
    loadStartTimeRef.current = Date.now();
    
    // Add delay before retry to avoid hammering the server
    retryTimeoutRef.current = setTimeout(() => {
      // Force re-render by clearing the error state
      // (pageNumber is managed externally)
    }, 1000 * retryCount);
  }, [retryCount]);

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