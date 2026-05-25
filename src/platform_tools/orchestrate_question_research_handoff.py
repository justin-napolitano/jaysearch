from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.question_to_research_problem_transform import materialize_research_problem
from platform_tools.research_questions import write_json


COMMAND = "orchestrate-question-research-handoff"
DEFAULT_OUTPUT_ROOT = Path("artifacts/orchestration/question-research-handoff-runs")


def run_question_research_handoff_workflow(
    *,
    root: str = ".",
    research_question_path: str,
    evidence_packet_path: str | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    run_root = repo_root / output_root
    run_root.mkdir(parents=True, exist_ok=True)
    step_reports: list[dict[str, Any]] = []

    transform_code, transform_report = materialize_research_problem(
        root=root,
        research_question_path=research_question_path,
        evidence_packet_path=evidence_packet_path,
        output_root=output_root,
    )
    step_reports.append(
        {
            "step": "materialize_research_problem",
            "status": str(transform_report.get("status", "")).strip(),
            "ok": transform_report.get("ok") is True,
            "report": transform_report,
        }
    )
    if transform_code != 0 or transform_report.get("ok") is not True:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "research_question_path": research_question_path,
                "evidence_packet_path": evidence_packet_path or "",
                "step_reports": step_reports,
                "blockers": transform_report.get("blockers", []),
            },
        )
        write_json(run_root / "question-research-handoff.report.json", report)
        return 1, report

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "research_question_path": research_question_path,
            "evidence_packet_path": evidence_packet_path or "",
            "research_problem_path": transform_report.get("research_problem_path", ""),
            "transform_packet_path": transform_report.get("transform_packet_path", ""),
            "step_reports": step_reports,
            "blockers": [],
        },
    )
    write_json(run_root / "question-research-handoff.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--research-question-path", required=True)
    parser.add_argument("--evidence-packet-path", default=None)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = run_question_research_handoff_workflow(
            root=args.root,
            research_question_path=args.research_question_path,
            evidence_packet_path=args.evidence_packet_path,
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
