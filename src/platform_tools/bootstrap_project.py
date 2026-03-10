from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import yaml

PROFILE_SPEC_PATH = Path("spec/bootstrap-profiles.yaml")
MANIFEST_RELATIVE_PATH = Path(".agent/bootstrap-manifest.json")


def _load_profiles() -> tuple[str, dict[str, list[str]]]:
    if not PROFILE_SPEC_PATH.exists():
        return "full", {}
    data = yaml.safe_load(PROFILE_SPEC_PATH.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return "full", {}
    default_profile = str(data.get("default_profile", "full")).strip() or "full"
    raw_profiles = data.get("profiles", {})
    profiles: dict[str, list[str]] = {}
    if isinstance(raw_profiles, dict):
        for name, cfg in raw_profiles.items():
            if not isinstance(cfg, dict):
                continue
            include = cfg.get("include", [])
            if isinstance(include, list):
                dedup = sorted({str(item).strip() for item in include if str(item).strip()})
                profiles[str(name).strip()] = dedup
    return default_profile, profiles


def _copy_path(src: Path, dst: Path, force: bool) -> tuple[bool, str]:
    if src.is_dir():
        if dst.exists() and not force:
            return False, "exists"
        shutil.copytree(src, dst, dirs_exist_ok=force)
        return True, "copied"
    if src.is_file():
        if dst.exists() and not force:
            return False, "exists"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True, "copied"
    return False, "missing_source"


def _write_manifest(project_dir: Path, profile: str, included_paths: list[str]) -> None:
    manifest = {
        "tool": "bootstrap_project",
        "schema_version": "v1",
        "profile": profile,
        "included_paths": sorted(included_paths),
    }
    manifest_path = project_dir / MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bootstrap_project(
    destination: str,
    project_name: str | None = None,
    profile: str | None = None,
    force: bool = False,
) -> tuple[int, dict[str, Any]]:
    default_profile, profiles = _load_profiles()
    selected_profile = profile or default_profile
    selected_paths = profiles.get(selected_profile, [])
    if not selected_paths:
        return 1, {
            "tool": "bootstrap_project",
            "ok": False,
            "reason": "invalid_profile",
            "profile": selected_profile,
            "available_profiles": sorted(profiles),
        }

    repo_root = Path(".").resolve()
    target_root = Path(destination).resolve()
    project_dir = target_root / project_name if project_name else target_root

    if project_dir.exists() and any(project_dir.iterdir()) and not force:
        return 1, {
            "tool": "bootstrap_project",
            "ok": False,
            "reason": "destination_not_empty",
            "destination": project_dir.as_posix(),
            "created": [],
            "skipped": [],
        }

    project_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[dict[str, str]] = []

    for rel in selected_paths:
        src = repo_root / rel
        dst = project_dir / rel
        did_copy, reason = _copy_path(src, dst, force=force)
        if did_copy:
            created.append(rel)
        else:
            skipped.append({"path": rel, "reason": reason})

    _write_manifest(project_dir, selected_profile, selected_paths)
    created.append(MANIFEST_RELATIVE_PATH.as_posix())

    report = {
        "tool": "bootstrap_project",
        "ok": True,
        "destination": project_dir.as_posix(),
        "project_name": project_name or project_dir.name,
        "profile": selected_profile,
        "created_count": len(created),
        "created": sorted(created),
        "skipped": sorted(skipped, key=lambda item: item["path"]),
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    parser.add_argument("--name", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    code, report = bootstrap_project(
        destination=args.destination,
        project_name=args.name,
        profile=args.profile,
        force=args.force,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
