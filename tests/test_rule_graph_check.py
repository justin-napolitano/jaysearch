from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.rule_graph_check import check_rule_graph


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_repo(root: Path, *, missing_rule: bool = False) -> None:
    _write_text(
        root / "spec" / "rule-graph.schema.yaml",
        "\n".join(
            [
                "graph:",
                "  required_fields:",
                "    - graph_id",
                "    - created_at",
                "    - nodes",
                "    - edges",
                "node:",
                "  required_fields:",
                "    - id",
                "    - type",
                "    - label",
                "    - title",
                "  type_allowed:",
                "    - rule",
                "    - artifact",
                "    - validator",
                "    - phase",
                "    - authority",
                "    - exception",
                "edge:",
                "  required_fields:",
                "    - from",
                "    - to",
                "    - relation",
                "  relation_allowed:",
                "    - applies_to",
                "    - enforced_by",
                "    - requires",
                "    - blocks",
                "    - overrides",
                "    - depends_on",
                "    - satisfied_by",
                "    - exception_for",
            ]
        )
        + "\n",
    )
    _write_text(root / "docs/agent-game-rules-v1.md", "rules\n")
    _write_text(root / "docs/governance.md", "gov\n")
    _write_text(root / "spec/governance.yaml", "gov: true\n")
    _write_text(root / "spec/ruleset.yaml", "ruleset: true\n")
    _write_text(root / "spec/workflow.yaml", "workflow: true\n")
    _write_text(root / "bin/execplan-validate", "#!/usr/bin/env bash\n")
    _write_text(root / "bin/run-local-ci", "#!/usr/bin/env bash\n")
    rule_nodes = [
        {"id": "rule-smoke-test-required", "type": "rule", "label": "smoke", "title": "smoke"},
        {"id": "rule-clean-merge-state", "type": "rule", "label": "clean", "title": "clean"},
        {"id": "rule-human-sized-commits", "type": "rule", "label": "commit", "title": "commit"},
        {"id": "rule-execplan-validation", "type": "rule", "label": "execplan", "title": "execplan"},
        {"id": "rule-human-finalization", "type": "rule", "label": "human", "title": "human"},
        {"id": "artifact-agent-game-rules", "type": "artifact", "label": "rules", "title": "docs/agent-game-rules-v1.md"},
        {"id": "artifact-governance-doc", "type": "artifact", "label": "gov", "title": "docs/governance.md"},
        {"id": "artifact-governance-spec", "type": "artifact", "label": "govspec", "title": "spec/governance.yaml"},
        {"id": "artifact-ruleset-spec", "type": "artifact", "label": "rulespec", "title": "spec/ruleset.yaml"},
        {"id": "artifact-workflow-spec", "type": "artifact", "label": "work", "title": "spec/workflow.yaml"},
        {"id": "validator-execplan-validate", "type": "validator", "label": "execval", "title": "bin/execplan-validate"},
        {"id": "validator-smoke-test", "type": "validator", "label": "smokeval", "title": "bin/run-local-ci"},
        {"id": "phase-merge-readiness", "type": "phase", "label": "merge", "title": "merge"},
        {"id": "authority-human", "type": "authority", "label": "human", "title": "human"},
    ]
    if missing_rule:
        rule_nodes = [node for node in rule_nodes if node["id"] != "rule-clean-merge-state"]
    _write_json(
        root / "artifacts" / "planner" / "research" / "rule-graph.json",
        {
            "graph_id": "rg1",
            "created_at": "2026-03-10T00:00:00Z",
            "nodes": rule_nodes,
            "edges": [
                {"from": "rule-smoke-test-required", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-smoke-test-required", "to": "validator-smoke-test", "relation": "enforced_by"},
                {"from": "rule-clean-merge-state", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-clean-merge-state", "to": "artifact-governance-doc", "relation": "satisfied_by"},
                {"from": "rule-human-sized-commits", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-human-sized-commits", "to": "artifact-governance-doc", "relation": "satisfied_by"},
                {"from": "rule-execplan-validation", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-execplan-validation", "to": "validator-execplan-validate", "relation": "enforced_by"},
                {"from": "rule-human-finalization", "to": "authority-human", "relation": "requires"},
                {"from": "rule-human-finalization", "to": "artifact-ruleset-spec", "relation": "satisfied_by"},
            ],
        },
    )


def test_rule_graph_check_passes_for_valid_graph(tmp_path: Path) -> None:
    _seed_repo(tmp_path)
    code, report = check_rule_graph(tmp_path.as_posix())
    assert code == 0
    assert report["ok"] is True


def test_rule_graph_check_fails_for_missing_required_rule(tmp_path: Path) -> None:
    _seed_repo(tmp_path, missing_rule=True)
    code, report = check_rule_graph(tmp_path.as_posix())
    assert code == 1
    assert any("missing_required_rule:rule-clean-merge-state" == err for err in report["errors"])
