"""
路径对比可视化脚本 v2
Manus 2026-03-19 Round3 修复：
- 所有路径改为相对于项目根目录的相对路径，不含 /home/ubuntu 绝对路径
- 移除 fc-cache 和 Noto Sans CJK SC 系统字体依赖
- 仅使用 matplotlib 默认字体（DejaVu Sans），可选 CJK fallback 但不影响运行
- 起终点改为从 .scen 文件读取固定任务（与 v3 实验口径一致），不再随机采样
- 在 Windows/Linux/macOS 项目根目录均可直接运行：
    python code/visualize/plot_path_comparison.py
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── 路径锚点（相对于本文件，不含绝对路径）────────────────────────────────
ROOT     = Path(__file__).resolve().parents[2]   # research_project/
CODE_DIR = ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# ── 字体：仅使用 matplotlib 默认字体，不依赖系统安装 ─────────────────────
# 可选 CJK fallback：若系统有 Noto Sans CJK SC 则自动使用，否则静默跳过
try:
    import matplotlib.font_manager as fm
    _cjk_fonts = [f.name for f in fm.fontManager.ttflist
                  if "CJK" in f.name or "Noto" in f.name]
    if _cjk_fonts:
        plt.rcParams["font.family"] = [_cjk_fonts[0], "DejaVu Sans"]
    else:
        plt.rcParams["font.family"] = ["DejaVu Sans"]
except Exception:
    plt.rcParams["font.family"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

from planners import vanilla_astar_search, improved_astar_search
from utils.map_loader import load_grid_map


# ── scen 解析（与 run_fix15_v3.py 保持一致）──────────────────────────────
def parse_scen_long_task(scen_path: Path, min_opt_len: float = 100.0):
    """
    从 scen 文件中读取第一条 optimal_length >= min_opt_len 的任务，
    确保路径足够长，具有可视化代表性。
    坐标转换：scen (col, row) → grid (row, col)。
    若无满足条件的任务，则返回 optimal_length 最大的那条。
    """
    best = None
    best_len = -1.0
    with scen_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("version"):
                continue
            parts = line.split()
            if len(parts) < 9:
                continue
            sc, sr = int(parts[4]), int(parts[5])
            gc, gr = int(parts[6]), int(parts[7])
            opt_len = float(parts[8])
            if opt_len == 0.0:
                continue
            if opt_len > best_len:
                best = ((sr, sc), (gr, gc))
                best_len = opt_len
            if opt_len >= min_opt_len:
                return ((sr, sc), (gr, gc))
    return best  # fallback: 返回最长任务


# ── 地图绘制 ──────────────────────────────────────────────────────────────
def draw_path_on_ax(ax, grid, path, color, linewidth, label):
    h, w = grid.shape
    img = np.ones((h, w, 3))
    img[grid == 1] = [0.20, 0.20, 0.20]
    img[grid == 0] = [0.97, 0.97, 0.95]
    ax.imshow(img, origin="upper", interpolation="nearest")
    if path and len(path) > 1:
        ys = [p[0] for p in path]
        xs = [p[1] for p in path]
        ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=0.90,
                label=label, zorder=3)
    if path:
        s, g = path[0], path[-1]
        ax.scatter([s[1]], [s[0]], c="#4CAF50", s=80, zorder=5,
                   marker="o", edgecolors="white", linewidths=0.8)
        ax.scatter([g[1]], [g[0]], c="#F44336", s=80, zorder=5,
                   marker="*", edgecolors="white", linewidths=0.8)
    ax.axis("off")

# ── 6 张地图配置（地图文件 + scen 文件，均为相对路径）────────────────────
# 每张地图选取 optimal_length >= 100 的第一条 scen 任务，确保路径具有可视化代表性

MAP_CONFIGS = [
    {
        "map":  "data/benchmark_maps/dao-map/arena.map",
        "scen": "data/benchmark_scens/dao/arena.map.scen",
        "label": "DAO: arena",
    },
    {
        "map":  "data/benchmark_maps/dao-map/brc000d.map",
        "scen": "data/benchmark_scens/dao/brc000d.map.scen",
        "label": "DAO: brc000d",
    },
    {
        "map":  "data/benchmark_maps/street-map/Berlin_0_256.map",
        "scen": "data/benchmark_scens/street/Berlin_0_256.map.scen",
        "label": "Street: Berlin_0_256",
    },
    {
        "map":  "data/benchmark_maps/street-map/Berlin_1_256.map",
        "scen": "data/benchmark_scens/street/Berlin_1_256.map.scen",
        "label": "Street: Berlin_1_256",
    },
    {
        "map":  "data/benchmark_maps/wc3-map/battleground.map",
        "scen": "data/benchmark_scens/wc3maps512/battleground.map.scen",
        "label": "WC3: battleground",
    },
    {
        "map":  "data/benchmark_maps/wc3-map/bootybay.map",
        "scen": "data/benchmark_scens/wc3maps512/bootybay.map.scen",
        "label": "WC3: bootybay",
    },
]


def main():
    fig, axes = plt.subplots(3, 4, figsize=(20, 15))
    fig.patch.set_facecolor("#1a1a2e")
    fig.suptitle(
        "Path Planning Comparison: Standard A*  vs  Improved A*\n"
        "Blue = Standard A*  |  Orange-Red = Improved A*  |  "
        "Green dot = Start  |  Red star = Goal",
        fontsize=13, color="white", fontweight="bold", y=0.98,
    )

    stats = []

    for idx, cfg in enumerate(MAP_CONFIGS):
        map_path  = ROOT / cfg["map"]
        scen_path = ROOT / cfg["scen"]
        label     = cfg["label"]

        if not map_path.exists():
            print(f"[WARN] map not found: {cfg['map']}")
            continue
        if not scen_path.exists():
            print(f"[WARN] scen not found: {cfg['scen']}")
            continue

        grid  = load_grid_map(map_path)
        h, w  = grid.shape

        # 读取 scen 固定任务：选取 optimal_length >= 100 的第一条任务，确保路径具有可视化代表性
        task = parse_scen_long_task(scen_path, min_opt_len=100.0)
        if task is None:
            print(f"[WARN] {label}: no valid task in scen, skipping")
            continue
        start, goal = task

        # 边界与障碍检查
        if not (0 <= start[0] < h and 0 <= start[1] < w and
                0 <= goal[0]  < h and 0 <= goal[1]  < w):
            print(f"[WARN] {label}: scen task out of bounds, skipping")
            continue
        if grid[start] == 1 or grid[goal] == 1:
            print(f"[WARN] {label}: start/goal on obstacle, skipping")
            continue

        res_a = vanilla_astar_search(grid, start, goal)
        res_b = improved_astar_search(grid, start, goal)

        path_a = res_a.get("path", []) if res_a.get("success") else []
        path_b = res_b.get("path", []) if res_b.get("success") else []
        rt_a   = res_a.get("runtime_ms", 0)
        rt_b   = res_b.get("runtime_ms", 0)
        pl_a   = res_a.get("path_length", 0)
        pl_b   = res_b.get("path_length", 0)
        tc_a   = res_a.get("turn_count", 0)
        tc_b   = res_b.get("turn_count", 0)
        stats.append((label, rt_a, rt_b, pl_a, pl_b, tc_a, tc_b))

        row   = idx // 2
        col_a = (idx % 2) * 2
        col_b = col_a + 1
        ax_a  = axes[row][col_a]
        ax_b  = axes[row][col_b]

        title_a = (f"{label}\nA*  |  {rt_a:.2f}ms  |  "
                   f"len={pl_a:.1f}  |  turns={tc_a}")
        title_b = (f"{label}\nImproved A*  |  {rt_b:.2f}ms  |  "
                   f"len={pl_b:.1f}  |  turns={tc_b}")

        draw_path_on_ax(ax_a, grid, path_a, "#2196F3", 1.5, "A*")
        draw_path_on_ax(ax_b, grid, path_b, "#FF5722", 2.0, "Improved A*")
        ax_a.set_title(title_a, fontsize=8, color="#90CAF9", pad=3)
        ax_b.set_title(title_b, fontsize=8, color="#FFAB91", pad=3)

        print(f"[{label}] A*: {rt_a:.2f}ms len={pl_a:.1f} tc={tc_a}"
              f"  |  Improved: {rt_b:.2f}ms len={pl_b:.1f} tc={tc_b}")

    for ax in axes.flat:
        ax.set_facecolor("#1a1a2e")

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    out_path = ROOT / "figures" / "path_comparison_6maps_v3_Manus.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight",
                facecolor="#1a1a2e")
    print(f"\n[saved] {out_path.relative_to(ROOT)}")

    # 汇总统计
    print("\n=== Summary ===")
    header = f"{'Map':<28} {'A*(ms)':>8} {'Imp(ms)':>8} {'Ratio':>7} "
    header += f"{'A*len':>8} {'Implen':>8} {'A*tc':>6} {'Imptc':>7}"
    print(header)
    for name, rt_a, rt_b, pl_a, pl_b, tc_a, tc_b in stats:
        ratio = rt_b / rt_a if rt_a > 0 else float("nan")
        print(f"{name:<28} {rt_a:>8.2f} {rt_b:>8.2f} {ratio:>7.3f}x "
              f"{pl_a:>8.1f} {pl_b:>8.1f} {tc_a:>6} {tc_b:>7}")


if __name__ == "__main__":
    main()
