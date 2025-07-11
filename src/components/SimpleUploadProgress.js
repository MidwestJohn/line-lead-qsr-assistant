import React, { useState, useEffect } from 'react';
import './UploadProgress.css';

const SimpleUploadProgress = ({ processId, onComplete }) => {
  const [progress, setProgress] = useState({
    stage: 'initializing',
    progress_percent: 0,
    message: 'Starting upload processing...',
    entities_found: 0,
    relationships_found: 0
  });
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    console.log('SimpleUploadProgress mounted with processId:', processId);
    
    if (!processId) {
      console.warn('No processId provided to SimpleUploadProgress');
      return;
    }

    let isActive = true;
    let pollingTimer = null;

    const pollProgress = async () => {
      if (!isActive || !processId || isCompleted) return;
      
      try {
        console.log(`📊 Polling progress for: ${processId}`);
        const response = await fetch(`/progress/${processId}`);
        
        if (response.ok) {
          const data = await response.json();
          console.log('📊 Simple progress update:', data);
          
          if (data.success && data.progress) {
            // Update progress state
            setProgress(prevProgress => ({
              ...prevProgress,
              stage: data.progress.stage || prevProgress.stage,
              progress_percent: data.progress.progress_percent || prevProgress.progress_percent,
              message: data.progress.message || prevProgress.message,
              entities_found: data.progress.entities_found || prevProgress.entities_found,
              relationships_found: data.progress.relationships_found || prevProgress.relationships_found
            }));

            // Check if complete
            if (data.progress.stage === 'verification' && data.progress.progress_percent >= 100) {
              console.log('🎉 Processing complete!');
              setIsCompleted(true);
              if (onComplete) {
                onComplete({
                  entities: data.progress.entities_found || 0,
                  relationships: data.progress.relationships_found || 0
                });
              }
              return; // Stop polling
            }
          } else if (data.error) {
            console.warn('Progress polling error:', data.error);
            setProgress(prev => ({
              ...prev,
              stage: 'error',
              message: `Error: ${data.error}`
            }));
            setIsCompleted(true);
            return;
          }
        } else {
          console.warn('Progress polling failed:', response.status);
        }
      } catch (error) {
        console.warn('Progress polling request failed:', error);
        setProgress(prev => ({
          ...prev,
          stage: 'error',
          message: 'Failed to get progress updates'
        }));
        setIsCompleted(true);
        return;
      }
      
      // Continue polling if still active and not complete
      if (isActive && !isCompleted) {
        pollingTimer = setTimeout(pollProgress, 2000); // Poll every 2 seconds
      }
    };

    // Start polling immediately
    pollProgress();

    // Cleanup function
    return () => {
      console.log('🧹 Cleaning up progress polling');
      isActive = false;
      
      if (pollingTimer) {
        clearTimeout(pollingTimer);
      }
    };
  }, [processId, onComplete, isCompleted]);

  const getStageDisplay = (stage) => {
    const stages = {
      'upload_complete': 'Upload Complete',
      'text_extraction': 'Extracting Text',
      'entity_extraction': 'Finding QSR Elements',
      'relationship_generation': 'Building Relationships',
      'verification': 'Finalizing',
      'error': 'Error'
    };
    return stages[stage] || stage;
  };

  const getProgressColor = () => {
    if (progress.stage === 'error') return '#ff4444';
    if (progress.progress_percent >= 100) return '#4CAF50';
    return '#2196F3';
  };

  return (
    <div className="file-upload-area uploading progress-mode">
      <div className="upload-progress-header">
        <h3>Processing Document</h3>
        <div className="progress-percentage">{Math.round(progress.progress_percent)}%</div>
      </div>

      <div className="progress-bar-wrapper">
        <div className="progress-bar-track">
          <div 
            className="progress-bar-fill"
            style={{
              width: `${progress.progress_percent}%`,
              backgroundColor: getProgressColor()
            }}
          />
        </div>
      </div>

      <div className="progress-stage-info">
        <div className="stage-title">
          <strong>Stage:</strong> {getStageDisplay(progress.stage)}
        </div>
        <div className="stage-description">
          {progress.message}
        </div>
      </div>

      <div className="progress-metrics">
        <div className="metric-item">
          <span className="metric-icon">📄</span>
          <span className="metric-label">Entities</span>
          <span className="metric-value">{progress.entities_found}</span>
        </div>
        <div className="metric-item">
          <span className="metric-icon">🔗</span>
          <span className="metric-label">Relationships</span>
          <span className="metric-value">{progress.relationships_found}</span>
        </div>
      </div>

      <div className="connection-info">
        <span className="connection-badge">HTTP Polling ✓ Reliable</span>
      </div>
    </div>
  );
};

export default SimpleUploadProgress;