// Node.js script to verify PDF setup before deployment
const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying PDF setup...\n');

// Check package.json for required dependencies
console.log('1. Checking package.json dependencies...');
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const requiredDeps = ['react-pdf', 'pdfjs-dist'];

requiredDeps.forEach(dep => {
  if (packageJson.dependencies[dep]) {
    console.log(`   ✅ ${dep}: ${packageJson.dependencies[dep]}`);
  } else {
    console.log(`   ❌ ${dep}: Missing`);
  }
});

// Check if test PDFs exist
console.log('\n2. Checking test PDF files...');
const testPDFs = ['public/test_fryer_manual.pdf', 'public/test_grill_manual.pdf'];

testPDFs.forEach(pdfPath => {
  if (fs.existsSync(pdfPath)) {
    const stats = fs.statSync(pdfPath);
    console.log(`   ✅ ${pdfPath}: ${(stats.size / 1024).toFixed(1)}KB`);
  } else {
    console.log(`   ❌ ${pdfPath}: Missing`);
  }
});

// Check if PDF components exist
console.log('\n3. Checking PDF components...');
const components = [
  'src/PDFPreview.js',
  'src/PDFPreview.css',
  'src/PDFTest.js'
];

components.forEach(componentPath => {
  if (fs.existsSync(componentPath)) {
    console.log(`   ✅ ${componentPath}: Found`);
  } else {
    console.log(`   ❌ ${componentPath}: Missing`);
  }
});

// Check PDF.js worker configuration in PDFPreview.js
console.log('\n4. Checking PDF.js worker configuration...');
if (fs.existsSync('src/PDFPreview.js')) {
  const pdfPreviewContent = fs.readFileSync('src/PDFPreview.js', 'utf8');
  
  if (pdfPreviewContent.includes('cdnjs.cloudflare.com/ajax/libs/pdf.js')) {
    console.log('   ✅ PDF.js worker configured to use CDN');
  } else {
    console.log('   ❌ PDF.js worker CDN configuration not found');
  }
  
  if (pdfPreviewContent.includes('renderTextLayer={false}')) {
    console.log('   ✅ Text layer disabled for performance');
  } else {
    console.log('   ❌ Text layer performance optimization not found');
  }
  
  if (pdfPreviewContent.includes('renderAnnotationLayer={false}')) {
    console.log('   ✅ Annotation layer disabled for performance');
  } else {
    console.log('   ❌ Annotation layer performance optimization not found');
  }
} else {
  console.log('   ❌ PDFPreview.js not found');
}

console.log('\n🎯 PDF setup verification complete!\n');

// Summary
const allChecks = [
  packageJson.dependencies['react-pdf'],
  packageJson.dependencies['pdfjs-dist'],
  fs.existsSync('public/test_fryer_manual.pdf'),
  fs.existsSync('public/test_grill_manual.pdf'),
  fs.existsSync('src/PDFPreview.js'),
  fs.existsSync('src/PDFPreview.css'),
  fs.existsSync('src/PDFTest.js')
];

const passedChecks = allChecks.filter(Boolean).length;
const totalChecks = allChecks.length;

if (passedChecks === totalChecks) {
  console.log('✅ All checks passed! PDF setup is ready for testing.');
} else {
  console.log(`⚠️  ${passedChecks}/${totalChecks} checks passed. Some issues need attention.`);
}

console.log('\n📝 Next steps:');
console.log('   1. Open http://localhost:3000 in browser');
console.log('   2. Click "PDF" button to access test interface');
console.log('   3. Verify PDFs load and display correctly');
console.log('   4. Test navigation on multi-page PDFs');
console.log('   5. Check responsive behavior on mobile');