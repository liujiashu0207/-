# CLAUDE.md — 论文项目全局配置

> 本文件为 Cursor / Claude / Manus 等 AI 助手的项目级配置文件。
> 适用于：《基于改进 A* 算法的栅格地图路径规划研究》

---

## 一、项目概况

- **论文题目**：面向移动机器人的自适应加权 A* 路径规划算法研究
- **目标期刊**：《计算机工程与应用》（北大核心 + EI 收录）
- **备选期刊**：《计算机应用研究》（CSCD）
- **当前状态**：主稿已完成（`docs/投稿主稿_v1.docx`），处于最终润色与定稿阶段
- **唯一权威数据**：`results/exp_fix15_v3_all_summary.csv`（15张地图 × 30次，2700条记录）

---

## 二、可用 Skills（按优先级排序）

### 写作润色类（最常用）

| Skill | 路径 | 功能 | 触发场景 |
|---|---|---|---|
| **humanize-academic-writing** | `.cursor/skills/humanize-academic-writing/SKILL.md` | 学术写作去 AI 化，含检测脚本 | 润色段落、降低 AI 检测风险 |
| **humanizer** | `.cursor/skills/humanizer/SKILL.md` | 快速去除 AI 写作痕迹 | 编辑或审查任何文本段落 |
| **stop-slop** | `.cursor/skills/stop-slop/SKILL.md` | 消除 AI 写作套路（规则最精炼） | 起草、编辑、审查文本 |

### 格式排版类

| Skill | 路径 | 功能 | 触发场景 |
|---|---|---|---|
| **cursor-latex-skill** | `.cursor/skills/cursor-latex-skill/CLAUDE.md` | LaTeX 科学写作辅助 | 如需将论文转为 LaTeX 格式 |

### 项目已有 Skills（原有配置）

| Skill | 路径 | 功能 |
|---|---|---|
| paper-section-writer-zh | `.cursor/skills/paper-section-writer-zh/SKILL.md` | 中文论文章节写作 |
| result-audit-stats | `.cursor/skills/result-audit-stats/SKILL.md` | 实验结果统计审计 |
| submission-packager-cn | `.cursor/skills/submission-packager-cn/SKILL.md` | 投稿打包 |
| paper-figure-generator | `.cursor/skills/paper-figure-generator/SKILL.md` | 论文图表生成 |
| literature-screener-cn | `.cursor/skills/literature-screener-cn/SKILL.md` | 文献筛选 |

---

## 三、写作规范（核心原则）

### 3.1 数值引用铁律
- 所有数值必须来源于 `results/exp_fix15_v3_all_summary.csv`（v3 strict scen 口径）
- 核心指标：运行时间比 **0.8728x**（快约 12.7%）、路径长度缩短 **4.9%**、转弯次数减少 **97.6%**
- 引用数值时需注明证据来源（如"见表 5-1"）

### 3.2 去 AI 化要点
- 禁止使用：`此外`（连续使用）、`值得注意的是`、`综合来看`、`不难发现`
- 禁止句式：连续三句相同结构开头；先提问再自答
- 正确做法：直接陈述，数据先行，逻辑自然流动

### 3.3 参考文献规范
- 严格遵守 GB/T 7714-2015
- 编号按正文首次出现顺序排列（当前存在 [10][11] 先于 [9] 的问题，需修复）

---

## 四、当前 P0/P1 待办

### 🔴 P0（投稿前必须完成）
1. 合并第1章1.2节与第2章的重复文献综述内容
2. 修复参考文献引用顺序（[9] 需先于 [10][11] 出现）
3. 统一 4.7 节承诺与第5章实际（补标准差 或 修改4.7节表述）

### 🟡 P1（强烈建议完成）
1. 在第5章各段末补充图表引用语句（见图1、见图2……）
2. 解释消融实验微小异常（无自适应权重时转弯次数 0.0244 < 完整模型 0.0267）
3. 补充自适应权重公式的物理直觉说明（对数映射选择依据、上界 1.8 的确定方法）

---

## 五、关键文件索引

| 文件 | 说明 |
|---|---|
| `docs/投稿主稿_v1.md` | 主稿 Markdown 版（最新：Round 13） |
| `docs/投稿主稿_v1.docx` | 主稿 Word 版（含嵌入图表） |
| `results/exp_fix15_v3_key_metrics.csv` | 唯一权威指标汇总 |
| `results/exp_fix15_v3_all_summary.csv` | 完整实验数据（90行） |
| `figures/fig1_runtime_comparison_v3.png` | 运行时间对比图 |
| `figures/fig2_turncount_comparison_v3.png` | 转弯次数对比图 |
| `figures/fig3_ablation_study_v3.png` | 消融实验对比图 |
| `figures/path_comparison_6maps_v3.png` | 路径可视化对比图（图4） |
| `figures/fig5_nodes_vs_obstacle_v3.png` | 扩展节点数 vs 障碍率图 |
| `docs/结论-证据对照表_v3_Manus.md` | 每条论文声明对应的精确数值证据 |
| `code/planners/core.py` | 核心算法实现 |
| `code/experiments/run_fix15_v3.py` | 权威实验脚本 |

---

*配置更新时间：2026-03-19 | 配置者：Manus AI*
