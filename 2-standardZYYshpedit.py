# -*- coding: utf-8 -*-
from __future__ import print_function
"""
对 standardZYYshp.py 生成的要素类执行19步字段修改。
先运行 standardZYYshp.py 生成数据，再运行此脚本修改字段。

使用方法：
  在ArcGIS Python窗口运行：
    exec(open(r'C:\4code\3lot\2-standardZYYshpedit.py').read())
"""

import sys
import os
import traceback
from collections import defaultdict

SCRIPT_DIR = r"C:\4code\3lot"
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from project_config import (
    GDB, ZYY_TARGET_FC_NAME, STANDARD_FILE, DEFAULT_ZONE,
    county_zone, prj_path_for_zone,
)

reload(sys)
sys.setdefaultencoding('utf-8')

_arcpy_found = False
_arcpy_paths = [
    r"C:\Python27\ArcGIS10.8\Lib\site-packages",
    r"C:\Python27\ArcGIS10.7\Lib\site-packages",
    r"C:\Python27\ArcGIS10.6\Lib\site-packages",
    r"C:\Python27\ArcGIS10.5\Lib\site-packages",
    r"C:\Python27\ArcGIS10.4\Lib\site-packages",
    r"C:\Python27\ArcGIS10.3\Lib\site-packages",
    r"C:\Python27\ArcGIS10.2\Lib\site-packages",
    r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro\Lib\site-packages",
]
for _p in _arcpy_paths:
    if os.path.isdir(_p):
        sys.path.insert(0, _p)
        break

try:
    import arcpy
    _arcpy_found = True
except ImportError:
    pass

if not _arcpy_found:
    print("=" * 70)
    print("错误：未找到 arcpy 模块！")
    print("请用ArcGIS自带的Python解释器运行。")
    print("=" * 70)
    sys.exit(1)

# ========== 路径配置 ==========
gdb = GDB
target_fc = gdb + u"\\" + ZYY_TARGET_FC_NAME
CHANGE_LOG_PATH = u"C:\\4code\\3lot\\修改记录_标准ZYY字段.txt"

FIELD_TYPE_MAP = {
    "String": "TEXT",
    "Integer": "LONG",
    "SmallInteger": "SHORT",
    "Float": "FLOAT",
    "Double": "DOUBLE",
    "Geometry": "GEOMETRY",
}


def is_null(val):
    """判断字段值是否为空（None 或空字符串）"""
    return val is None or (isinstance(val, basestring) and str(val).strip() == "")


def _text(val):
    if val is None:
        return u""
    try:
        return unicode(val).strip()
    except Exception:
        return str(val).strip()


def _projection_zone_for_fc(fc):
    zones = set()
    try:
        field_names = {f.name.upper(): f.name for f in arcpy.ListFields(fc)}
        xian_field = field_names.get("XIAN")
        if not xian_field:
            return None
        with arcpy.da.SearchCursor(fc, [xian_field]) as cur:
            for (xian,) in cur:
                if xian is None:
                    continue
                zones.add(county_zone(xian))
    except Exception:
        return None
    if len(zones) == 1:
        zone = list(zones)[0]
        if zone != DEFAULT_ZONE:
            return zone
    return None


def _load_sr(zone):
    prj_path = prj_path_for_zone(zone)
    if not os.path.exists(prj_path):
        return None
    sr = arcpy.SpatialReference()
    with open(prj_path, "r") as f:
        sr.loadFromString(f.read())
    return sr


def _project_to_zone_if_needed(fc):
    zone = _projection_zone_for_fc(fc)
    if not zone:
        return fc
    sr = _load_sr(zone)
    if sr is None:
        print("  警告：{}E投影文件不存在，跳过投影".format(zone))
        return fc

    tmp_fc = gdb + u"\\tmp_%s_source" % zone
    if arcpy.Exists(tmp_fc):
        arcpy.Delete_management(tmp_fc)
    arcpy.Project_management(fc, tmp_fc, sr)
    arcpy.Delete_management(fc)
    arcpy.Rename_management(tmp_fc, os.path.basename(fc))
    print("  已将数据投影到CGCS2000_3_Degree_GK_CM_{}E".format(zone))
    return fc


def parse_code_tables():
    """从 ZYY字段属性标准设置.MD 解析乡镇和行政村代码表"""
    if not os.path.exists(STANDARD_FILE):
        print("  警告：标准文件不存在，跳过代码表解析")
        return {}, {}

    with open(STANDARD_FILE, "r") as f:
        content = f.read()

    lines = content.decode("utf-8").split("\n")
    township_start = -1
    village_start = -1
    for i, line in enumerate(lines):
        if "乡镇代码（字段XIANG引用）" in line:
            township_start = i
        if "行政村代码（字段CUN引用）" in line:
            village_start = i

    name_to_code = {}
    township_lookup = {}
    village_lookup = {}

    if township_start >= 0:
        in_table = False
        end_pos = village_start if village_start > township_start else len(lines)
        for line in lines[township_start + 1:end_pos]:
            if "|" not in line:
                continue
            if "--" in line:
                in_table = True
                continue
            if not in_table:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                name_to_code[parts[1]] = parts[2]
                township_lookup[(parts[2], parts[3])] = parts[4]

    if village_start >= 0:
        in_table = False
        for line in lines[village_start + 1:]:
            if "|" not in line:
                continue
            if "--" in line:
                in_table = True
                continue
            if not in_table:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                county_code = name_to_code.get(parts[1], "")
                if county_code:
                    village_lookup[(county_code, parts[2], parts[3])] = parts[4]

    print("  代码表: 乡镇 {} 条, 行政村 {} 条".format(
        len(township_lookup), len(village_lookup)))
    return township_lookup, village_lookup


def multipart_to_singlepart():
    """将目标要素类规范化为单部件小班。"""
    tmp_fc = gdb + u"\\tmp_zyy_singlepart"
    clean_fc = gdb + u"\\tmp_zyy_singlepart_clean"
    if arcpy.Exists(tmp_fc):
        arcpy.Delete_management(tmp_fc)
    if arcpy.Exists(clean_fc):
        arcpy.Delete_management(clean_fc)

    before = int(arcpy.GetCount_management(target_fc).getOutput(0))
    arcpy.MultipartToSinglepart_management(target_fc, tmp_fc)
    after = int(arcpy.GetCount_management(tmp_fc).getOutput(0))

    fmap = arcpy.FieldMappings()
    fmap.addTable(tmp_fc)
    for i in range(fmap.fieldCount - 1, -1, -1):
        fm = fmap.getFieldMap(i)
        if fm.outputField.name.upper() == "ORIG_FID":
            fmap.removeFieldMap(i)
            print("排除Multipart To Singlepart辅助字段: ORIG_FID")
            break
    arcpy.FeatureClassToFeatureClass_conversion(
        tmp_fc, gdb, os.path.basename(clean_fc), field_mapping=fmap)
    arcpy.Delete_management(tmp_fc)

    arcpy.Delete_management(target_fc)
    arcpy.Rename_management(clean_fc, os.path.basename(target_fc))
    print("Multipart To Singlepart: {} -> {} 条".format(before, after))


def modify_fields():
    """按指定顺序修改字段值（共19步），后序步骤可依赖前序修改结果"""
    multipart_to_singlepart()

    print("修改字段值（19步）...")
    total = int(arcpy.GetCount_management(target_fc).getOutput(0))
    print("共 {} 条记录".format(total))

    # ---- 步骤1: LIN_BAN 空值设为"0000" ----
    print("1/19: LIN_BAN 空值->'0000'")
    with arcpy.da.UpdateCursor(target_fc, ["LIN_BAN"]) as cursor:
        cnt = 0
        for row in cursor:
            if is_null(row[0]):
                row[0] = "0000"
                cursor.updateRow(row)
                cnt += 1
        print("  修改 {} 条".format(cnt))

    # ---- 步骤2: XBMJ 重新计算（平面几何面积，公顷）并删除0面积记录 ----
    print("2/19: XBMJ 平面几何面积重算（公顷，按县配置投影带）")
    sr_cache = {}
    with arcpy.da.UpdateCursor(target_fc, ["SHAPE@", "XIAN", "XBMJ"]) as cursor:
        cnt = 0
        for row in cursor:
            try:
                geom = row[0]
                zone = county_zone(row[1])
                if zone != DEFAULT_ZONE:
                    if zone not in sr_cache:
                        sr_cache[zone] = _load_sr(zone)
                        if sr_cache[zone] is None:
                            print("  警告：{}E投影文件不存在，该带按原投影计算".format(zone))
                    if sr_cache.get(zone) is not None:
                        geom = geom.projectAs(sr_cache[zone])
                row[2] = round(geom.getArea("PLANAR", "HECTARES"), 4)
                cursor.updateRow(row)
                cnt += 1
            except Exception:
                pass
        print("  重新计算 {} 条".format(cnt))

    print("XBMJ: 删除0面积记录")
    with arcpy.da.UpdateCursor(target_fc, ["XBMJ"]) as cursor:
        cnt = 0
        for row in cursor:
            if row[0] is not None and float(row[0]) == 0.0:
                cursor.deleteRow()
                cnt += 1
        print("  删除 {} 条".format(cnt))

    # ---- 步骤3: SYLDDKXH 最近邻链编码（沿工程走向，环形工程可转一圈）----
    # 每个要素按所在县投影带投影后取 labelPoint 转成点，用 ArcGIS PointDistance
    # 算两两距离，从西北角起步做贪心最近邻链：每次跳到最近的未编号要素，
    # 形成一条沿工程实际走向的施工路径。县间按最西点从左到右，全县连续编号。
    print("3/19: SYLDDKXH 最近邻链编码（沿工程走向）")
    sr_cache = {}
    groups = defaultdict(list)          # XIAN -> [(src_oid, projected_geom), ...]
    county_min_x = {}                   # XIAN -> 县内最西 X（用于县间排序）
    with arcpy.da.SearchCursor(target_fc, ["OID@", "XIAN", "SHAPE@"]) as cursor:
        for oid, xian, geom in cursor:
            xian = xian if xian else ""
            zone = county_zone(xian)
            if zone != DEFAULT_ZONE and zone not in sr_cache:
                sr_cache[zone] = _load_sr(zone)
            sr = sr_cache.get(zone) if zone != DEFAULT_ZONE else None
            g = geom.projectAs(sr) if (sr is not None and geom is not None) else geom
            groups[xian].append((oid, g))
            pt = g.labelPoint if g is not None else None
            x = pt.X if pt is not None else 0.0
            county_min_x[xian] = min(county_min_x.get(xian, x), x)

    ordered_oids = []
    for ci, xian in enumerate(sorted(county_min_x.keys(), key=lambda k: county_min_x[k])):
        items = groups[xian]
        n = len(items)
        if n == 0:
            continue
        if n == 1:
            ordered_oids.append(items[0][0])
            continue

        # 1) 建临时点要素类，写入投影后的 labelPoint，记录源 OID
        tmp_pts = gdb + u"\\tmp_nn_pts_%d" % ci
        tmp_tbl = gdb + u"\\tmp_nn_tbl_%d" % ci
        for tmp in (tmp_pts, tmp_tbl):
            if arcpy.Exists(tmp):
                arcpy.Delete_management(tmp)
        arcpy.CreateFeatureclass_management(gdb, os.path.basename(tmp_pts), "POINT",
                                            spatial_reference=arcpy.Describe(target_fc).spatialReference)
        arcpy.AddField_management(tmp_pts, "SRC_OID", "LONG")
        with arcpy.da.InsertCursor(tmp_pts, ["SHAPE@", "SRC_OID"]) as icur:
            for src_oid, g in items:
                pt = g.labelPoint if g is not None else None
                if pt is not None:
                    icur.insertRow([arcpy.PointGeometry(pt), src_oid])
        fid_to_src = {}
        fid_to_xy = {}
        for f, src, xy in arcpy.da.SearchCursor(tmp_pts, ["OID@", "SRC_OID", "SHAPE@XY"]):
            fid_to_src[f] = src
            fid_to_xy[f] = xy

        # 2) 用 PointDistance 算两两距离（输入输出同为该点要素类）
        arcpy.PointDistance_analysis(tmp_pts, tmp_pts, tmp_tbl)
        # 邻接表：in_fid -> [(dist, near_fid), ...]，过滤掉自身(距离0)
        nbr = defaultdict(list)
        with arcpy.da.SearchCursor(tmp_tbl, ["INPUT_FID", "NEAR_FID", "DISTANCE"]) as cur:
            for in_fid, near_fid, dist in cur:
                if in_fid == near_fid:
                    continue
                if dist is not None and dist > 0:
                    nbr[in_fid].append((dist, near_fid))
        for k in nbr:
            nbr[k].sort()

        # 3) 起点：西北角（Y 最大，并列取 X 最小）
        start_fid = max(fid_to_xy.keys(), key=lambda f: (fid_to_xy[f][1], -fid_to_xy[f][0]))

        # 4) 贪心最近邻链
        visited = set()
        cur_fid = start_fid
        while cur_fid is not None and len(visited) < n:
            visited.add(cur_fid)
            ordered_oids.append(fid_to_src[cur_fid])
            nxt = None
            for dist, near_fid in nbr.get(cur_fid, []):
                if near_fid not in visited:
                    nxt = near_fid
                    break
            cur_fid = nxt

        # 兜底：链中断时把剩余按 X、Y 顺序补上
        if len(visited) < n:
            remaining = [(it[1].labelPoint.X, -it[1].labelPoint.Y, it[0])
                         for it in items if it[0] not in set(ordered_oids)]
            remaining.sort()
            ordered_oids.extend(r[2] for r in remaining)

        for tmp in (tmp_pts, tmp_tbl):
            if arcpy.Exists(tmp):
                arcpy.Delete_management(tmp)

    seq_map = {oid: str(i + 1) for i, oid in enumerate(ordered_oids)}
    with arcpy.da.UpdateCursor(target_fc, ["OID@", "SYLDDKXH"]) as cursor:
        cnt = 0
        for row in cursor:
            row[1] = seq_map[row[0]]
            cursor.updateRow(row)
            cnt += 1
        print("  编码 {} 条 (县数 {})".format(cnt, len(groups)))

    # ---- 步骤4-9, 11-12, 14-16, 18-20: 批量简单填充 ----
    print("4-20: 批量填充...")
    with arcpy.da.UpdateCursor(target_fc, [
        "BH_DJ", "SEN_LIN_LB", "QI_YUAN", "ZRBHQ_DJ",
        "PINGJUN_XJ", "HUO_LMGQXJ", "MEI_GQ_ZS", "YU_BI_DU",
        "GJGYLD_MJ", "TRLLD_MJ", "WFTBMJ", "DCRY", "DCRQ",
        "CS_GHQ", "DI_LEI",
    ]) as cursor:
        c = [0] * 14
        for row in cursor:
            dl = str(row[14]).strip() if row[14] else ""
            if is_null(row[0]):   # 4. BH_DJ
                row[0] = "4"; c[0] += 1
            if is_null(row[1]):   # 5. SEN_LIN_LB
                row[1] = "022"; c[1] += 1
            if dl == "030405":
                if not is_null(row[2]):
                    row[2] = None; c[2] += 1
            elif is_null(row[2]):   # 6. QI_YUAN
                row[2] = "20"; c[2] += 1
            if row[3] is not None:  # 7. ZRBHQ_DJ
                zrbhq_dj = str(row[3]).strip()
                if zrbhq_dj == "1":
                    row[3] = u"国家级"; c[3] += 1
                elif zrbhq_dj == "2":
                    row[3] = u"省级"; c[3] += 1
            if row[4] is None:    # 8. PINGJUN_XJ
                row[4] = 0.0; c[4] += 1
            if row[5] is None:    # 9. HUO_LMGQXJ
                row[5] = 0.0; c[5] += 1
            if row[6] is None:    # 11. MEI_GQ_ZS
                row[6] = 0; c[6] += 1
            if row[7] is None:    # 12. YU_BI_DU
                row[7] = 0.0; c[7] += 1
            if row[8] is None:    # 14. GJGYLD_MJ
                row[8] = 0.0; c[8] += 1
            if row[9] is None:    # 15. TRLLD_MJ
                row[9] = 0.0; c[9] += 1
            if row[10] is None:   # 16. WFTBMJ
                row[10] = 0.0; c[10] += 1
            # 18. DCRY 全部填写（覆盖所有行）
            row[11] = u"宋庆安、钟安豪"; c[11] += 1
            # 19. DCRQ 全部填写（覆盖所有行）
            row[12] = "20260512"; c[12] += 1
            # 20. CS_GHQ 全部填0
            row[13] = 0; c[13] += 1
            cursor.updateRow(row)
        print("  4. BH_DJ: {}".format(c[0]))
        print("  5. SEN_LIN_LB: {}".format(c[1]))
        print("  6. QI_YUAN: {}".format(c[2]))
        print("  7. ZRBHQ_DJ(1->国家级, 2->省级): {}".format(c[3]))
        print("  8. PINGJUN_XJ: {}".format(c[4]))
        print("  9. HUO_LMGQXJ: {}".format(c[5]))
        print("  11. MEI_GQ_ZS: {}".format(c[6]))
        print("  12. YU_BI_DU: {}".format(c[7]))
        print("  14. GJGYLD_MJ: {}".format(c[8]))
        print("  15. TRLLD_MJ: {}".format(c[9]))
        print("  16. WFTBMJ: {}".format(c[10]))
        print("  18. DCRY: {}".format(c[11]))
        print("  19. DCRQ: {}".format(c[12]))
        print("  20. CS_GHQ: {} (全部填0)".format(c[13]))

    # ---- LIN_ZHONG 条件填充（已停用：不修改该字段）----
    # print("LIN_ZHONG: SEN_LIN_LB=022 + DI_LEI匹配时填充")
    # with arcpy.da.UpdateCursor(target_fc, ["LIN_ZHONG", "SEN_LIN_LB", "DI_LEI"]) as cursor:
    #     cnt = 0
    #     di_lei_map = {"030100": "233", "030302": "255"}
    #     for row in cursor:
    #         if str(row[1]).strip() == "022":
    #             dl = str(row[2]).strip() if row[2] else ""
    #             if dl in ("030404", "030405"):
    #                 if not is_null(row[0]):
    #                     row[0] = None
    #                     cursor.updateRow(row)
    #                     cnt += 1
    #             elif is_null(row[0]) and dl in di_lei_map:
    #                 row[0] = di_lei_map[dl]
    #                 cursor.updateRow(row)
    #                 cnt += 1
    #     print("  填充 {} 条".format(cnt))

    # ---- CS_GHQ 判断：XIANG含"街道" + CUN含"社区"/"街坊" → 1 ----
    print("CS_GHQ: 街道+社区/街坊判断")
    township_lookup, village_lookup = parse_code_tables()
    if township_lookup and village_lookup:
        with arcpy.da.UpdateCursor(target_fc, ["XIAN", "XIANG", "CUN", "CS_GHQ"]) as cursor:
            cnt = 0
            for row in cursor:
                xian = str(row[0]).strip() if row[0] else ""
                xiang = str(row[1]).strip() if row[1] else ""
                cun = str(row[2]).strip() if row[2] else ""
                t_name = township_lookup.get((xian, xiang), "")
                v_name = village_lookup.get((xian, xiang, cun), "")
                if u"街道" in t_name and (u"社区" in v_name or u"街坊" in v_name):
                    row[3] = 1
                    cursor.updateRow(row)
                    cnt += 1
            print("  设为1: {} 条".format(cnt))
    else:
        print("  代码表为空，跳过（CS_GHQ保持0）")

    # ---- 步骤10: XIAO_BAN_X = HUO_LMGQXJ x XBMJ ----
    print("10/19: XIAO_BAN_X = HUO_LMGQXJ x XBMJ")
    with arcpy.da.UpdateCursor(target_fc, ["HUO_LMGQXJ", "XBMJ", "XIAO_BAN_X"]) as cursor:
        cnt = 0
        for row in cursor:
            row[2] = int(round((row[0] if row[0] is not None else 0.0) *
                           (row[1] if row[1] is not None else 0.0)))
            cursor.updateRow(row)
            cnt += 1
        print("  计算 {} 条".format(cnt))

    # ---- 步骤13: ZRBHDLX ----
    print("13/19: ZRBHDLX <- ZRBHQ_MC有值时填")
    with arcpy.da.UpdateCursor(target_fc, ["ZRBHQ_MC", "ZRBHDLX"]) as cursor:
        cnt = 0
        for row in cursor:
            if not is_null(row[0]):
                row[1] = u"内陆湿地和水域生态系统类型"
                cursor.updateRow(row)
                cnt += 1
        print("  填写 {} 条".format(cnt))

    # ---- 步骤17: JJLZS = MEI_GQ_ZS x XBMJ ----
    print("17/19: JJLZS = MEI_GQ_ZS x XBMJ")
    with arcpy.da.UpdateCursor(target_fc, ["MEI_GQ_ZS", "XBMJ", "JJLZS"]) as cursor:
        cnt = 0
        for row in cursor:
            a = row[0] if row[0] is not None else 0
            b = row[1] if row[1] is not None else 0.0
            row[2] = int(round(float(a) * b))
            cursor.updateRow(row)
            cnt += 1
        print("  修改 {} 条".format(cnt))

    print("字段修改完成！")


def check_field_properties():
    """对照标准文件检查修改字段的属性"""
    # 只检查被修改的字段
    modified = [
        ("LIN_BAN",    "String",  4, None),
        ("SYLDDKXH",   "String", 20, None),
        ("XBMJ",       "Double", 18, 4),
        ("BH_DJ",      "String",  1, None),
        ("SEN_LIN_LB", "String",  3, None),
        ("QI_YUAN",    "String",  2, None),
        ("ZRBHQ_DJ",   "String",250, None),
        ("PINGJUN_XJ", "Double",  6, 1),
        ("HUO_LMGQXJ", "Double", 12, 1),
        ("XIAO_BAN_X", "Double", 12, 1),
        ("MEI_GQ_ZS",  "Integer", 5, None),
        ("YU_BI_DU",   "Double",  6, 2),
        ("ZRBHDLX",    "String",250, None),
        ("GJGYLD_MJ",  "Double", 18, 4),
        ("TRLLD_MJ",   "Double", 18, 4),
        ("WFTBMJ",     "Double", 18, 4),
        ("DCRY",       "String",250, None),
        ("DCRQ",       "String",  8, None),
        ("JJLZS",      "Integer", 5, None),
        ("CS_GHQ",     "SmallInteger", 1, None),
    ]

    print("\n字段属性检查（仅修改字段）:")
    tgt_fields = {f.name.upper(): f for f in arcpy.ListFields(target_fc)}
    all_ok = True
    for name, ftype, length, scale in modified:
        nu = name.upper()
        f = tgt_fields.get(nu)
        if not f:
            print("  {}: 字段不存在！".format(name))
            all_ok = False
            continue
        af_type = FIELD_TYPE_MAP.get(ftype, "TEXT")
        issues = []
        if f.type.upper() != af_type.upper():
            issues.append("类型应为{}实际为{}".format(af_type, f.type))
        if ftype == "String" and length:
            if f.length != length:
                issues.append("长度应为{}实际为{}".format(length, f.length))
        if ftype == "Integer" and length:
            if f.precision != length:
                issues.append("精度应为{}实际为{}".format(length, f.precision))
        if ftype == "Double" and scale is not None:
            if f.scale != scale:
                issues.append("小数位应为{}实际为{}".format(scale, f.scale))
        if issues:
            print("  {}: 异常 - {}".format(name, "; ".join(issues)))
            all_ok = False
        else:
            print("  {}: 正常".format(name))
    if all_ok:
        print("所有修改字段属性全部正确！")


def save_changelog():
    """保存修改记录到根目录"""
    lines = []
    lines.append("=" * 60)
    lines.append("ZYY标准字段修改记录")
    lines.append("生成时间: 2026-05-13")
    lines.append("目标要素类: " + target_fc)
    lines.append("=" * 60)
    lines.append("")
    lines.append("修改顺序及内容（共19步）：")
    lines.append("")
    lines.append("  预处理. Multipart To Singlepart，将小班规范化为单部件")
    lines.append("")

    steps = [
        ("LIN_BAN",     u"空值->'0000'"),
        ("XBMJ",        u"按GIS平面几何重新计算（公顷），删除为0的行"),
        ("SYLDDKXH",    u"按县投影带投影，PointDistance算两两距离，西北角起贪心最近邻链，全县连续从1编码"),
        ("BH_DJ",       u"空值->4"),
        ("SEN_LIN_LB",  u"空值->022"),
        ("QI_YUAN",     u"DI_LEI=030405时留空，其余空值->20"),
        ("ZRBHQ_DJ",    u"1->国家级，2->省级（不填空值）"),
        ("PINGJUN_XJ",  u"空值->0"),
        ("HUO_LMGQXJ",  u"空值->0"),
        ("XIAO_BAN_X",  u"= HUO_LMGQXJ x XBMJ"),
        ("MEI_GQ_ZS",   u"空值->0"),
        ("YU_BI_DU",    u"空值->0"),
        ("ZRBHDLX",     u"ZRBHQ_MC有值时->内陆湿地和水域生态系统类型"),
        ("GJGYLD_MJ",   u"空值->0"),
        ("TRLLD_MJ",    u"空值->0"),
        ("WFTBMJ",      u"空值->0"),
        ("JJLZS",       u"全部行 = MEI_GQ_ZS x XBMJ"),
        ("DCRY",        u"全部行->宋庆安、钟安豪"),
        ("DCRQ",        u"全部行->20260612"),
        ("CS_GHQ",      u"全部行->0"),
    ]
    for i, (f, d) in enumerate(steps, 1):
        lines.append("  {:2d}. {:<12s} {}".format(i, f, d))

    lines.append("")
    lines.append("-" * 60)
    lines.append("字段属性检查结果（对照ZYY字段属性标准设置.MD）:")
    lines.append("  (运行 check_field_properties() 查看详情)")
    lines.append("")
    lines.append("=" * 60)

    with open(CHANGE_LOG_PATH, "w") as f:
        f.write("\n".join(lines))

    print("修改记录已保存至: " + CHANGE_LOG_PATH)


if __name__ == "__main__":
    print("=" * 60)
    print(" ZYY标准字段 修改工具")
    print(" 操作对象: {}".format(target_fc))
    print(" 说明: 先运行 standardZYYshp.py 生成数据")
    print("=" * 60)

    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True

    if not arcpy.Exists(target_fc):
        print("\n错误：目标要素类不存在！请先运行 standardZYYshp.py")
        sys.exit(1)

    try:
        target_fc = _project_to_zone_if_needed(target_fc)
        modify_fields()
        check_field_properties()
        save_changelog()
        print("\n完成！")
    except Exception as e:
        print("\n错误: {}".format(str(sys.exc_info()[1])))
        traceback.print_exc()
        sys.exit(1)
