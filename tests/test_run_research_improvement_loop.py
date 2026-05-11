from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import platform_tools.run_research_improvement_loop as loop_mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_run_research_improvement_loop_blocks_on_missing_request(tmp_path: Path) -> None:
    code, report = loop_mod.run_research_improvement_loop(
        root=tmp_path.as_posix(),
        researcher_root=(tmp_path / "researcher").as_posix(),
        request_path=(tmp_path / "missing.json").as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["command"] == "run-research-improvement-loop"
    assert report["status"] == "blocked"
    assert "request_path_missing" in report["blockers"]


def test_run_research_improvement_loop_runs_chain(monkeypatch, tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    _write(request_path, json.dumps({"request_id": "req-1"}))
    output_root = tmp_path / "out"
    researcher_root = tmp_path / "researcher"
    researcher_root.mkdir()

    def fake_run_research_capability(**kwargs):
        assert Path(kwargs["request_path"]).exists()
        return 0, {
            "api_version": "public-orchestration.v1",
            "command": "run-research-capability",
            "status": "ok",
            "ok": True,
            "request_id": "req-1",
            "blockers": [],
        }

    def fake_prepare_research_followups(**kwargs):
        assert Path(kwargs["report_path"]).exists()
        draft_path = output_root / "execution" / "draft_followups" / "req-1.json"
        _write(draft_path, json.dumps({"source_request_id": "req-1"}))
        return 0, {
            "api_version": "public-orchestration.v1",
            "command": "prepare-research-followups",
            "status": "ok",
            "ok": True,
            "draft_followups_path": draft_path.as_posix(),
            "blockers": [],
        }

    def fake_project_research_followup_packets(**kwargs):
        assert Path(kwargs["prepared_followups_path"]).exists()
        packets_path = output_root / "execution" / "repo_followup_packets" / "req-1.json"
        _write(packets_path, json.dumps({"source_request_id": "req-1"}))
        return 0, {
            "api_version": "public-orchestration.v1",
            "command": "project-research-followup-packets",
            "status": "ok",
            "ok": True,
            "packets_path": packets_path.as_posix(),
            "blockers": [],
        }

    def fake_materialize_research_followup_assets(**kwargs):
        assert Path(kwargs["packets_path"]).exists()
        manifest_path = output_root / "execution" / "materialized_followup_assets" / "req-1.json"
        _write(manifest_path, json.dumps({"source_request_id": "req-1"}))
        return 0, {
            "api_version": "public-orchestration.v1",
            "command": "materialize-research-followup-assets",
            "status": "ok",
            "ok": True,
            "manifest_path": manifest_path.as_posix(),
            "blockers": [],
        }

    def fake_render_platform_execplan_drafts(**kwargs):
        assert Path(kwargs["materialized_manifest_path"]).exists()
        draft_manifest_path = output_root / "execution" / "draft_execplan_candidates" / "req-1.manifest.json"
        _write(draft_manifest_path, json.dumps({"source_request_id": "req-1"}))
        return 0, {
            "api_version": "public-orchestration.v1",
            "command": "render-platform-execplan-drafts",
            "status": "ok",
            "ok": True,
            "draft_manifest_path": draft_manifest_path.as_posix(),
            "blockers": [],
        }

    def fake_render_researcher_followup_handoffs(**kwargs):
        assert Path(kwargs["materialized_manifest_path"]).exists()
        handoff_manifest_path = output_root / "execution" / "researcher_handoff_requests" / "req-1.manifest.json"
        _write(handoff_manifest_path, json.dumps({"source_request_id": "req-1"}))
        return 0, {
            "api_version": "public-orchestration.v1",
            "command": "render-researcher-followup-handoffs",
            "status": "ok",
            "ok": True,
            "handoff_manifest_path": handoff_manifest_path.as_posix(),
            "blockers": [],
        }

    monkeypatch.setattr(loop_mod, "run_research_capability", fake_run_research_capability)
    monkeypatch.setattr(loop_mod, "prepare_research_followups", fake_prepare_research_followups)
    monkeypatch.setattr(loop_mod, "project_research_followup_packets", fake_project_research_followup_packets)
    monkeypatch.setattr(loop_mod, "materialize_research_followup_assets", fake_materialize_research_followup_assets)
    monkeypatch.setattr(loop_mod, "render_platform_execplan_drafts", fake_render_platform_execplan_drafts)
    monkeypatch.setattr(loop_mod, "render_researcher_followup_handoffs", fake_render_researcher_followup_handoffs)

    code, report = loop_mod.run_research_improvement_loop(
        root=tmp_path.as_posix(),
        researcher_root=researcher_root.as_posix(),
        request_path=request_path.as_posix(),
        output_root=output_root.as_posix(),
    )

    assert code == 0
    assert report["command"] == "run-research-improvement-loop"
    assert report["status"] == "ok"
    assert len(report["step_reports"]) == 6
    assert Path(report["loop_manifest_path"]).exists()
