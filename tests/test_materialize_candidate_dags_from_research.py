from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_candidate_dags_from_research import (  # noqa: E402
    materialize_candidate_dags_from_research,
)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_candidate(root: Path, candidate_id: str, *, promoted: bool = True) -> str:
    payload = {
        "packet_type": "research_candidate_packet",
        "packet_version": "v1",
        "packet_id": f"{candidate_id}:packet",
        "created_at": "2026-05-27T00:00:00Z",
        "producer": "test",
        "candidate_id": candidate_id,
        "problem_id": "problem-1",
        "source_hypothesis_id": f"hypothesis:{candidate_id}",
        "candidate_family": "baseline_reference" if promoted else "novel_synthesized",
        "approach_summary": f"Use {candidate_id} to build the adapter.",
        "implementation_intent": {"summary": "Adapter implementation intent."},
        "contract_changes": ["spec/contracts/candidate-dag-manifest.schema.yaml"],
        "runtime_changes": ["src/platform_tools/materialize_candidate_dags_from_research.py"],
        "validation_changes": ["tests/test_materialize_candidate_dags_from_research.py"],
        "docs_changes": ["docs/research-candidate-to-dag-adapter-v1.md"],
        "expected_changes": ["candidate DAG manifest is emitted"],
        "non_goals": ["do not synthesize code"],
        "handoff_requirements": ["selected DAG can materialize execution units"],
        "planner_entry_notes": ["ready"],
        "assumptions": ["bounded"],
        "proposed_changes": ["project candidate intent into a DAG"],
        "artifact_refs": [],
        "source_type": "hypothesis_tree_search",
        "evidence_refs": ["artifacts/evidence.packet.json"],
        "feasibility_priors": {
            "expected_complexity": "low" if promoted else "high",
            "implementation_risk": "low" if promoted else "high",
            "dependency_risk": "low",
        },
    }
    path = root / "artifacts" / f"{candidate_id}.packet.json"
    _write_json(path, payload)
    return f"artifacts/{candidate_id}.packet.json"


def _seed_recommendation(root: Path) -> str:
    payload = {
        "packet_type": "research_recommendation_packet",
        "packet_version": "v1",
        "packet_id": "problem-1:research-recommendation",
        "created_at": "2026-05-27T00:00:00Z",
        "producer": "test",
        "problem_id": "problem-1",
        "candidate_search_tree_ref": "artifacts/candidate-search-tree.packet.json",
        "evaluation_summary_ref": "artifacts/candidate-evaluation-summary.packet.json",
        "evaluation_refs": ["artifacts/candidate-1.evaluation.packet.json"],
        "ranked_candidates": [
            {
                "candidate_id": "candidate-1",
                "rank": 1,
                "total_score": 0.9,
                "promotion_status": "promoted",
                "evidence_refs": ["artifacts/evidence.packet.json"],
            },
            {
                "candidate_id": "candidate-2",
                "rank": 2,
                "total_score": 0.4,
                "promotion_status": "blocked",
                "evidence_refs": ["artifacts/evidence.packet.json"],
            },
        ],
        "recommended_candidate_id": "candidate-1",
        "recommendation_reason": "test",
        "winner_evidence_refs": ["artifacts/evidence.packet.json"],
        "rejected_candidate_summaries": [{"candidate_id": "candidate-2"}],
        "open_questions": [],
        "artifact_refs": [],
        "evidence_refs": ["artifacts/evidence.packet.json"],
    }
    path = root / "artifacts" / "research-recommendation.packet.json"
    _write_json(path, payload)
    return "artifacts/research-recommendation.packet.json"


def _seed_evidence(root: Path) -> str:
    payload = {
        "packet_type": "evidence_packet",
        "packet_version": "v1",
        "packet_id": "evidence-1",
        "created_at": "2026-05-27T00:00:00Z",
        "producer": "test",
        "problem_id": "problem-1",
        "source_refs": ["docs/research-recommendation-v1.md"],
        "claim_refs": ["candidate intent can be projected"],
        "method_refs": ["bounded adapter"],
        "benchmark_refs": ["unit test"],
        "evidence_summary": "Evidence summary.",
    }
    path = root / "artifacts" / "evidence.packet.json"
    _write_json(path, payload)
    return "artifacts/evidence.packet.json"


def test_materialize_candidate_dags_from_research_emits_manifest_and_dag(tmp_path: Path) -> None:
    recommendation = _seed_recommendation(tmp_path)
    candidate_1 = _seed_candidate(tmp_path, "candidate-1")
    candidate_2 = _seed_candidate(tmp_path, "candidate-2", promoted=False)
    evidence = _seed_evidence(tmp_path)

    code, report = materialize_candidate_dags_from_research(
        root=tmp_path.as_posix(),
        research_recommendation_path=recommendation,
        candidate_paths=[candidate_1, candidate_2],
        evidence_packet_path=evidence,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["generated_candidate_count"] == 2
    manifest = json.loads(Path(tmp_path / report["candidate_dag_manifest_path"]).read_text(encoding="utf-8"))
    dag = json.loads(Path(tmp_path / report["candidate_dag_paths"][0]).read_text(encoding="utf-8"))
    assert manifest["packet_type"] == "candidate_dag_manifest"
    assert manifest["candidate_dag_refs"][0]["candidate_id"] == "research_candidate_candidate-1"
    assert manifest["candidate_dag_refs"][1]["blockers"] == ["research_candidate_not_promoted:candidate-2"]
    assert dag["graph_type"] == "implementation_dag"
    node_ids = {node["node_id"] for node in dag["nodes"]}
    assert "candidate-1_runtime_surface" in node_ids
    runtime_node = next(node for node in dag["nodes"] if node["node_id"] == "candidate-1_runtime_surface")
    assert runtime_node["owned_changes"] == ["src/platform_tools/materialize_candidate_dags_from_research.py"]
    assert runtime_node["source_research_candidate_id"] == "candidate-1"
    assert dag["edges"]


def test_materialize_candidate_dags_from_research_blocks_missing_ranked_candidate(tmp_path: Path) -> None:
    recommendation = _seed_recommendation(tmp_path)
    evidence = _seed_evidence(tmp_path)

    code, report = materialize_candidate_dags_from_research(
        root=tmp_path.as_posix(),
        research_recommendation_path=recommendation,
        candidate_paths=[],
        evidence_packet_path=evidence,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "research_candidate_packets_missing" in report["blockers"]
