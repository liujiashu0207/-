"""
Generate Figure 5: expanded nodes vs obstacle ratio.
Shows how the adaptive weight mechanism works across different obstacle densities.

Usage:
    python code/visualize/plot_nodes_vs_obstacle.py
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

ALGO_STYLES = {
    "astar":          {"color": "#3498db", "marker": "o",  "label": "传统 A*",         "ls": "-"},
    "weighted_astar": {"color": "#e67e22", "marker": "s",  "label": "加权 A*(α=1.2)",  "ls": "--"},
    "improved_astar": {"color": "#e74c3c", "marker": "D",  "label": "改进 A*(本文)",   "ls": "-"},
    "dijkstra":       {"color": "#95a5a6", "marker": "^",  "label": "Dijkstra",        "ls": ":"},
}


def load_per_map_data():
    rows = []
    with SUMMARY_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["map_name"].startswith("GLOBAL"):
                continue
            r["obstacle_ratio"] = float(r["obstacle_ratio"])
            r["expanded_nodes_mean"] = float(r["expanded_nodes_mean"])
            rows.append(r)
    return rows


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_per_map_data()

    per_algo = defaultdict(list)
    for r in rows:
        algo = r["algorithm"]
        if algo in ALGO_STYLES:
            per_algo[algo].append((r["obstacle_ratio"], r["expanded_nodes_mean"]))

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(8, 8),
                                          gridspec_kw={"height_ratios": [1, 1.2]})

    for algo, style in ALGO_STYLES.items():
        points = sorted(per_algo[algo], key=lambda p: p[0])
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax_top.plot(xs, ys, color=style["color"], marker=style["marker"],
                    linestyle=style["ls"], linewidth=1.5, markersize=5,
                    label=style["label"], alpha=0.85)

    ax_top.set_xlabel("地图障碍率")
    ax_top.set_ylabel("平均扩展节点数")
    ax_top.set_title("(a) 全部算法（含 Dijkstra）")
    ax_top.legend(loc="upper left", framealpha=0.9)
    ax_top.grid(alpha=0.3, linestyle="--")
    ax_top.spines["top"].set_visible(False)
    ax_top.spines["right"].set_visible(False)

    focus_algos = ["astar", "weighted_astar", "improved_astar"]
    for algo in focus_algos:
        style = ALGO_STYLES[algo]
        points = sorted(per_algo[algo], key=lambda p: p[0])
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax_bot.plot(xs, ys, color=style["color"], marker=style["marker"],
                    linestyle=style["ls"], linewidth=2, markersize=6,
                    label=style["label"], alpha=0.9)

    ax_bot.annotate("α ≈ 1.8\n(低障碍率，节点数少)",
                    xy=(0.055, 7.1), fontsize=9, color="#e74c3c", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffeaa7", alpha=0.85),
                    ha="center")
    ax_bot.annotate("α ≈ 1.0\n(高障碍率，近似标准A*)",
                    xy=(0.40, 8.3), fontsize=9, color="#e74c3c", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#fab1a0", alpha=0.85),
                    ha="center")

    ax_bot.axvline(x=0.10, color="#bdc3c7", linestyle=":", alpha=0.6)
    ax_bot.axvline(x=0.35, color="#bdc3c7", linestyle=":", alpha=0.6)
    ax_bot.axhspan(6.0, 6.5, alpha=0.08, color="#27ae60")
    ax_bot.axhspan(7.5, 8.2, alpha=0.08, color="#e74c3c")

    ax_bot.set_xlabel("地图障碍率 (obstacle ratio)")
    ax_bot.set_ylabel("平均扩展节点数")
    ax_bot.set_title("(b) A* 系列放大对比（不含 Dijkstra）")
    ax_bot.legend(loc="upper left", framealpha=0.9)
    ax_bot.grid(alpha=0.3, linestyle="--")
    ax_bot.spines["top"].set_visible(False)
    ax_bot.spines["right"].set_visible(False)

    fig.suptitle("图 5  扩展节点数随障碍率的变化趋势", fontsize=13, y=1.01)
    fig.tight_layout()
    out = FIGURES_DIR / "fig5_nodes_vs_obstacle_v3.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
