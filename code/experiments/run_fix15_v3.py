"""
fix15 基准实验 v3 — strict scen 口径
Manus 2026-03-19 Round3 修复：

变更说明（相对 v2）：
1. 禁用 sample_start_goal，改为读取 Moving AI .scen 固定任务（strict 口径）。
   scen 格式：version 1 / bucket map_file W H start_col start_row goal_col goal_row opt_len
   注意：scen 中坐标为 (col, row)，即 (y, x)，需转换为 grid (row, col) = (x, y)。
2. precomputed_alpha 按地图预计算一次并传入 improved_astar_search，
   避免每次搜索重复遍历全图计算障碍率。
3. 所有路径使用 Path(__file__).resolve() 相对锚点，不含 /home/ubuntu 绝对路径。
4. 产出文件名改为 exp_fix15_v3_*。

地图数量与重复次数不变：15 图 × 30 repeats。
"""

import csv
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── 路径锚点（全部相对，不含绝对路径）─────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]   # research_project/
CODE_DIR = ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from planners import (
    dijkstra_search,
    improved_astar_search,
    vanilla_astar_search,
    weighted_astar_search,
)
from planners.core import (
    adaptive_alpha,
    obstacle_ratio,
    path_length,
    simplify_path,
    smooth_corners,
    turn_count,
)
from utils.map_loader import load_grid_map

RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
SCEN_DIR    = ROOT / "data" / "benchmark_scens"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── 15 张地图：地图文件 + 对应 scen 文件 ─────────────────────────────────
# 格式：(map_type, map_rel_path, scen_rel_path)
MAP_SCEN_PAIRS = [
    # DAO × 5
    ("dao", "data/benchmark_maps/dao-map/arena.map",
             "data/benchmark_scens/dao/arena.map.scen"),
    ("dao", "data/benchmark_maps/dao-map/arena2.map",
             "data/benchmark_scens/dao/arena2.map.scen"),
    ("dao", "data/benchmark_maps/dao-map/brc000d.map",
             "data/benchmark_scens/dao/brc000d.map.scen"),
    ("dao", "data/benchmark_maps/dao-map/brc100d.map",
             "data/benchmark_scens/dao/brc100d.map.scen"),
    ("dao", "data/benchmark_maps/dao-map/brc101d.map",
             "data/benchmark_scens/dao/brc101d.map.scen"),
    # Street × 5
    ("street", "data/benchmark_maps/street-map/Berlin_0_256.map",
               "data/benchmark_scens/street/Berlin_0_256.map.scen"),
    ("street", "data/benchmark_maps/street-map/Berlin_0_512.map",
               "data/benchmark_scens/street/Berlin_0_512.map.scen"),
    ("street", "data/benchmark_maps/street-map/Berlin_0_1024.map",
               "data/benchmark_scens/street/Berlin_0_1024.map.scen"),
    ("street", "data/benchmark_maps/street-map/Berlin_1_256.map",
               "data/benchmark_scens/street/Berlin_1_256.map.scen"),
    ("street", "data/benchmark_maps/street-map/Berlin_1_1024.map",
               "data/benchmark_scens/street/Berlin_1_1024.map.scen"),
    # WC3 × 5
    ("wc3", "data/benchmark_maps/wc3-map/battleground.map",
            "data/benchmark_scens/wc3maps512/battleground.map.scen"),
    ("wc3", "data/benchmark_maps/wc3-map/blastedlands.map",
            "data/benchmark_scens/wc3maps512/blastedlands.map.scen"),
    ("wc3", "data/benchmark_maps/wc3-map/bloodvenomfalls.map",
            "data/benchmark_scens/wc3maps512/bloodvenomfalls.map.scen"),
    ("wc3", "data/benchmark_maps/wc3-map/bootybay.map",
            "data/benchmark_scens/wc3maps512/bootybay.map.scen"),
    ("wc3", "data/benchmark_maps/wc3-map/darkforest.map",
            "data/benchmark_scens/wc3maps512/darkforest.map.scen"),
]

REPEATS = 30  # 每图取前 REPEATS 条可解任务，与 v2 保持一致


# ── scen 解析 ──────────────────────────────────────────────────────────────
def parse_scen(scen_path: Path) -> List[Tuple[Tuple[int,int], Tuple[int,int]]]:
    """
    解析 Moving AI .scen 文件，返回 (start, goal) 列表。
    scen 坐标为 (col, row)，转换为 grid (row, col)。
    跳过 optimal_length == 0 的平凡任务（起终点相同）。
    """
    tasks = []
    with scen_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("version"):
                continue
            parts = line.split()
            if len(parts) < 9:
                continue
            # bucket, map_file, W, H, sc, sr, gc, gr, opt_len
            sc, sr, gc, gr = int(parts[4]), int(parts[5]), int(parts[6]), int(parts[7])
            opt_len = float(parts[8])
            if opt_len == 0.0:
                continue  # 跳过平凡任务
            # scen 坐标 (col, row) → grid (row, col)
            start = (sr, sc)
            goal  = (gr, gc)
            tasks.append((start, goal))
    return tasks


# ── 消融变体 ──────────────────────────────────────────────────────────────
def ablation_no_adaptive(grid: np.ndarray, start, goal) -> Dict:
    """去掉自适应 alpha（固定 weight=1.0），但保留路径平滑。"""
    res = vanilla_astar_search(grid, start, goal)
    if not res["success"]:
        return res
    p1 = simplify_path(res["path"], grid)
    p2 = smooth_corners(p1, grid)
    res["path"] = p2
    res["path_length"] = path_length(p2)
    res["turn_count"] = turn_count(p2)
    return res


def ablation_no_smoothing(grid: np.ndarray, start, goal,
                           precomputed_alpha: float = None) -> Dict:
    """保留自适应 alpha，但去掉路径平滑（仅搜索，不平滑）。"""
    alpha = precomputed_alpha if precomputed_alpha is not None \
            else adaptive_alpha(obstacle_ratio(grid))
    return weighted_astar_search(grid, start, goal, weight=alpha)


# ── 单张地图实验 ───────────────────────────────────────────────────────────
def run_one_map(map_path: Path, scen_path: Path,
                map_name: str, map_type: str, repeats: int) -> List[Dict]:
    """
    从 scen 文件读取固定任务，取前 repeats 条可解任务运行所有算法。
    precomputed_alpha 按地图预计算一次，传入 improved_astar_search 和
    ablation_no_smoothing，避免重复遍历全图。
    """
    grid = load_grid_map(map_path)
    h, w = grid.shape

    # 按地图预计算 alpha（Round3 要求：precomputed_alpha 实际传入）
    obs_ratio = float(obstacle_ratio(grid))
    alpha_for_map = adaptive_alpha(obs_ratio)

    # 构建算法字典（闭包捕获 alpha_for_map）
    algo_dict = {
        "dijkstra":            dijkstra_search,
        "astar":               vanilla_astar_search,
        "weighted_astar":      lambda g, s, t: weighted_astar_search(g, s, t, weight=1.2),
        "improved_astar":      lambda g, s, t: improved_astar_search(
                                    g, s, t, precomputed_alpha=alpha_for_map),
        "ablation_no_adaptive":  ablation_no_adaptive,
        "ablation_no_smoothing": lambda g, s, t: ablation_no_smoothing(
                                    g, s, t, precomputed_alpha=alpha_for_map),
    }

    tasks = parse_scen(scen_path)
    rows = []
    valid = 0

    for start, goal in tasks:
        if valid >= repeats:
            break
        # 边界检查
        if not (0 <= start[0] < h and 0 <= start[1] < w and
                0 <= goal[0]  < h and 0 <= goal[1]  < w):
            continue
        # 起终点不能是障碍
        if grid[start] == 1 or grid[goal] == 1:
            continue
        # 起终点不能相同
        if start == goal:
            continue

        # 先用 astar 验证可达性，不可达则跳过
        probe = vanilla_astar_search(grid, start, goal)
        if not probe["success"]:
            continue

        for algo_name, fn in algo_dict.items():
            res = fn(grid, start, goal)
            rows.append({
                "map_name":      map_name,
                "map_type":      map_type,
                "size":          h,
                "obstacle_ratio": obs_ratio,
                "alpha":         alpha_for_map,
                "run_id":        valid,
                "algorithm":     algo_name,
                "success":       int(res["success"]),
                "runtime_ms":    float(res["runtime_ms"]),
                "path_length":   float(res["path_length"]) if res["success"] else float("nan"),
                "turn_count":    int(res["turn_count"])    if res["success"] else -1,
                "expanded_nodes": int(res["expanded_nodes"]),
            })
        valid += 1

    print(f"  [{map_type}] {map_name}: {valid}/{repeats} tasks "
          f"| obs_ratio={obs_ratio:.3f} alpha={alpha_for_map:.3f}")
    if valid < repeats:
        print(f"    ⚠️  scen 文件中可解任务不足 {repeats} 条（实际 {valid} 条）")
    return rows


# ── 汇总与输出 ─────────────────────────────────────────────────────────────
def build_summary(raw_rows: List[Dict]) -> List[Dict]:
    grouped = defaultdict(list)
    for r in raw_rows:
        key = (r["map_name"], r["algorithm"])
        grouped[key].append(r)

    summary = []
    for (map_name, algo), rows in grouped.items():
        succ_rows = [r for r in rows if r["success"]]
        runtimes  = [r["runtime_ms"] for r in rows]
        plens     = [r["path_length"] for r in succ_rows]
        turns     = [r["turn_count"]  for r in succ_rows]
        nodes     = [r["expanded_nodes"] for r in rows]
        summary.append({
            "map_name":           map_name,
            "map_type":           rows[0]["map_type"],
            "size":               rows[0]["size"],
            "obstacle_ratio":     rows[0]["obstacle_ratio"],
            "alpha":              rows[0]["alpha"],
            "algorithm":          algo,
            "effective_repeats":  len(rows),
            "success_rate":       len(succ_rows) / len(rows) if rows else 0,
            "runtime_ms_mean":    mean(runtimes),
            "runtime_ms_std":     pstdev(runtimes) if len(runtimes) > 1 else 0.0,
            "path_length_mean":   mean(plens) if plens else float("nan"),
            "turn_count_mean":    mean(turns) if turns else float("nan"),
            "expanded_nodes_mean": mean(nodes),
            "source":             "exp_fix15_v3_strict_scen",
        })
    return summary


def save_csv(rows: List[Dict], path: Path):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def compute_key_metrics(summary: List[Dict], source_tag: str = "v3") -> Dict:
    """计算 improved_astar vs astar 的核心对比指标。"""
    astar_map = {r["map_name"]: r for r in summary if r["algorithm"] == "astar"}
    imp_map   = {r["map_name"]: r for r in summary if r["algorithm"] == "improved_astar"}
    common    = set(astar_map) & set(imp_map)

    rt_ratios, pl_deltas, tc_deltas, exp_deltas = [], [], [], []
    for m in common:
        a, b = astar_map[m], imp_map[m]
        if a["runtime_ms_mean"] > 0:
            rt_ratios.append(b["runtime_ms_mean"] / a["runtime_ms_mean"])
        if not (np.isnan(a["path_length_mean"]) or np.isnan(b["path_length_mean"])):
            pl_deltas.append(b["path_length_mean"] - a["path_length_mean"])
        if not (np.isnan(a["turn_count_mean"]) or np.isnan(b["turn_count_mean"])):
            tc_deltas.append(b["turn_count_mean"] - a["turn_count_mean"])
        exp_deltas.append(b["expanded_nodes_mean"] - a["expanded_nodes_mean"])

    return {
        "source":                            source_tag,
        "maps":                              len(common),
        "runtime_ratio_improved_vs_astar":   mean(rt_ratios)  if rt_ratios  else float("nan"),
        "path_delta_improved_minus_astar":   mean(pl_deltas)  if pl_deltas  else float("nan"),
        "turn_delta_improved_minus_astar":   mean(tc_deltas)  if tc_deltas  else float("nan"),
        "expanded_delta_improved_minus_astar": mean(exp_deltas) if exp_deltas else float("nan"),
    }


def plot_comparison(summary: List[Dict], map_type: str, out_path: Path):
    """生成运行时间对比柱状图，仅使用 matplotlib 默认字体，不依赖系统字体。"""
    sub = [r for r in summary if r["map_type"] == map_type]
    if not sub:
        return

    maps   = sorted(set(r["map_name"] for r in sub))
    algos  = ["astar", "improved_astar", "weighted_astar"]
    colors = {"astar": "#4C72B0", "improved_astar": "#DD8452", "weighted_astar": "#55A868"}

    x, width = np.arange(len(maps)), 0.25
    fig, ax = plt.subplots(figsize=(12, 5))
    for i, algo in enumerate(algos):
        vals = []
        for m in maps:
            row = next((r for r in sub if r["map_name"] == m and r["algorithm"] == algo), None)
            vals.append(row["runtime_ms_mean"] if row else 0)
        ax.bar(x + i * width, vals, width, label=algo, color=colors.get(algo, "#999"))

    ax.set_xlabel("Map")
    ax.set_ylabel("Runtime (ms)")
    ax.set_title(f"Runtime Comparison - {map_type.upper()} maps (fix15_v3, strict scen)")
    ax.set_xticks(x + width)
    ax.set_xticklabels([m.replace(".map", "") for m in maps],
                       rotation=25, ha="right", fontsize=8)
    ax.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  [chart] saved: {out_path.name}")


# ── 主流程 ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("fix15_v3 实验 — strict scen 口径")
    print(f"地图数: 15 | 每图 repeats: {REPEATS} | 任务来源: Moving AI .scen")
    print("=" * 65)

    all_raw = []
    t_start = time.time()

    for map_type, map_rel, scen_rel in MAP_SCEN_PAIRS:
        map_path  = ROOT / map_rel
        scen_path = ROOT / scen_rel
        if not map_path.exists():
            print(f"  ⚠️  地图文件不存在，跳过: {map_rel}")
            continue
        if not scen_path.exists():
            print(f"  ⚠️  scen 文件不存在，跳过: {scen_rel}")
            continue
        map_name = map_path.name
        rows = run_one_map(map_path, scen_path, map_name, map_type, REPEATS)
        all_raw.extend(rows)

    elapsed = time.time() - t_start
    print(f"\n总耗时: {elapsed:.1f}s | 总记录数: {len(all_raw)}")

    # 保存各类型原始数据
    for mt in ["dao", "street", "wc3"]:
        sub = [r for r in all_raw if r["map_type"] == mt]
        save_csv(sub, RESULTS_DIR / f"exp_fix15_v3_{mt}_raw_records.csv")
        print(f"  [saved] exp_fix15_v3_{mt}_raw_records.csv  ({len(sub)} rows)")

    # 汇总
    summary = build_summary(all_raw)
    save_csv(summary, RESULTS_DIR / "exp_fix15_v3_all_summary.csv")
    print(f"\n[OK] exp_fix15_v3_all_summary.csv  ({len(summary)} rows)")

    # 关键指标
    km_v3 = compute_key_metrics(summary, source_tag="v3_strict_scen")
    save_csv([km_v3], RESULTS_DIR / "exp_fix15_v3_key_metrics.csv")
    print(f"\n[Key Metrics v3] improved_astar vs astar:")
    print(f"  runtime_ratio : {km_v3['runtime_ratio_improved_vs_astar']:.4f}x")
    print(f"  path_delta    : {km_v3['path_delta_improved_minus_astar']:+.4f}")
    print(f"  turn_delta    : {km_v3['turn_delta_improved_minus_astar']:+.4f}")
    print(f"  expanded_delta: {km_v3['expanded_delta_improved_minus_astar']:+.1f}")

    # 生成图表
    for mt in ["dao", "street", "wc3"]:
        plot_comparison(summary, mt,
                        FIGURES_DIR / f"runtime_comparison_exp_fix15_v3_{mt}.png")

    print("\n✅ fix15_v3 实验全部完成！")


if __name__ == "__main__":
    main()
