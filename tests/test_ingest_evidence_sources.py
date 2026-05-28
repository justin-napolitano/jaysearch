from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.ingest_evidence_sources import ingest_evidence_sources


def _load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_ingest_evidence_sources_accepts_file_url_and_emits_packets(tmp_path: Path) -> None:
    source = tmp_path / "source.html"
    source.write_text(
        """
        <html>
          <head><title>Workflow DAGs</title></head>
          <body>
            <h1>Workflow DAGs</h1>
            <p>A directed acyclic graph represents tasks and dependencies in a workflow system.</p>
            <p>Topological ordering helps determine which graph nodes can run after their dependencies complete.</p>
            <p>Provenance records should preserve generated artifacts, used sources, and responsible agents.</p>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    code, report = ingest_evidence_sources(
        root=tmp_path.as_posix(),
        question="How should Jaysearch structure workflow graphs?",
        urls=[source.as_uri()],
        output_root="runs",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert len(report["source_record_refs"]) == 1
    assert len(report["accepted_source_refs"]) == 1
    assert report["rejected_source_refs"] == []

    source_record = _load(report["source_record_refs"][0])
    assert source_record["packet_type"] == "source_record"
    assert source_record["accepted"] is True
    assert source_record["retrieval_status"] == "retrieved"

    claim_set = _load(report["claim_records_path"])
    assert claim_set["packet_type"] == "claim_record_set"
    assert claim_set["claim_count"] >= 1
    assert all(claim["source_id"] == source_record["source_id"] for claim in claim_set["claim_records"])

    evidence = _load(report["evidence_packet_path"])
    assert evidence["packet_type"] == "evidence_packet"
    assert evidence["accepted_source_refs"] == report["accepted_source_refs"]
    assert evidence["claim_record_refs"] == [report["claim_records_path"]]


def test_ingest_evidence_sources_preserves_failed_sources(tmp_path: Path) -> None:
    missing = tmp_path / "missing.html"

    code, report = ingest_evidence_sources(
        root=tmp_path.as_posix(),
        question="What sources support this design?",
        urls=[missing.as_uri()],
        output_root="runs",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["accepted_source_refs"] == []
    assert len(report["rejected_source_refs"]) == 1
    assert "no_sources_accepted" in report["blockers"]

    source_record = _load(report["source_record_refs"][0])
    assert source_record["packet_type"] == "source_record"
    assert source_record["accepted"] is False
    assert source_record["retrieval_status"] == "failed"
    assert source_record["rejection_reasons"]


def test_ingest_evidence_sources_blocks_without_question_or_urls(tmp_path: Path) -> None:
    code, report = ingest_evidence_sources(
        root=tmp_path.as_posix(),
        question="",
        urls=[],
        output_root="runs",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["blockers"] == ["question_required", "url_required"]
