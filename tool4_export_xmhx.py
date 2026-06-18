# -*- coding: utf-8 -*-
"""
工具4：按县导出XMHX（运行 4-export_xmhx_by_xian.py）
ArcMap 工具属性 Parameter 标签页按顺序配：
  参数1 GDB路径           Workspace or String
  参数2 项目红线源要素类名 String            （如 多县合并红线_擦除历史）
  参数3 县界要素类名       String            （如 重点垸三调县界_M）
  参数4 模板目录           Folder
  参数5 输出根目录         Folder
  参数6 默认投影带         String  默认值 111
"""
import arcpy
from LKY_toolbox import _run_script, _need

gdb = arcpy.GetParameterAsText(0)
src_name = arcpy.GetParameterAsText(1)
boundary_name = arcpy.GetParameterAsText(2)
template_dir = arcpy.GetParameterAsText(3)
output_base = arcpy.GetParameterAsText(4)
default_zone = arcpy.GetParameterAsText(5) or "111"

arcpy.AddMessage(u"=" * 50)
arcpy.AddMessage(u"工具4 按县导出XMHX")
arcpy.AddMessage(u"  GDB       : {}".format(gdb))
arcpy.AddMessage(u"  红线源     : {}".format(src_name))
arcpy.AddMessage(u"  县界要素类 : {}".format(boundary_name))
arcpy.AddMessage(u"  模板目录   : {}".format(template_dir))
arcpy.AddMessage(u"  输出目录   : {}".format(output_base))
arcpy.AddMessage(u"  默认投影带 : {}".format(default_zone))
arcpy.AddMessage(u"=" * 50)

_need(gdb, src_name, boundary_name, template_dir, output_base)

_run_script("4-export_xmhx_by_xian.py", {
    "GDB": gdb,
    "XMHX_SOURCE_FC_NAME": src_name,
    "COUNTY_BOUNDARY_FC_NAME": boundary_name,
    "TEMPLATE_DIR_111": template_dir,
    "OUTPUT_BASE": output_base,
    "DEFAULT_ZONE": default_zone,
})
arcpy.AddMessage(u"工具4 完成。")
