import React from 'react';
import './ErrorBoundary.css';

class ErrorBoundary extends React.Component {
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
    // Log error details
    console.error('React Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // You could also log the error to an error reporting service here
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error, errorInfo) => {
    // In a real app, you'd send this to an error monitoring service
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    console.error('Error logged:', errorData);
    
    // Example: Send to logging service
    // fetch('/api/log-error', {
    //   method: 'POST',
    //   body: JSON.stringify(errorData),
    //   headers: { 'Content-Type': 'application/json' }
    // }).catch(e => console.error('Failed to log error:', e));
  };

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { error } = this.state;
      const isNetworkError = error?.message?.includes('fetch') || 
                           error?.message?.includes('Network');
      
      return (
        <div className="error-boundary">
          <div className="error-container">
            <div className="error-icon">⚠️</div>
            
            <h2 className="error-title">
              {isNetworkError ? 'Connection Problem' : 'Something went wrong'}
            </h2>
            
            <p className="error-message">
              {isNetworkError 
                ? 'Unable to connect to the assistant. Please check your internet connection.'
                : 'The Line Lead Assistant encountered an unexpected error.'
              }
            </p>

            {this.state.retryCount > 0 && (
              <p className="retry-info">
                Retry attempt: {this.state.retryCount}
              </p>
            )}

            <div className="error-actions">
              <button 
                onClick={this.handleRetry}
                className="retry-button primary"
              >
                Try Again
              </button>
              
              <button 
                onClick={this.handleReload}
                className="reload-button secondary"
              >
                Reload Page
              </button>
            </div>

            {/* Error details for development/debugging */}
            {process.env.NODE_ENV === 'development' && (
              <details className="error-details">
                <summary>Error Details (Development)</summary>
                <pre className="error-stack">
                  {error?.stack}
                </pre>
                {this.state.errorInfo && (
                  <pre className="component-stack">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </details>
            )}

            <div className="error-help">
              <p>If this problem persists:</p>
              <ul>
                <li>Try refreshing the page</li>
                <li>Check your internet connection</li>
                <li>Clear your browser cache</li>
                <li>Contact support if the issue continues</li>
              </ul>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component to wrap components with error boundary
export const withErrorBoundary = (WrappedComponent, fallbackComponent) => {
  return class extends React.Component {
    render() {
      return (
        <ErrorBoundary fallback={fallbackComponent}>
          <WrappedComponent {...this.props} />
        </ErrorBoundary>
      );
    }
  };
};

export default ErrorBoundary;