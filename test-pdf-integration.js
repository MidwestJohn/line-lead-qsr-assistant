// Test script to verify PDF preview integration
// Run this in browser console on http://localhost:3000

console.log('🧪 Testing PDF Preview Integration...\n');

// Test 1: Check if DocumentList component loads
const testDocumentListLoading = () => {
  console.log('1. Testing DocumentList component loading...');
  
  // Navigate to documents page
  const documentsButton = document.querySelector('[title="Upload Manual"], [aria-label="Show documents"]');
  if (documentsButton) {
    console.log('   ✅ Documents button found');
    documentsButton.click();
    
    setTimeout(() => {
      const documentList = document.querySelector('.document-list-container');
      if (documentList) {
        console.log('   ✅ DocumentList component loaded');
        testPDFPreviewButtons();
      } else {
        console.log('   ❌ DocumentList component not found');
      }
    }, 1000);
  } else {
    console.log('   ❌ Documents button not found');
  }
};

// Test 2: Check for PDF preview buttons
const testPDFPreviewButtons = () => {
  console.log('\n2. Testing PDF preview buttons...');
  
  const documentCards = document.querySelectorAll('.document-card');
  console.log(`   Found ${documentCards.length} document cards`);
  
  let pdfCount = 0;
  let previewButtonCount = 0;
  
  documentCards.forEach((card, index) => {
    const filename = card.querySelector('.document-name')?.textContent;
    const previewButton = card.querySelector('.preview-button');
    const eyeIcon = card.querySelector('.preview-icon');
    
    console.log(`   Document ${index + 1}: ${filename}`);
    
    if (filename && filename.toLowerCase().endsWith('.pdf')) {
      pdfCount++;
      console.log(`     📄 PDF file detected`);
      
      if (previewButton) {
        previewButtonCount++;
        console.log(`     ✅ Preview button found`);
        
        if (eyeIcon) {
          console.log(`     ✅ Eye icon found`);
        } else {
          console.log(`     ❌ Eye icon missing`);
        }
      } else {
        console.log(`     ❌ Preview button missing for PDF`);
      }
    } else {
      console.log(`     📄 Non-PDF file`);
      if (previewButton) {
        console.log(`     ❌ Preview button found for non-PDF (should not exist)`);
      } else {
        console.log(`     ✅ No preview button for non-PDF (correct)`);
      }
    }
  });
  
  console.log(`\n   Summary: ${previewButtonCount}/${pdfCount} PDF files have preview buttons`);
  
  if (previewButtonCount > 0) {
    testModalOpening();
  }
};

// Test 3: Test modal opening
const testModalOpening = () => {
  console.log('\n3. Testing PDF modal opening...');
  
  const firstPreviewButton = document.querySelector('.preview-button');
  if (firstPreviewButton) {
    console.log('   ✅ First preview button found');
    
    // Click the preview button
    firstPreviewButton.click();
    
    setTimeout(() => {
      const modal = document.querySelector('.pdf-modal-overlay');
      const modalContainer = document.querySelector('.pdf-modal-container');
      
      if (modal && modalContainer) {
        console.log('   ✅ PDF modal opened successfully');
        testModalContent();
      } else {
        console.log('   ❌ PDF modal failed to open');
      }
    }, 1000);
  } else {
    console.log('   ❌ No preview buttons found to test');
  }
};

// Test 4: Test modal content and functionality
const testModalContent = () => {
  console.log('\n4. Testing PDF modal content...');
  
  const modalHeader = document.querySelector('.pdf-modal-header');
  const filename = document.querySelector('.pdf-filename');
  const downloadButton = document.querySelector('.pdf-modal-btn-secondary');
  const closeButton = document.querySelector('.pdf-modal-btn-close');
  const controlBar = document.querySelector('.pdf-modal-controls');
  const content = document.querySelector('.pdf-modal-content');
  
  // Check header elements
  if (modalHeader) {
    console.log('   ✅ Modal header found');
  } else {
    console.log('   ❌ Modal header missing');
  }
  
  if (filename) {
    console.log(`   ✅ Filename displayed: ${filename.textContent}`);
  } else {
    console.log('   ❌ Filename missing');
  }
  
  if (downloadButton) {
    console.log('   ✅ Download button found');
  } else {
    console.log('   ❌ Download button missing');
  }
  
  if (closeButton) {
    console.log('   ✅ Close button found');
  } else {
    console.log('   ❌ Close button missing');
  }
  
  if (controlBar) {
    console.log('   ✅ Control bar found');
  } else {
    console.log('   ❌ Control bar missing');
  }
  
  if (content) {
    console.log('   ✅ Content area found');
    
    // Check for PDF loading
    setTimeout(() => {
      const pdfPage = document.querySelector('.pdf-modal-page');
      const loadingSpinner = document.querySelector('.pdf-modal-spinner');
      const errorMessage = document.querySelector('.pdf-modal-error');
      
      if (pdfPage) {
        console.log('   ✅ PDF page rendered successfully');
      } else if (loadingSpinner) {
        console.log('   ⏳ PDF still loading...');
      } else if (errorMessage) {
        console.log('   ❌ PDF failed to load');
      } else {
        console.log('   ⏳ PDF loading state unclear');
      }
      
      testModalClosing();
    }, 3000);
  } else {
    console.log('   ❌ Content area missing');
  }
};

// Test 5: Test modal closing
const testModalClosing = () => {
  console.log('\n5. Testing PDF modal closing...');
  
  const closeButton = document.querySelector('.pdf-modal-btn-close');
  if (closeButton) {
    closeButton.click();
    
    setTimeout(() => {
      const modal = document.querySelector('.pdf-modal-overlay');
      if (!modal || modal.style.display === 'none') {
        console.log('   ✅ Modal closed successfully');
        printTestSummary();
      } else {
        console.log('   ❌ Modal failed to close');
        printTestSummary();
      }
    }, 500);
  } else {
    console.log('   ❌ Close button not found');
    printTestSummary();
  }
};

// Print test summary
const printTestSummary = () => {
  console.log('\n🎯 Test Summary:');
  console.log('════════════════════════════════════════');
  console.log('✅ Integration tests completed');
  console.log('📋 Check console output above for detailed results');
  console.log('🔍 Visual inspection recommended for:');
  console.log('   - Button styling and hover states');
  console.log('   - PDF rendering quality');
  console.log('   - Mobile responsiveness');
  console.log('   - Keyboard navigation');
  console.log('════════════════════════════════════════');
};

// Start the test
console.log('📋 PDF Preview Integration Test');
console.log('═══════════════════════════════════════');
console.log('This will test the DocumentList PDF preview functionality');
console.log('Make sure you are on http://localhost:3000\n');

// Wait a moment for the page to load, then start testing
setTimeout(testDocumentListLoading, 1000);

// Export functions for manual testing
window.testPDFIntegration = {
  testDocumentListLoading,
  testPDFPreviewButtons,
  testModalOpening,
  testModalContent,
  testModalClosing,
  printTestSummary
};