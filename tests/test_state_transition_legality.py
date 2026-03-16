from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.state_transition_legality import check_state_transition_legality


EXECPLAN_ID = "20260316-subgame-branch-state-transition-governance-codex-01-execplan"


def _git(root: Path, *args: str) -> str:
    command = ["git", *args]
    if args and args[0] == "commit":
        command = ["git", "commit", "--no-gpg-sign", *args[1:]]
    proc = subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _contract_text() -> str:
    return (
        "version: v1\n"
        "branch_roles:\n"
        "  - id: impl_execplan_root\n"
        "    branch_patterns: [impl-execplan/*]\n"
        "    scope_source: execplan_changes\n"
        "    allowed_surface_classes: [canonical_state_surface, projection_surface, capability_policy_surface]\n"
        "    requires_handoff: false\n"
        "    handoff_paths: []\n"
        "    merge_back_requires_local_referee: true\n"
        "  - id: subgame_branch\n"
        "    branch_patterns: [subgame/*]\n"
        "    scope_source: execplan_changes\n"
        "    allowed_surface_classes: [canonical_state_surface]\n"
        "    requires_handoff: true\n"
        "    handoff_paths: [.agent/handoffs/]\n"
        "    merge_back_requires_local_referee: true\n"
    )


def _surfaces_text() -> str:
    return (
        "version: v1\n"
        "surface_entries:\n"
        "  - id: execplan_surface\n"
        "    surface_class: canonical_state_surface\n"
        "    authority_role: canonical_local\n"
        "    path_prefixes: [.agent/execplans/]\n"
        "  - id: graph_surface\n"
        "    surface_class: canonical_state_surface\n"
        "    authority_role: canonical_local\n"
        "    path_exact: [artifacts/planner/research/remaining-work-graph.json]\n"
        "  - id: queue_surface\n"
        "    surface_class: projection_surface\n"
        "    authority_role: projection_only\n"
        "    path_exact: [docs/queued-execplans.md]\n"
        "  - id: policy_surface\n"
        "    surface_class: capability_policy_surface\n"
        "    authority_role: governance_local\n"
        "    path_exact: [spec/agent-capability-policy.yaml, spec/protected-surfaces.schema.yaml, spec/subgame-branch-contract.yaml]\n"
        "  - id: handoff_surface\n"
        "    surface_class: canonical_state_surface\n"
        "    authority_role: canonical_local\n"
        "    path_prefixes: [.agent/handoffs/]\n"
    )


def _execplan_text(branch: str, changes: list[str]) -> str:
    lines = [
        "---",
        f'id: "{EXECPLAN_ID}"',
        'title: "Transition Test"',
        'owner: "agent/codex-01"',
        'created: "2026-03-16T00:00:00Z"',
        'status: "draft"',
        'base_branch: "main"',
        "changes:",
    ]
    lines.extend(f"  - {item}" for item in changes)
    lines.extend(
        [
            'approve_policy: "codeowners"',
            'reviewers: ["github:test"]',
            'draft_by: "agent/codex-01"',
            f'draft_branch: "{branch}"',
            'draft_created: "2026-03-16T00:00:00Z"',
            'finalized_by: ""',
            'finalized_at: ""',
            'finalized_in_pr: ""',
            "---",
            "",
            "# Purpose / Big Picture",
            "",
            "## Progress",
            "",
            "## Surprises & Discoveries",
            "",
            "## Decision Log",
            "",
            "## Outcomes & Retrospective",
            "",
            "## Context and Orientation",
            "",
            "## Plan of Work",
            "",
            "## Concrete Steps",
            "",
            "## Validation and Acceptance",
            "",
            "## Idempotence and Recovery",
            "",
            "## Artifacts and Notes",
            "",
            "## Interfaces and Dependencies",
            "",
        ]
    )
    return "\n".join(lines)


def _graph(execplan_id: str) -> dict[str, object]:
    return {
        "nodes": [
            {"node_id": "rwg-021", "status": "completed", "target_execplan_id": "dep-plan"},
            {
                "node_id": "rwg-023",
                "status": "ready",
                "target_execplan_id": execplan_id,
                "goal_area": "governance",
                "implementation_branch": "impl-execplan/test",
                "action_state": {"action_required": False},
            },
        ],
        "edges": [{"from": "rwg-023", "to": "rwg-021", "relation": "depends_on"}],
    }


def _seed_repo(root: Path, branch: str, changes: list[str], *, extra_changed_file: str | None = None) -> Path:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Tests")
    _git(root, "config", "user.email", "tests@example.com")
    _write(root / "README.md", "base\n")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "docs: base")

    _git(root, "checkout", "-b", branch)
    execplan = root / ".agent" / "execplans" / f"{EXECPLAN_ID}.md"
    _write(execplan, _execplan_text(branch, changes))
    _write(root / "spec" / "subgame-branch-contract.yaml", _contract_text())
    _write(root / "spec" / "protected-surfaces.schema.yaml", _surfaces_text())
    _write(root / "spec" / "agent-capability-policy.yaml", "version: v1\ncapability_rules: []\n")
    _write_json(root / "artifacts/planner/research/remaining-work-graph.json", _graph(EXECPLAN_ID))
    _write(root / "docs/queued-execplans.md", "- queue\n")
    if extra_changed_file:
        _write(root / extra_changed_file, "extra\n")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "docs(governance): seed transition branch")
    return execplan


def test_state_transition_legality_accepts_declared_impl_branch_changes(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/test"
    execplan = _seed_repo(
        tmp_path,
        branch,
        [
            ".agent/execplans/20260316-subgame-branch-state-transition-governance-codex-01-execplan.md",
            "artifacts/planner/research/remaining-work-graph.json",
            "docs/queued-execplans.md",
            "spec/agent-capability-policy.yaml",
            "spec/protected-surfaces.schema.yaml",
            "spec/subgame-branch-contract.yaml",
        ],
    )
    monkeypatch.setattr(
        "platform_tools.state_transition_legality.check_remaining_work_graph",
        lambda **kwargs: (0, {"active_node": {"node_id": "rwg-023", "status": "ready"}}),
    )
    monkeypatch.setattr(
        "platform_tools.state_transition_legality.check_anti_cheat",
        lambda **kwargs: (0, {"ok": True, "blockers": []}),
    )

    code, report = check_state_transition_legality(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert report["branch_role"] == "impl_execplan_root"
    assert report["decision"] == "accepted"


def test_state_transition_legality_blocks_undeclared_file(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/test"
    execplan = _seed_repo(
        tmp_path,
        branch,
        [
            ".agent/execplans/20260316-subgame-branch-state-transition-governance-codex-01-execplan.md",
            "artifacts/planner/research/remaining-work-graph.json",
            "docs/queued-execplans.md",
            "spec/agent-capability-policy.yaml",
            "spec/protected-surfaces.schema.yaml",
            "spec/subgame-branch-contract.yaml",
        ],
        extra_changed_file="notes/unplanned.txt",
    )
    monkeypatch.setattr(
        "platform_tools.state_transition_legality.check_remaining_work_graph",
        lambda **kwargs: (0, {"active_node": {"node_id": "rwg-023", "status": "ready"}}),
    )
    monkeypatch.setattr(
        "platform_tools.state_transition_legality.check_anti_cheat",
        lambda **kwargs: (0, {"ok": True, "blockers": []}),
    )

    code, report = check_state_transition_legality(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 1
    assert "changed_file_not_declared:notes/unplanned.txt" in report["blockers"]


def test_state_transition_legality_requires_handoff_for_subgame_branch(monkeypatch, tmp_path: Path) -> None:
    branch = "subgame/test"
    execplan = _seed_repo(
        tmp_path,
        branch,
        [
            ".agent/execplans/20260316-subgame-branch-state-transition-governance-codex-01-execplan.md",
            "artifacts/planner/research/remaining-work-graph.json",
        ],
    )
    monkeypatch.setattr(
        "platform_tools.state_transition_legality.check_remaining_work_graph",
        lambda **kwargs: (0, {"active_node": {"node_id": "rwg-023", "status": "ready"}}),
    )
    monkeypatch.setattr(
        "platform_tools.state_transition_legality.check_anti_cheat",
        lambda **kwargs: (0, {"ok": True, "blockers": []}),
    )

    code, report = check_state_transition_legality(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 1
    assert "missing_handoff_artifact" in report["blockers"]
