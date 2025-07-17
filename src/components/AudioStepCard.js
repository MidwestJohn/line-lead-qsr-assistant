import React, { useState, useCallback, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, FileText, Headphones } from 'lucide-react';
import AudioPlayer from './AudioPlayer';
import './AudioStepCard.css';

const AudioStepCard = ({ 
  step, 
  stepNumber, 
  isActive = false,
  onAudioStart,
  onAudioEnd,
  onAudioProgress,
  className = '',
  style = {}
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Extract audio media from step
  const audioMedia = step.media ? step.media.filter(m => m.type === 'audio') : [];
  const hasAudio = audioMedia.length > 0;
  
  // Get primary audio (first audio file)
  const primaryAudio = audioMedia[0];

  // Handle audio state changes
  const handleAudioTimeUpdate = useCallback((currentTime, duration) => {
    setAudioCurrentTime(currentTime);
    setAudioDuration(duration);
    onAudioProgress && onAudioProgress(currentTime, duration);
  }, [onAudioProgress]);

  const handleAudioLoad = useCallback(() => {
    console.log('Audio loaded successfully');
  }, []);

  const handleAudioError = useCallback((error) => {
    console.error('Audio error:', error);
  }, []);

  // Format time for display
  const formatTime = useCallback((seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Toggle expanded state
  const toggleExpanded = useCallback(() => {
    setIsExpanded(!isExpanded);
  }, [isExpanded]);

  // Progress percentage for visual indicator
  const progressPercentage = audioDuration > 0 ? (audioCurrentTime / audioDuration) * 100 : 0;

  return (
    <div className={`audio-step-card ${isActive ? 'active' : ''} ${className}`} style={style}>
      {/* Step Header */}
      <div className="audio-step-header">
        <div className="audio-step-number">
          {stepNumber}
        </div>
        <div className="audio-step-title-section">
          <h3 className="audio-step-title">{step.title}</h3>
          {step.description && (
            <p className="audio-step-description">{step.description}</p>
          )}
        </div>
        {hasAudio && (
          <div className="audio-step-indicators">
            <div className="audio-indicator">
              <Headphones className="audio-icon" />
              <span className="audio-duration">{formatTime(audioDuration)}</span>
            </div>
            {progressPercentage > 0 && (
              <div className="audio-progress-mini">
                <div 
                  className="audio-progress-mini-fill"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Step Content */}
      <div className="audio-step-content">
        {/* Instructions */}
        {step.instructions && step.instructions.length > 0 && (
          <div className="audio-step-instructions">
            <div className="audio-instructions-header">
              <FileText className="instructions-icon" />
              <span>Instructions</span>
            </div>
            <ol className="audio-instructions-list">
              {step.instructions.map((instruction, index) => (
                <li key={index} className="audio-instruction-item">
                  {instruction}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Audio Player */}
        {hasAudio && (
          <div className="audio-step-media">
            <div className="audio-media-header">
              <Headphones className="audio-icon" />
              <span>Audio Training</span>
              <button
                onClick={toggleExpanded}
                className="audio-expand-button"
                aria-label={isExpanded ? "Collapse audio player" : "Expand audio player"}
              >
                {isExpanded ? "−" : "+"}
              </button>
            </div>
            
            {isExpanded && (
              <div className="audio-media-content">
                <AudioPlayer
                  documentId={primaryAudio.documentId}
                  title={primaryAudio.title || `Step ${stepNumber} Audio`}
                  transcript={primaryAudio.transcript}
                  showTranscript={false}
                  onLoad={handleAudioLoad}
                  onError={handleAudioError}
                  onTimeUpdate={handleAudioTimeUpdate}
                />
              </div>
            )}
            
            {/* Compact Controls (when collapsed) */}
            {!isExpanded && (
              <div className="audio-compact-controls">
                <div className="audio-compact-info">
                  <span className="audio-compact-title">
                    {primaryAudio.title || `Step ${stepNumber} Audio`}
                  </span>
                  {audioDuration > 0 && (
                    <span className="audio-compact-duration">
                      {formatTime(audioCurrentTime)} / {formatTime(audioDuration)}
                    </span>
                  )}
                </div>
                <button
                  onClick={toggleExpanded}
                  className="audio-compact-play-button"
                  title="Expand audio player"
                >
                  <Play className="play-icon" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Additional Media (if any) */}
        {audioMedia.length > 1 && (
          <div className="audio-additional-media">
            <div className="audio-additional-header">
              <span>Additional Audio Files</span>
            </div>
            <div className="audio-additional-list">
              {audioMedia.slice(1).map((audio, index) => (
                <div key={index} className="audio-additional-item">
                  <Headphones className="audio-icon" />
                  <span>{audio.title || `Audio ${index + 2}`}</span>
                  <button
                    onClick={() => {
                      // Handle additional audio playback
                      console.log('Play additional audio:', audio.documentId);
                    }}
                    className="audio-additional-play"
                    title="Play this audio"
                  >
                    <Play className="play-icon" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Step Footer */}
      <div className="audio-step-footer">
        <div className="audio-step-meta">
          {hasAudio && (
            <span className="audio-step-type">
              <Headphones className="audio-icon" />
              Audio Training
            </span>
          )}
          {step.estimatedTime && (
            <span className="audio-step-time">
              Est. {step.estimatedTime}
            </span>
          )}
        </div>
        
        {/* Progress Indicator */}
        {hasAudio && progressPercentage > 0 && (
          <div className="audio-step-progress">
            <div className="audio-step-progress-bar">
              <div 
                className="audio-step-progress-fill"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <span className="audio-step-progress-text">
              {Math.round(progressPercentage)}% complete
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default AudioStepCard;