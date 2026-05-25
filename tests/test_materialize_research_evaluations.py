from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_research_evaluations import materialize_research_evaluations


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
        "candidate_packet_refs": ["artifacts/candidate-1.packet.json"],
    }
    path = root / "artifacts" / "candidate-search-tree.packet.json"
    _write_json(path, payload)
    return "artifacts/candidate-search-tree.packet.json"


def _seed_candidate(root: Path, *, missing_hypothesis: bool = False) -> str:
    payload = {
        "packet_type": "research_candidate_packet",
        "packet_version": "v1",
        "packet_id": "candidate-1:packet",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "candidate_id": "candidate-1",
        "problem_id": "problem-1",
        "source_hypothesis_id": "" if missing_hypothesis else "hypothesis-1",
        "candidate_family": "baseline_reference",
        "approach_summary": "Baseline candidate",
        "assumptions": ["bounded"],
        "proposed_changes": ["make a packet"],
        "artifact_refs": [],
        "source_type": "hypothesis_tree_search",
        "evidence_refs": ["artifacts/evidence.packet.json"],
        "feasibility_priors": {
            "expected_complexity": "low",
            "dependency_risk": "low",
            "implementation_risk": "low",
            "evidence_strength": "supported",
        },
    }
    path = root / "artifacts" / "candidate-1.packet.json"
    _write_json(path, payload)
    return "artifacts/candidate-1.packet.json"


def test_materialize_research_evaluations_emits_evaluation_and_summary(tmp_path: Path) -> None:
    tree_path = _seed_tree(tmp_path)
    candidate_path = _seed_candidate(tmp_path)

    code, report = materialize_research_evaluations(
        root=tmp_path.as_posix(),
        candidate_search_tree_path=tree_path,
        candidate_paths=[candidate_path],
    )

    assert code == 0
    assert report["status"] == "ok"
    evaluation = json.loads(Path(report["evaluation_packet_paths"][0]).read_text(encoding="utf-8"))
    summary = json.loads(Path(report["evaluation_summary_packet_path"]).read_text(encoding="utf-8"))
    assert evaluation["packet_type"] == "research_evaluation_packet"
    assert evaluation["promotion_status"] == "promoted"
    assert summary["packet_type"] == "candidate_evaluation_summary_packet"
    assert summary["promoted_candidate_ids"] == ["candidate-1"]


def test_materialize_research_evaluations_blocks_untraceable_candidate(tmp_path: Path) -> None:
    tree_path = _seed_tree(tmp_path)
    candidate_path = _seed_candidate(tmp_path, missing_hypothesis=True)

    code, report = materialize_research_evaluations(
        root=tmp_path.as_posix(),
        candidate_search_tree_path=tree_path,
        candidate_paths=[candidate_path],
    )

    assert code == 0
    assert report["status"] == "ok"
    evaluation = json.loads(Path(report["evaluation_packet_paths"][0]).read_text(encoding="utf-8"))
    assert evaluation["promotion_status"] == "blocked"
    assert "candidate_missing_source_hypothesis_id" in evaluation["failures"]
