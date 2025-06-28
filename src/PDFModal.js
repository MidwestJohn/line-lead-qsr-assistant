import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  X, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  ZoomIn, 
  ZoomOut 
} from 'lucide-react';
import PDFErrorBoundary from './PDFErrorBoundary';
import LazyPDFViewer from './LazyPDFViewer';
import './PDFModal.css';
import './PDFErrorBoundary.css';

const PDFModal = ({ fileUrl, filename, isOpen, onClose }) => {
  // PDF state
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  
  // Zoom state
  const [scale, setScale] = useState(1.0);
  const MIN_SCALE = 0.5;
  const MAX_SCALE = 3.0;
  const SCALE_INCREMENT = 0.2;
  
  // Accessibility and performance refs
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);
  const firstFocusableRef = useRef(null);
  const lastFocusableRef = useRef(null);
  
  // Performance monitoring
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  
  // Reset state when modal opens/closes or file changes
  useEffect(() => {
    if (isOpen && fileUrl) {
      setPageNumber(1);
      setScale(1.0);
      setLoading(true);
      setError(null);
      setNumPages(null);
      setLoadingProgress(0);
      setPerformanceMetrics(null);
    }
  }, [isOpen, fileUrl]);

  // Focus management for accessibility
  useEffect(() => {
    if (isOpen) {
      // Store the previously focused element
      previousFocusRef.current = document.activeElement;
      
      // Focus the modal
      setTimeout(() => {
        if (firstFocusableRef.current) {
          firstFocusableRef.current.focus();
        } else if (modalRef.current) {
          modalRef.current.focus();
        }
      }, 100);
    } else {
      // Restore focus when modal closes
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
    
    // Store performance metrics
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

  // Zoom handlers
  const zoomIn = useCallback(() => {
    setScale(prevScale => Math.min(MAX_SCALE, prevScale + SCALE_INCREMENT));
  }, []);

  const zoomOut = useCallback(() => {
    setScale(prevScale => Math.max(MIN_SCALE, prevScale - SCALE_INCREMENT));
  }, []);

  // Enhanced keyboard event handler with accessibility
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        onClose();
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
      case 'Home':
        e.preventDefault();
        setPageNumber(1);
        break;
      case 'End':
        e.preventDefault();
        if (numPages) setPageNumber(numPages);
        break;
      case 'Tab':
        // Handle focus trapping
        handleTabKey(e);
        break;
      default:
        break;
    }
  }, [isOpen, onClose, goToPrevPage, goToNextPage, zoomIn, zoomOut, numPages]);

  // Focus trapping for accessibility
  const handleTabKey = useCallback((e) => {
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
  }, []);

  // Add/remove keyboard event listener with cleanup
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden'; // Prevent background scroll
      
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

  // Download handler
  const handleDownload = () => {
    if (fileUrl) {
      const link = document.createElement('a');
      link.href = fileUrl;
      link.download = filename || 'document.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Close modal when clicking overlay
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="pdf-modal-overlay" 
      onClick={handleOverlayClick}
      role="presentation"
    >
      <div 
        ref={modalRef}
        className="pdf-modal-container"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pdf-modal-title"
        aria-describedby="pdf-modal-description"
      >
        {/* Header */}
        <div className="pdf-modal-header">
          <div className="pdf-modal-title">
            <span 
              id="pdf-modal-title" 
              className="pdf-filename"
            >
              {filename || 'Document'}
            </span>
            {numPages && (
              <span 
                className="pdf-page-count"
                aria-label={`Document has ${numPages} pages`}
              >
                ({numPages} pages)
              </span>
            )}
            {performanceMetrics && (
              <span 
                className="pdf-load-time"
                aria-hidden="true"
                title={`Loaded in ${performanceMetrics.loadTime}ms`}
              >
                {performanceMetrics.loadTime < 1000 ? 'Fast' : 
                 performanceMetrics.loadTime < 3000 ? 'Normal' : 'Slow'} load
              </span>
            )}
          </div>
          <div className="pdf-modal-header-actions">
            <button 
              ref={firstFocusableRef}
              onClick={handleDownload}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Download PDF file to your device"
              aria-label={`Download ${filename || 'PDF document'}`}
            >
              <Download className="pdf-modal-icon" aria-hidden="true" />
              <span className="sr-only">Download</span>
            </button>
            <button 
              ref={lastFocusableRef}
              onClick={onClose}
              className="pdf-modal-btn pdf-modal-btn-close"
              title="Close PDF preview"
              aria-label="Close PDF preview modal"
            >
              <X className="pdf-modal-icon" aria-hidden="true" />
              <span className="sr-only">Close</span>
            </button>
          </div>
        </div>

        {/* Control Bar */}
        <div 
          className="pdf-modal-controls"
          role="toolbar"
          aria-label="PDF navigation and zoom controls"
        >
          <div className="pdf-modal-nav-controls" role="group" aria-label="Page navigation">
            <button 
              onClick={goToPrevPage}
              disabled={pageNumber <= 1 || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Go to previous page (Left arrow)"
              aria-label={`Go to previous page. Currently on page ${pageNumber}`}
            >
              <ChevronLeft className="pdf-modal-icon" aria-hidden="true" />
              <span className="sr-only">Previous</span>
            </button>
            
            <span 
              className="pdf-page-indicator"
              aria-live="polite"
              aria-atomic="true"
              role="status"
            >
              {loading ? 'Loading...' : `Page ${pageNumber} of ${numPages || 0}`}
            </span>
            
            <button 
              onClick={goToNextPage}
              disabled={pageNumber >= (numPages || 0) || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Go to next page (Right arrow)"
              aria-label={`Go to next page. Currently on page ${pageNumber} of ${numPages || 0}`}
            >
              <ChevronRight className="pdf-modal-icon" aria-hidden="true" />
              <span className="sr-only">Next</span>
            </button>
          </div>

          <div className="pdf-modal-zoom-controls" role="group" aria-label="Zoom controls">
            <button 
              onClick={zoomOut}
              disabled={scale <= MIN_SCALE || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Zoom out (- key)"
              aria-label={`Zoom out. Current zoom: ${Math.round(scale * 100)}%`}
            >
              <ZoomOut className="pdf-modal-icon" aria-hidden="true" />
              <span className="sr-only">Zoom out</span>
            </button>
            
            <span 
              className="pdf-zoom-indicator"
              aria-live="polite"
              role="status"
            >
              {Math.round(scale * 100)}%
            </span>
            
            <button 
              onClick={zoomIn}
              disabled={scale >= MAX_SCALE || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Zoom in (+ key)"
              aria-label={`Zoom in. Current zoom: ${Math.round(scale * 100)}%`}
            >
              <ZoomIn className="pdf-modal-icon" aria-hidden="true" />
              <span className="sr-only">Zoom in</span>
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <div 
          className="pdf-modal-content"
          id="pdf-modal-description"
          aria-label="PDF document content"
        >
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
        </div>

        {/* Mobile Navigation */}
        <div className="pdf-modal-mobile-nav">
          <button 
            onClick={goToPrevPage}
            disabled={pageNumber <= 1 || loading}
            className="pdf-modal-btn pdf-modal-btn-secondary pdf-modal-mobile-btn"
            aria-label="Previous page"
          >
            <ChevronLeft className="pdf-modal-icon" />
            Previous
          </button>
          
          <span className="pdf-page-indicator-mobile">
            {loading ? 'Loading...' : `Page ${pageNumber} of ${numPages || 0}`}
          </span>
          
          <button 
            onClick={goToNextPage}
            disabled={pageNumber >= (numPages || 0) || loading}
            className="pdf-modal-btn pdf-modal-btn-secondary pdf-modal-mobile-btn"
            aria-label="Next page"
          >
            Next
            <ChevronRight className="pdf-modal-icon" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PDFModal;