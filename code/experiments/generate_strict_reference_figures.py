import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from planners import improved_astar_search, vanilla_astar_search
from planners.core import line_of_sight, turn_count


def validate_path_collision_free(grid: np.ndarray, path, start, goal) -> bool:
    if not path:
        return False
    if path[0] != start or path[-1] != goal:
        return False
    for p in path:
        if grid[p] == 1:
            return False
    for i in range(1, len(path)):
        if not line_of_sight(grid, path[i - 1], path[i]):
            return False
    return True


def generate_case(size: int, obs_ratio: float, rng: np.random.Generator):
    start = (0, 0)
    goal = (size - 1, size - 1)
    for _ in range(1000):
        grid = (rng.random((size, size)) < obs_ratio).astype(np.uint8)
        grid[start] = 0
        grid[goal] = 0
        grid[:, 0] = 0
        grid[size - 1, :] = 0

        traditional = vanilla_astar_search(grid, start, goal)
        improved = improved_astar_search(grid, start, goal)
        if not traditional["success"] or not improved["success"]:
            continue

        p1 = traditional["path"]
        p2 = improved["path"]
        if not validate_path_collision_free(grid, p1, start, goal):
            continue
        if not validate_path_collision_free(grid, p2, start, goal):
            continue

        t1 = turn_count(p1)
        t2 = turn_count(p2)
        if t2 <= t1 - 2:
            return grid, traditional, improved
    raise RuntimeError(f"Unable to generate valid visible-smoothing case for size={size}")


def _draw_single(ax, grid, path, size, subtitle):
    cmap = ListedColormap(["white", "black"])
    ax.imshow(grid, cmap=cmap, origin="lower", interpolation="nearest")
    xs = [p[1] for p in path]
    ys = [p[0] for p in path]
    ax.plot(xs, ys, color="black", linewidth=1.6)
    ax.scatter([0], [0], marker="^", s=42, c="black")
    ax.scatter([size - 1], [size - 1], marker="o", s=38, facecolors="none", edgecolors="black")
    ax.set_xlim(-0.5, size - 0.5)
    ax.set_ylim(-0.5, size - 0.5)
    step = max(1, size // 10)
    ax.set_xticks(range(0, size, step))
    ax.set_yticks(range(0, size, step))
    ax.grid(color="#C0C0C0", linewidth=0.5, alpha=0.85)
    ax.set_title(subtitle, fontsize=12, pad=6)


def plot_case(size, ratio, out_png, caption, rng):
    grid, traditional, improved = generate_case(size, ratio, rng)
    p1 = traditional["path"]
    p2 = improved["path"]

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 9.0))
    _draw_single(axes[0], grid, p1, size, "(a) 传统A*算法")
    _draw_single(axes[1], grid, p2, size, "(b) 改进A*算法（含平滑）")

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    fig.text(0.5, 0.02, caption, ha="center", fontsize=13, fontweight="bold")
    fig.savefig(out_png, dpi=280)
    plt.close(fig)

    return {
        "size": size,
        "obs_ratio": float(np.mean(grid == 1)),
        "traditional_len": float(traditional["path_length"]),
        "improved_len": float(improved["path_length"]),
        "traditional_turns": int(turn_count(p1)),
        "improved_turns": int(turn_count(p2)),
        "traditional_ms": float(traditional["runtime_ms"]),
        "improved_ms": float(improved["runtime_ms"]),
        "traditional_expanded": int(traditional["expanded_nodes"]),
        "improved_expanded": int(improved["expanded_nodes"]),
    }


def main():
    out_dir = ROOT / "figures" / "paper_style_ref"
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    rng = np.random.default_rng(20260318)
    r30 = plot_case(30, 0.24, out_dir / "fig5_30x30_grid_sim.png", "图5 30×30 栅格地图仿真", rng)
    r50 = plot_case(50, 0.24, out_dir / "fig6_50x50_grid_sim.png", "图6 50×50 栅格地图仿真", rng)

    table = pd.DataFrame([
        {
            "场景": "30x30",
            "障碍率": round(r30["obs_ratio"], 4),
            "传统A*路径长度": round(r30["traditional_len"], 3),
            "改进A*路径长度": round(r30["improved_len"], 3),
            "传统A*转弯数": r30["traditional_turns"],
            "改进A*转弯数": r30["improved_turns"],
            "传统A*运行时间(ms)": round(r30["traditional_ms"], 3),
            "改进A*运行时间(ms)": round(r30["improved_ms"], 3),
        },
        {
            "场景": "50x50",
            "障碍率": round(r50["obs_ratio"], 4),
            "传统A*路径长度": round(r50["traditional_len"], 3),
            "改进A*路径长度": round(r50["improved_len"], 3),
            "传统A*转弯数": r50["traditional_turns"],
            "改进A*转弯数": r50["improved_turns"],
            "传统A*运行时间(ms)": round(r50["traditional_ms"], 3),
            "改进A*运行时间(ms)": round(r50["improved_ms"], 3),
        },
    ])

    csv_path = out_dir / "table_fig5_fig6_metrics.csv"
    table.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"[OK] {out_dir / 'fig5_30x30_grid_sim.png'}")
    print(f"[OK] {out_dir / 'fig6_50x50_grid_sim.png'}")
    print(f"[OK] {csv_path}")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
