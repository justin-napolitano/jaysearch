from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "review-evidence-adapter"
DEFAULT_OUTPUT_ROOT = Path("artifacts/evidence/review-adapter-runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("rea-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _clean_records(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def assemble_review_evidence_packet(
    *,
    root: str = ".",
    request_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    request = _load_json(repo_root / request_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    review_id = str(request.get("review_id", "")).strip() or run_id
    review_inputs = request.get("review_inputs", {})
    if not isinstance(review_inputs, dict):
        review_inputs = {}

    problem_id = str(review_inputs.get("evidence_problem_id", review_id)).strip() or review_id
    source_records = _clean_records(review_inputs.get("source_records", []))
    claim_records = _clean_records(review_inputs.get("claim_records", []))
    benchmark_refs = [str(item).strip() for item in review_inputs.get("benchmark_refs", []) if str(item).strip()]
    method_refs = [str(item).strip() for item in review_inputs.get("method_refs", []) if str(item).strip()]
    blockers: list[str] = []

    if not source_records:
        blockers.append("source_records_missing")
    if not claim_records:
        blockers.append("claim_records_missing")

    source_refs = [str(item.get("source_id", "")).strip() for item in source_records if str(item.get("source_id", "")).strip()]
    claim_refs = [str(item.get("claim_id", "")).strip() for item in claim_records if str(item.get("claim_id", "")).strip()]

    evidence_packet = {
        "packet_type": "evidence_packet",
        "packet_version": "v1",
        "packet_id": f"{run_id}:evidence",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "problem_id": problem_id,
        "source_refs": source_refs,
        "claim_refs": claim_refs,
        "method_refs": method_refs,
        "benchmark_refs": benchmark_refs,
        "evidence_summary": {
            "review_id": review_id,
            "source_count": len(source_refs),
            "claim_count": len(claim_refs),
            "summary_text": str(review_inputs.get("evidence_summary_text", "Review evidence assembled from bounded request records.")).strip()
            or "Review evidence assembled from bounded request records.",
        },
    }
    evidence_packet_path = write_json(run_root / "evidence.packet.json", evidence_packet)

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "request_path": str((repo_root / request_path).resolve()),
            "evidence_packet_path": evidence_packet_path.as_posix(),
            "source_count": len(source_refs),
            "claim_count": len(claim_refs),
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "review-evidence-adapter.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--request", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = assemble_review_evidence_packet(
            root=args.root,
            request_path=args.request,
            output_root=args.output_root,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
