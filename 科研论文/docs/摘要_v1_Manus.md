# 摘要（草稿 v1）
> 撰写：Manus AI | 日期：2026-03-18 | 基于 fix15_v2 实验数据

---

## 中文摘要

针对标准 A* 算法在 8 邻域栅格地图中存在的路径质量差、启发函数精度不足和环境自适应性弱等问题，本文提出一种综合改进的路径规划算法。该算法以 Octile 距离作为启发函数，引入基于地图障碍率的自适应权重机制，并设计了视线简化与拐角插值平滑相结合的两阶段路径后处理策略。其中，自适应权重根据 $\alpha = \text{clip}(|\ln(\text{障碍率})|, 1.0, 1.8)$ 动态计算，在保证启发函数可采纳性的前提下实现自适应加速；路径平滑过程中引入障碍物碰撞检测，确保平滑后路径的物理合法性。

在 Moving AI Lab 标准基准地图集的 15 张真实地图（涵盖 DAO 游戏地图、城市街道地图和魔兽争霸地图三种类型）上进行系统性实验，每张地图进行 30 次独立随机测试。实验结果表明，与传统 A* 算法相比，改进算法的平均运行时间缩短 25.2%，路径长度缩短 5.4%，转弯次数平均减少 13.7 次，在 15 张地图上均取得一致的改进效果。消融实验进一步验证了各模块的独立贡献，其中两阶段路径后处理策略是路径质量提升的主要来源。

**关键词：** 路径规划；A* 算法；Octile 启发函数；自适应权重；路径平滑；栅格地图

---

## Abstract

This paper proposes a comprehensive improvement to the A* path planning algorithm for 8-connected grid maps, addressing the limitations of the standard A* algorithm in terms of path quality, heuristic accuracy, and environmental adaptability. The proposed algorithm employs the Octile distance as the heuristic function, introduces an adaptive weight mechanism based on the obstacle ratio of the map, and designs a two-stage path post-processing strategy combining line-of-sight simplification and corner interpolation smoothing. The adaptive weight is computed as $\alpha = \text{clip}(|\ln(\text{obstacle\_ratio})|, 1.0, 1.8)$, ensuring admissibility while enabling adaptive acceleration. Obstacle collision detection is incorporated into the smoothing process to guarantee the physical legality of the smoothed path.

Systematic experiments are conducted on 15 real-world maps from the Moving AI Lab benchmark dataset, covering three map types (DAO game maps, street maps, and Warcraft III maps), with 30 independent random trials per map. Experimental results demonstrate that, compared to the standard A* algorithm, the proposed method achieves an average reduction of 25.2% in runtime, 5.4% in path length, and 13.7 in turn count, with consistent improvements across all 15 maps. Ablation studies further validate the individual contributions of each module, with the two-stage path post-processing strategy identified as the primary source of path quality improvement.

**Keywords:** Path planning; A* algorithm; Octile heuristic; Adaptive weight; Path smoothing; Grid map
