from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.merge_readiness import check_merge_readiness
from platform_tools.plan_utils import parse_plan


API_VERSION = "mergeback-orchestration.v1"
ALLOWED_VALIDATIONS = {
    "bin/merge-readiness-check",
    "bin/execplan-validate",
    "bin/remaining-work-graph-check",
    "bin/policy-compliance-check",
}
PENDING_IMPL_NODE_STATUSES = {"decision_gated", "review_gated", "ready"}


def envelope(*, command: str, status: str, ok: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {
        "api_version": API_VERSION,
        "command": command,
        "status": status,
        "ok": ok,
    }
    if payload:
        body.update(payload)
    return body


def _load_graph(root: Path) -> dict[str, Any]:
    graph_path = root / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    return json.loads(graph_path.read_text(encoding="utf-8"))


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout.strip()


def _ref_exists(root: Path, ref: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _is_ancestor(root: Path, ancestor_ref: str, descendant_ref: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor_ref, descendant_ref],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _resolve_branch_ref(root: Path, branch: str, *, current_branch: str | None = None) -> str:
    current = (current_branch or get_current_branch(root=root)).strip()
    candidates = [
        f"refs/remotes/origin/{branch}",
        f"refs/heads/{branch}",
    ]
    if branch == current:
        candidates.insert(0, "HEAD")
    for candidate in candidates:
        if candidate == "HEAD" or _ref_exists(root, candidate):
            return candidate
    return ""


def _same_initiative_pending_nodes(graph: dict[str, Any], initiative_branch: str) -> list[dict[str, Any]]:
    nodes = graph.get("nodes", [])
    if not isinstance(nodes, list):
        return []
    return [
        node
        for node in nodes
        if isinstance(node, dict)
        and str(node.get("initiative_branch", "")).strip() == initiative_branch
        and str(node.get("status", "")).strip() in PENDING_IMPL_NODE_STATUSES
        and str(node.get("node_id", "")).strip() != str(node.get("parent_initiative_node", "")).strip()
        and str(node.get("target_execplan_id", "")).strip()
    ]


def _queue_position(node: dict[str, Any]) -> int:
    ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
    value = ordering.get("queue_position")
    return value if isinstance(value, int) else 10**9


def _active_node(graph: dict[str, Any], initiative_branch: str) -> dict[str, Any] | None:
    matches = [
        node
        for node in _same_initiative_pending_nodes(graph, initiative_branch)
        if str(node.get("node_id", "")).strip() == str(graph.get("active_node", {}).get("node_id", "")).strip()
    ]
    if len(matches) == 1:
        return matches[0]
    ordered = sorted(
        _same_initiative_pending_nodes(graph, initiative_branch),
        key=lambda node: (
            _queue_position(node),
            str(node.get("target_execplan_id", "")).strip(),
            str(node.get("node_id", "")).strip(),
        ),
    )
    return ordered[0] if ordered else None


def _stale_initiative_base(root: Path, *, source_branch: str, initiative_branch: str) -> bool | None:
    current_branch = get_current_branch(root=root)
    source_ref = _resolve_branch_ref(root, source_branch, current_branch=current_branch)
    target_ref = _resolve_branch_ref(root, initiative_branch, current_branch=current_branch)
    if not source_ref or not target_ref:
        return None
    return not _is_ancestor(root, target_ref, source_ref)


def _prior_unmerged_impl_slices(
    root: Path,
    *,
    initiative_branch: str,
    selected_node_id: str = "",
) -> list[dict[str, str]]:
    graph = _load_graph(root)
    initiative_ref = _resolve_branch_ref(root, initiative_branch, current_branch=get_current_branch(root=root))
    if not initiative_ref:
        return [{"blocker": "initiative_branch_not_current", "initiative_branch": initiative_branch}]

    unresolved: list[dict[str, str]] = []
    for node in sorted(
        _same_initiative_pending_nodes(graph, initiative_branch),
        key=lambda item: (_queue_position(item), str(item.get("node_id", "")).strip()),
    ):
        node_id = str(node.get("node_id", "")).strip()
        if selected_node_id and node_id == selected_node_id:
            continue
        branch = str(node.get("implementation_branch", "")).strip()
        if not branch:
            continue
        branch_ref = _resolve_branch_ref(root, branch, current_branch=get_current_branch(root=root))
        if not branch_ref:
            unresolved.append(
                {
                    "blocker": "prior_impl_slice_unmerged",
                    "node_id": node_id,
                    "implementation_branch": branch,
                    "reason": "branch_ref_missing",
                }
            )
            continue
        if not _is_ancestor(root, branch_ref, initiative_ref):
            unresolved.append(
                {
                    "blocker": "prior_impl_slice_unmerged",
                    "node_id": node_id,
                    "implementation_branch": branch,
                    "reason": "branch_not_merged_into_initiative",
                }
            )
    return unresolved


def _execplan_path_from_id(root: Path, execplan_id: str) -> Path | None:
    if not execplan_id:
        return None
    execplan_dir = root / ".agent" / "execplans"
    if not execplan_dir.exists():
        return None
    for path in sorted(execplan_dir.glob("*.md")):
        try:
            parsed = parse_plan(path)
        except Exception:
            continue
        if str(parsed.frontmatter.get("id", "")).strip() == execplan_id:
            return path
    return None


def resolve_mergeback_context(
    *,
    root: str = ".",
    source_branch: str | None = None,
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root).resolve()
    resolved_source = (source_branch or "").strip() or get_current_branch(root=root_path)
    resolved_initiative = (initiative_branch or "").strip()
    resolved_execplan_id = (execplan_id or "").strip()

    if not resolved_source.startswith("impl-execplan/"):
        return ["source_branch_role_invalid"], {
            "source_branch": resolved_source,
            "source_branch_role": "unknown",
        }

    graph = _load_graph(root_path)
    nodes = graph.get("nodes", [])
    matches = [
        node
        for node in nodes
        if isinstance(node, dict) and str(node.get("implementation_branch", "")).strip() == resolved_source
    ]
    if len(matches) != 1:
        return ["ambiguous_initiative_mapping"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
        }

    node = matches[0]
    target_branch = str(node.get("initiative_branch", "")).strip()
    if not target_branch:
        return ["target_branch_resolution_failed"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
            "node_id": str(node.get("node_id", "")).strip(),
        }
    if resolved_initiative and resolved_initiative != target_branch:
        return ["target_branch_resolution_failed"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
            "node_id": str(node.get("node_id", "")).strip(),
            "target_branch": target_branch,
            "initiative_branch": resolved_initiative,
        }

    resolved_execplan_id = resolved_execplan_id or str(node.get("target_execplan_id", "")).strip()
    execplan_path = _execplan_path_from_id(root_path, resolved_execplan_id)
    if execplan_path is None:
        return ["missing_active_execplan"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
            "target_branch": target_branch,
            "target_branch_role": "initiative",
            "node_id": str(node.get("node_id", "")).strip(),
            "execplan_id": resolved_execplan_id,
        }

    return [], {
        "source_branch": resolved_source,
        "source_branch_role": "implementation_execplan",
        "target_branch": target_branch,
        "target_branch_role": "initiative",
        "initiative_branch": target_branch,
        "integration_mode": str(node.get("integration_mode", "")).strip() or "via_initiative",
        "node_id": str(node.get("node_id", "")).strip(),
        "execplan_id": resolved_execplan_id,
        "execplan_path": execplan_path.as_posix(),
    }


def blockers_from_merge_readiness(report: dict[str, Any]) -> list[str]:
    failing_checks = [str(item).strip() for item in report.get("failing_checks", []) if str(item).strip()]
    blockers: list[str] = []
    if any(
        item.startswith("missing_base_ref:")
        or item.startswith("merge_target_mismatch:")
        or item == "missing_merge_target_contract"
        for item in failing_checks
    ):
        blockers.append("target_branch_resolution_failed")
    if any(item.startswith("validation_failed:") or item == "missing_smoke_test_validation" for item in failing_checks):
        blockers.append("required_validation_failed")
    if "dirty_generated_artifacts" in failing_checks:
        blockers.append("working_tree_hygiene_failed")
    if "implementation_branch_stale_against_initiative" in failing_checks:
        blockers.append("stale_initiative_base")
    if failing_checks and not blockers:
        blockers.append("merge_readiness_failed")
    seen: set[str] = set()
    ordered: list[str] = []
    for blocker in blockers:
        if blocker not in seen:
            seen.add(blocker)
            ordered.append(blocker)
    return ordered


def next_validations_from_merge_readiness(report: dict[str, Any]) -> list[str]:
    validations = report.get("checks", {}).get("validations", [])
    next_validations = ["bin/merge-readiness-check"]
    for result in validations:
        if not isinstance(result, dict):
            continue
        command = str(result.get("command", "")).strip()
        if command in ALLOWED_VALIDATIONS and not result.get("ok", False) and command not in next_validations:
            next_validations.append(command)
    return next_validations


def project_merge_readiness(
    *,
    root: str = ".",
    source_branch: str | None = None,
    target_branch: str | None = None,
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    blockers, context = resolve_mergeback_context(
        root=root,
        source_branch=source_branch,
        initiative_branch=initiative_branch or target_branch,
        execplan_id=execplan_id,
    )
    resolved_target = (target_branch or "").strip() or str(context.get("target_branch", "")).strip()
    if blockers:
        return 1, envelope(
            command="get-merge-readiness",
            status="blocked",
            ok=False,
            payload={
                "source_branch": str(context.get("source_branch", "")).strip(),
                "target_branch": resolved_target,
                "source_branch_role": str(context.get("source_branch_role", "")).strip(),
                "target_branch_role": "initiative",
                "initiative_branch": str(context.get("initiative_branch", "")).strip(),
                "readiness_checks": [],
                "blockers": blockers,
                "next_validations": ["bin/merge-readiness-check"],
                "next_action": "resolve_initiative_target",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/target-resolution-failed",
                    "title": "Merge-back target resolution failed",
                    "status": 409,
                    "detail": "The implementation branch could not be mapped to one lawful initiative merge target.",
                },
            },
        )

    code, report = check_merge_readiness(
        root=root,
        execplan_path=str(context.get("execplan_path", "")).strip() or None,
        base_ref=resolved_target,
    )
    readiness_checks = []
    for result in report.get("checks", {}).get("validations", []):
        if not isinstance(result, dict):
            continue
        command = str(result.get("command", "")).strip()
        if command in ALLOWED_VALIDATIONS:
            readiness_checks.append(
                {
                    "check_id": command,
                    "status": "passed" if result.get("ok", False) else "failed",
                }
            )
    blockers = blockers_from_merge_readiness(report)
    readiness = not blockers and code == 0
    payload = {
        "source_branch": str(context.get("source_branch", "")).strip(),
        "target_branch": resolved_target,
        "source_branch_role": "implementation_execplan",
        "target_branch_role": "initiative",
        "initiative_branch": str(context.get("initiative_branch", "")).strip(),
        "execplan_id": str(context.get("execplan_id", "")).strip(),
        "readiness_checks": readiness_checks,
        "blockers": blockers,
        "next_validations": [] if readiness else next_validations_from_merge_readiness(report),
        "next_action": "open_pr_to_initiative" if readiness else "run_merge_readiness_check",
    }
    stale_base = _stale_initiative_base(
        root=root_path,
        source_branch=str(context.get("source_branch", "")).strip(),
        initiative_branch=str(context.get("initiative_branch", "")).strip(),
    )
    if stale_base is None:
        blockers = list(payload["blockers"])
        blockers.append("target_branch_resolution_failed")
        payload["blockers"] = sorted(set(blockers))
        payload["next_action"] = "resolve_initiative_target"
    elif stale_base:
        blockers = list(payload["blockers"])
        blockers.append("stale_initiative_base")
        payload["blockers"] = sorted(set(blockers))
        payload["next_action"] = "restack_on_initiative"
    if blockers:
        payload["problem"] = {
            "type": "https://platform-template-bootstrap/problems/stale-initiative-base"
            if "stale_initiative_base" in payload["blockers"]
            else "https://platform-template-bootstrap/problems/merge-readiness-failed",
            "title": "Implementation branch no longer contains the current initiative head"
            if "stale_initiative_base" in payload["blockers"]
            else "Merge readiness failed",
            "status": 409,
            "detail": "Restack or rebase the implementation branch onto the current initiative head before merge-back."
            if "stale_initiative_base" in payload["blockers"]
            else "One or more merge-readiness checks are still failing for the implementation branch.",
        }
    readiness = not payload["blockers"] and code == 0
    return (0 if readiness else 1), envelope(
        command="get-merge-readiness",
        status="ok" if readiness else "blocked",
        ok=readiness,
        payload=payload,
    )


def project_pr_integration_contract(
    *,
    root: str = ".",
    source_branch: str | None = None,
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    blockers, context = resolve_mergeback_context(
        root=root,
        source_branch=source_branch,
        initiative_branch=initiative_branch,
        execplan_id=execplan_id,
    )
    if blockers:
        return 1, envelope(
            command="get-pr-integration-contract",
            status="blocked",
            ok=False,
            payload={
                "source_branch": str(context.get("source_branch", "")).strip(),
                "target_branch": str(context.get("target_branch", "")).strip(),
                "source_branch_role": str(context.get("source_branch_role", "")).strip(),
                "target_branch_role": "initiative",
                "integration_mode": "via_initiative",
                "required_validations": [],
                "required_human_actions": [],
                "blockers": blockers,
                "next_action": "resolve_initiative_target",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/target-resolution-failed",
                    "title": "PR integration target resolution failed",
                    "status": 409,
                    "detail": "The lawful initiative merge target could not be resolved for this implementation branch.",
                },
            },
        )

    return 0, envelope(
        command="get-pr-integration-contract",
        status="ok",
        ok=True,
        payload={
            "source_branch": str(context.get("source_branch", "")).strip(),
            "target_branch": str(context.get("target_branch", "")).strip(),
            "source_branch_role": "implementation_execplan",
            "target_branch_role": "initiative",
            "initiative_branch": str(context.get("initiative_branch", "")).strip(),
            "execplan_id": str(context.get("execplan_id", "")).strip(),
            "integration_mode": "via_initiative",
            "required_validations": [
                "bin/merge-readiness-check",
                "bin/execplan-validate",
                "bin/remaining-work-graph-check",
                "bin/policy-compliance-check",
            ],
            "required_human_actions": [
                "review_pr",
                "approve_pr",
                "merge_pr",
            ],
            "blockers": [],
            "next_action": "open_pr_to_initiative",
        },
    )


def prepare_next_impl_branch(
    *,
    root: str = ".",
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
    node_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    resolved_initiative = (initiative_branch or "").strip() or get_current_branch(root=root_path)
    if not resolved_initiative.startswith("initiative/"):
        return 1, envelope(
            command="prepare-next-impl-branch",
            status="blocked",
            ok=False,
            payload={
                "initiative_branch": resolved_initiative,
                "blockers": ["target_branch_role_invalid"],
                "next_action": "refresh_initiative_branch",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/invalid-branch-role",
                    "title": "Initiative branch required",
                    "status": 409,
                    "detail": "The next implementation slice must be prepared from an initiative branch context.",
                },
            },
        )

    current_branch = get_current_branch(root=root_path)
    if current_branch != resolved_initiative:
        return 1, envelope(
            command="prepare-next-impl-branch",
            status="blocked",
            ok=False,
            payload={
                "initiative_branch": resolved_initiative,
                "blockers": ["initiative_branch_not_current"],
                "next_action": "refresh_initiative_branch",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/stale-initiative-base",
                    "title": "Current branch is not the initiative branch",
                    "status": 409,
                    "detail": "Switch to the initiative branch before preparing the next implementation slice.",
                },
            },
        )

    initiative_ref = _resolve_branch_ref(root_path, resolved_initiative, current_branch=current_branch)
    if initiative_ref != "HEAD" and initiative_ref and not _is_ancestor(root_path, initiative_ref, "HEAD"):
        return 1, envelope(
            command="prepare-next-impl-branch",
            status="blocked",
            ok=False,
            payload={
                "initiative_branch": resolved_initiative,
                "blockers": ["initiative_branch_not_current"],
                "next_action": "refresh_initiative_branch",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/stale-initiative-base",
                    "title": "Initiative branch is behind its current published head",
                    "status": 409,
                    "detail": "Fast-forward the initiative branch before cutting the next implementation slice.",
                },
            },
        )

    graph = _load_graph(root_path)
    candidates = _same_initiative_pending_nodes(graph, resolved_initiative)
    if execplan_id:
        candidates = [
            node for node in candidates if str(node.get("target_execplan_id", "")).strip() == execplan_id.strip()
        ]
    if node_id:
        candidates = [node for node in candidates if str(node.get("node_id", "")).strip() == node_id.strip()]
    if not execplan_id and not node_id:
        active = _active_node(graph, resolved_initiative)
        candidates = [active] if active is not None else []

    if len(candidates) != 1:
        blocker = "ambiguous_initiative_mapping" if len(candidates) > 1 else "missing_active_execplan"
        return 1, envelope(
            command="prepare-next-impl-branch",
            status="blocked",
            ok=False,
            payload={
                "initiative_branch": resolved_initiative,
                "selectors": {
                    "execplan_id": (execplan_id or "").strip(),
                    "node_id": (node_id or "").strip(),
                },
                "blockers": [blocker],
                "next_action": "resolve_initiative_target",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/ambiguous-initiative-mapping",
                    "title": "The next implementation slice is not deterministic",
                    "status": 409,
                    "detail": "Specify the target execplan or reconcile the active node before cutting the next implementation branch.",
                },
            },
        )

    selected = candidates[0]
    selected_node_id = str(selected.get("node_id", "")).strip()
    unresolved = _prior_unmerged_impl_slices(
        root_path,
        initiative_branch=resolved_initiative,
        selected_node_id=selected_node_id,
    )
    if unresolved:
        return 1, envelope(
            command="prepare-next-impl-branch",
            status="blocked",
            ok=False,
            payload={
                "initiative_branch": resolved_initiative,
                "selected": {
                    "node_id": selected_node_id,
                    "execplan_id": str(selected.get("target_execplan_id", "")).strip(),
                    "implementation_branch": str(selected.get("implementation_branch", "")).strip(),
                },
                "blockers": ["prior_impl_slice_unmerged"],
                "prior_impl_slices": unresolved,
                "next_action": "resolve_prior_impl_slice",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/prior-impl-slice-unmerged",
                    "title": "An earlier implementation slice is still unmerged",
                    "status": 409,
                    "detail": "Merge or close the older implementation slice before cutting the next one.",
                },
            },
        )

    suggested_branch = str(selected.get("implementation_branch", "")).strip() or (
        f"impl-execplan/{str(selected.get('target_execplan_id', '')).strip()}"
    )
    return 0, envelope(
        command="prepare-next-impl-branch",
        status="ok",
        ok=True,
        payload={
            "initiative_branch": resolved_initiative,
            "selected": {
                "node_id": selected_node_id,
                "title": str(selected.get("title", "")).strip(),
                "execplan_id": str(selected.get("target_execplan_id", "")).strip(),
                "implementation_branch": suggested_branch,
            },
            "blockers": [],
            "next_action": "cut_impl_branch",
        },
    )
