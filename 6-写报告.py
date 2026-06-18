# -*- coding: utf-8 -*-
"""
按县生成报告小任务结果。

每个小任务写成一个独立函数，并在 TASKS 中注册。
运行时通过 --task 选择任务，结果输出为 Markdown。
"""

import argparse
import importlib.util
from pathlib import Path

from project_config import OUTPUT_BASE, STANDARD_FILE, COUNTY_CODE_TO_NAME


PROJECT_NAME = "湖南省洞庭湖区重点垸堤防加固二期工程"
PROJECT_USE = "主要用于一线防洪大堤堤防加固"
DEFAULT_OUTPUT = Path(__file__).with_name("6-报告小任务结果.md")


def load_code5():
    path = Path(__file__).with_name("5-populate_template.py")
    spec = importlib.util.spec_from_file_location("populate_template_code5", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def county_name(code5, value, fallback):
    code = code5._norm_code(value, 6)
    return COUNTY_CODE_TO_NAME.get(code) or fallback


def location_text(df, code5, town_names, vill_names, fallback_county):
    groups = location_groups(df, code5, town_names, vill_names, fallback_county)

    by_town = []
    for town, village in groups:
        if not by_town or by_town[-1][0] != town:
            by_town.append([town, []])
        by_town[-1][1].append(village)

    parts = []
    for town, villages in by_town:
        clean_villages = [v for v in villages if v and v != town]
        parts.append("{}{}".format(town, "、".join(clean_villages)))
    return "、".join(parts)


def location_groups(df, code5, town_names, vill_names, fallback_county):
    seen = set()
    groups = []

    for _, row in df.iterrows():
        xian_code = code5._norm_code(row.get("XIAN", ""), 6)
        xiang_code = code5._norm_code(row.get("XIANG", ""), 3)
        cun_code = code5._norm_code(row.get("CUN", ""), 3)
        xian_name = COUNTY_CODE_TO_NAME.get(xian_code) or fallback_county
        town = town_names.get((xian_code, xiang_code)) or xiang_code
        village = (
            vill_names.get((xian_name, xiang_code, cun_code))
            or vill_names.get((xiang_code, cun_code))
            or cun_code
        )
        key = (town, village)
        if town and village and key not in seen:
            seen.add(key)
            groups.append(key)
    return groups


def format_area(area):
    return f"{area:.4f}".rstrip("0").rstrip(".")


def task_forestland_application(cname, df, code5, town_names, vill_names):
    """使用林地申请说明：按县生成一段文字。"""
    area = sum(code5._num(v) for v in df.get("XBMJ", []))
    first_xian = df.iloc[0].get("XIAN", "") if len(df) else ""
    county = county_name(code5, first_xian, cname)
    location = location_text(df, code5, town_names, vill_names, county)

    return (
        f"{PROJECT_NAME}需使用{county}林地{format_area(area)}公顷，"
        f"{PROJECT_USE}，地点位于{location}。林地权属界线明晰，无争议。\n"
        f"为确保项目的顺利实施，特申请项目使用林地{format_area(area)}公顷。"
    )


def ownership_detail_line(label, df, code5, town_names, vill_names, county):
    if df.empty:
        return f"{label}林地：无。"

    location = location_text(df, code5, town_names, vill_names, county)
    groups = location_groups(df, code5, town_names, vill_names, county)
    town_count = len({town for town, _village in groups})
    village_count = len({(town, village) for town, village in groups})
    return (
        f"{label}林地：{county}等1个县（区、市）"
        f"{location}等{town_count}个镇{village_count}个行政村。"
    )


def task_used_forestland_unit_detail(cname, df, code5, town_names, vill_names):
    """被使用林地单位明细表：按国有、集体林地列出涉及单位。"""
    first_xian = df.iloc[0].get("XIAN", "") if len(df) else ""
    county = county_name(code5, first_xian, cname)

    if "LD_QS" in df.columns:
        ownership = df["LD_QS"].apply(code5._normalize_ownership)
    else:
        ownership = "集体"

    state_df = df.loc[ownership == "国有"]
    collective_df = df.loc[ownership == "集体"]
    return "\n".join([
        "被使用林地单位明细表",
        ownership_detail_line("国有", state_df, code5, town_names, vill_names, county),
        ownership_detail_line("集体", collective_df, code5, town_names, vill_names, county),
    ])


TASKS = {
    "forestland_application": {
        "category": "使用林地申请说明",
        "title": "使用林地申请说明",
        "func": task_forestland_application,
    },
    "used_forestland_unit_detail": {
        "category": "被使用林地单位明细表",
        "title": "被使用林地单位明细表",
        "func": task_used_forestland_unit_detail,
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="按县执行报告小任务并输出 Markdown")
    parser.add_argument(
        "--task",
        default="all",
        choices=["all"] + sorted(TASKS.keys()),
        help="要执行的小任务模块；all 表示全部任务",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="输出 Markdown 文件名或完整路径",
    )
    return parser.parse_args()


def output_path(name):
    path = Path(name)
    if path.is_absolute():
        return path
    return Path(__file__).with_name(name)


def main():
    args = parse_args()
    selected_tasks = TASKS.items() if args.task == "all" else [(args.task, TASKS[args.task])]
    code5 = load_code5()
    town_names = code5.parse_township_names(STANDARD_FILE)
    vill_names = code5.parse_village_names(STANDARD_FILE)
    counties = code5.discover_counties(OUTPUT_BASE)

    if not counties:
        print("未发现可处理县目录: {}".format(OUTPUT_BASE))
        return

    county_data = []
    for cname in counties:
        zzy = Path(OUTPUT_BASE) / cname / "林地图斑" / "ZZY.shp"
        df = code5.read_zzy_shp(str(zzy))
        if df is None or len(df) == 0:
            print("跳过 {}: 无 ZZY 数据".format(cname))
            continue
        county_data.append((cname, df))

    out = ["# 报告小任务结果", ""]
    current_category = None
    for _task_name, task in selected_tasks:
        if task["category"] != current_category:
            current_category = task["category"]
            out.extend(["## {}".format(current_category), ""])
        out.extend(["### {}".format(task["title"]), ""])
        for cname, df in county_data:
            paragraph = task["func"](cname, df, code5, town_names, vill_names)
            out.extend(["#### {}".format(cname), "", paragraph, ""])

    md_path = output_path(args.output)
    md_path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print("\n".join(out))
    print("已生成: {}".format(md_path))


if __name__ == "__main__":
    main()
