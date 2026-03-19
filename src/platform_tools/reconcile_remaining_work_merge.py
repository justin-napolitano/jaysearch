from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from platform_tools.finalize_execplan import _merge_candidates
from platform_tools.remaining_work_graph_check import check_remaining_work_graph
from platform_tools.plan_utils import parse_plan


GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")
QUEUE_PATH = Path("docs/queued-execplans.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _next_action_id(actions: list[dict[str, Any]], *, committed_at: str, action: str, node_id: str) -> str:
    date_token = committed_at[:10].replace("-", "")
    prefix = f"rwg-action-{date_token}-"
    sequence = 0
    for item in actions:
        action_id = str(item.get("action_id", "")).strip()
        if not action_id.startswith(prefix):
            continue
        parts = action_id.split("-")
        if len(parts) < 4:
            continue
        try:
            sequence = max(sequence, int(parts[3]))
        except ValueError:
            continue
    return f"{prefix}{sequence + 1:03d}-{action}-{node_id}"


def _dependencies_complete(node_id: str, nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> bool:
    deps = [
        str(edge.get("to", "")).strip()
        for edge in edges
        if isinstance(edge, dict)
        and str(edge.get("from", "")).strip() == node_id
        and str(edge.get("relation", "")).strip() == "depends_on"
    ]
    return all(str(nodes.get(dep_id, {}).get("status", "")).strip() == "completed" for dep_id in deps)


def _queue_sort_key(node: dict[str, Any]) -> tuple[int, str, str]:
    ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
    queue_position = ordering.get("queue_position")
    if not isinstance(queue_position, int):
        queue_position = 999999
    return (queue_position, str(ordering.get("tie_breaker", "")).strip(), str(node.get("node_id", "")).strip())


def _choose_follow_on_node(nodes: list[dict[str, Any]], *, completed_node_id: str, edges: list[dict[str, Any]]) -> dict[str, Any] | None:
    node_map = {str(node.get("node_id", "")).strip(): node for node in nodes}
    candidates = []
    for node in nodes:
        node_id = str(node.get("node_id", "")).strip()
        if not node_id or node_id == completed_node_id:
            continue
        if str(node.get("status", "")).strip() != "blocked":
            continue
        if not _dependencies_complete(node_id, node_map, edges):
            continue
        candidates.append(node)
    if not candidates:
        return None
    candidates.sort(key=_queue_sort_key)
    return candidates[0]


def _recompute_ready_projection(nodes: list[dict[str, Any]]) -> list[str]:
    ready_nodes = []
    for node in nodes:
        goal_area = str(node.get("goal_area", "")).strip()
        if str(node.get("status", "")).strip() != "ready":
            ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
            ordering.pop("ready_order", None)
            node["ordering"] = ordering
            continue
        if not goal_area or goal_area == "reference":
            ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
            ordering.pop("ready_order", None)
            node["ordering"] = ordering
            continue
        ready_nodes.append(node)
    ready_nodes.sort(key=_queue_sort_key)
    for index, node in enumerate(ready_nodes, start=1):
        ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
        ordering["ready_order"] = index
        node["ordering"] = ordering
    return [str(node.get("target_execplan_id", "")).strip() for node in ready_nodes if str(node.get("target_execplan_id", "")).strip()]


def _update_queue_metadata(text: str, *, last_action_id: str, ready_execplan_ids: list[str]) -> str:
    ready_value = ", ".join(ready_execplan_ids)
    text = re.sub(r"canonical_last_graph_action_id:\s*`[^`]*`", f"canonical_last_graph_action_id: `{last_action_id}`", text)
    text = re.sub(r"canonical_ready_order:\s*`[^`]*`", f"canonical_ready_order: `{ready_value}`", text)
    return text


def _update_queue_entry(
    text: str,
    *,
    execplan_id: str,
    status: str,
    completion_ref: str | None = None,
    gate_note: str | None = None,
) -> str:
    lines = text.splitlines()
    item_start = None
    item_end = len(lines)
    item_pattern = re.compile(r"^\d+\.\s+`([^`]+)`")
    for idx, line in enumerate(lines):
        match = item_pattern.match(line)
        if not match:
            if item_start is not None and line.startswith("## "):
                item_end = idx
                break
            continue
        if match.group(1) == execplan_id:
            item_start = idx
            continue
        if item_start is not None:
            item_end = idx
            break
    if item_start is None:
        return text

    entry = lines[item_start:item_end]
    updated: list[str] = []
    status_written = False
    completion_written = False
    gate_written = False
    for line in entry:
        stripped = line.strip()
        if stripped.startswith("- status:"):
            updated.append(f"   - status: `{status}`")
            status_written = True
            continue
        if stripped.startswith("- completion ref:"):
            if completion_ref:
                updated.append(f"   - completion ref: `{completion_ref}`")
                completion_written = True
            continue
        if stripped.startswith("- blocker:") or stripped.startswith("- gate:"):
            if gate_note:
                updated.append(f"   - gate: `{gate_note}`")
                gate_written = True
            continue
        updated.append(line)
    trailing_blank_lines = 0
    while updated and updated[-1] == "":
        updated.pop()
        trailing_blank_lines += 1
    if not status_written:
        updated.append(f"   - status: `{status}`")
    if completion_ref and not completion_written:
        updated.append(f"   - completion ref: `{completion_ref}`")
    if gate_note and not gate_written:
        updated.append(f"   - gate: `{gate_note}`")
    updated.extend([""] * trailing_blank_lines)
    return "\n".join(lines[:item_start] + updated + lines[item_end:]) + ("\n" if text.endswith("\n") else "")


def _cleanup_queue_tail(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    in_tail_section = False
    for line in lines:
        if line.startswith("## Relationship to the Graph"):
            in_tail_section = True
            cleaned.append(line)
            continue
        if in_tail_section and line.startswith("   - "):
            continue
        cleaned.append(line)
    return "\n".join(cleaned) + ("\n" if text.endswith("\n") else "")


def _merge_search_ref(node: dict[str, Any], main_ref: str) -> str:
    integration_mode = str(node.get("integration_mode", "")).strip()
    initiative_branch = str(node.get("initiative_branch", "")).strip()
    if integration_mode == "via_initiative" and initiative_branch:
        return initiative_branch
    return main_ref


def _transition_event(node: dict[str, Any], *, completion_target_ref: str, main_ref: str) -> str:
    integration_mode = str(node.get("integration_mode", "")).strip()
    if str(node.get("node_id", "")).strip().startswith("initiative-"):
        return "initiative_merge_to_main"
    if integration_mode == "via_initiative" and completion_target_ref != main_ref:
        return "impl_execplan_merge_to_initiative"
    if integration_mode in {"direct_to_main_hotfix", "direct_to_main_patch"}:
        return "impl_execplan_merge_to_main_exception"
    return "impl_execplan_merge_to_main"


def _select_merge_candidate(
    *,
    candidates: list[dict[str, str]],
    implementation_branch: str,
) -> dict[str, str] | None:
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            1 if implementation_branch and str(item.get("branch_ref", "")).strip() == implementation_branch else 0,
            1 if item.get("merge_role") == "impl-execplan" else 0,
            item.get("committed_at", ""),
            item.get("commit", ""),
        ),
        reverse=True,
    )
    return candidates[0]


def _plan_path_for_execplan(repo_root: Path, execplan_id: str) -> Path | None:
    candidate = repo_root / ".agent" / "execplans" / f"{execplan_id}.md"
    return candidate if candidate.exists() else None


def _safe_merge_candidates(
    repo_root: Path,
    merge_ref: str,
    execplan_id: str,
    draft_branch: str,
) -> list[dict[str, str]]:
    try:
        return _merge_candidates(repo_root, merge_ref, execplan_id, draft_branch)
    except ValueError as exc:
        message = str(exc).strip()
        if message.startswith("fatal: ambiguous argument "):
            return []
        raise


def find_pending_merge_reconciliations(
    *,
    repo_root: Path,
    main_ref: str = "main",
) -> list[dict[str, Any]]:
    graph = _load_json(repo_root / GRAPH_PATH)
    nodes = graph.get("nodes", [])
    pending: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("status", "")).strip() == "completed":
            continue
        execplan_id = str(node.get("target_execplan_id", "")).strip()
        if not execplan_id:
            continue
        plan_path = _plan_path_for_execplan(repo_root, execplan_id)
        if plan_path is None:
            continue
        plan = parse_plan(plan_path)
        draft_branch = str(plan.frontmatter.get("draft_branch", "")).strip()
        merge_ref = _merge_search_ref(node, main_ref)
        candidates = _safe_merge_candidates(repo_root, merge_ref, execplan_id, draft_branch)
        selected = _select_merge_candidate(
            candidates=candidates,
            implementation_branch=str(node.get("implementation_branch", "")).strip(),
        )
        if selected is None:
            continue
        pending.append(
            {
                "node_id": str(node.get("node_id", "")).strip(),
                "execplan_id": execplan_id,
                "execplan_path": plan_path,
                "merge_evidence": selected,
            }
        )
    return pending


def reconcile_pending_merge_completions(
    *,
    repo_root: Path,
    main_ref: str = "main",
) -> dict[str, Any]:
    pending = find_pending_merge_reconciliations(repo_root=repo_root, main_ref=main_ref)
    results: list[dict[str, Any]] = []
    for item in pending:
        results.append(
            reconcile_remaining_work_merge(
                execplan_path=item["execplan_path"],
                repo_root=repo_root,
                main_ref=main_ref,
                merge_evidence=item["merge_evidence"],
            )
        )
    return {
        "command": "reconcile-pending-merge-completions",
        "status": "ok",
        "ok": True,
        "reconciled_count": len(results),
        "results": results,
    }


def reconcile_remaining_work_merge(
    *,
    execplan_path: Path,
    repo_root: Path,
    main_ref: str = "main",
    merge_evidence: dict[str, str] | None = None,
) -> dict[str, Any]:
    plan = parse_plan(execplan_path)
    execplan_id = str(plan.frontmatter.get("id", "")).strip()
    if not execplan_id:
        raise ValueError("missing_execplan_id")

    graph_path = repo_root / GRAPH_PATH
    queue_path = repo_root / QUEUE_PATH
    graph = _load_json(graph_path)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    actions = graph.get("graph_actions", [])
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(actions, list):
        raise ValueError("invalid_remaining_work_graph")

    node = next((item for item in nodes if str(item.get("target_execplan_id", "")).strip() == execplan_id), None)
    if node is None:
        raise ValueError("remaining_work_node_not_found")

    if merge_evidence is None:
        draft_branch = str(plan.frontmatter.get("draft_branch", "")).strip()
        merge_ref = _merge_search_ref(node, main_ref)
        candidates = _merge_candidates(repo_root, merge_ref, execplan_id, draft_branch)
        if not candidates:
            raise ValueError("missing_merge_commit")
        implementation_branch = str(node.get("implementation_branch", "")).strip()
        merge_evidence = _select_merge_candidate(candidates=candidates, implementation_branch=implementation_branch)
        if merge_evidence is None:
            raise ValueError("missing_merge_commit")
    completion_ref = f"merged:pr-{merge_evidence['pull_request']}" if merge_evidence.get("pull_request", "").strip() else f"merged:{merge_evidence['commit']}"
    completion_target_ref = _merge_search_ref(node, main_ref)
    transition_event = _transition_event(node, completion_target_ref=completion_target_ref, main_ref=main_ref)

    node_id = str(node.get("node_id", "")).strip()
    existing_complete_action = None
    for action in reversed(actions):
        if (
            str(action.get("node_id", "")).strip() == node_id
            and str(action.get("action", "")).strip() == "complete"
            and str(action.get("evidence_ref", "")).strip() == completion_ref
        ):
            existing_complete_action = action
            break
    if existing_complete_action is None:
        complete_action_id = _next_action_id(actions, committed_at=merge_evidence["committed_at"], action="complete", node_id=node_id)
        actions.append(
            {
                "action_id": complete_action_id,
                "action": "complete",
                "node_id": node_id,
                "rationale": (
                    f"{execplan_id} merged to {completion_target_ref} and is now canonical completed state"
                ),
                "evidence_ref": completion_ref,
                "queue_reconciled": True,
            }
        )
    else:
        complete_action_id = str(existing_complete_action.get("action_id", "")).strip()
    node["status"] = "completed"
    node["completion_ref"] = completion_ref
    node["status_reason"] = ""
    ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
    ordering.pop("ready_order", None)
    ordering["source_action_id"] = complete_action_id
    node["ordering"] = ordering
    action_state = node.get("action_state", {}) if isinstance(node.get("action_state"), dict) else {}
    action_state["last_action_id"] = complete_action_id
    action_state["last_action"] = "complete"
    action_state["action_required"] = False
    action_state["reorder_requires_human"] = False
    action_state["reorder_blockers"] = []
    node["action_state"] = action_state

    next_node = _choose_follow_on_node(nodes, completed_node_id=node_id, edges=edges)
    next_action_id = complete_action_id
    next_node_status = ""
    if next_node is not None:
        next_node_id = str(next_node.get("node_id", "")).strip()
        next_execplan_id = str(next_node.get("target_execplan_id", "")).strip()
        next_node["status"] = "review_gated"
        next_node["gating_class"] = "review_gated"
        next_node["status_reason"] = (
            f"{execplan_id} is completed on {completion_target_ref}; this is the next canonical slice and now requires "
            "a canonical ExecPlan plus a published implementation branch before execution"
        )
        next_ordering = next_node.get("ordering", {}) if isinstance(next_node.get("ordering"), dict) else {}
        next_ordering.pop("ready_order", None)
        existing_unblock_action = None
        for action in reversed(actions):
            if (
                str(action.get("node_id", "")).strip() == next_node_id
                and str(action.get("action", "")).strip() == "unblock"
                and str(action.get("evidence_ref", "")).strip() == completion_ref
            ):
                existing_unblock_action = action
                break
        if existing_unblock_action is None:
            next_action_id = _next_action_id(actions, committed_at=merge_evidence["committed_at"], action="unblock", node_id=next_node_id)
            actions.append(
                {
                    "action_id": next_action_id,
                    "action": "unblock",
                    "node_id": next_node_id,
                    "rationale": (
                        f"{execplan_id} completed on {completion_target_ref}; dependency gating is cleared "
                        "for the next canonical slice"
                    ),
                    "evidence_ref": completion_ref,
                    "queue_reconciled": True,
                }
            )
        else:
            next_action_id = str(existing_unblock_action.get("action_id", "")).strip()
        next_ordering["source_action_id"] = next_action_id
        next_node["ordering"] = next_ordering
        next_action_state = next_node.get("action_state", {}) if isinstance(next_node.get("action_state"), dict) else {}
        next_action_state["last_action_id"] = next_action_id
        next_action_state["last_action"] = "unblock"
        next_action_state["action_required"] = False
        next_action_state["reorder_requires_human"] = False
        next_action_state["reorder_blockers"] = []
        next_node["action_state"] = next_action_state
        next_node_status = str(next_node.get("status", "")).strip()

    ready_execplan_ids = _recompute_ready_projection(nodes)
    queue_projection = graph.get("queue_projection", {}) if isinstance(graph.get("queue_projection"), dict) else {}
    queue_projection["last_reconciled_action_id"] = actions[-1]["action_id"]
    queue_projection["ready_execplan_ids"] = ready_execplan_ids
    queue_projection["projection_authority"] = "projection_only"
    graph["queue_projection"] = queue_projection
    graph["graph_actions"] = actions
    graph["nodes"] = nodes
    _write_json(graph_path, graph)

    queue_text = queue_path.read_text(encoding="utf-8")
    queue_text = _update_queue_metadata(queue_text, last_action_id=actions[-1]["action_id"], ready_execplan_ids=ready_execplan_ids)
    queue_text = _update_queue_entry(queue_text, execplan_id=execplan_id, status="completed", completion_ref=completion_ref)
    if next_node is not None:
        queue_text = _update_queue_entry(
            queue_text,
            execplan_id=str(next_node.get("target_execplan_id", "")).strip(),
            status=str(next_node.get("status", "")).strip(),
            gate_note="canonical ExecPlan and published implementation branch required before execution",
        )
    queue_text = _cleanup_queue_tail(queue_text)
    queue_path.write_text(queue_text, encoding="utf-8")

    code, graph_report = check_remaining_work_graph(root=repo_root.as_posix(), branch="main")
    return {
        "command": "reconcile-remaining-work-merge",
        "status": "ok" if code == 0 else "blocked",
        "ok": code == 0,
        "execplan_id": execplan_id,
        "completed_node_id": node_id,
        "completion_ref": completion_ref,
        "completion_target_ref": completion_target_ref,
        "transition_event": transition_event,
        "merge_commit": str(merge_evidence.get("commit", "")).strip(),
        "merge_signature_status": str(merge_evidence.get("signature_status", "")).strip(),
        "graph_action_ids": [complete_action_id] + ([next_action_id] if next_node is not None else []),
        "next_node_id": str(next_node.get("node_id", "")).strip() if next_node is not None else "",
        "next_node_status": next_node_status,
        "ready_execplan_ids": ready_execplan_ids,
        "graph_report": graph_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execplan-path", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--main-ref", default="main")
    args = parser.parse_args()
    report = reconcile_remaining_work_merge(
        execplan_path=Path(args.execplan_path),
        repo_root=Path(args.repo_root),
        main_ref=args.main_ref,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
