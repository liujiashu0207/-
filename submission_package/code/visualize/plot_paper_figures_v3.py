"""
Generate publication-quality figures for the paper.
  fig1: Runtime comparison by map type (bar chart)
  fig2: Turn count comparison by map type (bar chart)
  fig3: Ablation study (grouped bar chart)

Usage:
    python code/visualize/plot_paper_figures_v3.py
"""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "SimHei",
    "axes.unicode_minus": False,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
SUMMARY_CSV = RESULTS_DIR / "exp_fix15_v3_all_summary.csv"

MAP_TYPE_ORDER = ["DAO", "Street", "WC3"]
MAP_TYPE_LABELS_CN = {"DAO": "DAO 游戏地图", "Street": "Street 城市地图", "WC3": "WC3 魔兽地图"}

ALGO_COLORS = {
    "dijkstra":       "#95a5a6",
    "astar":          "#3498db",
    "weighted_astar": "#e67e22",
    "improved_astar": "#e74c3c",
}
ALGO_LABELS_CN = {
    "dijkstra":       "Dijkstra",
    "astar":          "传统 A*",
    "weighted_astar": "加权 A*(α=1.2)",
    "improved_astar": "改进 A*(本文)",
}


def load_summary():
    rows = []
    with SUMMARY_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["runtime_ms_mean"] = float(r["runtime_ms_mean"])
            r["path_length_mean"] = float(r["path_length_mean"])
            r["turn_count_mean"] = float(r["turn_count_mean"])
            r["expanded_nodes_mean"] = float(r["expanded_nodes_mean"])
            r["obstacle_ratio"] = float(r["obstacle_ratio"])
            rows.append(r)
    return rows


def aggregate_by_map_type(rows, metric):
    per_type = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["map_name"].startswith("GLOBAL"):
            continue
        per_type[r["map_type"]][r["algorithm"]].append(r[metric])
    result = {}
    for mt in MAP_TYPE_ORDER:
        result[mt] = {}
        for algo in ALGO_COLORS:
            vals = per_type[mt].get(algo, [])
            result[mt][algo] = np.mean(vals) if vals else 0.0
    return result


def fig1_runtime(rows):
    data = aggregate_by_map_type(rows, "runtime_ms_mean")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5),
                                    gridspec_kw={"width_ratios": [1, 1.2]})

    x = np.arange(len(MAP_TYPE_ORDER))
    width = 0.18
    algos = list(ALGO_COLORS.keys())

    for i, algo in enumerate(algos):
        vals = [data[mt][algo] for mt in MAP_TYPE_ORDER]
        bars = ax1.bar(x + i * width, vals, width, label=ALGO_LABELS_CN[algo],
                       color=ALGO_COLORS[algo], edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                     f"{v:.4f}", ha="center", va="bottom", fontsize=7)

    ax1.set_xlabel("地图类型")
    ax1.set_ylabel("平均运行时间 (ms)")
    ax1.set_title("(a) 全部算法")
    ax1.set_xticks(x + width * 1.5)
    ax1.set_xticklabels([MAP_TYPE_LABELS_CN[mt] for mt in MAP_TYPE_ORDER])
    ax1.legend(loc="upper left", framealpha=0.9, fontsize=8)
    ax1.set_ylim(0, ax1.get_ylim()[1] * 1.15)
    ax1.grid(axis="y", alpha=0.3, linestyle="--")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    focus_algos = ["astar", "weighted_astar", "improved_astar"]
    width2 = 0.22
    for i, algo in enumerate(focus_algos):
        vals = [data[mt][algo] for mt in MAP_TYPE_ORDER]
        bars = ax2.bar(x + i * width2, vals, width2, label=ALGO_LABELS_CN[algo],
                       color=ALGO_COLORS[algo], edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.0005,
                     f"{v:.4f}", ha="center", va="bottom", fontsize=7.5)

    ax2.set_xlabel("地图类型")
    ax2.set_ylabel("平均运行时间 (ms)")
    ax2.set_title("(b) A* 系列放大对比")
    ax2.set_xticks(x + width2)
    ax2.set_xticklabels([MAP_TYPE_LABELS_CN[mt] for mt in MAP_TYPE_ORDER])
    ax2.legend(loc="upper left", framealpha=0.9, fontsize=8)
    ax2.grid(axis="y", alpha=0.3, linestyle="--")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.suptitle("图 1  各算法运行时间对比（按地图类型）", fontsize=13, y=1.02)
    fig.tight_layout()
    out = FIGURES_DIR / "fig1_runtime_comparison_v3.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[OK] {out}")


def fig2_turncount(rows):
    data = aggregate_by_map_type(rows, "turn_count_mean")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={"width_ratios": [1, 1]})

    x = np.arange(len(MAP_TYPE_ORDER))
    width = 0.22
    algos_left = ["dijkstra", "astar", "weighted_astar"]
    for i, algo in enumerate(algos_left):
        vals = [data[mt][algo] for mt in MAP_TYPE_ORDER]
        bars = ax1.bar(x + i * width, vals, width, label=ALGO_LABELS_CN[algo],
                       color=ALGO_COLORS[algo], edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                     f"{v:.3f}", ha="center", va="bottom", fontsize=7)

    ax1.set_xlabel("地图类型")
    ax1.set_ylabel("平均转弯次数")
    ax1.set_title("(a) Dijkstra / A* / 加权A*")
    ax1.set_xticks(x + width)
    ax1.set_xticklabels([MAP_TYPE_LABELS_CN[mt] for mt in MAP_TYPE_ORDER])
    ax1.legend(fontsize=8)
    ax1.grid(axis="y", alpha=0.3, linestyle="--")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    vals_improved = [data[mt]["improved_astar"] for mt in MAP_TYPE_ORDER]
    bars = ax2.bar(x, vals_improved, 0.5, color=ALGO_COLORS["improved_astar"],
                   edgecolor="white", linewidth=0.5, label=ALGO_LABELS_CN["improved_astar"])
    for bar, v in zip(bars, vals_improved):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                 f"{v:.4f}", ha="center", va="bottom", fontsize=8)

    ax2.set_xlabel("地图类型")
    ax2.set_ylabel("平均转弯次数")
    ax2.set_title("(b) 改进 A*（本文）")
    ax2.set_xticks(x)
    ax2.set_xticklabels([MAP_TYPE_LABELS_CN[mt] for mt in MAP_TYPE_ORDER])
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3, linestyle="--")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.suptitle("图 2  各算法转弯次数对比（按地图类型）", fontsize=13, y=1.02)
    fig.tight_layout()
    out = FIGURES_DIR / "fig2_turncount_comparison_v3.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[OK] {out}")


def fig3_ablation(rows):
    ablation_rows = [r for r in rows if r["map_name"].startswith("GLOBAL")]
    if not ablation_rows:
        print("[WARN] No ablation data found, skipping fig3.")
        return

    configs = ["improved_astar", "ablation_no_adaptive", "ablation_no_smoothing", "astar"]
    config_labels = [
        "完整改进A*\n(本文)",
        "消融: 无自适应\n权重",
        "消融: 无路径\n平滑",
        "传统 A*\n(基线)",
    ]
    config_colors = ["#e74c3c", "#f39c12", "#9b59b6", "#3498db"]

    metrics = ["runtime_ms_mean", "path_length_mean", "turn_count_mean", "expanded_nodes_mean"]
    metric_labels = ["运行时间 (ms)", "路径长度", "转弯次数", "扩展节点数"]

    data_map = {r["algorithm"]: r for r in ablation_rows}

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()

    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        ax = axes[idx]
        vals = [data_map[c][metric] for c in configs]
        bars = ax.bar(range(len(configs)), vals, color=config_colors,
                      edgecolor="white", linewidth=0.5, width=0.6)
        for bar, v in zip(bars, vals):
            fmt = f"{v:.4f}" if v < 1 else f"{v:.2f}"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vals) * 0.02,
                    fmt, ha="center", va="bottom", fontsize=8)
        ax.set_ylabel(label)
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels(config_labels, fontsize=8)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_ylim(0, max(vals) * 1.2)

    fig.suptitle("图 3  消融实验结果（全局15张地图均值）", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = FIGURES_DIR / "fig3_ablation_study_v3.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[OK] {out}")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_summary()
    print(f"Loaded {len(rows)} rows from {SUMMARY_CSV}")
    fig1_runtime(rows)
    fig2_turncount(rows)
    fig3_ablation(rows)
    print("All figures generated.")


if __name__ == "__main__":
    main()
