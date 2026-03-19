from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools import bootstrap_managed_repo as bootstrap


def test_bootstrap_managed_repo_writes_lightweight_repo_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "execute_bootstrap",
        lambda **_: (
            0,
            {
                "command": "github-projects-bootstrap",
                "ok": True,
                "status": "ok",
                "dry_run": True,
                "field_map_preview": {
                    "project_id": "pending:project_id",
                    "fields": {
                        "title": {"field_id": "builtin:title", "data_type": "title"},
                        "completion_pr": {"field_id": "pending:completion_pr", "data_type": "text"},
                    },
                    "item_ids_by_node_id": {},
                },
            },
        ),
    )

    code, report = bootstrap.bootstrap_managed_repo(
        root=tmp_path.as_posix(),
        repo_name="Jayrun",
        owner="JNA31A_AIT",
        owner_type="organization",
    )

    assert code == 0
    assert report["ok"] is True
    assert (tmp_path / "spec" / "workflow.yaml").exists()
    assert (tmp_path / ".agent" / "execplans").is_dir()
    assert (tmp_path / "docs" / "queued-execplans.md").exists()
    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    assert graph["nodes"][0]["node_id"] == "initiative-jayrun-foundation"
    field_map = json.loads((tmp_path / "artifacts" / "provider-sync" / "github-projects-field-map.json").read_text(encoding="utf-8"))
    assert field_map["fields"]["completion_pr"]["data_type"] == "text"
    assert report["provider_bootstrap"]["dry_run"] is True

