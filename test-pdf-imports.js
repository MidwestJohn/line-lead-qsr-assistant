#!/usr/bin/env node

/**
 * 🔍 PDF.js Import Validation Test
 * 
 * Tests PDF.js import configuration and worker setup
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 PDF.JS IMPORT VALIDATION TEST');
console.log('================================');
console.log('');

// Test 1: Package Dependencies
console.log('📦 TEST 1: Package Dependencies');
console.log('-------------------------------');

try {
    const packagePath = './package.json';
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    const pdfDeps = {
        'react-pdf': packageJson.dependencies['react-pdf'],
        'pdfjs-dist': packageJson.dependencies['pdfjs-dist']
    };
    
    console.log('Dependencies found:');
    Object.entries(pdfDeps).forEach(([pkg, version]) => {
        if (version) {
            console.log(`   ✅ ${pkg}: ${version}`);
        } else {
            console.log(`   ❌ ${pkg}: Not found`);
        }
    });
    
    // Check if both are present
    if (pdfDeps['react-pdf'] && pdfDeps['pdfjs-dist']) {
        console.log('✅ Both PDF packages are installed');
    } else {
        console.log('❌ Missing PDF packages - run: npm install react-pdf pdfjs-dist');
    }
    
} catch (error) {
    console.log(`❌ Failed to read package.json: ${error.message}`);
}

console.log('');

// Test 2: PDF Component Import Structure
console.log('🔧 TEST 2: PDF Component Import Structure');
console.log('-----------------------------------------');

const componentPath = './src/PDFViewerComponent.js';

try {
    const componentCode = fs.readFileSync(componentPath, 'utf8');
    
    const importTests = [
        { test: 'React PDF imports', pattern: /import.*{.*Document.*Page.*pdfjs.*}.*from.*['"]react-pdf['"]/, required: true },
        { test: 'CSS imports', pattern: /import.*['"]react-pdf\/dist\/Page\/.*\.css['"]/, required: true },
        { test: 'Worker configuration', pattern: /pdfjs\.GlobalWorkerOptions\.workerSrc\s*=/, required: true },
        { test: 'PDF.js version check', pattern: /pdfjs\.version/, required: true },
        { test: 'Worker availability check', pattern: /typeof pdfjs.*undefined/, required: true }
    ];
    
    let passed = 0;
    
    importTests.forEach(test => {
        const found = test.pattern.test(componentCode);
        if (found) {
            console.log(`   ✅ ${test.test} - Found`);
            passed++;
        } else {
            const status = test.required ? '❌' : '⚠️';
            console.log(`   ${status} ${test.test} - ${test.required ? 'Missing (Required)' : 'Not found (Optional)'}`);
        }
    });
    
    console.log(`📊 Import structure: ${passed}/${importTests.length} tests passed`);
    
} catch (error) {
    console.log(`❌ Failed to read component file: ${error.message}`);
}

console.log('');

// Test 3: Worker File Availability
console.log('📄 TEST 3: Worker File Availability');
console.log('-----------------------------------');

const workerPaths = [
    './public/pdf.worker.min.js',
    './node_modules/pdfjs-dist/build/pdf.worker.min.js',
    './node_modules/pdfjs-dist/build/pdf.worker.js'
];

let workerFound = false;

workerPaths.forEach(workerPath => {
    try {
        if (fs.existsSync(workerPath)) {
            const stats = fs.statSync(workerPath);
            console.log(`   ✅ ${workerPath} - Found (${(stats.size / 1024).toFixed(1)}KB)`);
            workerFound = true;
        } else {
            console.log(`   ❌ ${workerPath} - Not found`);
        }
    } catch (error) {
        console.log(`   ❌ ${workerPath} - Error: ${error.message}`);
    }
});

if (workerFound) {
    console.log('✅ Local worker files available');
} else {
    console.log('⚠️ No local worker files - will depend on CDN');
}

console.log('');

// Test 4: CSS Files
console.log('🎨 TEST 4: CSS Files');
console.log('--------------------');

const cssFiles = [
    './node_modules/react-pdf/dist/Page/AnnotationLayer.css',
    './node_modules/react-pdf/dist/Page/TextLayer.css'
];

cssFiles.forEach(cssFile => {
    try {
        if (fs.existsSync(cssFile)) {
            console.log(`   ✅ ${path.basename(cssFile)} - Available`);
        } else {
            console.log(`   ❌ ${path.basename(cssFile)} - Not found`);
        }
    } catch (error) {
        console.log(`   ❌ ${path.basename(cssFile)} - Error: ${error.message}`);
    }
});

console.log('');

// Test 5: Build Configuration
console.log('⚙️ TEST 5: Build Configuration');
console.log('------------------------------');

try {
    // Check if there's a craco config that might affect PDF.js
    const cracoConfigPath = './craco.config.js';
    if (fs.existsSync(cracoConfigPath)) {
        console.log('   ✅ CRACO config found - check for PDF.js specific configuration');
        
        const cracoConfig = fs.readFileSync(cracoConfigPath, 'utf8');
        if (cracoConfig.includes('pdf') || cracoConfig.includes('worker')) {
            console.log('   ⚠️ PDF/worker related configuration detected in CRACO');
        } else {
            console.log('   ℹ️ No PDF-specific CRACO configuration found');
        }
    } else {
        console.log('   ℹ️ No CRACO config found - using default Create React App configuration');
    }
    
    // Check package.json scripts
    const packageJson = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
    if (packageJson.scripts && packageJson.scripts.build) {
        console.log(`   ✅ Build script: ${packageJson.scripts.build}`);
    } else {
        console.log('   ❌ No build script found');
    }
    
} catch (error) {
    console.log(`   ❌ Build configuration check failed: ${error.message}`);
}

console.log('');

// Test 6: Common Import Issues Detection
console.log('🔍 TEST 6: Common Import Issues Detection');
console.log('----------------------------------------');

try {
    const componentCode = fs.readFileSync(componentPath, 'utf8');
    
    const issueTests = [
        { 
            issue: 'Missing react-pdf CSS imports', 
            pattern: /import.*['"]react-pdf\/dist\/esm\/Page.*\.css['"]/, 
            expected: true,
            fix: "Add: import 'react-pdf/dist/esm/Page/AnnotationLayer.css'; import 'react-pdf/dist/esm/Page/TextLayer.css';"
        },
        { 
            issue: 'Worker configured before imports', 
            pattern: /pdfjs\.GlobalWorkerOptions\.workerSrc.*=.*\n.*import/, 
            expected: false,
            fix: "Move worker configuration AFTER imports"
        },
        { 
            issue: 'Missing worker availability check', 
            pattern: /if.*!pdfjs\.GlobalWorkerOptions\.workerSrc/, 
            expected: true,
            fix: "Add: if (!pdfjs.GlobalWorkerOptions.workerSrc) { ... }"
        },
        { 
            issue: 'Using protocol-relative URL for worker', 
            pattern: /\/\/cdnjs\.cloudflare\.com/, 
            expected: false,
            fix: "Use https: instead of // for worker URL"
        }
    ];
    
    issueTests.forEach(test => {
        const found = test.pattern.test(componentCode);
        if (found === test.expected) {
            console.log(`   ✅ ${test.issue} - OK`);
        } else {
            console.log(`   ⚠️ ${test.issue} - Potential issue`);
            console.log(`      Fix: ${test.fix}`);
        }
    });
    
} catch (error) {
    console.log(`   ❌ Issue detection failed: ${error.message}`);
}

console.log('');

// Summary and Recommendations
console.log('📊 SUMMARY AND RECOMMENDATIONS');
console.log('==============================');
console.log('');

console.log('🔧 IMMEDIATE FIXES TO TRY:');
console.log('');
console.log('1. Clear node_modules and reinstall:');
console.log('   rm -rf node_modules package-lock.json');
console.log('   npm install');
console.log('');
console.log('2. Verify imports in browser console:');
console.log('   Open browser dev tools');
console.log('   Type: console.log(pdfjs.version)');
console.log('   Should show version number, not "undefined"');
console.log('');
console.log('3. Test worker configuration:');
console.log('   Type: console.log(pdfjs.GlobalWorkerOptions.workerSrc)');
console.log('   Should show worker URL, not undefined');
console.log('');
console.log('4. If still failing, try alternative import:');
console.log('   import * as pdfjs from "pdfjs-dist";');
console.log('   import { Document, Page } from "react-pdf";');
console.log('');

console.log('🎯 SUCCESS CRITERIA:');
console.log('   ✅ No "pdfjs is not defined" errors in console');
console.log('   ✅ PDF.js version logs correctly');
console.log('   ✅ Worker URL is accessible');
console.log('   ✅ PDF preview modal opens (even if loading fails)');
console.log('');

console.log('🏁 PDF.js import validation complete!');
console.log('Run this test after each fix to verify progress.');