import React from 'react';
import './PDFLoadingSkeleton.css';

const PDFLoadingSkeleton = ({ showProgress = false, progress = 0 }) => {
  return (
    <div className="pdf-loading-skeleton">
      {/* Header skeleton */}
      <div className="pdf-skeleton-header">
        <div className="pdf-skeleton-title">
          <div className="pdf-skeleton-line pdf-skeleton-line-title"></div>
          <div className="pdf-skeleton-line pdf-skeleton-line-subtitle"></div>
        </div>
        <div className="pdf-skeleton-actions">
          <div className="pdf-skeleton-button"></div>
          <div className="pdf-skeleton-button"></div>
        </div>
      </div>

      {/* Controls skeleton */}
      <div className="pdf-skeleton-controls">
        <div className="pdf-skeleton-nav-group">
          <div className="pdf-skeleton-button-small"></div>
          <div className="pdf-skeleton-page-indicator"></div>
          <div className="pdf-skeleton-button-small"></div>
        </div>
        <div className="pdf-skeleton-zoom-group">
          <div className="pdf-skeleton-button-small"></div>
          <div className="pdf-skeleton-zoom-indicator"></div>
          <div className="pdf-skeleton-button-small"></div>
        </div>
      </div>

      {/* PDF page skeleton */}
      <div className="pdf-skeleton-content">
        <div className="pdf-skeleton-page">
          <div className="pdf-skeleton-page-content">
            {/* Text lines skeleton */}
            <div className="pdf-skeleton-text-block">
              <div className="pdf-skeleton-line pdf-skeleton-line-full"></div>
              <div className="pdf-skeleton-line pdf-skeleton-line-full"></div>
              <div className="pdf-skeleton-line pdf-skeleton-line-medium"></div>
            </div>
            
            <div className="pdf-skeleton-text-block">
              <div className="pdf-skeleton-line pdf-skeleton-line-full"></div>
              <div className="pdf-skeleton-line pdf-skeleton-line-large"></div>
              <div className="pdf-skeleton-line pdf-skeleton-line-small"></div>
            </div>

            {/* Image placeholder */}
            <div className="pdf-skeleton-image"></div>

            <div className="pdf-skeleton-text-block">
              <div className="pdf-skeleton-line pdf-skeleton-line-full"></div>
              <div className="pdf-skeleton-line pdf-skeleton-line-medium"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress bar if loading */}
      {showProgress && (
        <div className="pdf-skeleton-progress">
          <div className="pdf-skeleton-progress-bar">
            <div 
              className="pdf-skeleton-progress-fill"
              style={{ width: `${Math.min(progress, 100)}%` }}
            ></div>
          </div>
          <div className="pdf-skeleton-progress-text">
            Loading PDF... {progress}%
          </div>
        </div>
      )}
    </div>
  );
};

export default PDFLoadingSkeleton;