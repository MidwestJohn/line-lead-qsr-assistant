# 📄 PDF Modal Integration Guide

## 🎯 Integration Examples for Line Lead App

### 1. **DocumentList Integration**

Add PDF preview to the existing DocumentList component:

```javascript
// In DocumentList.js
import PDFModal from './PDFModal';

const DocumentList = ({ refreshTrigger, onDocumentDeleted }) => {
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);

  const handlePreviewPDF = (document) => {
    setSelectedDocument(document);
    setPdfModalOpen(true);
  };

  return (
    <div className="document-list">
      {/* Existing document list code */}
      {documents.map((doc) => (
        <div key={doc.id} className="document-item">
          <span className="document-name">{doc.name}</span>
          <div className="document-actions">
            {/* Add preview button */}
            <button 
              onClick={() => handlePreviewPDF(doc)}
              className="preview-btn"
              title="Preview PDF"
            >
              <Eye className="icon" />
            </button>
            {/* Existing delete button */}
            <button onClick={() => handleDelete(doc.id)}>
              <Trash2 className="icon" />
            </button>
          </div>
        </div>
      ))}

      {/* PDF Modal */}
      <PDFModal
        fileUrl={selectedDocument?.url}
        filename={selectedDocument?.name}
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
      />
    </div>
  );
};
```

### 2. **Chat Message Integration**

Show PDFs referenced in chat messages:

```javascript
// In chat message rendering
import PDFModal from './PDFModal';

const ChatMessage = ({ message }) => {
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [selectedPDF, setSelectedPDF] = useState(null);

  const handleViewPDF = (attachment) => {
    setSelectedPDF(attachment);
    setPdfModalOpen(true);
  };

  return (
    <div className="message">
      <div className="message-text">
        {message.text}
      </div>
      
      {/* PDF Attachments */}
      {message.attachments?.map((attachment) => (
        <div key={attachment.id} className="pdf-attachment">
          <div className="attachment-info">
            <FileText className="attachment-icon" />
            <span className="attachment-name">{attachment.name}</span>
            <button 
              onClick={() => handleViewPDF(attachment)}
              className="view-pdf-btn"
            >
              View PDF
            </button>
          </div>
        </div>
      ))}

      {/* PDF Modal */}
      <PDFModal
        fileUrl={selectedPDF?.url}
        filename={selectedPDF?.name}
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
      />
    </div>
  );
};
```

### 3. **FileUpload Success Handler**

Show uploaded PDF immediately after upload:

```javascript
// In FileUpload.js
import PDFModal from './PDFModal';

const FileUpload = ({ onUploadSuccess, onDocumentsUpdate }) => {
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const handleUploadSuccess = (result) => {
    setUploadedFile(result);
    
    // Show success message
    onUploadSuccess(result);
    
    // Auto-open PDF preview for immediate review
    if (result.filename.toLowerCase().endsWith('.pdf')) {
      setPdfModalOpen(true);
    }
    
    onDocumentsUpdate();
  };

  return (
    <div className="file-upload">
      {/* Existing upload UI */}
      
      {/* Success message with preview option */}
      {uploadedFile && (
        <div className="upload-success">
          <p>✅ Upload successful!</p>
          {uploadedFile.filename.toLowerCase().endsWith('.pdf') && (
            <button 
              onClick={() => setPdfModalOpen(true)}
              className="preview-uploaded-btn"
            >
              Preview Uploaded PDF
            </button>
          )}
        </div>
      )}

      {/* PDF Modal */}
      <PDFModal
        fileUrl={uploadedFile?.fileUrl}
        filename={uploadedFile?.filename}
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
      />
    </div>
  );
};
```

### 4. **Service Status Integration**

Show training manuals from service status:

```javascript
// In ServiceStatus.js
import PDFModal from './PDFModal';

const ServiceStatus = ({ onStatusChange }) => {
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [selectedManual, setSelectedManual] = useState(null);

  const trainingManuals = [
    { name: 'Quick Start Guide', url: '/manuals/quick-start.pdf' },
    { name: 'Safety Procedures', url: '/manuals/safety.pdf' }
  ];

  const openManual = (manual) => {
    setSelectedManual(manual);
    setPdfModalOpen(true);
  };

  return (
    <div className="service-status">
      {/* Existing status display */}
      
      {/* Training resources section */}
      <div className="training-resources">
        <h4>📚 Training Resources</h4>
        {trainingManuals.map((manual, index) => (
          <button 
            key={index}
            onClick={() => openManual(manual)}
            className="manual-link"
          >
            {manual.name}
          </button>
        ))}
      </div>

      {/* PDF Modal */}
      <PDFModal
        fileUrl={selectedManual?.url}
        filename={selectedManual?.name}
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
      />
    </div>
  );
};
```

## 🎨 CSS Integration

Add these styles to your existing CSS files:

```css
/* Document List Preview Button */
.preview-btn {
  padding: 6px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preview-btn:hover {
  background: #f9fafb;
  border-color: #DC1111;
}

.preview-btn .icon {
  width: 16px;
  height: 16px;
  color: #6b7280;
}

.preview-btn:hover .icon {
  color: #DC1111;
}

/* PDF Attachment Styles */
.pdf-attachment {
  margin: 8px 0;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attachment-icon {
  width: 20px;
  height: 20px;
  color: #DC1111;
}

.attachment-name {
  flex: 1;
  font-size: 14px;
  color: #374151;
}

.view-pdf-btn {
  padding: 4px 8px;
  background: #DC1111;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.view-pdf-btn:hover {
  background: #b91c1c;
}

/* Upload Success Styles */
.upload-success {
  padding: 12px;
  background: #d1fae5;
  border: 1px solid #10b981;
  border-radius: 6px;
  margin: 16px 0;
}

.preview-uploaded-btn {
  margin-top: 8px;
  padding: 6px 12px;
  background: #DC1111;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.preview-uploaded-btn:hover {
  background: #b91c1c;
}

/* Training Resources */
.training-resources {
  margin-top: 16px;
}

.training-resources h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #374151;
}

.manual-link {
  display: block;
  width: 100%;
  padding: 6px 8px;
  text-align: left;
  background: none;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  margin: 4px 0;
  cursor: pointer;
  font-size: 13px;
  color: #DC1111;
  text-decoration: none;
  transition: all 0.2s ease;
}

.manual-link:hover {
  background: #fef2f2;
  border-color: #DC1111;
}
```

## 🔧 Props API Reference

```javascript
<PDFModal
  fileUrl={string}     // Required: URL to PDF file
  filename={string}    // Required: Display name for PDF
  isOpen={boolean}     // Required: Modal visibility state
  onClose={function}   // Required: Close handler function
/>
```

## 🚀 Implementation Steps

1. **Import the component:**
   ```javascript
   import PDFModal from './PDFModal';
   ```

2. **Add state management:**
   ```javascript
   const [pdfModalOpen, setPdfModalOpen] = useState(false);
   const [selectedPDF, setSelectedPDF] = useState(null);
   ```

3. **Add trigger button:**
   ```javascript
   <button onClick={() => {
     setSelectedPDF({ url: pdfUrl, name: pdfName });
     setPdfModalOpen(true);
   }}>
     View PDF
   </button>
   ```

4. **Add modal component:**
   ```javascript
   <PDFModal
     fileUrl={selectedPDF?.url}
     filename={selectedPDF?.name}
     isOpen={pdfModalOpen}
     onClose={() => setPdfModalOpen(false)}
   />
   ```

## ✅ Best Practices

- **Loading States**: Always show loading indicators while PDFs load
- **Error Handling**: Provide download fallback if PDF fails to render
- **Mobile UX**: Ensure touch targets are minimum 44px
- **Accessibility**: Include proper ARIA labels and keyboard support
- **Performance**: Use react-pdf's performance optimizations (text layer disabled)
- **User Feedback**: Show clear page navigation and zoom levels

The PDF modal is now ready for integration into any part of the Line Lead application! 🎉