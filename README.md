# 改进 A* 路径规划算法

> **论文题目**：面向移动机器人的自适应加权 A* 路径规划算法研究
> **目标期刊**：《计算机工程与应用》（北大核心 + EI）
> **实验基准**：Moving AI Lab 真实地图（DAO / Street / WC3，共 15 张地图，2700 条记录）

---

## 仓库结构

```
.
├── code/                        # 核心算法与实验代码
│   ├── planners/                # 算法实现（core.py 为主文件）
│   ├── experiments/             # 实验脚本（run_fix15_v3.py 为权威实验）
│   ├── stats/                   # 统计分析脚本
│   ├── utils/                   # 工具函数
│   └── visualize/               # 可视化脚本
├── data/                        # 实验数据集
│   ├── benchmark_maps/          # Moving AI Lab 地图文件（.map）
│   └── benchmark_scens/         # 场景文件（.scen），按 dao/street/wc3 分类
├── docs/                        # 论文文档
│   ├── 投稿主稿_v1.docx         # ★ 最新主稿（Word，含嵌入图表）
│   ├── 投稿主稿_v1.md           # ★ 最新主稿（Markdown）
│   ├── 结论-证据对照表_v3.md    # 每条声明对应的精确数值证据
│   ├── 科研透明看板.md           # 项目进度看板
│   ├── 图文一致性审计_v1.md     # 图表与正文一致性检查
│   ├── 主稿审查评估报告_v1_Manus.md
│   └── 论文现状评估报告_Manus.md
├── figures/                     # 论文最终图表（共 5 张）
│   ├── fig1_runtime_comparison_v3.png    # 图1：运行时间对比
│   ├── fig2_turncount_comparison_v3.png  # 图2：转弯次数对比
│   ├── fig3_ablation_study_v3.png        # 图3：消融实验
│   ├── path_comparison_6maps_v3.png      # 图4：路径可视化对比
│   └── fig5_nodes_vs_obstacle_v3.png     # 图5：扩展节点数 vs 障碍率
├── results/                     # 权威实验数据（v3 strict scen 口径）
│   ├── exp_fix15_v3_all_summary.csv      # ★ 完整汇总（90行）
│   ├── exp_fix15_v3_key_metrics.csv      # ★ 核心指标汇总
│   ├── exp_fix15_v3_significance.csv     # 显著性检验结果
│   ├── exp_fix15_v3_dao_raw_records.csv  # DAO 原始数据
│   ├── exp_fix15_v3_street_raw_records.csv
│   ├── exp_fix15_v3_wc3_raw_records.csv
│   ├── adaptive_alpha_gridsearch_raw.csv # 自适应权重参数搜索原始数据
│   ├── adaptive_alpha_gridsearch_summary.csv
│   ├── adaptive_alpha_recommendation.csv
│   ├── literature_core8.csv             # 核心文献数据
│   └── literature_quick_screen.csv      # 文献筛选记录
├── scripts/                     # 辅助脚本
│   └── manus_auto_monitor.py
├── 科研论文/文献/               # 参考文献 PDF（10 篇）
├── .cursor/                     # AI 助手配置
│   ├── rules/                   # Cursor 写作规则（academic-paper-cn.mdc）
│   └── skills/                  # 写作 Skills（humanize、stop-slop 等）
├── CLAUDE.md                    # 项目全局 AI 配置（Skills 索引 + 写作规范）
└── README.md                    # 本文件
```

---

## 核心实验结果（v3 权威数据）

| 指标 | 标准 A* | 改进 A* | 提升幅度 |
|---|---|---|---|
| 运行时间 | 基准 | 0.8728x | **快 12.7%** |
| 路径长度 | 基准 | 0.9510x | **缩短 4.9%** |
| 转弯次数 | 1.131 次 | 0.027 次 | **减少 97.6%** |

> 数据来源：`results/exp_fix15_v3_key_metrics.csv`（15 张地图 × 30 次重复 = 2700 条记录）

---

## 算法创新点

1. **Octile 启发函数**：专为 8 邻域移动设计，比曼哈顿/欧氏距离更准确。
2. **自适应权重**：$\alpha = \text{clip}(|\ln(\rho)|, 1.0, 1.8)$，根据局部障碍率动态调整搜索偏向。
3. **两阶段路径平滑**：先 Line-of-Sight 消除冗余折点，再 B 样条插值平滑曲率。

---

## 快速复现

```bash
# 克隆仓库
git clone https://github.com/liujiashu0206/-.git && cd -

# 安装依赖
pip install numpy matplotlib

# 运行权威实验（v3 strict scen，15 张地图 × 30 次）
python code/experiments/run_fix15_v3.py

# 查看核心指标
cat results/exp_fix15_v3_key_metrics.csv
```

> 所有脚本使用相对路径，请在项目根目录下运行。

---

*最后更新：2026-03-20 | 维护：Manus AI + Cursor*
