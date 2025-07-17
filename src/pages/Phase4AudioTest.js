import React, { useState, useEffect } from 'react';
import { AudioPlayer, AudioStepCard, MediaCitation } from '../components';

const Phase4AudioTest = () => {
  const [testStatus, setTestStatus] = useState({
    audioPlayer: 'pending',
    audioStepCard: 'pending',
    audioControls: 'pending',
    keyboardShortcuts: 'pending',
    transcriptDisplay: 'pending'
  });

  const [testAudioId, setTestAudioId] = useState(null);
  const [availableDocuments, setAvailableDocuments] = useState([]);

  // Mock step data for AudioStepCard
  const mockAudioStep = {
    id: 1,
    title: 'Fryer Safety Training',
    description: 'Learn proper fryer operation and safety procedures',
    media: [
      {
        documentId: testAudioId,
        type: 'audio',
        title: 'Fryer Safety Narration',
        transcript: 'Welcome to fryer safety training. First, always ensure the fryer is at the correct temperature before adding food. Check the oil level and quality before each use. Never leave food unattended in the fryer as it can quickly burn and create a fire hazard...'
      }
    ],
    instructions: [
      'Put on heat-resistant gloves and apron',
      'Check oil temperature (350°F for most items)',
      'Lower food slowly into oil to prevent splashing',
      'Set timer according to cooking chart',
      'Remove food when golden brown and crispy'
    ],
    estimatedTime: '5 minutes'
  };

  // Fetch available documents to find audio files
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/documents');
        const data = await response.json();
        setAvailableDocuments(data.documents || []);
        
        // Try to find an audio file for testing
        const audioDoc = data.documents?.find(doc => 
          doc.name.includes('.mp3') || 
          doc.name.includes('.wav') || 
          doc.name.includes('.m4a') ||
          doc.name.includes('audio')
        );
        
        if (audioDoc) {
          setTestAudioId(audioDoc.id);
        } else {
          // Use a known image ID as fallback for testing UI
          setTestAudioId('cefc0e1b-dcb6-41ca-bcbd-b787bacc8d0f');
        }
      } catch (error) {
        console.error('Error fetching documents:', error);
        // Use fallback ID
        setTestAudioId('cefc0e1b-dcb6-41ca-bcbd-b787bacc8d0f');
      }
    };

    fetchDocuments();
  }, []);

  const updateTestStatus = (test, status) => {
    setTestStatus(prev => ({
      ...prev,
      [test]: status
    }));
  };

  const handleAudioLoad = () => {
    updateTestStatus('audioPlayer', 'pass');
  };

  const handleAudioError = (error) => {
    updateTestStatus('audioPlayer', 'fail');
    console.error('Audio test error:', error);
  };

  const handleAudioProgress = (currentTime, duration) => {
    if (duration > 0) {
      updateTestStatus('audioControls', 'pass');
    }
  };

  const handleStepCardAudioStart = () => {
    updateTestStatus('audioStepCard', 'pass');
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
          Phase 4: Audio Streaming Test
        </h1>
        <p style={{ color: '#666', marginBottom: '20px' }}>
          Testing AudioPlayer, AudioStepCard, and audio streaming capabilities
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
              {test.replace(/([A-Z])/g, ' $1')}: {status}
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gap: '30px' }}>
        {/* Test 1: AudioPlayer Component */}
        <div style={{ 
          background: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Test 1: AudioPlayer Component
          </h3>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Standalone audio player with full controls
          </p>
          
          <div style={{ marginBottom: '20px' }}>
            <AudioPlayer
              documentId={testAudioId}
              title="Fryer Safety Training"
              transcript="Welcome to fryer safety training. This comprehensive guide will walk you through proper fryer operation, safety procedures, and maintenance requirements. Always ensure proper ventilation and keep fire extinguisher nearby."
              showTranscript={false}
              onLoad={handleAudioLoad}
              onError={handleAudioError}
              onTimeUpdate={handleAudioProgress}
            />
          </div>
          
          <div style={{ fontSize: '14px', color: '#666' }}>
            <p>✓ Space: Play/Pause • ←/→: Skip 10s • M: Mute • T: Transcript</p>
            <p>✓ Volume control and progress bar</p>
            <p>✓ Keyboard shortcuts for hands-free operation</p>
          </div>
        </div>

        {/* Test 2: AudioStepCard Component */}
        <div style={{ 
          background: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Test 2: AudioStepCard Component
          </h3>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Step-by-step procedure with integrated audio
          </p>
          
          <AudioStepCard
            step={mockAudioStep}
            stepNumber={1}
            isActive={true}
            onAudioStart={handleStepCardAudioStart}
            onAudioProgress={handleAudioProgress}
          />
          
          <div style={{ fontSize: '14px', color: '#666' }}>
            <p>✓ Expandable/collapsible audio player</p>
            <p>✓ Compact controls when collapsed</p>
            <p>✓ Progress indicator in step header</p>
          </div>
        </div>

        {/* Test 3: Audio Citation */}
        <div style={{ 
          background: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Test 3: Audio Citation
          </h3>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Citation display for audio references
          </p>
          
          <MediaCitation
            documentId={testAudioId}
            mediaType="audio"
            onLoad={() => updateTestStatus('transcriptDisplay', 'pass')}
            onError={() => updateTestStatus('transcriptDisplay', 'fail')}
          />
          
          <div style={{ fontSize: '14px', color: '#666' }}>
            <p>✓ Audio file metadata display</p>
            <p>✓ Proper audio icon and formatting</p>
            <p>✓ Clickable citation link</p>
          </div>
        </div>

        {/* Test 4: Available Documents */}
        <div style={{ 
          background: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#d32f2f', marginBottom: '15px' }}>
            Test 4: Available Documents
          </h3>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Current document library ({availableDocuments.length} documents)
          </p>
          
          <div style={{ 
            maxHeight: '300px', 
            overflow: 'auto',
            border: '1px solid #e0e0e0',
            borderRadius: '4px',
            padding: '15px'
          }}>
            {availableDocuments.length > 0 ? (
              availableDocuments.map(doc => (
                <div key={doc.id} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}>
                  <div>
                    <strong>{doc.name}</strong>
                    <br />
                    <small style={{ color: '#666' }}>
                      {doc.metadata?.equipment_type || 'general'} • {doc.metadata?.file_size || 'unknown size'}
                    </small>
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {doc.id === testAudioId ? '← Testing with this' : ''}
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: '#666' }}>No documents available</p>
            )}
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
            Phase 4 Test Results
          </h3>
          <div style={{ fontSize: '18px', fontWeight: '500', marginBottom: '15px' }}>
            {Object.values(testStatus).filter(s => s === 'pass').length} / {Object.keys(testStatus).length} Tests Passing
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div>
              <h4 style={{ color: '#333', marginBottom: '10px' }}>Audio Features</h4>
              <ul style={{ textAlign: 'left', fontSize: '14px', color: '#666' }}>
                <li>Play/Pause controls</li>
                <li>Skip forward/backward</li>
                <li>Volume control</li>
                <li>Progress bar</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{ color: '#333', marginBottom: '10px' }}>Keyboard Shortcuts</h4>
              <ul style={{ textAlign: 'left', fontSize: '14px', color: '#666' }}>
                <li>Space: Play/Pause</li>
                <li>←/→: Skip 10 seconds</li>
                <li>M: Mute toggle</li>
                <li>T: Transcript toggle</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{ color: '#333', marginBottom: '10px' }}>Mobile Optimized</h4>
              <ul style={{ textAlign: 'left', fontSize: '14px', color: '#666' }}>
                <li>Touch-friendly controls</li>
                <li>Large tap targets</li>
                <li>Responsive design</li>
                <li>Kitchen-friendly UI</li>
              </ul>
            </div>
          </div>
          
          <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
            <p>Backend API: {window.location.origin.replace('3000', '8000')}</p>
            <p>Test Document: {testAudioId}</p>
            <p>Available Documents: {availableDocuments.length}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Phase4AudioTest;