import React, { useState, useEffect } from 'react';
import './AIStatusIndicator.css';
import { apiService } from './services/api';

function AIStatusIndicator() {
  const [aiStatus, setAiStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAIStatus();
  }, []);

  const fetchAIStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.get('/ai-status');
      setAiStatus(data);
    } catch (error) {
      console.error('Error fetching AI status:', error);
      setError(error.message);
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