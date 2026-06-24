# LKY_LDKY 工具箱使用说明（给只会 ArcGIS 的同事）

把 1~4 号脚本做成了 **ArcMap 工具箱**，以后不用复制粘贴 `exec(open(...))` 那几行了，**双击工具、填几个参数、点 OK 就跑**。

> 5、6 号脚本依赖 pandas/openpyxl，ArcMap 自带的 Python 2.7 跑不了，所以没做进工具箱，仍按 README 第四节用命令行（Python 3）跑。

---

## 一、工具箱里有哪些工具

| 工具 | 对应脚本 | 作用 |
|---|---|---|
| 工具1 标准化ZYY字段 | `1-standardZYYshp.py` | 按 ZYY 标准字段结构生成新图层，把源数据复制进去 |
| 工具2 整理ZYY字段 | `2-standardZYYshpedit.py` | 单部件化、重算面积、按标准翻译填充字段、检查 |
| 工具3 按县导出ZZY | `3-export_by_xian.py` | 复制模板目录，按县导出 `林地图斑\ZZY.shp` |
| 工具4 按县导出XMHX | `4-export_xmhx_by_xian.py` | 按县导出、合并项目红线 `项目红线\XMHX.shp` |

四个工具**按顺序跑**，和原来 1→2→3→4 一样。

---

## 二、一次性安装（建工具箱、挂工具）

`.tbx` 工具箱文件没法用代码生成，需要在 ArcMap 里手动建一次，建好以后就能一直双击用。

### 第 1 步：建工具箱

1. 打开 ArcMap。
2. 打开 **Catalog 窗口**（菜单 `Windows` → `Catalog`，或点工具栏上的地球+文件夹图标）。
3. 在 Catalog 里找到代码目录 `C:\4code\3lot`，**右键 → New → Toolbox**。
4. 把新建的工具箱改名为 `LKY_LDKY`（生成 `LKY_LDKY.tbx`）。

### 第 2 步：往工具箱里加 4 个工具

对下面 4 个脚本，**每个都重复一遍**这个操作：

1. 右键 `LKY_LDKY.tbx` → `Add` → `Script...`（弹出向导）。
2. **第一页**：
   - Name / Label：填下表"工具名"。
   - 勾掉 "Store relative path names"（用绝对路径更稳）。
   - 点 Next。
3. **第二页**：Script File 选对应的 `toolN_xxx.py`（在 `C:\4code\3lot` 下）。点 Next。
4. **第三页（参数页）**：按下表的"参数表"逐行添加参数。每一行点进去，左侧填参数显示名（任意，自己认得就行），右侧 `Data Type` 选对应的类型。填完点 Finish。

加好 4 个工具后，工具箱里就有 4 个图标了。

### 4 个工具的参数表

#### 工具1：标准化ZYY字段（指向 `tool1_standardize.py`）

| # | 参数显示名（自定） | Data Type | 默认值/示例 |
|---|---|---|---|
| 1 | GDB路径 | Workspace or String | `C:\4code\3lot\输出结果.gdb` |
| 2 | ZYY源要素类名 | String | `多县ZYY空间连接保护区` |
| 3 | 标准字段版输出名 | String | `多县ZYY_标准字段版` |
| 4 | 默认投影带 | String | `111`（108/111/114） |

#### 工具2：整理ZYY字段（指向 `tool2_edit.py`）

| # | 参数显示名（自定） | Data Type | 默认值/示例 |
|---|---|---|---|
| 1 | GDB路径 | Workspace or String | `C:\4code\3lot\输出结果.gdb` |
| 2 | 标准字段版要素类名 | String | `多县ZYY_标准字段版` |
| 3 | 标准文件MD路径 | String | `C:\4code\3lot\ZYY字段属性标准设置.MD` |
| 4 | 默认投影带 | String | `111（括号需删除，填的是多县合并矢量的投影带）` |

#### 工具3：按县导出ZZY（指向 `tool3_export_zzy.py`）

| # | 参数显示名（自定） | Data Type | 默认值/示例 |
|---|---|---|---|
| 1 | GDB路径 | Workspace or String | `C:\4code\3lot\输出结果.gdb` |
| 2 | 标准字段版要素类名 | String | `多县ZYY_标准字段版` |
| 3 | 模板目录 | Folder | `C:\4code\3lot\模版-1009征占用林地数据模板CGCG2000_111` |
| 4 | 输出根目录 | Folder | `C:\Users\zhong\Downloads\work file\五个垸和防护堤\结果\按县导出结果` |
| 5 | 默认投影带 | String | `111` |

#### 工具4：按县导出XMHX（指向 `tool4_export_xmhx.py`）

| # | 参数显示名（自定） | Data Type | 默认值/示例 |
|---|---|---|---|
| 1 | GDB路径 | Workspace or String | `C:\4code\3lot\输出结果.gdb` |
| 2 | 项目红线源要素类名 | String | `多县合并红线_擦除历史` |
| 3 | 县界要素类名 | String | `重点垸三调县界_M` |
| 4 | 模板目录 | Folder | `C:\4code\3lot\模版-1009征占用林地数据模板CGCG2000_111` |
| 5 | 输出根目录 | Folder | `C:\Users\zhong\Downloads\work file\五个垸和防护堤\结果\按县导出结果` |
| 6 | 默认投影带 | String | `111` |

> **小提示**：在参数页右下角可以给每个参数设 Default，下次开工具自动带出来，少打字。

### 第 3 步：设默认参数值（可选但强烈建议）

填完参数后，回到工具箱，**右键某个工具 → Properties → Parameters 标签页**，给每行参数填一个 Default。这样以后双击工具，参数框已经预填好，日常只要确认/微调即可。

---

## 三、日常怎么用

1. 源数据准备好（按 README 第三节：ZYY 命名 `多县ZYY空间连接保护区`、红线命名 `多县合并红线_擦除历史`，都存进 `输出结果.gdb`）。
2. 双击 **工具1** → 确认参数 → OK → 等它跑完（看进度条/消息窗口）。
3. 双击 **工具2** → OK → 等跑完。
4. 双击 **工具3** → OK → 等跑完。
5. 双击 **工具4** → OK → 等跑完。
6. 5、6 号在命令行用 Python 3 跑（见 README 第四节）。

工具跑的过程和原来在 Python 窗口里跑完全一样，只是入口从"粘四行代码"变成"双击填表"。

---

## 四、常见问题

**Q：双击工具报错"找不到脚本 / 找不到 project_config"？**
A：工具脚本必须和 1~4 号源脚本、`project_config.py` 在同一个目录（`C:\4code\3lot`）。如果换目录，所有路径都要一起搬，并在工具属性里重选 Script File。

**Q：跑完没看到 print 输出？**
A：原脚本里有 `reload(sys)` 会重置输出流。包装脚本已经做了恢复，但若仍无输出，点工具对话框的 **Results** 窗口（菜单 `Geoprocessing` → `Results`）能看到全部 `arcpy.AddMessage` 消息。

**Q：工具跑报"参数不完整"？**
A：工具对话框里有空格没填。GDB、要素类名、模板目录、输出目录这些是必填，投影带不填默认 111。

**Q：换了一个新项目，参数怎么改？**
A：直接在工具对话框里改对应的源要素类名/输出名即可，**不用再改 `project_config.py`**（工具参数会临时覆盖它）。这是工具箱相对命令行的主要好处。

**Q：`.tbx` 文件能给别人/新电脑用吗？**
A：可以拷贝 `.tbx`，但拷过去后要在新电脑 ArcMap 里**右键工具 → Properties → 重新指定 Script File**（因为绝对路径变了）。代码文件（`toolN_*.py`、`LKY_toolbox.py`、`project_config.py`、1~6 号源脚本）要一起拷到 `C:\4code\3lot`。
