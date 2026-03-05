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


def collect_tasks(
    execplans_glob: str = ".agent/execplans/*.md",
    paths: list[Path] | None = None,
    tracked_only: bool = True,
) -> tuple[list[dict[str, str]], list[str]]:
    tasks: list[dict[str, str]] = []
    warnings: list[str] = []
    plan_paths = (
        sorted(paths)
        if paths is not None
        else list_execplans(execplans_glob, tracked_only=tracked_only)
    )
    for path in plan_paths:
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


def parse_existing_state(todo_path: str) -> dict[str, dict[str, str]]:
    path = Path(todo_path)
    if not path.exists():
        return {}
    entries: dict[str, dict[str, str]] = {}
    current_key = ""
    current_state = ""
    current_owner = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- id: "):
            if current_key:
                entries[current_key] = {"state": current_state or "open", "owner": current_owner or "unassigned"}
            current_key = ""
            current_state = ""
            current_owner = ""
            continue
        if line.startswith("state: "):
            current_state = line.split(":", 1)[1].strip()
            continue
        if line.startswith("owner: "):
            current_owner = line.split(":", 1)[1].strip()
            continue
        if line.startswith("key: "):
            current_key = line.split(":", 1)[1].strip()
            continue
    if current_key:
        entries[current_key] = {"state": current_state or "open", "owner": current_owner or "unassigned"}
    return entries


def render_todo(tasks: list[dict[str, str]], existing_state: dict[str, dict[str, str]]) -> str:
    lines = [TODO_HEADER.rstrip("\n")]
    for idx, task in enumerate(tasks, start=1):
        todo_id = f"TODO-{idx:04d}"
        state_owner = existing_state.get(task["key"], {})
        state = state_owner.get("state", "open")
        owner = state_owner.get("owner", "unassigned")
        lines.extend(
            [
                "",
                f"- id: {todo_id}",
                f"  title: {task['title']}",
                f"  state: {state}",
                f"  owner: {owner}",
                f"  priority: {task['priority']}",
                f"  execplan: {task['plan_id']}",
                f"  key: {task['key']}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def generate_todos(todo_path: str = "TODO.md") -> dict[str, Any]:
    tasks, warnings = collect_tasks()
    existing_state = parse_existing_state(todo_path)
    rendered = render_todo(tasks, existing_state)
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
