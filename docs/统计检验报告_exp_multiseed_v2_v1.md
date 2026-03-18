# 统计检验报告 v1

## 方法
- 检验对象：`improved_astar` 对比 `astar / weighted_astar / jps_like / dijkstra`
- 分场景检验：按 `size x ratio` 分组
- 指标：`runtime_ms`, `path_length`, `turn_count`
- 检验方法：双侧置换检验（permutation test）
- 置换次数：`5000`

## 结果文件
- `results/exp_multiseed_v2_significance.csv`

## 对比传统A*的显著性统计
- 运行时间显著场景数（p<0.05）：`8`
- 路径长度显著场景数（p<0.05）：`8`
- 转弯次数显著场景数（p<0.05）：`8`
- 运行时间显著场景数（FDR q<0.05）：`8`
- 路径长度显著场景数（FDR q<0.05）：`8`
- 转弯次数显著场景数（FDR q<0.05）：`8`

## 备注
- 置换检验不依赖正态分布假设，适合当前小样本与非高斯分布场景。
- 已加入 Benjamini-Hochberg 多重比较校正，减少多指标多场景带来的假阳性风险。
