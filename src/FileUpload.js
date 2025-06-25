import React, { useState } from 'react';
import './FileUpload.css';
import { Paperclip, Loader2 } from 'lucide-react';
import { API_BASE_URL } from './config';

function FileUpload({ onUploadSuccess, onDocumentsUpdate }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState('');

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const validateFile = (file) => {
    // Check file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      throw new Error('Only PDF files are allowed');
    }
    
    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      throw new Error('File size must be less than 10MB');
    }
    
    return true;
  };

  const handleFile = async (file) => {
    try {
      validateFile(file);
      
      setUploading(true);
      setUploadProgress(0);
      setUploadMessage('Uploading and processing PDF...');

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Upload failed');
      }

      setUploadProgress(100);
      setUploadMessage(`✅ ${result.message} (${result.pages_extracted} pages extracted)`);
      
      // Notify parent components
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
      if (onDocumentsUpdate) {
        onDocumentsUpdate();
      }

      // Clear message after 3 seconds
      setTimeout(() => {
        setUploadMessage('');
        setUploadProgress(0);
      }, 3000);

    } catch (error) {
      console.error('Upload error:', error);
      setUploadMessage(`❌ Error: ${error.message}`);
      
      // Clear error message after 5 seconds
      setTimeout(() => {
        setUploadMessage('');
      }, 5000);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload-container">
      <div 
        className={`file-upload-area ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept=".pdf"
          onChange={handleFileInput}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        
        {!uploading ? (
          <>
            <div className="upload-icon">
              <Paperclip className="upload-icon-svg" />
            </div>
            <div className="upload-text">
              <strong>Upload Equipment Manual</strong>
              <br />
              Drag & drop a PDF file here, or{' '}
              <label htmlFor="file-upload" className="upload-link">
                browse
              </label>
            </div>
            <div className="upload-hint">
              PDF files only, max 10MB
            </div>
          </>
        ) : (
          <>
            <div className="upload-spinner">
              <Loader2 className="upload-spinner-svg" />
            </div>
            <div className="upload-text">
              Processing PDF...
            </div>
          </>
        )}
      </div>
      
      {uploadMessage && (
        <div className={`upload-message ${uploadMessage.includes('❌') ? 'error' : 'success'}`}>
          {uploadMessage}
        </div>
      )}
    </div>
  );
}

export default FileUpload;