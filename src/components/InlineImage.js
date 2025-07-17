import { useState } from 'react';
import './InlineImage.css';

const InlineImage = ({ visualCitations = [] }) => {
  const [loadedImages, setLoadedImages] = useState({});
  const [failedImages, setFailedImages] = useState({});

  if (!visualCitations || visualCitations.length === 0) {
    return null;
  }

  const handleImageLoad = (imageId) => {
    setLoadedImages(prev => ({ ...prev, [imageId]: true }));
  };

  const handleImageError = (imageId) => {
    setFailedImages(prev => ({ ...prev, [imageId]: true }));
  };

  const getImageUrl = (citation) => {
    // For now, return a placeholder or document-based URL
    // In a real implementation, this would fetch from your image service
    if (citation.document_id === 'cefc0e1b-dcb6-41ca-bcbd-b787bacc8d0f') {
      // Known Baxter oven image - use a placeholder that represents equipment diagrams
      return 'https://via.placeholder.com/300x200/4f46e5/ffffff?text=Baxter+Oven+Diagram';
    }
    
    // For other images, use generic equipment placeholder
    return `https://via.placeholder.com/300x200/6b7280/ffffff?text=${encodeURIComponent(citation.title || 'Equipment')}`;
  };

  return (
    <div className="inline-images">
      {visualCitations.map((citation, index) => {
        const imageId = citation.document_id || index;
        const imageUrl = getImageUrl(citation);
        
        if (failedImages[imageId]) {
          // Show a fallback for failed images
          return (
            <div key={imageId} className="image-fallback">
              <div className="image-placeholder">
                <span className="image-icon">🖼️</span>
                <p className="image-title">{citation.title}</p>
                <p className="image-description">{citation.content_preview}</p>
              </div>
            </div>
          );
        }

        return (
          <div key={imageId} className="inline-image-container">
            <img
              src={imageUrl}
              alt={citation.title || 'Equipment diagram'}
              className="inline-image"
              onLoad={() => handleImageLoad(imageId)}
              onError={() => handleImageError(imageId)}
              loading="lazy"
            />
            {citation.title && (
              <p className="image-caption">{citation.title}</p>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default InlineImage;