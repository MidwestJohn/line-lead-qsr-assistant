// Complete Media Integration Example
// This shows how all Phase 1-4 components work together

import React, { useState } from 'react';
import { 
  VideoPlayer, 
  EnhancedImage, 
  AudioPlayer, 
  AudioStepCard, 
  EnhancedStepCard,
  MediaCitation 
} from './components';

const CompleteMediaIntegration = () => {
  const [activeStep, setActiveStep] = useState(0);

  // Complete training procedure with all media types
  const trainingSteps = [
    {
      id: 1,
      title: 'Equipment Overview',
      description: 'Familiarize yourself with the fryer components',
      media: [
        {
          documentId: 'cefc0e1b-dcb6-41ca-bcbd-b787bacc8d0f',
          type: 'image',
          title: 'Fryer Control Panel Diagram'
        }
      ],
      instructions: [
        'Locate the temperature control dial',
        'Identify the timer display',
        'Find the power indicator lights',
        'Check the oil level indicator'
      ],
      estimatedTime: '3 minutes'
    },
    {
      id: 2,
      title: 'Safety Training Video',
      description: 'Watch the complete safety procedures',
      media: [
        {
          documentId: 'video-training-id',
          type: 'video',
          title: 'Fryer Safety Training Video'
        }
      ],
      instructions: [
        'Watch the entire safety video',
        'Pay attention to proper PPE usage',
        'Note emergency procedures',
        'Complete the safety checklist'
      ],
      estimatedTime: '8 minutes'
    },
    {
      id: 3,
      title: 'Audio Narration',
      description: 'Listen to detailed operating procedures',
      media: [
        {
          documentId: 'audio-training-id',
          type: 'audio',
          title: 'Fryer Operation Narration',
          transcript: 'Welcome to fryer operation training. This audio guide will walk you through each step of proper fryer operation...'
        }
      ],
      instructions: [
        'Listen to the complete narration',
        'Follow along with the steps',
        'Use transcript if kitchen is noisy',
        'Practice each procedure'
      ],
      estimatedTime: '5 minutes'
    }
  ];

  const renderStepContent = (step) => {
    const mediaItem = step.media[0];
    
    switch (mediaItem.type) {
      case 'image':
        return (
          <EnhancedStepCard
            step={step}
            stepNumber={step.id}
            isActive={activeStep === step.id - 1}
          />
        );
      
      case 'video':
        return (
          <div className="video-step">
            <h3>{step.title}</h3>
            <p>{step.description}</p>
            <VideoPlayer
              documentId={mediaItem.documentId}
              title={mediaItem.title}
            />
            <div className="instructions">
              <h4>Instructions:</h4>
              <ol>
                {step.instructions.map((instruction, index) => (
                  <li key={index}>{instruction}</li>
                ))}
              </ol>
            </div>
            <MediaCitation 
              documentId={mediaItem.documentId}
              mediaType="video"
            />
          </div>
        );
      
      case 'audio':
        return (
          <AudioStepCard
            step={step}
            stepNumber={step.id}
            isActive={activeStep === step.id - 1}
          />
        );
      
      default:
        return (
          <div className="document-step">
            <h3>{step.title}</h3>
            <p>{step.description}</p>
            <MediaCitation 
              documentId={mediaItem.documentId}
              mediaType="document"
            />
          </div>
        );
    }
  };

  return (
    <div className="complete-training-system">
      <div className="training-header">
        <h1>🍳 Complete QSR Training System</h1>
        <p>All media types working together for comprehensive training</p>
      </div>

      {/* Progress Indicator */}
      <div className="training-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${((activeStep + 1) / trainingSteps.length) * 100}%` }}
          />
        </div>
        <span className="progress-text">
          Step {activeStep + 1} of {trainingSteps.length}
        </span>
      </div>

      {/* Step Navigation */}
      <div className="step-navigation">
        {trainingSteps.map((step, index) => (
          <button
            key={step.id}
            className={`step-button ${activeStep === index ? 'active' : ''}`}
            onClick={() => setActiveStep(index)}
          >
            <div className="step-number">{step.id}</div>
            <div className="step-info">
              <span className="step-title">{step.title}</span>
              <span className="step-type">
                {step.media[0].type === 'image' ? '🖼️' :
                 step.media[0].type === 'video' ? '🎥' :
                 step.media[0].type === 'audio' ? '🎵' : '📄'}
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Current Step Content */}
      <div className="step-content">
        {renderStepContent(trainingSteps[activeStep])}
      </div>

      {/* Navigation Controls */}
      <div className="navigation-controls">
        <button
          onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
          disabled={activeStep === 0}
          className="nav-button"
        >
          ← Previous
        </button>
        <button
          onClick={() => setActiveStep(Math.min(trainingSteps.length - 1, activeStep + 1))}
          disabled={activeStep === trainingSteps.length - 1}
          className="nav-button"
        >
          Next →
        </button>
      </div>

      {/* Media Summary */}
      <div className="media-summary">
        <h3>📊 Complete Media System</h3>
        <div className="media-types">
          <div className="media-type">
            <span className="icon">📄</span>
            <span>Documents</span>
            <small>PDF, DOCX, TXT</small>
          </div>
          <div className="media-type">
            <span className="icon">🖼️</span>
            <span>Images</span>
            <small>PNG, JPG, with zoom/pan</small>
          </div>
          <div className="media-type">
            <span className="icon">🎥</span>
            <span>Videos</span>
            <small>MP4, with custom controls</small>
          </div>
          <div className="media-type">
            <span className="icon">🎵</span>
            <span>Audio</span>
            <small>MP3, WAV, with transcript</small>
          </div>
        </div>
      </div>

      {/* Kitchen Features */}
      <div className="kitchen-features">
        <h3>🍳 Kitchen-Optimized Features</h3>
        <div className="features-grid">
          <div className="feature">
            <strong>Touch-Friendly:</strong> 44px minimum tap targets
          </div>
          <div className="feature">
            <strong>Hands-Free:</strong> Keyboard shortcuts for all controls
          </div>
          <div className="feature">
            <strong>High Contrast:</strong> Readable in bright environments
          </div>
          <div className="feature">
            <strong>Noise Tolerant:</strong> Visual feedback and transcripts
          </div>
          <div className="feature">
            <strong>Glove Compatible:</strong> Large controls and gestures
          </div>
          <div className="feature">
            <strong>Error Recovery:</strong> Clear error states and retry
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompleteMediaIntegration;

/* 
USAGE EXAMPLE:

1. Import all components:
   import { VideoPlayer, EnhancedImage, AudioPlayer, AudioStepCard, EnhancedStepCard, MediaCitation } from './components';

2. Use individual components:
   - <VideoPlayer documentId="video-id" title="Training Video" />
   - <EnhancedImage documentId="image-id" equipmentType="fryer" showZoom={true} />
   - <AudioPlayer documentId="audio-id" title="Training Audio" showTranscript={true} />
   - <AudioStepCard step={stepData} stepNumber={1} isActive={true} />
   - <EnhancedStepCard step={stepData} stepNumber={1} />
   - <MediaCitation documentId="doc-id" mediaType="video" />

3. Backend API endpoints:
   - GET /api/documents/{id}/source - Get media file
   - GET /api/documents/{id}/metadata - Get file metadata
   - GET /api/documents/source/health - Check service health

4. Keyboard shortcuts:
   - Space: Play/Pause (audio/video)
   - ←/→: Skip 10 seconds
   - +/-: Zoom in/out (images)
   - M: Mute toggle
   - T: Transcript toggle
   - F: Fullscreen
   - R: Rotate (images)

🎯 ALL PHASES COMPLETE!
✅ Phase 1: Document Source Integration
✅ Phase 2: Video Player Implementation  
✅ Phase 3: Image Rendering Enhancement
✅ Phase 4: Audio Streaming Implementation

Your QSR training system now supports all major media formats
with kitchen-optimized controls and mobile-first design.
*/