import React, { useState } from 'react';
import PDFModal from './PDFModal';
import { FileText, Eye } from 'lucide-react';

const PDFModalTest = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedPDF, setSelectedPDF] = useState(null);

  const testDocuments = [
    {
      id: 1,
      filename: 'Fryer Training Manual.pdf',
      url: './test_fryer_manual.pdf',
      description: 'Complete guide for fryer operations and safety procedures'
    },
    {
      id: 2,
      filename: 'Grill Training Manual.pdf', 
      url: './test_grill_manual.pdf',
      description: 'Comprehensive grill operation and maintenance manual'
    }
  ];

  const openModal = (doc) => {
    setSelectedPDF(doc);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedPDF(null);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ 
          fontSize: '28px', 
          fontWeight: '700', 
          color: '#111827', 
          marginBottom: '8px' 
        }}>
          PDF Modal Test
        </h1>
        <p style={{ 
          fontSize: '16px', 
          color: '#6b7280', 
          marginBottom: '24px' 
        }}>
          Test the professional PDF preview modal with the documents below.
        </p>
        
        <div style={{
          padding: '16px',
          backgroundColor: '#f0f9ff',
          border: '1px solid #0ea5e9',
          borderRadius: '8px',
          marginBottom: '24px'
        }}>
          <h3 style={{ margin: '0 0 8px 0', color: '#0c4a6e', fontSize: '16px' }}>
            🎯 Test Features:
          </h3>
          <ul style={{ margin: '0', paddingLeft: '20px', color: '#0369a1' }}>
            <li>Full-screen modal with professional design</li>
            <li>Page navigation (keyboard arrows or buttons)</li>
            <li>Zoom controls (+/- keys or buttons)</li>
            <li>Download functionality</li>
            <li>Mobile-responsive layout</li>
            <li>Keyboard support (ESC to close)</li>
          </ul>
        </div>
      </div>

      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ 
          fontSize: '20px', 
          fontWeight: '600', 
          color: '#111827', 
          marginBottom: '16px' 
        }}>
          Available Documents
        </h2>
        
        <div style={{ display: 'grid', gap: '16px' }}>
          {testDocuments.map((doc) => (
            <div
              key={doc.id}
              style={{
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '20px',
                backgroundColor: 'white',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
                e.currentTarget.style.borderColor = '#DC1111';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
                e.currentTarget.style.borderColor = '#e5e7eb';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <FileText 
                  style={{ 
                    width: '24px', 
                    height: '24px', 
                    color: '#DC1111',
                    flexShrink: 0,
                    marginTop: '2px'
                  }} 
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '18px', 
                    fontWeight: '600',
                    color: '#111827'
                  }}>
                    {doc.filename}
                  </h3>
                  <p style={{ 
                    margin: '0 0 16px 0', 
                    fontSize: '14px', 
                    color: '#6b7280',
                    lineHeight: '1.5'
                  }}>
                    {doc.description}
                  </p>
                  <button
                    onClick={() => openModal(doc)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 16px',
                      backgroundColor: '#DC1111',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s ease',
                      minHeight: '44px'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = '#b91c1c';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = '#DC1111';
                    }}
                  >
                    <Eye style={{ width: '16px', height: '16px' }} />
                    Preview PDF
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{
        padding: '20px',
        backgroundColor: '#f9fafb',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        marginBottom: '24px'
      }}>
        <h3 style={{ margin: '0 0 12px 0', color: '#374151', fontSize: '16px' }}>
          🎮 Keyboard Controls:
        </h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '12px',
          fontSize: '14px',
          color: '#6b7280'
        }}>
          <div><kbd style={kbdStyle}>←</kbd> <kbd style={kbdStyle}>→</kbd> Navigate pages</div>
          <div><kbd style={kbdStyle}>+</kbd> <kbd style={kbdStyle}>-</kbd> Zoom in/out</div>
          <div><kbd style={kbdStyle}>ESC</kbd> Close modal</div>
        </div>
      </div>

      {/* PDF Modal */}
      <PDFModal
        fileUrl={selectedPDF?.url}
        filename={selectedPDF?.filename}
        isOpen={modalOpen}
        onClose={closeModal}
      />
    </div>
  );
};

const kbdStyle = {
  padding: '2px 6px',
  backgroundColor: '#e5e7eb',
  border: '1px solid #d1d5db',
  borderRadius: '3px',
  fontFamily: 'monospace',
  fontSize: '12px',
  marginRight: '4px'
};

export default PDFModalTest;