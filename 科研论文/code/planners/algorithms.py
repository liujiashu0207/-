import heapq
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from .core import (
    Point,
    adaptive_alpha,
    neighbors8,
    obstacle_ratio,
    octile_distance,
    path_length,
    reconstruct_path,
    simplify_path,
    smooth_corners,
    turn_count,
)


def _heuristic(a: Point, b: Point, mode: str) -> float:
    if mode == "zero":
        return 0.0
    return octile_distance(a, b)


def astar_search(
    grid: np.ndarray,
    start: Point,
    goal: Point,
    heuristic_mode: str = "octile",
    weight: float = 1.0,
) -> Dict[str, object]:
    """标准 8 邻域 A* 搜索（Octile 启发 + 可选加权）。"""
    t0 = time.perf_counter()
    open_heap: List[Tuple[float, Point]] = []
    heapq.heappush(open_heap, (0.0, start))
    came_from: Dict[Point, Point] = {}
    g_score: Dict[Point, float] = {start: 0.0}
    f_score: Dict[Point, float] = {start: weight * _heuristic(start, goal, heuristic_mode)}
    closed = set()
    expanded = 0

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1
        if current == goal:
            path = reconstruct_path(came_from, current)
            return {
                "success": True,
                "path": path,
                "path_length": path_length(path),
                "turn_count": turn_count(path),
                "expanded_nodes": expanded,
                "runtime_ms": (time.perf_counter() - t0) * 1000.0,
            }

        for nb, move_cost in neighbors8(grid, current):
            if nb in closed:
                continue
            tentative_g = g_score[current] + move_cost
            if tentative_g < g_score.get(nb, float("inf")):
                came_from[nb] = current
                g_score[nb] = tentative_g
                f = tentative_g + weight * _heuristic(nb, goal, heuristic_mode)
                f_score[nb] = f
                heapq.heappush(open_heap, (f, nb))

    return {
        "success": False,
        "path": [],
        "path_length": float("inf"),
        "turn_count": 0,
        "expanded_nodes": expanded,
        "runtime_ms": (time.perf_counter() - t0) * 1000.0,
    }


def dijkstra_search(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return astar_search(grid, start, goal, heuristic_mode="zero", weight=1.0)


def vanilla_astar_search(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return astar_search(grid, start, goal, heuristic_mode="octile", weight=1.0)


def weighted_astar_search(grid: np.ndarray, start: Point, goal: Point, weight: float = 1.2) -> Dict[str, object]:
    return astar_search(grid, start, goal, heuristic_mode="octile", weight=weight)


def improved_astar_search(
    grid: np.ndarray,
    start: Point,
    goal: Point,
    precomputed_alpha: float = None,
) -> Dict[str, object]:
    """改进 A*：自适应权重 + 两阶段路径平滑（冗余点删除 + 拐角插值）。

    Args:
        grid: 二值网格（0=自由，1=障碍）。
        start: 起点坐标 (row, col)。
        goal: 终点坐标 (row, col)。
        precomputed_alpha: 同一地图多次搜索时可传入预计算值，
            避免重复遍历全图计算障碍率（对大地图有意义）。
    """
    alpha = precomputed_alpha if precomputed_alpha is not None else adaptive_alpha(obstacle_ratio(grid))
    res = astar_search(grid, start, goal, heuristic_mode="octile", weight=alpha)
    if not res["success"]:
        return res
    p0 = res["path"]
    p1 = simplify_path(p0, grid)
    p2 = smooth_corners(p1, grid)
    res["path"] = p2
    res["path_length"] = path_length(p2)
    res["turn_count"] = turn_count(p2)
    return res
