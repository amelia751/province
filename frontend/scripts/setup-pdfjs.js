#!/usr/bin/env node

/**
 * Setup script for PDF.js worker file
 * Copies the worker from node_modules to public directory
 */

const fs = require('fs');
const path = require('path');

const source = path.join(__dirname, '../node_modules/pdfjs-dist/build/pdf.worker.min.mjs');
const dest = path.join(__dirname, '../public/pdf.worker.min.mjs');

console.log('📄 Setting up PDF.js worker...');

// Check if source exists
if (!fs.existsSync(source)) {
  console.error('❌ Error: PDF.js worker not found in node_modules');
  console.error('   Run: npm install pdfjs-dist');
  process.exit(1);
}

// Create public directory if it doesn't exist
const publicDir = path.dirname(dest);
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
  console.log('✅ Created public directory');
}

// Copy worker file
try {
  fs.copyFileSync(source, dest);
  console.log('✅ PDF.js worker copied successfully');
  console.log(`   From: ${source}`);
  console.log(`   To:   ${dest}`);
} catch (error) {
  console.error('❌ Error copying worker file:', error.message);
  process.exit(1);
}

console.log('✨ PDF.js setup complete!');
