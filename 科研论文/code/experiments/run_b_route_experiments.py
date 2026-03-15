import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
import sys
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from planners import (
    dijkstra_search,
    improved_astar_search,
    jps_like_search,
    vanilla_astar_search,
    weighted_astar_search,
)
from planners.core import random_grid, sample_start_goal

RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"


def parse_args():
    parser = argparse.ArgumentParser(description="Run B-route planning experiments.")
    parser.add_argument("--sizes", type=str, default="20,40,80,100", help="Comma-separated map sizes")
    parser.add_argument("--ratios", type=str, default="0.3,0.7", help="Comma-separated obstacle ratios")
    parser.add_argument("--repeats", type=int, default=10, help="Repeats per size-ratio combo")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument(
        "--out_prefix",
        type=str,
        default="exp",
        help="Output file prefix, e.g. exp or exp_seed42",
    )
    return parser.parse_args()


def _algo_dict():
    return {
        "dijkstra": dijkstra_search,
        "astar": vanilla_astar_search,
        "weighted_astar": lambda g, s, t: weighted_astar_search(g, s, t, weight=1.2),
        "jps_like": jps_like_search,
        "improved_astar": improved_astar_search,
    }


def run_once(grid: np.ndarray, start, goal) -> List[Dict[str, object]]:
    rows = []
    for name, fn in _algo_dict().items():
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
        key = f"{r['size']}_{r['ratio']}_{r['algorithm']}"
        grouped[key].append(r)

    summary = []
    for key, values in grouped.items():
        size, ratio, algo = key.split("_", 2)
        succ = [v["success"] for v in values]
        runtime = [v["runtime_ms"] for v in values]
        plen = [v["path_length"] for v in values if not np.isnan(v["path_length"])]
        turns = [v["turn_count"] for v in values if not np.isnan(v["turn_count"])]
        expanded = [v["expanded_nodes"] for v in values]
        summary.append(
            {
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
    # Visualize the largest map with high obstacle ratio to highlight speed differences.
    candidates = [r for r in summary if r["size"] == max(x["size"] for x in summary) and abs(r["ratio"] - 0.7) < 1e-6]
    if not candidates:
        candidates = [r for r in summary if r["size"] == max(x["size"] for x in summary)]
    algos = [r["algorithm"] for r in candidates]
    vals = [r["runtime_ms_mean"] for r in candidates]

    plt.figure(figsize=(9, 4))
    plt.bar(algos, vals)
    plt.ylabel("Runtime (ms)")
    plt.title("Runtime Comparison (B-route)")
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
                one = run_once(grid, start, goal)
                for row in one:
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
