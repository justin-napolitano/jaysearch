from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_selected_solution_scope import materialize_selected_solution_scope


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_recommendation(root: Path, *, missing_selected: bool = False) -> str:
    implementation_intent = {
        "summary": "Build candidate intent bridge.",
        "contract_changes": ["add implementation_intent to selected scope"],
        "runtime_changes": ["default scope from candidate intent"],
        "validation_changes": ["test selected scope carries candidate intent"],
        "docs_changes": ["document selected scope intent bridge"],
        "handoff_requirements": ["planner can create problem node from selected scope"],
    }
    payload = {
        "packet_type": "research_recommendation_packet",
        "packet_version": "v1",
        "packet_id": "rec-001",
        "created_at": "2026-05-20T00:00:00Z",
        "producer": "test",
        "problem_id": "prob-1",
        "candidate_search_tree_ref": "artifacts/candidate-search-tree.packet.json",
        "evaluation_summary_ref": "artifacts/candidate-evaluation-summary.packet.json",
        "evaluation_refs": ["artifacts/cand-1.evaluation.packet.json"],
        "ranked_candidates": [
            {
                "candidate_id": "cand-1",
                "problem_id": "prob-1",
                "rank": 1,
                "total_score": 0.9,
                "score_breakdown": {"contract_completeness": {"value": 1.0}},
                "summary": "Best candidate",
                "implementation_intent": implementation_intent,
                "contract_changes": implementation_intent["contract_changes"],
                "runtime_changes": implementation_intent["runtime_changes"],
                "validation_changes": implementation_intent["validation_changes"],
                "docs_changes": implementation_intent["docs_changes"],
                "expected_changes": [
                    *implementation_intent["contract_changes"],
                    *implementation_intent["runtime_changes"],
                    *implementation_intent["validation_changes"],
                    *implementation_intent["docs_changes"],
                ],
                "non_goals": ["do not build executor"],
                "handoff_requirements": implementation_intent["handoff_requirements"],
                "strengths": ["strong validation"],
                "weaknesses": ["narrow scope"],
                "promotion_status": "promoted",
                "evaluation_ref": "artifacts/cand-1.evaluation.packet.json",
                "evidence_refs": ["docs/example.md"],
                "source_hypothesis_id": "hypothesis-1",
                "assumptions": ["local runtime"],
            }
        ],
        "recommended_candidate_id": "" if missing_selected else "cand-1",
        "recommendation_reason": "Best candidate for planning",
        "open_questions": ["one"],
        "artifact_refs": ["artifact/a.json"],
        "evidence_refs": ["docs/example.md"],
    }
    path = root / "artifacts" / "recommendation.packet.json"
    _write_json(path, payload)
    return "artifacts/recommendation.packet.json"


def test_materialize_selected_solution_scope_emits_scope_packet(tmp_path: Path) -> None:
    recommendation_path = _seed_recommendation(tmp_path)
    code, report = materialize_selected_solution_scope(
        root=tmp_path.as_posix(),
        recommendation_path=recommendation_path,
        in_scope=["build bridge"],
        out_of_scope=["full research runtime"],
        acceptance_checks=["scope packet exists"],
    )

    assert code == 0
    assert report["status"] == "ok"
    packet = json.loads(Path(report["selected_solution_scope_path"]).read_text(encoding="utf-8"))
    assert packet["packet_type"] == "selected_solution_scope"
    assert packet["selected_candidate_id"] == "cand-1"
    assert packet["in_scope"] == ["build bridge"]
    assert packet["selection_policy"]["policy_id"] == "evaluation_backed_recommendation_gate_v1"
    assert packet["implementation_intent"]["summary"] == "Build candidate intent bridge."


def test_materialize_selected_solution_scope_defaults_scope_from_candidate_intent(
    tmp_path: Path,
) -> None:
    recommendation_path = _seed_recommendation(tmp_path)

    code, report = materialize_selected_solution_scope(
        root=tmp_path.as_posix(),
        recommendation_path=recommendation_path,
    )

    assert code == 0
    packet = json.loads(Path(report["selected_solution_scope_path"]).read_text(encoding="utf-8"))
    assert packet["in_scope"] == [
        "add implementation_intent to selected scope",
        "default scope from candidate intent",
        "test selected scope carries candidate intent",
        "document selected scope intent bridge",
    ]
    assert packet["acceptance_checks"] == ["test selected scope carries candidate intent"]
    assert packet["out_of_scope"] == ["do not build executor"]
    assert packet["handoff_requirements"] == [
        "planner can create problem node from selected scope"
    ]


def test_materialize_selected_solution_scope_blocks_invalid_recommendation(tmp_path: Path) -> None:
    recommendation_path = _seed_recommendation(tmp_path, missing_selected=True)
    code, report = materialize_selected_solution_scope(
        root=tmp_path.as_posix(),
        recommendation_path=recommendation_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "recommended_candidate_missing" in report["blockers"]


def test_materialize_selected_solution_scope_blocks_unevaluated_recommendation(
    tmp_path: Path,
) -> None:
    recommendation_path = _seed_recommendation(tmp_path)
    path = tmp_path / recommendation_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["evaluation_refs"] = []
    _write_json(path, payload)

    code, report = materialize_selected_solution_scope(
        root=tmp_path.as_posix(),
        recommendation_path=recommendation_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "recommendation_missing_evaluation_refs" in report["blockers"]


def test_materialize_selected_solution_scope_blocks_unpromoted_selection(
    tmp_path: Path,
) -> None:
    recommendation_path = _seed_recommendation(tmp_path)
    path = tmp_path / recommendation_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["ranked_candidates"][0]["promotion_status"] = "blocked"
    _write_json(path, payload)

    code, report = materialize_selected_solution_scope(
        root=tmp_path.as_posix(),
        recommendation_path=recommendation_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "selected_candidate_not_promoted" in report["blockers"]
