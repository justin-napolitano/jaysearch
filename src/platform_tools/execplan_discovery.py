from __future__ import annotations

import json
import subprocess
from pathlib import Path

from platform_tools.plan_utils import parse_plan


GRAPH_PATH = "artifacts/planner/research/remaining-work-graph.json"


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout.strip()


def _changed_execplans(cwd: Path, base_ref: str) -> list[Path]:
    try:
        merge_base = _git(cwd, "merge-base", "HEAD", base_ref)
        output = _git(cwd, "diff", "--name-only", f"{merge_base}..HEAD", "--", ".agent/execplans")
    except RuntimeError:
        return []
    return sorted(
        cwd / line.strip()
        for line in output.splitlines()
        if line.strip().startswith(".agent/execplans/") and line.strip().endswith(".md")
    )


def _execplan_index(cwd: Path) -> tuple[dict[str, Path], dict[str, list[Path]]]:
    execplan_dir = cwd / ".agent" / "execplans"
    id_to_path: dict[str, Path] = {}
    draft_branch_to_paths: dict[str, list[Path]] = {}
    if not execplan_dir.exists():
        return id_to_path, draft_branch_to_paths
    for path in sorted(execplan_dir.glob("*.md")):
        parsed = parse_plan(path)
        plan_id = str(parsed.frontmatter.get("id", "")).strip()
        draft_branch = str(parsed.frontmatter.get("draft_branch", "")).strip()
        if plan_id and plan_id not in id_to_path:
            id_to_path[plan_id] = path
        if draft_branch:
            draft_branch_to_paths.setdefault(draft_branch, []).append(path)
    return id_to_path, draft_branch_to_paths


def discover_execplan(cwd: Path, branch: str, base_ref: str) -> tuple[Path | None, list[str], str]:
    id_to_path, draft_branch_to_paths = _execplan_index(cwd)

    draft_matches = sorted(draft_branch_to_paths.get(branch, []))
    if len(draft_matches) == 1:
        return draft_matches[0], [draft_matches[0].as_posix()], "draft_branch"
    if len(draft_matches) > 1:
        return None, [path.as_posix() for path in draft_matches], "ambiguous_draft_branch"

    graph_path = cwd / GRAPH_PATH
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        impl_matches: list[Path] = []
        missing_ids: list[str] = []
        for node in graph.get("nodes", []):
            if not isinstance(node, dict):
                continue
            implementation_branch = str(node.get("implementation_branch", "")).strip()
            target_execplan_id = str(node.get("target_execplan_id", "")).strip()
            if implementation_branch != branch or not target_execplan_id:
                continue
            plan_path = id_to_path.get(target_execplan_id)
            if plan_path is None:
                missing_ids.append(target_execplan_id)
                continue
            impl_matches.append(plan_path)
        deduped_impl_matches = sorted(
            {path.as_posix(): path for path in impl_matches}.values(),
            key=lambda path: path.as_posix(),
        )
        if len(deduped_impl_matches) == 1:
            path = deduped_impl_matches[0]
            return path, [path.as_posix()], "implementation_branch"
        if len(deduped_impl_matches) > 1:
            return None, [path.as_posix() for path in deduped_impl_matches], "ambiguous_implementation_branch"
        if missing_ids:
            return None, sorted(set(missing_ids)), "missing_execplan_for_implementation_branch"

    changed = _changed_execplans(cwd, base_ref)
    if len(changed) == 1:
        return changed[0], [changed[0].as_posix()], "changed_files"
    if len(changed) > 1:
        return None, [path.as_posix() for path in changed], "ambiguous_changed_files"
    return None, [], "not_found"
