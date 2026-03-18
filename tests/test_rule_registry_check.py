from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.rule_registry_check import check_rule_registry


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_repo(root: Path, *, invalid_command: bool = False) -> None:
    _write(root / "docs" / "governance.md", "governance\n")
    _write(root / "spec" / "workflow.yaml", "workflow: true\n")
    _write(root / "bin" / "governance-check", "#!/usr/bin/env bash\n")
    _write(
        root / "pyproject.toml",
        "[project]\nname='x'\nversion='0.1.0'\n[project.scripts]\ngovernance-check='x:y'\n",
    )
    enforcement = "bin/not-a-real-command" if invalid_command else "bin/governance-check"
    _write(
        root / "spec" / "rule-registry.yaml",
        "\n".join(
            [
                "version: v1",
                "registry:",
                "  required_fields: [rule_id, title, class, scope, authority, source_artifacts]",
                "rule_classes: [enforced, derived, human_gated, backlog, deprecated]",
                "rules:",
                "  - rule_id: rule-governance-contract",
                "    title: governance contract",
                "    class: enforced",
                "    scope: governance",
                "    authority: referee",
                "    source_artifacts: [docs/governance.md, spec/workflow.yaml]",
                f"    enforced_by: [{enforcement}]",
                "    graph_required: true",
            ]
        )
        + "\n",
    )


def test_rule_registry_check_passes_for_valid_registry(tmp_path: Path) -> None:
    _seed_repo(tmp_path)
    code, report = check_rule_registry(tmp_path.as_posix())
    assert code == 0
    assert report["ok"] is True
    assert report["errors"] == []


def test_rule_registry_check_fails_for_unknown_enforcement_command(tmp_path: Path) -> None:
    _seed_repo(tmp_path, invalid_command=True)
    code, report = check_rule_registry(tmp_path.as_posix())
    assert code == 1
    assert "unknown_enforcement_command:rule-governance-contract:bin/not-a-real-command" in report["errors"]
