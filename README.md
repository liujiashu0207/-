# 改进 A* 路径规划算法

> 面向移动机器人的自适应加权 A* 路径规划算法研究  
> 基于 Moving AI Lab 真实地图基准测试（DAO / Street / WC3，共 15 张地图）

---

## 唯一源代码目录

**`code/`** 是本项目的唯一源代码目录，所有实验、可视化脚本均从此处导入。

> `科研论文/code/` 已于 Round5 归档至 `results/obsolete_pre_v3/科研论文_code_archive/`，不再维护，不得引用。

---

## 算法创新点

本项目在标准 A* 基础上提出三项改进：

1. **Octile 启发函数**：专为 8 邻域移动设计，比曼哈顿/欧氏距离更准确。
2. **自适应权重 α**：根据地图障碍率自动调节搜索激进程度（`α = clip(|ln(ρ)|, 1.0, 1.8)`）。
3. **两阶段路径平滑**：冗余点删除（Line-of-Sight）+ 拐角插值平滑，大幅减少转弯次数。

> **注**：JPS-like 扩展策略已于 Round4/5 彻底移除，全仓库 grep 确认无任何残留。

---

## 从零复现 v3 实验结果（单命令）

```bash
# 1. 克隆仓库
git clone https://github.com/liujiashu0202/-.git
cd -

# 2. 安装依赖（仅需 numpy）
pip install numpy

# 3. 运行实验（strict scen 口径，15 张地图 × 30 次）
python code/experiments/run_fix15_v3.py

# 4. 查看关键指标
cat results/exp_fix15_v3_key_metrics.csv

# 5. 生成路径对比可视化图
python code/visualize/plot_path_comparison.py
# 输出：figures/path_comparison_6maps_v3_Manus.png
```

> **注意**：所有脚本使用相对路径，必须在项目根目录（`-/`）下运行。

---

## 权威结果文件（v3，strict scen 口径）

| 文件 | 说明 |
|---|---|
| `results/exp_fix15_v3_all_summary.csv` | 15 张地图 × 6 算法的完整汇总（90 行） |
| `results/exp_fix15_v3_key_metrics.csv` | 改进 A* vs 传统 A* 的关键指标对比 |
| `results/exp_fix15_v3_dao_raw_records.csv` | DAO 地图原始记录（900 行） |
| `results/exp_fix15_v3_street_raw_records.csv` | Street 地图原始记录（900 行） |
| `results/exp_fix15_v3_wc3_raw_records.csv` | WC3 地图原始记录（900 行） |
| `docs/结论-证据对照表_v3.md` | 每条论文结论对应的 CSV 字段与图文件名（唯一权威引用路径） |

> **已废弃（obsolete）**：`results/obsolete_pre_v3/` 目录下的所有文件均为旧版实验数据，不得用于论文引用。  
> **注**：`科研论文/docs/结论-证据对照表_v3_Manus.md` 为历史路径，已同步至 `docs/结论-证据对照表_v3.md`，请统一引用主路径。

---

## 核心实验结果（v3，strict scen，15 张地图均值）

| 指标 | 传统 A* | 改进 A* | 变化 |
|---|---|---|---|
| 运行时间 | 基准 | **0.8728x** | 快约 13% |
| 路径长度 | 基准 | **-0.30** | 缩短 |
| 转弯次数 | 基准 | **-1.10 次** | 减少 |

---

## 目录结构

```
.
├── code/                     ← 唯一源代码目录
│   ├── planners/
│   │   ├── algorithms.py     # 核心算法（A*, 改进A*, 消融变体）
│   │   └── core.py           # 基础工具（启发函数、路径平滑等）
│   ├── experiments/
│   │   └── run_fix15_v3.py   # 主实验脚本（strict scen 口径）
│   └── visualize/
│       └── plot_path_comparison.py  # 路径对比可视化（相对路径，跨平台）
├── data/
│   ├── benchmark_maps/       # Moving AI 真实地图（.map 格式）
│   └── benchmark_scens/      # 固定测试任务（.scen 格式）
├── docs/                     ← 项目级权威文档（唯一引用路径）
│   └── 结论-证据对照表_v3.md # 每条论文结论 → CSV 字段 + 图文件名（可追溯）
├── results/
│   ├── exp_fix15_v3_*.csv    # 权威实验结果（v3，唯一口径）
│   └── obsolete_pre_v3/      # 已废弃的旧版数据（含 科研论文/code 归档）
├── figures/                  # 实验图表
└── 科研论文/
    └── docs/                 # 论文草稿与分析报告（科研论文/docs/结论-证据对照表_v3_Manus.md 已同步至 docs/）
```

---

## 环境要求

- Python 3.8+
- numpy（`pip install numpy`）
- matplotlib（仅可视化需要，`pip install matplotlib`）

---

*本项目由 Manus AI 辅助开发与审查，Cursor 协同编码，所有实验数据均基于 Moving AI Lab 公开基准测试集。*
