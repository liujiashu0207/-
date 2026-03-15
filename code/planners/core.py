import math
from collections import deque
from typing import Iterable, List, Optional, Tuple

import numpy as np

Point = Tuple[int, int]


def octile_distance(a: Point, b: Point) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2.0) - 1.0) * min(dx, dy)


def euclidean_distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def neighbors8(grid: np.ndarray, node: Point) -> Iterable[Tuple[Point, float]]:
    h, w = grid.shape
    x, y = node
    for dx, dy in (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    ):
        nx, ny = x + dx, y + dy
        if 0 <= nx < h and 0 <= ny < w and grid[nx, ny] == 0:
            step = math.sqrt(2.0) if dx != 0 and dy != 0 else 1.0
            yield (nx, ny), step


def obstacle_ratio(grid: np.ndarray) -> float:
    return float(np.mean(grid == 1))


def adaptive_alpha(obs_ratio: float) -> float:
    # Keep alpha in a safe numeric range to avoid over-greedy behavior.
    obs_ratio = min(max(obs_ratio, 0.01), 0.99)
    raw = abs(math.log(obs_ratio))
    return min(max(raw, 0.8), 1.8)


def reconstruct_path(came_from: dict, current: Point) -> List[Point]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def path_length(path: List[Point]) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(path)):
        total += euclidean_distance(path[i - 1], path[i])
    return total


def turn_count(path: List[Point]) -> int:
    if len(path) < 3:
        return 0
    turns = 0
    for i in range(1, len(path) - 1):
        v1 = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        v2 = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        if v1 != v2:
            turns += 1
    return turns


def line_of_sight(grid: np.ndarray, p1: Point, p2: Point) -> bool:
    x0, y0 = p1
    x1, y1 = p2
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if grid[x0, y0] == 1:
            return False
        if (x0, y0) == (x1, y1):
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return True


def simplify_path(path: List[Point], grid: np.ndarray) -> List[Point]:
    if len(path) < 3:
        return path[:]
    kept = [path[0]]
    anchor = 0
    i = 2
    while i < len(path):
        if not line_of_sight(grid, path[anchor], path[i]):
            kept.append(path[i - 1])
            anchor = i - 1
        i += 1
    kept.append(path[-1])
    return kept


def smooth_corners(path: List[Point]) -> List[Point]:
    if len(path) < 3:
        return path[:]
    smoothed: List[Point] = [path[0]]
    for i in range(1, len(path) - 1):
        ax, ay = path[i - 1]
        bx, by = path[i]
        cx, cy = path[i + 1]
        mx = int(round((ax + 2 * bx + cx) / 4.0))
        my = int(round((ay + 2 * by + cy) / 4.0))
        smoothed.append((mx, my))
    smoothed.append(path[-1])
    # Remove duplicates caused by integer rounding.
    deduped = [smoothed[0]]
    for p in smoothed[1:]:
        if p != deduped[-1]:
            deduped.append(p)
    return deduped


def random_grid(size: int, obstacle_ratio_value: float, rng: np.random.Generator) -> np.ndarray:
    grid = (rng.random((size, size)) < obstacle_ratio_value).astype(np.int8)
    return grid


def sample_start_goal(grid: np.ndarray, rng: np.random.Generator) -> Optional[Tuple[Point, Point]]:
    free = np.argwhere(grid == 0)
    if len(free) < 2:
        return None

    # Try multiple pairs and keep only reachable start-goal samples.
    for _ in range(80):
        idx = rng.choice(len(free), size=2, replace=False)
        s = tuple(int(v) for v in free[idx[0]])
        g = tuple(int(v) for v in free[idx[1]])
        if _is_reachable(grid, s, g):
            return s, g
    return None


def _is_reachable(grid: np.ndarray, start: Point, goal: Point) -> bool:
    if start == goal:
        return True
    h, w = grid.shape
    q = deque([start])
    visited = {start}
    while q:
        x, y = q.popleft()
        for dx, dy in (
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ):
            nx, ny = x + dx, y + dy
            nb = (nx, ny)
            if not (0 <= nx < h and 0 <= ny < w):
                continue
            if grid[nx, ny] == 1 or nb in visited:
                continue
            if nb == goal:
                return True
            visited.add(nb)
            q.append(nb)
    return False
