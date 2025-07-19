import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import './ImageCitation.css';

const ImageCitation = ({ visualCitations }) => {
  const [imageUrls, setImageUrls] = useState({});
  const [loading, setLoading] = useState({});
  const [errors, setErrors] = useState({});

  const loadImage = async (citation) => {
    const citationId = citation.document_id || citation.citation_id;
    if (!citationId || imageUrls[citationId] || loading[citationId]) {
      return;
    }

    setLoading(prev => ({ ...prev, [citationId]: true }));

    try {
      // Use the backend endpoint that proxies to Ragie
      const response = await fetch(`${API_BASE_URL}/citation-content/${citationId}`);
      if (response.ok) {
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setImageUrls(prev => ({ ...prev, [citationId]: imageUrl }));
        console.log(`✅ Image loaded from Ragie via backend proxy`);
      } else {
        const errorMsg = `Failed to load image: ${response.status} ${response.statusText}`;
        console.warn(`Failed to load image for citation ${citationId}:`, response.status);
        setErrors(prev => ({ ...prev, [citationId]: errorMsg }));
      }
    } catch (error) {
      const errorMsg = `Network error: ${error.message}`;
      console.error(`Error loading image for citation ${citationId}:`, error);
      setErrors(prev => ({ ...prev, [citationId]: errorMsg }));
    } finally {
      setLoading(prev => ({ ...prev, [citationId]: false }));
    }
  };

  useEffect(() => {
    if (visualCitations && visualCitations.length > 0) {
      visualCitations.forEach(citation => {
        if (citation.media_type === 'image') {
          loadImage(citation);
        }
      });
    }
  }, [visualCitations]);

  if (!visualCitations || visualCitations.length === 0) {
    return null;
  }

  const imageCitations = visualCitations.filter(citation => citation.media_type === 'image');

  if (imageCitations.length === 0) {
    return null;
  }

  return (
    <div className="image-citations">
      {imageCitations.map((citation, index) => {
        const citationId = citation.document_id || citation.citation_id;
        const imageUrl = imageUrls[citationId];
        const isLoading = loading[citationId];
        const error = errors[citationId];

        return (
          <div key={citationId || index} className="image-citation">
            <div className="image-container">
              {isLoading && (
                <div className="image-loading">
                  <div className="loading-spinner"></div>
                  <span>Loading diagram...</span>
                </div>
              )}
              {imageUrl && (
                <img 
                  src={imageUrl} 
                  alt={citation.title || citation.equipment_name || 'Equipment diagram'}
                  className="citation-image"
                  onError={(e) => {
                    console.error('Image failed to load:', e);
                    e.target.style.display = 'none';
                  }}
                />
              )}
              {!isLoading && !imageUrl && error && (
                <div className="image-error">
                  <div className="error-icon">⚠️</div>
                  <div className="error-text">
                    <strong>Image temporarily unavailable</strong>
                    <br />
                    <span>{citation.title || citation.equipment_name}</span>
                    <br />
                    <small>{error}</small>
                  </div>
                </div>
              )}
              {!isLoading && !imageUrl && !error && (
                <div className="image-placeholder">
                  <div className="placeholder-icon">🔧</div>
                  <div className="placeholder-text">
                    <strong>{citation.title || citation.equipment_name}</strong>
                    <br />
                    <span>Equipment diagram referenced</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ImageCitation;