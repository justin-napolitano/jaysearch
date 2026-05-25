from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_research_hypotheses import materialize_research_hypotheses


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_research_problem(root: Path, *, invalid: bool = False) -> str:
    payload = {
        "packet_type": "research_problem_packet",
        "packet_version": "v1",
        "packet_id": "rp-001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "problem_id": "" if invalid else "research-problem:proj-1:rq-1",
        "title": "Research problem for rq-1",
        "goal": "Produce a canonical research problem packet.",
        "problem_statement": "How should the platform transform bounded questions into research input?",
        "constraints": ["local-first", "typed packets"],
        "repo_context": {
            "project_id": "proj-1",
            "decision_target": "build better research runtime"
        },
        "artifact_targets": ["research_problem_packet", "research_hypothesis_packet[]"],
        "evaluation_criteria": ["contract completeness", "traceability"],
        "search_budget": {"max_sources": 5, "max_candidates": 3},
        "output_requirements": ["research_hypothesis_packet[]"],
        "evidence_packet_ref": "artifacts/evidence.packet.json",
        "reference_implementations": ["https://arxiv.org/abs/2305.11738"],
        "source_question_refs": ["artifacts/research-question.packet.json"]
    }
    path = root / "artifacts" / "research-problem.packet.json"
    _write_json(path, payload)
    return "artifacts/research-problem.packet.json"


def test_materialize_research_hypotheses_emits_branch_packets(tmp_path: Path) -> None:
    research_problem_path = _seed_research_problem(tmp_path)
    code, report = materialize_research_hypotheses(
        root=tmp_path.as_posix(),
        research_problem_path=research_problem_path,
        families=["baseline_reference", "reuse_hybrid", "novel_synthesized"],
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["hypothesis_count"] == 3
    packet = json.loads(Path(report["hypothesis_packet_paths"][0]).read_text(encoding="utf-8"))
    assert packet["packet_type"] == "research_hypothesis_packet"
    assert packet["hypothesis_family"] == "baseline_reference"


def test_materialize_research_hypotheses_blocks_invalid_problem(tmp_path: Path) -> None:
    research_problem_path = _seed_research_problem(tmp_path, invalid=True)
    code, report = materialize_research_hypotheses(
        root=tmp_path.as_posix(),
        research_problem_path=research_problem_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "research_problem_missing_problem_id" in report["blockers"]
