# -*- coding: utf-8 -*-
"""读取ZYY字段名与属性.xlsx，兼容ArcGIS Python 2.7"""
import zipfile
import xml.etree.ElementTree as ET

path = u'c:\\4code\\3lot\\ZYY字段名与属性.xlsx'
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

with zipfile.ZipFile(path, 'r') as z:
    # 读取共享字符串表
    shared_strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.parse(z.open('xl/sharedStrings.xml'))
        root = tree.getroot()
        for si in root.findall('.//s:si', ns):
            texts = []
            for t in si.findall('.//s:t', ns):
                if t.text:
                    texts.append(t.text)
            shared_strings.append(''.join(texts))

    # 读取工作表
    for name in z.namelist():
        if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
            print(u"\n=== {} ===".format(name))
            tree = ET.parse(z.open(name))
            root = tree.getroot()
            sheet_data = root.find('.//s:sheetData', ns)
            if sheet_data is not None:
                for row in sheet_data.findall('s:row', ns):
                    cells = []
                    for c in row.findall('s:c', ns):
                        cell_ref = c.get('r', '')
                        cell_type = c.get('t', '')
                        cell_value_elem = c.find('s:v', ns)
                        cell_value = cell_value_elem.text if cell_value_elem is not None else ''
                        if cell_type == 's' and cell_value:
                            try:
                                cell_value = shared_strings[int(cell_value)]
                            except (ValueError, IndexError):
                                pass
                        cells.append(cell_value)
                    print(u' | '.join(cells))
