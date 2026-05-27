from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.run_jaysearch_demo import run_jaysearch_demo  # noqa: E402


def test_jaysearch_demo_emits_report_summary_and_execution_units(tmp_path: Path) -> None:
    code, report = run_jaysearch_demo(root=tmp_path.as_posix(), include_era_smoke=True)

    assert code == 0
    assert report["ok"] is True
    assert report["selected_candidate_id"] == "compact"
    assert set(report["rejected_candidate_ids"]) == {"over_split", "cycle"}
    assert len(report["execution_unit_paths"]) == 3
    assert report["era_smoke_status"] == "ok"

    demo_report = json.loads(Path(report["demo_report_path"]).read_text(encoding="utf-8"))
    assert demo_report["explicit_non_claims"] == [
        "no autonomous code synthesis",
        "no source worktree patch application",
        "fixture-backed demo inputs",
    ]
    summary = Path(report["demo_summary_path"]).read_text(encoding="utf-8")
    assert "Jaysearch Demo Summary" in summary
    assert "Selected candidate: `compact`" in summary


def test_jaysearch_demo_can_skip_era_smoke(tmp_path: Path) -> None:
    code, report = run_jaysearch_demo(root=tmp_path.as_posix(), include_era_smoke=False)

    assert code == 0
    assert report["ok"] is True
    assert report["era_smoke_status"] == "skipped"
    assert report["era_smoke_report_path"] == ""
