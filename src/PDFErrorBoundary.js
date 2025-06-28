import React from 'react';
import { Download, ExternalLink, RefreshCw, AlertTriangle } from 'lucide-react';

class PDFErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      retryCount: 0 
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error for debugging
    console.error('PDF Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Optional: Log to error reporting service
    // errorReportingService.logError(error, errorInfo);
  }

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  handleDownload = () => {
    if (this.props.fileUrl) {
      const link = document.createElement('a');
      link.href = this.props.fileUrl;
      link.download = this.props.filename || 'document.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  handleOpenInNewTab = () => {
    if (this.props.fileUrl) {
      window.open(this.props.fileUrl, '_blank', 'noopener,noreferrer');
    }
  };

  render() {
    if (this.state.hasError) {
      const { filename = 'PDF Document' } = this.props;
      
      return (
        <div className="pdf-error-boundary">
          <div className="pdf-error-container">
            <div className="pdf-error-icon">
              <AlertTriangle className="error-triangle" />
            </div>
            
            <div className="pdf-error-content">
              <h3 className="pdf-error-title">Unable to Display PDF</h3>
              <p className="pdf-error-message">
                There was an issue rendering "{filename}". This could be due to:
              </p>
              
              <ul className="pdf-error-reasons">
                <li>Network connectivity issues</li>
                <li>Corrupted or unsupported PDF format</li>
                <li>Browser compatibility limitations</li>
                <li>Insufficient memory for large files</li>
              </ul>
              
              <div className="pdf-error-actions">
                {this.state.retryCount < 3 && (
                  <button 
                    onClick={this.handleRetry}
                    className="pdf-error-btn pdf-error-btn-primary"
                    aria-label="Retry loading PDF"
                  >
                    <RefreshCw className="btn-icon" />
                    Try Again
                  </button>
                )}
                
                <button 
                  onClick={this.handleDownload}
                  className="pdf-error-btn pdf-error-btn-secondary"
                  aria-label="Download PDF file"
                >
                  <Download className="btn-icon" />
                  Download PDF
                </button>
                
                <button 
                  onClick={this.handleOpenInNewTab}
                  className="pdf-error-btn pdf-error-btn-secondary"
                  aria-label="Open PDF in new tab"
                >
                  <ExternalLink className="btn-icon" />
                  Open in New Tab
                </button>
              </div>
              
              {this.state.retryCount >= 3 && (
                <p className="pdf-error-help">
                  If the problem persists, try downloading the file or contact support.
                </p>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default PDFErrorBoundary;