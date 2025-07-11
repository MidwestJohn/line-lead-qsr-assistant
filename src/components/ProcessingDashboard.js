import React, { useState, useEffect } from 'react';
import './ProcessingDashboard.css';

const ProcessingDashboard = () => {
  const [diagnostics, setDiagnostics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDiagnostics();
    const interval = setInterval(fetchDiagnostics, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDiagnostics = async () => {
    try {
      const response = await fetch('http://localhost:8000/diagnostics/processing-status');
      if (response.ok) {
        const data = await response.json();
        setDiagnostics(data);
        setError(null);
      } else {
        setError('Failed to fetch diagnostics');
      }
    } catch (err) {
      setError('Connection error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#4CAF50';
      case 'processing': return '#FF9800';
      case 'pending': return '#9E9E9E';
      case 'failed': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return '#4CAF50';
      case 'degraded': return '#FF9800';
      case 'failed': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  if (loading) return <div className="processing-dashboard loading">Loading pipeline status...</div>;
  if (error) return <div className="processing-dashboard error">Error: {error}</div>;

  const { system_metrics, documents, neo4j_status } = diagnostics;

  return (
    <div className="processing-dashboard">
      <h2>🔄 Document Processing Pipeline</h2>
      
      {/* System Overview */}
      <div className="dashboard-section">
        <h3>📊 System Status</h3>
        <div className="status-grid">
          <div className="status-card">
            <div className="status-label">Pipeline Health</div>
            <div 
              className="status-value" 
              style={{ color: getHealthColor(system_metrics.pipeline_health) }}
            >
              {system_metrics.pipeline_health.toUpperCase()}
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-label">Total Documents</div>
            <div className="status-value">{system_metrics.total_documents}</div>
          </div>
          
          <div className="status-card">
            <div className="status-label">Neo4j Connection</div>
            <div 
              className="status-value" 
              style={{ color: system_metrics.neo4j_connected ? '#4CAF50' : '#F44336' }}
            >
              {system_metrics.neo4j_connected ? 'CONNECTED' : 'DISCONNECTED'}
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-label">Graph Entities</div>
            <div className="status-value">{system_metrics.total_nodes}</div>
          </div>
        </div>
      </div>

      {/* Processing Progress */}
      <div className="dashboard-section">
        <h3>📈 Processing Progress</h3>
        <div className="progress-overview">
          <div className="progress-item">
            <span>Processing: {system_metrics.documents_processing}</span>
            <span>Completed: {system_metrics.documents_completed}</span>
            <span>Failed: {system_metrics.documents_failed}</span>
          </div>
        </div>
      </div>

      {/* Document Details */}
      <div className="dashboard-section">
        <h3>📄 Document Status</h3>
        <div className="documents-list">
          {documents.map((doc) => (
            <div key={doc.document_id} className="document-card">
              <div className="document-header">
                <span className="document-name">{doc.original_filename}</span>
                <span 
                  className="document-status" 
                  style={{ color: getStatusColor(doc.status) }}
                >
                  {doc.status.toUpperCase()}
                </span>
              </div>
              
              <div className="document-details">
                <div className="detail-row">
                  <span>Stage: {doc.stage}</span>
                  <span>Entities: {doc.entities_extracted}</span>
                  <span>Relationships: {doc.relationships_extracted}</span>
                </div>
                
                <div className="detail-row">
                  <span>Text Extracted: {doc.text_extracted ? '✅' : '❌'}</span>
                  <span>Neo4j Synced: {doc.neo4j_synced ? '✅' : '⏳'}</span>
                  <span>Graph Ready: {doc.graph_ready ? '✅' : '⏳'}</span>
                </div>
                
                {doc.extraction_file_size && (
                  <div className="detail-row">
                    <span>Processing Data: {(doc.extraction_file_size / 1024).toFixed(1)}KB</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Neo4j Graph Status */}
      <div className="dashboard-section">
        <h3>🕸️ Knowledge Graph Status</h3>
        <div className="graph-stats">
          <div className="stat-item">
            <span className="stat-label">Total Nodes:</span>
            <span className="stat-value">{neo4j_status.total_nodes}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total Relationships:</span>
            <span className="stat-value">{neo4j_status.total_relationships}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">QSR Equipment:</span>
            <span className="stat-value">{neo4j_status.qsr_equipment_nodes}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Document Nodes:</span>
            <span className="stat-value">{neo4j_status.document_nodes}</span>
          </div>
        </div>
        
        {neo4j_status.equipment_types && neo4j_status.equipment_types.length > 0 && (
          <div className="equipment-preview">
            <h4>🏭 Equipment Found:</h4>
            <div className="equipment-tags">
              {neo4j_status.equipment_types.slice(0, 6).map((equipment, index) => (
                <span key={index} className="equipment-tag">{equipment}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Processing Files */}
      <div className="dashboard-section">
        <h3>🗂️ Processing Files</h3>
        <div className="files-summary">
          <div>Extraction Files: {system_metrics.temp_extraction_files}</div>
          <div>Checkpoint Files: {system_metrics.checkpoint_files}</div>
          <div>Total Size: {system_metrics.total_processing_size_mb}MB</div>
        </div>
      </div>

      <div className="dashboard-footer">
        <small>Last updated: {new Date(diagnostics.timestamp).toLocaleTimeString()}</small>
      </div>
    </div>
  );
};

export default ProcessingDashboard;