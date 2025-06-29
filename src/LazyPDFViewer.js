import React, { Suspense, lazy } from 'react';
import './LazyPDFViewer.css';

// Lazy load the PDF component for better performance
const PDFViewerComponent = lazy(() => 
  import('./PDFViewerComponent').then(module => ({
    default: module.PDFViewerComponent
  }))
);

const PDFLoadingFallback = () => (
  <div className="pdf-loading-fallback">
    <div className="pdf-loading-spinner">
      <div className="spinner-ring"></div>
    </div>
    <div className="pdf-loading-text">
      <h3>Loading PDF Viewer...</h3>
      <p>Preparing document preview</p>
    </div>
  </div>
);

const LazyPDFViewer = ({ 
  fileUrl, 
  filename, 
  pageNumber, 
  scale, 
  onLoadSuccess, 
  onLoadError 
}) => {
  console.log('🔍 [LAZY-PDF] LazyPDFViewer rendering with props:', {
    fileUrl,
    filename,
    pageNumber,
    scale,
    onLoadSuccess: !!onLoadSuccess,
    onLoadError: !!onLoadError
  });

  return (
    <div className="lazy-pdf-viewer">
      <Suspense fallback={
        (() => {
          console.log('📋 [LAZY-PDF] Showing loading fallback while PDF component loads');
          return <PDFLoadingFallback />;
        })()
      }>
        {(() => {
          console.log('📄 [LAZY-PDF] About to render PDFViewerComponent');
          return (
            <PDFViewerComponent
              fileUrl={fileUrl}
              filename={filename}
              pageNumber={pageNumber}
              scale={scale}
              onLoadSuccess={onLoadSuccess}
              onLoadError={onLoadError}
            />
          );
        })()}
      </Suspense>
    </div>
  );
};

export default LazyPDFViewer;