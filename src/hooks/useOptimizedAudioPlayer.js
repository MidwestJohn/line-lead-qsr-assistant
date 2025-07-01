/**
 * Optimized Audio Player Hook - Eliminates chunking issues
 * 
 * This replaces the complex TTS queue system with simple, reliable audio playback
 * that prevents the weird pausing and chunking problems.
 */

import { useRef, useCallback, useState } from 'react';
import { Howl } from 'howler';

const useOptimizedAudioPlayer = () => {
  const currentAudio = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [lastRequestTime, setLastRequestTime] = useState(0);

  const playAudio = useCallback((audioData, onComplete = null) => {
    // CRITICAL: Stop any existing audio first to prevent overlapping
    if (currentAudio.current) {
      try {
        currentAudio.current.stop();
        currentAudio.current.unload();
      } catch (e) {
        console.warn('Error stopping previous audio:', e);
      }
      currentAudio.current = null;
    }

    if (!audioData) {
      console.warn('No audio data provided');
      if (onComplete) onComplete();
      return;
    }

    try {
      // OPTIMIZED: Simple Howler.js configuration for reliability
      const audio = new Howl({
        src: [`data:audio/mp3;base64,${audioData}`],
        format: ['mp3'],
        html5: true,  // Better mobile support
        preload: true,
        volume: 0.85,
        onload: () => {
          console.log('✅ Audio loaded successfully');
        },
        onplay: () => {
          setIsPlaying(true);
          console.log('🔊 Audio playback started');
        },
        onend: () => {
          setIsPlaying(false);
          currentAudio.current = null;
          console.log('🔊 Audio playback completed');
          if (onComplete) onComplete();
        },
        onerror: (error) => {
          console.error('❌ Audio playback error:', error);
          setIsPlaying(false);
          currentAudio.current = null;
          if (onComplete) onComplete();
        }
      });

      currentAudio.current = audio;
      
      // SMALL DELAY: Prevents audio cut-off issues on some devices
      setTimeout(() => {
        if (currentAudio.current) {
          currentAudio.current.play();
        }
      }, 100);

    } catch (error) {
      console.error('❌ Failed to create audio:', error);
      setIsPlaying(false);
      if (onComplete) onComplete();
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (currentAudio.current) {
      try {
        currentAudio.current.stop();
        currentAudio.current.unload();
      } catch (e) {
        console.warn('Error stopping audio:', e);
      }
      currentAudio.current = null;
    }
    setIsPlaying(false);
  }, []);

  // REQUEST THROTTLING: Prevent rapid-fire voice requests that cause API issues
  const makeVoiceRequest = useCallback(async (message, apiEndpoint = '/api/chat-voice-with-audio') => {
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    const minInterval = 3000; // Minimum 3 seconds between requests

    if (timeSinceLastRequest < minInterval) {
      console.log('🚫 Voice request throttled - please wait');
      throw new Error('Please wait before making another voice request');
    }

    setLastRequestTime(now);

    try {
      // REQUEST TIMEOUT: Prevent hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 25000);

      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timed out');
      }
      throw error;
    }
  }, [lastRequestTime]);

  return { 
    playAudio, 
    stopAudio, 
    isPlaying, 
    makeVoiceRequest
  };
};

export default useOptimizedAudioPlayer;