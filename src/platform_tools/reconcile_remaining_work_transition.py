from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from platform_tools.board_action_api import append_event_record
from platform_tools.plan_utils import parse_plan
from platform_tools.reconcile_remaining_work_merge import (
    _cleanup_queue_tail,
    _next_action_id,
    _recompute_ready_projection,
    _update_queue_entry,
    _update_queue_metadata,
)
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")
QUEUE_PATH = Path("docs/queued-execplans.md")
EVENT_LOG_PATH = Path("artifacts/governance/board-action-events.jsonl")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _branch_publish_evidence(root: Path, branch: str) -> dict[str, str] | None:
    if not branch:
        return None
    remote_ref = f"refs/remotes/origin/{branch}"
    commit = _git(root, "rev-parse", "--verify", remote_ref)
    if not commit:
        return None
    committed_at = _git(root, "show", "-s", "--format=%cI", commit)
    return {
        "branch_ref": branch,
        "remote_ref": f"origin/{branch}",
        "commit": commit,
        "committed_at": committed_at,
    }


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


def reconcile_remaining_work_transition(
    *,
    execplan_path: Path,
    repo_root: Path,
    event_log_path: Path | None = None,
) -> dict[str, Any]:
    plan = parse_plan(execplan_path)
    frontmatter = plan.frontmatter
    execplan_id = str(frontmatter.get("id", "")).strip()
    if not execplan_id:
        raise ValueError("missing_execplan_id")

    graph = _load_json(repo_root / GRAPH_PATH)
    nodes = graph.get("nodes", [])
    actions = graph.get("graph_actions", [])
    if not isinstance(nodes, list) or not isinstance(actions, list):
        raise ValueError("invalid_remaining_work_graph")

    node = next((item for item in nodes if str(item.get("target_execplan_id", "")).strip() == execplan_id), None)
    if node is None:
        raise ValueError("remaining_work_node_not_found")

    node_id = str(node.get("node_id", "")).strip()
    source_state = str(node.get("status", "")).strip()
    finalized_in_pr = str(frontmatter.get("finalized_in_pr", "")).strip()
    finalized_at = str(frontmatter.get("finalized_at", "")).strip()
    implementation_branch = str(node.get("implementation_branch", "")).strip()
    publish_evidence = _branch_publish_evidence(repo_root, implementation_branch)

    transition_name = ""
    target_state = source_state
    action_name = ""
    action_family = ""
    decision_reason = ""
    evidence_ref = ""
    timestamp = ""
    git_evidence_refs: list[str] = []
    github_evidence_refs: list[str] = []

    if source_state == "decision_gated" and finalized_in_pr:
        transition_name = "draft_execplan_merge_to_main"
        target_state = "review_gated"
        action_name = "unblock"
        action_family = "backlog_graph_action"
        decision_reason = "finalized_draft_detected"
        evidence_ref = f"merged:pr-{finalized_in_pr}"
        timestamp = finalized_at or ""
        github_evidence_refs = [f"pr:{finalized_in_pr}"]
    elif source_state == "review_gated" and publish_evidence is not None:
        transition_name = "implementation_branch_publish"
        target_state = "ready"
        action_name = "promote_ready"
        action_family = "implementation_branch_publish"
        decision_reason = "published_branch_detected"
        evidence_ref = f"branch:{publish_evidence['remote_ref']}"
        timestamp = publish_evidence["committed_at"]
        git_evidence_refs = [
            f"branch:{publish_evidence['remote_ref']}",
            f"commit:{publish_evidence['commit']}",
        ]

    if not transition_name:
        code, graph_report = check_remaining_work_graph(root=repo_root.as_posix())
        return {
            "command": "reconcile-remaining-work-transition",
            "status": "noop" if code == 0 else "blocked",
            "ok": code == 0,
            "execplan_id": execplan_id,
            "node_id": node_id,
            "source_state": source_state,
            "target_state": source_state,
            "transition_event": "",
            "graph_report": graph_report,
        }

    action_id = _next_action_id(actions, committed_at=timestamp or "2026-01-01T00:00:00Z", action=action_name, node_id=node_id)
    actions.append(
        {
            "action_id": action_id,
            "action": action_name,
            "node_id": node_id,
            "rationale": f"{transition_name} derived deterministically from canonical branch and ExecPlan evidence",
            "evidence_ref": evidence_ref,
            "queue_reconciled": True,
        }
    )

    node["status"] = target_state
    node["gating_class"] = "auto_runnable" if target_state == "ready" else "review_gated"
    node["status_reason"] = "" if target_state == "ready" else "finalized draft is canonical; implementation branch publication required before execution"
    ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
    ordering["source_action_id"] = action_id
    if target_state != "ready":
        ordering.pop("ready_order", None)
    node["ordering"] = ordering
    action_state = node.get("action_state", {}) if isinstance(node.get("action_state"), dict) else {}
    action_state["last_action_id"] = action_id
    action_state["last_action"] = action_name
    action_state["action_required"] = False
    action_state["reorder_requires_human"] = False
    action_state["reorder_blockers"] = []
    node["action_state"] = action_state

    ready_execplan_ids = _recompute_ready_projection(nodes)
    queue_projection = graph.get("queue_projection", {}) if isinstance(graph.get("queue_projection"), dict) else {}
    queue_projection["last_reconciled_action_id"] = action_id
    queue_projection["ready_execplan_ids"] = ready_execplan_ids
    queue_projection["projection_authority"] = "projection_only"
    graph["queue_projection"] = queue_projection
    graph["graph_actions"] = actions
    graph["nodes"] = nodes
    _write_json(repo_root / GRAPH_PATH, graph)

    queue_path = repo_root / QUEUE_PATH
    queue_text = queue_path.read_text(encoding="utf-8")
    queue_text = _update_queue_metadata(queue_text, last_action_id=action_id, ready_execplan_ids=ready_execplan_ids)
    gate_note = None
    if target_state == "review_gated":
        gate_note = "canonical ExecPlan is finalized; published implementation branch required before execution"
    queue_text = _update_queue_entry(
        queue_text,
        execplan_id=execplan_id,
        status=target_state,
        gate_note=gate_note,
    )
    queue_text = _cleanup_queue_tail(queue_text)
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
                "transition_id": f"{execplan_id}:{node_id}:{transition_name}",
                "timestamp": timestamp or "2026-01-01T00:00:00Z",
                "actor_id": "agent/codex-01",
                "actor_class": "agent",
                "action_id": action_id,
                "action_family": action_family,
                "object_id": node_id,
                "source_state": source_state,
                "target_state": target_state,
                "decision": "accepted",
                "decision_reason": decision_reason,
                "requested_mutation_surfaces": ["queue_projection", "remaining_work_graph"],
                "applied_mutation_surfaces": ["queue_projection", "remaining_work_graph"],
                "canonical_artifact_refs": [GRAPH_PATH.as_posix(), QUEUE_PATH.as_posix()],
                "git_evidence_refs": git_evidence_refs,
                "github_evidence_refs": github_evidence_refs,
            },
        )

    code, graph_report = check_remaining_work_graph(root=repo_root.as_posix())
    return {
        "command": "reconcile-remaining-work-transition",
        "status": "ok" if code == 0 else "blocked",
        "ok": code == 0,
        "execplan_id": execplan_id,
        "node_id": node_id,
        "source_state": source_state,
        "target_state": target_state,
        "transition_event": transition_name,
        "action_id": action_id,
        "event_log_path": event_path.as_posix(),
        "graph_report": graph_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execplan-path", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--event-log-path", default=EVENT_LOG_PATH.as_posix())
    args = parser.parse_args()
    report = reconcile_remaining_work_transition(
        execplan_path=Path(args.execplan_path),
        repo_root=Path(args.repo_root),
        event_log_path=Path(args.event_log_path),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
