# -*- coding: utf-8 -*-
#在gis python窗口运行：
#execfile(r'C:\4code\3lot\4-export_xmhx_by_xian.py')

import os, shutil, sys
import arcpy

SCRIPT_DIR = r"C:\4code\3lot"
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from project_config import (
    GDB, XMHX_SOURCE_FC_NAME, TEMPLATE_DIR_111, OUTPUT_BASE,
    COUNTY_DBF, PROJECT_114_PRJ, COUNTIES_114E as CONFIG_COUNTIES_114E,
)

reload(sys)
sys.setdefaultencoding('utf-8')

gdb = GDB
source_fc = gdb + u"/" + XMHX_SOURCE_FC_NAME
template_dir_111 = TEMPLATE_DIR_111
output_base = OUTPUT_BASE
SKIP_FIELDS = {"OBJECTID", "SHAPE", "SHAPE_LENGTH", "SHAPE_AREA"}
COUNTIES_114E = set(CONFIG_COUNTIES_114E)

# 读取县代码→名称映射
CODE_NAME_MAP = {}
if arcpy.Exists(COUNTY_DBF):
    with arcpy.da.SearchCursor(COUNTY_DBF, [u"县代码", u"县"]) as cur:
        for r in cur:
            if r[0] and r[1]:
                CODE_NAME_MAP[unicode(r[0]).strip()] = unicode(r[1]).strip()


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


def export_xmhx_by_xian():
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = gdb

    # 清理上一轮残留暂存
    for tmp in arcpy.ListFeatureClasses("tmp_xmhx_*") + arcpy.ListTables("tmp_xmhx_*"):
        try:
            arcpy.Delete_management(tmp)
        except:
            pass

    if not arcpy.Exists(source_fc):
        print u"错误：源要素类不存在！"
        return

    # 从模版XMHX获取目标字段集合及字段属性
    template_xmhx = os.path.join(template_dir_111, u"项目红线", "XMHX.shp")
    if not os.path.exists(template_xmhx):
        print u"错误：模版 XMHX 不存在！"
        return

    target_fields = set()
    xmhx_field_info = {}
    for f in arcpy.ListFields(template_xmhx):
        if f.name.upper() not in SKIP_FIELDS:
            target_fields.add(f.name)
            xmhx_field_info[f.name] = {
                'type': f.type,
                'length': f.length,
                'precision': f.precision,
                'scale': f.scale
            }
    text_fields = sorted(
        n for n, i in xmhx_field_info.iteritems() if i['type'] in ('String',)
    )
    print u"模版 XMHX 字段 (%d): %s" % (len(target_fields), u", ".join(sorted(target_fields)))

    # 检查源字段，报告多余字段
    extra_fields = []
    for f in arcpy.ListFields(source_fc):
        if f.name.upper() not in SKIP_FIELDS and f.name not in target_fields:
            extra_fields.append(f.name)
    if extra_fields:
        print u"以下字段不在模版XMHX中，将被删除: %s" % u", ".join(extra_fields)

    xian_vals = sorted(set(
        r[0].strip() for r in arcpy.da.SearchCursor(source_fc, ["XIAN"]) if r[0]
    ))
    print u"共 %d 个县: %s" % (len(xian_vals), u", ".join(xian_vals))

    for xian in xian_vals:
        xian_name = CODE_NAME_MAP.get(xian, xian)
        print u"\n--- %s (%s) ---" % (xian, xian_name)

        xmhx_dir = os.path.join(output_base, xian_name, u"项目红线")

        # Step 1: 按县筛选（仅保留 XMHX 字段，窄表）
        fmap = arcpy.FieldMappings()
        for f in arcpy.ListFields(source_fc):
            if f.name.upper() in SKIP_FIELDS:
                continue
            if f.name not in target_fields:
                continue
            fm = arcpy.FieldMap()
            fm.addInputField(source_fc, f.name)
            fmap.addFieldMap(fm)

        tmp_filtered = os.path.join(gdb, "tmp_xmhx_f_" + xian)
        arcpy.FeatureClassToFeatureClass_conversion(
            source_fc, gdb, "tmp_xmhx_f_" + xian,
            u"XIAN = '%s'" % xian, field_mapping=fmap
        )

        cnt = int(arcpy.GetCount_management(tmp_filtered).getOutput(0))
        if cnt == 0:
            arcpy.Delete_management(tmp_filtered)
            print u"  跳过（无数据）"
            continue
        print u"  筛选 %d 条" % cnt

        tmp_working = _project_fc_if_needed(tmp_filtered, xian_name, "tmp_xmhx_114_" + xian)

        # Step 2: 合并为一个小班（直接 FIRST）
        tmp_dissolved = os.path.join(gdb, "tmp_xmhx_d_" + xian)
        stats = []
        for f in arcpy.ListFields(tmp_working):
            if f.name.upper() in SKIP_FIELDS:
                continue
            stats.append([f.name, "FIRST"])

        if stats:
            arcpy.Dissolve_management(tmp_working, tmp_dissolved,
                                      statistics_fields=stats, multi_part="MULTI_PART")
        else:
            arcpy.Dissolve_management(tmp_working, tmp_dissolved, multi_part="MULTI_PART")
        if tmp_working != tmp_filtered and arcpy.Exists(tmp_working):
            arcpy.Delete_management(tmp_working)
        arcpy.Delete_management(tmp_filtered)
        print u"  已合并为 1 个小班"

        # Step 2.5: FIRST_xxx 改回 xxx
        for f in arcpy.ListFields(tmp_dissolved):
            name = f.name
            if name.startswith("FIRST_") and name[6:].upper() not in SKIP_FIELDS:
                arcpy.AlterField_management(tmp_dissolved, name, name[6:])

        # Step 3: 重建 Schema — 删多余字段，按标准补缺失字段
        existing_fields = {f.name for f in arcpy.ListFields(tmp_dissolved)}
        for f in arcpy.ListFields(tmp_dissolved):
            if f.name.upper() not in SKIP_FIELDS and f.name not in target_fields:
                arcpy.DeleteField_management(tmp_dissolved, f.name)
                print u"  已删除多余字段: %s" % f.name

        for fld_name in target_fields:
            if fld_name not in existing_fields:
                info = xmhx_field_info[fld_name]
                if info['type'] in ('String',):
                    arcpy.AddField_management(tmp_dissolved, fld_name, "TEXT",
                                              field_length=info['length'])
                elif info['type'] in ('Double',):
                    arcpy.AddField_management(tmp_dissolved, fld_name, "DOUBLE",
                                              field_precision=info['precision'],
                                              field_scale=info['scale'])
                print u"  已补建缺失字段: %s (%s)" % (fld_name, info['type'])

        # Step 4: XMPFNYTDMJ = 合并后平面几何面积（仅 1 次计算）
        with arcpy.da.UpdateCursor(tmp_dissolved, ["SHAPE@", "XMPFNYTDMJ"]) as cur:
            for row in cur:
                geom = row[0]
                if geom:
                    row[1] = geom.getArea("PLANAR", "HECTARES")
                    cur.updateRow(row)
        print u"  XMPFNYTDMJ（合并后平面几何面积）已计算"

        # Step 5: NSYLDMJ = 对应县 ZYY.shp 的 XBMJ 字段求和
        nsyldmj_val = 0.0
        zyy_shp = os.path.join(output_base, xian_name, u"林地图斑", "ZZY.shp")
        if os.path.exists(zyy_shp):
            with arcpy.da.SearchCursor(zyy_shp, ["XBMJ"]) as cur:
                for row in cur:
                    if row[0] is not None:
                        nsyldmj_val += row[0]
        with arcpy.da.UpdateCursor(tmp_dissolved, ["NSYLDMJ"]) as cur:
            for row in cur:
                row[0] = nsyldmj_val
                cur.updateRow(row)
        print u"  NSYLDMJ（ZYY的XBMJ合计）= %.4f 公顷" % nsyldmj_val

        # Step 7: 导出到县目录，覆盖 XMHX
        if os.path.exists(xmhx_dir):
            for root2, _, files2 in os.walk(xmhx_dir):
                for f2 in files2:
                    try:
                        os.chmod(os.path.join(root2, f2), 0o777)
                    except:
                        pass
            # 重试删除整个目录
            try:
                shutil.rmtree(xmhx_dir)
            except:
                # 逐个删除残余文件
                for root2, _, files2 in os.walk(xmhx_dir):
                    for f2 in files2:
                        try:
                            os.remove(os.path.join(root2, f2))
                        except:
                            pass

        if not os.path.exists(xmhx_dir):
            os.makedirs(xmhx_dir)
        arcpy.FeatureClassToFeatureClass_conversion(tmp_dissolved, xmhx_dir, "XMHX")
        print u"  已导出至 " + os.path.join(xmhx_dir, "XMHX.shp")

        # Step 8: 清理输出 shapefile 的系统面积字段
        out_shp = os.path.join(xmhx_dir, "XMHX.shp")
        to_del = []
        for f in arcpy.ListFields(out_shp):
            if f.name.upper() in ("SHAPE_LENGTH", "SHAPE_LENG", "SHAPE_AREA"):
                to_del.append(f.name)
        if to_del:
            try:
                arcpy.DeleteField_management(out_shp, to_del)
                print u"  已删除字段: %s" % u", ".join(to_del)
            except Exception:
                print u"  删除字段失败（系统字段，保留）"

        arcpy.Delete_management(tmp_dissolved)

    print u"\n全部导出完成！"


# 直接执行
print "=" * 60
print u"  项目红线 → XMHX 分县导出（合并+平面几何面积）"
print u"  源要素类: " + source_fc
print "=" * 60
export_xmhx_by_xian()
