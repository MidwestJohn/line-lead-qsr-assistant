import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

/**
 * 🧪 Simple PDF Test Component
 * 
 * Minimal PDF viewer to test if PDF.js works at all
 */
const SimplePDFTest = ({ fileUrl }) => {
  const [numPages, setNumPages] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  console.log('🧪 [SIMPLE-PDF-TEST] Component rendering with fileUrl:', fileUrl);

  const onDocumentLoadSuccess = ({ numPages }) => {
    console.log('🎉 [SIMPLE-PDF-TEST] PDF loaded successfully!', { numPages });
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (error) => {
    console.log('❌ [SIMPLE-PDF-TEST] PDF load error:', error);
    setError(error.message);
    setLoading(false);
  };

  const onDocumentLoadStart = () => {
    console.log('🚀 [SIMPLE-PDF-TEST] PDF loading started');
    setLoading(true);
    setError(null);
  };

  const onDocumentLoadProgress = ({ loaded, total }) => {
    const progress = total > 0 ? Math.round((loaded / total) * 100) : 0;
    console.log(`📊 [SIMPLE-PDF-TEST] Loading progress: ${progress}% (${loaded}/${total})`);
  };

  if (!fileUrl) {
    return (
      <div style={{ padding: '20px', border: '2px solid red' }}>
        <h3>🧪 Simple PDF Test</h3>
        <p>❌ No file URL provided</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', border: '2px solid blue' }}>
      <h3>🧪 Simple PDF Test</h3>
      <p><strong>File URL:</strong> {fileUrl}</p>
      <p><strong>PDF.js Version:</strong> {pdfjs.version}</p>
      <p><strong>Worker Source:</strong> {pdfjs.GlobalWorkerOptions.workerSrc}</p>
      
      {loading && <p>📋 Loading PDF...</p>}
      {error && <p style={{ color: 'red' }}>❌ Error: {error}</p>}
      {numPages && <p style={{ color: 'green' }}>✅ PDF loaded with {numPages} pages</p>}

      <div style={{ border: '1px solid gray', minHeight: '400px' }}>
        <Document
          file={fileUrl}
          onLoadStart={onDocumentLoadStart}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          onLoadProgress={onDocumentLoadProgress}
          loading={<div>📋 Loading Document...</div>}
          error={<div>❌ Document Error</div>}
        >
          {numPages && (
            <Page 
              pageNumber={1} 
              scale={0.8}
              loading={<div>📋 Loading Page...</div>}
              error={<div>❌ Page Error</div>}
            />
          )}
        </Document>
      </div>
    </div>
  );
};

export default SimplePDFTest;