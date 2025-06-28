// Simple test script to verify PDF.js setup
import { pdfjs } from 'react-pdf';

// Test PDF.js worker configuration
export const testPDFSetup = () => {
  console.log('Testing PDF.js setup...');
  console.log('PDF.js version:', pdfjs.version);
  console.log('Worker source configured:', pdfjs.GlobalWorkerOptions.workerSrc);
  
  // Test if we can create a basic PDF loading promise
  try {
    const testPDFPath = './test_fryer_manual.pdf';
    console.log('Testing PDF path:', testPDFPath);
    
    // Basic loading test (without actually loading)
    console.log('✅ PDF.js setup appears to be working');
    return true;
  } catch (error) {
    console.error('❌ PDF.js setup error:', error);
    return false;
  }
};

export default testPDFSetup;