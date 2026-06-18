# -*- coding: utf-8 -*-
"""
工具1：标准化ZYY字段（运行 1-standardZYYshp.py）
ArcMap 工具属性 Parameter 标签页按顺序配：
  参数1 GDB路径           Workspace or String   （如 C:\4code\3lot\输出结果.gdb）
  参数2 ZYY源要素类名     String                （如 多县ZYY空间连接保护区）
  参数3 标准字段版输出名  String                （如 多县ZYY_标准字段版）
  参数4 默认投影带         String  默认值 111     （108/111/114）
"""
import arcpy
from LKY_toolbox import _run_script, _need

gdb = arcpy.GetParameterAsText(0)
src_name = arcpy.GetParameterAsText(1)
tgt_name = arcpy.GetParameterAsText(2)
default_zone = arcpy.GetParameterAsText(3) or "111"

arcpy.AddMessage(u"=" * 50)
arcpy.AddMessage(u"工具1 标准化ZYY字段")
arcpy.AddMessage(u"  GDB       : {}".format(gdb))
arcpy.AddMessage(u"  源要素类   : {}".format(src_name))
arcpy.AddMessage(u"  输出要素类 : {}".format(tgt_name))
arcpy.AddMessage(u"  默认投影带 : {}".format(default_zone))
arcpy.AddMessage(u"=" * 50)

_need(gdb, src_name, tgt_name)

_run_script("1-standardZYYshp.py", {
    "GDB": gdb,
    "ZYY_SOURCE_FC_NAME": src_name,
    "ZYY_TARGET_FC_NAME": tgt_name,
    "DEFAULT_ZONE": default_zone,
})
arcpy.AddMessage(u"工具1 完成。")
