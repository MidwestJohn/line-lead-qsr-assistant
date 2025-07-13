import { useState } from 'react';
import { Image, Eye, Book, AlertTriangle, FileText, Grid3x3, Table, BookOpen } from 'lucide-react';
import './MultiModalCitation.css';

const MultiModalCitation = ({ citations, manualReferences, isVisible = true, onCitationClick }) => {
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [imageCache, setImageCache] = useState({});
  
  // Debug logging for citation props
  console.log('🎯 MultiModalCitation received:', {
    citations: citations?.length || 0,
    manualReferences: manualReferences?.length || 0,
    isVisible
  });

  // Enhanced citation type icons based on Ragie file_type metadata
  const getCitationIcon = (type) => {
    switch (type) {
      case 'image':
        return <Image size={16} className="citation-icon image" />;
      case 'diagram':
        return <Grid3x3 size={16} className="citation-icon diagram" />;
      case 'video':
        return <Eye size={16} className="citation-icon video" />;
      case 'table':
        return <Table size={16} className="citation-icon table" />;
      case 'safety_warning':
        return <AlertTriangle size={16} className="citation-icon safety" />;
      case 'procedure_step':
        return <FileText size={16} className="citation-icon procedure" />;
      case 'pdf_page':
        return <Book size={16} className="citation-icon pdf" />;
      case 'text':
        return <FileText size={16} className="citation-icon text" />;
      default:
        return <Image size={16} className="citation-icon default" />;
    }
  };

  // Load citation image content
  const loadCitationImage = async (citation) => {
    const citationId = citation.citation_id || citation.url || citation.id;
    
    if (imageCache[citationId]) {
      return imageCache[citationId];
    }

    try {
      // If citation has a direct URL (from Ragie), use it
      if (citation.url && citation.url.startsWith('http')) {
        setImageCache(prev => ({ ...prev, [citationId]: citation.url }));
        return citation.url;
      }
      
      // Otherwise, try to fetch from our backend
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
    
    // Check if citation has content (images, etc.)
    const hasContent = citation.has_content || citation.url || citation.type === 'image';
    
    if (hasContent) {
      await loadCitationImage(citation);
    }

    if (onCitationClick) {
      onCitationClick(citation);
    }
  };

  // Enhanced citation reference formatting using Ragie metadata
  const formatCitationReference = (citation) => {
    const { type, reference, page, source, equipment_type } = citation;
    
    // Use enhanced metadata for better formatting
    const pageStr = page ? `p.${page}` : 'page unknown';
    const sourceStr = source || 'Unknown Source';
    
    if (type === 'image') {
      return `Image: ${reference || 'Visual Content'} (${sourceStr}, ${pageStr})`;
    } else if (type === 'video') {
      return `Video: ${reference || 'Video Content'} (${sourceStr}, ${pageStr})`;
    } else if (type === 'diagram') {
      const equipmentStr = equipment_type ? ` - ${equipment_type.replace('_', ' ')}` : '';
      return `Diagram${equipmentStr} (${sourceStr}, ${pageStr})`;
    } else if (type === 'safety_warning') {
      return `Safety Guidelines (${sourceStr}, ${pageStr})`;
    } else if (type === 'table') {
      return `${reference || 'Table'} (${sourceStr}, ${pageStr})`;
    } else if (type === 'pdf_page') {
      return `${reference || 'PDF Page'} (${sourceStr}, ${pageStr})`;
    } else if (type === 'text') {
      return `${reference || 'Text Reference'} (${sourceStr}, ${pageStr})`;
    } else {
      return `${reference || 'Content'} (${sourceStr}, ${pageStr})`;
    }
  };

  // Force visibility for debugging if citations exist
  const shouldShow = citations?.length > 0 || manualReferences?.length > 0;
  
  console.log('🔍 MultiModalCitation render decision:', {
    isVisible,
    citationsLength: citations?.length || 0,
    manualReferencesLength: manualReferences?.length || 0,
    shouldShow,
    willRender: isVisible && shouldShow
  });

  if (!isVisible || !shouldShow) {
    console.log('❌ MultiModalCitation not rendering:', { isVisible, shouldShow });
    return null;
  }
  
  // Add alert for debugging (remove in production)
  if (citations?.length > 0) {
    console.log('🚨 ALERT: Citations exist, component should render!', citations);
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
                  
                  {/* Equipment and procedure badges for enhanced context */}
                  {(citation.equipment_type || citation.procedure) && (
                    <div className="citation-badges">
                      {citation.equipment_type && (
                        <span className="badge equipment">
                          {citation.equipment_type.replace('_', ' ')}
                        </span>
                      )}
                      {citation.procedure && (
                        <span className="badge procedure">
                          {citation.procedure}
                        </span>
                      )}
                    </div>
                  )}
                  
                  {/* Confidence score for QSR decision making */}
                  {citation.confidence && citation.confidence > 0 && (
                    <div className="confidence-score">
                      <span className="confidence-label">Relevance:</span>
                      <span className={`confidence-value ${citation.confidence > 0.8 ? 'high' : citation.confidence > 0.6 ? 'medium' : 'low'}`}>
                        {Math.round(citation.confidence * 100)}%
                      </span>
                    </div>
                  )}
                  
                  {citation.highlight_area && (
                    <div className="highlight-area">
                      <span className="highlight-label">Focus:</span>
                      <span className="highlight-text">{citation.highlight_area}</span>
                    </div>
                  )}
                  
                  {/* Enhanced description for image/video content */}
                  {citation.description && citation.type !== 'text' && (
                    <div className="citation-description">
                      <span className="description-text">{citation.description}</span>
                    </div>
                  )}
                </div>
                {(citation.has_content || citation.url || citation.media || ['image', 'video', 'diagram'].includes(citation.type)) && (
                  <div className="citation-preview">
                    {citation.type === 'image' && <Image size={14} />}
                    {citation.type === 'video' && <Eye size={14} />}
                    {citation.type === 'diagram' && <Grid3x3 size={14} />}
                    {citation.type === 'pdf_page' && <Book size={14} />}
                    {!['image', 'video', 'diagram', 'pdf_page'].includes(citation.type) && <FileText size={14} />}
                    <span>
                      {citation.type === 'image' ? 'View Image' :
                       citation.type === 'video' ? 'View Video' :
                       citation.type === 'diagram' ? 'View Diagram' :
                       citation.type === 'pdf_page' ? 'View PDF' :
                       'View Content'}
                    </span>
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

      {/* Enhanced Modal for Different Media Types */}
      {selectedCitation && (selectedCitation.has_content || selectedCitation.url || selectedCitation.media || ['image', 'video', 'diagram', 'pdf_page'].includes(selectedCitation.type)) && (
        <div 
          className="citation-modal-overlay" 
          role="button"
          tabIndex={0}
          onClick={() => setSelectedCitation(null)}
          onKeyDown={(e) => {
            if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') {
              setSelectedCitation(null);
            }
          }}
        >
          <div 
            className="citation-modal" 
            role="dialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div className="modal-title">
                {getCitationIcon(selectedCitation.type)}
                <h3>{formatCitationReference(selectedCitation)}</h3>
              </div>
              
              {/* Equipment context in modal header */}
              {(selectedCitation.equipment_type || selectedCitation.procedure) && (
                <div className="modal-badges">
                  {selectedCitation.equipment_type && (
                    <span className="modal-badge equipment">
                      {selectedCitation.equipment_type.replace('_', ' ')}
                    </span>
                  )}
                  {selectedCitation.procedure && (
                    <span className="modal-badge procedure">
                      {selectedCitation.procedure}
                    </span>
                  )}
                </div>
              )}
              
              <button 
                className="close-button"
                onClick={() => setSelectedCitation(null)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-content">
              {(() => {
                // Handle different content types based on Ragie metadata
                const citationId = selectedCitation.citation_id || selectedCitation.url || selectedCitation.id;
                const mediaUrl = selectedCitation.media?.url || selectedCitation.url || imageCache[citationId];
                const mediaType = selectedCitation.media?.type || selectedCitation.type;
                
                if (selectedCitation.type === 'pdf_page') {
                  // PDF page viewer
                  return (
                    <div className="pdf-viewer">
                      <div className="pdf-info">
                        <Book size={24} />
                        <div>
                          <h4>PDF Reference</h4>
                          <p>Page {selectedCitation.page} of {selectedCitation.source}</p>
                          {selectedCitation.description && (
                            <p className="pdf-description">{selectedCitation.description}</p>
                          )}
                        </div>
                      </div>
                      <div className="pdf-actions">
                        <button onClick={() => window.open(selectedCitation.pdf_url || '#', '_blank')}>
                          <BookOpen size={16} />
                          Open PDF
                        </button>
                      </div>
                    </div>
                  );
                } else if (mediaType === 'video' && mediaUrl) {
                  // Video content
                  return (
                    <div className="video-viewer">
                      <video 
                        src={mediaUrl}
                        controls
                        className="citation-video"
                        aria-label={selectedCitation.description || selectedCitation.reference || 'QSR Manual Video'}
                      >
                        <track kind="captions" src="" label="No captions available" default />
                        Your browser does not support video playback.
                      </video>
                      {selectedCitation.description && (
                        <p className="media-description">{selectedCitation.description}</p>
                      )}
                    </div>
                  );
                } else if (mediaUrl) {
                  // Image content (default)
                  return (
                    <div className="image-viewer">
                      <img 
                        src={mediaUrl}
                        alt={selectedCitation.description || selectedCitation.reference || 'QSR Manual Image'}
                        className="citation-image"
                      />
                      {selectedCitation.description && (
                        <p className="media-description">{selectedCitation.description}</p>
                      )}
                    </div>
                  );
                } else {
                  // Loading state or text-only content
                  return (
                    <div className="loading-placeholder">
                      <div className="loader"></div>
                      <p>Loading {mediaType || 'visual'} content...</p>
                      {selectedCitation.description && (
                        <div className="text-content">
                          <h4>Content Description:</h4>
                          <p>{selectedCitation.description}</p>
                        </div>
                      )}
                    </div>
                  );
                }
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiModalCitation;