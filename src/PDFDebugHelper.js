/**
 * 🔍 PDF Debug Helper
 * 
 * Comprehensive debugging utilities for PDF preview issues
 */

// Enhanced debug logger with better formatting
export const pdfDebugLog = (section, message, data = null) => {
  const timestamp = new Date().toISOString();
  const style = 'color: #2563eb; font-weight: bold;';
  
  console.group(`%c🔍 [PDF-DEBUG] [${section}] ${message}`, style);
  if (data) {
    console.log('Data:', data);
  }
  console.groupEnd();
};

// Test network connectivity
export const testNetworkConnectivity = async () => {
  const testUrls = [
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
    'https://google.com',
    window.location.origin
  ];

  const results = [];
  
  for (const url of testUrls) {
    try {
      const start = Date.now();
      const response = await fetch(url, { method: 'HEAD', mode: 'no-cors' });
      const time = Date.now() - start;
      
      results.push({
        url,
        accessible: true,
        responseTime: time,
        status: response.status || 'no-cors'
      });
    } catch (error) {
      results.push({
        url,
        accessible: false,
        error: error.message
      });
    }
  }
  
  pdfDebugLog('NETWORK-TEST', 'Network connectivity test results', results);
  return results;
};

// Test PDF.js worker
export const testPDFWorker = async () => {
  const workerUrls = [
    `//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`,
    `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`,
    `https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js`,
    '/pdf.worker.min.js'
  ];

  const results = [];
  
  for (const url of workerUrls) {
    try {
      const start = Date.now();
      const response = await fetch(url, { method: 'HEAD' });
      const time = Date.now() - start;
      
      results.push({
        url,
        accessible: response.ok,
        status: response.status,
        responseTime: time,
        contentType: response.headers.get('Content-Type')
      });
    } catch (error) {
      results.push({
        url,
        accessible: false,
        error: error.message
      });
    }
  }
  
  pdfDebugLog('WORKER-TEST', 'PDF.js worker accessibility test', results);
  return results;
};

// Test file accessibility
export const testFileAccess = async (fileUrl) => {
  try {
    pdfDebugLog('FILE-TEST', `Testing file access: ${fileUrl}`);
    
    const start = Date.now();
    const response = await fetch(fileUrl, { method: 'HEAD' });
    const time = Date.now() - start;
    
    const headers = {};
    response.headers.forEach((value, key) => {
      headers[key] = value;
    });
    
    const result = {
      url: fileUrl,
      accessible: response.ok,
      status: response.status,
      statusText: response.statusText,
      responseTime: time,
      headers,
      contentLength: response.headers.get('Content-Length'),
      contentType: response.headers.get('Content-Type'),
      contentDisposition: response.headers.get('Content-Disposition'),
      corsHeaders: {
        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
        'Access-Control-Expose-Headers': response.headers.get('Access-Control-Expose-Headers')
      }
    };
    
    pdfDebugLog('FILE-TEST', response.ok ? '✅ File accessible' : '❌ File access failed', result);
    return result;
    
  } catch (error) {
    const result = {
      url: fileUrl,
      accessible: false,
      error: error.message,
      errorType: error.name
    };
    
    pdfDebugLog('FILE-TEST', '❌ File access error', result);
    return result;
  }
};

// Browser and environment information
export const getBrowserInfo = () => {
  const info = {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    cookieEnabled: navigator.cookieEnabled,
    onLine: navigator.onLine,
    hardwareConcurrency: navigator.hardwareConcurrency,
    maxTouchPoints: navigator.maxTouchPoints,
    screen: {
      width: window.screen.width,
      height: window.screen.height,
      availWidth: window.screen.availWidth,
      availHeight: window.screen.availHeight,
      pixelDepth: window.screen.pixelDepth
    },
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight
    },
    memory: performance?.memory ? {
      usedJSHeapSize: performance.memory.usedJSHeapSize,
      totalJSHeapSize: performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
    } : null,
    connection: navigator?.connection ? {
      effectiveType: navigator.connection.effectiveType,
      downlink: navigator.connection.downlink,
      rtt: navigator.connection.rtt
    } : null
  };
  
  pdfDebugLog('BROWSER-INFO', 'Browser and environment information', info);
  return info;
};

// Comprehensive PDF preview debugging
export const runComprehensiveDebug = async (fileUrl) => {
  pdfDebugLog('DEBUG-SUITE', '🚀 Starting comprehensive PDF preview debugging...');
  
  const results = {
    timestamp: new Date().toISOString(),
    fileUrl,
    browserInfo: getBrowserInfo(),
    networkTest: await testNetworkConnectivity(),
    workerTest: await testPDFWorker(),
    fileTest: await testFileAccess(fileUrl)
  };
  
  // Analyze results
  const analysis = {
    networkConnected: results.networkTest.some(test => test.accessible),
    workerAvailable: results.workerTest.some(test => test.accessible),
    fileAccessible: results.fileTest.accessible,
    corsConfigured: !!results.fileTest.corsHeaders['Access-Control-Allow-Origin'],
    hasContentLength: !!results.fileTest.contentLength,
    isValidPDF: results.fileTest.contentType?.includes('application/pdf'),
    recommendations: []
  };
  
  // Generate recommendations
  if (!analysis.networkConnected) {
    analysis.recommendations.push('❌ Network connectivity issues detected');
  }
  
  if (!analysis.workerAvailable) {
    analysis.recommendations.push('❌ PDF.js worker not accessible - try local fallback');
  }
  
  if (!analysis.fileAccessible) {
    analysis.recommendations.push('❌ PDF file not accessible - check server configuration');
  }
  
  if (!analysis.corsConfigured) {
    analysis.recommendations.push('⚠️ CORS headers not configured properly');
  }
  
  if (!analysis.hasContentLength) {
    analysis.recommendations.push('⚠️ Content-Length header missing - progress tracking unavailable');
  }
  
  if (!analysis.isValidPDF) {
    analysis.recommendations.push('❌ File is not served as application/pdf');
  }
  
  if (analysis.recommendations.length === 0) {
    analysis.recommendations.push('✅ All basic checks passed - investigate PDF.js specific issues');
  }
  
  results.analysis = analysis;
  
  pdfDebugLog('DEBUG-SUITE', '📊 Comprehensive debugging completed', results);
  
  // Log summary
  console.group('🎯 PDF DEBUG SUMMARY');
  analysis.recommendations.forEach(rec => console.log(rec));
  console.groupEnd();
  
  return results;
};

// Test PDF.js availability
export const testPDFJSAvailability = () => {
  try {
    // Try to import PDF.js dynamically to test availability
    const testResults = {
      available: false,
      version: null,
      workerSrc: null,
      error: null
    };
    
    // This will only work if PDF.js is imported in the calling component
    // We can't test it directly here, but we can provide the test function
    pdfDebugLog('PDFJS-TEST', 'PDF.js availability test function ready');
    
    return testResults;
  } catch (error) {
    pdfDebugLog('PDFJS-TEST', 'PDF.js availability test failed', error);
    return {
      available: false,
      error: error.message
    };
  }
};

// Enhanced debug suite with PDF.js availability check
export const runEnhancedPDFDebug = async (fileUrl, pdfjs = null) => {
  pdfDebugLog('DEBUG-SUITE', '🚀 Starting enhanced PDF preview debugging...');
  
  const results = {
    timestamp: new Date().toISOString(),
    fileUrl,
    pdfjs: null,
    browserInfo: getBrowserInfo(),
    networkTest: await testNetworkConnectivity(),
    workerTest: await testPDFWorker(),
    fileTest: await testFileAccess(fileUrl)
  };
  
  // Test PDF.js availability if provided
  if (pdfjs) {
    results.pdfjs = {
      available: true,
      version: pdfjs.version,
      workerSrc: pdfjs.GlobalWorkerOptions.workerSrc,
      workerConfigured: !!pdfjs.GlobalWorkerOptions.workerSrc
    };
    pdfDebugLog('PDFJS-TEST', 'PDF.js is available', results.pdfjs);
  } else {
    results.pdfjs = {
      available: false,
      error: 'PDF.js not provided to debug function'
    };
    pdfDebugLog('PDFJS-TEST', 'PDF.js not available or not provided');
  }
  
  // Enhanced analysis with PDF.js specific checks
  const analysis = {
    pdfjsAvailable: results.pdfjs.available,
    pdfjsWorkerConfigured: results.pdfjs.workerConfigured,
    networkConnected: results.networkTest.some(test => test.accessible),
    workerAvailable: results.workerTest.some(test => test.accessible),
    fileAccessible: results.fileTest.accessible,
    corsConfigured: !!results.fileTest.corsHeaders['Access-Control-Allow-Origin'],
    hasContentLength: !!results.fileTest.contentLength,
    isValidPDF: results.fileTest.contentType?.includes('application/pdf'),
    recommendations: []
  };
  
  // Generate enhanced recommendations
  if (!analysis.pdfjsAvailable) {
    analysis.recommendations.push('❌ PDF.js not imported or not available in component');
  }
  
  if (!analysis.pdfjsWorkerConfigured) {
    analysis.recommendations.push('❌ PDF.js worker not configured');
  }
  
  if (!analysis.networkConnected) {
    analysis.recommendations.push('❌ Network connectivity issues detected');
  }
  
  if (!analysis.workerAvailable) {
    analysis.recommendations.push('❌ PDF.js worker not accessible - try local fallback');
  }
  
  if (!analysis.fileAccessible) {
    analysis.recommendations.push('❌ PDF file not accessible - check server configuration');
  }
  
  if (!analysis.corsConfigured) {
    analysis.recommendations.push('⚠️ CORS headers not configured properly');
  }
  
  if (!analysis.hasContentLength) {
    analysis.recommendations.push('⚠️ Content-Length header missing - progress tracking unavailable');
  }
  
  if (!analysis.isValidPDF) {
    analysis.recommendations.push('❌ File is not served as application/pdf');
  }
  
  if (analysis.recommendations.length === 0) {
    analysis.recommendations.push('✅ All basic checks passed - investigate PDF.js specific rendering issues');
  }
  
  results.analysis = analysis;
  
  pdfDebugLog('DEBUG-SUITE', '📊 Enhanced PDF debugging completed', results);
  
  // Log summary
  console.group('🎯 ENHANCED PDF DEBUG SUMMARY');
  analysis.recommendations.forEach(rec => console.log(rec));
  console.groupEnd();
  
  return results;
};

// Auto-run debugging when this module is loaded
if (typeof window !== 'undefined') {
  window.pdfDebug = {
    runComprehensiveDebug,
    runEnhancedPDFDebug,
    testFileAccess,
    testPDFWorker,
    testNetworkConnectivity,
    testPDFJSAvailability,
    getBrowserInfo,
    pdfDebugLog
  };
  
  pdfDebugLog('DEBUG-INIT', '🔧 Enhanced PDF Debug Helper loaded - use window.pdfDebug for manual testing');
}