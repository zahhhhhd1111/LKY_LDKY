# -*- coding: utf-8 -*-
"""Shared project paths and county-level projection settings."""

import os

try:
    text_type = unicode
except NameError:
    text_type = str

PROJECT_DIR = u"C:/4code/3lot"
GDB = PROJECT_DIR + u"/输出结果.gdb"

# Update these feature class names when the source data is replaced.
ZYY_SOURCE_FC_NAME = u"多县ZYY空间连接保护区"
# 调减后数据：已用「二期工程调减的地块」擦除。脚本1/2 跳过（target 已标准化且 XBMJ 仍准确）。
ZYY_TARGET_FC_NAME = u"ZYY_擦除调减"
XMHX_SOURCE_FC_NAME = u"红线_擦除调减"
COUNTY_BOUNDARY_FC_NAME = u"重点垸三调县界_M"

TEMPLATE_DIR_108 = PROJECT_DIR + u"/模版-1009征占用林地数据模板CGCG2000_108"
TEMPLATE_DIR_111 = PROJECT_DIR + u"/模版-1009征占用林地数据模板CGCG2000_111"
TEMPLATE_DIR_114 = PROJECT_DIR + u"/模版-1009征占用林地数据模板CGCG2000_114"
OUTPUT_BASE = u"C:/Users/zhong/Downloads/work file/五个垸和防护堤/结果/按县导出结果"

STANDARD_FILE = PROJECT_DIR + u"/ZYY字段属性标准设置.MD"

TEMPLATE_DIRS = {
    u"108": TEMPLATE_DIR_108,
    u"111": TEMPLATE_DIR_111,
    u"114": TEMPLATE_DIR_114,
}

PROJECT_PRJ = {
    u"108": TEMPLATE_DIR_108 + u"/林地图斑/ZZY.prj",
    u"111": TEMPLATE_DIR_111 + u"/林地图斑/ZZY.prj",
    u"114": TEMPLATE_DIR_114 + u"/林地图斑/ZZY.prj",
}

DEFAULT_ZONE = u"111"
COUNTY_TABLE_TITLE = u"县代码与投影带"


def _text(val):
    if val is None:
        return u""
    return text_type(val).strip()


def _norm_code(val, width=None):
    s = _text(val)
    if not s:
        return u""
    if s.isdigit() and width:
        return s.zfill(width)
    return s


def _read_standard_text():
    if not os.path.exists(STANDARD_FILE):
        return u""
    with open(STANDARD_FILE, "rb") as f:
        raw = f.read()
    if isinstance(raw, text_type):
        return raw
    return raw.decode("utf-8")


def _md_table_rows(title):
    lines = _read_standard_text().splitlines()
    start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(u"### ") and title in line:
            start = i + 1
            break
    if start < 0:
        return []

    table_lines = []
    for line in lines[start:]:
        s = line.strip()
        if s.startswith(u"---") or s.startswith(u"### "):
            break
        if s.startswith(u"|") and s.endswith(u"|"):
            table_lines.append(s)

    headers = []
    rows = []
    for line in table_lines:
        parts = [p.strip() for p in line.split(u"|")[1:-1]]
        if not parts:
            continue
        if all(set(p) <= set(u"-: ") for p in parts if p):
            continue
        if not headers:
            headers = parts
            continue
        row = {}
        for idx, header in enumerate(headers):
            row[header] = parts[idx] if idx < len(parts) else u""
        rows.append(row)
    return rows


def load_county_settings():
    code_to_name = {}
    name_to_code = {}
    code_to_zone = {}
    name_to_zone = {}

    for row in _md_table_rows(COUNTY_TABLE_TITLE):
        name = _text(row.get(u"县", row.get(u"县（市、区）", u"")))
        code = _norm_code(row.get(u"县代码", u""), 6)
        zone = _text(row.get(u"投影带", row.get(u"中央经线", u""))).replace(u"E", u"")
        if zone not in TEMPLATE_DIRS:
            zone = DEFAULT_ZONE
        if code and name:
            code_to_name[code] = name
            name_to_code[name] = code
        if code:
            code_to_zone[code] = zone
        if name:
            name_to_zone[name] = zone

    return code_to_name, name_to_code, code_to_zone, name_to_zone


COUNTY_CODE_TO_NAME, COUNTY_NAME_TO_CODE, COUNTY_CODE_TO_ZONE, COUNTY_NAME_TO_ZONE = load_county_settings()


def county_name(xian):
    x = _text(xian)
    return COUNTY_CODE_TO_NAME.get(_norm_code(x, 6), x)


def county_zone(xian_or_name):
    x = _text(xian_or_name)
    code = _norm_code(x, 6)
    if code in COUNTY_CODE_TO_ZONE:
        return COUNTY_CODE_TO_ZONE[code]
    name = COUNTY_CODE_TO_NAME.get(code, x)
    return COUNTY_NAME_TO_ZONE.get(name, DEFAULT_ZONE)


def template_dir_for_county(xian_or_name):
    return TEMPLATE_DIRS.get(county_zone(xian_or_name), TEMPLATE_DIRS[DEFAULT_ZONE])


def prj_path_for_zone(zone):
    return PROJECT_PRJ.get(_text(zone), PROJECT_PRJ[DEFAULT_ZONE])
