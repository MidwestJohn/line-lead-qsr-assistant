import { API_CONFIG, DEV_CONFIG } from './config/constants';

// Legacy exports for backwards compatibility
export const API_BASE_URL = API_CONFIG.BASE_URL;
export const IS_DEVELOPMENT = DEV_CONFIG.ENABLE_DEBUG_LOGS;

// App Configuration
export const APP_CONFIG = {
  API_BASE_URL: API_CONFIG.BASE_URL,
  IS_DEVELOPMENT: DEV_CONFIG.ENABLE_DEBUG_LOGS,
  VERSION: '1.0.0',
  APP_NAME: 'Line Lead QSR Assistant'
};