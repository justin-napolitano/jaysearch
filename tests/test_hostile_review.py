from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.hostile_review import load_hostile_review_state, run_hostile_review


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_execplan(root: Path) -> Path:
    path = root / ".agent" / "execplans" / "20260313-game-hostile-review-runtime-codex-01-execplan.md"
    _write_text(
        path,
        "\n".join(
            [
                "---",
                'id: "20260313-game-hostile-review-runtime-codex-01-execplan"',
                'title: "Hostile Review"',
                'owner: "agent/codex-01"',
                'created: "2026-03-13T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - src/platform_tools/hostile_review.py",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                'draft_branch: "draft-execplan/test"',
                'draft_created: "2026-03-13T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "validation:",
                "  tests:",
                '    - name: "execplan-validate"',
                '      command: "bin/execplan-validate .agent/execplans/20260313-game-hostile-review-runtime-codex-01-execplan.md"',
                '      expected_exit: 0',
                '    - name: "policy-compliance-check"',
                '      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260313-game-hostile-review-runtime-codex-01-execplan.md"',
                '      expected_exit: 0',
                '    - name: "hostile-review-smoke-test"',
                '      command: "bin/hostile-review-smoke-test"',
                '      expected_exit: 0',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    return path


def _seed_spec(root: Path) -> None:
    _write_text(
        root / "spec" / "games" / "hostile-review-game.yaml",
        "\n".join(
            [
                "game_id: game-hostile-review",
                "parent_game: game-implementation",
                "layer: review",
                "objective: deterministic hostile review",
            ]
        )
        + "\n",
    )


def test_hostile_review_writes_deterministic_artifacts(monkeypatch, tmp_path: Path) -> None:
    execplan = _seed_execplan(tmp_path)
    _seed_spec(tmp_path)
    branch = "impl-execplan/20260313-game-hostile-review-runtime-codex-01-execplan-codex-01-20260313"

    monkeypatch.setattr(
        "platform_tools.hostile_review.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "status": "ok",
                "active_node": {
                    "node_id": "rwg-014",
                    "status": "ready",
                    "target_execplan_id": "20260313-game-hostile-review-runtime-codex-01-execplan",
                    "implementation_branch": branch,
                },
                "ordering": {"ready_execplan_ids": ["20260313-game-hostile-review-runtime-codex-01-execplan"]},
                "queue_projection": {"projection_authority": "projection_only"},
                "errors": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.hostile_review.check_policy_compliance",
        lambda **kwargs: (0, {"ok": True, "status": "ok", "blockers": []}),
    )
    monkeypatch.setattr(
        "platform_tools.hostile_review.check_merge_readiness",
        lambda **kwargs: (
            0,
            {
                "readiness": False,
                "failing_checks": ["validation_failed:pending"],
                "checks": {"validations": []},
            },
        ),
    )

    code, report = run_hostile_review(
        root=tmp_path.as_posix(),
        branch=branch,
        execplan_path=execplan.as_posix(),
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["review_state"] == "clean"
    assert report["finding_counts"]["warning"] == 1

    artifact_report = json.loads((tmp_path / "artifacts" / "review" / "hostile-review-report.json").read_text(encoding="utf-8"))
    artifact_evidence = json.loads((tmp_path / "artifacts" / "review" / "validation-evidence.json").read_text(encoding="utf-8"))
    artifact_summary = (tmp_path / "artifacts" / "review" / "hostile-review-summary.md").read_text(encoding="utf-8")

    assert artifact_report["review_state"] == "clean"
    assert artifact_evidence["checks"][0]["name"] == "policy-compliance-check"
    assert "# Hostile Review Summary" in artifact_summary


def test_load_hostile_review_state_reads_current_artifact(tmp_path: Path) -> None:
    report_path = tmp_path / "artifacts" / "review" / "hostile-review-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "execplan_id": "20260313-game-hostile-review-runtime-codex-01-execplan",
                "review_state": "recovery_required",
                "ok": False,
                "finding_counts": {"blocker": 2, "warning": 1},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    state = load_hostile_review_state(
        root=tmp_path.as_posix(),
        target_execplan_id="20260313-game-hostile-review-runtime-codex-01-execplan",
        implementation_branch="impl-execplan/example",
        current_branch="impl-execplan/example",
        node_status="ready",
    )

    assert state["state"] == "recovery_required"
    assert state["blocker_count"] == 2
    assert state["warning_count"] == 1
