"""
消融实验（Ablation Study）脚本
在 Moving AI 真实地图上，逐一拆除改进A*的四个创新点，验证每个模块的贡献。

消融变体设计（严格按照 rules.md §6 要求）：
  - Full:         完整改进A*（Octile + 自适应权重 + JPS-like + 两阶段平滑）
  - w/o Adaptive: 去掉自适应权重（固定 alpha=1.0）
  - w/o JPS:      去掉 JPS-like 跳跃策略（回退到 8-邻域逐步搜索）
  - w/o Smooth:   去掉两阶段平滑（不做 simplify + smooth_corners）
  - w/o All:      仅保留 Octile 启发（等价于传统A*，作为下界对照）

数据来源：Moving AI Benchmark 真实地图（8room / 16room / 32room / maze）
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import heapq
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
from typing import Dict, List, Tuple

from planners.core import (
    Point, adaptive_alpha, neighbors8, obstacle_ratio,
    octile_distance, path_length, reconstruct_path,
    simplify_path, smooth_corners, turn_count,
    random_grid, sample_start_goal
)

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

MAPS_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data', 'benchmark_maps')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
FIGURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


# ── 消融变体实现 ──────────────────────────────────────────────────────────────

def _jump_like_neighbors(grid, node, max_jump=3):
    x, y = node
    h, w = grid.shape
    for dx, dy in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
        for step in range(1, max_jump + 1):
            nx, ny = x + dx*step, y + dy*step
            if not (0 <= nx < h and 0 <= ny < w): break
            if grid[nx, ny] == 1: break
            yield (nx, ny), step * (2**0.5 if dx!=0 and dy!=0 else 1.0)


def _astar_core(grid, start, goal, weight, use_jump):
    t0 = time.perf_counter()
    open_heap = [(0.0, start)]
    came_from = {}
    g = {start: 0.0}
    closed = set()
    expanded = 0
    while open_heap:
        _, cur = heapq.heappop(open_heap)
        if cur in closed: continue
        closed.add(cur); expanded += 1
        if cur == goal:
            path = reconstruct_path(came_from, cur)
            return True, path, expanded, (time.perf_counter()-t0)*1000
        nbrs = _jump_like_neighbors(grid, cur) if use_jump else neighbors8(grid, cur)
        for nb, cost in nbrs:
            if nb in closed: continue
            tg = g[cur] + cost
            if tg < g.get(nb, float('inf')):
                came_from[nb] = cur
                g[nb] = tg
                f = tg + weight * octile_distance(nb, goal)
                heapq.heappush(open_heap, (f, nb))
    return False, [], expanded, (time.perf_counter()-t0)*1000


def ablation_variants(grid, start, goal):
    """返回所有消融变体的结果字典"""
    obs = obstacle_ratio(grid)
    alpha = adaptive_alpha(obs)
    results = {}

    # ① Full: 完整改进A*
    ok, path, nodes, rt = _astar_core(grid, start, goal, alpha, use_jump=True)
    if ok:
        p1 = simplify_path(path, grid)
        p2 = smooth_corners(p1)
        results['Full (Ours)'] = {'success': True, 'path': p2,
            'path_length': path_length(p2), 'turn_count': turn_count(p2),
            'expanded_nodes': nodes, 'runtime_ms': rt}
    else:
        results['Full (Ours)'] = {'success': False}

    # ② w/o Adaptive: 固定 alpha=1.0，其余不变
    ok, path, nodes, rt = _astar_core(grid, start, goal, 1.0, use_jump=True)
    if ok:
        p1 = simplify_path(path, grid)
        p2 = smooth_corners(p1)
        results['w/o Adaptive'] = {'success': True, 'path': p2,
            'path_length': path_length(p2), 'turn_count': turn_count(p2),
            'expanded_nodes': nodes, 'runtime_ms': rt}
    else:
        results['w/o Adaptive'] = {'success': False}

    # ③ w/o JPS: 去掉跳跃，保留自适应权重和平滑
    ok, path, nodes, rt = _astar_core(grid, start, goal, alpha, use_jump=False)
    if ok:
        p1 = simplify_path(path, grid)
        p2 = smooth_corners(p1)
        results['w/o JPS-like'] = {'success': True, 'path': p2,
            'path_length': path_length(p2), 'turn_count': turn_count(p2),
            'expanded_nodes': nodes, 'runtime_ms': rt}
    else:
        results['w/o JPS-like'] = {'success': False}

    # ④ w/o Smooth: 去掉两阶段平滑，保留自适应权重和JPS
    ok, path, nodes, rt = _astar_core(grid, start, goal, alpha, use_jump=True)
    if ok:
        results['w/o Smooth'] = {'success': True, 'path': path,
            'path_length': path_length(path), 'turn_count': turn_count(path),
            'expanded_nodes': nodes, 'runtime_ms': rt}
    else:
        results['w/o Smooth'] = {'success': False}

    # ⑤ w/o All: 仅 Octile 启发，alpha=1.0，无跳跃，无平滑（= 传统A*）
    ok, path, nodes, rt = _astar_core(grid, start, goal, 1.0, use_jump=False)
    if ok:
        results['Traditional A*'] = {'success': True, 'path': path,
            'path_length': path_length(path), 'turn_count': turn_count(path),
            'expanded_nodes': nodes, 'runtime_ms': rt}
    else:
        results['Traditional A*'] = {'success': False}

    return results


# ── 地图解析 ──────────────────────────────────────────────────────────────────

def parse_movingai_map(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    height, width, map_start = 0, 0, 0
    for i, line in enumerate(lines):
        l = line.strip()
        if l.startswith('height'): height = int(l.split()[1])
        elif l.startswith('width'): width = int(l.split()[1])
        elif l == 'map': map_start = i + 1; break
    grid = np.zeros((height, width), dtype=np.int8)
    for r, line in enumerate(lines[map_start:map_start+height]):
        for c, ch in enumerate(line.rstrip('\n')):
            if c >= width: break
            grid[r, c] = 0 if ch in ('.', 'G', 'S') else 1
    return grid


def crop_submap(grid, size, rng):
    h, w = grid.shape
    if h < size or w < size: return None
    for _ in range(50):
        r = int(rng.integers(0, h-size+1))
        c = int(rng.integers(0, w-size+1))
        sub = grid[r:r+size, c:c+size]
        if np.mean(sub==0) >= 0.2:
            return sub.copy()
    return None


# ── 主实验循环 ────────────────────────────────────────────────────────────────

def run_ablation(map_files, crop_size=100, repeats=30, seed=42):
    rng = np.random.default_rng(seed)
    all_rows = []
    variant_names = ['Full (Ours)', 'w/o Adaptive', 'w/o JPS-like', 'w/o Smooth', 'Traditional A*']

    for map_file in map_files:
        map_name = os.path.basename(map_file).replace('.map', '')
        print(f"\n[消融] {map_name}")
        grid_full = parse_movingai_map(map_file)

        accum = {v: {'runtime': [], 'path_len': [], 'turns': [], 'nodes': []}
                 for v in variant_names}
        valid, attempt = 0, 0

        while valid < repeats and attempt < repeats * 20:
            attempt += 1
            sub = crop_submap(grid_full, crop_size, rng)
            if sub is None: continue
            sg = sample_start_goal(sub, rng)
            if sg is None: continue
            start, goal = sg

            res = ablation_variants(sub, start, goal)
            if not all(res[v]['success'] for v in variant_names): continue

            for v in variant_names:
                r = res[v]
                accum[v]['runtime'].append(r['runtime_ms'])
                accum[v]['path_len'].append(r['path_length'])
                accum[v]['turns'].append(r['turn_count'])
                accum[v]['nodes'].append(r['expanded_nodes'])
            valid += 1

        print(f"  有效样本: {valid}/{repeats}")
        for v in variant_names:
            d = accum[v]
            if not d['runtime']: continue
            row = {
                'map': map_name, 'variant': v, 'n': len(d['runtime']),
                'runtime_mean': np.mean(d['runtime']), 'runtime_std': np.std(d['runtime']),
                'path_len_mean': np.mean(d['path_len']), 'path_len_std': np.std(d['path_len']),
                'turns_mean': np.mean(d['turns']), 'turns_std': np.std(d['turns']),
                'nodes_mean': np.mean(d['nodes']),
            }
            all_rows.append(row)
            print(f"  {v:20s}: time={row['runtime_mean']:.3f}ms  "
                  f"len={row['path_len_mean']:.2f}  "
                  f"turns={row['turns_mean']:.1f}  "
                  f"nodes={row['nodes_mean']:.0f}")
    return all_rows


# ── 绘图 ──────────────────────────────────────────────────────────────────────

def plot_ablation(rows):
    import pandas as pd
    df = pd.DataFrame(rows)
    maps = df['map'].unique()
    variants = ['Traditional A*', 'w/o Smooth', 'w/o JPS-like', 'w/o Adaptive', 'Full (Ours)']
    colors   = ['#7f8c8d',        '#95a5a6',    '#3498db',       '#f39c12',       '#e74c3c']

    metrics = [
        ('runtime_mean', 'runtime_std', 'Planning Time (ms)', 'Runtime'),
        ('path_len_mean', 'path_len_std', 'Path Length (grid units)', 'Path Length'),
        ('turns_mean', 'turns_std', 'Turn Count', 'Turn Count'),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    x = np.arange(len(maps))
    width = 0.15

    for ax, (metric, std_col, ylabel, title) in zip(axes, metrics):
        for i, (v, c) in enumerate(zip(variants, colors)):
            vals, stds = [], []
            for m in maps:
                row = df[(df['map']==m) & (df['variant']==v)]
                vals.append(row[metric].values[0] if len(row)>0 else 0)
                stds.append(row[std_col].values[0] if len(row)>0 else 0)
            ax.bar(x + i*width, vals, width, label=v, color=c, alpha=0.85,
                   edgecolor='white', linewidth=0.5)
            ax.errorbar(x + i*width, vals, yerr=stds, fmt='none',
                        color='black', capsize=2.5, linewidth=0.8)
        ax.set_xlabel('Map', fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticks(x + width*2)
        ax.set_xticklabels([m.replace('_000','') for m in maps], fontsize=9)
        ax.legend(fontsize=7.5)
        ax.grid(axis='y', alpha=0.3)

    plt.suptitle(
        'Ablation Study — Contribution of Each Module\n'
        '(Moving AI Real-World Benchmark Maps, 100x100 submap, n=30 per map)',
        fontsize=13, fontweight='bold', y=1.02
    )
    plt.tight_layout()
    os.makedirs(FIGURES_DIR, exist_ok=True)
    out = os.path.join(FIGURES_DIR, 'ablation_study_real_maps.png')
    plt.savefig(out, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"\n[OK] 消融实验图已保存: {out}")
    return out


def plot_ablation_improvement(rows):
    """以传统A*为基准，绘制各变体的相对提升率（%）"""
    import pandas as pd
    df = pd.DataFrame(rows)
    maps = df['map'].unique()
    variants = ['w/o Smooth', 'w/o JPS-like', 'w/o Adaptive', 'Full (Ours)']
    colors   = ['#95a5a6',    '#3498db',       '#f39c12',       '#e74c3c']
    metrics  = [
        ('runtime_mean', 'Runtime Reduction (%)'),
        ('turns_mean',   'Turn Count Reduction (%)'),
        ('path_len_mean','Path Length Reduction (%)'),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    x = np.arange(len(maps))
    width = 0.18

    for ax, (metric, ylabel) in zip(axes, metrics):
        for i, (v, c) in enumerate(zip(variants, colors)):
            improvements = []
            for m in maps:
                base = df[(df['map']==m) & (df['variant']=='Traditional A*')][metric]
                curr = df[(df['map']==m) & (df['variant']==v)][metric]
                if len(base)>0 and len(curr)>0 and base.values[0]>0:
                    imp = (base.values[0] - curr.values[0]) / base.values[0] * 100
                else:
                    imp = 0
                improvements.append(imp)
            bars = ax.bar(x + i*width, improvements, width, label=v, color=c,
                          alpha=0.85, edgecolor='white', linewidth=0.5)
            # 在柱子上标注数值
            for bar, val in zip(bars, improvements):
                if abs(val) > 0.5:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                            f'{val:.1f}%', ha='center', va='bottom', fontsize=7)

        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
        ax.set_xlabel('Map', fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(ylabel.replace(' (%)', ''), fontsize=12, fontweight='bold')
        ax.set_xticks(x + width*1.5)
        ax.set_xticklabels([m.replace('_000','') for m in maps], fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

    plt.suptitle(
        'Ablation Study — Relative Improvement over Traditional A* (%)\n'
        '(Positive = better than Traditional A*)',
        fontsize=13, fontweight='bold', y=1.02
    )
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, 'ablation_improvement_rate.png')
    plt.savefig(out, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"[OK] 消融提升率图已保存: {out}")
    return out


def main():
    map_files = [f for f in [
        os.path.join(MAPS_DIR, '8room_000.map'),
        os.path.join(MAPS_DIR, '16room_000.map'),
        os.path.join(MAPS_DIR, '32room_000.map'),
        os.path.join(MAPS_DIR, 'maze512-1-0.map'),
    ] if os.path.exists(f)]
    print(f"找到 {len(map_files)} 个真实地图文件")

    rows = run_ablation(map_files, crop_size=100, repeats=30, seed=42)

    # 保存 CSV
    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_path = os.path.join(RESULTS_DIR, 'ablation_real_maps.csv')
    if rows:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n[OK] 消融数据已保存: {csv_path}")

    if rows:
        plot_ablation(rows)
        plot_ablation_improvement(rows)

    print("\n消融实验全部完成！")


if __name__ == "__main__":
    main()
