"""
v3 统计显著性检验脚本
- 基于 results/exp_fix15_v3_all_summary.csv
- 对 improved_astar vs astar 在三项指标上做 Wilcoxon 符号秩检验
- 多重比较使用 BH-FDR 校正
- 输出 results/exp_fix15_v3_significance.csv
"""
import pandas as pd
import numpy as np
from scipy import stats

# ── 数据加载 ──────────────────────────────────────────────
CSV_PATH = "results/exp_fix15_v3_all_summary.csv"
OUT_PATH = "results/exp_fix15_v3_significance.csv"

df = pd.read_csv(CSV_PATH)

# 只取 improved_astar 和 astar 两组
imp = df[df["algorithm"] == "improved_astar"].copy()
astar = df[df["algorithm"] == "astar"].copy()

# 按 map_name 对齐（两组应有相同的 15 张地图）
imp = imp.set_index("map_name").sort_index()
astar = astar.set_index("map_name").sort_index()

assert list(imp.index) == list(astar.index), "地图名称不一致，请检查数据"

metrics = {
    "runtime_ms":    ("runtime_ms_mean",    "运行时间 (ms)"),
    "path_length":   ("path_length_mean",   "路径长度"),
    "turn_count":    ("turn_count_mean",    "转弯次数"),
}

# ── Wilcoxon 符号秩检验 ────────────────────────────────────
results = []
raw_pvals = []

for key, (col, label) in metrics.items():
    x_imp = imp[col].values
    x_ast = astar[col].values
    diff = x_imp - x_ast  # 改进A* - 传统A*

    stat, pval = stats.wilcoxon(diff, alternative="two-sided")
    mean_imp = x_imp.mean()
    mean_ast = x_ast.mean()
    mean_diff = diff.mean()
    pct_change = mean_diff / mean_ast * 100

    results.append({
        "metric":           key,
        "metric_label":     label,
        "n_maps":           len(x_imp),
        "mean_astar":       round(mean_ast, 6),
        "mean_improved":    round(mean_imp, 6),
        "mean_diff":        round(mean_diff, 6),
        "pct_change":       round(pct_change, 2),
        "wilcoxon_stat":    round(stat, 4),
        "p_value_raw":      pval,
    })
    raw_pvals.append(pval)

# ── BH-FDR 校正 ───────────────────────────────────────────
def bh_fdr(pvals, alpha=0.05):
    """Benjamini-Hochberg FDR correction."""
    n = len(pvals)
    sorted_idx = np.argsort(pvals)
    sorted_pvals = np.array(pvals)[sorted_idx]
    bh_threshold = (np.arange(1, n + 1) / n) * alpha
    reject = sorted_pvals <= bh_threshold
    # 调整后 p 值
    adj = np.minimum(1.0, sorted_pvals * n / (np.arange(1, n + 1)))
    # 保证单调性
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    # 还原原始顺序
    adj_pvals = np.empty(n)
    adj_pvals[sorted_idx] = adj
    return adj_pvals

adj_pvals = bh_fdr(raw_pvals)

for i, r in enumerate(results):
    r["p_value_bh_fdr"]  = round(adj_pvals[i], 6)
    r["significant_005"] = "是" if adj_pvals[i] < 0.05 else "否"
    r["effect_direction"] = "改进A*更优" if r["mean_diff"] < 0 else "传统A*更优"

# ── 输出 CSV ──────────────────────────────────────────────
out_df = pd.DataFrame(results, columns=[
    "metric", "metric_label", "n_maps",
    "mean_astar", "mean_improved", "mean_diff", "pct_change",
    "wilcoxon_stat", "p_value_raw", "p_value_bh_fdr",
    "significant_005", "effect_direction"
])
out_df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
print(f"[OK] 显著性检验结果已保存：{OUT_PATH}")
print()
print(out_df[["metric_label", "mean_astar", "mean_improved", "pct_change",
              "p_value_raw", "p_value_bh_fdr", "significant_005"]].to_string(index=False))
