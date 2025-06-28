import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import './PDFPreview.css';

// Configure PDF.js worker to use CDN
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const PDFPreview = ({ file, onLoadSuccess, onLoadError }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
    if (onLoadSuccess) {
      onLoadSuccess({ numPages });
    }
  };

  const onDocumentLoadError = (error) => {
    setLoading(false);
    setError(error);
    console.error('PDF load error:', error);
    if (onLoadError) {
      onLoadError(error);
    }
  };

  const goToPrevPage = () => {
    setPageNumber(page => Math.max(1, page - 1));
  };

  const goToNextPage = () => {
    setPageNumber(page => Math.min(numPages, page + 1));
  };

  if (loading) {
    return (
      <div className="pdf-preview pdf-loading">
        <div className="pdf-loading-text">Loading PDF...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pdf-preview pdf-error">
        <div className="pdf-error-text">
          Failed to load PDF: {error.message}
        </div>
      </div>
    );
  }

  return (
    <div className="pdf-preview">
      <div className="pdf-document-container">
        <Document
          file={file}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading={<div className="pdf-loading-text">Loading PDF...</div>}
          error={<div className="pdf-error-text">Failed to load PDF</div>}
          options={{
            // Disable text layer and annotations for better mobile performance
            cMapUrl: `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/cmaps/`,
            cMapPacked: true,
          }}
        >
          <Page
            pageNumber={pageNumber}
            renderTextLayer={false}
            renderAnnotationLayer={false}
            className="pdf-page"
            width={Math.min(window.innerWidth - 32, 800)} // Responsive width with padding
          />
        </Document>
      </div>
      
      {numPages > 1 && (
        <div className="pdf-navigation">
          <button 
            type="button" 
            disabled={pageNumber <= 1} 
            onClick={goToPrevPage}
            className="pdf-nav-button pdf-prev"
          >
            Previous
          </button>
          <span className="pdf-page-info">
            Page {pageNumber} of {numPages}
          </span>
          <button 
            type="button" 
            disabled={pageNumber >= numPages} 
            onClick={goToNextPage}
            className="pdf-nav-button pdf-next"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default PDFPreview;