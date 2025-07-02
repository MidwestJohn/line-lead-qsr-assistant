// API Configuration (restored after removing problematic config system)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';

// Legacy exports for backwards compatibility
export { API_BASE_URL, IS_DEVELOPMENT };

// App Configuration
export const APP_CONFIG = {
  API_BASE_URL,
  IS_DEVELOPMENT,
  VERSION: '1.0.0',
  APP_NAME: 'Line Lead QSR Assistant'
};