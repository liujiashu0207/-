"""
Generate Figure 4: path comparison on 6 representative maps.
Runs A* and improved A* on each map with a fixed start/goal,
then plots the map + two paths side by side.

Usage:
    python code/visualize/plot_path_comparison.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from utils.map_loader import load_grid_map
from planners.algorithms import vanilla_astar_search, improved_astar_search
from planners.core import line_of_sight

plt.rcParams.update({
    "font.family": "SimHei",
    "axes.unicode_minus": False,
    "font.size": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})

FIGURES_DIR = ROOT / "figures"

MAPS_TO_PLOT = [
    ("DAO", "arena.map", "data/benchmark_maps/dao-map/arena.map", "data/benchmark_scens/dao/arena.map.scen"),
    ("DAO", "arena2.map", "data/benchmark_maps/dao-map/arena2.map", "data/benchmark_scens/dao/arena2.map.scen"),
    ("WC3", "battleground.map", "data/benchmark_maps/wc3-map/battleground.map", "data/benchmark_scens/wc3maps512/battleground.map.scen"),
    ("WC3", "darkforest.map", "data/benchmark_maps/wc3-map/darkforest.map", "data/benchmark_scens/wc3maps512/darkforest.map.scen"),
    ("DAO", "brc000d.map", "data/benchmark_maps/dao-map/brc000d.map", "data/benchmark_scens/dao/brc000d.map.scen"),
    ("WC3", "bootybay.map", "data/benchmark_maps/wc3-map/bootybay.map", "data/benchmark_scens/wc3maps512/bootybay.map.scen"),
]

CMAP_GRID = ListedColormap(["#f0f0f0", "#2c3e50"])


def plot_path_on_ax(ax, grid, path_astar, path_improved, title):
    ax.imshow(grid, cmap=CMAP_GRID, interpolation="nearest", origin="upper")

    if path_astar:
        ys = [p[0] for p in path_astar]
        xs = [p[1] for p in path_astar]
        ax.plot(xs, ys, color="#3498db", linewidth=1.2, alpha=0.8, label="传统 A*")
        ax.plot(xs[0], ys[0], "o", color="#27ae60", markersize=5, zorder=5)
        ax.plot(xs[-1], ys[-1], "s", color="#e74c3c", markersize=5, zorder=5)

    if path_improved:
        ys = [p[0] for p in path_improved]
        xs = [p[1] for p in path_improved]
        ax.plot(xs, ys, color="#e74c3c", linewidth=1.5, alpha=0.9,
                linestyle="-", label="改进 A*")

    ax.set_title(title, fontsize=9)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(fontsize=6, loc="lower right", framealpha=0.8)


def parse_scen_tasks(path: Path):
    tasks = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("version"):
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        sc, sr, gc, gr = int(parts[4]), int(parts[5]), int(parts[6]), int(parts[7])
        start = (sr, sc)
        goal = (gr, gc)
        if start != goal:
            tasks.append((start, goal))
    return tasks


def path_is_collision_free(grid, path):
    if not path:
        return False
    h, w = grid.shape
    for p in path:
        x, y = p
        if not (0 <= x < h and 0 <= y < w):
            return False
        if grid[x, y] == 1:
            return False
    for i in range(1, len(path)):
        a = path[i - 1]
        b = path[i]
        if not line_of_sight(grid, a, b):
            return False
    return True


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    valid_maps = []
    for map_type, name, rel_path, scen_rel in MAPS_TO_PLOT:
        full_path = ROOT / rel_path
        scen_path = ROOT / scen_rel
        if full_path.exists() and scen_path.exists():
            valid_maps.append((map_type, name, full_path, scen_path))
        else:
            print(f"[SKIP] Missing map/scen: {full_path} | {scen_path}")

    if len(valid_maps) < 2:
        print("[ERROR] Need at least 2 maps, aborting.")
        return

    n = min(len(valid_maps), 6)
    ncols = 3
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 4 * nrows))
    if nrows == 1:
        axes = axes.reshape(1, -1)

    for idx in range(n):
        map_type, name, full_path, scen_path = valid_maps[idx]
        grid = load_grid_map(full_path)
        h, w = grid.shape

        path_a, path_i, res_astar, res_improved = [], [], None, None
        for start, goal in parse_scen_tasks(scen_path):
            if grid[start] == 1 or grid[goal] == 1:
                continue
            res_astar = vanilla_astar_search(grid, start, goal)
            res_improved = improved_astar_search(grid, start, goal)
            if not (res_astar["success"] and res_improved["success"]):
                continue
            pa = res_astar["path"]
            pi = res_improved["path"]
            if path_is_collision_free(grid, pa) and path_is_collision_free(grid, pi):
                path_a, path_i = pa, pi
                break

        if not path_a or not path_i:
            print(f"[WARN] Cannot find collision-free pair from scen for {name}")
            continue

        row, col = divmod(idx, ncols)
        ax = axes[row][col]

        title = f"({chr(97+idx)}) {name}\n[{map_type}] {h}×{w}"
        plot_path_on_ax(ax, grid, path_a, path_i, title)

        info_text = (
            f"A*: L={res_astar['path_length']:.1f}, T={res_astar['turn_count']}\n"
            f"改进: L={res_improved['path_length']:.1f}, T={res_improved['turn_count']}"
        )
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                fontsize=6, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    for idx in range(n, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    fig.suptitle("图 4  路径对比可视化（传统 A* vs 改进 A*）", fontsize=13, y=1.01)
    fig.tight_layout()
    out = FIGURES_DIR / "path_comparison_6maps_v4_no_tunneling.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
