# -*- coding: utf-8 -*-
#在gis python窗
# execfile(r'C:\4code\3lot\3-export_by_xian.py')
# 

import os, shutil, sys
import arcpy

SCRIPT_DIR = r"C:\4code\3lot"
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from project_config import (
    GDB, ZYY_TARGET_FC_NAME, TEMPLATE_DIR_111, TEMPLATE_DIR_114,
    OUTPUT_BASE, COUNTY_DBF, PROJECT_114_PRJ,
    COUNTIES_114E as CONFIG_COUNTIES_114E,
)

reload(sys)
sys.setdefaultencoding('utf-8')

gdb = GDB
target_fc = gdb + u"/" + ZYY_TARGET_FC_NAME
template_dir_111 = TEMPLATE_DIR_111
template_dir_114 = TEMPLATE_DIR_114
output_base = OUTPUT_BASE
SKIP_FIELDS = {"OBJECTID", "SHAPE", "SHAPE_LENGTH", "SHAPE_AREA"}
COUNTIES_114E = set(CONFIG_COUNTIES_114E)


def _text(val):
    if val is None:
        return u""
    try:
        return unicode(val).strip()
    except Exception:
        return str(val).strip()

# 读取县代码→名称映射
CODE_NAME_MAP = {}
if arcpy.Exists(COUNTY_DBF):
    with arcpy.da.SearchCursor(COUNTY_DBF, [u"县代码", u"县"]) as cur:
        for r in cur:
            if r[0] and r[1]:
                CODE_NAME_MAP[_text(r[0])] = _text(r[1])


def _project_fc_if_needed(fc, xian_name, tmp_name):
    if xian_name not in COUNTIES_114E:
        return fc
    if not os.path.exists(PROJECT_114_PRJ):
        print u"  警告：114E投影文件不存在，跳过投影"
        return fc
    tmp_fc = os.path.join(gdb, tmp_name)
    if arcpy.Exists(tmp_fc):
        arcpy.Delete_management(tmp_fc)
    sr = arcpy.SpatialReference()
    with open(PROJECT_114_PRJ, "r") as f:
        sr.loadFromString(f.read())
    arcpy.Project_management(fc, tmp_fc, sr)
    print u"  已投影到CGCS2000_3_Degree_GK_CM_114E"
    return tmp_fc


def export_by_xian():
    arcpy.env.overwriteOutput = True

    if not arcpy.Exists(target_fc):
        print u"错误：目标要素类不存在！"
        return
    if not os.path.exists(template_dir_111):
        print u"错误：模版目录不存在！"
        return

    xian_vals = sorted(set(
        r[0].strip() for r in arcpy.da.SearchCursor(target_fc, ["XIAN"]) if r[0]
    ))
    print u"共 %d 个县: %s" % (len(xian_vals), u", ".join(xian_vals))

    for xian in xian_vals:
        xian_name = CODE_NAME_MAP.get(xian, xian)
        print u"\n--- %s (%s) ---" % (xian, xian_name)

        cur_template_dir = template_dir_114 if xian_name in COUNTIES_114E else template_dir_111
        if not os.path.exists(cur_template_dir):
            print u"  错误：模版目录不存在！"
            continue
        out_dir = os.path.join(output_base, xian_name)
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        shutil.copytree(cur_template_dir, out_dir)
        print u"  模版已复制（含子目录及数据）"

        fmap = arcpy.FieldMappings()
        for f in arcpy.ListFields(target_fc):
            if f.name.upper() in SKIP_FIELDS:
                continue
            fm = arcpy.FieldMap()
            fm.addInputField(target_fc, f.name)
            fmap.addFieldMap(fm)

        arcpy.FeatureClassToFeatureClass_conversion(
            target_fc, gdb, "tmp_" + xian,
            u"XIAN = '%s'" % xian, field_mapping=fmap
        )

        temp_fc = os.path.join(gdb, "tmp_" + xian)
        cnt = int(arcpy.GetCount_management(temp_fc).getOutput(0))
        if cnt == 0:
            arcpy.Delete_management(temp_fc)
            print u"  跳过（无数据）"
            continue
        print u"  筛选 %d 条" % cnt

        export_fc = _project_fc_if_needed(temp_fc, xian_name, "tmp_xian_114_" + xian)

        shp_dir = os.path.join(out_dir, u"林地图斑")
        # 删除整个林地图斑目录（避免 .sr.lock 文件权限问题）
        for root2, _, files2 in os.walk(shp_dir):
            for f2 in files2:
                try:
                    os.chmod(os.path.join(root2, f2), 0o777)
                except:
                    pass
        shutil.rmtree(shp_dir, ignore_errors=True)

        os.makedirs(shp_dir)
        arcpy.FeatureClassToFeatureClass_conversion(export_fc, shp_dir, "ZZY")
        print u"  已导出至 " + os.path.join(shp_dir, "ZZY.shp")

        zzy_shp = os.path.join(shp_dir, "ZZY.shp")
        to_del = []
        for f in arcpy.ListFields(zzy_shp):
            if f.name.upper() in ("SHAPE_LENGTH", "SHAPE_LENG", "SHAPE_AREA"):
                to_del.append(f.name)
        if to_del:
            try:
                arcpy.DeleteField_management(zzy_shp, to_del)
                print u"  已删除字段: " + u", ".join(to_del)
            except Exception:
                print u"  删除失败（系统字段，保留）"

        if export_fc != temp_fc and arcpy.Exists(export_fc):
            arcpy.Delete_management(export_fc)
        arcpy.Delete_management(temp_fc)

    print u"\n全部导出完成！"


# 直接执行
print "=" * 60
print u"  ZYY 分县导出工具"
print u"  目标要素类: " + target_fc
print "=" * 60
export_by_xian()
