"""
路径对比可视化脚本
在 6 张典型真实地图上，分别运行 A* 和改进 A*，并排展示路径对比
作者：Manus AI | 2026-03-18
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import random

# 安装并设置中文字体
import subprocess
subprocess.run(['fc-cache', '-fv'], capture_output=True)
plt.rcParams['font.family'] = ['Noto Sans CJK SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, '/home/ubuntu/research_project/科研论文/code')
sys.path.insert(0, '/home/ubuntu/research_project')

from planners.algorithms import astar_search, improved_astar_search

# ── 地图加载 ──────────────────────────────────────────────────────────────────
def load_map(map_path):
    """加载 Moving AI .map 格式地图"""
    with open(map_path, 'r') as f:
        lines = f.readlines()
    # 跳过 header
    data_start = 0
    height, width = 0, 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('height'):
            height = int(line.split()[1])
        elif line.startswith('width'):
            width = int(line.split()[1])
        elif line == 'map':
            data_start = i + 1
            break
    grid = np.zeros((height, width), dtype=np.int8)
    for r, line in enumerate(lines[data_start:data_start + height]):
        for c, ch in enumerate(line.rstrip('\n')):
            if ch in ('@', 'O', 'T', 'W'):
                grid[r, c] = 1
    return grid

def find_valid_pair(grid, seed=42, max_tries=500):
    """在地图上随机找一对距离适中的可达起终点"""
    rng = random.Random(seed)
    free = list(zip(*np.where(grid == 0)))
    h, w = grid.shape
    min_dist = max(h, w) * 0.3
    for _ in range(max_tries):
        s = rng.choice(free)
        g = rng.choice(free)
        dist = abs(s[0]-g[0]) + abs(s[1]-g[1])
        if dist >= min_dist:
            return s, g
    # fallback
    return free[0], free[-1]

# ── 绘图函数 ──────────────────────────────────────────────────────────────────
def draw_map_with_paths(ax, grid, path_a, path_b, title, label_a='A*', label_b='改进 A*'):
    """在一个 axes 上绘制地图 + 两条路径"""
    h, w = grid.shape
    
    # 地图背景：白色可通行，深灰障碍
    img = np.ones((h, w, 3))
    img[grid == 1] = [0.2, 0.2, 0.2]   # 障碍：深灰
    img[grid == 0] = [0.97, 0.97, 0.95] # 可通行：米白
    ax.imshow(img, origin='upper', interpolation='nearest')
    
    # 绘制 A* 路径（蓝色，较细）
    if path_a and len(path_a) > 1:
        ys_a = [p[0] for p in path_a]
        xs_a = [p[1] for p in path_a]
        ax.plot(xs_a, ys_a, color='#2196F3', linewidth=1.5, alpha=0.85,
                label=label_a, zorder=3)
    
    # 绘制改进 A* 路径（橙红色，较粗）
    if path_b and len(path_b) > 1:
        ys_b = [p[0] for p in path_b]
        xs_b = [p[1] for p in path_b]
        ax.plot(xs_b, ys_b, color='#FF5722', linewidth=2.0, alpha=0.90,
                label=label_b, zorder=4)
    
    # 起终点标记
    if path_a:
        s, g = path_a[0], path_a[-1]
        ax.scatter([s[1]], [s[0]], c='#4CAF50', s=80, zorder=5, marker='o', edgecolors='white', linewidths=0.8)
        ax.scatter([g[1]], [g[0]], c='#F44336', s=80, zorder=5, marker='*', edgecolors='white', linewidths=0.8)
    
    ax.set_title(title, fontsize=9, fontweight='bold', pad=4)
    ax.axis('off')

# ── 主程序 ────────────────────────────────────────────────────────────────────
MAP_CONFIGS = [
    # (地图路径, 显示名称, 种子)
    ('data/benchmark_maps/dao-map/arena.map',           'DAO: arena',         42),
    ('data/benchmark_maps/dao-map/brc000d.map',         'DAO: brc000d',       77),
    ('data/benchmark_maps/street-map/Berlin_0_256.map', 'Street: Berlin_256', 42),
    ('data/benchmark_maps/street-map/Berlin_1_256.map', 'Street: Berlin_1',   88),
    ('data/benchmark_maps/wc3-map/battleground.map',    'WC3: battleground',  42),
    ('data/benchmark_maps/wc3-map/bootybay.map',        'WC3: bootybay',      55),
]

BASE = '/home/ubuntu/research_project'

fig, axes = plt.subplots(3, 4, figsize=(20, 15))
fig.patch.set_facecolor('#1a1a2e')

# 大标题
fig.suptitle('Path Planning Comparison: Standard A*  vs  Improved A*\n'
             'Blue = Standard A*  |  Orange-Red = Improved A*  |  Green dot = Start  |  Red star = Goal',
             fontsize=13, color='white', fontweight='bold', y=0.98)

stats = []

for idx, (map_rel, name, seed) in enumerate(MAP_CONFIGS):
    map_path = os.path.join(BASE, map_rel)
    if not os.path.exists(map_path):
        print(f'[WARN] 地图不存在: {map_path}')
        continue
    
    grid = load_map(map_path)
    start, goal = find_valid_pair(grid, seed=seed)
    
    # 运行两个算法
    res_a = astar_search(grid, start, goal)
    res_b = improved_astar_search(grid, start, goal)
    
    path_a = res_a.get('path', []) if res_a.get('success') else []
    path_b = res_b.get('path', []) if res_b.get('success') else []
    
    rt_a  = res_a.get('runtime_ms', 0)
    rt_b  = res_b.get('runtime_ms', 0)
    pl_a  = res_a.get('path_length', 0)
    pl_b  = res_b.get('path_length', 0)
    tc_a  = res_a.get('turn_count', 0)
    tc_b  = res_b.get('turn_count', 0)
    
    stats.append((name, rt_a, rt_b, pl_a, pl_b, tc_a, tc_b))
    
    # 左图：A*，右图：改进 A*
    col_a = idx * 2 % 4
    col_b = col_a + 1
    row   = idx // 2
    
    ax_a = axes[row][col_a]
    ax_b = axes[row][col_b]
    
    title_a = f'{name}\nA*  |  {rt_a:.2f}ms  |  len={pl_a:.1f}  |  turns={tc_a}'
    title_b = f'{name}\nImproved A*  |  {rt_b:.2f}ms  |  len={pl_b:.1f}  |  turns={tc_b}'
    
    draw_map_with_paths(ax_a, grid, path_a, [], title_a, label_a='A*')
    draw_map_with_paths(ax_b, grid, [], path_b, title_b, label_b='Improved A*')
    
    # 标题颜色
    ax_a.set_title(title_a, fontsize=8, color='#90CAF9', pad=3)
    ax_b.set_title(title_b, fontsize=8, color='#FFAB91', pad=3)
    
    print(f'[{name}] A*: {rt_a:.2f}ms, len={pl_a:.1f}, tc={tc_a}  |  改进: {rt_b:.2f}ms, len={pl_b:.1f}, tc={tc_b}')

# 背景色
for ax in axes.flat:
    ax.set_facecolor('#1a1a2e')

plt.tight_layout(rect=[0, 0, 1, 0.96])
out_path = '/home/ubuntu/research_project/figures/path_comparison_6maps_Manus.png'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
print(f'\n路径对比图已保存: {out_path}')

# 打印汇总统计
print('\n=== 汇总 ===')
print(f'{"地图":<25} {"A*时间":>8} {"改进时间":>8} {"时间比":>7} {"A*长度":>8} {"改进长度":>8} {"A*转弯":>7} {"改进转弯":>8}')
for name, rt_a, rt_b, pl_a, pl_b, tc_a, tc_b in stats:
    ratio = rt_b/rt_a if rt_a > 0 else 0
    print(f'{name:<25} {rt_a:>8.2f} {rt_b:>8.2f} {ratio:>7.3f}x {pl_a:>8.1f} {pl_b:>8.1f} {tc_a:>7} {tc_b:>8}')
