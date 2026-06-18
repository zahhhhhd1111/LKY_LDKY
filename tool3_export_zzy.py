# -*- coding: utf-8 -*-
"""
工具3：按县导出ZZY（运行 3-export_by_xian.py）
ArcMap 工具属性 Parameter 标签页按顺序配：
  参数1 GDB路径           Workspace or String
  参数2 标准字段版要素类名 String
  参数3 模板目录           Folder              （如 模版-1009征占用林地数据模板CGCG2000_111）
  参数4 输出根目录         Folder              （如 ...按县导出结果）
  参数5 默认投影带         String  默认值 111
"""
import arcpy
from LKY_toolbox import _run_script, _need

gdb = arcpy.GetParameterAsText(0)
tgt_name = arcpy.GetParameterAsText(1)
template_dir = arcpy.GetParameterAsText(2)
output_base = arcpy.GetParameterAsText(3)
default_zone = arcpy.GetParameterAsText(4) or "111"

arcpy.AddMessage(u"=" * 50)
arcpy.AddMessage(u"工具3 按县导出ZZY")
arcpy.AddMessage(u"  GDB       : {}".format(gdb))
arcpy.AddMessage(u"  要素类     : {}".format(tgt_name))
arcpy.AddMessage(u"  模板目录   : {}".format(template_dir))
arcpy.AddMessage(u"  输出目录   : {}".format(output_base))
arcpy.AddMessage(u"  默认投影带 : {}".format(default_zone))
arcpy.AddMessage(u"=" * 50)

_need(gdb, tgt_name, template_dir, output_base)

_run_script("3-export_by_xian.py", {
    "GDB": gdb,
    "ZYY_TARGET_FC_NAME": tgt_name,
    "TEMPLATE_DIR_111": template_dir,
    "OUTPUT_BASE": output_base,
    "DEFAULT_ZONE": default_zone,
})
arcpy.AddMessage(u"工具3 完成。")
