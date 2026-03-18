from __future__ import annotations

import argparse
import json
import shlex
import tomllib
from pathlib import Path
from typing import Any

import yaml


COMMAND = "rule-registry-check"
RULE_ID_PATTERN = "abcdefghijklmnopqrstuvwxyz0123456789-"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _command_surface(root: Path) -> set[str]:
    known: set[str] = set()
    bin_dir = root / "bin"
    if bin_dir.exists():
        known.update(f"bin/{path.name}" for path in bin_dir.iterdir() if path.is_file())

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        scripts = (
            data.get("project", {}).get("scripts", {})
            if isinstance(data.get("project", {}), dict)
            else {}
        )
        if isinstance(scripts, dict):
            known.update(str(name).strip() for name in scripts if str(name).strip())
            known.update(f"bin/{str(name).strip()}" for name in scripts if str(name).strip())
    return known


def _is_canonical_rule_id(rule_id: str) -> bool:
    return bool(rule_id) and all(ch in RULE_ID_PATTERN for ch in rule_id) and "--" not in rule_id


def _first_token(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        return command.strip()
    return parts[0].strip() if parts else ""


def check_rule_registry(root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root)
    registry_path = base / "spec" / "rule-registry.yaml"
    evidence_refs = [registry_path.as_posix()] if registry_path.exists() else []
    errors: list[str] = []

    if not registry_path.exists():
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "error_count": 1,
            "errors": ["missing_rule_registry"],
            "blockers": ["missing_rule_registry"],
            "rule_count": 0,
            "evidence_refs": evidence_refs,
        }
        return 1, report

    registry = _load_yaml(registry_path)
    required_fields = (
        registry.get("registry", {}).get("required_fields", [])
        if isinstance(registry.get("registry", {}), dict)
        else []
    )
    allowed_classes = set(registry.get("rule_classes", []) if isinstance(registry.get("rule_classes", []), list) else [])
    rules = registry.get("rules", [])
    if not isinstance(rules, list):
        rules = []
        errors.append("invalid_rules_collection")

    known_commands = _command_surface(base)
    seen_rule_ids: set[str] = set()

    for item in rules:
        if not isinstance(item, dict):
            errors.append("invalid_rule_entry_type")
            continue
        rule_id = str(item.get("rule_id", "")).strip()
        if not rule_id:
            errors.append("missing_rule_id")
            continue
        if rule_id in seen_rule_ids:
            errors.append(f"duplicate_rule_id:{rule_id}")
        seen_rule_ids.add(rule_id)
        if not _is_canonical_rule_id(rule_id):
            errors.append(f"invalid_rule_id:{rule_id}")

        for field in required_fields:
            value = item.get(field)
            if value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
                errors.append(f"missing_required_field:{rule_id}:{field}")

        rule_class = str(item.get("class", "")).strip()
        if rule_class and rule_class not in allowed_classes:
            errors.append(f"invalid_rule_class:{rule_id}:{rule_class}")

        source_artifacts = item.get("source_artifacts", [])
        if not isinstance(source_artifacts, list):
            errors.append(f"invalid_source_artifacts:{rule_id}")
            source_artifacts = []
        for artifact in source_artifacts:
            artifact_path = str(artifact).strip()
            if artifact_path and not (base / artifact_path).exists():
                errors.append(f"missing_source_artifact:{rule_id}:{artifact_path}")

        enforced_by = item.get("enforced_by", [])
        if not isinstance(enforced_by, list):
            errors.append(f"invalid_enforced_by:{rule_id}")
            enforced_by = []
        if rule_class == "enforced" and not enforced_by:
            errors.append(f"missing_enforced_by:{rule_id}")
        for command in enforced_by:
            command_str = str(command).strip()
            if not command_str:
                errors.append(f"empty_enforced_by:{rule_id}")
                continue
            token = _first_token(command_str)
            if token.startswith("bin/") and token not in known_commands:
                errors.append(f"unknown_enforcement_command:{rule_id}:{token}")
            elif token and not token.startswith("bin/") and token not in known_commands:
                errors.append(f"unknown_enforcement_command:{rule_id}:{token}")

    report = {
        "command": COMMAND,
        "status": "ok" if not errors else "blocked",
        "ok": not errors,
        "error_count": len(errors),
        "errors": sorted(errors),
        "blockers": sorted(errors),
        "rule_count": len(rules),
        "evidence_refs": evidence_refs,
    }
    return (1 if errors else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = check_rule_registry(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
