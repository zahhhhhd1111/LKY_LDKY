# 数据准备
# ZYY与XMHX需进行如下处理：
# XMHX：
项目红线按标准结构表整理好，命名为“多县合并红线_擦除历史”，存入工程目录下的“输出数据”数据库即可。
# ZYY：
1、项目红线交林草湿一张图后空间连接保护地数据；2、检查DILEI与DLMC，添加相关备注到BZ字段；3、可能会存在BZ_1以及其他无关字段，无需删除；4、擦除历史红线
ZYY仅需处理上述内容，命名为“多县ZYY空间连接保护区”，存入工程目录下的“输出数据”数据库即可。

# 注意
自然保护区类型字段需要检查，当前代码将所有保护区类型命名为湿地湖泊类型

# 下面是工程（LKY_LDKY）具体描述 及代码用法

本工程用于征占用林地可研数据整理：把 ZYY 图斑标准化、按县导出 ZZY/XMHX，并自动填充可研附表模板。

## 运行环境

- ArcGIS Desktop/ArcMap Python 2.7 + `arcpy`：运行 `1-4` 号脚本。
- Python 3：运行 `5-populate_template.py`，依赖 `pandas`、`numpy`、`openpyxl`。
- 推荐放在 `C:\4code\3lot`。如果换目录，先改 `project_config.py` 里的路径。

## 不入库的数据

GitHub 只保存代码和轻量标准文件，不保存 GDB、shp/dbf、模板目录、xlsx 成果、压缩包、安装包、`.pyc` 等本地数据或产物。

接手项目时需要把这些数据放回本机：

- `输出结果.gdb` (在代码目录下新建一个数据库，用于存放源数据)
- `模版-1009征占用林地数据模板CGCG2000_108`
- `模版-1009征占用林地数据模板CGCG2000_111`
- `模版-1009征占用林地数据模板CGCG2000_114`
- 各次项目的 ZYY 源要素类、项目红线源要素类
- 导出结果目录：`C:\Users\zhong\Downloads\work file\五个垸和防护堤\结果\按县导出结果`

## 配置入口

所有常改配置集中在 `project_config.py`：

- `ZYY_SOURCE_FC_NAME`：空间连接保护区后的 ZYY 源要素类。
- `ZYY_TARGET_FC_NAME`：标准字段版 ZYY 输出要素类。
- `XMHX_SOURCE_FC_NAME`：项目红线源要素类。
- `OUTPUT_BASE`：按县导出结果目录。

县名、县代码、投影带直接写在 `ZYY字段属性标准设置.MD` 的“县代码与投影带”表。当前 16 县中，望城区、宁乡市、华容县、湘阴县走 114E，其余走 111E；如后续有 108E 县，直接把该县投影带写成 `108`。
项目红线源要素类按县导出时需要有 `XIAN` 或 `县代码` 字段。

## 标准流程

在 ArcGIS Python 窗口运行：

```python
exec(open(r"C:\4code\3lot\1-standardZYYshp.py").read())
exec(open(r"C:\4code\3lot\2-standardZYYshpedit.py").read())
execfile(r"C:\4code\3lot\3-export_by_xian.py")
execfile(r"C:\4code\3lot\4-export_xmhx_by_xian.py")
```

然后用 Python 3 运行：

```powershell
python C:\4code\3lot\5-populate_template.py
```


## 添加新项目时要补什么

除了更新新的 ZYY 空间连接保护区源数据，还要检查：

1. `ZYY字段属性标准设置.MD` 的“县代码与投影带”表是否包含新增县的 `县代码`、`县`、`投影带`。
2. `ZYY字段属性标准设置.MD` 是否包含新增县的乡镇代码、行政村代码，以及新出现的字段代码字典。
3. `project_config.py` 的 `ZYY_SOURCE_FC_NAME`、`ZYY_TARGET_FC_NAME` 是否指向本次项目。
4. `XMHX_SOURCE_FC_NAME` 是否换成包含新增县的项目红线源要素类。
5. 新增县若要按 108E/111E/114E 导出，在 MD 表里直接写对应投影带。
6. 如果新增县超出现有 108E/111E/114E 范围，需要补对应模板目录和 `.prj`，并扩展代码。

## 文件说明

- `1-standardZYYshp.py`：按标准字段结构生成 ZYY 要素类。
- `2-standardZYYshpedit.py`：单部件化、面积重算、字段填充和字段检查。
- `3-export_by_xian.py`：按县复制模板并导出 `林地图斑\ZZY.shp`。
- `4-export_xmhx_by_xian.py`：按县导出、合并项目红线 `项目红线\XMHX.shp`。
- `5-populate_template.py`：读取各县 ZZY，填充可研附表模板并压缩县目录。
- `project_config.py`：项目路径、源数据名、模板目录等配置。
- `ZYY字段属性标准设置.MD`：字段值翻译、县名/投影带、乡镇/村代码等标准表。

辅助读取脚本（`read_*`、`check_*`、`analyze.py`）主要用于排查模板和字段标准。
