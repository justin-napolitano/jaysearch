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


def test_impl_branch_requires_initiative_metadata_by_default(tmp_path: Path, monkeypatch) -> None:
    _write(
        tmp_path / "spec" / "workflow.yaml",
        "\n".join(
            [
                "execution_requirements:",
                "  initiative_requirements:",
                "    fail_closed_on_missing_initiative_mapping: true",
                "    normal_governed_work_requires_initiative_branch: true",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "ruleset.yaml",
        "execution_constraints:\n  allowed_branch_patterns: [impl-execplan/*]\n",
    )
    _write(tmp_path / "spec" / "governance.yaml", "required_checks: {}\n")
    _write(tmp_path / "project.rules.yaml", "overlay:\n  required_check_names_add: []\n  forbidden_branches_add: []\n  allowed_branch_patterns_remove: []\n")
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "rwg-027",
                        "implementation_branch": "impl-execplan/graph-transition",
                        "integration_mode": "",
                        "initiative_branch": "",
                        "parent_initiative_node": "",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    report = evaluate_branch_policy("impl-execplan/graph-transition")

    assert report["ok"] is False
    assert "branch_policy_violation:implementation_integration_mode_missing" in report["findings"]


def test_impl_branch_accepts_via_initiative_mapping(tmp_path: Path, monkeypatch) -> None:
    _write(
        tmp_path / "spec" / "workflow.yaml",
        "\n".join(
            [
                "execution_requirements:",
                "  initiative_requirements:",
                "    fail_closed_on_missing_initiative_mapping: true",
                "    normal_governed_work_requires_initiative_branch: true",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "ruleset.yaml",
        "execution_constraints:\n  allowed_branch_patterns: [impl-execplan/*]\n",
    )
    _write(tmp_path / "spec" / "governance.yaml", "required_checks: {}\n")
    _write(tmp_path / "project.rules.yaml", "overlay:\n  required_check_names_add: []\n  forbidden_branches_add: []\n  allowed_branch_patterns_remove: []\n")
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-graph-transition",
                        "initiative_branch": "initiative/graph-transition",
                        "parent_initiative_node": "initiative-graph-transition",
                    },
                    {
                        "node_id": "rwg-027",
                        "implementation_branch": "impl-execplan/graph-transition",
                        "integration_mode": "via_initiative",
                        "initiative_branch": "initiative/graph-transition",
                        "parent_initiative_node": "initiative-graph-transition",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    report = evaluate_branch_policy("impl-execplan/graph-transition")

    assert report["ok"] is True
    assert report["findings"] == []


def test_impl_branch_rejects_missing_parent_initiative_node(tmp_path: Path, monkeypatch) -> None:
    _write(
        tmp_path / "spec" / "workflow.yaml",
        "\n".join(
            [
                "execution_requirements:",
                "  initiative_requirements:",
                "    fail_closed_on_missing_initiative_mapping: true",
                "    normal_governed_work_requires_initiative_branch: true",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "ruleset.yaml",
        "execution_constraints:\n  allowed_branch_patterns: [impl-execplan/*]\n",
    )
    _write(tmp_path / "spec" / "governance.yaml", "required_checks: {}\n")
    _write(tmp_path / "project.rules.yaml", "overlay:\n  required_check_names_add: []\n  forbidden_branches_add: []\n  allowed_branch_patterns_remove: []\n")
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "rwg-027",
                        "implementation_branch": "impl-execplan/graph-transition",
                        "integration_mode": "via_initiative",
                        "initiative_branch": "initiative/graph-transition",
                        "parent_initiative_node": "initiative-graph-transition",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    report = evaluate_branch_policy("impl-execplan/graph-transition")

    assert report["ok"] is False
    assert "branch_policy_violation:implementation_parent_initiative_not_found" in report["findings"]
