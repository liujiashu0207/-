import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MONITOR_DIR = ROOT / "results" / "monitor"
STATE_PATH = MONITOR_DIR / "manus_monitor_state.json"
REPORT_PATH = MONITOR_DIR / "manus_monitor_latest.md"
TASK_PATH = MONITOR_DIR / "manus_next_instruction.txt"


def run_git(args: List[str]) -> str:
    out = subprocess.check_output(["git"] + args, cwd=ROOT, text=True, encoding="utf-8", errors="ignore")
    return out.strip()


def fetch_origin() -> None:
    subprocess.check_call(["git", "fetch", "origin"], cwd=ROOT)


def get_remote_head() -> str:
    return run_git(["rev-parse", "origin/main"])


def get_new_remote_commits(since_commit: str) -> List[Tuple[str, str, str]]:
    if not since_commit:
        raw = run_git(["log", "--oneline", "--decorate=short", "-12", "origin/main"])
    else:
        raw = run_git(["log", "--oneline", f"{since_commit}..origin/main"])
    commits = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        parts = ln.split(maxsplit=1)
        sha = parts[0]
        msg = parts[1] if len(parts) > 1 else ""
        author = run_git(["show", "-s", "--format=%an", sha])
        commits.append((sha, author, msg))
    return commits


def blob(path: str) -> str:
    return run_git(["show", f"origin/main:{path}"])


def check_remote_state() -> Dict[str, object]:
    checks: Dict[str, object] = {"ok": True, "issues": [], "notes": []}

    def issue(msg: str) -> None:
        checks["ok"] = False
        checks["issues"].append(msg)

    # Round5 收口后，唯一源码目录为 code/，科研论文/code/ 已归档
    core = blob("code/planners/core.py")
    alg = blob("code/planners/algorithms.py")

    if "return min(max(raw, 1.0), 1.8)" in core:
        checks["notes"].append("adaptive_alpha 下界=1.0：通过")
    else:
        issue("adaptive_alpha 下界不是 1.0。")

    if "def smooth_corners(path: List[Point], grid: np.ndarray)" in core:
        checks["notes"].append("smooth_corners 签名带 grid：通过")
    else:
        issue("smooth_corners 未接收 grid 参数。")

    if "grid[mx, my] == 0" in core or "grid[mx, my] == 1" in core:
        checks["notes"].append("smooth_corners 含障碍检测：通过")
    else:
        issue("smooth_corners 缺少障碍检测。")

    if "smooth_corners(p1, grid)" in alg:
        checks["notes"].append("algorithms.py 调用 smooth_corners(p1, grid)：通过")
    else:
        issue("algorithms.py 未正确传入 grid 给 smooth_corners。")

    if "use_jump_like=True" in alg:
        issue("发现 use_jump_like=True，JPS-like 仍被启用。")
    else:
        checks["notes"].append("未发现 use_jump_like=True：通过")

    # v3 口径审查：确认唯一权威实验脚本存在且不使用随机起终点
    try:
        run_v3 = blob("code/experiments/run_fix15_v3.py")
        if "sample_start_goal(" in run_v3:
            issue("run_fix15_v3.py 仍使用随机起终点，应改为 strict scen 口径。")
        elif "scen" in run_v3.lower():
            checks["notes"].append("run_fix15_v3.py 使用 strict scen 口径：通过")
        else:
            issue("run_fix15_v3.py 未发现 scen 口径逻辑，请检查。")
    except subprocess.CalledProcessError:
        issue("未找到 run_fix15_v3.py，唯一权威实验脚本丢失。")

    # v2 deprecated 检查：确认文件头含有 DEPRECATED 警告
    try:
        run_v2 = blob("code/experiments/run_fix15_v2.py")
        if "DEPRECATED" in run_v2:
            checks["notes"].append("run_fix15_v2.py 已标记 DEPRECATED：通过")
        else:
            issue("run_fix15_v2.py 未标记 DEPRECATED，存在误用风险。")
    except subprocess.CalledProcessError:
        checks["notes"].append("未找到 run_fix15_v2.py（已删除或归档，可忽略）")

    try:
        viz = blob("code/visualize/plot_path_comparison.py")
        if "/home/" in viz or "\\home\\" in viz:
            issue("可视化脚本存在绝对路径绑定（/home/...）。")
        else:
            checks["notes"].append("可视化脚本未发现绝对路径：通过")
    except subprocess.CalledProcessError:
        checks["notes"].append("未找到可视化脚本（可忽略）")

    return checks


def build_instruction(issues: List[str]) -> str:
    lines = [
        "给 Manus 的下一步指令（自动生成）",
        "",
        "请严格执行以下修复，不要改其他参数：",
    ]
    for i, x in enumerate(issues, 1):
        lines.append(f"{i}. {x}")
    lines += [
        "",
        "完成后请：",
        "- 推送到 origin/main",
        "- 在提交信息注明已修复项",
        "- 回传新的关键结果文件路径（如 exp_fix15_v3_key_metrics.csv）",
    ]
    return "\n".join(lines)


def write_outputs(head: str, commits: List[Tuple[str, str, str]], checks: Dict[str, object]) -> None:
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Manus 自动监控报告",
        "",
        f"- 时间: {now}",
        f"- origin/main: `{head}`",
        "",
        "## 新提交",
    ]
    if commits:
        lines += [f"- `{sha}` | {author} | {msg}" for sha, author, msg in commits]
    else:
        lines.append("- 无新增提交")

    lines += ["", "## 审查结果", f"- 总结: {'通过' if checks['ok'] else '存在问题'}", ""]
    lines += ["### 通过项"] + [f"- {x}" for x in checks["notes"]] if checks["notes"] else ["### 通过项", "- 无"]
    lines += ["", "### 问题项"] + [f"- {x}" for x in checks["issues"]] if checks["issues"] else ["", "### 问题项", "- 无"]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    task_text = build_instruction(checks["issues"]) if checks["issues"] else "当前无问题，无需新增指令。"
    TASK_PATH.write_text(task_text, encoding="utf-8")

    STATE_PATH.write_text(json.dumps({"last_remote_head": head, "updated_at": now}, ensure_ascii=False, indent=2), encoding="utf-8")


def load_last_head() -> str:
    if not STATE_PATH.exists():
        return ""
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return str(data.get("last_remote_head", ""))
    except Exception:
        return ""


def run_once() -> None:
    fetch_origin()
    last = load_last_head()
    head = get_remote_head()
    commits = get_new_remote_commits(last if last != head else "")
    checks = check_remote_state()
    write_outputs(head, commits, checks)
    print(f"[MONITOR] origin/main={head}")
    print(f"[MONITOR] report={REPORT_PATH}")
    print(f"[MONITOR] task={TASK_PATH}")
    print(f"[MONITOR] status={'OK' if checks['ok'] else 'ISSUES'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto monitor Manus commits on GitHub.")
    parser.add_argument("--watch", action="store_true", help="Run continuously")
    parser.add_argument("--interval_sec", type=int, default=180, help="Polling interval in seconds")
    args = parser.parse_args()

    if not args.watch:
        run_once()
        return

    while True:
        try:
            run_once()
        except Exception as e:
            MONITOR_DIR.mkdir(parents=True, exist_ok=True)
            (MONITOR_DIR / "manus_monitor_error.log").write_text(str(e), encoding="utf-8")
            print(f"[MONITOR] ERROR: {e}")
        time.sleep(max(args.interval_sec, 30))


if __name__ == "__main__":
    main()
