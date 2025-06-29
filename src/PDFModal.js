import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Local worker configuration
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

const PDFModal = ({ isOpen, onClose, fileUrl, filename }) => {
  
  // ✅ ALL HOOKS MUST BE AT THE TOP - BEFORE ANY CONDITIONS
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [error, setError] = useState(null);
  const [pdfHeight, setPdfHeight] = useState(null);

  // ✅ ALL useEffect HOOKS HERE TOO - BEFORE CONDITIONAL RETURNS
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen]);

  // Calculate optimal PDF height when modal opens
  useEffect(() => {
    if (isOpen) {
      const calculatePdfHeight = () => {
        // Calculate available height: viewport - modal padding - header - footer - content padding
        const viewportHeight = window.innerHeight;
        const modalVerticalPadding = 32; // 16px top + 16px bottom from modal
        const headerHeight = 80; // Approximate header height
        const footerHeight = 80; // Approximate footer height (when navigation visible)
        const contentPadding = 40; // 20px top + 20px bottom
        
        const availableHeight = viewportHeight - modalVerticalPadding - headerHeight - footerHeight - contentPadding;
        
        // Set PDF height to fit within available space (90% for some breathing room)
        setPdfHeight(Math.max(400, availableHeight * 0.9)); // Minimum 400px height
      };

      calculatePdfHeight();
      window.addEventListener('resize', calculatePdfHeight);
      return () => window.removeEventListener('resize', calculatePdfHeight);
    }
  }, [isOpen]);

  // Only render when modal is open
  if (!isOpen) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        maxWidth: '1200px',
        maxHeight: '90vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '20px',
          borderBottom: '1px solid #e5e7eb',
          borderRadius: '12px 12px 0 0'
        }}>
          <div>
            <h3 style={{
              fontWeight: '600',
              fontSize: '18px',
              color: '#111827',
              margin: 0
            }}>
              {filename}
            </h3>
            {numPages && (
              <p style={{
                fontSize: '14px',
                color: '#6b7280',
                margin: '4px 0 0 0'
              }}>
                {numPages} pages
              </p>
            )}
          </div>
          <button 
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              color: '#6b7280',
              border: 'none',
              padding: '8px',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#f3f4f6';
              e.target.style.color = '#374151';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.color = '#6b7280';
            }}
          >
            <X size={20} />
          </button>
        </div>
        {/* Content */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: '#f9fafb',
          minHeight: '0' // Ensure flex child can shrink
        }}>
          {error ? (
            <div style={{
              color: '#dc2626',
              fontSize: '16px',
              textAlign: 'center',
              padding: '40px',
              backgroundColor: '#fef2f2',
              borderRadius: '8px',
              border: '1px solid #fecaca'
            }}>
              <p style={{margin: '0 0 8px 0', fontWeight: '600'}}>Error loading PDF</p>
              <p style={{margin: 0, fontSize: '14px'}}>{error}</p>
            </div>
          ) : (
            <Document
              file={fileUrl}
              onLoadSuccess={({ numPages }) => {
                setNumPages(numPages);
                setPageNumber(1);
              }}
              onLoadError={(err) => {
                setError(err.message);
              }}
              loading={
                <div style={{
                  padding: '40px',
                  textAlign: 'center',
                  color: '#6b7280'
                }}>
                  Loading PDF...
                </div>
              }
            >
              <Page 
                pageNumber={pageNumber}
                height={pdfHeight || 600} // Scale to fit height, not width
                loading={
                  <div style={{
                    padding: '40px',
                    textAlign: 'center',
                    color: '#6b7280'
                  }}>
                    Loading page...
                  </div>
                }
                renderTextLayer={false} // Improve performance for better visual fit
                renderAnnotationLayer={false} // Improve performance
              />
            </Document>
          )}
        </div>
        
        {/* Footer with Navigation */}
        {numPages && numPages > 1 && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '16px',
            padding: '16px 20px',
            borderTop: '1px solid #e5e7eb',
            borderRadius: '0 0 12px 12px'
          }}>
            <button
              onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
              disabled={pageNumber <= 1}
              style={{
                minWidth: '40px',
                minHeight: '40px',
                backgroundColor: pageNumber <= 1 ? '#f3f4f6' : '#DC1111',
                color: pageNumber <= 1 ? '#9ca3af' : '#ffffff',
                border: 'none',
                borderRadius: '0.75rem', // var(--aui-radius)
                cursor: pageNumber <= 1 ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '8px 12px',
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                boxShadow: pageNumber <= 1 ? 'none' : '0 1px 2px 0 rgb(0 0 0 / 0.05)',
                opacity: pageNumber <= 1 ? '0.5' : '1'
              }}
              onMouseEnter={(e) => {
                if (pageNumber > 1) {
                  e.target.style.backgroundColor = '#C10E0E'; // Darker red on hover
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)';
                }
              }}
              onMouseLeave={(e) => {
                if (pageNumber > 1) {
                  e.target.style.backgroundColor = '#DC1111';
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 1px 2px 0 rgb(0 0 0 / 0.05)';
                }
              }}
              onMouseDown={(e) => {
                if (pageNumber > 1) {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 1px 2px 0 rgb(0 0 0 / 0.05)';
                }
              }}
            >
              <ChevronLeft size={16} strokeWidth={2} />
              Previous
            </button>
            
            <span style={{
              fontSize: '14px',
              color: '#374151',
              fontWeight: '500',
              fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
              minWidth: '80px',
              textAlign: 'center'
            }}>
              Page {pageNumber} of {numPages}
            </span>
            
            <button
              onClick={() => setPageNumber(Math.min(numPages, pageNumber + 1))}
              disabled={pageNumber >= numPages}
              style={{
                minWidth: '40px',
                minHeight: '40px',
                backgroundColor: pageNumber >= numPages ? '#f3f4f6' : '#DC1111',
                color: pageNumber >= numPages ? '#9ca3af' : '#ffffff',
                border: 'none',
                borderRadius: '0.75rem', // var(--aui-radius)
                cursor: pageNumber >= numPages ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '8px 12px',
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                boxShadow: pageNumber >= numPages ? 'none' : '0 1px 2px 0 rgb(0 0 0 / 0.05)',
                opacity: pageNumber >= numPages ? '0.5' : '1'
              }}
              onMouseEnter={(e) => {
                if (pageNumber < numPages) {
                  e.target.style.backgroundColor = '#C10E0E'; // Darker red on hover
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)';
                }
              }}
              onMouseLeave={(e) => {
                if (pageNumber < numPages) {
                  e.target.style.backgroundColor = '#DC1111';
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 1px 2px 0 rgb(0 0 0 / 0.05)';
                }
              }}
              onMouseDown={(e) => {
                if (pageNumber < numPages) {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 1px 2px 0 rgb(0 0 0 / 0.05)';
                }
              }}
            >
              Next
              <ChevronRight size={16} strokeWidth={2} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFModal;