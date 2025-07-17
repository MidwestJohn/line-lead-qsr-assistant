import React, { useState, useEffect } from 'react';
import { EnhancedImage } from './index';
import { VideoPlayer } from './index';
import { Clock, AlertTriangle, Info, CheckCircle, Eye, EyeOff } from 'lucide-react';
import './EnhancedStepCard.css';

const EnhancedStepCard = ({
  step,
  stepNumber,
  isActive = false,
  isCompleted = false,
  showMedia = true,
  onStepComplete,
  onMediaToggle,
  className = ""
}) => {
  const [mediaExpanded, setMediaExpanded] = useState(false);
  const [mediaLoaded, setMediaLoaded] = useState(false);
  const [mediaError, setMediaError] = useState(null);
  
  // Extract media from step
  const getStepMedia = () => {
    if (!step.media || !step.media.length) return null;
    
    return step.media.map(media => ({
      ...media,
      type: media.type || detectMediaType(media.contentType),
      title: media.title || `Step ${stepNumber} - ${media.type}`,
      equipmentType: step.equipmentType || null
    }));
  };
  
  const detectMediaType = (contentType) => {
    if (!contentType) return 'unknown';
    
    if (contentType.startsWith('video/')) return 'video';
    if (contentType.startsWith('audio/')) return 'audio';
    if (contentType.startsWith('image/')) return 'image';
    return 'document';
  };
  
  const stepMedia = getStepMedia();
  
  // Get step priority/type styling
  const getStepType = () => {
    if (step.safety) return 'safety';
    if (step.critical) return 'critical';
    if (step.warning) return 'warning';
    return 'normal';
  };
  
  const stepType = getStepType();
  
  // Get appropriate icon
  const getStepIcon = () => {
    switch (stepType) {
      case 'safety':
        return <AlertTriangle size={20} className="step-icon safety" />;
      case 'critical':
        return <AlertTriangle size={20} className="step-icon critical" />;
      case 'warning':
        return <Info size={20} className="step-icon warning" />;
      default:
        return <CheckCircle size={20} className="step-icon normal" />;
    }
  };
  
  const handleMediaToggle = () => {
    const newExpanded = !mediaExpanded;
    setMediaExpanded(newExpanded);
    
    if (onMediaToggle) {
      onMediaToggle(stepNumber, newExpanded);
    }
  };
  
  const handleStepComplete = () => {
    if (onStepComplete) {
      onStepComplete(stepNumber);
    }
  };
  
  const handleMediaLoad = () => {
    setMediaLoaded(true);
    setMediaError(null);
  };
  
  const handleMediaError = (error) => {
    setMediaError(error);
    setMediaLoaded(false);
  };
  
  // Auto-expand media for critical steps
  useEffect(() => {
    if (stepType === 'critical' && stepMedia && stepMedia.length > 0) {
      setMediaExpanded(true);
    }
  }, [stepType, stepMedia]);
  
  return (
    <div className={`enhanced-step-card ${stepType} ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${className}`}>
      <div className="step-header">
        <div className="step-number-container">
          <div className="step-number">{stepNumber}</div>
          {getStepIcon()}
        </div>
        
        <div className="step-content">
          <div className="step-title">
            {step.title || `Step ${stepNumber}`}
          </div>
          
          {step.description && (
            <div className="step-description">
              {step.description}
            </div>
          )}
          
          {step.time && (
            <div className="step-time">
              <Clock size={14} />
              <span>{step.time}</span>
            </div>
          )}
        </div>
        
        {stepMedia && stepMedia.length > 0 && showMedia && (
          <div className="media-toggle">
            <button
              className="media-toggle-btn"
              onClick={handleMediaToggle}
              title={mediaExpanded ? 'Hide media' : 'Show media'}
            >
              {mediaExpanded ? <EyeOff size={18} /> : <Eye size={18} />}
              <span>{mediaExpanded ? 'Hide' : 'Show'}</span>
            </button>
          </div>
        )}
      </div>
      
      {step.details && (
        <div className="step-details">
          {Array.isArray(step.details) ? (
            <ul className="step-details-list">
              {step.details.map((detail, index) => (
                <li key={index}>{detail}</li>
              ))}
            </ul>
          ) : (
            <p>{step.details}</p>
          )}
        </div>
      )}
      
      {step.safety && (
        <div className="step-safety">
          <AlertTriangle size={16} />
          <span>Safety: {step.safety}</span>
        </div>
      )}
      
      {step.tips && (
        <div className="step-tips">
          <Info size={16} />
          <span>Tip: {step.tips}</span>
        </div>
      )}
      
      {mediaExpanded && stepMedia && stepMedia.length > 0 && (
        <div className="step-media">
          {stepMedia.map((media, index) => (
            <div key={index} className="media-item">
              {media.type === 'image' && (
                <EnhancedImage
                  documentId={media.documentId}
                  title={media.title}
                  alt={media.alt || `Step ${stepNumber} diagram`}
                  showControls={true}
                  showZoom={true}
                  showRotate={true}
                  showDownload={true}
                  equipmentType={media.equipmentType}
                  onLoad={handleMediaLoad}
                  onError={handleMediaError}
                  className="step-media-image"
                />
              )}
              
              {media.type === 'video' && (
                <VideoPlayer
                  documentId={media.documentId}
                  title={media.title}
                  startTime={media.startTime || 0}
                  onError={handleMediaError}
                  onLoadStart={() => setMediaLoaded(false)}
                  onLoadEnd={handleMediaLoad}
                  className="step-media-video"
                />
              )}
              
              {media.type === 'audio' && (
                <div className="step-media-audio">
                  <audio 
                    controls 
                    preload="metadata"
                    src={`/api/documents/${media.documentId}/source`}
                    onLoadStart={() => setMediaLoaded(false)}
                    onLoadedData={handleMediaLoad}
                    onError={handleMediaError}
                  >
                    Your browser does not support the audio element.
                  </audio>
                  <div className="audio-title">{media.title}</div>
                </div>
              )}
              
              {media.description && (
                <div className="media-description">
                  {media.description}
                </div>
              )}
            </div>
          ))}
          
          {mediaError && (
            <div className="media-error">
              <AlertTriangle size={16} />
              <span>Failed to load media content</span>
            </div>
          )}
        </div>
      )}
      
      <div className="step-actions">
        {!isCompleted && (
          <button
            className="step-complete-btn"
            onClick={handleStepComplete}
            disabled={!isActive}
          >
            {isActive ? 'Mark Complete' : 'Complete Previous Steps'}
          </button>
        )}
        
        {isCompleted && (
          <div className="step-completed">
            <CheckCircle size={16} />
            <span>Completed</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedStepCard;