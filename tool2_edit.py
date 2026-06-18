# -*- coding: utf-8 -*-
"""
工具2：整理ZYY字段（运行 2-standardZYYshpedit.py）
ArcMap 工具属性 Parameter 标签页按顺序配：
  参数1 GDB路径           Workspace or String
  参数2 标准字段版要素类名 String              （同工具1的输出名）
  参数3 标准文件MD路径     String              （ZYY字段属性标准设置.MD）
  参数4 默认投影带         String  默认值 111
"""
import arcpy
from LKY_toolbox import _run_script, _need

gdb = arcpy.GetParameterAsText(0)
tgt_name = arcpy.GetParameterAsText(1)
standard_file = arcpy.GetParameterAsText(2)
default_zone = arcpy.GetParameterAsText(3) or "111"

arcpy.AddMessage(u"=" * 50)
arcpy.AddMessage(u"工具2 整理ZYY字段")
arcpy.AddMessage(u"  GDB       : {}".format(gdb))
arcpy.AddMessage(u"  要素类     : {}".format(tgt_name))
arcpy.AddMessage(u"  标准文件   : {}".format(standard_file))
arcpy.AddMessage(u"  默认投影带 : {}".format(default_zone))
arcpy.AddMessage(u"=" * 50)

_need(gdb, tgt_name, standard_file)

_run_script("2-standardZYYshpedit.py", {
    "GDB": gdb,
    "ZYY_TARGET_FC_NAME": tgt_name,
    "STANDARD_FILE": standard_file,
    "DEFAULT_ZONE": default_zone,
})
arcpy.AddMessage(u"工具2 完成。")
