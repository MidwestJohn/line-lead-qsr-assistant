import React, { useState, useRef, useEffect, useCallback, useReducer } from 'react';
import { Play, Pause, Volume2, VolumeX, RotateCcw, RotateCw, Headphones } from 'lucide-react';
import './AudioPlayer.css';

// Audio player state reducer following BaseChat patterns
const audioReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_PLAYING':
      return { ...state, playing: action.payload };
    case 'SET_MUTED':
      return { ...state, muted: action.payload };
    case 'SET_VOLUME':
      return { ...state, volume: action.payload };
    case 'SET_PROGRESS':
      return { ...state, currentTime: action.payload.currentTime, duration: action.payload.duration };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_BUFFERING':
      return { ...state, buffering: action.payload };
    default:
      return state;
  }
};

const AudioPlayer = ({ 
  documentId, 
  title = 'Audio Training',
  showTranscript = false,
  transcript = '',
  onLoad,
  onError,
  onTimeUpdate,
  className = '',
  style = {}
}) => {
  const [state, dispatch] = useReducer(audioReducer, {
    loading: true,
    playing: false,
    muted: false,
    volume: 1,
    currentTime: 0,
    duration: 0,
    buffering: false,
    error: null
  });

  const [isTranscriptVisible, setIsTranscriptVisible] = useState(showTranscript);
  const [audioSrc, setAudioSrc] = useState(null);
  
  const audioRef = useRef(null);
  const progressRef = useRef(null);
  const volumeRef = useRef(null);

  // Load audio source from document service
  const loadAudio = useCallback(async () => {
    if (!documentId) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const audioUrl = `http://localhost:8000/api/documents/${documentId}/source`;
      setAudioSrc(audioUrl);
      
    } catch (error) {
      console.error('Error loading audio:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load audio' });
      onError && onError(error);
    }
  }, [documentId, onError]);

  // Format time display (mm:ss)
  const formatTime = useCallback((seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Handle audio events
  const handleLoadedMetadata = useCallback(() => {
    if (audioRef.current) {
      dispatch({ 
        type: 'SET_PROGRESS', 
        payload: { 
          currentTime: audioRef.current.currentTime, 
          duration: audioRef.current.duration 
        }
      });
      dispatch({ type: 'SET_LOADING', payload: false });
      onLoad && onLoad();
    }
  }, [onLoad]);

  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      dispatch({ 
        type: 'SET_PROGRESS', 
        payload: { 
          currentTime: audioRef.current.currentTime, 
          duration: audioRef.current.duration 
        }
      });
      onTimeUpdate && onTimeUpdate(audioRef.current.currentTime, audioRef.current.duration);
    }
  }, [onTimeUpdate]);

  const handleLoadStart = useCallback(() => {
    dispatch({ type: 'SET_BUFFERING', payload: true });
  }, []);

  const handleCanPlay = useCallback(() => {
    dispatch({ type: 'SET_BUFFERING', payload: false });
  }, []);

  const handleError = useCallback((error) => {
    console.error('Audio error:', error);
    dispatch({ type: 'SET_ERROR', payload: 'Audio failed to load' });
    onError && onError(error);
  }, [onError]);

  // Control functions
  const togglePlayPause = useCallback(() => {
    if (!audioRef.current) return;
    
    if (state.playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
  }, [state.playing]);

  const toggleMute = useCallback(() => {
    if (!audioRef.current) return;
    
    const newMuted = !state.muted;
    audioRef.current.muted = newMuted;
    dispatch({ type: 'SET_MUTED', payload: newMuted });
  }, [state.muted]);

  const handleVolumeChange = useCallback((e) => {
    if (!audioRef.current) return;
    
    const newVolume = parseFloat(e.target.value);
    audioRef.current.volume = newVolume;
    dispatch({ type: 'SET_VOLUME', payload: newVolume });
    
    // Auto-unmute if volume is increased
    if (newVolume > 0 && state.muted) {
      audioRef.current.muted = false;
      dispatch({ type: 'SET_MUTED', payload: false });
    }
  }, [state.muted]);

  const handleProgressClick = useCallback((e) => {
    if (!audioRef.current || !progressRef.current) return;
    
    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * state.duration;
    
    audioRef.current.currentTime = newTime;
  }, [state.duration]);

  const skipBackward = useCallback(() => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
  }, []);

  const skipForward = useCallback(() => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.min(state.duration, audioRef.current.currentTime + 10);
  }, [state.duration]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      switch (e.key) {
        case ' ':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          skipBackward();
          break;
        case 'ArrowRight':
          e.preventDefault();
          skipForward();
          break;
        case 'm':
        case 'M':
          toggleMute();
          break;
        case 't':
        case 'T':
          setIsTranscriptVisible(!isTranscriptVisible);
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlayPause, skipBackward, skipForward, toggleMute, isTranscriptVisible]);

  // Load audio when component mounts or documentId changes
  useEffect(() => {
    loadAudio();
  }, [loadAudio]);

  // Audio event listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handlePlay = () => dispatch({ type: 'SET_PLAYING', payload: true });
    const handlePause = () => dispatch({ type: 'SET_PLAYING', payload: false });

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('error', handleError);
    };
  }, [handleLoadedMetadata, handleTimeUpdate, handleLoadStart, handleCanPlay, handleError]);

  const progressPercentage = state.duration > 0 ? (state.currentTime / state.duration) * 100 : 0;

  return (
    <div className={`audio-player ${className}`} style={style}>
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        src={audioSrc}
        preload="metadata"
        style={{ display: 'none' }}
      />

      {/* Main Player Interface */}
      <div className="audio-player-main">
        {/* Header */}
        <div className="audio-player-header">
          <div className="audio-title">
            <Headphones className="audio-icon" />
            <span>{title}</span>
          </div>
          {state.loading && (
            <div className="audio-loading">
              <div className="loading-spinner"></div>
              <span>Loading...</span>
            </div>
          )}
        </div>

        {/* Error State */}
        {state.error && (
          <div className="audio-error">
            <span>{state.error}</span>
            <button onClick={loadAudio} className="retry-button">
              Retry
            </button>
          </div>
        )}

        {/* Controls */}
        {!state.error && (
          <div className="audio-controls">
            {/* Primary Controls */}
            <div className="audio-primary-controls">
              <button
                onClick={skipBackward}
                className="audio-control-button"
                disabled={state.loading}
                title="Skip back 10 seconds"
              >
                <RotateCcw />
              </button>
              
              <button
                onClick={togglePlayPause}
                className="audio-play-button"
                disabled={state.loading}
                title={state.playing ? 'Pause' : 'Play'}
              >
                {state.playing ? <Pause /> : <Play />}
              </button>
              
              <button
                onClick={skipForward}
                className="audio-control-button"
                disabled={state.loading}
                title="Skip forward 10 seconds"
              >
                <RotateCw />
              </button>
            </div>

            {/* Progress Bar */}
            <div className="audio-progress-container">
              <span className="audio-time">{formatTime(state.currentTime)}</span>
              <div
                ref={progressRef}
                className="audio-progress-bar"
                onClick={handleProgressClick}
              >
                <div 
                  className="audio-progress-fill"
                  style={{ width: `${progressPercentage}%` }}
                />
                <div 
                  className="audio-progress-handle"
                  style={{ left: `${progressPercentage}%` }}
                />
              </div>
              <span className="audio-time">{formatTime(state.duration)}</span>
            </div>

            {/* Volume Controls */}
            <div className="audio-volume-controls">
              <button
                onClick={toggleMute}
                className="audio-control-button"
                title={state.muted ? 'Unmute' : 'Mute'}
              >
                {state.muted ? <VolumeX /> : <Volume2 />}
              </button>
              <input
                ref={volumeRef}
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={state.volume}
                onChange={handleVolumeChange}
                className="audio-volume-slider"
                title="Volume"
              />
            </div>

            {/* Transcript Toggle */}
            {transcript && (
              <button
                onClick={() => setIsTranscriptVisible(!isTranscriptVisible)}
                className={`audio-transcript-toggle ${isTranscriptVisible ? 'active' : ''}`}
                title="Toggle transcript"
              >
                T
              </button>
            )}
          </div>
        )}

        {/* Transcript Display */}
        {transcript && isTranscriptVisible && (
          <div className="audio-transcript">
            <div className="audio-transcript-header">
              <span>Transcript</span>
              <button
                onClick={() => setIsTranscriptVisible(false)}
                className="audio-transcript-close"
              >
                ×
              </button>
            </div>
            <div className="audio-transcript-content">
              {transcript}
            </div>
          </div>
        )}

        {/* Buffering Indicator */}
        {state.buffering && (
          <div className="audio-buffering">
            <div className="loading-spinner"></div>
            <span>Buffering...</span>
          </div>
        )}
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="audio-shortcuts">
        <small>
          Space: Play/Pause • ←/→: Skip 10s • M: Mute • T: Transcript
        </small>
      </div>
    </div>
  );
};

export default AudioPlayer;