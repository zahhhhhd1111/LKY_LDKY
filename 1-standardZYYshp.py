# -*- coding: utf-8 -*-
from __future__ import print_function
"""
生成符合ZYY标准字段结构的工作矢量新版
输入：五县ZYY空间连接保护区
输出：五县ZYY_标准字段版（在同个GDB中）

使用方法：
  在ArcGIS Python窗口运行：
    exec(open(r'C:\4code\3lot\1-standardZYYshp.py').read())
"""

import sys
import os
import traceback

# Python 2.7 中文编码修复
reload(sys)
sys.setdefaultencoding('utf-8')

# ====== arcpy 导入兼容处理 ======
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
gdb = r"C:\4code\3lot\输出结果.gdb"
source_fc = gdb + r"\五县ZYY空间连接保护区"
target_fc_name = "五县ZYY_标准字段版测试"
target_fc = gdb + "\\" + target_fc_name
SPECIAL_COUNTIES = set([u"华容县", u"湘阴县"])
PROJECT_114_PRJ = r"C:\4code\3lot\模版-1009征占用林地数据模板CGCG2000_114\林地图斑\ZZY.prj"
COUNTY_DBF = u"C:\\4code\\3lot\\县名.dbf"

# ========== ZZY标准字段定义 ==========
# (字段名, 类型, 别名, 长度, 小数位)
# 字段属性严格按照 "ZYY字段属性标准设置" 表格
ZZY_FIELDS = [
    # 系统字段
    ("OBJECTID",       "OID",       "FID",        None, None),
    ("Shape",          "Geometry",  "Shape",      None, None),
    # 业务字段
    ("XIAN",           "String",    "XIAN",              6, None),
    ("XIANG",          "String",    "XIANG",             3, None),
    ("CUN",            "String",    "CUN",               3, None),
    ("LIN_BAN",        "String",    "LIN_BAN",           4, None),
    ("SYLDDKXH",       "String",    "SYLDDKXH",         20, None),
    ("XIAO_BAN",       "String",    "XIAO_BAN",          5, None),
    ("XBMJ",           "Double",    "XBMJ",             18, 4),
    ("DI_LEI",         "String",    "DI_LEI",            6, None),
    ("DLBM",           "String",    "DLBM",              5, None),
    ("LD_QS",          "String",    "LD_QS",             2, None),
    ("BH_DJ",          "String",    "BH_DJ",             1, None),
    ("SEN_LIN_LB",     "String",    "SEN_LIN_LB",        3, None),
    ("LIN_ZHONG",      "String",    "LIN_ZHONG",         3, None),
    ("QI_YUAN",        "String",    "QI_YUAN",           2, None),
    ("ZRBHQ_MC",       "String",    "ZRBHQ_MC",        250, None),
    ("ZRBHQ_DJ",       "String",    "ZRBHQ_DJ",        250, None),
    ("SLGY_MC",        "String",    "SLGY_MC",         250, None),
    ("SLGY_DJ",        "String",    "SLGY_DJ",         250, None),
    ("SDGY_MC",        "String",    "SDGY_MC",         250, None),
    ("SDGY_DJ",        "String",    "SDGY_DJ",         250, None),
    ("FJMSQ_MC",       "String",    "FJMSQ_MC",        250, None),
    ("FJMSQ_DJ",       "String",    "FJMSQ_DJ",        250, None),
    ("DZGY_MC",        "String",    "DZGY_MC",         250, None),
    ("DZGY_DJ",        "String",    "DZGY_DJ",         250, None),
    ("HYGY_MC",        "String",    "HYGY_MC",         250, None),
    ("HYGY_DJ",        "String",    "HYGY_DJ",         250, None),
    ("SMGY_MC",        "String",    "SMGY_MC",         250, None),
    ("SMGY_DJ",        "String",    "SMGY_DJ",         250, None),
    ("CYGY_MC",        "String",    "CYGY_MC",         250, None),
    ("CYGY_DJ",        "String",    "CYGY_DJ",         250, None),
    ("SHU_ZHONG_",     "String",    "SHU_ZHONG_",       50, None),
    ("YOU_SHI_SZ",     "String",    "YOU_SHI_SZ",        6, None),
    ("LING_ZU",        "String",    "LING_ZU",           1, None),
    ("PINGJUN_SG",     "Double",    "PINGJUN_SG",        6, 1),
    ("PINGJUN_XJ",     "Double",    "PINGJUN_XJ",        6, 1),
    ("HUO_LMGQXJ",     "Double",    "HUO_LMGQXJ",       12, 1),
    ("JSNR",           "String",    "JSNR",             255, None),
    ("LD_XZ",          "String",    "LD_XZ",            250, None),
    ("BZ",             "String",    "BZ",               250, None),
    ("XIAO_BAN_X",     "Double",    "XIAO_BAN_X",       12, 1),
    ("MEI_GQ_ZS",      "Integer",   "MEI_GQ_ZS",         5, None),
    ("GJGYL_BHDJ",     "String",    "GJGYL_BHDJ",        1, None),
    ("YU_BI_DU",       "Double",    "YU_BI_DU",          6, 2),
    ("Y_SQDJ",         "String",    "Y_SQDJ",            3, None),
    ("ZRBHDLX",        "String",    "ZRBHDLX",          250, None),
    ("CS_GHQ",         "SmallInteger","CS_GHQ",          1, None),
    ("DCRY",           "String",    "DCRY",             250, None),
    ("DCRQ",           "String",    "DCRQ",              8, None),
    ("XMMC",           "String",    "XMMC",             200, None),
    ("GJGYLD_MJ",      "Double",    "GJGYLD_MJ",        18, 4),
    ("TRLLD_MJ",       "Double",    "TRLLD_MJ",         18, 4),
    ("SFWFTB",         "String",    "SFWFTB",            3, None),
    ("WFTBMJ",         "Double",    "WFTBMJ",           18, 4),
    ("YC_CQ",          "String",    "YC_CQ",             1, None),
    ("JJLZS",          "Integer",   "JJLZS",             5, None),
    ("SJND",           "String",    "SJND",              4, None),
    ("Shape_Length",   "Double",    "Shape_Length",    None, None),
    ("Shape_Area",     "Double",    "Shape_Area",      None, None),
]

FIELD_TYPE_MAP = {
    "String": "TEXT",
    "Integer": "LONG",
    "SmallInteger": "SHORT",
    "Float": "FLOAT",
    "Double": "DOUBLE",
    "Geometry": "GEOMETRY",
}

# ========== 源→目标字段映射 ==========
# (源字段名, 目标字段名, 特殊处理函数)
# 特殊处理: None=直接复制, "r3"=取后3位, "date"=Date转String
FIELD_MAP = [
    ("xian",        "XIAN",        None),
    ("xiang",       "XIANG",       "r3"),
    ("cun",         "CUN",         "r3"),
    ("lin_ban",     "LIN_BAN",     None),
    ("xiao_ban",    "XIAO_BAN",    None),
    ("xbmj",        "XBMJ",        None),
    ("di_lei",      "DI_LEI",      None),
    ("dlbm",        "DLBM",        None),
    ("ld_qs",       "LD_QS",       None),
    ("bh_dj",       "BH_DJ",       None),
    ("sen_lin_lb",  "SEN_LIN_LB",  None),
    ("lin_zhong",   "LIN_ZHONG",   None),
    ("qi_yuan",     "QI_YUAN",     None),
    ("you_shi_sz",  "YOU_SHI_SZ",  None),
    ("ling_zu",     "LING_ZU",     None),
    ("pingjun_sg",  "PINGJUN_SG",  None),
    ("pingjun_xj",  "PINGJUN_XJ",  None),
    ("HUO_LMGQXJ",  "HUO_LMGQXJ",  None),
    ("bz",          "BZ",          None),
    ("mei_gq_zs",   "MEI_GQ_ZS",   None),
    ("gjgyl_bhdj",  "GJGYL_BHDJ",  None),
    ("yu_bi_du",    "YU_BI_DU",    None),
    ("Y_SQDJ",      "Y_SQDJ",      None),
    ("ZRBHDLX",     "ZRBHDLX",     None),
    ("XMMC",        "XMMC",        None),
    ("YC_CQ",       "YC_CQ",       None),
    ("SJND",        "SJND",        None),
    # 语义映射
    ("BHDMC_1",     "ZRBHQ_MC",    None),
    ("JB",          "ZRBHQ_DJ",    None),
    ("SHU_ZHONG_ZC","SHU_ZHONG_",  None),
    ("XZ",          "LD_XZ",       None),
    ("XIAO_BAN_XJ", "XIAO_BAN_X",  None),
    ("dc_ry",       "DCRY",        None),
    ("dc_rq",       "DCRQ",        "date"),
    (u"建设内容",    "JSNR",        None),
    ("WFQK",        "SFWFTB",      None),
]


def make_field_dict(fields):
    """构建 {大写名: Field对象} 字典"""
    return {f.name.upper(): f for f in fields}


def _text(val):
    if val is None:
        return u""
    try:
        return unicode(val).strip()
    except Exception:
        return str(val).strip()


def _load_county_names():
    county_map = {}
    if not os.path.exists(COUNTY_DBF):
        return county_map
    try:
        with arcpy.da.SearchCursor(COUNTY_DBF, [u"县代码", u"县"]) as cur:
            for code, name in cur:
                if code and name:
                    county_map[_text(code)] = _text(name)
    except Exception:
        pass
    return county_map


def _needs_114_projection(fc):
    county_map = _load_county_names()
    counties = set()
    try:
        field_names = {f.name.upper(): f.name for f in arcpy.ListFields(fc)}
        xian_field = field_names.get("XIAN")
        if not xian_field:
            return False
        with arcpy.da.SearchCursor(fc, [xian_field]) as cur:
            for (xian,) in cur:
                if xian is None:
                    continue
                counties.add(county_map.get(_text(xian), _text(xian)))
    except Exception:
        return False
    return bool(counties) and counties.issubset(SPECIAL_COUNTIES)


def _project_to_114_if_needed(fc):
    if not os.path.exists(PROJECT_114_PRJ):
        print("  警告：114E投影文件不存在，跳过投影")
        return fc
    if not _needs_114_projection(fc):
        return fc

    tmp_fc = gdb + r"\tmp_114_source"
    if arcpy.Exists(tmp_fc):
        arcpy.Delete_management(tmp_fc)
    sr = arcpy.SpatialReference()
    with open(PROJECT_114_PRJ, "r") as f:
        sr.loadFromString(f.read())
    arcpy.Project_management(fc, tmp_fc, sr)
    print("  已将数据投影到CGCS2000_3_Degree_GK_CM_114E")
    return tmp_fc


def add_fields():
    """创建目标要素类并添加字段"""
    print("\n[1/3] 创建要素类...")

    desc = arcpy.Describe(source_fc)
    sr = desc.spatialReference

    if arcpy.Exists(target_fc):
        arcpy.Delete_management(target_fc)
        print("  已删除旧版本")

    arcpy.CreateFeatureclass_management(
        gdb, target_fc_name, "POLYGON",
        spatial_reference=sr
    )

    system_names = {"OBJECTID", "SHAPE", "SHAPE_LENGTH", "SHAPE_AREA"}
    added = 0
    for name, ftype, alias, length, scale in ZZY_FIELDS:
        if name.upper() in system_names:
            continue
        af_type = FIELD_TYPE_MAP.get(ftype, "TEXT")
        # Double类型用 precision+scale
        if ftype == "Double" and length and scale is not None:
            arcpy.AddField_management(
                target_fc, name, af_type,
                field_alias=alias,
                field_precision=length,
                field_scale=scale
            )
        elif ftype == "Double" and length:
            arcpy.AddField_management(
                target_fc, name, af_type,
                field_alias=alias,
                field_precision=length
            )
        elif ftype == "Integer" and length:
            arcpy.AddField_management(
                target_fc, name, af_type,
                field_alias=alias,
                field_precision=length
            )
        else:
            arcpy.AddField_management(
                target_fc, name, af_type,
                field_alias=alias,
                field_length=length
            )
        added += 1

    print("  已添加 {} 个业务字段".format(added))


def copy_data():
    """复制要素几何和属性"""
    print("\n[2/3] 复制数据...")

    src_count = int(arcpy.GetCount_management(source_fc).getOutput(0))
    print("  源要素类记录数: {}".format(src_count))
    if src_count == 0:
        print("  警告：无记录，跳过")
        return

    src_fdict = make_field_dict(arcpy.ListFields(source_fc))
    tgt_fdict = make_field_dict(arcpy.ListFields(target_fc))

    # 构建批量插入字段列表
    src_names = ["SHAPE@"]
    tgt_names = ["SHAPE@"]

    # 记录每列的处理方式
    handlers = {}  # tgt_idx -> handler_key

    for src_key, tgt_key, handler in FIELD_MAP:
        su = src_key.upper()
        tu = tgt_key.upper()
        if su not in src_fdict:
            print("  跳过：源字段 '{}' 不存在".format(src_key))
            continue
        if tu not in tgt_fdict:
            print("  跳过：目标字段 '{}' 不存在".format(tgt_key))
            continue
        src_names.append(src_fdict[su].name)
        tgt_names.append(tgt_fdict[tu].name)
        if handler:
            handlers[len(tgt_names) - 1] = handler

    print("  将复制 {} 个属性字段".format(len(src_names) - 1))

    copied = 0
    try:
        with arcpy.da.SearchCursor(source_fc, src_names) as s_cur:
            with arcpy.da.InsertCursor(target_fc, tgt_names) as i_cur:
                for row in s_cur:
                    vals = list(row)
                    # 逐一处理特殊转换
                    for idx, handler in handlers.items():
                        if vals[idx] is None:
                            continue
                        if handler == "r3":
                            # 取字符串后3位
                            s = str(vals[idx])
                            vals[idx] = s[-3:] if len(s) >= 3 else s
                        elif handler == "date":
                            # Date → String yyyyMMdd
                            vals[idx] = vals[idx].strftime("%Y%m%d")
                    i_cur.insertRow(tuple(vals))
                    copied += 1
    except Exception as e:
        print("  !! 出错！已复制 {} 条后失败".format(copied))
        traceback.print_exc()
        return

    print("  成功复制 {} 条记录".format(copied))


def print_summary():
    """打印空字段和汇总"""
    empty_fields = [
        "SYLDDKXH",
        "SLGY_MC", "SLGY_DJ", "SDGY_MC", "SDGY_DJ",
        "FJMSQ_MC", "FJMSQ_DJ", "DZGY_MC", "DZGY_DJ",
        "HYGY_MC", "HYGY_DJ", "SMGY_MC", "SMGY_DJ",
        "CYGY_MC", "CYGY_DJ",
        "CS_GHQ", "GJGYLD_MJ", "TRLLD_MJ",
        "WFTBMJ", "JJLZS",
    ]
    print("\n[3/3] 空字段清单（已创建、无数据填入）：")
    for f in empty_fields:
        print("  " + f)
    print("  共 {} 个空字段".format(len(empty_fields)))

    # 字段属性验证
    print("\n--- 字段属性检查 ---")
    tgt_fields = {f.name.upper(): f for f in arcpy.ListFields(target_fc)}
    issues = []
    for name, ftype, _, length, scale in ZZY_FIELDS:
        nu = name.upper()
        if nu in ("OBJECTID", "SHAPE", "SHAPE_LENGTH", "SHAPE_AREA"):
            continue
        f = tgt_fields.get(nu)
        if not f:
            issues.append("  {}: 字段不存在！".format(name))
            continue
        # 检查类型
        af_type = FIELD_TYPE_MAP.get(ftype, "TEXT")
        if f.type.upper() != af_type.upper():
            issues.append("  {}: 类型应为 {}，实际为 {}".format(name, af_type, f.type))
        # 检查长度(仅String/Integer)
        if ftype == "String" and length:
            if f.length != length:
                issues.append("  {}: 长度应为 {}，实际为 {}".format(name, length, f.length))
        if ftype == "Integer" and length:
            if f.precision != length:
                issues.append("  {}: 精度应为 {}，实际为 {}".format(name, length, f.precision))
        # 检查小数位
        if ftype == "Double" and scale is not None:
            if f.scale != scale:
                issues.append("  {}: 小数位应为 {}，实际为 {}".format(name, scale, f.scale))

    if issues:
        for msg in issues:
            print(msg)
    else:
        print("  全部字段属性正确！")

    print("\n共计业务字段: {} 个".format(
        len([z for z in ZZY_FIELDS if z[0].upper() not in
             ("OBJECTID", "SHAPE", "SHAPE_LENGTH", "SHAPE_AREA")])))


if __name__ == "__main__":
    print("=" * 60)
    print("  ZYY标准字段版 生成工具")
    print("  来源: {}".format(source_fc))
    print("  输出: {}".format(target_fc))
    print("=" * 60)

    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True

    original_source_fc = source_fc
    try:
        source_fc = _project_to_114_if_needed(source_fc)
        add_fields()
        copy_data()
        print_summary()
        print("\n完成！")
    except Exception as e:
        print("\n错误: {}".format(str(sys.exc_info()[1])))
        traceback.print_exc()
        sys.exit(1)
    finally:
        if source_fc != original_source_fc and arcpy.Exists(source_fc):
            arcpy.Delete_management(source_fc)
