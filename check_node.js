// Simple script to test if node works
const fs = require('fs');
const path = require('path');

const xlsxPath = 'c:\\4code\\3lot\\ZYY字段名与属性.xlsx';
console.log('File exists:', fs.existsSync(xlsxPath));
console.log('File size:', fs.statSync(xlsxPath).size);

// xlsx is a zip file, try to read the zip structure
try {
  // Read first few bytes to verify it's a zip
  const fd = fs.openSync(xlsxPath, 'r');
  const buf = Buffer.alloc(4);
  fs.readSync(fd, buf, 0, 4, 0);
  console.log('First 4 bytes (ZIP signature):', buf.toString('hex'));
  fs.closeSync(fd);
} catch(e) {
  console.log('Error reading file:', e.message);
}
