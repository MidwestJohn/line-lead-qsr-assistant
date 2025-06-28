import React, { useState, useEffect } from 'react';
import './DocumentList.css';
import { FileText, Loader2, Trash2, AlertTriangle, Eye } from 'lucide-react';
import { apiUtils } from './apiUtils';
import EnhancedPDFModal from './EnhancedPDFModal';
import { API_BASE_URL } from './config';

function DocumentList({ refreshTrigger, onDocumentDeleted }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(null);
  
  // PDF Preview state
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError('');
      
      const data = await apiUtils.getDocuments();
      setDocuments(data.documents);
      
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents. Check your connection and try again.');
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

  const handleDeleteClick = (doc) => {
    setDeleteConfirm(doc);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    
    try {
      setDeleting(deleteConfirm.id);
      setError('');
      
      const result = await apiUtils.deleteDocument(deleteConfirm.id);
      
      // Remove the document from local state
      setDocuments(prev => prev.filter(doc => doc.id !== deleteConfirm.id));
      
      // Call the callback to refresh other components if needed
      if (onDocumentDeleted) {
        onDocumentDeleted(result);
      }
      
      setDeleteConfirm(null);
    } catch (err) {
      console.error('Error deleting document:', err);
      setError('Failed to delete document: ' + err.message);
    } finally {
      setDeleting(null);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirm(null);
  };

  // PDF Preview handlers
  const handlePreviewClick = (doc) => {
    setSelectedDocument(doc);
    setPdfModalOpen(true);
  };

  const handlePreviewClose = () => {
    setPdfModalOpen(false);
    setSelectedDocument(null);
  };

  // Check if file is PDF based on filename
  const isPDFFile = (filename) => {
    return filename && filename.toLowerCase().endsWith('.pdf');
  };

  // Generate file URL for serving
  const getFileURL = (doc) => {
    if (!doc) return null;
    // Use URL from backend if available, otherwise construct it
    if (doc.url) {
      return `${API_BASE_URL}${doc.url}`;
    }
    // Fallback for backward compatibility
    if (doc.filename) {
      return `${API_BASE_URL}/files/${doc.filename}`;
    }
    return null;
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

              </div>
              <div className="document-actions">
                {isPDFFile(doc.original_filename) && (
                  <button
                    className="preview-button"
                    onClick={() => handlePreviewClick(doc)}
                    title="Preview PDF"
                    aria-label="Preview PDF"
                  >
                    <Eye className="preview-icon" />
                  </button>
                )}
                <button
                  className="delete-button"
                  onClick={() => handleDeleteClick(doc)}
                  disabled={deleting === doc.id}
                  title="Delete document"
                >
                  {deleting === doc.id ? (
                    <Loader2 className="delete-icon loading" />
                  ) : (
                    <Trash2 className="delete-icon" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {deleteConfirm && (
        <div className="delete-modal-overlay">
          <div className="delete-modal">
            <div className="delete-modal-icon">
              <AlertTriangle className="warning-icon" />
            </div>
            <div className="delete-modal-content">
              <h3>Delete Document</h3>
              <p>
                Are you sure you want to delete "<strong>{deleteConfirm.original_filename}</strong>"?
              </p>
              <p className="delete-warning">
                This action cannot be undone. The document will be permanently removed from the system.
              </p>
            </div>
            <div className="delete-modal-actions">
              <button 
                className="cancel-button" 
                onClick={cancelDelete}
                disabled={deleting}
              >
                Cancel
              </button>
              <button 
                className="confirm-delete-button" 
                onClick={confirmDelete}
                disabled={deleting}
              >
                {deleting ? (
                  <>
                    <Loader2 className="button-icon loading" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="button-icon" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Enhanced PDF Preview Modal */}
      <EnhancedPDFModal
        fileUrl={selectedDocument ? getFileURL(selectedDocument) : null}
        filename={selectedDocument?.original_filename}
        isOpen={pdfModalOpen}
        onClose={handlePreviewClose}
      />
    </div>
  );
}

export default DocumentList;