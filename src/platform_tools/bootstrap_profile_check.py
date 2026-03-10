from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

PROFILE_SPEC_PATH = Path("spec/bootstrap-profiles.yaml")
MANIFEST_PATH = Path(".agent/bootstrap-manifest.json")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def check_bootstrap_profile() -> tuple[int, dict[str, Any]]:
    findings: list[str] = []
    spec = _load_yaml(PROFILE_SPEC_PATH)
    default_profile = str(spec.get("default_profile", "full")).strip() or "full"
    profiles = spec.get("profiles", {})
    if not isinstance(profiles, dict):
        profiles = {}

    manifest = _load_manifest(MANIFEST_PATH)
    profile = str(manifest.get("profile", default_profile)).strip() or default_profile
    included = manifest.get("included_paths", [])
    if not isinstance(included, list):
        findings.append("invalid_manifest_included_paths")
        included = []
    included_set = {str(item).strip() for item in included if str(item).strip()}

    profile_cfg = profiles.get(profile, {})
    if not isinstance(profile_cfg, dict):
        findings.append(f"profile_not_found:{profile}")
        profile_cfg = {}
    expected = profile_cfg.get("include", [])
    if not isinstance(expected, list):
        findings.append(f"invalid_profile_include:{profile}")
        expected = []
    expected_set = {str(item).strip() for item in expected if str(item).strip()}

    missing_in_manifest = sorted(expected_set - included_set)
    extra_in_manifest = sorted(included_set - expected_set)
    findings.extend(f"manifest_missing_path:{p}" for p in missing_in_manifest)
    findings.extend(f"manifest_extra_path:{p}" for p in extra_in_manifest)

    for path in sorted(expected_set):
        if not Path(path).exists():
            findings.append(f"missing_profile_path_on_disk:{path}")

    findings = sorted(set(findings))
    report = {
        "tool": "bootstrap_profile_check",
        "profile": profile,
        "manifest_path": MANIFEST_PATH.as_posix(),
        "expected_count": len(expected_set),
        "manifest_count": len(included_set),
        "finding_count": len(findings),
        "findings": findings,
    }
    return (1 if findings else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    code, report = check_bootstrap_profile()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
