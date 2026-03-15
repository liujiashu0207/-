"""
科研经验自动沉淀脚本

功能：
1) --add 追加一条科研经验到 results/research_experience_log.jsonl
2) 自动刷新 rules.md 中 EXPERIENCE_AUTO 区块
3) --sync 仅执行刷新，不新增条目
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "rules.md"
LOG_PATH = ROOT / "results" / "research_experience_log.jsonl"
START_MARKER = "<!-- EXPERIENCE_AUTO_START -->"
END_MARKER = "<!-- EXPERIENCE_AUTO_END -->"


@dataclass
class ExperienceEntry:
    time: str
    issue: str
    cause: str
    solution: str
    prevention: str
    stage: str
    tags: List[str]
    outcome: str


def ensure_files() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"找不到 rules.md: {RULES_PATH}")


def parse_tags(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def append_entry(entry: ExperienceEntry) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def load_entries() -> List[ExperienceEntry]:
    items: List[ExperienceEntry] = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                items.append(
                    ExperienceEntry(
                        time=raw.get("time", ""),
                        issue=raw.get("issue", ""),
                        cause=raw.get("cause", ""),
                        solution=raw.get("solution", ""),
                        prevention=raw.get("prevention", ""),
                        stage=raw.get("stage", ""),
                        tags=raw.get("tags", []),
                        outcome=raw.get("outcome", ""),
                    )
                )
            except json.JSONDecodeError:
                continue
    return items


def render_auto_block(entries: List[ExperienceEntry], max_items: int = 20) -> str:
    if not entries:
        return "_经验库尚无记录。_"

    latest = sorted(entries, key=lambda x: x.time, reverse=True)[:max_items]
    lines = [
        f"共记录 **{len(entries)}** 条经验，展示最近 **{len(latest)}** 条：",
        "",
        "| 时间 | 阶段 | 问题 | 解决方案 | 预防措施 | 标签 |",
        "|---|---|---|---|---|---|",
    ]
    for e in latest:
        tags = "、".join(e.tags) if e.tags else "-"
        lines.append(
            f"| {e.time} | {e.stage or '-'} | {e.issue} | {e.solution} | {e.prevention} | {tags} |"
        )
    lines.append("")
    lines.append("说明：详细原始记录见 `results/research_experience_log.jsonl`。")
    return "\n".join(lines)


def sync_rules(entries: List[ExperienceEntry]) -> None:
    content = RULES_PATH.read_text(encoding="utf-8")
    new_block = render_auto_block(entries)
    if START_MARKER not in content or END_MARKER not in content:
        # 若标记不存在，则追加到末尾
        content += f"\n\n{START_MARKER}\n{new_block}\n{END_MARKER}\n"
    else:
        start = content.index(START_MARKER) + len(START_MARKER)
        end = content.index(END_MARKER)
        content = content[:start] + "\n" + new_block + "\n" + content[end:]

    RULES_PATH.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="科研经验自动沉淀与同步脚本")
    p.add_argument("--sync", action="store_true", help="仅同步 rules.md 自动经验区块")
    p.add_argument("--add", action="store_true", help="新增一条经验并同步")
    p.add_argument("--issue", type=str, default="", help="问题描述")
    p.add_argument("--cause", type=str, default="", help="问题原因")
    p.add_argument("--solution", type=str, default="", help="解决方案")
    p.add_argument("--prevention", type=str, default="", help="预防措施")
    p.add_argument("--stage", type=str, default="", help="适用阶段，例如 Day2/文献检索")
    p.add_argument("--tags", type=str, default="", help="标签，逗号分隔")
    p.add_argument("--outcome", type=str, default="", help="结果说明")
    return p


def main() -> None:
    ensure_files()
    args = build_parser().parse_args()

    if args.add:
        required = [args.issue, args.cause, args.solution, args.prevention]
        if not all(required):
            raise ValueError("--add 时必须提供 issue/cause/solution/prevention")
        entry = ExperienceEntry(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            issue=args.issue.strip(),
            cause=args.cause.strip(),
            solution=args.solution.strip(),
            prevention=args.prevention.strip(),
            stage=args.stage.strip(),
            tags=parse_tags(args.tags),
            outcome=args.outcome.strip(),
        )
        append_entry(entry)

    entries = load_entries()
    sync_rules(entries)
    print(f"[OK] 已同步经验库，当前总条目: {len(entries)}")
    print(f"[INFO] 经验日志: {LOG_PATH}")
    print(f"[INFO] 规则文件: {RULES_PATH}")


if __name__ == "__main__":
    main()
