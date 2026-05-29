# -*- coding: utf-8 -*-
"""Shared project paths and county-level projection settings."""

PROJECT_DIR = u"C:/4code/3lot"
GDB = PROJECT_DIR + u"/输出结果.gdb"

# Update these feature class names when the source data is replaced.
ZYY_SOURCE_FC_NAME = u"多县ZYY空间连接保护区"
ZYY_TARGET_FC_NAME = u"多县ZYY_标准字段版"
XMHX_SOURCE_FC_NAME = u"wuxianhebing_cachu"

TEMPLATE_DIR_111 = PROJECT_DIR + u"/模版-1009征占用林地数据模板CGCG2000_111"
TEMPLATE_DIR_114 = PROJECT_DIR + u"/模版-1009征占用林地数据模板CGCG2000_114"
OUTPUT_BASE = u"C:/Users/zhong/Downloads/work file/五个垸和防护堤/结果/按县导出结果"

STANDARD_FILE = PROJECT_DIR + u"/ZYY字段属性标准设置.MD"
COUNTY_DBF = PROJECT_DIR + u"/县名.dbf"
PROJECT_114_PRJ = TEMPLATE_DIR_114 + u"/林地图斑/ZZY.prj"

# County names or 6-digit XIAN codes whose exports should use CGCS2000 3-degree GK CM 114E.
# Current data check: 湘阴县 is east of 112.5E; 华容县 project polygons are west of 112.5E.
COUNTIES_114E = set([u"湘阴县", u"430624"])
