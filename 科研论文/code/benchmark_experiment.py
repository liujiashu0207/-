"""
Moving AI Benchmark 真实地图实验脚本
在 8-room / 16-room / 32-room / maze 等真实地图上对比各算法性能
数据来源：Moving AI Lab (https://movingai.com/benchmarks/)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
from typing import List, Tuple, Dict, Optional

from planners.core import sample_start_goal, path_length, turn_count
from planners.algorithms import (
    dijkstra_search,
    vanilla_astar_search,
    jps_like_search,
    improved_astar_search,
)

# ── 字体设置 ──────────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

MAPS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'benchmark_maps')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
FIGURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


def parse_movingai_map(filepath: str) -> np.ndarray:
    """
    解析 Moving AI .map 格式文件，返回 numpy 栅格矩阵
    0 = 可通行（.），1 = 障碍（@, T, O, W等）
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # 解析头部
    height, width = 0, 0
    map_start = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('height'):
            height = int(line.split()[1])
        elif line.startswith('width'):
            width = int(line.split()[1])
        elif line == 'map':
            map_start = i + 1
            break

    grid = np.zeros((height, width), dtype=np.int8)
    for row_idx, line in enumerate(lines[map_start:map_start + height]):
        for col_idx, ch in enumerate(line.rstrip('\n')):
            if col_idx >= width:
                break
            # '.' 和 'G' 是可通行，其余均为障碍
            if ch in ('.', 'G', 'S'):
                grid[row_idx, col_idx] = 0
            else:
                grid[row_idx, col_idx] = 1

    return grid


def crop_submap(grid: np.ndarray, size: int, rng: np.random.Generator) -> Optional[np.ndarray]:
    """从大地图中随机裁剪一个 size×size 的子图"""
    h, w = grid.shape
    if h < size or w < size:
        return None
    max_row = h - size
    max_col = w - size
    for _ in range(50):
        r = int(rng.integers(0, max_row + 1))
        c = int(rng.integers(0, max_col + 1))
        sub = grid[r:r+size, c:c+size]
        # 确保子图有足够的可通行格子（至少 20%）
        free_ratio = np.mean(sub == 0)
        if free_ratio >= 0.2:
            return sub.copy()
    return None


def run_benchmark(map_files: List[str], crop_size: int = 100,
                  repeats: int = 30, seed: int = 42) -> List[Dict]:
    """在真实地图上运行基准测试"""
    rng = np.random.default_rng(seed)
    results = []

    algos = [
        ("Dijkstra",           dijkstra_search),
        ("Traditional A*",     vanilla_astar_search),
        ("JPS-like",           jps_like_search),
        ("Improved A* (Ours)", improved_astar_search),
    ]

    for map_file in map_files:
        map_name = os.path.basename(map_file).replace('.map', '')
        print(f"\n[地图] {map_name} (裁剪为 {crop_size}x{crop_size})")

        grid_full = parse_movingai_map(map_file)
        obs_ratio = float(np.mean(grid_full == 1))
        print(f"  原始尺寸: {grid_full.shape}, 障碍率: {obs_ratio:.1%}")

        valid_count = 0
        attempt = 0
        map_results = {algo: {'runtime': [], 'path_len': [], 'turns': [], 'nodes': []}
                       for algo, _ in algos}

        while valid_count < repeats and attempt < repeats * 20:
            attempt += 1
            sub = crop_submap(grid_full, crop_size, rng)
            if sub is None:
                continue
            sg = sample_start_goal(sub, rng)
            if sg is None:
                continue
            start, goal = sg

            all_success = True
            run_data = {}
            for algo_name, algo_fn in algos:
                res = algo_fn(sub, start, goal)
                if not res['success']:
                    all_success = False
                    break
                run_data[algo_name] = res

            if not all_success:
                continue

            for algo_name, _ in algos:
                res = run_data[algo_name]
                map_results[algo_name]['runtime'].append(res['runtime_ms'])
                map_results[algo_name]['path_len'].append(res['path_length'])
                map_results[algo_name]['turns'].append(res['turn_count'])
                map_results[algo_name]['nodes'].append(res['expanded_nodes'])

            valid_count += 1

        print(f"  有效样本: {valid_count}/{repeats}")

        for algo_name, _ in algos:
            d = map_results[algo_name]
            if d['runtime']:
                results.append({
                    'map': map_name,
                    'algorithm': algo_name,
                    'n': len(d['runtime']),
                    'runtime_mean': np.mean(d['runtime']),
                    'runtime_std': np.std(d['runtime']),
                    'path_len_mean': np.mean(d['path_len']),
                    'path_len_std': np.std(d['path_len']),
                    'turns_mean': np.mean(d['turns']),
                    'turns_std': np.std(d['turns']),
                    'nodes_mean': np.mean(d['nodes']),
                })
                print(f"  {algo_name:22s}: "
                      f"time={np.mean(d['runtime']):.3f}ms  "
                      f"len={np.mean(d['path_len']):.2f}  "
                      f"turns={np.mean(d['turns']):.1f}  "
                      f"nodes={np.mean(d['nodes']):.0f}")

    return results


def plot_benchmark_results(results: List[Dict]):
    """绘制基准测试结果对比图"""
    import pandas as pd
    df = pd.DataFrame(results)
    maps = df['map'].unique()
    algos = ["Dijkstra", "Traditional A*", "JPS-like", "Improved A* (Ours)"]
    colors = ['#7f8c8d', '#3498db', '#f39c12', '#e74c3c']

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    metrics = [
        ('runtime_mean', 'Planning Time (ms)', 'Runtime'),
        ('path_len_mean', 'Path Length (grid units)', 'Path Length'),
        ('turns_mean', 'Turn Count', 'Turn Count'),
    ]

    x = np.arange(len(maps))
    width = 0.18

    for ax, (metric, ylabel, title) in zip(axes, metrics):
        for i, (algo, color) in enumerate(zip(algos, colors)):
            vals = []
            stds = []
            for m in maps:
                row = df[(df['map'] == m) & (df['algorithm'] == algo)]
                if len(row) > 0:
                    vals.append(row[metric].values[0])
                    std_col = metric.replace('_mean', '_std')
                    stds.append(row[std_col].values[0] if std_col in row.columns else 0)
                else:
                    vals.append(0)
                    stds.append(0)
            bars = ax.bar(x + i * width, vals, width, label=algo, color=color,
                          alpha=0.85, edgecolor='white', linewidth=0.5)
            ax.errorbar(x + i * width, vals, yerr=stds, fmt='none',
                        color='black', capsize=3, linewidth=1)

        ax.set_xlabel('Map', fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([m.replace('_000', '') for m in maps], fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

    plt.suptitle('Algorithm Comparison on Moving AI Real-World Benchmark Maps\n'
                 '(Source: movingai.com — Room & Maze Maps)',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()

    os.makedirs(FIGURES_DIR, exist_ok=True)
    out = os.path.join(FIGURES_DIR, 'benchmark_real_maps_comparison.png')
    plt.savefig(out, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"\n[OK] 基准测试对比图已保存: {out}")
    return out


def visualize_real_map_path(map_file: str, crop_size: int = 80, seed: int = 999):
    """在真实地图上可视化路径对比"""
    rng = np.random.default_rng(seed)
    grid_full = parse_movingai_map(map_file)
    map_name = os.path.basename(map_file).replace('.map', '')

    sub = None
    for _ in range(100):
        sub = crop_submap(grid_full, crop_size, rng)
        if sub is not None:
            sg = sample_start_goal(sub, rng)
            if sg is not None:
                start, goal = sg
                break
    if sub is None:
        print("无法找到合适的子图")
        return

    astar_res = vanilla_astar_search(sub, start, goal)
    imp_res = improved_astar_search(sub, start, goal)

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(
        f'Traditional A* vs Improved A* on Real Map: {map_name}\n'
        f'(Moving AI Benchmark, {crop_size}x{crop_size} submap)',
        fontsize=13, fontweight='bold'
    )

    for ax, res, color, title in [
        (axes[0], astar_res, '#3498db',
         f"Traditional A*\nLength={astar_res['path_length']:.2f}  "
         f"Turns={astar_res['turn_count']}  Time={astar_res['runtime_ms']:.3f}ms"),
        (axes[1], imp_res, '#e74c3c',
         f"Improved A* (Ours)\nLength={imp_res['path_length']:.2f}  "
         f"Turns={imp_res['turn_count']}  Time={imp_res['runtime_ms']:.3f}ms"),
    ]:
        h, w = sub.shape
        display = np.where(sub == 1, 0.0, 0.95)
        ax.imshow(display, cmap='gray_r', vmin=0, vmax=1, origin='upper',
                  extent=[-0.5, w-0.5, h-0.5, -0.5])
        path = res['path']
        if len(path) >= 2:
            xs = [p[1] for p in path]
            ys = [p[0] for p in path]
            ax.plot(xs, ys, color=color, linewidth=2.5, zorder=3)
        ax.scatter([start[1]], [start[0]], marker='*', s=300, color='#2ecc71', zorder=5)
        ax.scatter([goal[1]], [goal[0]], marker='*', s=300, color='#e74c3c', zorder=5)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect('equal')

    plt.tight_layout()
    os.makedirs(FIGURES_DIR, exist_ok=True)
    out = os.path.join(FIGURES_DIR, f'real_map_{map_name}_path_comparison.png')
    plt.savefig(out, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"[OK] 真实地图路径对比图已保存: {out}")
    return out


def main():
    map_files = [
        os.path.join(MAPS_DIR, '8room_000.map'),
        os.path.join(MAPS_DIR, '16room_000.map'),
        os.path.join(MAPS_DIR, '32room_000.map'),
        os.path.join(MAPS_DIR, 'maze512-1-0.map'),
    ]
    # 过滤存在的文件
    map_files = [f for f in map_files if os.path.exists(f)]
    print(f"找到 {len(map_files)} 个真实地图文件")

    # 1. 在真实地图上跑基准测试
    results = run_benchmark(map_files, crop_size=100, repeats=30, seed=42)

    # 2. 保存 CSV
    import csv
    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_path = os.path.join(RESULTS_DIR, 'benchmark_real_maps.csv')
    if results:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\n[OK] 基准测试数据已保存: {csv_path}")

    # 3. 绘制对比图
    if results:
        plot_benchmark_results(results)

    # 4. 在室内地图上可视化路径
    room_map = os.path.join(MAPS_DIR, '8room_000.map')
    if os.path.exists(room_map):
        print("\n生成真实地图路径可视化...")
        visualize_real_map_path(room_map, crop_size=80, seed=2024)

    print("\n全部完成！")


if __name__ == "__main__":
    main()
