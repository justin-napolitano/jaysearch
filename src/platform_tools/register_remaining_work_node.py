from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.board_action_api import append_event_record
from platform_tools.plan_utils import parse_plan
from platform_tools.reconcile_remaining_work_merge import _update_queue_metadata
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")
QUEUE_PATH = Path("docs/queued-execplans.md")
EVENT_LOG_PATH = Path("artifacts/governance/board-action-events.jsonl")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _default_action_state() -> dict[str, Any]:
    return {
        "last_action_id": "",
        "last_action": "",
        "action_required": False,
        "reorder_requires_human": False,
        "reorder_blockers": [],
    }


def _insert_queue_entry(text: str, *, queue_position: int, execplan_id: str, title: str, implementation_branch: str) -> str:
    lines = text.splitlines()
    insert_at = len(lines)
    for idx, line in enumerate(lines):
        if line.startswith("## Mirror Metadata"):
            insert_at = idx
            break
    entry = [
        f"{queue_position}. `{execplan_id}`",
        "   - status: `decision_gated`",
        f"   - goal: {title}",
    ]
    if implementation_branch:
        entry.append(f"   - implementation branch: `{implementation_branch}`")
    entry.append("   - gate: `finalized draft ExecPlan required before execution`")
    if insert_at > 0 and lines[insert_at - 1] != "":
        entry.insert(0, "")
    if insert_at < len(lines) and lines[insert_at] != "":
        entry.append("")
    updated = lines[:insert_at] + entry + lines[insert_at:]
    return "\n".join(updated) + ("\n" if text.endswith("\n") else "")


def _event_exists(path: Path, event_id: str) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(record.get("event_id", "")).strip() == event_id:
            return True
    return False


def register_remaining_work_node(
    *,
    execplan_path: Path,
    repo_root: Path,
    event_log_path: Path | None = None,
) -> dict[str, Any]:
    plan = parse_plan(execplan_path)
    frontmatter = plan.frontmatter
    execplan_id = str(frontmatter.get("id", "")).strip()
    title = str(frontmatter.get("title", "")).strip()
    registration = frontmatter.get("graph_registration")
    if not execplan_id:
        raise ValueError("missing_execplan_id")
    if not isinstance(registration, dict):
        raise ValueError("missing_graph_registration")

    node_id = str(registration.get("node_id", "")).strip()
    queue_position = registration.get("queue_position")
    goal_area = str(registration.get("goal_area", "")).strip()
    conflict_domains = [str(item).strip() for item in registration.get("conflict_domains", []) if str(item).strip()]
    expected_artifacts = [str(item).strip() for item in registration.get("expected_artifacts", []) if str(item).strip()]
    implementation_branch = str(registration.get("implementation_branch", "")).strip()
    integration_mode = str(registration.get("integration_mode", "")).strip()
    initiative_branch = str(frontmatter.get("initiative_branch", "")).strip()
    initiative_node_id = str(frontmatter.get("initiative_node_id", "")).strip()
    if not node_id or not isinstance(queue_position, int) or not goal_area:
        raise ValueError("invalid_graph_registration")

    graph_path = repo_root / GRAPH_PATH
    queue_path = repo_root / QUEUE_PATH
    graph = _load_json(graph_path)
    nodes = graph.get("nodes", [])
    actions = graph.get("graph_actions", [])
    if not isinstance(nodes, list) or not isinstance(actions, list):
        raise ValueError("invalid_remaining_work_graph")

    existing = next((item for item in nodes if str(item.get("node_id", "")).strip() == node_id), None)
    if existing is None:
        if initiative_node_id:
            parent = next((item for item in nodes if str(item.get("node_id", "")).strip() == initiative_node_id), None)
            if parent is None:
                nodes.append(
                    {
                        "node_id": initiative_node_id,
                        "title": f"Initiative / {initiative_branch.removeprefix('initiative/').replace('-', ' ')}".strip(),
                        "status": "ready",
                        "gating_class": "auto_runnable",
                        "conflict_domains": sorted(set(conflict_domains)),
                        "target_execplan_id": f"initiative:{initiative_branch.removeprefix('initiative/')}",
                        "goal_area": "reference",
                        "initiative_branch": initiative_branch,
                        "parent_initiative_node": initiative_node_id,
                        "ordering": {},
                    }
                )
        new_node = {
            "node_id": node_id,
            "title": title,
            "status": "decision_gated",
            "status_reason": "registered from ExecPlan metadata; finalized draft ExecPlan required before execution",
            "gating_class": "decision_gated",
            "conflict_domains": sorted(set(conflict_domains)),
            "target_execplan_id": execplan_id,
            "goal_area": goal_area,
            "implementation_branch": implementation_branch,
            "initiative_branch": initiative_branch,
            "parent_initiative_node": initiative_node_id,
            "integration_mode": integration_mode,
            "expected_artifacts": expected_artifacts,
            "ordering": {
                "queue_position": queue_position,
                "tie_breaker": execplan_id,
            },
            "action_state": _default_action_state(),
        }
        nodes.append(new_node)
        action_id = f"rwg-action-{str(frontmatter.get('created', ''))[:10].replace('-', '')}-register-{node_id}"
        actions.append(
            {
                "action_id": action_id,
                "action": "block",
                "node_id": node_id,
                "rationale": "node registered deterministically from ExecPlan graph_registration metadata",
                "evidence_ref": execplan_path.as_posix(),
                "queue_reconciled": True,
            }
        )
        new_node["ordering"]["source_action_id"] = action_id
        new_node["action_state"]["last_action_id"] = action_id
        new_node["action_state"]["last_action"] = "block"
        queue_projection = graph.get("queue_projection", {}) if isinstance(graph.get("queue_projection"), dict) else {}
        queue_projection["last_reconciled_action_id"] = action_id
        queue_projection.setdefault("ready_execplan_ids", [])
        queue_projection["projection_authority"] = "projection_only"
        graph["queue_projection"] = queue_projection
        graph["nodes"] = nodes
        graph["graph_actions"] = actions
        _write_json(graph_path, graph)

        queue_text = queue_path.read_text(encoding="utf-8")
        queue_text = _insert_queue_entry(
            queue_text,
            queue_position=queue_position,
            execplan_id=execplan_id,
            title=title,
            implementation_branch=implementation_branch,
        )
        queue_text = _update_queue_metadata(
            queue_text,
            last_action_id=action_id,
            ready_execplan_ids=queue_projection.get("ready_execplan_ids", []),
        )
        queue_path.write_text(queue_text, encoding="utf-8")

        event_path = event_log_path or EVENT_LOG_PATH
        event_abs = repo_root / event_path
        event_id = f"event:{action_id}"
        if not _event_exists(event_abs, event_id):
            append_event_record(
                root=repo_root.as_posix(),
                event_log_path=event_path.as_posix(),
                record={
                    "event_id": event_id,
                    "transition_id": f"{execplan_id}:{node_id}:register_remaining_work_node",
                    "timestamp": str(frontmatter.get("created", "")).strip(),
                    "actor_id": str(frontmatter.get("owner", "")).strip() or "agent/codex-01",
                    "actor_class": "agent",
                    "action_id": action_id,
                    "action_family": "backlog_graph_action",
                    "object_id": node_id,
                    "source_state": "",
                    "target_state": "decision_gated",
                    "decision": "accepted",
                    "decision_reason": "registered_from_execplan_metadata",
                    "requested_mutation_surfaces": ["queue_projection", "remaining_work_graph"],
                    "applied_mutation_surfaces": ["queue_projection", "remaining_work_graph"],
                    "canonical_artifact_refs": [GRAPH_PATH.as_posix(), QUEUE_PATH.as_posix(), execplan_path.as_posix()],
                    "git_evidence_refs": [],
                    "github_evidence_refs": [],
                },
            )
        action_taken = "registered"
    else:
        action_id = str(existing.get("ordering", {}).get("source_action_id", "")).strip()
        action_taken = "noop"

    code, graph_report = check_remaining_work_graph(root=repo_root.as_posix())
    return {
        "command": "register-remaining-work-node",
        "status": "ok" if code == 0 else "blocked",
        "ok": code == 0,
        "action": action_taken,
        "execplan_id": execplan_id,
        "node_id": node_id,
        "action_id": action_id,
        "graph_report": graph_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execplan-path", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--event-log-path", default=EVENT_LOG_PATH.as_posix())
    args = parser.parse_args()
    report = register_remaining_work_node(
        execplan_path=Path(args.execplan_path),
        repo_root=Path(args.repo_root),
        event_log_path=Path(args.event_log_path),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
