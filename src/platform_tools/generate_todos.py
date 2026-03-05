from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.plan_utils import list_execplans, parse_plan

TODO_HEADER = "# TODO list\n\n"


def _normalize_task(plan_id: str, task: dict[str, Any]) -> dict[str, str]:
    title = str(task.get("title", "")).strip()
    priority = str(task.get("priority", "P2")).strip() or "P2"
    return {
        "plan_id": plan_id,
        "title": title,
        "priority": priority,
        "key": f"{plan_id}::{title}",
    }


def collect_tasks(execplans_glob: str = ".agent/execplans/*.md") -> tuple[list[dict[str, str]], list[str]]:
    tasks: list[dict[str, str]] = []
    warnings: list[str] = []
    for path in list_execplans(execplans_glob):
        parsed = parse_plan(path)
        fm = parsed.frontmatter
        if not fm:
            continue
        plan_id = str(fm.get("id", "")).strip()
        raw_tasks = fm.get("tasks", [])
        if not plan_id:
            warnings.append(f"missing_id:{path.as_posix()}")
            continue
        if not isinstance(raw_tasks, list):
            warnings.append(f"invalid_tasks:{path.as_posix()}")
            continue
        for raw in raw_tasks:
            if not isinstance(raw, dict):
                warnings.append(f"invalid_task_entry:{path.as_posix()}")
                continue
            norm = _normalize_task(plan_id, raw)
            if not norm["title"]:
                warnings.append(f"missing_task_title:{path.as_posix()}")
                continue
            tasks.append(norm)
    dedup = {item["key"]: item for item in tasks}
    normalized = [dedup[k] for k in sorted(dedup)]
    return normalized, sorted(set(warnings))


def render_todo(tasks: list[dict[str, str]]) -> str:
    lines = [TODO_HEADER.rstrip("\n")]
    for idx, task in enumerate(tasks, start=1):
        todo_id = f"TODO-{idx:04d}"
        lines.extend(
            [
                "",
                f"- id: {todo_id}",
                f"  title: {task['title']}",
                "  state: open",
                "  owner: unassigned",
                f"  priority: {task['priority']}",
                f"  execplan: {task['plan_id']}",
                f"  key: {task['key']}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def generate_todos(todo_path: str = "TODO.md") -> dict[str, Any]:
    tasks, warnings = collect_tasks()
    rendered = render_todo(tasks)
    target = Path(todo_path)
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    changed = old != rendered
    target.write_text(rendered, encoding="utf-8")
    return {
        "tool": "generate_todos",
        "todo_path": target.as_posix(),
        "task_count": len(tasks),
        "warnings": warnings,
        "changed": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--todo-path", default="TODO.md")
    args = parser.parse_args()
    report = generate_todos(args.todo_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
