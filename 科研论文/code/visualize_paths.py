"""
路径可视化对比脚本
在同一张随机地图上，同时展示 Dijkstra / 传统A* / JPS-like / 改进A* 的寻路路径
让用户直观看到"黑盒"内部的真实情况
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap

from planners.core import random_grid, sample_start_goal
from planners.algorithms import (
    dijkstra_search,
    vanilla_astar_search,
    jps_like_search,
    improved_astar_search,
)

# ── 字体设置 ──────────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


def draw_grid_with_path(ax, grid, path, start, goal, title, color, show_nodes=True):
    """在子图上绘制栅格地图和路径"""
    h, w = grid.shape

    # 绘制地图背景（白色=空地，黑色=障碍）
    display = np.zeros_like(grid, dtype=float)
    display[grid == 1] = 1.0   # 障碍物 -> 黑色
    display[grid == 0] = 0.95  # 空地   -> 浅灰

    ax.imshow(display, cmap='gray_r', vmin=0, vmax=1, origin='upper',
              extent=[-0.5, w - 0.5, h - 0.5, -0.5])

    # 绘制网格线
    for x in range(w + 1):
        ax.axvline(x - 0.5, color='#cccccc', linewidth=0.3)
    for y in range(h + 1):
        ax.axhline(y - 0.5, color='#cccccc', linewidth=0.3)

    # 绘制路径
    if len(path) >= 2:
        xs = [p[1] for p in path]   # 列 -> x轴
        ys = [p[0] for p in path]   # 行 -> y轴
        ax.plot(xs, ys, color=color, linewidth=2.5, zorder=3, solid_capstyle='round')
        # 绘制路径节点
        if show_nodes and len(path) <= 60:
            ax.scatter(xs[1:-1], ys[1:-1], color=color, s=18, zorder=4, alpha=0.7)

    # 绘制起点（绿色五角星）和终点（红色五角星）
    ax.scatter([start[1]], [start[0]], marker='*', s=280, color='#2ecc71',
               zorder=5, edgecolors='white', linewidths=0.8)
    ax.scatter([goal[1]], [goal[0]], marker='*', s=280, color='#e74c3c',
               zorder=5, edgecolors='white', linewidths=0.8)

    ax.set_title(title, fontsize=11, fontweight='bold', pad=6)
    ax.set_xlim(-0.5, w - 0.5)
    ax.set_ylim(h - 0.5, -0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')


def main():
    # ── 生成一张固定种子的地图（保证可复现）──────────────────────────────────
    SIZE = 30
    RATIO = 0.35
    SEED = 2024

    rng = np.random.default_rng(SEED)
    grid = random_grid(SIZE, RATIO, rng)
    sg = sample_start_goal(grid, rng)
    if sg is None:
        print("地图生成失败，换个种子重试")
        return
    start, goal = sg

    print(f"地图尺寸: {SIZE}x{SIZE}, 障碍率: {RATIO:.0%}, 起点: {start}, 终点: {goal}")

    # ── 运行所有算法 ──────────────────────────────────────────────────────────
    algos = [
        ("Dijkstra",          dijkstra_search(grid, start, goal),          "#7f8c8d"),
        ("Traditional A*",    vanilla_astar_search(grid, start, goal),     "#3498db"),
        ("JPS-like",          jps_like_search(grid, start, goal),          "#f39c12"),
        ("Improved A* (Ours)",improved_astar_search(grid, start, goal),    "#e74c3c"),
    ]

    for name, res, _ in algos:
        if res['success']:
            print(f"  [{name}] 路径长度={res['path_length']:.2f}  "
                  f"转弯次数={res['turn_count']}  "
                  f"运行时间={res['runtime_ms']:.3f}ms  "
                  f"扩展节点={res['expanded_nodes']}")
        else:
            print(f"  [{name}] 寻路失败")

    # ── 绘图：2行2列，每个子图展示一种算法 ───────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(
        f"Path Planning Comparison on {SIZE}x{SIZE} Random Grid (Obstacle Ratio={RATIO:.0%})\n"
        f"Start ★ (green)  →  Goal ★ (red)",
        fontsize=13, fontweight='bold', y=0.98
    )

    for ax, (name, res, color) in zip(axes.flat, algos):
        path = res['path'] if res['success'] else []
        if res['success']:
            subtitle = (f"{name}\n"
                        f"Length={res['path_length']:.2f}  "
                        f"Turns={res['turn_count']}  "
                        f"Time={res['runtime_ms']:.3f}ms  "
                        f"Nodes={res['expanded_nodes']}")
        else:
            subtitle = f"{name}\n[No path found]"
        draw_grid_with_path(ax, grid, path, start, goal, subtitle, color)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    out_path = os.path.join(os.path.dirname(__file__), '..', 'figures', 'path_comparison_visual.png')
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"\n[OK] 路径对比图已保存: {out_path}")

    # ── 额外生成一张"改进前 vs 改进后"的并排对比图 ────────────────────────────
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 7))
    fig2.suptitle(
        f"Traditional A* vs Improved A* — Path Quality Comparison\n"
        f"{SIZE}x{SIZE} Grid, Obstacle Ratio={RATIO:.0%}",
        fontsize=13, fontweight='bold'
    )

    astar_res = algos[1][1]
    imp_res   = algos[3][1]

    draw_grid_with_path(axes2[0], grid, astar_res['path'], start, goal,
                        f"Traditional A*\n"
                        f"Length={astar_res['path_length']:.2f}  "
                        f"Turns={astar_res['turn_count']}  "
                        f"Time={astar_res['runtime_ms']:.3f}ms",
                        "#3498db")

    draw_grid_with_path(axes2[1], grid, imp_res['path'], start, goal,
                        f"Improved A* (Ours)\n"
                        f"Length={imp_res['path_length']:.2f}  "
                        f"Turns={imp_res['turn_count']}  "
                        f"Time={imp_res['runtime_ms']:.3f}ms",
                        "#e74c3c")

    plt.tight_layout()
    out_path2 = os.path.join(os.path.dirname(__file__), '..', 'figures', 'astar_vs_improved_visual.png')
    out_path2 = os.path.abspath(out_path2)
    plt.savefig(out_path2, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"[OK] A* vs 改进A* 对比图已保存: {out_path2}")


if __name__ == "__main__":
    main()
