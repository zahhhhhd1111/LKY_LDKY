// read_xlsx.js - Read ZYY字段名与属性.xlsx using Node.js with the 'xlsx' package
//
// Setup:
//   cd c:\4code\3lot
//   npm init -y
//   npm install xlsx
//
// Then run: node "c:\4code\3lot\read_xlsx.js"

const XLSX = require('xlsx');
const path = 'c:\\4code\\3lot\\ZYY字段名与属性.xlsx';

try {
    const workbook = XLSX.readFile(path, {cellDates: true});
    workbook.SheetNames.forEach(function(name) {
        console.log('\n=== Sheet: ' + name + ' ===');
        const sheet = workbook.Sheets[name];
        const data = XLSX.utils.sheet_to_json(sheet, {header: 1});
        data.forEach(function(row, i) {
            console.log('Row ' + (i+1) + ': ' + JSON.stringify(row));
        });
    });
} catch(e) {
    console.error('Error:', e.message);
}
