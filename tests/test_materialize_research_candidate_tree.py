from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_research_candidate_tree import materialize_research_candidate_tree


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_problem(
    root: Path,
    *,
    problem_id: str = "research-problem:proj-1:rq-1",
    problem_statement: str = "How should candidates be generated?",
    artifact_targets: list[str] | None = None,
) -> str:
    payload = {
        "packet_type": "research_problem_packet",
        "packet_version": "v1",
        "packet_id": "rp-001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "problem_id": problem_id,
        "title": "Research problem",
        "goal": "Generate candidates",
        "problem_statement": problem_statement,
        "constraints": ["bounded"],
        "repo_context": {"project_id": "proj-1"},
        "artifact_targets": artifact_targets or ["research_candidate_packet[]"],
        "evaluation_criteria": ["traceability"],
        "search_budget": {"max_candidates": 3},
        "output_requirements": ["research_candidate_packet[]"],
    }
    path = root / "artifacts" / "research-problem.packet.json"
    _write_json(path, payload)
    return "artifacts/research-problem.packet.json"


def _seed_hypothesis(root: Path, *, index: int, family: str, problem_id: str = "research-problem:proj-1:rq-1") -> str:
    payload = {
        "packet_type": "research_hypothesis_packet",
        "packet_version": "v1",
        "packet_id": f"hyp-{index}:packet",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "hypothesis_id": f"{problem_id}:hypothesis:{family}",
        "problem_id": problem_id,
        "hypothesis_family": family,
        "hypothesis_statement": f"Try {family}",
        "approach_outline": f"Use {family}",
        "evaluation_focus": ["traceability"],
        "evidence_refs": ["artifacts/evidence.packet.json"],
        "branch_rank": index,
        "prune_conditions": ["fails validation"],
        "constraints": ["bounded"],
        "risk_notes": ["risk"],
    }
    path = root / "artifacts" / f"hypothesis-{index}.packet.json"
    _write_json(path, payload)
    return f"artifacts/hypothesis-{index}.packet.json"


def test_materialize_research_candidate_tree_emits_tree_candidates_and_decisions(tmp_path: Path) -> None:
    problem_path = _seed_problem(tmp_path)
    hypothesis_paths = [
        _seed_hypothesis(tmp_path, index=1, family="baseline_reference"),
        _seed_hypothesis(tmp_path, index=2, family="reuse_hybrid"),
    ]

    code, report = materialize_research_candidate_tree(
        root=tmp_path.as_posix(),
        research_problem_path=problem_path,
        hypothesis_paths=hypothesis_paths,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["candidate_count"] == 2
    tree = json.loads(Path(report["candidate_search_tree_path"]).read_text(encoding="utf-8"))
    candidate = json.loads(Path(report["candidate_packet_paths"][0]).read_text(encoding="utf-8"))
    decision = json.loads(Path(report["expansion_decision_packet_paths"][0]).read_text(encoding="utf-8"))
    assert tree["packet_type"] == "candidate_search_tree_packet"
    assert candidate["packet_type"] == "research_candidate_packet"
    assert candidate["source_hypothesis_id"].endswith("baseline_reference")
    assert candidate["implementation_intent"]["summary"]
    assert candidate["contract_changes"]
    assert candidate["runtime_changes"]
    assert candidate["validation_changes"]
    assert candidate["expected_changes"]
    assert candidate["handoff_requirements"]
    assert decision["packet_type"] == "candidate_expansion_decision_packet"


def test_materialize_research_candidate_tree_emits_evaluation_strength_intent(tmp_path: Path) -> None:
    problem_id = "evaluation-strength-contract-001"
    problem_path = _seed_problem(
        tmp_path,
        problem_id=problem_id,
        problem_statement="Define evaluation strength for research evaluation packets.",
    )
    hypothesis_path = _seed_hypothesis(
        tmp_path,
        index=1,
        family="baseline_reference",
        problem_id=problem_id,
    )

    code, report = materialize_research_candidate_tree(
        root=tmp_path.as_posix(),
        research_problem_path=problem_path,
        hypothesis_paths=[hypothesis_path],
    )

    assert code == 0
    candidate = json.loads(Path(report["candidate_packet_paths"][0]).read_text(encoding="utf-8"))
    assert "add evaluation_strength to research_evaluation_packet" in candidate["contract_changes"]
    assert "propagate evaluation_strength into recommendation ranking" in candidate["runtime_changes"]
    assert any("static-only evidence" in item for item in candidate["validation_changes"])


def test_materialize_research_candidate_tree_emits_evidence_search_intent(tmp_path: Path) -> None:
    problem_id = "evidence-search-runtime-001"
    problem_path = _seed_problem(
        tmp_path,
        problem_id=problem_id,
        problem_statement="Build evidence search runtime with ranked accepted and rejected sources.",
    )
    hypothesis_path = _seed_hypothesis(
        tmp_path,
        index=1,
        family="reuse_hybrid",
        problem_id=problem_id,
    )

    code, report = materialize_research_candidate_tree(
        root=tmp_path.as_posix(),
        research_problem_path=problem_path,
        hypothesis_paths=[hypothesis_path],
    )

    assert code == 0
    candidate = json.loads(Path(report["candidate_packet_paths"][0]).read_text(encoding="utf-8"))
    assert "add source_record contract" in candidate["contract_changes"]
    assert "emit evidence_packet from ranked source records" in candidate["runtime_changes"]
    assert any("rejected-source traceability" in item for item in candidate["validation_changes"])


def test_materialize_research_candidate_tree_blocks_problem_mismatch(tmp_path: Path) -> None:
    problem_path = _seed_problem(tmp_path)
    hypothesis_path = _seed_hypothesis(
        tmp_path,
        index=1,
        family="baseline_reference",
        problem_id="other-problem",
    )

    code, report = materialize_research_candidate_tree(
        root=tmp_path.as_posix(),
        research_problem_path=problem_path,
        hypothesis_paths=[hypothesis_path],
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "research_hypothesis_problem_mismatch:1" in report["blockers"]
