from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.review_evidence_adapter import assemble_review_evidence_packet


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_assemble_review_evidence_packet(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "design-review-request.packet.json",
        {
            "packet_type": "design_review_request_packet",
            "packet_version": "v1",
            "packet_id": "drr-001",
            "created_at": "2026-05-21T00:00:00Z",
            "producer": "test",
            "review_id": "review-001",
            "system_scope": "platform-template-bootstrap",
            "artifact_refs": ["docs/design-review-automation-v1.md"],
            "requested_review_modes": ["evidence_backed_claim_review"],
            "requested_outputs": ["evidence_packet"],
            "review_inputs": {
                "evidence_problem_id": "design-review-claims",
                "source_records": [
                    {
                        "source_id": "critic-paper",
                        "title": "CRITIC",
                        "authors": ["Gou et al."],
                        "published_at": "2023-05-19",
                        "source_type": "paper",
                        "uri": "https://arxiv.org/abs/2305.11738",
                        "abstract": "Tool-interactive critique.",
                        "artifact_refs": ["https://arxiv.org/abs/2305.11738"],
                    }
                ],
                "claim_records": [
                    {
                        "claim_id": "claim-001",
                        "source_id": "critic-paper",
                        "claim_text": "Tool-interactive critique improves over unsupported introspection.",
                        "claim_type": "methodological",
                        "evidence_span_refs": ["abstract"],
                        "metric_refs": [],
                    }
                ],
                "method_refs": ["tool-assisted critique"],
                "benchmark_refs": ["design-review workflow"],
                "evidence_summary_text": "Bounded evidence packet for design review.",
            },
        },
    )

    code, report = assemble_review_evidence_packet(
        root=tmp_path.as_posix(),
        request_path="artifacts/design-review-request.packet.json",
        output_root="artifacts/evidence-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    evidence_packet = json.loads(Path(report["evidence_packet_path"]).read_text(encoding="utf-8"))
    assert evidence_packet["packet_type"] == "evidence_packet"
    assert evidence_packet["problem_id"] == "design-review-claims"
    assert evidence_packet["source_refs"] == ["critic-paper"]
    assert evidence_packet["claim_refs"] == ["claim-001"]
