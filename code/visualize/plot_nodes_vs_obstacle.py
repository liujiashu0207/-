import csv
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'results' / 'exp_fix15_v3_all_summary.csv'
OUT = ROOT / 'figures' / 'fig5_nodes_vs_obstacle_v3.png'
OUT.parent.mkdir(exist_ok=True)

plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150

COLORS = {'dijkstra':'#7b3294','astar':'#2166ac','weighted_astar':'#4dac26','improved_astar':'#d6604d'}
LABELS = {'dijkstra':'Dijkstra','astar':'A* (baseline)','weighted_astar':'Weighted A* (a=1.2)','improved_astar':'Improved A* (ours)'}
ALGOS = ['dijkstra','astar','weighted_astar','improved_astar']

rows = list(csv.DictReader(open(DATA, encoding='utf-8')))
data = defaultdict(list)
for r in rows:
    a = r['algorithm']
    if a not in ALGOS:
        continue
    data[a].append((float(r['obstacle_ratio']), float(r['expanded_nodes_mean'])))

fig, ax = plt.subplots(figsize=(9, 5.5))
for algo in ALGOS:
    pts = sorted(data[algo])
    ax.plot([p[0] for p in pts], [p[1] for p in pts], 'o-',
            color=COLORS[algo], label=LABELS[algo], markersize=5, linewidth=1.8, alpha=0.85)

ymax = ax.get_ylim()[1]
ax.text(0.08, ymax * 0.25, 'a ~ 1.8\n(low obstacle)', fontsize=9, color='#d6604d', fontweight='bold')
ax.text(0.35, ymax * 0.25, 'a ~ 1.0\n(high obstacle)', fontsize=9, color='#d6604d', fontweight='bold')

ax.set_xlabel('Obstacle Ratio', fontsize=11)
ax.set_ylabel('Expanded Nodes (mean per map)', fontsize=11)
ax.set_title('Figure 5: Expanded Nodes vs Obstacle Ratio\n(15 maps, strict .scen benchmark)', fontsize=11)
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3, linestyle='--')
fig.tight_layout()
fig.savefig(OUT, bbox_inches='tight')
plt.close(fig)
print(f'[OK] fig5 saved: {OUT}')
