import math
import time
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

import sys
ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from planners.algorithms import astar_search
from planners.core import simplify_path, smooth_corners, path_length, turn_count
from utils.map_loader import list_supported_maps, load_grid_map
from utils.scen_loader import build_scen_index


# ====== 你可以改这两个参数控制耗时 ======
MAPS_PER_DATASET = 2      # 每个数据集取前N张地图参与调参
SCEN_PER_MAP = 10         # 每张地图取前N个scen任务
# ======================================


def build_candidates() -> List[Tuple[str, Callable[[float], float]]]:
    cands = []

    # 基线：固定权重（等价 no_adaptive 的核心权重）
    cands.append(("fixed_1.2", lambda r: 1.2))

    # 当前默认公式（你现有版本）
    cands.append(("log_clip_0.8_1.8", lambda r: min(max(abs(math.log(min(max(r, 0.01), 0.99))), 0.8), 1.8)))

    # 网格1：log + clip 参数网格
    for lo in [0.8, 0.9, 1.0, 1.1]:
        for hi in [1.4, 1.6, 1.8, 2.0]:
            name = f"log_clip_{lo}_{hi}"
            cands.append((name, lambda r, lo=lo, hi=hi: min(max(abs(math.log(min(max(r, 0.01), 0.99))), lo), hi)))

    # 网格2：线性映射 alpha = clip(base + k*r, 1.0, 2.0)
    for base in [0.9, 1.0, 1.1]:
        for k in [0.6, 0.8, 1.0, 1.2]:
            name = f"linear_b{base}_k{k}"
            cands.append((name, lambda r, base=base, k=k: min(max(base + k * r, 1.0), 2.0)))

    # 去重（避免和基线重名）
    uniq = {}
    for n, f in cands:
        uniq[n] = f
    return list(uniq.items())


def load_tasks() -> List[Dict]:
    dataset_pairs = [
        ("dao", ROOT / "data/benchmark_maps/dao-map", ROOT / "data/benchmark_scens/dao"),
        ("street", ROOT / "data/benchmark_maps/street-map", ROOT / "data/benchmark_scens/street"),
        ("wc3", ROOT / "data/benchmark_maps/wc3maps512-map", ROOT / "data/benchmark_scens/wc3maps512"),
        ("weighted", ROOT / "data/benchmark_maps/weighted-map", ROOT / "data/benchmark_scens/weighted"),
    ]

    tasks = []
    for ds_name, map_dir, scen_dir in dataset_pairs:
        if not map_dir.exists() or not scen_dir.exists():
            print(f"[WARN] 跳过数据集 {ds_name}: 缺少目录")
            continue

        maps = list_supported_maps(map_dir)
        if not maps:
            print(f"[WARN] 跳过数据集 {ds_name}: 无地图")
            continue
        maps = maps[:MAPS_PER_DATASET]

        scen_index = build_scen_index(scen_dir)
        if not scen_index:
            print(f"[WARN] 跳过数据集 {ds_name}: 无scen")
            continue

        for mp in maps:
            mname = mp.name
            if mname not in scen_index:
                print(f"[WARN] {ds_name} {mname} 无匹配scen，跳过")
                continue

            grid = load_grid_map(mp)
            h, w = grid.shape
            ratio = float(np.mean(grid == 1))
            scen_rows = scen_index[mname][:SCEN_PER_MAP]

            valid_cnt = 0
            for sc in scen_rows:
                sx, sy = sc["start"]
                gx, gy = sc["goal"]

                if not (0 <= sx < h and 0 <= sy < w and 0 <= gx < h and 0 <= gy < w):
                    continue
                if grid[sx, sy] == 1 or grid[gx, gy] == 1:
                    continue

                tasks.append(
                    {
                        "dataset": ds_name,
                        "map_name": mname,
                        "ratio": ratio,
                        "size": int(max(h, w)),
                        "grid": grid,
                        "start": (sx, sy),
                        "goal": (gx, gy),
                    }
                )
                valid_cnt += 1

            print(f"[INFO] {ds_name} | {mname} | tasks={valid_cnt}")

    if not tasks:
        raise RuntimeError("没有可用任务，请检查 map/scen 目录")
    print(f"[INFO] 总任务数: {len(tasks)}")
    return tasks


def run_candidate(name: str, alpha_fn: Callable[[float], float], tasks: List[Dict]) -> Dict:
    rows = []
    for t in tasks:
        alpha = float(alpha_fn(t["ratio"]))

        t0 = time.perf_counter()
        res = astar_search(
            t["grid"],
            t["start"],
            t["goal"],
            heuristic_mode="octile",
            weight=alpha,
        )
        runtime_ms = (time.perf_counter() - t0) * 1000.0

        if res["success"]:
            p0 = res["path"]
            p1 = simplify_path(p0, t["grid"])
            p2 = smooth_corners(p1, t["grid"])
            plen = float(path_length(p2))
            turns = int(turn_count(p2))
            succ = 1
        else:
            plen = np.nan
            turns = np.nan
            succ = 0

        rows.append(
            {
                "candidate": name,
                "dataset": t["dataset"],
                "map_name": t["map_name"],
                "size": t["size"],
                "ratio": t["ratio"],
                "alpha": alpha,
                "success": succ,
                "runtime_ms": runtime_ms,
                "path_length": plen,
                "turn_count": turns,
                "expanded_nodes": int(res["expanded_nodes"]),
            }
        )

    df = pd.DataFrame(rows)
    out = {
        "candidate": name,
        "effective_samples": len(df),
        "success_rate": float(df["success"].mean()),
        "runtime_ms_mean": float(df["runtime_ms"].mean()),
        "path_length_mean": float(df["path_length"].mean(skipna=True)),
        "turn_count_mean": float(df["turn_count"].mean(skipna=True)),
        "expanded_nodes_mean": float(df["expanded_nodes"].mean()),
    }
    return out, df


def main():
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks()
    cands = build_candidates()
    print(f"[INFO] 候选参数组数: {len(cands)}")

    sum_rows = []
    raw_frames = []

    for i, (name, fn) in enumerate(cands, 1):
        s, raw = run_candidate(name, fn, tasks)
        sum_rows.append(s)
        raw_frames.append(raw)
        print(f"[{i}/{len(cands)}] {name} | succ={s['success_rate']:.3f} | rt={s['runtime_ms_mean']:.4f}")

    summary = pd.DataFrame(sum_rows).sort_values(["success_rate", "runtime_ms_mean"], ascending=[False, True])
    raw_all = pd.concat(raw_frames, ignore_index=True)

    # 相对 fixed_1.2 的增量
    base = summary[summary["candidate"] == "fixed_1.2"].iloc[0]
    summary["d_runtime_vs_fixed"] = summary["runtime_ms_mean"] - base["runtime_ms_mean"]
    summary["d_path_vs_fixed"] = summary["path_length_mean"] - base["path_length_mean"]
    summary["d_turn_vs_fixed"] = summary["turn_count_mean"] - base["turn_count_mean"]
    summary["d_expand_vs_fixed"] = summary["expanded_nodes_mean"] - base["expanded_nodes_mean"]

    # 推荐规则：优先成功率>=0.99 且路径不劣化太多，再选最快
    filt = summary[
        (summary["success_rate"] >= 0.99) &
        (summary["d_path_vs_fixed"] <= 0.03)
    ].copy()
    if len(filt) == 0:
        filt = summary.copy()
    best = filt.sort_values(["runtime_ms_mean", "expanded_nodes_mean"], ascending=[True, True]).iloc[0]

    summary.to_csv(results_dir / "adaptive_alpha_gridsearch_summary.csv", index=False, encoding="utf-8-sig")
    raw_all.to_csv(results_dir / "adaptive_alpha_gridsearch_raw.csv", index=False, encoding="utf-8-sig")

    rec = pd.DataFrame([best])
    rec.to_csv(results_dir / "adaptive_alpha_recommendation.csv", index=False, encoding="utf-8-sig")

    print("\n[OK] 调参完成")
    print("[OK] summary:", results_dir / "adaptive_alpha_gridsearch_summary.csv")
    print("[OK] raw    :", results_dir / "adaptive_alpha_gridsearch_raw.csv")
    print("[OK] best   :", results_dir / "adaptive_alpha_recommendation.csv")
    print("\n=== 推荐参数 ===")
    print(rec.to_string(index=False))


if __name__ == "__main__":
    main()
