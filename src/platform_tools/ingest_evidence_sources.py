from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "ingest-evidence-sources"
DEFAULT_OUTPUT_ROOT = Path("artifacts/evidence-source-ingest/runs")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._in_title:
            self.title_parts.append(cleaned)
        if not self._skip_depth:
            self.text_parts.append(cleaned)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return " ".join(self.text_parts).strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("esi-%Y%m%dT%H%M%SZ")


def _slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or fallback


def _read_url(uri: str, *, timeout_seconds: int) -> tuple[str, str, str]:
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        path = Path(parsed.path)
        return path.read_text(encoding="utf-8"), "retrieved", ""
    if parsed.scheme in {"http", "https"}:
        request = Request(uri, headers={"User-Agent": "jaysearch-evidence-source-ingest/1.0"})
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            return raw.decode(encoding, errors="replace"), "retrieved", ""
    if parsed.scheme == "":
        path = Path(uri)
        return path.read_text(encoding="utf-8"), "retrieved", ""
    return "", "failed", f"unsupported_url_scheme:{parsed.scheme}"


def _normalize_text(raw_text: str) -> tuple[str, str]:
    parser = _TextExtractor()
    try:
        parser.feed(raw_text)
    except Exception:
        return "", " ".join(raw_text.split())
    extracted = parser.text or " ".join(raw_text.split())
    return parser.title, extracted


def _sentences(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    candidates = re.split(r"(?<=[.!?])\s+", normalized)
    return [item.strip() for item in candidates if len(item.strip()) >= 40]


def _claim_type(sentence: str) -> str:
    lowered = sentence.lower()
    if any(term in lowered for term in ["dag", "dependency", "topological", "acyclic", "graph"]):
        return "workflow_graph_structure"
    if any(term in lowered for term in ["provenance", "derived", "generated", "used", "agent"]):
        return "lineage_provenance"
    if any(term in lowered for term in ["reproduc", "workflow", "execution"]):
        return "workflow_reproducibility"
    return "source_summary"


def _extract_claims(*, source_id: str, text: str, max_claims: int) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for index, sentence in enumerate(_sentences(text)[:max_claims], start=1):
        claim_id = f"{source_id}:claim:{index:02d}"
        claims.append(
            {
                "packet_type": "claim_record",
                "packet_version": "v1",
                "claim_id": claim_id,
                "source_id": source_id,
                "claim_text": sentence[:700],
                "claim_type": _claim_type(sentence),
                "evidence_span_ref": f"{source_id}:span:{index:02d}",
                "extraction_status": "extracted",
                "limitations": [
                    "deterministic_sentence_extraction_v1",
                    "claim requires human review before being treated as authoritative",
                ],
            }
        )
    return claims


def _source_quality(uri: str, retrieval_status: str, text: str) -> tuple[bool, list[str], list[str]]:
    if retrieval_status != "retrieved":
        return False, [], ["source_not_retrieved"]
    reasons: list[str] = []
    rejections: list[str] = []
    parsed = urlparse(uri)
    if parsed.scheme in {"http", "https", "file", ""}:
        reasons.append("supported_source_scheme")
    if len(text) >= 300:
        reasons.append("sufficient_extracted_text")
    else:
        rejections.append("insufficient_extracted_text")
    return not rejections, reasons, rejections


def ingest_evidence_sources(
    *,
    root: str = ".",
    question: str,
    urls: list[str],
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    max_claims_per_source: int = 4,
    timeout_seconds: int = 15,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    clean_question = question.strip()
    clean_urls = [url.strip() for url in urls if url.strip()]
    if not clean_question:
        blockers.append("question_required")
    if not clean_urls:
        blockers.append("url_required")
    if max_claims_per_source < 1:
        blockers.append("max_claims_per_source_invalid")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"run_id": run_id, "blockers": sorted(set(blockers))},
        )
        write_json(run_root / "ingest.report.json", report)
        return 1, report

    created_at = _utc_now()
    source_record_refs: list[str] = []
    accepted_source_refs: list[str] = []
    rejected_source_refs: list[str] = []
    all_claims: list[dict[str, Any]] = []

    for index, uri in enumerate(clean_urls, start=1):
        source_id = f"source-{index:02d}-{_slug(uri, f'url-{index:02d}')}"
        try:
            raw_text, retrieval_status, retrieval_error = _read_url(uri, timeout_seconds=timeout_seconds)
        except (OSError, URLError, TimeoutError, ValueError) as exc:
            raw_text = ""
            retrieval_status = "failed"
            retrieval_error = f"{type(exc).__name__}:{exc}"

        title, extracted_text = _normalize_text(raw_text)
        accepted, acceptance_reasons, rejection_reasons = _source_quality(uri, retrieval_status, extracted_text)
        if retrieval_error:
            rejection_reasons.append(retrieval_error[:300])
        summary = extracted_text[:900]
        source_record = {
            "packet_type": "source_record",
            "packet_version": "v1",
            "source_id": source_id,
            "question": clean_question,
            "uri": uri,
            "retrieval_status": retrieval_status,
            "source_type": "url",
            "title": title or uri,
            "summary": summary,
            "accepted": accepted,
            "acceptance_reasons": acceptance_reasons,
            "rejection_reasons": rejection_reasons,
            "retrieved_at": created_at,
        }
        source_path = write_json(run_root / f"source-record-{index:02d}.packet.json", source_record)
        source_ref = source_path.as_posix()
        source_record_refs.append(source_ref)
        if accepted:
            accepted_source_refs.append(source_ref)
            all_claims.extend(
                _extract_claims(
                    source_id=source_id,
                    text=extracted_text,
                    max_claims=max_claims_per_source,
                )
            )
        else:
            rejected_source_refs.append(source_ref)

    claim_records_packet = {
        "packet_type": "claim_record_set",
        "packet_version": "v1",
        "packet_id": f"{run_id}:claim-records",
        "created_at": created_at,
        "producer": COMMAND,
        "question": clean_question,
        "claim_records": all_claims,
        "claim_count": len(all_claims),
    }
    claim_records_path = write_json(run_root / "claim-records.packet.json", claim_records_packet)

    evidence_packet = {
        "packet_type": "evidence_packet",
        "packet_version": "v1",
        "evidence_packet_id": f"{run_id}:evidence",
        "created_at": created_at,
        "producer": COMMAND,
        "question": clean_question,
        "source_record_refs": source_record_refs,
        "accepted_source_refs": accepted_source_refs,
        "rejected_source_refs": rejected_source_refs,
        "claim_record_refs": [claim_records_path.as_posix()],
        "evidence_summary": (
            f"Ingested {len(source_record_refs)} source(s), accepted {len(accepted_source_refs)}, "
            f"rejected {len(rejected_source_refs)}, extracted {len(all_claims)} claim(s)."
        ),
        "limitations": [
            "V1 ingests explicit URLs only; search automation is out of scope.",
            "Claim extraction is deterministic and conservative; claims require review before final design authority.",
        ],
    }
    evidence_path = write_json(run_root / "evidence.packet.json", evidence_packet)

    status = "ok" if accepted_source_refs else "blocked"
    if not accepted_source_refs:
        blockers.append("no_sources_accepted")
    report = envelope(
        command=COMMAND,
        status=status,
        ok=status == "ok",
        payload={
            "run_id": run_id,
            "question": clean_question,
            "source_record_refs": source_record_refs,
            "accepted_source_refs": accepted_source_refs,
            "rejected_source_refs": rejected_source_refs,
            "claim_records_path": claim_records_path.as_posix(),
            "evidence_packet_path": evidence_path.as_posix(),
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "ingest.report.json", report)
    return (0 if status == "ok" else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--question", required=True)
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--max-claims-per-source", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=15)
    args = parser.parse_args()
    code, report = ingest_evidence_sources(
        root=args.root,
        question=args.question,
        urls=args.url,
        output_root=args.output_root,
        max_claims_per_source=args.max_claims_per_source,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
