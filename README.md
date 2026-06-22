# LKY_LDKY 征占用林地可研数据整理

把 ZYY 图斑标准化、按县导出，并自动填可研附表、生成报告文字。

## 环境

- **ArcMap（自带 Python 2.7）**：跑 1~4 号脚本。
- **Python 3**（装 `pandas`、`numpy`、`openpyxl`）：跑 5、6 号脚本。
- 代码放 `C:\4code\3lot`；换目录就改 `project_config.py` 里的路径。

## 准备源数据（在 ArcGIS 里手工做）

放进 `C:\4code\3lot\输出结果.gdb`：

| 图层名 | 内容 |
|---|---|
| `多县ZYY空间连接保护区` | 项目红线交林草湿一张图 → 空间连接保护地 → 擦除历史红线 |
| `多县合并红线_擦除历史` | 项目红线按标准结构整理 → 擦除历史（需有 `XIAN` 或 `县代码` 字段） |

> ⚠️ 保护区类型字段需人工核对，代码默认全写成"湿地湖泊类型"。

## 运行

**ArcMap Python 窗口**，依次执行：

```python
exec(open(r"C:\4code\3lot\1-standardZYYshp.py").read())
exec(open(r"C:\4code\3lot\2-standardZYYshpedit.py").read())
execfile(r"C:\4code\3lot\3-export_by_xian.py")
execfile(r"C:\4code\3lot\4-export_xmhx_by_xian.py")
```

**命令行（Python 3）**：

```powershell
python C:\4code\3lot\5-populate_template.py
python C:\4code\3lot\6-写报告.py
```

| 脚本 | 作用 |
|---|---|
| `1-standardZYYshp.py` | 按标准字段结构生成 ZYY 图层 |
| `2-standardZYYshpedit.py` | 单部件化、重算面积、填充并检查字段 |
| `3-export_by_xian.py` | 按县复制模板，导出 `林地图斑\ZZY.shp` |
| `4-export_xmhx_by_xian.py` | 按县导出 `项目红线\XMHX.shp` |
| `5-populate_template.py` | 填可研附表 Excel，打包县目录 |
| `6-写报告.py` | 生成报告小任务文字 |

成果在 `project_config.py` 的 `OUTPUT_BASE` 目录下，每县一个文件夹。

## 加新项目要改

1. `project_config.py`：`ZYY_SOURCE_FC_NAME`、`XMHX_SOURCE_FC_NAME` 指向本次源数据。
2. `ZYY字段属性标准设置.MD` 的"县代码与投影带"表：补新县的县代码、县名、投影带（望城/宁乡/华容/湘阴走 `114E`，其余 `111E`）。
3. 同一个 MD：补新县的乡镇代码、行政村代码及新字段代码字典。

## 换电脑要搬回的数据（不入 git）

- `输出结果.gdb`（源数据）
- 三个模板目录 `模版-1009征占用林地数据模板CGCG2000_108/111/114`
- 各项目 ZYY、项目红线源要素类
- 导出结果目录 `C:\Users\zhong\Downloads\work file\五个垸和防护堤\结果\按县导出结果`

GitHub 只存代码和轻量标准文件。
