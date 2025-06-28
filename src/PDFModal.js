import React, { useState, useEffect, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { 
  X, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  ZoomIn, 
  ZoomOut 
} from 'lucide-react';
import './PDFModal.css';

// Configure PDF.js worker to use CDN
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const PDFModal = ({ fileUrl, filename, isOpen, onClose }) => {
  // PDF state
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Zoom state
  const [scale, setScale] = useState(1.0);
  const MIN_SCALE = 0.5;
  const MAX_SCALE = 3.0;
  const SCALE_INCREMENT = 0.2;
  
  // Reset state when modal opens/closes or file changes
  useEffect(() => {
    if (isOpen && fileUrl) {
      setPageNumber(1);
      setScale(1.0);
      setLoading(true);
      setError(null);
      setNumPages(null);
    }
  }, [isOpen, fileUrl]);

  // Document load handlers
  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (error) => {
    setLoading(false);
    setError(error);
    console.error('PDF load error:', error);
  };

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

  // Keyboard event handler
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'Escape':
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
      default:
        break;
    }
  }, [isOpen, onClose, goToPrevPage, goToNextPage, zoomIn, zoomOut]);

  // Add/remove keyboard event listener
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden'; // Prevent background scroll
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
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
    <div className="pdf-modal-overlay" onClick={handleOverlayClick}>
      <div className="pdf-modal-container">
        {/* Header */}
        <div className="pdf-modal-header">
          <div className="pdf-modal-title">
            <span className="pdf-filename">{filename || 'Document'}</span>
            {numPages && (
              <span className="pdf-page-count">({numPages} pages)</span>
            )}
          </div>
          <div className="pdf-modal-header-actions">
            <button 
              onClick={handleDownload}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Download PDF"
              aria-label="Download PDF"
            >
              <Download className="pdf-modal-icon" />
            </button>
            <button 
              onClick={onClose}
              className="pdf-modal-btn pdf-modal-btn-close"
              title="Close"
              aria-label="Close modal"
            >
              <X className="pdf-modal-icon" />
            </button>
          </div>
        </div>

        {/* Control Bar */}
        <div className="pdf-modal-controls">
          <div className="pdf-modal-nav-controls">
            <button 
              onClick={goToPrevPage}
              disabled={pageNumber <= 1 || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Previous page"
              aria-label="Previous page"
            >
              <ChevronLeft className="pdf-modal-icon" />
            </button>
            
            <span className="pdf-page-indicator">
              {loading ? 'Loading...' : `${pageNumber} of ${numPages || 0}`}
            </span>
            
            <button 
              onClick={goToNextPage}
              disabled={pageNumber >= (numPages || 0) || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Next page"
              aria-label="Next page"
            >
              <ChevronRight className="pdf-modal-icon" />
            </button>
          </div>

          <div className="pdf-modal-zoom-controls">
            <button 
              onClick={zoomOut}
              disabled={scale <= MIN_SCALE || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Zoom out"
              aria-label="Zoom out"
            >
              <ZoomOut className="pdf-modal-icon" />
            </button>
            
            <span className="pdf-zoom-indicator">
              {Math.round(scale * 100)}%
            </span>
            
            <button 
              onClick={zoomIn}
              disabled={scale >= MAX_SCALE || loading}
              className="pdf-modal-btn pdf-modal-btn-secondary"
              title="Zoom in"
              aria-label="Zoom in"
            >
              <ZoomIn className="pdf-modal-icon" />
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="pdf-modal-content">
          {loading && (
            <div className="pdf-modal-loading">
              <div className="pdf-modal-spinner"></div>
              <span>Loading PDF...</span>
            </div>
          )}

          {error && (
            <div className="pdf-modal-error">
              <h3>Unable to display PDF</h3>
              <p>The PDF could not be loaded. You can still download it below.</p>
              <button 
                onClick={handleDownload}
                className="pdf-modal-btn pdf-modal-btn-primary"
              >
                <Download className="pdf-modal-icon" />
                Download PDF
              </button>
            </div>
          )}

          {!loading && !error && (
            <div className="pdf-modal-document-container">
              <Document
                file={fileUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={<div className="pdf-modal-spinner"></div>}
                error={
                  <div className="pdf-modal-error">
                    <h3>Failed to load PDF</h3>
                    <button onClick={handleDownload} className="pdf-modal-btn pdf-modal-btn-primary">
                      <Download className="pdf-modal-icon" />
                      Download instead
                    </button>
                  </div>
                }
                options={{
                  cMapUrl: `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/cmaps/`,
                  cMapPacked: true,
                }}
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                  className="pdf-modal-page"
                />
              </Document>
            </div>
          )}
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