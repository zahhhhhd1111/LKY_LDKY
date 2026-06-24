# -*- coding: utf-8 -*-
# 在 ArcMap Python 窗口运行：
# execfile(r'C:\4code\3lot\7-更新红线面积字段.py')
#
# 作用：用 3/4 号脚本已导出的分县 ZYY.shp 与 XMHX.shp 的面积字段值作为标准，
#       回写到源要素类「多县合并红线_擦除历史」的两个面积字段：
#         XMPFNYTDMJ ← 对应县 XMHX.shp 的 XMPFNYTDMJ（合并后平面几何面积）
#         NSYLDMJ    ← 对应县 ZYY.shp 的 XBMJ 合计
#       只更新已有字段，不新增字段。

import os, sys
import arcpy

SCRIPT_DIR = r"C:\4code\3lot"
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from project_config import (
    GDB, XMHX_SOURCE_FC_NAME, OUTPUT_BASE, county_name,
)

reload(sys)
sys.setdefaultencoding('utf-8')

gdb = GDB
source_fc = gdb + u"/" + XMHX_SOURCE_FC_NAME
output_base = OUTPUT_BASE

XIAN_FIELD = u"XIAN"
AREA_GEOM_FIELD = u"XMPFNYTDMJ"   # 项目拟使用林地面积（XMHX 几何面积）
AREA_USE_FIELD = u"NSYLDMJ"        # 拟使用林地面积（ZYY 的 XBMJ 合计）


def _log(msg):
    try:
        arcpy.AddMessage(msg)
    except Exception:
        try:
            sys.__stdout__.write((unicode(msg) + u"\n").encode("utf-8"))
        except Exception:
            pass


def _text(val):
    if val is None:
        return u""
    try:
        return unicode(val).strip()
    except Exception:
        return str(val).strip()


def _num(val):
    s = _text(val)
    if not s:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def _read_xmhx_area(xmhx_shp):
    """读取分县 XMHX.shp 的 XMPFNYTDMJ（1 个小班，取其值；多个则求和）。"""
    if not arcpy.Exists(xmhx_shp):
        return None
    total = 0.0
    found = False
    with arcpy.da.SearchCursor(xmhx_shp, [AREA_GEOM_FIELD]) as cur:
        for row in cur:
            if row[0] is not None:
                total += _num(row[0])
                found = True
    return round(total, 4) if found else None


def _read_zyy_xbmj_sum(zyy_shp):
    """读取分县 ZYY.shp 的 XBMJ 合计。"""
    if not arcpy.Exists(zyy_shp):
        return None
    total = 0.0
    with arcpy.da.SearchCursor(zyy_shp, ["XBMJ"]) as cur:
        for row in cur:
            if row[0] is not None:
                total += _num(row[0])
    return round(total, 4)


def update_redline_areas():
    arcpy.env.overwriteOutput = True

    if not arcpy.Exists(source_fc):
        _log(u"错误：源要素类不存在！ " + source_fc)
        return

    fields = {f.name for f in arcpy.ListFields(source_fc)}
    for fld in (XIAN_FIELD, AREA_GEOM_FIELD, AREA_USE_FIELD):
        if fld not in fields:
            _log(u"错误：源要素类缺少字段 %s，未做改动" % fld)
            return

    _log(u"源要素类: " + source_fc)
    _log(u"按县回写 %s / %s 两个面积字段" % (AREA_GEOM_FIELD, AREA_USE_FIELD))
    _log(u"-" * 60)

    updated = 0
    missing = []
    with arcpy.da.UpdateCursor(source_fc, [XIAN_FIELD, AREA_GEOM_FIELD, AREA_USE_FIELD]) as cur:
        for row in cur:
            xian = _text(row[0])
            cname = county_name(xian)
            xmhx_shp = os.path.join(output_base, cname, u"项目红线", "XMHX.shp")
            zyy_shp = os.path.join(output_base, cname, u"林地图斑", "ZZY.shp")

            geom_area = _read_xmhx_area(xmhx_shp)
            use_area = _read_zyy_xbmj_sum(zyy_shp)

            if geom_area is None or use_area is None:
                missing.append(u"%s(%s)" % (xian, cname))
                _log(u"  跳过 %s(%s)：找不到导出的 XMHX/ZZY" % (xian, cname))
                continue

            row[1] = geom_area
            row[2] = use_area
            cur.updateRow(row)
            updated += 1
            _log(u"  %s(%s): XMPFNYTDMJ=%.4f  NSYLDMJ=%.4f" %
                 (xian, cname, geom_area, use_area))

    _log(u"-" * 60)
    _log(u"完成：更新 %d 条" % updated)
    if missing:
        _log(u"未更新（缺导出数据）: %s" % u", ".join(missing))


# 直接执行
_log("=" * 60)
_log(u"  回写「多县合并红线_擦除历史」面积字段")
_log(u"  标准：分县导出的 ZYY.shp(XBMJ合计) / XMHX.shp(XMPFNYTDMJ)")
_log("=" * 60)
update_redline_areas()
