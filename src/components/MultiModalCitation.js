import { useState } from 'react';
import { Image, Eye, Book, AlertTriangle, FileText, Grid3x3, Table } from 'lucide-react';
import './MultiModalCitation.css';

const MultiModalCitation = ({ citations, manualReferences, isVisible = true, onCitationClick }) => {
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [imageCache, setImageCache] = useState({});

  // Citation type icons
  const getCitationIcon = (type) => {
    switch (type) {
      case 'image':
      case 'diagram':
        return <Grid3x3 size={16} className="citation-icon" />;
      case 'table':
        return <Table size={16} className="citation-icon" />;
      case 'safety_warning':
        return <AlertTriangle size={16} className="citation-icon safety" />;
      case 'procedure_step':
        return <FileText size={16} className="citation-icon" />;
      default:
        return <Image size={16} className="citation-icon" />;
    }
  };

  // Load citation image content
  const loadCitationImage = async (citationId) => {
    if (imageCache[citationId]) {
      return imageCache[citationId];
    }

    try {
      const response = await fetch(`/citation-content/${citationId}`);
      if (response.ok) {
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setImageCache(prev => ({ ...prev, [citationId]: imageUrl }));
        return imageUrl;
      }
    } catch (error) {
      console.error('Failed to load citation image:', error);
    }
    return null;
  };

  // Handle citation click
  const handleCitationClick = async (citation) => {
    setSelectedCitation(citation);
    
    if (citation.has_content) {
      await loadCitationImage(citation.citation_id);
    }

    if (onCitationClick) {
      onCitationClick(citation);
    }
  };

  // Format citation reference for display
  const formatCitationReference = (citation) => {
    const { type, reference, page, source } = citation;
    
    if (type === 'safety_warning') {
      return `Safety Guidelines (${source}, p.${page})`;
    } else if (type === 'table') {
      return `${reference} (${source}, p.${page})`;
    } else if (type === 'diagram') {
      return `${reference} (${source}, p.${page})`;
    } else {
      return `${reference} (p.${page})`;
    }
  };

  if (!isVisible || (!citations?.length && !manualReferences?.length)) {
    return null;
  }

  return (
    <div className="multimodal-citation-container">
      {/* Visual Citations */}
      {citations && citations.length > 0 && (
        <div className="visual-citations">
          <h4 className="citations-header">
            <Eye size={18} />
            Visual References
          </h4>
          <div className="citation-grid">
            {citations.map((citation, index) => (
              <div
                key={citation.citation_id || index}
                className={`citation-card ${citation.type} ${selectedCitation?.citation_id === citation.citation_id ? 'selected' : ''}`}
                role="button"
                tabIndex={0}
                onClick={() => handleCitationClick(citation)}
                onKeyDown={(e) => e.key === 'Enter' && handleCitationClick(citation)}
                style={{cursor: 'pointer'}}
              >
                <div className="citation-header">
                  {getCitationIcon(citation.type)}
                  <span className="citation-type">{citation.type.replace('_', ' ')}</span>
                </div>
                <div className="citation-content">
                  <p className="citation-reference">
                    {formatCitationReference(citation)}
                  </p>
                  {citation.highlight_area && (
                    <div className="highlight-area">
                      <span className="highlight-label">Focus:</span>
                      <span className="highlight-text">{citation.highlight_area}</span>
                    </div>
                  )}
                </div>
                {citation.has_content && (
                  <div className="citation-preview">
                    <Image size={14} />
                    <span>View Content</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Manual References */}
      {manualReferences && manualReferences.length > 0 && (
        <div className="manual-references">
          <h4 className="references-header">
            <Book size={18} />
            Manual References
          </h4>
          <div className="reference-list">
            {manualReferences.map((ref, index) => (
              <div key={index} className="reference-item">
                <div className="reference-document">
                  <FileText size={14} />
                  <span>{ref.document}</span>
                </div>
                <div className="reference-details">
                  <span className="page-number">Page {ref.page}</span>
                  {ref.section && (
                    <span className="section">Section {ref.section}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Citation Modal */}
      {selectedCitation && selectedCitation.has_content && (
        <div 
          className="citation-modal-overlay" 
          role="button"
          tabIndex={0}
          onClick={() => setSelectedCitation(null)}
          onKeyDown={(e) => e.key === 'Escape' && setSelectedCitation(null)}
        >
          <div 
            className="citation-modal" 
            role="dialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.key === 'Escape' && setSelectedCitation(null)}
          >
            <div className="modal-header">
              <h3>{formatCitationReference(selectedCitation)}</h3>
              <button 
                className="close-button"
                onClick={() => setSelectedCitation(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-content">
              {imageCache[selectedCitation.citation_id] ? (
                <img 
                  src={imageCache[selectedCitation.citation_id]}
                  alt={selectedCitation.reference}
                  className="citation-image"
                />
              ) : (
                <div className="loading-placeholder">
                  <div className="loader"></div>
                  <p>Loading visual content...</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiModalCitation;