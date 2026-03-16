from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.board_action_api import append_event_record, build_event_record, check_board_action_api


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_specs(root: Path) -> None:
    _write(root / "spec/board-action-api.yaml", Path("spec/board-action-api.yaml").read_text(encoding="utf-8"))
    _write(root / "spec/board-event-log.schema.yaml", Path("spec/board-event-log.schema.yaml").read_text(encoding="utf-8"))


def test_board_action_api_check_passes_for_repo_contract() -> None:
    code, report = check_board_action_api()

    assert code == 0
    assert report["ok"] is True
    assert report["authority_model"]["canonical_backend"] == "local_repo_artifacts"
    assert "implementation_branch_publish" in report["action_family_ids"]


def test_board_action_api_check_detects_event_family_mismatch(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    schema_path = tmp_path / "spec/board-event-log.schema.yaml"
    schema_text = schema_path.read_text(encoding="utf-8").replace("  - exception_record\n", "  - unknown_family\n")
    schema_path.write_text(schema_text, encoding="utf-8")

    code, report = check_board_action_api(root=tmp_path.as_posix())

    assert code == 1
    assert "event_action_families_mismatch" in report["errors"]


def test_event_record_is_normalized_and_appended_deterministically(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    record = {
        "event_id": "evt-001",
        "transition_id": "tr-001",
        "timestamp": "2026-03-16T00:00:00Z",
        "actor_id": "agent/codex-01",
        "actor_class": "agent",
        "action_id": "act-001",
        "action_family": "implementation_branch_publish",
        "object_id": "rwg-021",
        "source_state": "review_gated",
        "target_state": "ready",
        "decision": "accepted",
        "decision_reason": "published_branch_detected",
        "requested_mutation_surfaces": ["queue_projection", "remaining_work_graph"],
        "applied_mutation_surfaces": ["remaining_work_graph", "queue_projection"],
        "canonical_artifact_refs": ["docs/queued-execplans.md", "artifacts/planner/research/remaining-work-graph.json"],
        "git_evidence_refs": ["refs/heads/impl-execplan/test", "commit:abc123"],
        "github_evidence_refs": ["pr:82"],
    }

    cleaned = build_event_record(record, root=tmp_path.as_posix())
    written = append_event_record(root=tmp_path.as_posix(), event_log_path="artifacts/governance/board-action-events.jsonl", record=record)

    assert written == cleaned
    assert written["canonical_artifact_refs"] == sorted(record["canonical_artifact_refs"])
    assert written["requested_mutation_surfaces"] == sorted(record["requested_mutation_surfaces"])

    lines = (tmp_path / "artifacts/governance/board-action-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == cleaned


def test_board_action_api_check_reports_invalid_yaml(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    (tmp_path / "spec/board-event-log.schema.yaml").write_text("event_log:\n  action_families_allowed:\n    - ok\n  deterministic_rules:\n    json_keys_sorted: true\n    timestamp_format: iso8601_utc\n    broken:\n      -\n    next: [\n", encoding="utf-8")

    code, report = check_board_action_api(root=tmp_path.as_posix())

    assert code == 1
    assert report["ok"] is False
    assert report["errors"][0].startswith("invalid_board_action_api_yaml:")
