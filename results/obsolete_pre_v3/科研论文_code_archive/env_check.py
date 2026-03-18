"""
Day 1 环境检查脚本
用途：
1) 记录 Python 与关键库版本
2) 生成可复现的环境信息文本（保存到 results/environment_report.txt）
"""

from __future__ import annotations

import importlib
import os
import platform
import sys
from datetime import datetime


def get_pkg_version(pkg_name: str) -> str:
    """安全获取包版本；未安装时返回 NOT_INSTALLED。"""
    try:
        module = importlib.import_module(pkg_name)
        return getattr(module, "__version__", "UNKNOWN")
    except Exception:
        return "NOT_INSTALLED"


def build_report() -> str:
    """生成环境报告文本。"""
    lines = [
        "=== 论文项目 Day1 环境报告 ===",
        f"生成时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "[系统信息]",
        f"OS: {platform.platform()}",
        f"Python: {sys.version.split()[0]}",
        f"解释器路径: {sys.executable}",
        "",
        "[关键依赖]",
        f"numpy: {get_pkg_version('numpy')}",
        f"matplotlib: {get_pkg_version('matplotlib')}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    report = build_report()
    print(report)

    out_dir = os.path.join("results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "environment_report.txt")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report + "\n")

    print(f"[OK] 已保存环境报告: {out_file}")


if __name__ == "__main__":
    main()
