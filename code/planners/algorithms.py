import heapq
import time
from typing import Dict, List, Tuple

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
    t0 = time.perf_counter()
    open_heap: List[Tuple[float, Point]] = []
    heapq.heappush(open_heap, (0.0, start))
    came_from: Dict[Point, Point] = {}
    g_score: Dict[Point, float] = {start: 0.0}
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


def improved_astar_search_configurable(
    grid: np.ndarray,
    start: Point,
    goal: Point,
    use_adaptive_weight: bool = True,
    use_smoothing: bool = True,
    fixed_weight: float = 1.2,
) -> Dict[str, object]:
    alpha = adaptive_alpha(obstacle_ratio(grid)) if use_adaptive_weight else fixed_weight
    res = astar_search(
        grid,
        start,
        goal,
        heuristic_mode="octile",
        weight=alpha,
    )
    if not res["success"]:
        return res

    if not use_smoothing:
        return res

    p0 = res["path"]
    p1 = simplify_path(p0, grid)
    p2 = smooth_corners(p1, grid)
    res["path"] = p2
    res["path_length"] = path_length(p2)
    res["turn_count"] = turn_count(p2)
    return res


def improved_astar_search(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return improved_astar_search_configurable(
        grid,
        start,
        goal,
        use_adaptive_weight=True,
        use_smoothing=True,
        fixed_weight=1.2,
    )


def ablation_no_adaptive_weight(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return improved_astar_search_configurable(
        grid,
        start,
        goal,
        use_adaptive_weight=False,
        use_smoothing=True,
        fixed_weight=1.2,
    )


def ablation_no_smoothing(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return improved_astar_search_configurable(
        grid,
        start,
        goal,
        use_adaptive_weight=True,
        use_smoothing=False,
        fixed_weight=1.2,
    )
