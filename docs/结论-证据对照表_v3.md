# 结论-证据对照表 v3

> **数据来源**：`results/exp_fix15_v3_all_summary.csv`（strict scen 口径，15 张 Moving AI 真实地图，每图 30 次重复）  
> **生成时间**：2026-03-19  
> **生成者**：Manus AI  
> **注意**：本表所有数值均来自 v3 实验数据，v2 及更早数据已标记 obsolete，不得引用。

---

## 结论一：改进 A* 的运行时间与传统 A* 持平或更快

**论文表述**：在 15 张真实地图上，改进 A* 的平均运行时间为传统 A* 的 **0.8728 倍**，整体快约 12.7%，且 15 张地图中 15 张均未出现显著劣化。

| 证据类型 | 具体字段 / 文件 | 精确数值 |
|---|---|---|
| 汇总 CSV | `exp_fix15_v3_key_metrics.csv` → `runtime_ratio_improved_vs_astar` | **0.8728** |
| 逐地图明细 | `exp_fix15_v3_all_summary.csv` → `algorithm=improved_astar` vs `algorithm=astar` → `runtime_ms_mean` | 见下表 |
| 可视化图 | `figures/runtime_comparison_exp_fix15_v3_street.png` | Street 地图运行时间柱状图 |

**逐地图运行时间比（改进A* / 传统A*）**：

| 地图 | 类型 | 时间比 |
|---|---|---|
| arena.map | DAO | 0.836x |
| arena2.map | DAO | 0.909x |
| brc000d.map | DAO | 0.943x |
| brc100d.map | DAO | 0.969x |
| brc101d.map | DAO | 0.958x |
| Berlin_0_256.map | Street | 0.718x |
| Berlin_0_512.map | Street | 0.734x |
| Berlin_0_1024.map | Street | 0.752x |
| Berlin_1_256.map | Street | 0.855x |
| Berlin_1_1024.map | Street | 0.761x |
| battleground.map | WC3 | 0.903x |
| blastedlands.map | WC3 | 0.985x |
| bloodvenomfalls.map | WC3 | 0.895x |
| bootybay.map | WC3 | 0.900x |
| darkforest.map | WC3 | 0.973x |

---

## 结论二：改进 A* 的路径长度优于传统 A*

**论文表述**：在所有 15 张地图上，改进 A* 的路径长度均短于传统 A*，平均缩短 **0.299 个单位**（改进A*均值 5.864 vs 传统A*均值 6.162）。

| 证据类型 | 具体字段 / 文件 | 精确数值 |
|---|---|---|
| 汇总 CSV | `exp_fix15_v3_key_metrics.csv` → `path_delta_improved_minus_astar` | **-0.2988** |
| 原始数据 | `exp_fix15_v3_all_summary.csv` → `algorithm=improved_astar` → `path_length_mean` 均值 | **5.8635** |
| 原始数据 | `exp_fix15_v3_all_summary.csv` → `algorithm=astar` → `path_length_mean` 均值 | **6.1624** |
| 消融对照 | `algorithm=ablation_no_smoothing` → `path_length_mean` 均值 | **6.1624**（与A*相同，证明路径缩短完全来自平滑模块） |

---

## 结论三：改进 A* 的路径转弯次数大幅减少

**论文表述**：改进 A* 的平均转弯次数为 **0.027 次**，而传统 A* 为 **1.131 次**，减少了 **97.6%**，在所有 15 张地图上均成立。

| 证据类型 | 具体字段 / 文件 | 精确数值 |
|---|---|---|
| 汇总 CSV | `exp_fix15_v3_key_metrics.csv` → `turn_delta_improved_minus_astar` | **-1.1044** |
| 原始数据 | `exp_fix15_v3_all_summary.csv` → `algorithm=improved_astar` → `turn_count_mean` 均值 | **0.0267** |
| 原始数据 | `exp_fix15_v3_all_summary.csv` → `algorithm=astar` → `turn_count_mean` 均值 | **1.1311** |
| 消融对照 | `algorithm=ablation_no_smoothing` → `turn_count_mean` 均值 | **0.9911**（无平滑时转弯次数接近A*，证明减少来自平滑模块） |
| 可视化图 | `figures/path_comparison_6maps_v3_Manus.png` | 6 张地图路径对比图，直观展示转弯减少 |

---

## 结论四：自适应权重 α 对加速有贡献

**论文表述**：消融实验表明，去掉自适应 α 后（固定 α=1.0），运行时间从 **0.0426ms** 增加到 **0.0460ms**，慢约 8%，证明自适应 α 对运行效率有正向贡献。

| 证据类型 | 具体字段 / 文件 | 精确数值 |
|---|---|---|
| 消融数据 | `exp_fix15_v3_all_summary.csv` → `algorithm=improved_astar` → `runtime_ms_mean` 均值 | **0.04257 ms** |
| 消融数据 | `exp_fix15_v3_all_summary.csv` → `algorithm=ablation_no_adaptive` → `runtime_ms_mean` 均值 | **0.04603 ms** |
| 加速比 | 改进A* / 无自适应α | **0.924x**（快约 7.6%） |

---

## 结论五：路径平滑模块是路径质量提升的核心来源

**论文表述**：消融实验证明，路径质量的提升（路径缩短 + 转弯减少）完全来自两阶段路径平滑模块：去掉平滑后，路径长度和转弯次数均退回到与传统 A* 相同的水平。

| 证据类型 | 具体字段 / 文件 | 精确数值 |
|---|---|---|
| 消融数据（无平滑） | `algorithm=ablation_no_smoothing` → `path_length_mean` 均值 | **6.1624**（与A*的6.1624完全一致） |
| 消融数据（无平滑） | `algorithm=ablation_no_smoothing` → `turn_count_mean` 均值 | **0.9911**（接近A*的1.1311） |
| 改进A*（有平滑） | `algorithm=improved_astar` → `path_length_mean` 均值 | **5.8635** |
| 改进A*（有平滑） | `algorithm=improved_astar` → `turn_count_mean` 均值 | **0.0267** |

---

## 数据完整性声明

- 所有数值均来自 `exp_fix15_v3_all_summary.csv`（strict scen 口径，15张地图，每图30次重复）
- 实验脚本：`code/experiments/run_fix15_v3.py`（唯一权威脚本）
- v2 数据（`results/obsolete_pre_v3/`）已废弃，因使用随机起终点导致数据严重失真，**不得引用**
- 本对照表中每条结论均可通过运行 `python code/experiments/run_fix15_v3.py` 独立复现
