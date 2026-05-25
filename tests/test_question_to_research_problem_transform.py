from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.question_to_research_problem_transform import materialize_research_problem


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_question(root: Path, *, omit_decision_target: bool = False) -> str:
    payload = {
        "packet_type": "research_question_packet",
        "packet_version": "v1",
        "packet_id": "rq-packet-001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "question_id": "rq-001",
        "project_id": "proj-1",
        "question_text": "How should we transform a bounded research question into research-tool input?",
        "question_type": "implementation_strategy",
        "goal": "Produce a bounded research problem packet.",
        "constraints": ["local-first", "typed packets"],
        "evaluation_targets": ["contract completeness", "traceability"],
        "artifact_targets": ["research_problem_packet", "question_to_research_problem_transform"],
        "decision_target": "" if omit_decision_target else "build transform tool",
        "decision_consequence": "changes whether upstream orchestration can hand off into research",
        "blocked_work_if_unanswered": "cannot safely build the upstream question/evidence/research bridge",
    }
    path = root / "artifacts" / "research-question.packet.json"
    _write_json(path, payload)
    return "artifacts/research-question.packet.json"


def _seed_evidence(root: Path) -> str:
    payload = {
        "packet_type": "evidence_packet",
        "packet_version": "v1",
        "packet_id": "ev-001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "problem_id": "rq-001",
        "source_refs": ["https://arxiv.org/abs/2305.11738"],
        "claim_refs": ["tool-assisted critique is stronger than unsupported introspection"],
        "method_refs": ["tool-assisted critique"],
        "benchmark_refs": ["question-to-evidence-to-research handoff review"],
        "evidence_summary": "Bounded evidence summary.",
    }
    path = root / "artifacts" / "evidence.packet.json"
    _write_json(path, payload)
    return "artifacts/evidence.packet.json"


def test_materialize_research_problem_emits_problem_and_transform_packets(tmp_path: Path) -> None:
    question_path = _seed_question(tmp_path)
    evidence_path = _seed_evidence(tmp_path)

    code, report = materialize_research_problem(
        root=tmp_path.as_posix(),
        research_question_path=question_path,
        evidence_packet_path=evidence_path,
    )

    assert code == 0
    assert report["status"] == "ok"
    research_problem = json.loads(Path(report["research_problem_path"]).read_text(encoding="utf-8"))
    transform_packet = json.loads(Path(report["transform_packet_path"]).read_text(encoding="utf-8"))
    assert research_problem["packet_type"] == "research_problem_packet"
    assert research_problem["repo_context"]["decision_target"] == "build transform tool"
    assert transform_packet["packet_type"] == "question_to_research_problem_transform"


def test_materialize_research_problem_blocks_missing_decision_target(tmp_path: Path) -> None:
    question_path = _seed_question(tmp_path, omit_decision_target=True)
    evidence_path = _seed_evidence(tmp_path)

    code, report = materialize_research_problem(
        root=tmp_path.as_posix(),
        research_question_path=question_path,
        evidence_packet_path=evidence_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "research_question_missing_decision_target" in report["blockers"]
