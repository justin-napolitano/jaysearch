from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.branch_policy import evaluate_branch_policy


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_initiative_branch_requires_parent_graph_node(tmp_path: Path, monkeypatch) -> None:
    _write(
        tmp_path / "spec" / "workflow.yaml",
        "\n".join(
            [
                "execution_requirements:",
                "  initiative_requirements:",
                "    fail_closed_on_missing_initiative_mapping: true",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "ruleset.yaml",
        "execution_constraints:\n  allowed_branch_patterns: [initiative/*]\n",
    )
    _write(tmp_path / "spec" / "governance.yaml", "required_checks: {}\n")
    _write(tmp_path / "project.rules.yaml", "overlay:\n  required_check_names_add: []\n  forbidden_branches_add: []\n  allowed_branch_patterns_remove: []\n")
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps({"nodes": []}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    report = evaluate_branch_policy("initiative/skills-runtime")

    assert report["ok"] is False
    assert "branch_policy_violation:initiative_parent_graph_node_missing" in report["findings"]
