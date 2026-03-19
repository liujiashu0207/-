# 阶段二-第1步 结果审查快照

## 数据来源
- `results/exp_fix15_key_metrics.csv`
- `results/exp_fix15_all_summary.csv`

## 样本覆盖
- 地图数: 15
- 算法: ablation_no_adaptive / ablation_no_smoothing / astar / dijkstra / improved_astar / weighted_astar

## 关键指标（improved_astar 相对 astar）
- 运行时间比: 0.981186（<1 代表更快）
- 路径长度差: -0.297997
- 转弯次数差: -1.102222
- 扩展节点差: -0.571111

## 审查结论（待确认）
- 15图标准实验显示：改进算法在路径质量与运行时间上同时具备优势。
- 通过后进入第2步：将这些数值回填到结果章节草稿。