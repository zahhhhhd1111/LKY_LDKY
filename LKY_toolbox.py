# -*- coding: utf-8 -*-
"""
LKY_LDKY ArcMap 工具箱公共运行器（Python 2.7 / arcpy）

把 1~4 号源脚本包装成 ArcMap 工具箱里的工具，双击填参数即可运行。
**不修改任何现有源代码**：原理是在 exec 每个原脚本之前，临时把用户填的参数
覆盖到 project_config 模块属性上（原脚本用 `from project_config import ...`
即时读取，exec 前覆盖即生效）。

本文件只提供公共函数 _run_script；每个工具各自的脚本（tool1.py ... tool4.py）
读界面参数后调用 _run_script。这样每个工具的 GetParameterAsText(0) 都是
第一个业务参数，索引无歧义。详细安装步骤见 README_工具箱.md。
"""

import os
import sys

import arcpy
import project_config

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


def _run_script(script_name, config_overrides):
    """临时覆盖 project_config 属性，然后在隔离 globals 里 exec 原脚本。

    config_overrides: {属性名: 新值}
    """
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        raise RuntimeError(u"找不到脚本: {}".format(script_path))

    # 保存旧值，跑完恢复，避免污染同进程后续工具
    saved = {}
    for key, val in config_overrides.items():
        saved[key] = getattr(project_config, key)
        setattr(project_config, key, val)

    # 保存 stdout/stderr：原脚本顶部 reload(sys) 会重置输出流，
    # 导致 ArcMap 工具对话框收不到 print。前后夹住恢复回 arcpy 的流。
    saved_stdout, saved_stderr = sys.stdout, sys.stderr

    # 隔离 globals：每个脚本独立命名空间，避免 target_fc/gdb 跨脚本串味。
    # __name__ 设为 __main__ 让带守卫的脚本（1/2号）执行入口块。
    script_globals = {
        "__name__": "__main__",
        "__file__": script_path,
        "__builtins__": __builtins__,
    }

    try:
        with open(script_path, "rb") as f:
            source = f.read()
        exec(compile(source, script_path, "exec"), script_globals)
    finally:
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr
        for key, val in saved.items():
            setattr(project_config, key, val)


def _need(*vals):
    if not all(vals):
        arcpy.AddError(u"参数不完整，请把工具对话框里的空参数都填上。")
        raise ValueError(u"missing params")
