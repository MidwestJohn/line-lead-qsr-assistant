/**
 * Application Configuration Constants
 * Centralized configuration to avoid hardcoded values throughout the application
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  TIMEOUT: 10000, // 10 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second base delay
};

// ElevenLabs TTS Configuration
export const TTS_CONFIG = {
  API_KEY: process.env.REACT_APP_ELEVENLABS_API_KEY,
  VOICE_ID: '21m00Tcm4TlvDq8ikWAM', // Rachel voice
  MODEL_ID: 'eleven_multilingual_v2',
  VOICE_SETTINGS: {
    stability: 0.8,
    similarity_boost: 0.9,
    style: 0.4,
    use_speaker_boost: true,
  },
  MAX_CONCURRENT_CALLS: 2,
  RETRY_DELAYS: [1000, 2000, 4000], // Exponential backoff
};

// Connection Management Configuration
export const CONNECTION_CONFIG = {
  HEARTBEAT_INTERVAL: 30000, // 30 seconds
  MAX_RETRY_ATTEMPTS: 6,
  INITIAL_RETRY_DELAY: 1000, // 1 second
  MAX_RETRY_DELAY: 30000, // 30 seconds
  CONNECTION_TIMEOUT: 5000, // 5 seconds
  QUEUE_SIZE_LIMIT: 100,
};

// UI Configuration
export const UI_CONFIG = {
  MESSAGE_MAX_LENGTH: 1000,
  TEXTAREA_MIN_HEIGHT: 40,
  TEXTAREA_MAX_HEIGHT: 120,
  SCROLL_THROTTLE: 50, // milliseconds
  TYPING_INDICATOR_DELAY: 200,
  AUTO_SCROLL_THRESHOLD: 100,
};

// Voice Recognition Configuration
export const VOICE_CONFIG = {
  LANGUAGE: 'en-US',
  INTERIM_RESULTS: true,
  MAX_ALTERNATIVES: 1,
  SILENCE_TIMEOUT: 2000, // 2 seconds
  RESTART_DELAY: 750,
  MIN_WORDS_FOR_SEND: 2,
};

// File Upload Configuration
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_EXTENSIONS: ['.pdf'],
  UPLOAD_TIMEOUT: 30000, // 30 seconds
};

// Development Configuration
export const DEV_CONFIG = {
  ENABLE_DEBUG_LOGS: process.env.NODE_ENV === 'development',
  MOCK_API_DELAY: 1000, // For testing
  ENABLE_SERVICE_WORKER: false,
};