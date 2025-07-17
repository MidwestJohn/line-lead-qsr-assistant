import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCw, Download, Maximize2, Minimize2, Move } from 'lucide-react';
import './EnhancedImage.css';

const EnhancedImage = ({
  documentId,
  title,
  alt,
  className = "",
  showControls = true,
  showZoom = true,
  showRotate = true,
  showDownload = true,
  showFullscreen = true,
  maxZoom = 4,
  minZoom = 0.5,
  onLoad,
  onError,
  onZoomChange,
  annotations = [],
  equipmentType = null
}) => {
  const containerRef = useRef(null);
  const imageRef = useRef(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Transform state
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  // UI state
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [metadata, setMetadata] = useState(null);
  
  // Performance optimization
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  // Image source URL from document source API
  const imageSrc = documentId ? `/api/documents/${documentId}/source` : null;
  
  // Load metadata when component mounts
  useEffect(() => {
    if (documentId) {
      fetch(`/api/documents/${documentId}/metadata`)
        .then(response => response.json())
        .then(data => {
          setMetadata(data);
        })
        .catch(error => {
          console.error('Error loading image metadata:', error);
        });
    }
  }, [documentId]);
  
  // Handle image load
  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
    setLoading(false);
    setImageError(null);
    
    if (onLoad) {
      onLoad();
    }
  }, [onLoad]);
  
  // Handle image error
  const handleImageError = useCallback((error) => {
    setImageError('Failed to load image');
    setLoading(false);
    setImageLoaded(false);
    
    if (onError) {
      onError(error);
    }
  }, [onError]);
  
  // Zoom functions
  const handleZoomIn = useCallback(() => {
    const newZoom = Math.min(zoom * 1.5, maxZoom);
    setZoom(newZoom);
    
    if (onZoomChange) {
      onZoomChange(newZoom);
    }
  }, [zoom, maxZoom, onZoomChange]);
  
  const handleZoomOut = useCallback(() => {
    const newZoom = Math.max(zoom / 1.5, minZoom);
    setZoom(newZoom);
    
    // Reset pan if zooming out to fit
    if (newZoom <= 1) {
      setPan({ x: 0, y: 0 });
    }
    
    if (onZoomChange) {
      onZoomChange(newZoom);
    }
  }, [zoom, minZoom, onZoomChange]);
  
  const handleZoomReset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setRotation(0);
    
    if (onZoomChange) {
      onZoomChange(1);
    }
  }, [onZoomChange]);
  
  // Rotation function
  const handleRotate = useCallback(() => {
    setRotation(prev => (prev + 90) % 360);
  }, []);
  
  // Pan functions
  const handleMouseDown = useCallback((e) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - pan.x,
        y: e.clientY - pan.y
      });
    }
  }, [zoom, pan]);
  
  const handleMouseMove = useCallback((e) => {
    if (isDragging && zoom > 1) {
      const newPan = {
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      };
      
      // Constrain pan to image bounds
      const container = containerRef.current;
      const image = imageRef.current;
      
      if (container && image) {
        const containerRect = container.getBoundingClientRect();
        const imageRect = image.getBoundingClientRect();
        
        const maxPanX = Math.max(0, (imageRect.width - containerRect.width) / 2);
        const maxPanY = Math.max(0, (imageRect.height - containerRect.height) / 2);
        
        newPan.x = Math.max(-maxPanX, Math.min(maxPanX, newPan.x));
        newPan.y = Math.max(-maxPanY, Math.min(maxPanY, newPan.y));
      }
      
      setPan(newPan);
    }
  }, [isDragging, dragStart, zoom]);
  
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  // Touch support for mobile
  const handleTouchStart = useCallback((e) => {
    if (e.touches.length === 1 && zoom > 1) {
      const touch = e.touches[0];
      setIsDragging(true);
      setDragStart({
        x: touch.clientX - pan.x,
        y: touch.clientY - pan.y
      });
    }
  }, [zoom, pan]);
  
  const handleTouchMove = useCallback((e) => {
    if (isDragging && e.touches.length === 1 && zoom > 1) {
      e.preventDefault();
      const touch = e.touches[0];
      const newPan = {
        x: touch.clientX - dragStart.x,
        y: touch.clientY - dragStart.y
      };
      setPan(newPan);
    }
  }, [isDragging, dragStart, zoom]);
  
  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  // Wheel zoom support
  const handleWheel = useCallback((e) => {
    if (showZoom && imageLoaded) {
      e.preventDefault();
      
      const delta = e.deltaY;
      const zoomFactor = delta > 0 ? 0.9 : 1.1;
      const newZoom = Math.max(minZoom, Math.min(maxZoom, zoom * zoomFactor));
      
      setZoom(newZoom);
      
      if (onZoomChange) {
        onZoomChange(newZoom);
      }
    }
  }, [showZoom, imageLoaded, zoom, minZoom, maxZoom, onZoomChange]);
  
  // Fullscreen support
  const handleFullscreen = useCallback(() => {
    const container = containerRef.current;
    if (container) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
        setIsFullscreen(false);
      } else {
        container.requestFullscreen();
        setIsFullscreen(true);
      }
    }
  }, []);
  
  // Download function
  const handleDownload = useCallback(() => {
    if (documentId) {
      const link = document.createElement('a');
      link.href = `/api/documents/${documentId}/source`;
      link.download = title || metadata?.name || 'image';
      link.click();
    }
  }, [documentId, title, metadata]);
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!imageLoaded) return;
      
      switch (e.key) {
        case '+':
        case '=':
          e.preventDefault();
          handleZoomIn();
          break;
        case '-':
          e.preventDefault();
          handleZoomOut();
          break;
        case '0':
          e.preventDefault();
          handleZoomReset();
          break;
        case 'r':
          e.preventDefault();
          handleRotate();
          break;
        case 'f':
          e.preventDefault();
          handleFullscreen();
          break;
        case 'Escape':
          if (isFullscreen) {
            document.exitFullscreen();
          }
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [imageLoaded, isFullscreen, handleZoomIn, handleZoomOut, handleZoomReset, handleRotate, handleFullscreen]);
  
  // Mouse event listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);
  
  // Calculate transform style
  const transformStyle = {
    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom}) rotate(${rotation}deg)`,
    transformOrigin: 'center',
    transition: isTransitioning ? 'transform 0.3s ease' : 'none',
    cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default'
  };
  
  // Equipment-specific annotations
  const getEquipmentAnnotations = () => {
    if (!equipmentType || !showAnnotations) return [];
    
    // Example annotations for different equipment types
    const equipmentAnnotations = {
      fryer: [
        { x: 20, y: 30, label: 'Temperature Control', type: 'critical' },
        { x: 60, y: 70, label: 'Drain Valve', type: 'warning' },
        { x: 80, y: 20, label: 'Safety Switch', type: 'info' }
      ],
      oven: [
        { x: 30, y: 40, label: 'Timer Controls', type: 'critical' },
        { x: 70, y: 60, label: 'Vent System', type: 'warning' }
      ],
      grill: [
        { x: 25, y: 35, label: 'Heat Zones', type: 'critical' },
        { x: 75, y: 80, label: 'Grease Tray', type: 'warning' }
      ]
    };
    
    return equipmentAnnotations[equipmentType] || [];
  };
  
  if (loading) {
    return (
      <div className={`enhanced-image-container loading ${className}`}>
        <div className="image-loading">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading image...</div>
        </div>
      </div>
    );
  }
  
  if (imageError) {
    return (
      <div className={`enhanced-image-container error ${className}`}>
        <div className="image-error">
          <div className="error-icon">🖼️</div>
          <div className="error-message">{imageError}</div>
          <div className="error-subtitle">Unable to load image content</div>
        </div>
      </div>
    );
  }
  
  return (
    <div 
      ref={containerRef}
      className={`enhanced-image-container ${className} ${isFullscreen ? 'fullscreen' : ''}`}
      onWheel={handleWheel}
    >
      <div className="image-wrapper">
        <div className="image-viewport">
          <img
            ref={imageRef}
            src={imageSrc}
            alt={alt || title || 'Equipment diagram'}
            style={transformStyle}
            onLoad={handleImageLoad}
            onError={handleImageError}
            onMouseDown={handleMouseDown}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
            draggable={false}
            className="enhanced-image"
          />
          
          {/* Equipment annotations */}
          {imageLoaded && getEquipmentAnnotations().map((annotation, index) => (
            <div
              key={index}
              className={`image-annotation ${annotation.type}`}
              style={{
                left: `${annotation.x}%`,
                top: `${annotation.y}%`,
                transform: `translate(-50%, -50%) scale(${1/zoom})`
              }}
            >
              <div className="annotation-dot"></div>
              <div className="annotation-label">{annotation.label}</div>
            </div>
          ))}
        </div>
        
        {title && (
          <div className="image-title">
            {title}
          </div>
        )}
      </div>
      
      {showControls && imageLoaded && (
        <div className="image-controls">
          <div className="control-group zoom-controls">
            {showZoom && (
              <>
                <button
                  className="control-btn"
                  onClick={handleZoomOut}
                  disabled={zoom <= minZoom}
                  title="Zoom out (-)"
                >
                  <ZoomOut size={18} />
                </button>
                
                <div className="zoom-display">
                  {Math.round(zoom * 100)}%
                </div>
                
                <button
                  className="control-btn"
                  onClick={handleZoomIn}
                  disabled={zoom >= maxZoom}
                  title="Zoom in (+)"
                >
                  <ZoomIn size={18} />
                </button>
                
                <button
                  className="control-btn"
                  onClick={handleZoomReset}
                  title="Reset zoom (0)"
                >
                  Reset
                </button>
              </>
            )}
          </div>
          
          <div className="control-group action-controls">
            {showRotate && (
              <button
                className="control-btn"
                onClick={handleRotate}
                title="Rotate (R)"
              >
                <RotateCw size={18} />
              </button>
            )}
            
            {equipmentType && (
              <button
                className="control-btn"
                onClick={() => setShowAnnotations(!showAnnotations)}
                title="Toggle annotations"
              >
                {showAnnotations ? 'Hide' : 'Show'} Labels
              </button>
            )}
            
            {showDownload && (
              <button
                className="control-btn"
                onClick={handleDownload}
                title="Download image"
              >
                <Download size={18} />
              </button>
            )}
            
            {showFullscreen && (
              <button
                className="control-btn"
                onClick={handleFullscreen}
                title="Toggle fullscreen (F)"
              >
                {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
              </button>
            )}
          </div>
        </div>
      )}
      
      {/* Help text */}
      {imageLoaded && zoom > 1 && (
        <div className="image-help">
          <Move size={14} />
          <span>Drag to pan • Scroll to zoom • Press 0 to reset</span>
        </div>
      )}
    </div>
  );
};

export default EnhancedImage;