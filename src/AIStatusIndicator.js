import React, { useState, useEffect } from 'react';
import './AIStatusIndicator.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000';

function AIStatusIndicator() {
  const [aiStatus, setAiStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAIStatus();
  }, []);

  const fetchAIStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/ai-status`);
      
      if (response.ok) {
        const data = await response.json();
        setAiStatus(data);
      }
    } catch (error) {
      console.error('Error fetching AI status:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="ai-status-indicator loading">
        <span className="ai-icon">🤖</span>
        <span className="ai-text">...</span>
      </div>
    );
  }

  if (!aiStatus) {
    return null;
  }

  return (
    <div className={`ai-status-indicator ${aiStatus.ai_available ? 'active' : 'inactive'}`}>
      <span className="ai-icon">
        {aiStatus.ai_available ? '🧠' : '🤖'}
      </span>
      <span className="ai-text">
        {aiStatus.ai_available ? 'AI Enhanced' : 'Document Search'}
      </span>
      <div className="ai-tooltip">
        {aiStatus.status_message}
      </div>
    </div>
  );
}

export default AIStatusIndicator;