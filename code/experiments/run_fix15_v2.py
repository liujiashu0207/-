"""
[DEPRECATED - 不得用于论文结论]
本脚本使用随机起终点（sample_start_goal），实验口径不统一，数据已被证明严重失真（路径长度、转弯次数均被大幅夹大）。
请使用唯一权威实验脚本： code/experiments/run_fix15_v3.py（strict scen 口径）。

重跑 fix15 基准实验（v2）
Manus 2026-03-18：在修复 smooth_corners 穿模漏洞和 adaptive_alpha 下界后重跑。

实验设计与 fix15 v1 完全一致：
- 15 张 Moving AI 真实地图（DAO x5, Street x5, WC3 x5）
- 每张地图 30 次有效随机起终点
- 对比算法：dijkstra / astar / weighted_astar / improved_astar
- 消融变体：ablation_no_adaptive / ablation_no_smoothing
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
import matplotlib.font_manager as fm
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
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
    reconstruct_path,
    sample_start_goal,
    simplify_path,
    smooth_corners,
    turn_count,
    octile_distance,
)
from utils.map_loader import load_grid_map

RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── 与 fix15 v1 完全一致的 15 张地图 ──────────────────────────────────────
MAP_FILES = {
    "dao": [
        "data/benchmark_maps/dao-map/arena.map",
        "data/benchmark_maps/dao-map/arena2.map",
        "data/benchmark_maps/dao-map/brc000d.map",
        "data/benchmark_maps/dao-map/brc100d.map",
        "data/benchmark_maps/dao-map/brc101d.map",
    ],
    "street": [
        "data/benchmark_maps/street-map/Berlin_0_256.map",
        "data/benchmark_maps/street-map/Berlin_0_512.map",
        "data/benchmark_maps/street-map/Berlin_0_1024.map",
        "data/benchmark_maps/street-map/Berlin_1_256.map",
        "data/benchmark_maps/street-map/Berlin_1_1024.map",
    ],
    "wc3": [
        "data/benchmark_maps/wc3-map/battleground.map",
        "data/benchmark_maps/wc3-map/blastedlands.map",
        "data/benchmark_maps/wc3-map/bloodvenomfalls.map",
        "data/benchmark_maps/wc3-map/bootybay.map",
        "data/benchmark_maps/wc3-map/darkforest.map",
    ],
}

REPEATS = 30
SEED = 2026


# ── 消融变体 ──────────────────────────────────────────────────────────────
def ablation_no_adaptive(grid: np.ndarray, start, goal) -> Dict:
    """去掉自适应 alpha，固定 weight=1.0（等同于标准 A*），但保留路径平滑。"""
    # 使用 vanilla_astar（weight=1.0）但加路径平滑
    res = vanilla_astar_search(grid, start, goal)
    if not res["success"]:
        return res
    p1 = simplify_path(res["path"], grid)
    p2 = smooth_corners(p1, grid)
    res["path"] = p2
    res["path_length"] = path_length(p2)
    res["turn_count"] = turn_count(p2)
    return res


def ablation_no_smoothing(grid: np.ndarray, start, goal) -> Dict:
    """保留自适应 alpha，但去掉路径平滑（仅搜索，不平滑）。"""
    alpha = adaptive_alpha(obstacle_ratio(grid))
    res = weighted_astar_search(grid, start, goal, weight=alpha)
    return res


ALGO_DICT = {
    "dijkstra": dijkstra_search,
    "astar": vanilla_astar_search,
    "weighted_astar": lambda g, s, t: weighted_astar_search(g, s, t, weight=1.2),
    "improved_astar": improved_astar_search,
    "ablation_no_adaptive": ablation_no_adaptive,
    "ablation_no_smoothing": ablation_no_smoothing,
}


def run_one_map(map_path: Path, map_name: str, map_type: str, repeats: int, seed: int) -> List[Dict]:
    grid = load_grid_map(map_path)
    rng = np.random.default_rng(seed)
    rows = []
    valid = 0
    attempts = 0
    max_attempts = repeats * 30

    while valid < repeats and attempts < max_attempts:
        sg = sample_start_goal(grid, rng)
        attempts += 1
        if sg is None:
            continue
        start, goal = sg
        for algo_name, fn in ALGO_DICT.items():
            res = fn(grid, start, goal)
            rows.append({
                "map_name": map_name,
                "map_type": map_type,
                "size": grid.shape[0],
                "ratio": float(np.mean(grid == 1)),
                "run_id": valid,
                "algorithm": algo_name,
                "success": int(res["success"]),
                "runtime_ms": float(res["runtime_ms"]),
                "path_length": float(res["path_length"]) if res["success"] else float("nan"),
                "turn_count": int(res["turn_count"]) if res["success"] else -1,
                "expanded_nodes": int(res["expanded_nodes"]),
            })
        valid += 1

    print(f"  [{map_type}] {map_name}: {valid}/{repeats} valid runs ({attempts} attempts)")
    return rows


def build_summary(raw_rows: List[Dict]) -> List[Dict]:
    grouped = defaultdict(list)
    for r in raw_rows:
        key = (r["map_name"], r["algorithm"])
        grouped[key].append(r)

    summary = []
    for (map_name, algo), rows in grouped.items():
        succ_rows = [r for r in rows if r["success"]]
        runtimes = [r["runtime_ms"] for r in rows]
        plens = [r["path_length"] for r in succ_rows]
        turns = [r["turn_count"] for r in succ_rows]
        nodes = [r["expanded_nodes"] for r in rows]
        summary.append({
            "map_name": map_name,
            "map_type": rows[0]["map_type"],
            "size": rows[0]["size"],
            "ratio": rows[0]["ratio"],
            "algorithm": algo,
            "effective_repeats": len(rows),
            "success_rate": len(succ_rows) / len(rows) if rows else 0,
            "runtime_ms_mean": mean(runtimes),
            "runtime_ms_std": pstdev(runtimes) if len(runtimes) > 1 else 0.0,
            "path_length_mean": mean(plens) if plens else float("nan"),
            "turn_count_mean": mean(turns) if turns else float("nan"),
            "expanded_nodes_mean": mean(nodes),
            "source": "exp_fix15_v2",
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


def plot_comparison(summary: List[Dict], map_type: str, out_path: Path):
    """为每种地图类型生成运行时间对比图。"""
    sub = [r for r in summary if r["map_type"] == map_type]
    if not sub:
        return

    # 按地图分组，取 astar 和 improved_astar
    maps = sorted(set(r["map_name"] for r in sub))
    algos_to_plot = ["astar", "improved_astar", "weighted_astar"]
    colors = {"astar": "#4C72B0", "improved_astar": "#DD8452", "weighted_astar": "#55A868"}

    x = np.arange(len(maps))
    width = 0.25
    fig, ax = plt.subplots(figsize=(12, 5))

    for i, algo in enumerate(algos_to_plot):
        vals = []
        for m in maps:
            row = next((r for r in sub if r["map_name"] == m and r["algorithm"] == algo), None)
            vals.append(row["runtime_ms_mean"] if row else 0)
        ax.bar(x + i * width, vals, width, label=algo, color=colors.get(algo, "#999"))

    ax.set_xlabel("Map")
    ax.set_ylabel("Runtime (ms)")
    ax.set_title(f"Runtime Comparison — {map_type.upper()} maps (fix15_v2, post-fix)")
    ax.set_xticks(x + width)
    ax.set_xticklabels([m.replace(".map", "") for m in maps], rotation=25, ha="right", fontsize=8)
    ax.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  [图表] 已保存: {out_path.name}")


def compute_key_metrics(summary: List[Dict]) -> Dict:
    """计算 improved_astar vs astar 的核心对比指标。"""
    astar_rows = [r for r in summary if r["algorithm"] == "astar"]
    imp_rows = [r for r in summary if r["algorithm"] == "improved_astar"]

    # 按地图名对齐
    astar_map = {r["map_name"]: r for r in astar_rows}
    imp_map = {r["map_name"]: r for r in imp_rows}
    common_maps = set(astar_map) & set(imp_map)

    rt_ratios, pl_deltas, tc_deltas, exp_deltas = [], [], [], []
    for m in common_maps:
        a, b = astar_map[m], imp_map[m]
        if a["runtime_ms_mean"] > 0:
            rt_ratios.append(b["runtime_ms_mean"] / a["runtime_ms_mean"])
        if not (np.isnan(a["path_length_mean"]) or np.isnan(b["path_length_mean"])):
            pl_deltas.append(b["path_length_mean"] - a["path_length_mean"])
        if not (np.isnan(a["turn_count_mean"]) or np.isnan(b["turn_count_mean"])):
            tc_deltas.append(b["turn_count_mean"] - a["turn_count_mean"])
        exp_deltas.append(b["expanded_nodes_mean"] - a["expanded_nodes_mean"])

    return {
        "maps": len(common_maps),
        "runtime_ratio_improved_vs_astar": mean(rt_ratios) if rt_ratios else float("nan"),
        "path_delta_improved_minus_astar": mean(pl_deltas) if pl_deltas else float("nan"),
        "turn_delta_improved_minus_astar": mean(tc_deltas) if tc_deltas else float("nan"),
        "expanded_delta_improved_minus_astar": mean(exp_deltas) if exp_deltas else float("nan"),
    }


def main():
    print("=" * 60)
    print("fix15_v2 实验开始（修复 smooth_corners + alpha 下界后）")
    print(f"地图数: 15 | 每图重复: {REPEATS} | 随机种子: {SEED}")
    print("=" * 60)

    all_raw = []
    t_start = time.time()

    for map_type, paths in MAP_FILES.items():
        print(f"\n[{map_type.upper()}] 开始处理 {len(paths)} 张地图...")
        for rel_path in paths:
            map_path = ROOT / rel_path
            if not map_path.exists():
                print(f"  ⚠️  地图文件不存在，跳过: {rel_path}")
                continue
            map_name = map_path.name
            rows = run_one_map(map_path, map_name, map_type, REPEATS, SEED)
            all_raw.extend(rows)

    print(f"\n总耗时: {time.time() - t_start:.1f}s | 总记录数: {len(all_raw)}")

    # 保存原始数据
    for map_type in ["dao", "street", "wc3"]:
        sub = [r for r in all_raw if r["map_type"] == map_type]
        save_csv(sub, RESULTS_DIR / f"exp_fix15_v2_{map_type}_raw_records.csv")

    # 构建汇总
    summary = build_summary(all_raw)
    save_csv(summary, RESULTS_DIR / "exp_fix15_v2_all_summary.csv")
    print(f"\n[OK] 汇总数据已保存: exp_fix15_v2_all_summary.csv")

    # 关键指标
    km = compute_key_metrics(summary)
    save_csv([km], RESULTS_DIR / "exp_fix15_v2_key_metrics.csv")
    print(f"\n[关键指标] improved_astar vs astar:")
    print(f"  运行时间比值: {km['runtime_ratio_improved_vs_astar']:.4f}x")
    print(f"  路径长度变化: {km['path_delta_improved_minus_astar']:+.4f}")
    print(f"  转弯次数变化: {km['turn_delta_improved_minus_astar']:+.4f}")

    # 生成对比图
    for map_type in ["dao", "street", "wc3"]:
        plot_comparison(summary, map_type, FIGURES_DIR / f"runtime_comparison_exp_fix15_v2_{map_type}.png")

    print("\n✅ fix15_v2 实验全部完成！")


if __name__ == "__main__":
    main()
