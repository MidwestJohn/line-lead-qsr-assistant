import React, { useState, useEffect } from 'react';
import './DocumentList.css';
import { FileText, Loader2 } from 'lucide-react';
import { API_BASE_URL } from './config';

function DocumentList({ refreshTrigger }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/documents`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      
      const data = await response.json();
      setDocuments(data.documents);
      setError('');
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger]);

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="document-list-container">
        <h3>
          Uploaded Manuals
        </h3>
        <div className="loading-documents">
          <Loader2 className="loading-icon" />
          Loading documents...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-list-container">
        <h3>
          Uploaded Manuals
        </h3>
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="document-list-container">
      <h3>
        Uploaded Manuals ({documents.length})
      </h3>
      
      {documents.length === 0 ? (
        <div className="no-documents">
          <p>No manuals uploaded yet.</p>
          <p>Upload your first equipment manual above to get started!</p>
        </div>
      ) : (
        <div className="documents-grid">
          {documents.map((doc) => (
            <div key={doc.id} className="document-card">
              <div className="document-icon">
                <FileText className="document-icon-svg" />
              </div>
              <div className="document-info">
                <div className="document-name" title={doc.original_filename}>
                  {doc.original_filename}
                </div>
                <div className="document-details">
                  <div className="document-meta">
                    <span>{formatFileSize(doc.file_size)}</span>
                    <span>•</span>
                    <span>{doc.pages_count} page{doc.pages_count !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="document-date">
                    {formatDate(doc.upload_timestamp)}
                  </div>
                </div>
                <div className="document-preview">
                  {doc.text_preview}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DocumentList;