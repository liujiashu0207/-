# Day 4 运行命令（并行推进版）

## 1) 快速冒烟测试（先跑小规模）
在项目根目录运行：

```bash
python code/experiments/run_b_route_experiments.py --sizes 20,40 --ratios 0.3,0.7 --repeats 5 --seed 42
```

## 2) 正式实验（建议）
```bash
python code/experiments/run_b_route_experiments.py --sizes 20,40,80,100 --ratios 0.3,0.7 --repeats 30 --seed 42
```

## 3) 结果输出位置
- 原始记录：`results/exp_raw_records.csv`
- 汇总结果：`results/exp_summary.csv`
- 运行时间图：`figures/runtime_comparison_b_route.png`

## 4) 通过标准（今日）
- [ ] 能生成三类文件（raw/summary/figure）
- [ ] 各算法都至少有一条有效记录
- [ ] 无运行报错
