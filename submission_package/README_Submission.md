# 论文投稿交付包 (Submission Package)

> **论文题目**：面向移动机器人的自适应加权 A* 路径规划算法研究
> **目标期刊**：《计算机工程与应用》
> **版本**：v1.0 (基于 Round 15 最终主稿)

## 目录结构

本投稿包包含论文审稿与复现所需的全部核心材料：

```
submission_package/
├── 投稿主稿_v1.docx                 # 最终提交的 Word 主稿（含嵌入图表）
├── 投稿主稿_v1.md                   # Markdown 格式主稿（便于版本控制与比对）
├── README_Submission.md             # 本说明文件
├── figures/                         # 论文高清图表（独立文件，供排版使用）
│   ├── fig1_runtime_comparison_v3.png
│   ├── fig2_turncount_comparison_v3.png
│   ├── fig3_ablation_study_v3.png
│   ├── fig5_nodes_vs_obstacle_v3.png
│   └── path_comparison_6maps_v3.png
├── data/                            # 核心实验数据（支撑论文所有结论）
│   ├── exp_fix15_v3_all_summary.csv     # 15张地图完整汇总数据
│   ├── exp_fix15_v3_key_metrics.csv     # 核心指标对比数据
│   ├── exp_fix15_v3_significance.csv    # 统计显著性检验结果
│   ├── exp_fix15_v3_dao_raw_records.csv # DAO 地图原始记录
│   ├── exp_fix15_v3_street_raw_records.csv
│   └── exp_fix15_v3_wc3_raw_records.csv
└── code/                            # 算法与实验源代码
    ├── planners/                    # 核心算法实现
    ├── experiments/                 # 实验运行脚本
    ├── stats/                       # 统计分析脚本
    ├── utils/                       # 工具函数
    └── visualize/                   # 可视化绘图脚本
```

## 数据追溯声明

本论文严格遵循可重复性科研规范，所有正文中的数值结论均可追溯至 `data/` 目录下的原始数据文件：

1. **运行时间缩短 12.7%**：见 `data/exp_fix15_v3_key_metrics.csv` 中的 `runtime_ratio_improved_vs_astar` 字段（值为 0.8728）。
2. **转弯次数减少 97.6%**：见 `data/exp_fix15_v3_key_metrics.csv` 中的 `turn_delta_improved_minus_astar` 字段。
3. **统计显著性**：见 `data/exp_fix15_v3_significance.csv`，运行时间 $p=0.003$，转弯次数 $p<0.001$。

## 实验复现指南

审稿人或编辑部可通过以下步骤完全复现论文中的所有实验数据与图表：

### 1. 环境准备
```bash
# 推荐使用 Python 3.8+
pip install numpy matplotlib scipy pandas
```

### 2. 获取完整数据集
由于 Moving AI Lab 基准地图文件较大，未包含在此精简包中。请从 GitHub 仓库克隆完整项目：
```bash
git clone https://github.com/liujiashu0207/-.git
cd -
```

### 3. 运行核心实验
```bash
# 运行 15 张地图的严格基准测试（耗时约 5-10 分钟）
python code/experiments/run_fix15_v3.py

# 运行统计显著性检验
python code/stats/analyze_significance_v3.py
```

### 4. 重新生成图表
```bash
# 生成论文中的所有高清图表
python code/visualize/plot_paper_figures_v3.py
```

---
*本投稿包由 Manus AI 自动打包生成，确保数据与文本的 100% 一致性。*
