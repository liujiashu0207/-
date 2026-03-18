# 给 Cursor 的修改指令（第二轮）— Manus 审查后发出

> **审查时间**：2026-03-18  
> **审查依据**：对提交 `afdedda` 的代码与实验数据进行逐行核查  
> **本轮状态**：实验数据整体良好，但以下 **2 处代码硬伤未修复**，必须完成后重跑实验

---

## 背景说明

Manus 对你最新提交的 `exp_fix15` 实验数据进行了全面核查，核心结论如下：

- 运行时间：`improved_astar` 比 `astar` 快 **0.5%**（15 张地图均值）
- 路径长度：缩短 **4.9%**
- 转弯次数：减少 **97.6%**（15/15 张地图均减少超过 90%）

这份数据已经非常接近可投稿状态。但以下两处代码问题会在审稿时被发现，必须先修复再定稿。

---

## 修改任务一（P0 级，必须完成）

**文件**：`code/planners/core.py`  
**问题**：`smooth_corners` 函数没有接收 `grid` 参数，无法检测平滑后的插值点是否落在障碍物上，存在路径穿越障碍物的物理非法漏洞。  
**实测验证**（Manus 已验证）：
```
输入路径: [(4,4), (5,6), (6,4)]，障碍在 (5,5)
当前输出: [(4,4), (5,5), (6,4)]  ← (5,5) 是障碍！路径非法！
```

**修改方法**：将 `smooth_corners` 函数替换为以下版本：

```python
def smooth_corners(path: List[Point], grid: np.ndarray) -> List[Point]:
    """对路径拐角进行加权平均平滑，跳过会穿越障碍物的插值点。"""
    if len(path) < 3:
        return path[:]
    smoothed: List[Point] = [path[0]]
    for i in range(1, len(path) - 1):
        ax, ay = path[i - 1]
        bx, by = path[i]
        cx, cy = path[i + 1]
        mx = int(round((ax + 2 * bx + cx) / 4.0))
        my = int(round((ay + 2 * by + cy) / 4.0))
        # 关键修复：若插值点是障碍物，保留原始拐点，放弃平滑
        if 0 <= mx < grid.shape[0] and 0 <= my < grid.shape[1] and grid[mx, my] == 0:
            smoothed.append((mx, my))
        else:
            smoothed.append((bx, by))
    smoothed.append(path[-1])
    # 去除整数舍入导致的重复点
    deduped = [smoothed[0]]
    for p in smoothed[1:]:
        if p != deduped[-1]:
            deduped.append(p)
    return deduped
```

---

## 修改任务二（同步修改，必须完成）

**文件**：`code/planners/algorithms.py`  
**问题**：`improved_astar_search` 调用 `smooth_corners` 时没有传入 `grid` 参数，修改任务一后此处必须同步更新，否则代码会报错。

**当前代码（第 133 行）**：
```python
p2 = smooth_corners(p1)
```

**修改为**：
```python
p2 = smooth_corners(p1, grid)
```

---

## 修改任务三（P1 级，强烈建议完成）

**文件**：`code/planners/core.py`  
**问题**：`adaptive_alpha` 函数的下界是 `0.8`，当障碍率 ≥ 50% 时 alpha 会低于 1.0，导致启发函数欠估计，算法退化为次优搜索。  
**实测验证**（Manus 已验证）：
```
obstacle_ratio=0.50  →  alpha=0.8000  （欠估计，BUG）
obstacle_ratio=0.70  →  alpha=0.8000  （欠估计，BUG）
obstacle_ratio=0.90  →  alpha=0.8000  （欠估计，BUG）
```

**当前代码（第 42 行）**：
```python
return min(max(raw, 0.8), 1.8)
```

**修改为**：
```python
return min(max(raw, 1.0), 1.8)
```

---

## 完成后的操作步骤

1. 完成上述三处修改
2. 运行以下验证脚本，确认穿模漏洞已修复：

```python
import numpy as np, sys
sys.path.insert(0, 'code')
from planners.core import smooth_corners, adaptive_alpha

grid = np.zeros((10,10), dtype=np.int8)
grid[5,5] = 1
path = [(4,4), (5,6), (6,4)]
result = smooth_corners(path, grid)
assert (5,5) not in result, "穿模漏洞未修复！"
print("穿模测试通过")

for ratio in [0.5, 0.7, 0.9]:
    a = adaptive_alpha(ratio)
    assert a >= 1.0, f"alpha={a} < 1.0，欠估计 BUG 未修复！"
print("alpha 下界测试通过")
print("所有验证通过，可以重跑实验")
```

3. 验证通过后，重新运行 15 张地图的基准实验，生成新的 `exp_fix15_v2` 数据
4. 将修改后的代码和新实验结果推送到 GitHub

---

## 注意事项

- **不要修改任何其他函数**，本次只改以上三处
- **不要自行修改实验参数**（地图数量、重复次数等）
- 完成后 Manus 会再次拉取代码进行验收

---

*本指令由 Manus AI 基于代码审查结果生成，2026-03-18*
