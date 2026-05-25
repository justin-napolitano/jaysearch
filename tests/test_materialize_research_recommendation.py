from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_research_recommendation import materialize_research_recommendation


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_tree(root: Path) -> str:
    payload = {
        "packet_type": "candidate_search_tree_packet",
        "packet_version": "v1",
        "packet_id": "tree-001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "problem_id": "problem-1",
        "root_node_id": "root",
        "tree_nodes": [],
        "tree_edges": [],
        "search_policy": {"max_candidates": 2},
        "candidate_packet_refs": [
            "artifacts/candidate-1.packet.json",
            "artifacts/candidate-2.packet.json",
        ],
    }
    path = root / "artifacts" / "candidate-search-tree.packet.json"
    _write_json(path, payload)
    return "artifacts/candidate-search-tree.packet.json"


def _seed_candidate(root: Path, candidate_id: str, hypothesis_id: str) -> str:
    implementation_intent = {
        "summary": "Implement candidate-specific packet changes.",
        "contract_changes": ["add candidate field"],
        "runtime_changes": ["propagate candidate field"],
        "validation_changes": ["test candidate field propagation"],
        "docs_changes": ["document candidate field"],
        "handoff_requirements": ["carry field to selected scope"],
    }
    payload = {
        "packet_type": "research_candidate_packet",
        "packet_version": "v1",
        "packet_id": f"{candidate_id}:packet",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "candidate_id": candidate_id,
        "problem_id": "problem-1",
        "source_hypothesis_id": hypothesis_id,
        "candidate_family": "baseline_reference",
        "approach_summary": "Candidate",
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
        "planner_entry_notes": ["ready for selected scope"],
        "assumptions": ["bounded"],
        "proposed_changes": ["make a packet"],
        "artifact_refs": [],
        "source_type": "hypothesis_tree_search",
        "evidence_refs": ["artifacts/evidence.packet.json"],
        "feasibility_priors": {"expected_complexity": "low"},
    }
    path = root / "artifacts" / f"{candidate_id}.packet.json"
    _write_json(path, payload)
    return f"artifacts/{candidate_id}.packet.json"


def _seed_evaluation(
    root: Path,
    candidate_id: str,
    *,
    score: float,
    promotion_status: str = "promoted",
) -> str:
    payload = {
        "packet_type": "research_evaluation_packet",
        "packet_version": "v1",
        "packet_id": f"{candidate_id}:evaluation:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "evaluation_id": f"{candidate_id}:evaluation:001",
        "problem_id": "problem-1",
        "candidate_id": candidate_id,
        "source_hypothesis_id": "hypothesis-1",
        "evaluation_method": "test",
        "metrics": {
            "contract_completeness": {"value": 1.0, "basis": "test"},
            "total_score": {"value": score, "basis": "test"},
        },
        "failures": [] if promotion_status == "promoted" else ["blocked_by_test"],
        "warnings": [],
        "artifact_refs": [],
        "evidence_refs": ["artifacts/evidence.packet.json"],
        "promotion_status": promotion_status,
    }
    path = root / "artifacts" / f"{candidate_id}.evaluation.packet.json"
    _write_json(path, payload)
    return f"artifacts/{candidate_id}.evaluation.packet.json"


def _seed_summary(root: Path, evaluation_paths: list[str]) -> str:
    payload = {
        "packet_type": "candidate_evaluation_summary_packet",
        "packet_version": "v1",
        "packet_id": "problem-1:candidate-evaluation-summary",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "problem_id": "problem-1",
        "candidate_search_tree_ref": "artifacts/candidate-search-tree.packet.json",
        "evaluation_packet_refs": evaluation_paths,
        "promoted_candidate_ids": ["candidate-1"],
        "blocked_candidate_ids": [],
        "evaluation_policy": {"method": "test"},
    }
    path = root / "artifacts" / "candidate-evaluation-summary.packet.json"
    _write_json(path, payload)
    return "artifacts/candidate-evaluation-summary.packet.json"


def test_materialize_research_recommendation_ranks_evaluated_candidates(tmp_path: Path) -> None:
    tree_path = _seed_tree(tmp_path)
    candidate_1 = _seed_candidate(tmp_path, "candidate-1", "hypothesis-1")
    candidate_2 = _seed_candidate(tmp_path, "candidate-2", "hypothesis-2")
    evaluation_1 = _seed_evaluation(tmp_path, "candidate-1", score=0.7)
    evaluation_2 = _seed_evaluation(tmp_path, "candidate-2", score=0.9, promotion_status="blocked")
    summary = _seed_summary(tmp_path, [evaluation_1, evaluation_2])

    code, report = materialize_research_recommendation(
        root=tmp_path.as_posix(),
        candidate_search_tree_path=tree_path,
        candidate_paths=[candidate_1, candidate_2],
        evaluation_paths=[evaluation_1, evaluation_2],
        evaluation_summary_path=summary,
    )

    assert code == 0
    assert report["status"] == "ok"
    recommendation = json.loads(Path(report["recommendation_packet_path"]).read_text(encoding="utf-8"))
    assert recommendation["packet_type"] == "research_recommendation_packet"
    assert recommendation["recommended_candidate_id"] == "candidate-1"
    assert recommendation["ranked_candidates"][0]["evaluation_ref"].endswith(
        "candidate-1.evaluation.packet.json"
    )
    assert recommendation["ranked_candidates"][0]["implementation_intent"]["summary"]
    assert recommendation["ranked_candidates"][0]["contract_changes"] == ["add candidate field"]
    assert recommendation["ranked_candidates"][0]["validation_changes"] == [
        "test candidate field propagation"
    ]
    assert recommendation["rejected_candidate_summaries"][0]["candidate_id"] == "candidate-2"


def test_materialize_research_recommendation_blocks_missing_evaluation(tmp_path: Path) -> None:
    tree_path = _seed_tree(tmp_path)
    candidate_1 = _seed_candidate(tmp_path, "candidate-1", "hypothesis-1")
    candidate_2 = _seed_candidate(tmp_path, "candidate-2", "hypothesis-2")
    evaluation_1 = _seed_evaluation(tmp_path, "candidate-1", score=0.7)
    summary = _seed_summary(tmp_path, [evaluation_1])

    code, report = materialize_research_recommendation(
        root=tmp_path.as_posix(),
        candidate_search_tree_path=tree_path,
        candidate_paths=[candidate_1, candidate_2],
        evaluation_paths=[evaluation_1],
        evaluation_summary_path=summary,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "candidate_missing_evaluation:candidate-2" in report["blockers"]


def test_materialize_research_recommendation_blocks_without_promoted_candidate(tmp_path: Path) -> None:
    tree_path = _seed_tree(tmp_path)
    candidate_1 = _seed_candidate(tmp_path, "candidate-1", "hypothesis-1")
    evaluation_1 = _seed_evaluation(tmp_path, "candidate-1", score=0.9, promotion_status="blocked")
    summary = _seed_summary(tmp_path, [evaluation_1])

    code, report = materialize_research_recommendation(
        root=tmp_path.as_posix(),
        candidate_search_tree_path=tree_path,
        candidate_paths=[candidate_1],
        evaluation_paths=[evaluation_1],
        evaluation_summary_path=summary,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["blockers"] == ["no_promoted_research_candidates"]
