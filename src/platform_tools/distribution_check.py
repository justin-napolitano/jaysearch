from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_pyproject(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def check_distribution() -> tuple[int, dict[str, Any]]:
    spec_path = Path("spec/distribution.yaml")
    spec = _load_yaml(spec_path)
    findings: list[str] = []

    core = spec.get("core_package", {})
    manifest_path = Path(str(core.get("manifest_path", "pyproject.toml")))
    version_key = str(core.get("version_key", "project.version"))
    version_regex = str(core.get("version_regex", r"^\d+\.\d+\.\d+$"))
    registry_path = Path(str(core.get("release_registry_path", ".agent/distribution/releases.yaml")))

    manifest = _load_pyproject(manifest_path)
    manifest_version = ""
    if version_key == "project.version":
        manifest_version = str(
            ((manifest.get("project") or {}) if isinstance(manifest.get("project"), dict) else {}).get("version", "")
        )
    if not manifest_version:
        findings.append("missing_manifest_version")
    elif not re.match(version_regex, manifest_version):
        findings.append("invalid_manifest_version_format")

    registry = _load_yaml(registry_path)
    releases = registry.get("releases", [])
    if not isinstance(releases, list) or not releases:
        findings.append("missing_release_registry_entries")
        releases = []

    active_release = None
    for item in releases:
        if isinstance(item, dict) and str(item.get("status", "")).strip() == "active":
            active_release = item
            break
    if active_release is None:
        findings.append("missing_active_release")
    else:
        active_version = str(active_release.get("version", "")).strip()
        if manifest_version and active_version != manifest_version:
            findings.append("active_release_version_mismatch")

    template = spec.get("template_sync", {})
    required_paths = template.get("required_template_paths", [])
    if not isinstance(required_paths, list) or not required_paths:
        findings.append("missing_required_template_paths")
        required_paths = []

    missing_paths = [p for p in required_paths if not Path(str(p)).exists()]
    if missing_paths:
        findings.extend(f"missing_template_path:{p}" for p in sorted(missing_paths))

    if isinstance(active_release, dict):
        registry_paths = active_release.get("template_paths", [])
        if not isinstance(registry_paths, list):
            findings.append("invalid_active_release_template_paths")
        else:
            if sorted(str(p) for p in registry_paths) != sorted(str(p) for p in required_paths):
                findings.append("active_release_template_paths_mismatch")

    manual = spec.get("manual_update", {})
    required_steps = manual.get("required_steps", [])
    if not isinstance(required_steps, list) or not required_steps:
        findings.append("missing_manual_update_steps")
    else:
        must_have = {
            "create_dedicated_branch",
            "update_release_registry",
            "run_distribution_check",
            "run_run_local_ci",
            "open_reviewable_pr",
            "human_merge",
        }
        missing_steps = sorted(step for step in must_have if step not in required_steps)
        findings.extend(f"missing_manual_update_step:{step}" for step in missing_steps)

    findings = sorted(set(findings))
    report = {
        "tool": "distribution_check",
        "spec_path": spec_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "registry_path": registry_path.as_posix(),
        "manifest_version": manifest_version,
        "release_count": len(releases),
        "finding_count": len(findings),
        "findings": findings,
    }
    return (1 if findings else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    code, report = check_distribution()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
