import zipfile
import xml.etree.ElementTree as ET
import os
import sys

path = r'c:\4code\3lot\ZYY字段名与属性.xlsx'

def parse_xlsx(filepath):
    with zipfile.ZipFile(filepath, 'r') as z:
        # List all files in the archive
        print("=== Files in xlsx archive ===")
        for name in z.namelist():
            print(f"  {name}")
        print()

        # Parse shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.parse(z.open('xl/sharedStrings.xml'))
            root = tree.getroot()
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in root.findall('.//s:si', ns):
                texts = []
                for t in si.findall('.//s:t', ns):
                    if t.text:
                        texts.append(t.text)
                shared_strings.append(''.join(texts))
            print(f"=== Shared Strings ({len(shared_strings)}) ===")
            for i, s in enumerate(shared_strings):
                print(f"  [{i}] {s}")
            print()

        # Parse all worksheets
        sheet_count = 0
        for name in z.namelist():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                sheet_count += 1
                print(f"=== Worksheet: {name} ===")
                tree = ET.parse(z.open(name))
                root = tree.getroot()
                ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
                      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

                # Parse sheet data
                sheet_data = root.find('.//s:sheetData', ns)
                if sheet_data is not None:
                    for row in sheet_data.findall('s:row', ns):
                        row_num = row.get('r', '')
                        cells = []
                        for c in row.findall('s:c', ns):
                            cell_ref = c.get('r', '')
                            cell_type = c.get('t', '')
                            cell_value_elem = c.find('s:v', ns)
                            cell_value = cell_value_elem.text if cell_value_elem is not None else ''

                            # If shared string (type 's'), look up in shared strings
                            if cell_type == 's' and cell_value:
                                try:
                                    cell_value = shared_strings[int(cell_value)]
                                except (ValueError, IndexError):
                                    pass

                            cells.append(f"{cell_ref}={cell_value}")
                        print(f"  Row {row_num}: {' | '.join(cells)}")
                print()

        # Parse workbook.xml for sheet names
        if 'xl/workbook.xml' in z.namelist():
            print("=== Workbook Info ===")
            tree = ET.parse(z.open('xl/workbook.xml'))
            root = tree.getroot()
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
                  'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
            for sheet in root.findall('.//s:sheet', ns):
                name = sheet.get('name', '')
                sheet_id = sheet.get('sheetId', '')
                print(f"  Sheet: '{name}' (id={sheet_id})")
            print()

        if sheet_count == 0:
            print("No worksheet XML files found! Checking alternate paths...")
            # Try other possible locations
            for name in z.namelist():
                if 'sheet' in name.lower() and name.endswith('.xml'):
                    print(f"  Found potential sheet: {name}")
                    try:
                        content = z.read(name).decode('utf-8')
                        print(f"  Content (first 500 chars): {content[:500]}")
                    except:
                        print(f"  Could not read {name}")

if __name__ == '__main__':
    parse_xlsx(path)
