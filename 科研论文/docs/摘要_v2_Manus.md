# 摘要（v2，已更新为 v3 权威数据）

> 撰写：Manus AI | 更新日期：2026-03-19
> 数据来源：`results/exp_fix15_v3_key_metrics.csv`（strict scen 口径，15 张地图 × 30 次，2700 条记录）
> 变更说明：v1 基于旧版随机采样数据，本版已全面替换为 v3 strict scen 权威数据。

---

## 中文摘要

针对标准 A* 算法在 8 邻域栅格地图中存在的路径质量差、启发函数精度不足和环境适应性弱等问题，本文提出一种综合改进的 A* 路径规划算法。所提算法采用 Octile 距离作为启发函数，引入基于地图障碍率的自适应权重机制，并设计了结合视线简化与拐角插值平滑的两阶段路径后处理策略。自适应权重按 $\alpha = \text{clip}(|\ln(\text{障碍率})|, 1.0, 1.8)$ 计算，用于工程加速，严格最优性不作保证（$\alpha > 1$ 时为 $\alpha$-最优）；平滑过程引入障碍物碰撞检测，保证平滑后路径的物理合法性。

在 Moving AI Lab 基准数据集的 15 张真实地图（涵盖 DAO 游戏地图、Street 城市地图和 WC3 魔兽地图三类场景）上，采用固定 .scen 任务文件进行 30 次严格基准测试，共 2700 条记录。实验结果表明，与标准 A* 算法相比，本文算法的平均运行时间缩短约 **12.7%**（运行时间比值 0.8728x），路径长度平均缩短约 **4.9%**（绝对减少 0.299），转弯次数平均减少约 **97.6%**（从 1.131 次降至 0.027 次），且 15 张地图全部呈正向改进，无一例外。消融实验进一步验证了各模块的独立贡献：自适应权重是运行时间改善的主要来源（去掉后运行时间增加约 8.1%），两阶段路径平滑是路径质量改善的主要来源（去掉后转弯次数从 0.027 回升至 0.991）。

**关键词：** 路径规划；A* 算法；Octile 启发函数；自适应权重；路径平滑；栅格地图

---

## Abstract

This paper proposes a comprehensive improvement to the A* path planning algorithm for 8-connected grid maps, addressing the limitations of the standard A* algorithm in path quality, heuristic accuracy, and environmental adaptability. The proposed algorithm employs the Octile distance as the heuristic function, introduces an adaptive weight mechanism based on the obstacle ratio of the map, and designs a two-stage path post-processing strategy combining line-of-sight simplification and corner interpolation smoothing. The adaptive weight is computed as $\alpha = \text{clip}(|\ln(\text{obstacle\_ratio})|, 1.0, 1.8)$ for engineering acceleration; strict path optimality is not guaranteed ($\alpha$-optimal when $\alpha > 1$). Obstacle collision detection is incorporated into the smoothing process to guarantee the physical legality of the smoothed path.

Systematic experiments are conducted on 15 real-world maps from the Moving AI Lab benchmark dataset, covering three map types (DAO game maps, Street maps, and Warcraft III maps), using fixed .scen task files with 30 trials per map (2,700 records in total). Experimental results demonstrate that, compared to the standard A* algorithm, the proposed method achieves an average reduction of **12.7%** in runtime (runtime ratio 0.8728x), **4.9%** in path length (absolute reduction 0.299), and **97.6%** in turn count (from 1.131 to 0.027), with consistent improvements across all 15 maps. Ablation studies further validate the individual contributions of each module: the adaptive weight is the primary source of runtime improvement (removing it increases runtime by ~8.1%), while the two-stage path smoothing is the primary source of path quality improvement (removing it raises turn count from 0.027 back to 0.991).

**Keywords:** Path planning; A* algorithm; Octile heuristic; Adaptive weight; Path smoothing; Grid map

---

## v1 → v2 数值变更对照

| 指标 | v1（旧，随机采样） | v2（v3 strict scen，权威） | 说明 |
|---|---|---|---|
| 运行时间改善 | 25.2% | **12.7%**（0.8728x） | v3 更保守但更严谨 |
| 路径长度改善 | 5.4% | **4.9%**（-0.299） | 数量级一致，略有调整 |
| 转弯次数改善 | "减少 13.7 次" | **减少 97.6%**（0.027 vs 1.131） | v3 数据更强，改用百分比表达 |
| 实验口径 | 随机起终点 | strict .scen 固定任务 | v3 更严谨，可复现 |
