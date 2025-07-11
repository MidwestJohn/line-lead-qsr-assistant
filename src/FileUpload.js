import React, { useState } from 'react';
import './FileUpload.css';
import { Paperclip, Loader2 } from 'lucide-react';
import { apiService } from './services/api';
import SimpleUploadProgress from './components/SimpleUploadProgress';

function FileUpload({ onUploadSuccess, onDocumentsUpdate }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState('');
  const [processId, setProcessId] = useState(null);
  const [showProgress, setShowProgress] = useState(false);
  const [progressCompleted, setProgressCompleted] = useState(false);

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
      setProgressCompleted(false); // Reset completion flag for new upload
      setUploadMessage('Starting enhanced upload with progress tracking...');

      // Use the simple upload endpoint with automatic processing
      const result = await apiService.uploadFileWithProgress(file);
      
      console.log('Simple upload result (full):', result);
      console.log('Process ID extracted from result.data:', result?.data?.process_id);

      // Store process ID for progress tracking (it's nested in result.data)
      const processId = result?.data?.process_id;
      if (processId) {
        setProcessId(processId);
        setShowProgress(true);
        setUploading(false); // Hide basic upload UI, show progress tracker
        setUploadMessage(`✅ Upload successful! Processing started...`);
        console.log('Progress tracking started for:', processId);
      } else {
        console.error('No process ID found in result:', result);
        setUploadMessage(`⚠️ Upload successful but no progress tracking available`);
      }
      
      console.log('Simple upload result:', result);

    } catch (error) {
      console.error('Enhanced upload error:', error);
      setUploadMessage(`❌ Error: ${error.message}`);
      
      // Fall back to regular upload if enhanced upload fails
      console.log('Falling back to regular upload...');
      try {
        const fallbackResult = await apiService.uploadFile(file);
        setUploadProgress(100);
        setUploadMessage(`✅ ${fallbackResult.message} (${fallbackResult.pages_extracted} pages extracted) - Basic upload completed`);
        
        // Notify parent components
        if (onUploadSuccess) {
          onUploadSuccess(fallbackResult);
        }
        if (onDocumentsUpdate) {
          onDocumentsUpdate();
        }

        // Clear message after 3 seconds
        setTimeout(() => {
          setUploadMessage('');
          setUploadProgress(0);
        }, 3000);
      } catch (fallbackError) {
        console.error('Fallback upload also failed:', fallbackError);
        setUploadMessage(`❌ Upload failed: ${fallbackError.message}`);
      }
      
      // Clear error message after 5 seconds
      setTimeout(() => {
        setUploadMessage('');
      }, 5000);
    } finally {
      if (!showProgress) {
        setUploading(false);
      }
    }
  };

  const handleProgressComplete = (result) => {
    if (progressCompleted) {
      console.log('Progress completion already handled, skipping...');
      return;
    }
    
    console.log('Processing completed:', result);
    setProgressCompleted(true);
    setUploadMessage(`✅ Processing complete! Found ${result.entities} entities and ${result.relationships} relationships.`);
    
    // Notify parent components
    if (onUploadSuccess) {
      onUploadSuccess({
        message: 'Enhanced processing completed successfully',
        pages_extracted: result.success_summary?.pages || 'unknown',
        entities: result.entities,
        relationships: result.relationships,
        enhanced: true
      });
    }
    if (onDocumentsUpdate) {
      onDocumentsUpdate();
    }

    // Hide progress and reset state after showing success
    setTimeout(() => {
      setShowProgress(false);
      setProcessId(null);
      setUploadMessage('');
      setProgressCompleted(false); // Reset for next upload
    }, 5000);
  };



  return (
    <div className="file-upload-container">
      {!showProgress ? (
        <>
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
                  <br />
                  <small style={{ opacity: 0.7 }}>Enhanced processing with real-time progress</small>
                </div>
              </>
            ) : (
              <>
                <div className="upload-spinner">
                  <Loader2 className="upload-spinner-svg" />
                </div>
                <div className="upload-text">
                  Starting enhanced processing...
                </div>
              </>
            )}
          </div>
          
          {uploadMessage && (
            <div className={`upload-message ${uploadMessage.includes('❌') ? 'error' : 'success'}`}>
              {uploadMessage}
            </div>
          )}
        </>
      ) : (
        <SimpleUploadProgress 
          processId={processId}
          onComplete={handleProgressComplete}
        />
      )}
    </div>
  );
}

export default FileUpload;