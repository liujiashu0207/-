# Cursor 任务指令：投稿主稿 Word 排版定稿

> **优先级**：P0（投稿前最后一步）  
> **目标**：将 `docs/投稿主稿_v1.md` 转换为符合《计算机工程与应用》期刊模板的 `.docx` 文件  
> **输出**：`docs/投稿主稿_v1_submit.docx`

---

## 一、期刊格式要求（来源：http://cea.ceaj.org/CN/column/column16.shtml）

### 1.1 页面设置
- 纸张：A4
- 页边距：上 2.5cm、下 2.5cm、左 2.5cm、右 2.5cm
- 分栏：通栏（单栏）

### 1.2 字体与字号

| 元素 | 中文字体 | 英文字体 | 字号 | 其他 |
|------|----------|----------|------|------|
| 论文标题（中文） | 黑体 | — | 二号 | 居中，加粗 |
| 论文标题（英文） | — | Times New Roman | 四号 | 居中，加粗 |
| 作者姓名 | 宋体 | Times New Roman | 小四号 | 居中 |
| 单位信息 | 宋体 | Times New Roman | 小五号 | 居中 |
| 摘要标题 | 黑体 | — | 五号 | "摘要"二字加粗 |
| 摘要正文 | 楷体 | Times New Roman | 五号 | |
| 关键词标题 | 黑体 | — | 五号 | "关键词"三字加粗 |
| 关键词内容 | 楷体 | Times New Roman | 五号 | 词间用分号分隔 |
| Abstract 标题 | — | Times New Roman | 五号 | 加粗 |
| Abstract 正文 | — | Times New Roman | 五号 | |
| Keywords 标题 | — | Times New Roman | 五号 | 加粗 |
| Keywords 内容 | — | Times New Roman | 五号 | |
| 一级标题（如"1 引言"） | 黑体 | Times New Roman | 四号 | 加粗，顶格 |
| 二级标题（如"1.1 研究背景"） | 黑体 | Times New Roman | 五号 | 加粗，顶格 |
| 三级标题（如"1.1.1 xxx"） | 宋体 | Times New Roman | 五号 | 加粗，顶格 |
| 正文 | 宋体 | Times New Roman | 五号（10.5pt） | 首行缩进 2 字符 |
| 表题/图题 | 宋体 | Times New Roman | 小五号 | 居中 |
| 表内文字 | 宋体 | Times New Roman | 小五号 | |
| 参考文献标题 | 黑体 | — | 五号 | 加粗 |
| 参考文献内容 | 宋体 | Times New Roman | 小五号 | 悬挂缩进 |
| 作者简介 | 宋体 | Times New Roman | 小五号 | |

### 1.3 行距
- 正文：1.5 倍行距
- 摘要、参考文献：单倍行距
- 标题前后各空 0.5 行

### 1.4 表格格式
- **三线表**：只有顶线、表头底线、底线三条横线，无竖线
- 表题在表格上方，居中
- 中英文双语表题（中文在上，英文在下）

### 1.5 图片格式
- 图题在图片下方，居中
- 中英文双语图题（中文在上，英文在下）
- 图片宽度不超过页面文字区域宽度
- 图片分辨率 ≥ 300 DPI

### 1.6 公式
- 公式居中，编号右对齐
- 公式编号格式：(1)、(2)、(3)……（按章编号也可）

### 1.7 参考文献
- GB/T 7714-2015 顺序编码制
- 正文引用用方括号上标，如 [1]、[2,3]、[4-6]

---

## 二、源文件说明

### 2.1 主稿文件
- **路径**：`docs/投稿主稿_v1.md`
- **编码**：UTF-8
- **状态**：内容已定稿（Round 19），含中英文摘要、6章正文、11条参考文献、5张图嵌入

### 2.2 图片文件（共 5 张，均在 `figures/` 目录下）

| 论文中编号 | 文件名 | 中文图题 | 英文图题 |
|-----------|--------|----------|----------|
| 图 1 | `fig1_runtime_comparison_v3.png` | 各算法运行时间对比（按地图类型） | Runtime comparison of algorithms by map type |
| 图 2 | `fig2_turncount_comparison_v3.png` | 各算法转弯次数对比（按地图类型） | Turn count comparison of algorithms by map type |
| 图 3 | `fig3_ablation_study_v3.png` | 消融实验各配置性能对比 | Performance comparison of ablation configurations |
| 图 4 | `path_comparison_6maps_v3.png` | 路径对比可视化（传统 A* vs 改进 A*，6 张代表性地图） | Path comparison visualization (standard A* vs. improved A*, 6 representative maps) |
| 图 5 | `fig5_nodes_vs_obstacle_v3.png` | 扩展节点数与地图障碍率的关系 | Expanded nodes vs. obstacle ratio |

### 2.3 首页元信息（已在 Markdown 中，需按格式排版）

```
标题：面向移动机器人的自适应加权 A* 路径规划算法研究
英文标题：Research on Adaptive Weighted A* Path Planning Algorithm for Mobile Robots
作者：刘家树
单位：南方科技大学 机械与能源工程系，广东 深圳 518055
英文作者：LIU Jiashu
英文单位：Department of Mechanical and Energy Engineering, Southern University of Science and Technology, Shenzhen 518055, China
中图分类号：TP301.6
文献标识码：A
作者简介：刘家树（2007—），男，本科生，研究方向为机器人路径规划，E-mail：12412724@mail.sustech.edu.cn。
```

---

## 三、具体执行步骤

### 步骤 1：安装依赖
```bash
pip install python-docx Pillow --break-system-packages
```

### 步骤 2：编写 Python 转换脚本

用 `python-docx` 库创建 `.docx` 文件。**不要用 pandoc**（pandoc 无法精确控制中文字体和期刊格式）。

核心逻辑：
1. 逐行解析 `docs/投稿主稿_v1.md`
2. 识别标题层级（`#` → 一级标题，`##` → 二级标题，`###` → 三级标题，`####` → 四级标题）
3. 识别表格（`|...|` 行）→ 创建三线表
4. 识别图片嵌入（`![](figures/xxx.png)`）→ 插入图片
5. 识别图题（`**图 X**` 开头行）→ 居中小五号
6. 识别公式（`$$...$$` 块）→ 居中段落
7. 识别参考文献（`[1]` 开头行）→ 小五号悬挂缩进
8. 其他 → 正文段落（宋体五号，首行缩进 2 字符）

### 步骤 3：关键排版细节

#### 三线表实现
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_table_three_line(table):
    """设置三线表：顶线粗、表头底线中、底线粗，其余无边框"""
    tbl = table._tbl
    tblBorders = OxmlElement('w:tblBorders')
    for border_name, sz, val in [
        ('top', '12', 'single'),      # 顶线 1.5pt
        ('bottom', '12', 'single'),    # 底线 1.5pt  
        ('insideH', '4', 'single'),    # 表头底线 0.5pt（只出现在第一行下方）
        ('left', '0', 'none'),
        ('right', '0', 'none'),
        ('insideV', '0', 'none'),
    ]:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), val)
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '000000')
        tblBorders.append(border)
    tbl.tblPr.append(tblBorders)
```

#### 图片插入
```python
from docx.shared import Inches, Cm

# 图片宽度设为页面文字区域宽度（A4 减去左右页边距）
# A4宽度 21cm - 左2.5cm - 右2.5cm = 16cm
MAX_IMG_WIDTH = Cm(15)  # 留一点余量

doc.add_picture(img_path, width=MAX_IMG_WIDTH)
```

#### 首行缩进
```python
from docx.shared import Pt, Cm

paragraph_format = paragraph.paragraph_format
paragraph_format.first_line_indent = Cm(0.74)  # 约2个五号字宽度
```

### 步骤 4：输出与验证
```bash
python scripts/convert_to_docx.py
# 输出到 docs/投稿主稿_v1_submit.docx
```

验证清单：
- [ ] 打开 Word 确认中文显示为宋体，英文显示为 Times New Roman
- [ ] 标题层级字号正确（二号→四号→五号）
- [ ] 表格为三线表样式
- [ ] 图片清晰且位置正确（图1/5在5.2.1后，图2/4在5.2.3后，图3在5.3后）
- [ ] 公式正常显示
- [ ] 参考文献编号 [1]-[11] 完整
- [ ] 首页作者信息完整

---

## 四、硬约束

1. **不改任何正文内容**——只做格式转换
2. **不改任何实验数值**
3. **不改参考文献内容**——只调格式
4. **图片使用原始 PNG**——不压缩、不裁剪
5. **如果 python-docx 无法完美实现某个格式**（如复杂公式），保留占位并在文件中用红色高亮标注"需手动调整"

---

## 五、备选方案

如果 python-docx 实现太复杂，可以采用以下替代方案：

### 方案 B：pandoc + 参考模板
1. 从 http://cea.ceaj.org/CN/column/column18.shtml 下载期刊 Word 模板
2. 用该模板作为 pandoc 的 `--reference-doc`
3. `pandoc docs/投稿主稿_v1.md -o docs/投稿主稿_v1_submit.docx --reference-doc=模板.docx`
4. 手动在 Word 中调整剩余格式问题

### 方案 C：手动排版
1. 打开已生成的 `投稿主稿_v1_final.docx`（pandoc 基础版）
2. 全选正文 → 宋体五号 + Times New Roman + 1.5倍行距
3. 逐级调整标题字体字号
4. 手动将表格改为三线表
5. 调整图片大小

**推荐方案 C**——最快最可靠，约 30-60 分钟可完成。
