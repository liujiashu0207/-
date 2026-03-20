#!/usr/bin/env python3
"""
Round10 Manus 负责的4项修改：
1. 1.2节各方向补充中文文献引用 [7]-[12]
2. 4.7节补充 Wilcoxon + BH-FDR 统计检验方法描述
3. 英文摘要 LaTeX 公式改文字描述
4. 5.1节补充图4引用
"""

path = "docs/投稿主稿_v1.md"
content = open(path, encoding="utf-8").read()

# ── 1. 1.2节各方向补充中文文献引用 ────────────────────────────────

# 启发函数方向：末尾加 [7][8]
old1 = "在实时性要求较高的场景中得到广泛应用[6]。"
new1 = "在实时性要求较高的场景中得到广泛应用[6]。沈克宇等[7]在此基础上结合障碍物膨胀策略进一步提升了搜索效率；尧尹柱等[8]提出自适应方向权重机制，在小规模栅格地图上取得了显著加速效果。"
content = content.replace(old1, new1)

# JPS方向：末尾加 [9]
old2 = "然而，JPS 在非均匀代价地图和复杂障碍分布下的性能提升有限。"
new2 = "然而，JPS 在非均匀代价地图和复杂障碍分布下的性能提升有限。任祥瑞等[9]将改进 JPS 与动态窗口法（DWA）融合，在多机器人路径规划场景中取得了良好效果。"
content = content.replace(old2, new2)

# 路径平滑方向：末尾加 [10][11]
old3 = "样条曲线拟合以及基于物理约束的轨迹优化等。"
new3 = "样条曲线拟合以及基于物理约束的轨迹优化等。冯志乾等[10]和高建京等[11]分别将改进 A* 与 DWA 融合，在平滑路径的同时兼顾了动态避障能力。"
content = content.replace(old3, new3)

# 自适应策略方向：末尾加 [12]
old4 = "可以在不同环境下取得更为均衡的性能表现。"
new4 = "可以在不同环境下取得更为均衡的性能表现。段孟滨等[12]在差动机器人路径跟踪控制中引入改进 A* 与多参考点 MPC，进一步验证了自适应策略在复杂场景中的有效性。"
content = content.replace(old4, new4)

# ── 2. 4.7节补充统计检验方法描述 ──────────────────────────────────
old5 = ("### 4.7 统计分析方法\n"
        "- 所有指标报告均值 ± 标准差（标准差基于 15 张地图的跨图波动计算）\n"
        "- 共 15 张地图 × 30 次 = 450 组有效测试；含 4 种算法共 1800 条记录，加消融组共 2700 条")
new5 = ("### 4.7 统计分析方法\n"
        "所有指标报告均值 ± 标准差，标准差基于 15 张地图的跨图波动计算。共 15 张地图 × 30 次 = 450 组有效测试；含 4 种算法共 1800 条记录，加消融组共 2700 条。\n\n"
        "对改进 A* 与传统 A* 在运行时间、路径长度、转弯次数三项指标上的差异，采用 Wilcoxon 符号秩检验（Wilcoxon signed-rank test）进行统计显著性分析，以 15 张地图的均值作为配对样本。针对三项指标的多重比较，采用 Benjamini-Hochberg 假发现率（BH-FDR）方法进行校正，控制假发现率 $q < 0.05$。检验结果见第 5.2.3 节。")
content = content.replace(old5, new5)

# ── 3. 英文摘要 LaTeX 公式改文字描述 ──────────────────────────────
old6 = ("The adaptive weight is computed as $\\alpha = \\text{clip}(|\\ln(\\text{obstacle\\_ratio})|, 1.0, 1.8)$ "
        "for engineering acceleration; strict path optimality is not guaranteed ($\\alpha$-optimal when $\\alpha > 1$).")
new6 = ("The adaptive weight is computed via a log-mapping of the map obstacle ratio, clipped to the range [1.0, 1.8], "
        "for engineering acceleration; strict path optimality is not guaranteed (the algorithm is alpha-optimal when alpha > 1).")
content = content.replace(old6, new6)

# ── 4. 5.1节补充图4引用 ────────────────────────────────────────────
# 在5.1节总览表格后补充图4引用
old7 = ("| 消融：无路径平滑 | 0.04296 ± 0.00706 | 6.1624 ± 0.2488 | 0.9911 ± 0.2556 | 7.54 ± 1.30 |\n\n"
        "### 5.2 与传统算法的对比分析")
new7 = ("| 消融：无路径平滑 | 0.04296 ± 0.00706 | 6.1624 ± 0.2488 | 0.9911 ± 0.2556 | 7.54 ± 1.30 |\n\n"
        "图 4 展示了 6 张代表性地图上各算法的路径可视化对比，直观呈现了路径平滑策略对路径形态的改善效果（见图 4）。\n\n"
        "### 5.2 与传统算法的对比分析")
content = content.replace(old7, new7)

# ── 写回并验证 ────────────────────────────────────────────────────
open(path, "w", encoding="utf-8").write(content)
print("写入完成，验证：")

c = open(path, encoding="utf-8").read()
checks = [
    ("[7]引用-启发函数方向", "沈克宇等[7]" in c),
    ("[8]引用-启发函数方向", "尧尹柱等[8]" in c),
    ("[9]引用-JPS方向",     "任祥瑞等[9]" in c),
    ("[10]引用-平滑方向",   "冯志乾等[10]" in c),
    ("[11]引用-平滑方向",   "高建京等[11]" in c),
    ("[12]引用-自适应方向", "段孟滨等[12]" in c),
    ("4.7节Wilcoxon描述",   "Wilcoxon 符号秩检验" in c),
    ("4.7节BH-FDR描述",     "BH-FDR" in c),
    ("英文摘要公式改文字",  "log-mapping" in c),
    ("英文摘要无LaTeX公式", "clip(|\\ln" not in c),
    ("图4引用",             "见图 4" in c),
]
all_pass = True
for name, result in checks:
    status = "✅" if result else "❌"
    if not result:
        all_pass = False
    print(f"  {status} {name}")

print(f"\n{'全部通过' if all_pass else '存在失败项，请检查'}")
