import React, { useState } from 'react';
import PDFPreview from './PDFPreview';

/**
 * Example integration showing how to use PDFPreview component
 * in different contexts within the Line Lead app
 */

// Example 1: PDF Modal/Overlay
export const PDFModal = ({ isOpen, onClose, pdfUrl, title }) => {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '900px',
        maxHeight: '90vh',
        overflow: 'hidden',
        position: 'relative'
      }}>
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h3 style={{ margin: 0, fontSize: '18px' }}>{title}</h3>
          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ×
          </button>
        </div>
        <div style={{ height: 'calc(90vh - 80px)', overflow: 'auto' }}>
          <PDFPreview 
            file={pdfUrl}
            onLoadSuccess={({ numPages }) => {
              console.log(`PDF "${title}" loaded with ${numPages} pages`);
            }}
            onLoadError={(error) => {
              console.error(`Failed to load PDF "${title}":`, error);
            }}
          />
        </div>
      </div>
    </div>
  );
};

// Example 2: Inline PDF Preview (for document list)
export const InlinePDFPreview = ({ document, maxHeight = '400px' }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!isExpanded) {
    return (
      <div style={{
        padding: '12px',
        border: '1px solid #e0e0e0',
        borderRadius: '4px',
        backgroundColor: '#f9f9f9',
        margin: '8px 0'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>
            📄 {document.name} ({document.pages} pages)
          </span>
          <button 
            onClick={() => setIsExpanded(true)}
            style={{
              padding: '4px 8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: 'white',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Preview
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      border: '1px solid #e0e0e0',
      borderRadius: '8px',
      overflow: 'hidden',
      margin: '8px 0'
    }}>
      <div style={{
        padding: '12px',
        backgroundColor: '#f5f5f5',
        borderBottom: '1px solid #e0e0e0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{ fontSize: '14px', fontWeight: '500' }}>
          📄 {document.name}
        </span>
        <button 
          onClick={() => setIsExpanded(false)}
          style={{
            padding: '4px 8px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            backgroundColor: 'white',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Collapse
        </button>
      </div>
      <div style={{ maxHeight, overflow: 'auto' }}>
        <PDFPreview 
          file={document.url}
          onLoadSuccess={({ numPages }) => {
            console.log(`Inline preview loaded: ${document.name} (${numPages} pages)`);
          }}
          onLoadError={(error) => {
            console.error(`Inline preview failed for ${document.name}:`, error);
          }}
        />
      </div>
    </div>
  );
};

// Example 3: Chat Message PDF Attachment
export const ChatPDFAttachment = ({ attachment, isCompact = false }) => {
  const [showPreview, setShowPreview] = useState(false);

  return (
    <div style={{
      border: '1px solid #e0e0e0',
      borderRadius: '8px',
      overflow: 'hidden',
      margin: '8px 0',
      maxWidth: isCompact ? '300px' : '100%'
    }}>
      <div style={{
        padding: '8px 12px',
        backgroundColor: '#f8f9fa',
        borderBottom: showPreview ? '1px solid #e0e0e0' : 'none',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '16px' }}>📄</span>
          <div>
            <div style={{ fontSize: '13px', fontWeight: '500', color: '#333' }}>
              {attachment.name}
            </div>
            <div style={{ fontSize: '11px', color: '#666' }}>
              {attachment.size} • {attachment.pages} pages
            </div>
          </div>
        </div>
        <button 
          onClick={() => setShowPreview(!showPreview)}
          style={{
            padding: '4px 8px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            backgroundColor: 'white',
            cursor: 'pointer',
            fontSize: '11px'
          }}
        >
          {showPreview ? 'Hide' : 'View'}
        </button>
      </div>
      {showPreview && (
        <div style={{ 
          maxHeight: isCompact ? '200px' : '400px', 
          overflow: 'auto' 
        }}>
          <PDFPreview 
            file={attachment.url}
            onLoadSuccess={({ numPages }) => {
              console.log(`Chat attachment loaded: ${attachment.name}`);
            }}
            onLoadError={(error) => {
              console.error(`Chat attachment failed: ${attachment.name}`, error);
            }}
          />
        </div>
      )}
    </div>
  );
};

// Example 4: Document Library Integration
export const DocumentLibraryWithPreview = ({ documents }) => {
  const [selectedDocument, setSelectedDocument] = useState(null);

  return (
    <div style={{ display: 'flex', height: '600px', border: '1px solid #e0e0e0', borderRadius: '8px' }}>
      {/* Document List */}
      <div style={{ 
        width: '300px', 
        borderRight: '1px solid #e0e0e0', 
        padding: '16px',
        overflowY: 'auto'
      }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>Documents</h3>
        {documents.map((doc) => (
          <div 
            key={doc.id}
            onClick={() => setSelectedDocument(doc)}
            style={{
              padding: '12px',
              border: '1px solid #e0e0e0',
              borderRadius: '4px',
              margin: '8px 0',
              cursor: 'pointer',
              backgroundColor: selectedDocument?.id === doc.id ? '#e3f2fd' : 'white',
              borderColor: selectedDocument?.id === doc.id ? '#2196f3' : '#e0e0e0'
            }}
          >
            <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
              {doc.name}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {doc.pages} pages • {doc.uploadDate}
            </div>
          </div>
        ))}
      </div>

      {/* PDF Preview */}
      <div style={{ flex: 1, padding: '16px' }}>
        {selectedDocument ? (
          <div>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>
              {selectedDocument.name}
            </h3>
            <div style={{ height: 'calc(100% - 40px)', overflow: 'auto' }}>
              <PDFPreview 
                file={selectedDocument.url}
                onLoadSuccess={({ numPages }) => {
                  console.log(`Library preview: ${selectedDocument.name} (${numPages} pages)`);
                }}
                onLoadError={(error) => {
                  console.error(`Library preview failed: ${selectedDocument.name}`, error);
                }}
              />
            </div>
          </div>
        ) : (
          <div style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#666'
          }}>
            Select a document to preview
          </div>
        )}
      </div>
    </div>
  );
};

export default {
  PDFModal,
  InlinePDFPreview,
  ChatPDFAttachment,
  DocumentLibraryWithPreview
};