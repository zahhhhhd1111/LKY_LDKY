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
    DEFAULT_ZONE, county_name, county_zone, prj_path_for_zone,
    COUNTY_BOUNDARY_FC_NAME, COUNTY_NAME_TO_CODE,
)

reload(sys)
sys.setdefaultencoding('utf-8')

gdb = GDB
source_fc = gdb + u"/" + XMHX_SOURCE_FC_NAME
county_boundary_fc = gdb + u"/" + COUNTY_BOUNDARY_FC_NAME
template_dir_111 = TEMPLATE_DIR_111
output_base = OUTPUT_BASE
SPLIT_XIAN_FIELD = "CUT_XIAN"
SKIP_FIELDS = {"OBJECTID", "SHAPE", "SHAPE_LENGTH", "SHAPE_AREA", SPLIT_XIAN_FIELD}


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


def _delete_if_exists(path):
    if arcpy.Exists(path):
        arcpy.Delete_management(path)


def _field_lookup(fc):
    return {f.name.upper(): f.name for f in arcpy.ListFields(fc)}


def _find_county_field(fc):
    fields = _field_lookup(fc)
    for name in ("XIAN", u"县代码", "XZQDM", "XZQHDM", "QXDM", "QX_CODE", "CODE"):
        found = fields.get(name.upper())
        if found:
            return found
    for name in (u"坐落县", u"县", u"县名", "XZQMC", "QXMC", "NAME"):
        found = fields.get(name.upper())
        if found:
            return found
    for f in arcpy.ListFields(fc):
        field_text = _text(f.aliasName) + u" " + _text(f.name)
        if u"县代码" in field_text or u"坐落县" in field_text:
            return f.name
    return None


def _county_code_from_boundary(val):
    s = _text(val)
    if s.isdigit():
        return s.zfill(6)
    return COUNTY_NAME_TO_CODE.get(s, s)


def _coerce_xian_value(val, field_obj):
    s = _text(val)
    if not s:
        return None
    if field_obj.type in ("Integer", "SmallInteger"):
        return int(float(s))
    if field_obj.type in ("Double", "Single"):
        return float(s)
    return s


def _ensure_double_field(fc, fld_name, info):
    fields = {f.name: f for f in arcpy.ListFields(fc)}
    field = fields.get(fld_name)
    if field and field.type == "Double" and field.precision == info['precision'] and field.scale == info['scale']:
        return
    if field:
        arcpy.DeleteField_management(fc, fld_name)
    arcpy.AddField_management(fc, fld_name, "DOUBLE",
                              field_precision=info['precision'],
                              field_scale=info['scale'])


def _split_fc_by_county(src_fc, xian_field, xian_field_obj, tmp_prefix):
    if not arcpy.Exists(county_boundary_fc):
        _log(u"  警告：县界要素不存在，跳过按坐落县切分: " + county_boundary_fc)
        return src_fc
    boundary_xian_field = _find_county_field(county_boundary_fc)
    if not boundary_xian_field:
        _log(u"  警告：县界要素缺少县代码字段，跳过按坐落县切分")
        return src_fc

    tmp_boundary = os.path.join(gdb, tmp_prefix + "_bnd")
    tmp_split = os.path.join(gdb, tmp_prefix + "_split")
    _delete_if_exists(tmp_boundary)
    _delete_if_exists(tmp_split)

    arcpy.CopyFeatures_management(county_boundary_fc, tmp_boundary)
    if SPLIT_XIAN_FIELD.upper() not in _field_lookup(tmp_boundary):
        arcpy.AddField_management(tmp_boundary, SPLIT_XIAN_FIELD, "TEXT", field_length=32)
    with arcpy.da.UpdateCursor(tmp_boundary, [boundary_xian_field, SPLIT_XIAN_FIELD]) as cur:
        for row in cur:
            row[1] = _county_code_from_boundary(row[0])
            cur.updateRow(row)

    arcpy.Intersect_analysis([src_fc, tmp_boundary], tmp_split, "ALL", "", "INPUT")
    cnt = int(arcpy.GetCount_management(tmp_split).getOutput(0))
    _delete_if_exists(tmp_boundary)
    if cnt == 0:
        _delete_if_exists(tmp_split)
        _log(u"  警告：按县界切分后无数据，仍使用原始要素")
        return src_fc

    with arcpy.da.UpdateCursor(tmp_split, [xian_field, SPLIT_XIAN_FIELD]) as cur:
        for row in cur:
            if row[1]:
                row[0] = _coerce_xian_value(row[1], xian_field_obj)
                cur.updateRow(row)
    _log(u"  已按坐落县界切分 %d 条，并刷新 %s" % (cnt, xian_field))
    return tmp_split


def _project_fc_if_needed(fc, zone, tmp_name):
    if zone == DEFAULT_ZONE:
        return fc
    prj_path = prj_path_for_zone(zone)
    if not os.path.exists(prj_path):
        _log(u"  警告：%sE投影文件不存在，跳过投影" % zone)
        return fc
    tmp_fc = os.path.join(gdb, tmp_name)
    if arcpy.Exists(tmp_fc):
        arcpy.Delete_management(tmp_fc)
    sr = arcpy.SpatialReference()
    with open(prj_path, "r") as f:
        sr.loadFromString(f.read())
    arcpy.Project_management(fc, tmp_fc, sr)
    _log(u"  已投影到CGCS2000_3_Degree_GK_CM_%sE" % zone)
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
        _log(u"错误：源要素类不存在！")
        return
    source_fields = {f.name.upper(): f.name for f in arcpy.ListFields(source_fc)}
    xian_field = source_fields.get("XIAN") or source_fields.get(u"县代码")
    if not xian_field:
        _log(u"错误：源要素类缺少 XIAN/县代码 字段，无法按县导出！")
        return
    xian_field_obj = [f for f in arcpy.ListFields(source_fc) if f.name == xian_field][0]

    # 从模版XMHX获取目标字段集合及字段属性
    template_xmhx = os.path.join(template_dir_111, u"项目红线", "XMHX.shp")
    if not os.path.exists(template_xmhx):
        _log(u"错误：模版 XMHX 不存在！")
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
    _log(u"模版 XMHX 字段 (%d): %s" % (len(target_fields), u", ".join(sorted(target_fields))))

    working_fc = _split_fc_by_county(source_fc, xian_field, xian_field_obj, "tmp_xmhx_county")

    # 检查源字段，报告多余字段
    extra_fields = []
    for f in arcpy.ListFields(working_fc):
        if f.name.upper() not in SKIP_FIELDS and f.name not in target_fields:
            extra_fields.append(f.name)
    if extra_fields:
        _log(u"以下字段不在模版XMHX中，将被删除: %s" % u", ".join(extra_fields))

    xian_vals = sorted(set(
        _text(r[0]) for r in arcpy.da.SearchCursor(working_fc, [xian_field]) if r[0]
    ))
    _log(u"共 %d 个县: %s" % (len(xian_vals), u", ".join(xian_vals)))

    for xian in xian_vals:
        xian_name = county_name(xian)
        zone = county_zone(xian)
        _log(u"\n--- %s (%s, %sE) ---" % (xian, xian_name, zone))

        xmhx_dir = os.path.join(output_base, xian_name, u"项目红线")

        # Step 1: 按县筛选（仅保留 XMHX 字段，窄表）
        fmap = arcpy.FieldMappings()
        for f in arcpy.ListFields(working_fc):
            if f.name.upper() in SKIP_FIELDS:
                continue
            if f.name not in target_fields:
                continue
            fm = arcpy.FieldMap()
            fm.addInputField(working_fc, f.name)
            fmap.addFieldMap(fm)

        tmp_filtered = os.path.join(gdb, "tmp_xmhx_f_" + xian)
        where_field = arcpy.AddFieldDelimiters(working_fc, xian_field)
        if xian_field_obj.type in ("Integer", "SmallInteger", "Double", "Single"):
            where_clause = u"%s = %s" % (where_field, xian)
        else:
            where_clause = u"%s = '%s'" % (where_field, xian)
        arcpy.FeatureClassToFeatureClass_conversion(
            working_fc, gdb, "tmp_xmhx_f_" + xian,
            where_clause, field_mapping=fmap
        )

        cnt = int(arcpy.GetCount_management(tmp_filtered).getOutput(0))
        if cnt == 0:
            arcpy.Delete_management(tmp_filtered)
            _log(u"  跳过（无数据）")
            continue
        _log(u"  筛选 %d 条" % cnt)

        tmp_working = _project_fc_if_needed(tmp_filtered, zone, "tmp_xmhx_" + zone + "_" + xian)

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
        _log(u"  已合并为 1 个小班")

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
                _log(u"  已删除多余字段: %s" % f.name)

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
                _log(u"  已补建缺失字段: %s (%s)" % (fld_name, info['type']))

        # Intersect 生成的临时要素可能改变字段 scale；面积字段后面会重算，按模板恢复字段定义。
        if "XMPFNYTDMJ" in xmhx_field_info and xmhx_field_info["XMPFNYTDMJ"]['type'] in ('Double',):
            _ensure_double_field(tmp_dissolved, "XMPFNYTDMJ", xmhx_field_info["XMPFNYTDMJ"])

        # Step 4: XMPFNYTDMJ = 合并后平面几何面积（仅 1 次计算）
        with arcpy.da.UpdateCursor(tmp_dissolved, ["SHAPE@", "XMPFNYTDMJ"]) as cur:
            for row in cur:
                geom = row[0]
                if geom:
                    row[1] = round(geom.getArea("PLANAR", "HECTARES"), 4)
                    cur.updateRow(row)
        _log(u"  XMPFNYTDMJ（合并后平面几何面积）已计算")

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
        _log(u"  NSYLDMJ（ZYY的XBMJ合计）= %.4f 公顷" % nsyldmj_val)

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
        _log(u"  已导出至 " + os.path.join(xmhx_dir, "XMHX.shp"))

        # Step 8: 清理输出 shapefile 的系统面积字段
        out_shp = os.path.join(xmhx_dir, "XMHX.shp")
        to_del = []
        for f in arcpy.ListFields(out_shp):
            if f.name.upper() in ("SHAPE_LENGTH", "SHAPE_LENG", "SHAPE_AREA"):
                to_del.append(f.name)
        if to_del:
            try:
                arcpy.DeleteField_management(out_shp, to_del)
                _log(u"  已删除字段: %s" % u", ".join(to_del))
            except Exception:
                _log(u"  删除字段失败（系统字段，保留）")

        arcpy.Delete_management(tmp_dissolved)

    if working_fc != source_fc and arcpy.Exists(working_fc):
        arcpy.Delete_management(working_fc)

    _log(u"\n全部导出完成！")


# 直接执行
_log("=" * 60)
_log(u"  项目红线 → XMHX 分县导出（合并+平面几何面积）")
_log(u"  源要素类: " + source_fc)
_log("=" * 60)
export_xmhx_by_xian()
