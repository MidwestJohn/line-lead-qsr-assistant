import React, { useState, useEffect } from 'react';
import PDFPreview from './PDFPreview';
import { testPDFSetup } from './test-pdf-setup';

const PDFTest = () => {
  const [selectedPDF, setSelectedPDF] = useState('./test_fryer_manual.pdf');
  const [loadStatus, setLoadStatus] = useState('');
  const [setupStatus, setSetupStatus] = useState('');

  useEffect(() => {
    // Test PDF setup on component mount
    const setupOk = testPDFSetup();
    setSetupStatus(setupOk ? '✅ PDF.js setup verified' : '❌ PDF.js setup failed');
  }, []);

  const testPDFs = [
    { name: 'Fryer Manual', path: './test_fryer_manual.pdf' },
    { name: 'Grill Manual', path: './test_grill_manual.pdf' }
  ];

  const handleLoadSuccess = ({ numPages }) => {
    setLoadStatus(`PDF loaded successfully! ${numPages} pages found.`);
    console.log('PDF Load Success:', { numPages });
  };

  const handleLoadError = (error) => {
    setLoadStatus(`PDF load failed: ${error.message}`);
    console.error('PDF Load Error:', error);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>PDF Preview Test</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="pdf-select" style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
          Select PDF to test:
        </label>
        <select 
          id="pdf-select"
          value={selectedPDF} 
          onChange={(e) => {
            setSelectedPDF(e.target.value);
            setLoadStatus('');
          }}
          style={{ 
            padding: '8px 12px', 
            borderRadius: '4px', 
            border: '1px solid #ddd',
            fontSize: '14px',
            minWidth: '200px'
          }}
        >
          {testPDFs.map((pdf) => (
            <option key={pdf.path} value={pdf.path}>
              {pdf.name}
            </option>
          ))}
        </select>
      </div>

      {setupStatus && (
        <div 
          style={{ 
            padding: '8px 12px', 
            borderRadius: '4px', 
            marginBottom: '12px',
            backgroundColor: setupStatus.includes('✅') ? '#f0fdf4' : '#fef2f2',
            border: `1px solid ${setupStatus.includes('✅') ? '#bbf7d0' : '#fecaca'}`,
            color: setupStatus.includes('✅') ? '#16a34a' : '#dc2626',
            fontSize: '14px'
          }}
        >
          {setupStatus}
        </div>
      )}

      {loadStatus && (
        <div 
          style={{ 
            padding: '12px', 
            borderRadius: '4px', 
            marginBottom: '20px',
            backgroundColor: loadStatus.includes('failed') ? '#fef2f2' : '#f0fdf4',
            border: `1px solid ${loadStatus.includes('failed') ? '#fecaca' : '#bbf7d0'}`,
            color: loadStatus.includes('failed') ? '#dc2626' : '#16a34a'
          }}
        >
          {loadStatus}
        </div>
      )}

      <div style={{ border: '1px solid #e0e0e0', borderRadius: '8px', overflow: 'hidden' }}>
        <PDFPreview 
          file={selectedPDF}
          onLoadSuccess={handleLoadSuccess}
          onLoadError={handleLoadError}
        />
      </div>

      <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
        <p><strong>Test Instructions:</strong></p>
        <ul>
          <li>PDF should load and display the first page</li>
          <li>Navigation buttons should appear if the PDF has multiple pages</li>
          <li>PDF should be responsive and fit within the container</li>
          <li>Loading state should show briefly while PDF loads</li>
          <li>Check browser console for any errors</li>
        </ul>
      </div>
    </div>
  );
};

export default PDFTest;