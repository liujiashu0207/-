"""
论文核心对比图生成脚本 v1
Manus 2026-03-19
生成3张论文图：
  1. 运行时间对比图（按地图类型分组，4种算法）
  2. 转弯次数对比图（按地图类型分组，4种算法）
  3. 消融实验对比图（4种配置 × 3个指标）
数据来源：results/exp_fix15_v3_all_summary.csv（唯一权威数据集）
输出路径：figures/
"""
import sys
from pathlib import Path
import csv
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── 路径锚点（相对于本文件，不含绝对路径）────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]   # research_project/
DATA_PATH = ROOT / "results" / "exp_fix15_v3_all_summary.csv"
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── 字体设置（不依赖系统 CJK 字体）────────────────────────────────────────
plt.rcParams["font.family"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 150

# ── 配色方案（学术风格，色盲友好）──────────────────────────────────────────
COLORS = {
    "astar":           "#2166ac",   # 蓝
    "improved_astar":  "#d6604d",   # 红
    "weighted_astar":  "#4dac26",   # 绿
    "dijkstra":        "#7b3294",   # 紫
    "ablation_no_adaptive":  "#f4a582",  # 浅橙
    "ablation_no_smoothing": "#92c5de",  # 浅蓝
}

ALGO_LABELS = {
    "dijkstra":              "Dijkstra",
    "astar":                 "A* (baseline)",
    "weighted_astar":        "Weighted A* (α=1.5)",
    "improved_astar":        "Improved A* (ours)",
    "ablation_no_adaptive":  "Ablation: no adaptive α",
    "ablation_no_smoothing": "Ablation: no smoothing",
}

MAP_TYPE_LABELS = {
    "dao":    "DAO\n(game maps)",
    "street": "Street\n(city maps)",
    "wc3":    "WC3\n(Warcraft maps)",
    "all":    "Overall\n(15 maps)",
}

# ── 数据加载 ────────────────────────────────────────────────────────────────
def load_data():
    rows = list(csv.DictReader(open(DATA_PATH, encoding="utf-8")))
    data = defaultdict(lambda: defaultdict(list))
    for r in rows:
        mtype = r["map_type"]
        algo = r["algorithm"]
        data[mtype][algo].append({
            "rt":  float(r["runtime_ms_mean"]),
            "pl":  float(r["path_length_mean"]),
            "tc":  float(r["turn_count_mean"]),
            "en":  float(r["expanded_nodes_mean"]),
        })
    return data

def mean(lst, key):
    return sum(x[key] for x in lst) / len(lst) if lst else 0.0

def get_by_type_and_algo(data, mtypes, algos, key):
    """返回 {mtype: {algo: mean_value}} 结构"""
    result = {}
    for mt in mtypes:
        result[mt] = {}
        for algo in algos:
            vals = data.get(mt, {}).get(algo, [])
            result[mt][algo] = mean(vals, key)
    # 全局均值
    result["all"] = {}
    for algo in algos:
        all_vals = []
        for mt in mtypes:
            all_vals.extend(data.get(mt, {}).get(algo, []))
        result["all"][algo] = mean(all_vals, key)
    return result


# ── 图1：运行时间对比（4种主算法，按地图类型分组）──────────────────────────
def plot_runtime(data):
    mtypes = ["dao", "street", "wc3", "all"]
    algos  = ["dijkstra", "astar", "weighted_astar", "improved_astar"]
    rt_data = get_by_type_and_algo(data, ["dao", "street", "wc3"], algos, "rt")

    x = np.arange(len(mtypes))
    width = 0.18
    offsets = [-1.5, -0.5, 0.5, 1.5]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, algo in enumerate(algos):
        vals = [rt_data[mt][algo] for mt in mtypes]
        bars = ax.bar(x + offsets[i] * width, vals, width,
                      color=COLORS[algo], label=ALGO_LABELS[algo],
                      edgecolor="white", linewidth=0.5)
        # 在柱顶标注数值
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.0008,
                        f"{v:.4f}", ha="center", va="bottom",
                        fontsize=6.5, rotation=45)

    ax.set_xticks(x)
    ax.set_xticklabels([MAP_TYPE_LABELS[mt] for mt in mtypes], fontsize=10)
    ax.set_ylabel("Average Runtime (ms)", fontsize=11)
    ax.set_title("Figure 1: Runtime Comparison by Map Type\n"
                 "(15 maps × 30 trials, strict .scen benchmark)", fontsize=11)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    ax.set_ylim(0, max(rt_data["all"]["dijkstra"] * 1.25, 0.6))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    # 标注改善幅度
    astar_all = rt_data["all"]["astar"]
    imp_all   = rt_data["all"]["improved_astar"]
    pct = (astar_all - imp_all) / astar_all * 100
    ax.annotate(f"Improved A* vs A*:\n−{pct:.1f}% overall",
                xy=(x[-1] + offsets[3] * width, imp_all),
                xytext=(x[-1] - 0.6, imp_all + 0.05),
                fontsize=8, color=COLORS["improved_astar"],
                arrowprops=dict(arrowstyle="->", color=COLORS["improved_astar"], lw=1.2))

    fig.tight_layout()
    out = FIG_DIR / "fig1_runtime_comparison_v3.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] 图1 已保存：{out}")
    return out


# ── 图2：转弯次数对比（4种主算法，按地图类型分组）──────────────────────────
def plot_turncount(data):
    mtypes = ["dao", "street", "wc3", "all"]
    algos  = ["dijkstra", "astar", "weighted_astar", "improved_astar"]
    tc_data = get_by_type_and_algo(data, ["dao", "street", "wc3"], algos, "tc")

    x = np.arange(len(mtypes))
    width = 0.18
    offsets = [-1.5, -0.5, 0.5, 1.5]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, algo in enumerate(algos):
        vals = [tc_data[mt][algo] for mt in mtypes]
        bars = ax.bar(x + offsets[i] * width, vals, width,
                      color=COLORS[algo], label=ALGO_LABELS[algo],
                      edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            if v > 0.01:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.01,
                        f"{v:.3f}", ha="center", va="bottom",
                        fontsize=7, rotation=45)
            elif v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.01,
                        f"{v:.4f}", ha="center", va="bottom",
                        fontsize=6, rotation=45)

    ax.set_xticks(x)
    ax.set_xticklabels([MAP_TYPE_LABELS[mt] for mt in mtypes], fontsize=10)
    ax.set_ylabel("Average Turn Count", fontsize=11)
    ax.set_title("Figure 2: Turn Count Comparison by Map Type\n"
                 "(15 maps × 30 trials, strict .scen benchmark)", fontsize=11)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    # 标注改善幅度
    astar_all = tc_data["all"]["astar"]
    imp_all   = tc_data["all"]["improved_astar"]
    pct = (astar_all - imp_all) / astar_all * 100
    ax.annotate(f"Improved A* vs A*:\n−{pct:.1f}% overall\n({astar_all:.3f}→{imp_all:.4f})",
                xy=(x[-1] + offsets[3] * width, imp_all + 0.02),
                xytext=(x[-1] - 1.0, astar_all * 0.6),
                fontsize=8, color=COLORS["improved_astar"],
                arrowprops=dict(arrowstyle="->", color=COLORS["improved_astar"], lw=1.2))

    fig.tight_layout()
    out = FIG_DIR / "fig2_turncount_comparison_v3.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] 图2 已保存：{out}")
    return out


# ── 图3：消融实验对比（4种配置 × 3个指标，归一化展示）──────────────────────
def plot_ablation(data):
    """
    4 种配置：传统A*（基线）、无自适应权重、无路径平滑、完整改进A*
    3 个指标：运行时间、路径长度、转弯次数
    每个指标以传统A*为基准归一化（=1.0），便于在同一图中比较
    """
    configs = ["astar", "ablation_no_adaptive", "ablation_no_smoothing", "improved_astar"]
    config_labels = [
        "A* (baseline)",
        "No adaptive α",
        "No smoothing",
        "Improved A* (ours)",
    ]
    config_colors = [
        COLORS["astar"],
        COLORS["ablation_no_adaptive"],
        COLORS["ablation_no_smoothing"],
        COLORS["improved_astar"],
    ]
    metrics = ["rt", "pl", "tc"]
    metric_labels = ["Runtime\n(normalized)", "Path Length\n(normalized)", "Turn Count\n(normalized)"]

    # 计算全局均值
    all_vals = {}
    for cfg in configs:
        all_vals[cfg] = {}
        for mt in ["dao", "street", "wc3"]:
            for r in data.get(mt, {}).get(cfg, []):
                for k in metrics:
                    all_vals[cfg].setdefault(k, []).append(r[k])
        for k in metrics:
            all_vals[cfg][k] = sum(all_vals[cfg].get(k, [0])) / max(len(all_vals[cfg].get(k, [1])), 1)

    # 归一化（以 astar 为基准）
    baseline = all_vals["astar"]
    norm_vals = {}
    for cfg in configs:
        norm_vals[cfg] = {k: all_vals[cfg][k] / baseline[k] for k in metrics}

    x = np.arange(len(metrics))
    width = 0.18
    offsets = [-1.5, -0.5, 0.5, 1.5]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, cfg in enumerate(configs):
        vals = [norm_vals[cfg][k] for k in metrics]
        bars = ax.bar(x + offsets[i] * width, vals, width,
                      color=config_colors[i], label=config_labels[i],
                      edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{v:.3f}", ha="center", va="bottom",
                    fontsize=7.5, fontweight="bold" if cfg == "improved_astar" else "normal")

    # 基准线
    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=1.2, alpha=0.7, label="A* baseline (=1.0)")

    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, fontsize=10)
    ax.set_ylabel("Normalized Value (A* = 1.0)", fontsize=11)
    ax.set_title("Figure 3: Ablation Study\n"
                 "(15 maps × 30 trials, strict .scen benchmark, lower is better)", fontsize=11)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_ylim(0, max(norm_vals["astar"]["tc"] * 1.3, 1.5))

    # 标注关键数值
    imp_rt = norm_vals["improved_astar"]["rt"]
    imp_tc = norm_vals["improved_astar"]["tc"]
    ax.text(x[0] + offsets[3] * width, imp_rt - 0.08,
            f"−{(1-imp_rt)*100:.1f}%", ha="center", fontsize=7.5,
            color=COLORS["improved_astar"], fontweight="bold")
    ax.text(x[2] + offsets[3] * width, imp_tc + 0.04,
            f"−{(1-imp_tc)*100:.1f}%", ha="center", fontsize=7.5,
            color=COLORS["improved_astar"], fontweight="bold")

    fig.tight_layout()
    out = FIG_DIR / "fig3_ablation_study_v3.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] 图3 已保存：{out}")
    return out


if __name__ == "__main__":
    print(f"[INFO] 数据来源：{DATA_PATH}")
    data = load_data()
    f1 = plot_runtime(data)
    f2 = plot_turncount(data)
    f3 = plot_ablation(data)
    print(f"\n[DONE] 3张图已生成：")
    print(f"  {f1}")
    print(f"  {f2}")
    print(f"  {f3}")
