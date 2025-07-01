import React, { useState, useEffect } from 'react';
import { apiService } from './services/api';

function HealthCheck() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkHealth();
    
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      setError(null);
      const data = await apiService.get('/health');
      setHealth(data);
    } catch (error) {
      console.error('Health check failed:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="health-check loading">Checking backend health...</div>;
  }

  if (error) {
    return (
      <div className="health-check error">
        ⚠️ Backend connection failed: {error}
      </div>
    );
  }

  if (health?.status === 'healthy') {
    return (
      <div className="health-check healthy">
        ✅ Backend healthy (v{health.version})
      </div>
    );
  }

  return (
    <div className="health-check degraded">
      ⚠️ Backend status: {health?.status || 'Unknown'}
    </div>
  );
}

export default HealthCheck;