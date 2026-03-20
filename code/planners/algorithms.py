import heapq
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from .core import (
    Point,
    adaptive_alpha,
    line_of_sight,
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


def _jump_like_neighbors(grid: np.ndarray, node: Point, max_jump: int = 3):
    # Lightweight JPS-like expansion: try longer strides per direction.
    x, y = node
    h, w = grid.shape
    dirs = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )
    for dx, dy in dirs:
        for step in range(1, max_jump + 1):
            nx, ny = x + dx * step, y + dy * step
            if not (0 <= nx < h and 0 <= ny < w):
                break
            if grid[nx, ny] == 1:
                break
            # Ensure every jumped segment stays collision-free.
            if not line_of_sight(grid, node, (nx, ny)):
                break
            move_cost = step * (2**0.5 if dx != 0 and dy != 0 else 1.0)
            yield (nx, ny), move_cost


def astar_search(
    grid: np.ndarray,
    start: Point,
    goal: Point,
    heuristic_mode: str = "octile",
    weight: float = 1.0,
    use_jump_like: bool = False,
) -> Dict[str, object]:
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

        nbr_iter = _jump_like_neighbors(grid, current) if use_jump_like else neighbors8(grid, current)
        for nb, move_cost in nbr_iter:
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
    return astar_search(grid, start, goal, heuristic_mode="zero", weight=1.0, use_jump_like=False)


def vanilla_astar_search(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return astar_search(grid, start, goal, heuristic_mode="octile", weight=1.0, use_jump_like=False)


def weighted_astar_search(grid: np.ndarray, start: Point, goal: Point, weight: float = 1.2) -> Dict[str, object]:
    return astar_search(grid, start, goal, heuristic_mode="octile", weight=weight, use_jump_like=False)


def jps_like_search(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return astar_search(grid, start, goal, heuristic_mode="octile", weight=1.0, use_jump_like=True)


def improved_astar_search_configurable(
    grid: np.ndarray,
    start: Point,
    goal: Point,
    use_adaptive_weight: bool = True,
    use_jump_like: bool = True,
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
        use_jump_like=use_jump_like,
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
        use_jump_like=True,
        use_smoothing=True,
        fixed_weight=1.2,
    )


def ablation_no_adaptive_weight(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return improved_astar_search_configurable(
        grid,
        start,
        goal,
        use_adaptive_weight=False,
        use_jump_like=True,
        use_smoothing=True,
        fixed_weight=1.2,
    )


def ablation_no_jump_like(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return improved_astar_search_configurable(
        grid,
        start,
        goal,
        use_adaptive_weight=True,
        use_jump_like=False,
        use_smoothing=True,
        fixed_weight=1.2,
    )


def ablation_no_smoothing(grid: np.ndarray, start: Point, goal: Point) -> Dict[str, object]:
    return improved_astar_search_configurable(
        grid,
        start,
        goal,
        use_adaptive_weight=True,
        use_jump_like=True,
        use_smoothing=False,
        fixed_weight=1.2,
    )
