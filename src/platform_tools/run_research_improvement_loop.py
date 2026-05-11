from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from platform_tools.materialize_research_followup_assets import materialize_research_followup_assets
from platform_tools.prepare_research_followups import prepare_research_followups
from platform_tools.project_research_followup_packets import project_research_followup_packets
from platform_tools.public_orchestration_api import API_VERSION, envelope
from platform_tools.render_platform_execplan_drafts import render_platform_execplan_drafts
from platform_tools.render_researcher_followup_handoffs import render_researcher_followup_handoffs
from platform_tools.run_research_capability import run_research_capability


COMMAND = "run-research-improvement-loop"


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _run_step(
    *,
    output_root: Path,
    source_request_id: str,
    step_name: str,
    runner: Callable[..., tuple[int, dict[str, Any]]],
    kwargs: dict[str, Any],
) -> tuple[int, dict[str, Any], str]:
    code, report = runner(**kwargs)
    report_path = output_root / "execution" / "loop_step_reports" / f"{source_request_id}.{step_name}.json"
    _write_json(report_path, report)
    return code, report, report_path.as_posix()


def _blocked_envelope(
    *,
    platform_root: Path,
    researcher_root: str,
    request_path: Path,
    output_root: Path,
    blockers: list[str],
    failed_step: str = "",
    step_reports: list[dict[str, Any]] | None = None,
) -> tuple[int, dict[str, Any]]:
    return 1, envelope(
        command=COMMAND,
        status="blocked",
        ok=False,
        payload={
            "platform_root": platform_root.as_posix(),
            "researcher_root": str(Path(researcher_root).resolve()) if researcher_root else "",
            "request_path": request_path.as_posix(),
            "output_root": output_root.as_posix(),
            "failed_step": failed_step,
            "step_reports": step_reports or [],
            "blockers": blockers,
        },
    )


def run_research_improvement_loop(
    *,
    root: str = ".",
    researcher_root: str,
    request_path: str,
    output_root: str,
    python_executable: str = "python3",
    max_promotions: int = 3,
    minimum_total_score: float | None = None,
) -> tuple[int, dict[str, Any]]:
    platform_root = Path(root).resolve()
    destination_root = Path(output_root).resolve()
    request_file = Path(request_path).resolve()

    blockers: list[str] = []
    if not str(researcher_root).strip():
        blockers.append("researcher_root_missing")
    if not request_file.exists():
        blockers.append("request_path_missing")
    if not str(output_root).strip():
        blockers.append("output_root_missing")
    if max_promotions < 1:
        blockers.append("max_promotions_invalid")
    if minimum_total_score is not None and minimum_total_score <= 0:
        blockers.append("minimum_total_score_invalid")
    if blockers:
        return _blocked_envelope(
            platform_root=platform_root,
            researcher_root=researcher_root,
            request_path=request_file,
            output_root=destination_root,
            blockers=sorted(set(blockers)),
        )

    source_request_id = request_file.stem
    step_reports: list[dict[str, Any]] = []

    code, research_report, research_report_path = _run_step(
        output_root=destination_root,
        source_request_id=source_request_id,
        step_name="run-research-capability",
        runner=run_research_capability,
        kwargs={
            "root": platform_root.as_posix(),
            "researcher_root": researcher_root,
            "request_path": request_file.as_posix(),
            "python_executable": python_executable,
        },
    )
    source_request_id = str(research_report.get("request_id", "")).strip() or source_request_id
    step_reports.append({"step": "run-research-capability", "report_path": research_report_path, "ok": research_report.get("ok") is True})
    if code != 0:
        return _blocked_envelope(
            platform_root=platform_root,
            researcher_root=researcher_root,
            request_path=request_file,
            output_root=destination_root,
            blockers=research_report.get("blockers", []),
            failed_step="run-research-capability",
            step_reports=step_reports,
        )

    code, prepared_report, prepared_report_path = _run_step(
        output_root=destination_root,
        source_request_id=source_request_id,
        step_name="prepare-research-followups",
        runner=prepare_research_followups,
        kwargs={
            "root": platform_root.as_posix(),
            "report_path": research_report_path,
            "output_root": destination_root.as_posix(),
            "max_promotions": max_promotions,
            "minimum_total_score": minimum_total_score,
        },
    )
    step_reports.append({"step": "prepare-research-followups", "report_path": prepared_report_path, "ok": prepared_report.get("ok") is True})
    if code != 0:
        return _blocked_envelope(
            platform_root=platform_root,
            researcher_root=researcher_root,
            request_path=request_file,
            output_root=destination_root,
            blockers=prepared_report.get("blockers", []),
            failed_step="prepare-research-followups",
            step_reports=step_reports,
        )

    code, projected_report, projected_report_path = _run_step(
        output_root=destination_root,
        source_request_id=source_request_id,
        step_name="project-research-followup-packets",
        runner=project_research_followup_packets,
        kwargs={
            "root": platform_root.as_posix(),
            "prepared_followups_path": str(prepared_report.get("draft_followups_path", "")).strip(),
            "output_root": destination_root.as_posix(),
        },
    )
    step_reports.append({"step": "project-research-followup-packets", "report_path": projected_report_path, "ok": projected_report.get("ok") is True})
    if code != 0:
        return _blocked_envelope(
            platform_root=platform_root,
            researcher_root=researcher_root,
            request_path=request_file,
            output_root=destination_root,
            blockers=projected_report.get("blockers", []),
            failed_step="project-research-followup-packets",
            step_reports=step_reports,
        )

    code, materialized_report, materialized_report_path = _run_step(
        output_root=destination_root,
        source_request_id=source_request_id,
        step_name="materialize-research-followup-assets",
        runner=materialize_research_followup_assets,
        kwargs={
            "root": platform_root.as_posix(),
            "packets_path": str(projected_report.get("packets_path", "")).strip(),
            "output_root": destination_root.as_posix(),
        },
    )
    step_reports.append({"step": "materialize-research-followup-assets", "report_path": materialized_report_path, "ok": materialized_report.get("ok") is True})
    if code != 0:
        return _blocked_envelope(
            platform_root=platform_root,
            researcher_root=researcher_root,
            request_path=request_file,
            output_root=destination_root,
            blockers=materialized_report.get("blockers", []),
            failed_step="materialize-research-followup-assets",
            step_reports=step_reports,
        )

    code, draft_report, draft_report_path = _run_step(
        output_root=destination_root,
        source_request_id=source_request_id,
        step_name="render-platform-execplan-drafts",
        runner=render_platform_execplan_drafts,
        kwargs={
            "root": platform_root.as_posix(),
            "materialized_manifest_path": str(materialized_report.get("manifest_path", "")).strip(),
            "output_root": destination_root.as_posix(),
        },
    )
    step_reports.append({"step": "render-platform-execplan-drafts", "report_path": draft_report_path, "ok": draft_report.get("ok") is True})
    if code != 0:
        return _blocked_envelope(
            platform_root=platform_root,
            researcher_root=researcher_root,
            request_path=request_file,
            output_root=destination_root,
            blockers=draft_report.get("blockers", []),
            failed_step="render-platform-execplan-drafts",
            step_reports=step_reports,
        )

    code, handoff_report, handoff_report_path = _run_step(
        output_root=destination_root,
        source_request_id=source_request_id,
        step_name="render-researcher-followup-handoffs",
        runner=render_researcher_followup_handoffs,
        kwargs={
            "root": platform_root.as_posix(),
            "materialized_manifest_path": str(materialized_report.get("manifest_path", "")).strip(),
            "output_root": destination_root.as_posix(),
        },
    )
    step_reports.append({"step": "render-researcher-followup-handoffs", "report_path": handoff_report_path, "ok": handoff_report.get("ok") is True})
    if code != 0:
        return _blocked_envelope(
            platform_root=platform_root,
            researcher_root=researcher_root,
            request_path=request_file,
            output_root=destination_root,
            blockers=handoff_report.get("blockers", []),
            failed_step="render-researcher-followup-handoffs",
            step_reports=step_reports,
        )

    loop_manifest = {
        "api_version": API_VERSION,
        "source_request_id": source_request_id,
        "request_path": request_file.as_posix(),
        "step_reports": step_reports,
        "draft_followups_path": str(prepared_report.get("draft_followups_path", "")).strip(),
        "packets_path": str(projected_report.get("packets_path", "")).strip(),
        "materialized_manifest_path": str(materialized_report.get("manifest_path", "")).strip(),
        "draft_manifest_path": str(draft_report.get("draft_manifest_path", "")).strip(),
        "handoff_manifest_path": str(handoff_report.get("handoff_manifest_path", "")).strip(),
    }
    loop_manifest_path = _write_json(
        destination_root / "execution" / "research_improvement_loops" / f"{source_request_id}.json",
        loop_manifest,
    )

    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "platform_root": platform_root.as_posix(),
            "researcher_root": str(Path(researcher_root).resolve()),
            "request_path": request_file.as_posix(),
            "output_root": destination_root.as_posix(),
            "request_id": source_request_id,
            "step_reports": step_reports,
            "draft_followups_path": str(prepared_report.get("draft_followups_path", "")).strip(),
            "packets_path": str(projected_report.get("packets_path", "")).strip(),
            "materialized_manifest_path": str(materialized_report.get("manifest_path", "")).strip(),
            "draft_manifest_path": str(draft_report.get("draft_manifest_path", "")).strip(),
            "handoff_manifest_path": str(handoff_report.get("handoff_manifest_path", "")).strip(),
            "loop_manifest_path": loop_manifest_path.as_posix(),
            "next_action": "review_loop_outputs_and_run_external_handoffs",
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--researcher-root", required=True)
    parser.add_argument("--request-path", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--python-executable", default="python3")
    parser.add_argument("--max-promotions", type=int, default=3)
    parser.add_argument("--minimum-total-score", type=float, default=None)
    args = parser.parse_args()
    code, report = run_research_improvement_loop(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
