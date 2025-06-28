import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  X, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  ZoomIn, 
  ZoomOut,
  Maximize,
  RotateCcw,
  HelpCircle,
  Grid3X3
} from 'lucide-react';
import PDFErrorBoundary from './PDFErrorBoundary';
import LazyPDFViewer from './LazyPDFViewer';
import PDFLoadingSkeleton from './PDFLoadingSkeleton';
import PDFKeyboardHelp from './PDFKeyboardHelp';
import './EnhancedPDFModal.css';
import './PDFErrorBoundary.css';
import './PDFLoadingSkeleton.css';
import './PDFKeyboardHelp.css';

const EnhancedPDFModal = ({ fileUrl, filename, isOpen, onClose }) => {
  // PDF state
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  
  // Zoom and view state
  const [scale, setScale] = useState(1.0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);
  const [autoScale, setAutoScale] = useState('fit-width'); // 'fit-width', 'fit-page', 'custom'
  
  // Zoom constants
  const MIN_SCALE = 0.25;
  const MAX_SCALE = 5.0;
  const SCALE_INCREMENT = 0.25;
  
  // User preferences (would be saved to localStorage in production)
  const [userPreferences, setUserPreferences] = useState({
    lastZoomLevel: 1.0,
    preferredScaling: 'fit-width',
    showHelpOnFirstOpen: true
  });
  
  // Accessibility and performance refs
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);
  const firstFocusableRef = useRef(null);
  const lastFocusableRef = useRef(null);
  
  // Performance monitoring
  const [performanceMetrics, setPerformanceMetrics] = useState(null);

  // Calculate smart auto-scaling based on device and preferences
  const calculateOptimalScale = useCallback(() => {
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth <= 1024 && window.innerWidth > 768;
    
    switch (autoScale) {
      case 'fit-width':
        if (isMobile) return 0.8;
        if (isTablet) return 0.9;
        return 1.0;
      case 'fit-page':
        if (isMobile) return 0.6;
        if (isTablet) return 0.7;
        return 0.8;
      case 'custom':
        return userPreferences.lastZoomLevel;
      default:
        return 1.0;
    }
  }, [autoScale, userPreferences.lastZoomLevel]);

  // Reset state when modal opens/closes or file changes
  useEffect(() => {
    if (isOpen && fileUrl) {
      setPageNumber(1);
      setScale(calculateOptimalScale());
      setLoading(true);
      setError(null);
      setNumPages(null);
      setLoadingProgress(0);
      setPerformanceMetrics(null);
      setShowThumbnails(false);
      
      // Show help on first open if user hasn't seen it
      if (userPreferences.showHelpOnFirstOpen) {
        setTimeout(() => {
          setShowKeyboardHelp(true);
          setUserPreferences(prev => ({ ...prev, showHelpOnFirstOpen: false }));
        }, 2000);
      }
    }
  }, [isOpen, fileUrl, calculateOptimalScale, userPreferences.showHelpOnFirstOpen]);

  // Auto-scale handling
  useEffect(() => {
    if (!loading && autoScale !== 'custom') {
      setScale(calculateOptimalScale());
    }
  }, [autoScale, calculateOptimalScale, loading]);

  // Focus management for accessibility
  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement;
      
      setTimeout(() => {
        if (firstFocusableRef.current) {
          firstFocusableRef.current.focus();
        } else if (modalRef.current) {
          modalRef.current.focus();
        }
      }, 150);
    } else {
      if (previousFocusRef.current && previousFocusRef.current.focus) {
        previousFocusRef.current.focus();
      }
    }
  }, [isOpen]);

  // Document load handlers with performance tracking
  const onDocumentLoadSuccess = useCallback((result) => {
    setNumPages(result.numPages);
    setLoading(false);
    setError(null);
    setLoadingProgress(100);
    
    setPerformanceMetrics({
      loadTime: result.loadTime,
      pageCount: result.numPages,
      fileSize: result.fileSize
    });
    
    console.log('PDF loaded successfully:', {
      pages: result.numPages,
      loadTime: result.loadTime,
      fileSize: result.fileSize
    });
  }, []);

  const onDocumentLoadError = useCallback((errorInfo) => {
    setLoading(false);
    setError(errorInfo);
    setLoadingProgress(0);
    console.error('PDF load error:', errorInfo);
  }, []);

  // Navigation handlers
  const goToPrevPage = useCallback(() => {
    setPageNumber(page => Math.max(1, page - 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setPageNumber(page => Math.min(numPages || 1, page + 1));
  }, [numPages]);

  const goToPage = useCallback((page) => {
    setPageNumber(Math.max(1, Math.min(numPages || 1, page)));
  }, [numPages]);

  // Zoom handlers
  const zoomIn = useCallback(() => {
    setScale(prevScale => {
      const newScale = Math.min(MAX_SCALE, prevScale + SCALE_INCREMENT);
      setAutoScale('custom');
      setUserPreferences(prev => ({ ...prev, lastZoomLevel: newScale }));
      return newScale;
    });
  }, []);

  const zoomOut = useCallback(() => {
    setScale(prevScale => {
      const newScale = Math.max(MIN_SCALE, prevScale - SCALE_INCREMENT);
      setAutoScale('custom');
      setUserPreferences(prev => ({ ...prev, lastZoomLevel: newScale }));
      return newScale;
    });
  }, []);

  const resetZoom = useCallback(() => {
    setAutoScale('fit-width');
    setScale(calculateOptimalScale());
  }, [calculateOptimalScale]);

  // Fullscreen handling
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      modalRef.current?.requestFullscreen?.()
        .then(() => setIsFullscreen(true))
        .catch(err => console.log('Fullscreen error:', err));
    } else {
      document.exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch(err => console.log('Exit fullscreen error:', err));
    }
  }, []);

  // Enhanced keyboard event handler
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;

    // Don't handle shortcuts if help is open or user is typing
    if (showKeyboardHelp || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      return;
    }

    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        if (isFullscreen) {
          toggleFullscreen();
        } else {
          onClose();
        }
        break;
      case 'ArrowLeft':
        e.preventDefault();
        goToPrevPage();
        break;
      case 'ArrowRight':
        e.preventDefault();
        goToNextPage();
        break;
      case '+':
      case '=':
        e.preventDefault();
        zoomIn();
        break;
      case '-':
        e.preventDefault();
        zoomOut();
        break;
      case '0':
        e.preventDefault();
        resetZoom();
        break;
      case 'Home':
        e.preventDefault();
        setPageNumber(1);
        break;
      case 'End':
        e.preventDefault();
        if (numPages) setPageNumber(numPages);
        break;
      case 'f':
      case 'F':
        if (!e.ctrlKey && !e.metaKey) {
          e.preventDefault();
          toggleFullscreen();
        }
        break;
      case 'd':
      case 'D':
        if (!e.ctrlKey && !e.metaKey) {
          e.preventDefault();
          handleDownload();
        }
        break;
      case '?':
        e.preventDefault();
        setShowKeyboardHelp(true);
        break;
      case 'g':
      case 'G':
        e.preventDefault();
        setShowThumbnails(!showThumbnails);
        break;
      case 'Tab':
        handleTabKey(e);
        break;
      default:
        break;
    }
  }, [isOpen, showKeyboardHelp, isFullscreen, goToPrevPage, goToNextPage, zoomIn, zoomOut, resetZoom, numPages, toggleFullscreen, onClose, showThumbnails]);

  // Focus trapping for accessibility
  const handleTabKey = useCallback((e) => {
    if (showKeyboardHelp) return; // Let keyboard help handle its own focus
    
    const focusableElements = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (!focusableElements || focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }, [showKeyboardHelp]);

  // Add/remove keyboard event listener with cleanup
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      
      // Add accessibility attributes
      document.body.setAttribute('aria-hidden', 'true');
      if (modalRef.current) {
        modalRef.current.setAttribute('aria-modal', 'true');
        modalRef.current.setAttribute('role', 'dialog');
        modalRef.current.setAttribute('aria-labelledby', 'pdf-modal-title');
      }
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
      document.body.removeAttribute('aria-hidden');
    };
  }, [isOpen, handleKeyDown]);

  // Fullscreen change listener
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Download handler
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

  // Close modal when clicking overlay
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div 
        className={`enhanced-pdf-modal-overlay ${isFullscreen ? 'fullscreen' : ''}`}
        onClick={handleOverlayClick}
        role="presentation"
      >
        <div 
          ref={modalRef}
          className={`enhanced-pdf-modal-container ${isFullscreen ? 'fullscreen' : ''}`}
          role="dialog"
          aria-modal="true"
          aria-labelledby="pdf-modal-title"
          aria-describedby="pdf-modal-description"
        >
          {/* Header */}
          <div className="enhanced-pdf-modal-header">
            <div className="enhanced-pdf-modal-title">
              <span 
                id="pdf-modal-title" 
                className="enhanced-pdf-filename"
              >
                {filename || 'Document'}
              </span>
              {numPages && (
                <span 
                  className="enhanced-pdf-page-count"
                  aria-label={`Document has ${numPages} pages`}
                >
                  ({numPages} pages)
                </span>
              )}
              {performanceMetrics && (
                <span 
                  className="enhanced-pdf-load-time"
                  aria-hidden="true"
                  title={`Loaded in ${performanceMetrics.loadTime}ms`}
                >
                  {performanceMetrics.loadTime < 1000 ? '⚡ Fast' : 
                   performanceMetrics.loadTime < 3000 ? '🔄 Normal' : '🐌 Slow'} load
                </span>
              )}
            </div>
            <div className="enhanced-pdf-modal-header-actions">
              <button 
                onClick={() => setShowKeyboardHelp(true)}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Keyboard shortcuts (? key)"
                aria-label="Show keyboard shortcuts help"
              >
                <HelpCircle className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
              
              <button 
                onClick={() => setShowThumbnails(!showThumbnails)}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Toggle page thumbnails (G key)"
                aria-label="Toggle page thumbnails"
              >
                <Grid3X3 className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
              
              <button 
                onClick={toggleFullscreen}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Toggle fullscreen (F key)"
                aria-label="Toggle fullscreen mode"
              >
                <Maximize className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
              
              <button 
                ref={firstFocusableRef}
                onClick={handleDownload}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Download PDF file to your device (D key)"
                aria-label={`Download ${filename || 'PDF document'}`}
              >
                <Download className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
              
              <button 
                ref={lastFocusableRef}
                onClick={onClose}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-close"
                title="Close PDF preview (ESC key)"
                aria-label="Close PDF preview modal"
              >
                <X className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Control Bar */}
          <div 
            className="enhanced-pdf-modal-controls"
            role="toolbar"
            aria-label="PDF navigation and zoom controls"
          >
            <div className="enhanced-pdf-modal-nav-controls" role="group" aria-label="Page navigation">
              <button 
                onClick={goToPrevPage}
                disabled={pageNumber <= 1 || loading}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Go to previous page (Left arrow)"
                aria-label={`Go to previous page. Currently on page ${pageNumber}`}
              >
                <ChevronLeft className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
              
              <span 
                className="enhanced-pdf-page-indicator"
                aria-live="polite"
                aria-atomic="true"
                role="status"
              >
                {loading ? 'Loading...' : `Page ${pageNumber} of ${numPages || 0}`}
              </span>
              
              <button 
                onClick={goToNextPage}
                disabled={pageNumber >= (numPages || 0) || loading}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Go to next page (Right arrow)"
                aria-label={`Go to next page. Currently on page ${pageNumber} of ${numPages || 0}`}
              >
                <ChevronRight className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
            </div>

            <div className="enhanced-pdf-modal-zoom-controls" role="group" aria-label="Zoom controls">
              <button 
                onClick={zoomOut}
                disabled={scale <= MIN_SCALE || loading}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Zoom out (- key)"
                aria-label={`Zoom out. Current zoom: ${Math.round(scale * 100)}%`}
              >
                <ZoomOut className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
              
              <button
                onClick={resetZoom}
                className="enhanced-pdf-zoom-indicator"
                title="Reset zoom (0 key)"
                aria-label={`Current zoom: ${Math.round(scale * 100)}%. Click to reset.`}
              >
                {Math.round(scale * 100)}%
              </button>
              
              <button 
                onClick={zoomIn}
                disabled={scale >= MAX_SCALE || loading}
                className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary"
                title="Zoom in (+ key)"
                aria-label={`Zoom in. Current zoom: ${Math.round(scale * 100)}%`}
              >
                <ZoomIn className="enhanced-pdf-modal-icon" aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Main Content Area */}
          <div 
            className="enhanced-pdf-modal-content"
            id="pdf-modal-description"
            aria-label="PDF document content"
          >
            {loading ? (
              <PDFLoadingSkeleton 
                showProgress={true} 
                progress={loadingProgress} 
              />
            ) : (
              <PDFErrorBoundary fileUrl={fileUrl} filename={filename}>
                <LazyPDFViewer
                  fileUrl={fileUrl}
                  filename={filename}
                  pageNumber={pageNumber}
                  scale={scale}
                  onLoadSuccess={onDocumentLoadSuccess}
                  onLoadError={onDocumentLoadError}
                />
              </PDFErrorBoundary>
            )}
          </div>

          {/* Mobile Navigation */}
          <div className="enhanced-pdf-modal-mobile-nav">
            <button 
              onClick={goToPrevPage}
              disabled={pageNumber <= 1 || loading}
              className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary enhanced-pdf-modal-mobile-btn"
              aria-label="Previous page"
            >
              <ChevronLeft className="enhanced-pdf-modal-icon" />
              Previous
            </button>
            
            <span className="enhanced-pdf-page-indicator-mobile">
              {loading ? 'Loading...' : `Page ${pageNumber} of ${numPages || 0}`}
            </span>
            
            <button 
              onClick={goToNextPage}
              disabled={pageNumber >= (numPages || 0) || loading}
              className="enhanced-pdf-modal-btn enhanced-pdf-modal-btn-secondary enhanced-pdf-modal-mobile-btn"
              aria-label="Next page"
            >
              Next
              <ChevronRight className="enhanced-pdf-modal-icon" />
            </button>
          </div>
        </div>
      </div>

      {/* Keyboard Help Modal */}
      <PDFKeyboardHelp 
        isVisible={showKeyboardHelp}
        onClose={() => setShowKeyboardHelp(false)}
      />
    </>
  );
};

export default EnhancedPDFModal;