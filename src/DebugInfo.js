import React from 'react';
import { API_BASE_URL, IS_DEVELOPMENT } from './config';

function DebugInfo() {
  return (
    <div style={{ 
      position: 'fixed', 
      bottom: '10px', 
      right: '10px', 
      background: 'rgba(0,0,0,0.8)', 
      color: 'white', 
      padding: '10px', 
      fontSize: '12px',
      zIndex: 9999,
      borderRadius: '5px'
    }}>
      <div><strong>Environment Debug Info:</strong></div>
      <div>NODE_ENV: {process.env.NODE_ENV}</div>
      <div>REACT_APP_API_URL: {process.env.REACT_APP_API_URL || 'UNDEFINED'}</div>
      <div>API_BASE_URL: {API_BASE_URL}</div>
      <div>IS_DEVELOPMENT: {IS_DEVELOPMENT.toString()}</div>
      <div>Timestamp: {new Date().toISOString()}</div>
    </div>
  );
}

export default DebugInfo;