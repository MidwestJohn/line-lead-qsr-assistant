import { useState } from 'react';
import './FileUpload.css';
import { Paperclip, Loader2, CheckCircle } from 'lucide-react';
import { apiService } from './services/api';

function FileUpload({ onUploadSuccess, onDocumentsUpdate }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);

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
    // Supported file types (20 formats)
    const supportedTypes = [
      // Documents
      '.pdf', '.docx', '.xlsx', '.pptx', '.docm', '.xlsm', '.txt', '.md', '.csv',
      // Images
      '.jpg', '.jpeg', '.png', '.gif', '.webp',
      // Audio/Video
      '.mp4', '.mov', '.avi', '.wav', '.mp3', '.m4a'
    ];
    
    const fileName = file.name.toLowerCase();
    const isSupported = supportedTypes.some(type => fileName.endsWith(type));
    
    if (!isSupported) {
      throw new Error('Unsupported file type. Supported formats: PDF, DOCX, XLSX, PPTX, Images (JPG, PNG, GIF, WEBP), Audio/Video (MP4, MOV, AVI, WAV, MP3, M4A), and text files (TXT, MD, CSV)');
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

        setUploadMessage(`✅ ${fallbackResult.message} (${fallbackResult.pages_extracted} pages extracted) - Basic upload completed`);
        
        // Notify parent components with small delay for Ragie processing
        if (onUploadSuccess) {
          onUploadSuccess(fallbackResult);
        }
        
        // Wait a moment for Ragie processing before refreshing document list
        setTimeout(() => {
          if (onDocumentsUpdate) {
            onDocumentsUpdate();
          }
        }, 2000); // 2 second delay for Ragie processing

        // Clear message after 3 seconds
        setTimeout(() => {
          setUploadMessage('');
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
    
    // Wait for Ragie processing before refreshing document list
    setTimeout(() => {
      if (onDocumentsUpdate) {
        onDocumentsUpdate();
      }
    }, 2000); // 2 second delay for Ragie processing

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
              accept=".pdf,.docx,.xlsx,.pptx,.docm,.xlsm,.txt,.md,.csv,.jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.avi,.wav,.mp3,.m4a"
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
                  Drag & drop your file here, or{' '}
                  <label htmlFor="file-upload" className="upload-link">
                    browse
                  </label>
                </div>
                <div className="upload-hint">
                  Documents, Images, Audio/Video supported • Max 10MB
                  <br />
                  <small style={{ opacity: 0.7 }}>PDF, DOCX, XLSX, PPTX, JPG, PNG, MP4, WAV, MP3, and more</small>
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
        <div className="upload-success-display">
          <CheckCircle size={48} color="#4CAF50" />
          <h3>Upload Successful!</h3>
          <p>Your document has been uploaded and is being processed by Ragie.</p>
          <p className="upload-note">Processing may take a few minutes for large documents with images.</p>
          <button 
            onClick={() => {
              setShowProgress(false);
              setProcessId(null);
              setProgressCompleted(false);
              setUploadMessage('');
            }}
            className="reset-upload-button"
          >
            Upload Another Document
          </button>
        </div>
      )}
    </div>
  );
}

export default FileUpload;