import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
import sys
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from planners import (
    ablation_no_adaptive_weight,
    ablation_no_jump_like,
    ablation_no_smoothing,
    dijkstra_search,
    improved_astar_search,
    jps_like_search,
    vanilla_astar_search,
    weighted_astar_search,
)
from utils.map_loader import list_supported_maps, load_grid_map
from planners.core import random_grid, sample_start_goal
from utils.scen_loader import build_scen_index

RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"


def parse_args():
    parser = argparse.ArgumentParser(description="Run B-route planning experiments.")
    parser.add_argument("--sizes", type=str, default="20,40,80,100", help="Comma-separated map sizes")
    parser.add_argument("--ratios", type=str, default="0.3,0.7", help="Comma-separated obstacle ratios")
    parser.add_argument("--repeats", type=int, default=10, help="Repeats per size-ratio combo")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--map_dir", type=str, default="", help="Directory of benchmark maps (.map/.txt/.csv)")
    parser.add_argument(
        "--scen_dir",
        type=str,
        default="",
        help="Optional directory of MovingAI .scen files for fixed start-goal tasks",
    )
    parser.add_argument("--map_limit", type=int, default=0, help="Optional max number of maps to load")
    parser.add_argument(
        "--scen_limit_per_map",
        type=int,
        default=0,
        help="Optional max number of scenario rows per map (0 means all)",
    )
    parser.add_argument(
        "--out_prefix",
        type=str,
        default="exp",
        help="Output file prefix, e.g. exp or exp_seed42",
    )
    parser.add_argument(
        "--include_ablation",
        action="store_true",
        help="Include ablation groups for improved A* module study",
    )
    return parser.parse_args()


def _algo_dict(include_ablation: bool = False):
    algos = {
        "dijkstra": dijkstra_search,
        "astar": vanilla_astar_search,
        "weighted_astar": lambda g, s, t: weighted_astar_search(g, s, t, weight=1.2),
        "jps_like": jps_like_search,
        "improved_astar": improved_astar_search,
    }
    if include_ablation:
        algos.update(
            {
                "ablation_no_adaptive": ablation_no_adaptive_weight,
                "ablation_no_jump": ablation_no_jump_like,
                "ablation_no_smoothing": ablation_no_smoothing,
            }
        )
    return algos


def run_once(grid: np.ndarray, start, goal, include_ablation: bool = False) -> List[Dict[str, object]]:
    rows = []
    for name, fn in _algo_dict(include_ablation=include_ablation).items():
        res = fn(grid, start, goal)
        rows.append(
            {
                "algorithm": name,
                "success": int(res["success"]),
                "path_length": float(res["path_length"]) if res["success"] else np.nan,
                "turn_count": int(res["turn_count"]) if res["success"] else np.nan,
                "runtime_ms": float(res["runtime_ms"]),
                "expanded_nodes": int(res["expanded_nodes"]),
            }
        )
    return rows


def save_raw(rows: List[Dict[str, object]], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_summary(rows: List[Dict[str, object]], path: Path):
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for r in rows:
        key = f"{r['map_name']}|{r['size']}|{r['ratio']}|{r['algorithm']}"
        grouped[key].append(r)

    summary = []
    for key, values in grouped.items():
        map_name, size, ratio, algo = key.split("|", 3)
        succ = [v["success"] for v in values]
        runtime = [v["runtime_ms"] for v in values]
        plen = [v["path_length"] for v in values if not np.isnan(v["path_length"])]
        turns = [v["turn_count"] for v in values if not np.isnan(v["turn_count"])]
        expanded = [v["expanded_nodes"] for v in values]
        summary.append(
            {
                "map_name": map_name,
                "size": int(size),
                "ratio": float(ratio),
                "algorithm": algo,
                "effective_repeats": len(values),
                "success_rate": mean(succ),
                "runtime_ms_mean": mean(runtime),
                "runtime_ms_std": pstdev(runtime) if len(runtime) > 1 else 0.0,
                "path_length_mean": mean(plen) if plen else np.nan,
                "turn_count_mean": mean(turns) if turns else np.nan,
                "expanded_nodes_mean": mean(expanded),
            }
        )

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    return summary


def plot_runtime(summary: List[Dict[str, object]], out_png: Path):
    # Pick one representative map to keep output simple.
    map_names = sorted({r["map_name"] for r in summary})
    focus_map = map_names[0]
    candidates = [r for r in summary if r["map_name"] == focus_map]
    algos = [r["algorithm"] for r in candidates]
    vals = [r["runtime_ms_mean"] for r in candidates]

    plt.figure(figsize=(9, 4))
    plt.bar(algos, vals)
    plt.ylabel("Runtime (ms)")
    plt.title(f"Runtime Comparison ({focus_map})")
    plt.xticks(rotation=20)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=180)
    plt.close()


def save_sampling_trace(rows: List[Dict[str, object]], path: Path):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()
    sizes = [int(x.strip()) for x in args.sizes.split(",") if x.strip()]
    ratios = [float(x.strip()) for x in args.ratios.split(",") if x.strip()]
    rng = np.random.default_rng(args.seed)

    raw_rows: List[Dict[str, object]] = []
    trace_rows: List[Dict[str, object]] = []
    map_dir = Path(args.map_dir) if args.map_dir else None
    scen_dir = Path(args.scen_dir) if args.scen_dir else None

    benchmark_maps: Optional[List[Path]] = None
    scen_index: Optional[Dict[str, List[Dict[str, object]]]] = None
    if map_dir:
        benchmark_maps = list_supported_maps(map_dir)
        if args.map_limit > 0:
            benchmark_maps = benchmark_maps[: args.map_limit]
        if not benchmark_maps:
            raise ValueError(f"No supported map files found in: {map_dir}")
        if scen_dir:
            scen_index = build_scen_index(scen_dir)
            if not scen_index:
                raise ValueError(f"No .scen rows found in: {scen_dir}")

    if benchmark_maps:
        # Benchmark mode: use external authoritative maps.
        for map_path in benchmark_maps:
            grid = load_grid_map(map_path)
            h, w = grid.shape
            ratio = float(np.mean(grid == 1))
            size = int(max(h, w))
            if scen_index is not None:
                scen_rows = scen_index.get(map_path.name, [])
                if args.scen_limit_per_map > 0:
                    scen_rows = scen_rows[: args.scen_limit_per_map]
                if len(scen_rows) < args.repeats:
                    raise ValueError(
                        f"Map {map_path.name} only has {len(scen_rows)} scenarios, "
                        f"less than repeats={args.repeats}. Increase scen_limit_per_map or reduce repeats."
                    )
                for run_id, scen in enumerate(scen_rows[: args.repeats]):
                    start = scen["start"]
                    goal = scen["goal"]
                    trace = {
                        "map_name": map_path.name,
                        "size": size,
                        "ratio": ratio,
                        "attempt_id": run_id,
                        "accepted": 0,
                        "reason": "",
                        "scenario_file": scen["scen_file"],
                        "scenario_bucket": scen["bucket"],
                        "scenario_optlen": scen["optimal_length"],
                    }
                    sx, sy = start
                    gx, gy = goal
                    if not (0 <= sx < h and 0 <= sy < w and 0 <= gx < h and 0 <= gy < w):
                        trace["reason"] = "scenario_out_of_bounds"
                        trace_rows.append(trace)
                        continue
                    if grid[sx, sy] == 1 or grid[gx, gy] == 1:
                        trace["reason"] = "scenario_on_obstacle"
                        trace_rows.append(trace)
                        continue
                    one = run_once(grid, start, goal, include_ablation=args.include_ablation)
                    for row in one:
                        row["map_name"] = map_path.name
                        row["size"] = size
                        row["ratio"] = ratio
                        row["run_id"] = run_id
                        row["attempt_id"] = run_id
                        row["scenario_file"] = scen["scen_file"]
                        row["scenario_bucket"] = scen["bucket"]
                        row["scenario_optlen"] = scen["optimal_length"]
                        raw_rows.append(row)
                    trace["accepted"] = 1
                    trace["reason"] = "valid_scenario_sample"
                    trace_rows.append(trace)
            else:
                valid_count = 0
                attempt_id = 0
                max_attempts = max(args.repeats * 20, args.repeats)
                while valid_count < args.repeats and attempt_id < max_attempts:
                    local_rng = np.random.default_rng(rng.integers(0, 1_000_000_000))
                    sg = sample_start_goal(grid, local_rng)
                    trace = {
                        "map_name": map_path.name,
                        "size": size,
                        "ratio": ratio,
                        "attempt_id": attempt_id,
                        "accepted": 0,
                        "reason": "",
                    }
                    if sg is None:
                        trace["reason"] = "no_reachable_start_goal"
                        trace_rows.append(trace)
                        attempt_id += 1
                        continue
                    start, goal = sg
                    one = run_once(grid, start, goal, include_ablation=args.include_ablation)
                    for row in one:
                        row["map_name"] = map_path.name
                        row["size"] = size
                        row["ratio"] = ratio
                        row["run_id"] = valid_count
                        row["attempt_id"] = attempt_id
                        raw_rows.append(row)
                    trace["accepted"] = 1
                    trace["reason"] = "valid_sample"
                    trace_rows.append(trace)
                    valid_count += 1
                    attempt_id += 1
    else:
        # Random mode: legacy behavior.
        for size in sizes:
            for ratio in ratios:
                valid_count = 0
                attempt_id = 0
                max_attempts = max(args.repeats * 20, args.repeats)
                while valid_count < args.repeats and attempt_id < max_attempts:
                    local_rng = np.random.default_rng(rng.integers(0, 1_000_000_000))
                    grid = random_grid(size, ratio, local_rng)
                    sg = sample_start_goal(grid, local_rng)
                    trace = {
                        "map_name": "random_generated",
                        "size": size,
                        "ratio": ratio,
                        "attempt_id": attempt_id,
                        "accepted": 0,
                        "reason": "",
                    }
                    if sg is None:
                        trace["reason"] = "no_reachable_start_goal"
                        trace_rows.append(trace)
                        attempt_id += 1
                        continue
                    start, goal = sg
                    one = run_once(grid, start, goal, include_ablation=args.include_ablation)
                    for row in one:
                        row["map_name"] = "random_generated"
                        row["size"] = size
                        row["ratio"] = ratio
                        row["run_id"] = valid_count
                        row["attempt_id"] = attempt_id
                        raw_rows.append(row)
                    trace["accepted"] = 1
                    trace["reason"] = "valid_sample"
                    trace_rows.append(trace)
                    valid_count += 1
                    attempt_id += 1

    raw_path = RESULTS_DIR / f"{args.out_prefix}_raw_records.csv"
    summary_path = RESULTS_DIR / f"{args.out_prefix}_summary.csv"
    trace_path = RESULTS_DIR / f"{args.out_prefix}_sampling_trace.csv"
    fig_path = FIGURES_DIR / f"runtime_comparison_{args.out_prefix}.png"

    save_raw(raw_rows, raw_path)
    save_sampling_trace(trace_rows, trace_path)
    summary = save_summary(raw_rows, summary_path)
    plot_runtime(summary, fig_path)

    print(f"[OK] Raw saved: {raw_path}")
    print(f"[OK] Summary saved: {summary_path}")
    print(f"[OK] Sampling trace saved: {trace_path}")
    print(f"[OK] Figure saved: {fig_path}")


if __name__ == "__main__":
    main()
