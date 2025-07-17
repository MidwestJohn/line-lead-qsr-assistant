import React, { useState } from 'react';
import { EnhancedImage, EnhancedStepCard, MediaCitation } from '../components';

const Phase3IntegrationTest = () => {
  const [testStatus, setTestStatus] = useState({
    imageLoading: 'pending',
    zoomFunction: 'pending',
    touchControls: 'pending',
    stepCard: 'pending',
    citation: 'pending'
  });

  const testDocumentId = 'cefc0e1b-dcb6-41ca-bcbd-b787bacc8d0f'; // PNG image
  
  const mockStep = {
    id: 1,
    title: 'Check Equipment Diagram',
    description: 'Review the oven components and controls',
    media: [
      {
        documentId: testDocumentId,
        type: 'image',
        title: 'Baxter Oven Controls'
      }
    ],
    instructions: [
      'Locate the temperature control dial',
      'Identify the timer settings',
      'Check the power indicator light'
    ]
  };

  const updateTestStatus = (test, status) => {
    setTestStatus(prev => ({
      ...prev,
      [test]: status
    }));
  };

  return (
    <div style={{ 
      padding: '20px', 
      maxWidth: '1200px', 
      margin: '0 auto',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '30px',
        padding: '20px',
        background: '#f8f9fa',
        borderRadius: '8px'
      }}>
        <h1 style={{ color: '#d32f2f', marginBottom: '10px' }}>
          Phase 3 Integration Test
        </h1>
        <p style={{ color: '#666', marginBottom: '20px' }}>
          Testing EnhancedImage, EnhancedStepCard, and MediaCitation components
        </p>
        
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {Object.entries(testStatus).map(([test, status]) => (
            <div 
              key={test}
              style={{
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '14px',
                fontWeight: '500',
                background: status === 'pending' ? '#fff3cd' : 
                           status === 'pass' ? '#d4edda' : '#f8d7da',
                color: status === 'pending' ? '#856404' : 
                       status === 'pass' ? '#155724' : '#721c24',
                border: `1px solid ${status === 'pending' ? '#ffeaa7' : 
                                   status === 'pass' ? '#c3e6cb' : '#f5c6cb'}`
              }}
            >
              {test}: {status}
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gap: '30px' }}>
        {/* Test 1: EnhancedImage Component */}
        <div style={{ 
          background: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Test 1: EnhancedImage Component
          </h3>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Equipment diagram with zoom/pan controls
          </p>
          
          <div style={{ 
            border: '2px solid #e0e0e0', 
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <EnhancedImage
              documentId={testDocumentId}
              equipmentType="oven"
              showZoom={true}
              maxZoom={4}
              onLoad={() => updateTestStatus('imageLoading', 'pass')}
              onError={() => updateTestStatus('imageLoading', 'fail')}
              style={{ width: '100%', height: '400px' }}
            />
          </div>
          
          <div style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
            <p>✓ Try zooming with mouse wheel or +/- keys</p>
            <p>✓ Pan by dragging when zoomed in</p>
            <p>✓ Press 'R' to rotate, 'F' for fullscreen</p>
          </div>
        </div>

        {/* Test 2: EnhancedStepCard Component */}
        <div style={{ 
          background: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Test 2: EnhancedStepCard Component
          </h3>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Step-by-step procedure with integrated image
          </p>
          
          <EnhancedStepCard
            step={mockStep}
            stepNumber={1}
            onImageLoad={() => updateTestStatus('stepCard', 'pass')}
            onImageError={() => updateTestStatus('stepCard', 'fail')}
          />
          
          <div style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
            <p>✓ Image should load within the step card</p>
            <p>✓ Instructions should be clearly visible</p>
            <p>✓ Touch-friendly interface</p>
          </div>
        </div>

        {/* Test 3: MediaCitation Component */}
        <div style={{ 
          background: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Test 3: MediaCitation Component
          </h3>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Citation display for media references
          </p>
          
          <MediaCitation
            documentId={testDocumentId}
            mediaType="image"
            onLoad={() => updateTestStatus('citation', 'pass')}
            onError={() => updateTestStatus('citation', 'fail')}
          />
          
          <div style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
            <p>✓ Citation should show document metadata</p>
            <p>✓ Link should be clickable</p>
            <p>✓ Proper formatting for image type</p>
          </div>
        </div>

        {/* Test Results Summary */}
        <div style={{ 
          background: '#f8f9fa', 
          padding: '20px', 
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Integration Test Results
          </h3>
          <div style={{ fontSize: '18px', fontWeight: '500' }}>
            {Object.values(testStatus).filter(s => s === 'pass').length} / {Object.keys(testStatus).length} Tests Passing
          </div>
          
          <div style={{ marginTop: '15px', fontSize: '14px', color: '#666' }}>
            <p>Backend API: {window.location.origin.replace('3000', '8000')}</p>
            <p>Test Document: {testDocumentId}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Phase3IntegrationTest;