import React, { useState, useEffect } from 'react';
import { VideoPlayer } from './index';
import { FileText, Image, Video, Music, Download, ExternalLink, Clock } from 'lucide-react';
import './MediaCitation.css';

const MediaCitation = ({ 
  documentId, 
  title, 
  mediaType, 
  contentType, 
  size, 
  timestamp,
  className = "",
  showDownload = true,
  showPreview = true,
  onPreviewOpen,
  onPreviewClose
}) => {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Get media type from content type if not provided
  const getMediaType = () => {
    if (mediaType) return mediaType;
    if (!contentType) return 'unknown';
    
    if (contentType.startsWith('video/')) return 'video';
    if (contentType.startsWith('audio/')) return 'audio';
    if (contentType.startsWith('image/')) return 'image';
    if (contentType.includes('pdf')) return 'pdf';
    if (contentType.startsWith('text/')) return 'text';
    return 'document';
  };
  
  const detectedMediaType = getMediaType();
  
  // Get appropriate icon
  const getIcon = () => {
    switch (detectedMediaType) {
      case 'video':
        return <Video size={20} />;
      case 'audio':
        return <Music size={20} />;
      case 'image':
        return <Image size={20} />;
      case 'pdf':
      case 'document':
        return <FileText size={20} />;
      default:
        return <FileText size={20} />;
    }
  };
  
  // Format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };
  
  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    
    if (typeof timestamp === 'number') {
      const minutes = Math.floor(timestamp / 60);
      const seconds = Math.floor(timestamp % 60);
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    
    return timestamp;
  };
  
  // Load metadata when needed
  useEffect(() => {
    if (documentId && !metadata && (isPreviewOpen || detectedMediaType === 'video')) {
      setLoading(true);
      fetch(`/api/documents/${documentId}/metadata`)
        .then(response => response.json())
        .then(data => {
          setMetadata(data);
          setLoading(false);
        })
        .catch(error => {
          console.error('Error loading metadata:', error);
          setLoading(false);
        });
    }
  }, [documentId, metadata, isPreviewOpen, detectedMediaType]);
  
  const handlePreviewToggle = () => {
    const newState = !isPreviewOpen;
    setIsPreviewOpen(newState);
    
    if (newState && onPreviewOpen) {
      onPreviewOpen();
    } else if (!newState && onPreviewClose) {
      onPreviewClose();
    }
  };
  
  const handleDownload = () => {
    if (documentId) {
      // Create download link
      const link = document.createElement('a');
      link.href = `/api/documents/${documentId}/source`;
      link.download = title || 'document';
      link.click();
    }
  };
  
  const handleExternalView = () => {
    if (documentId) {
      window.open(`/api/documents/${documentId}/source`, '_blank');
    }
  };
  
  return (
    <div className={`media-citation ${className}`}>
      <div className="citation-header">
        <div className="citation-info">
          <div className="citation-icon">
            {getIcon()}
          </div>
          <div className="citation-details">
            <div className="citation-title">{title || 'Untitled Document'}</div>
            <div className="citation-metadata">
              {size && <span className="file-size">{formatFileSize(size)}</span>}
              {contentType && <span className="content-type">{contentType}</span>}
              {timestamp && (
                <span className="timestamp">
                  <Clock size={12} />
                  {formatTimestamp(timestamp)}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="citation-actions">
          {showPreview && (detectedMediaType === 'video' || detectedMediaType === 'audio') && (
            <button 
              className="action-btn preview-btn"
              onClick={handlePreviewToggle}
              title={isPreviewOpen ? 'Close preview' : 'Open preview'}
            >
              {isPreviewOpen ? 'Close' : 'Preview'}
            </button>
          )}
          
          {showDownload && (
            <button 
              className="action-btn download-btn"
              onClick={handleDownload}
              title="Download file"
            >
              <Download size={16} />
            </button>
          )}
          
          <button 
            className="action-btn external-btn"
            onClick={handleExternalView}
            title="Open in new tab"
          >
            <ExternalLink size={16} />
          </button>
        </div>
      </div>
      
      {isPreviewOpen && (
        <div className="citation-preview">
          {detectedMediaType === 'video' && (
            <VideoPlayer
              documentId={documentId}
              title={title}
              startTime={typeof timestamp === 'number' ? timestamp : 0}
              onError={(error) => console.error('Video error:', error)}
              className="citation-video"
            />
          )}
          
          {detectedMediaType === 'audio' && (
            <div className="audio-player">
              <audio 
                controls 
                preload="metadata"
                src={`/api/documents/${documentId}/source`}
              >
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
          
          {detectedMediaType === 'image' && (
            <div className="image-preview">
              <img 
                src={`/api/documents/${documentId}/source`}
                alt={title || 'Document image'}
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <div className="image-error" style={{ display: 'none' }}>
                Failed to load image
              </div>
            </div>
          )}
          
          {loading && (
            <div className="preview-loading">
              <div className="loading-spinner"></div>
              <div>Loading preview...</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MediaCitation;