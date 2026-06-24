# -*- coding: utf-8 -*-
"""统计：从 ZYY 与红线中剔除「二期工程调减的地块」，分别计算减少量。

口径：
  - 几何面积（Shape_Area，CGCS2000 / 3度带 / 中央经线111E，单位米）为减少量主口径。
  - 业务字段原值（ZYY 的 XBMJ、红线的 XMPFNYTDMJ 与 NSYLDMJ）一并报出供对照。
  - ZYY 减少量 = 用调减地块擦除 ZYY 本体后的几何面积差。
  - 红线减少量 = 用调减地块擦除红线本体后的几何面积差。

注意：调减地块 SR 为 CGCS2000_3_Degree_GK_Zone_37，与 ZYY/红线的
CGCS2000_3_Degree_GK_CM_111E 同属 111E 带（数值一致），但 SR 定义不同，
先投影统一到 CM_111E 再做擦除，保证几何运算正确。

输出：在 输出结果.gdb 内生成 ZYY_擦除调减、红线_擦除调减 两个要素类，
      并把统计结果写入 6-报告小任务结果.md。
"""

import os
import arcpy
from project_config import GDB

ZYY_NAME = u"多县ZYY_标准字段版"
HX_NAME = u"多县合并红线_擦除历史"
E_NAME = u"二期工程调减的地块"

ZYY_OUT = u"ZYY_擦除调减"
HX_OUT = u"红线_擦除调减"
PROJ_TEMP = u"_调减地块_投影到111E"  # 临时投影结果

ZYY_AREA_FIELD = u"XBMJ"            # ZYY 小班面积（业务字段）
HX_PF_FIELD = u"XMPFNYTDMJ"         # 红线 项目拟使用林地面积
HX_NS_FIELD = u"NSYLDMJ"            # 红线 拟使用林地面积（ZYY 的 XBMJ 合计）

REPORT_MD = os.path.join(os.path.dirname(GDB), u"8-剔除调减地块统计.md")


def _sum_field(fc, field):
    total = 0.0
    count = 0
    with arcpy.da.SearchCursor(fc, [field]) as cur:
        for (v,) in cur:
            if v is not None:
                try:
                    total += float(v)
                except (TypeError, ValueError):
                    pass
            count += 1
    return total, count


def _geom_area_sum(fc):
    """几何面积合计（平方米），用 Shape_Area 字段。"""
    total, _ = _sum_field(fc, u"SHAPE@AREA")
    return total


def _mu(m2):
    return m2 / 666.6667


def _delete_if_exists(fc_path):
    if arcpy.Exists(fc_path):
        arcpy.Delete_management(fc_path)


def main():
    arcpy.env.workspace = GDB
    arcpy.env.overwriteOutput = True

    zyy_fc = GDB + u"/" + ZYY_NAME
    hx_fc = GDB + u"/" + HX_NAME
    e_fc = GDB + u"/" + E_NAME

    target_sr = arcpy.Describe(zyy_fc).spatialReference
    e_sr = arcpy.Describe(e_fc).spatialReference
    print(u"ZYY SR : {}".format(target_sr.name))
    print(u"红线 SR: {}".format(arcpy.Describe(hx_fc).spatialReference.name))
    print(u"调减 SR: {}".format(e_sr.name))

    # 1) 投影统一调减地块到目标 SR
    e_proj = GDB + u"/" + PROJ_TEMP
    _delete_if_exists(e_proj)
    if e_sr.name != target_sr.name:
        print(u"投影调减地块 -> {}".format(target_sr.name))
        arcpy.Project_management(e_fc, e_proj, target_sr)
    else:
        arcpy.CopyFeatures_management(e_fc, e_proj)
    erase_fc = e_proj

    # 2) 擦除 ZYY
    zyy_out = GDB + u"/" + ZYY_OUT
    _delete_if_exists(zyy_out)
    print(u"擦除 ZYY ...")
    arcpy.Erase_analysis(zyy_fc, erase_fc, zyy_out)

    # 3) 擦除红线
    hx_out = GDB + u"/" + HX_OUT
    _delete_if_exists(hx_out)
    print(u"擦除 红线 ...")
    arcpy.Erase_analysis(hx_fc, erase_fc, hx_out)

    # 清理临时投影
    _delete_if_exists(e_proj)

    # 4) 统计
    zyy_before = _geom_area_sum(zyy_fc)
    zyy_after = _geom_area_sum(zyy_out)
    zyy_dec = zyy_before - zyy_after
    zyy_xbmj_before, zyy_n_before = _sum_field(zyy_fc, ZYY_AREA_FIELD)
    zyy_xbmj_after, zyy_n_after = _sum_field(zyy_out, ZYY_AREA_FIELD)

    hx_before = _geom_area_sum(hx_fc)
    hx_after = _geom_area_sum(hx_out)
    hx_dec = hx_before - hx_after
    hx_pf_before, _ = _sum_field(hx_fc, HX_PF_FIELD)
    hx_pf_after, _ = _sum_field(hx_out, HX_PF_FIELD)
    hx_ns_before, _ = _sum_field(hx_fc, HX_NS_FIELD)
    hx_ns_after, _ = _sum_field(hx_out, HX_NS_FIELD)

    zyy_cnt_before = int(arcpy.GetCount_management(zyy_fc).getOutput(0))
    zyy_cnt_after = int(arcpy.GetCount_management(zyy_out).getOutput(0))
    hx_cnt_before = int(arcpy.GetCount_management(hx_fc).getOutput(0))
    hx_cnt_after = int(arcpy.GetCount_management(hx_out).getOutput(0))

    # 5) 打印
    print(u"\n========== 统计结果（几何面积，平方米 / 亩）==========")
    print(u"\n[ZYY 林地]")
    print(u"  擦除前: {} 个图斑, 几何面积 {:.4f} ㎡ ({:.2f} 亩)".format(
        zyy_cnt_before, zyy_before, _mu(zyy_before)))
    print(u"  擦除后: {} 个图斑, 几何面积 {:.4f} ㎡ ({:.2f} 亩)".format(
        zyy_cnt_after, zyy_after, _mu(zyy_after)))
    print(u"  减少量: {:.4f} ㎡ ({:.2f} 亩), 占原 {:.2f}%".format(
        zyy_dec, _mu(zyy_dec), (zyy_dec / zyy_before * 100) if zyy_before else 0))
    print(u"  XBMJ 字段原值合计 {:.4f} 公顷（仅对照，擦除后 {:.4f}）".format(
        zyy_xbmj_before, zyy_xbmj_after))

    print(u"\n[红线 项目完整矢量]")
    print(u"  擦除前: {} 个多边形, 几何面积 {:.4f} ㎡ ({:.2f} 亩)".format(
        hx_cnt_before, hx_before, _mu(hx_before)))
    print(u"  擦除后: {} 个多边形, 几何面积 {:.4f} ㎡ ({:.2f} 亩)".format(
        hx_cnt_after, hx_after, _mu(hx_after)))
    print(u"  减少量: {:.4f} ㎡ ({:.2f} 亩), 占原 {:.2f}%".format(
        hx_dec, _mu(hx_dec), (hx_dec / hx_before * 100) if hx_before else 0))
    print(u"  XMPFNYTDMJ 字段原值合计 {:.4f} 公顷（擦除后 {:.4f}）".format(
        hx_pf_before, hx_pf_after))
    print(u"  NSYLDMJ   字段原值合计 {:.4f} 公顷（擦除后 {:.4f}）".format(
        hx_ns_before, hx_ns_after))

    # 6) 写报告 md
    write_report(zyy_cnt_before, zyy_cnt_after, zyy_before, zyy_after, zyy_dec,
                 zyy_xbmj_before, zyy_xbmj_after,
                 hx_cnt_before, hx_cnt_after, hx_before, hx_after, hx_dec,
                 hx_pf_before, hx_pf_after, hx_ns_before, hx_ns_after)
    print(u"\n报告已写入: {}".format(REPORT_MD))


def write_report(zcb, zca, zb, za, zd, zxb, zxa,
                 hcb, hca, hb, ha, hd, hpb, hpa, hnb, hna):
    lines = []
    lines.append(u"# 报告小任务：剔除「二期工程调减的地块」面积统计\n")
    lines.append(u"## 一、口径说明\n")
    lines.append(u"- **减少量主口径**：几何面积（Shape_Area），坐标 CGCS2000 / 3度带 / 中央经线111E，单位平方米（同时换算亩，1亩≈666.6667㎡）。")
    lines.append(u"- **算法**：用「二期工程调减的地块」分别擦除 ZYY（多县ZYY_标准字段版）与红线（多县合并红线_擦除历史），擦除前后几何面积差即为减少量。")
    lines.append(u"- 调减地块原 SR 为 CGCS2000_3_Degree_GK_Zone_37，与 ZYY/红线的 CM_111E 同属 111E 带，已先投影统一再做擦除。")
    lines.append(u"- 业务字段（XBMJ / XMPFNYTDMJ / NSYLDMJ，单位均为**公顷**）原值一并列出供对照；因擦除会切割图斑、字段值不按面积拆分，**业务字段差不可直接当作减少量**，减少量以几何面积为准。\n")
    lines.append(u"## 二、ZYY（林地矢量）减少量\n")
    lines.append(u"| 项目 | 擦除前 | 擦除后 | 减少量 |")
    lines.append(u"| --- | --- | --- | --- |")
    lines.append(u"| 图斑数 | {} | {} | {} |".format(zcb, zca, zcb - zca))
    lines.append(u"| 几何面积(㎡) | {:.4f} | {:.4f} | {:.4f} |".format(zb, za, zd))
    lines.append(u"| 几何面积(亩) | {:.2f} | {:.2f} | {:.2f} |".format(_mu(zb), _mu(za), _mu(zd)))
    lines.append(u"| 占原比例 | 100% | {:.2f}% | {:.2f}% |".format(
        (za / zb * 100) if zb else 0, (zd / zb * 100) if zb else 0))
    lines.append(u"| XBMJ字段合计(公顷,仅对照) | {:.4f} | {:.4f} | — |".format(zxb, zxa))
    lines.append(u"")
    lines.append(u"## 三、红线（项目完整矢量）减少量\n")
    lines.append(u"| 项目 | 擦除前 | 擦除后 | 减少量 |")
    lines.append(u"| --- | --- | --- | --- |")
    lines.append(u"| 多边形数 | {} | {} | {} |".format(hcb, hca, hcb - hca))
    lines.append(u"| 几何面积(㎡) | {:.4f} | {:.4f} | {:.4f} |".format(hb, ha, hd))
    lines.append(u"| 几何面积(亩) | {:.2f} | {:.2f} | {:.2f} |".format(_mu(hb), _mu(ha), _mu(hd)))
    lines.append(u"| 占原比例 | 100% | {:.2f}% | {:.2f}% |".format(
        (ha / hb * 100) if hb else 0, (hd / hb * 100) if hb else 0))
    lines.append(u"| XMPFNYTDMJ字段合计(公顷,仅对照) | {:.4f} | {:.4f} | — |".format(hpb, hpa))
    lines.append(u"| NSYLDMJ字段合计(公顷,仅对照) | {:.4f} | {:.4f} | — |".format(hnb, hna))
    lines.append(u"")
    lines.append(u"## 四、结论\n")
    lines.append(u"- ZYY 减少 **{:.2f} 亩**（{:.4f} ㎡，占原 {:.2f}%）。".format(
        _mu(zd), zd, (zd / zb * 100) if zb else 0))
    lines.append(u"- 红线减少 **{:.2f} 亩**（{:.4f} ㎡，占原 {:.2f}%）。".format(
        _mu(hd), hd, (hd / hb * 100) if hb else 0))
    lines.append(u"- 擦除结果已写入：`输出结果.gdb/ZYY_擦除调减`、`输出结果.gdb/红线_擦除调减`。\n")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(u"\n".join(lines))


if __name__ == "__main__":
    main()
