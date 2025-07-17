import React, { useState, useRef, useEffect, useCallback, useReducer } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Maximize, Minimize } from 'lucide-react';
import './VideoPlayer.css';

// Drag state management for progress bar
const dragReducer = (state, action) => {
  switch (action.type) {
    case 'START_DRAG':
      return { isDragging: true, previewTime: action.time };
    case 'UPDATE_PREVIEW':
      return { ...state, previewTime: action.time };
    case 'END_DRAG':
      return { isDragging: false, previewTime: null };
    default:
      return state;
  }
};

const VideoPlayer = ({ 
  documentId, 
  title, 
  onError, 
  onLoadStart,
  onLoadEnd,
  className = "",
  controls = true,
  autoplay = false,
  startTime = 0
}) => {
  const videoRef = useRef(null);
  const progressBarRef = useRef(null);
  const [dragState, dispatch] = useReducer(dragReducer, { isDragging: false, previewTime: null });
  
  // Video state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [didInitialSeek, setDidInitialSeek] = useState(false);
  
  // Performance optimization
  const animationFrameRef = useRef(null);
  const dragTimeoutRef = useRef(null);
  
  // Video source URL from our document source API
  const videoSrc = documentId ? `/api/documents/${documentId}/source` : null;
  
  // Time formatting utility
  const formatTime = (time) => {
    if (isNaN(time) || !isFinite(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };
  
  // Calculate time from mouse position
  const calculateTimeFromPosition = (clientX) => {
    const rect = progressBarRef.current?.getBoundingClientRect();
    if (!rect) return currentTime;
    
    const relativeX = Math.max(0, Math.min(rect.width, clientX - rect.left));
    const percent = relativeX / rect.width;
    return Math.max(0, Math.min(duration, percent * duration));
  };
  
  // Handle progress bar click
  const handleProgressClick = (e) => {
    const video = videoRef.current;
    if (video && duration > 0) {
      const newTime = calculateTimeFromPosition(e.clientX);
      
      // Pause video before seeking to prevent race conditions
      const wasPlaying = !video.paused;
      if (wasPlaying) {
        video.pause();
      }
      
      video.currentTime = newTime;
      setCurrentTime(newTime);
      
      // Resume playback if it was playing
      if (wasPlaying) {
        const playPromise = video.play();
        if (playPromise !== undefined) {
          playPromise.catch((error) => {
            console.error("Error resuming playback:", error);
          });
        }
      }
    }
  };
  
  // Drag handlers for progress bar
  const handleDragStart = useCallback((e) => {
    e.dataTransfer.setData("text/plain", "");
    e.dataTransfer.effectAllowed = "move";
    
    dispatch({ type: 'START_DRAG', time: currentTime });
  }, [currentTime]);
  
  const handleDrag = useCallback((e) => {
    if (!dragState.isDragging || !progressBarRef.current) return;
    
    const newTime = calculateTimeFromPosition(e.clientX);
    dispatch({ type: 'UPDATE_PREVIEW', time: newTime });
  }, [dragState.isDragging]);
  
  const handleDragEnd = useCallback((e) => {
    if (!dragState.isDragging) return;
    
    handleProgressClick({
      clientX: e.clientX,
      currentTarget: progressBarRef.current,
    });
    
    dispatch({ type: 'END_DRAG' });
  }, [dragState.isDragging]);
  
  // Control handlers
  const handlePlayPause = () => {
    const video = videoRef.current;
    if (video) {
      if (video.paused) {
        video.play();
        setIsPlaying(true);
      } else {
        video.pause();
        setIsPlaying(false);
      }
    }
  };
  
  const handleMute = () => {
    const video = videoRef.current;
    if (video) {
      video.muted = !video.muted;
      setIsMuted(video.muted);
    }
  };
  
  const handleSkipBack = () => {
    const video = videoRef.current;
    if (video) {
      const newTime = Math.max(0, video.currentTime - 10);
      video.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };
  
  const handleSkipForward = () => {
    const video = videoRef.current;
    if (video) {
      const newTime = Math.min(video.duration, video.currentTime + 10);
      video.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };
  
  const handleFullscreen = () => {
    const video = videoRef.current;
    if (video) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
        setIsFullscreen(false);
      } else {
        video.requestFullscreen();
        setIsFullscreen(true);
      }
    }
  };
  
  // Video event handlers
  const handleLoadStart = () => {
    setIsLoading(true);
    setError(null);
    if (onLoadStart) onLoadStart();
  };
  
  const handleLoadedMetadata = () => {
    const video = videoRef.current;
    if (video) {
      setDuration(video.duration);
      setIsLoaded(true);
      
      // Seek to start time if provided
      if (startTime > 0 && !didInitialSeek) {
        video.currentTime = startTime;
        setCurrentTime(startTime);
        setDidInitialSeek(true);
      }
    }
  };
  
  const handleLoadedData = () => {
    setIsLoading(false);
    setIsLoaded(true);
    if (onLoadEnd) onLoadEnd();
  };
  
  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (video && !dragState.isDragging) {
      setCurrentTime(video.currentTime);
    }
  };
  
  const handleError = (e) => {
    console.error("Video error:", e);
    setError("Failed to load video");
    setIsLoading(false);
    if (onError) onError(e);
  };
  
  const handleEnded = () => {
    setIsPlaying(false);
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (dragTimeoutRef.current) {
        clearTimeout(dragTimeoutRef.current);
      }
    };
  }, []);
  
  // Handle autoplay
  useEffect(() => {
    if (autoplay && isLoaded && !isPlaying) {
      const video = videoRef.current;
      if (video) {
        video.play().catch(console.error);
      }
    }
  }, [autoplay, isLoaded, isPlaying]);
  
  // Progress calculation
  const currentProgress = dragState.previewTime !== null ? dragState.previewTime : currentTime;
  const progressPercent = duration > 0 ? (currentProgress / duration) * 100 : 0;
  
  if (error) {
    return (
      <div className={`video-player-error ${className}`}>
        <div className="error-content">
          <div className="error-icon">⚠️</div>
          <div className="error-message">{error}</div>
          <div className="error-subtitle">Unable to load video content</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`video-player-container ${className} ${isFullscreen ? 'fullscreen' : ''}`}>
      <div className="video-wrapper">
        <video
          ref={videoRef}
          className="video-element"
          src={videoSrc}
          controls={false} // We use custom controls
          onLoadStart={handleLoadStart}
          onLoadedMetadata={handleLoadedMetadata}
          onLoadedData={handleLoadedData}
          onTimeUpdate={handleTimeUpdate}
          onError={handleError}
          onEnded={handleEnded}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          playsInline
          preload="metadata"
        />
        
        {isLoading && (
          <div className="video-loading">
            <div className="loading-spinner"></div>
            <div className="loading-text">Loading video...</div>
          </div>
        )}
        
        {title && (
          <div className="video-title">
            {title}
          </div>
        )}
      </div>
      
      {controls && isLoaded && (
        <div className="video-controls">
          {/* Progress Bar */}
          <div className="progress-container">
            <div
              ref={progressBarRef}
              className={`progress-bar ${dragState.isDragging ? 'dragging' : ''}`}
              onClick={handleProgressClick}
            >
              <div 
                className="progress-fill"
                style={{ width: `${progressPercent}%` }}
              />
              <div
                className="progress-handle"
                style={{ left: `${progressPercent}%` }}
                draggable="true"
                onDragStart={handleDragStart}
                onDrag={handleDrag}
                onDragEnd={handleDragEnd}
              />
            </div>
            <div className="time-display">
              <span className="current-time">{formatTime(currentProgress)}</span>
              <span className="duration">{formatTime(duration)}</span>
            </div>
          </div>
          
          {/* Control Buttons */}
          <div className="control-buttons">
            <button 
              className="control-btn"
              onClick={handleMute}
              title={isMuted ? "Unmute" : "Mute"}
            >
              {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </button>
            
            <button 
              className="control-btn"
              onClick={handleSkipBack}
              title="Skip back 10 seconds"
            >
              <SkipBack size={20} />
            </button>
            
            <button 
              className="control-btn play-btn"
              onClick={handlePlayPause}
              title={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <Pause size={24} /> : <Play size={24} />}
            </button>
            
            <button 
              className="control-btn"
              onClick={handleSkipForward}
              title="Skip forward 10 seconds"
            >
              <SkipForward size={20} />
            </button>
            
            <button 
              className="control-btn"
              onClick={handleFullscreen}
              title="Toggle fullscreen"
            >
              {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;