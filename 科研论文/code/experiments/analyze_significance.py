import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
DOCS_DIR = ROOT / "docs"


def parse_args():
    parser = argparse.ArgumentParser(description="Permutation significance analysis for planning experiments.")
    parser.add_argument("--n_perm", type=int, default=5000, help="Permutation count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--raw_file", type=str, default="exp_raw_records.csv", help="Raw records filename in results/")
    parser.add_argument("--out_prefix", type=str, default="exp", help="Output prefix, e.g. exp or exp_seed42")
    return parser.parse_args()


def permutation_pvalue(a: np.ndarray, b: np.ndarray, rng: np.random.Generator, n_perm: int = 5000) -> Tuple[float, float]:
    """
    Two-sided permutation test for difference in means.
    Returns (observed_diff, pvalue), where observed_diff = mean(a)-mean(b).
    """
    observed = float(np.mean(a) - np.mean(b))
    pooled = np.concatenate([a, b])
    n_a = len(a)
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(pooled)
        diff = float(np.mean(perm[:n_a]) - np.mean(perm[n_a:]))
        if abs(diff) >= abs(observed):
            count += 1
    p = (count + 1) / (n_perm + 1)
    return observed, p


def summarize_effect(improved: float, baseline: float, lower_better: bool = True) -> float:
    if lower_better:
        if baseline == 0:
            return 0.0
        return (baseline - improved) / baseline * 100.0
    if baseline == 0:
        return 0.0
    return (improved - baseline) / baseline * 100.0


def benjamini_hochberg(p_values: List[float]) -> List[float]:
    n = len(p_values)
    order = np.argsort(p_values)
    ranked = np.array(p_values, dtype=float)[order]
    q = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        val = ranked[i] * n / rank
        prev = min(prev, val)
        q[i] = min(prev, 1.0)
    out = np.empty(n, dtype=float)
    out[order] = q
    return out.tolist()


def main():
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    raw_path = RESULTS_DIR / args.raw_file
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw file: {raw_path}")
    raw = pd.read_csv(raw_path)

    # Pair by same scenario and run_id for fairness.
    key_cols = ["size", "ratio", "run_id"]
    if "seed_tag" in raw.columns:
        key_cols.append("seed_tag")
    metrics = ["runtime_ms", "path_length", "turn_count"]
    baselines = ["astar", "weighted_astar", "jps_like", "dijkstra"]

    rows: List[Dict[str, object]] = []
    for size in sorted(raw["size"].unique()):
        for ratio in sorted(raw["ratio"].unique()):
            sub = raw[(raw["size"] == size) & (raw["ratio"] == ratio)]
            imp = sub[sub["algorithm"] == "improved_astar"][key_cols + metrics].copy()
            if imp.empty:
                continue
            for base_name in baselines:
                base = sub[sub["algorithm"] == base_name][key_cols + metrics].copy()
                if base.empty:
                    continue
                merged = imp.merge(base, on=key_cols, suffixes=("_imp", "_base"))
                if merged.empty:
                    continue
                for metric in metrics:
                    a = merged[f"{metric}_imp"].to_numpy(dtype=float)
                    b = merged[f"{metric}_base"].to_numpy(dtype=float)
                    obs, p = permutation_pvalue(a, b, rng, n_perm=args.n_perm)
                    imp_mean = float(np.mean(a))
                    base_mean = float(np.mean(b))
                    effect_pct = summarize_effect(imp_mean, base_mean, lower_better=True)
                    rows.append(
                        {
                            "size": int(size),
                            "ratio": float(ratio),
                            "metric": metric,
                            "baseline": base_name,
                            "n_pairs": int(len(a)),
                            "improved_mean": imp_mean,
                            "baseline_mean": base_mean,
                            "mean_diff_imp_minus_base": obs,
                            "improvement_percent": effect_pct,
                            "p_value_perm_two_sided": p,
                            "significant_p_lt_0_05": int(p < 0.05),
                        }
                    )

    if rows:
        q_values = benjamini_hochberg([float(r["p_value_perm_two_sided"]) for r in rows])
        for r, q in zip(rows, q_values):
            r["q_value_bh_fdr"] = q
            r["significant_q_lt_0_05"] = int(q < 0.05)

    out_csv = RESULTS_DIR / f"{args.out_prefix}_significance.csv"
    if rows:
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # Build a concise markdown report with key conclusions.
    report_path = DOCS_DIR / f"统计检验报告_{args.out_prefix}_v1.md"
    lines = [
        "# 统计检验报告 v1",
        "",
        "## 方法",
        "- 检验对象：`improved_astar` 对比 `astar / weighted_astar / jps_like / dijkstra`",
        "- 分场景检验：按 `size x ratio` 分组",
        "- 指标：`runtime_ms`, `path_length`, `turn_count`",
        "- 检验方法：双侧置换检验（permutation test）",
        f"- 置换次数：`{args.n_perm}`",
        "",
        "## 结果文件",
        f"- `results/{out_csv.name}`",
        "",
    ]

    if rows:
        df = pd.DataFrame(rows)
        # Focus on improved vs astar for primary claim.
        primary = df[df["baseline"] == "astar"].copy()
        sig_runtime_p = primary[(primary["metric"] == "runtime_ms") & (primary["significant_p_lt_0_05"] == 1)]
        sig_path_p = primary[(primary["metric"] == "path_length") & (primary["significant_p_lt_0_05"] == 1)]
        sig_turn_p = primary[(primary["metric"] == "turn_count") & (primary["significant_p_lt_0_05"] == 1)]
        sig_runtime_q = primary[(primary["metric"] == "runtime_ms") & (primary["significant_q_lt_0_05"] == 1)]
        sig_path_q = primary[(primary["metric"] == "path_length") & (primary["significant_q_lt_0_05"] == 1)]
        sig_turn_q = primary[(primary["metric"] == "turn_count") & (primary["significant_q_lt_0_05"] == 1)]

        lines.extend(
            [
                "## 对比传统A*的显著性统计",
                f"- 运行时间显著场景数（p<0.05）：`{len(sig_runtime_p)}`",
                f"- 路径长度显著场景数（p<0.05）：`{len(sig_path_p)}`",
                f"- 转弯次数显著场景数（p<0.05）：`{len(sig_turn_p)}`",
                f"- 运行时间显著场景数（FDR q<0.05）：`{len(sig_runtime_q)}`",
                f"- 路径长度显著场景数（FDR q<0.05）：`{len(sig_path_q)}`",
                f"- 转弯次数显著场景数（FDR q<0.05）：`{len(sig_turn_q)}`",
                "",
                "## 备注",
                "- 置换检验不依赖正态分布假设，适合当前小样本与非高斯分布场景。",
                "- 已加入 Benjamini-Hochberg 多重比较校正，减少多指标多场景带来的假阳性风险。",
            ]
        )
    else:
        lines.extend(["## 结果", "- 未生成可检验样本，请检查原始数据。"])

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Significance csv saved: {out_csv}")
    print(f"[OK] Report saved: {report_path}")


if __name__ == "__main__":
    main()
