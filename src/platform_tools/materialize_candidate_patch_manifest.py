from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "materialize-candidate-patch-manifest"
DEFAULT_OUTPUT_ROOT = Path("artifacts/candidate-patch-manifests/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("cpm-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in normalized.split("-") if part)[:80] or "candidate"


def _parse_patch_changed_paths(patch_path: Path) -> list[str]:
    changed: list[str] = []
    for line in patch_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("+++ "):
            continue
        target = line[4:].strip()
        if target == "/dev/null":
            continue
        if target.startswith("b/"):
            target = target[2:]
        changed.append(target)
    return sorted(set(changed))


def _run_patch_check(*, repo_root: Path, patch_path: Path, run_root: Path, index: int) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    completed = subprocess.run(
        ["git", "apply", "--check", patch_path.as_posix()],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    result = {
        "command": f"git apply --check {patch_path.as_posix()}",
        "status": "passed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "stdout_tail": completed.stdout[-12000:],
        "stderr_tail": completed.stderr[-12000:],
        "patch_ref": patch_path.as_posix(),
    }
    result_path = write_json(run_root / f"candidate-{index:02d}-patch-validation.result.json", result)
    return result, result_path.as_posix()


def materialize_candidate_patch_manifest(
    *,
    root: str = ".",
    execution_unit_path: str,
    patch_source_paths: list[str],
    candidate_families: list[str] | None = None,
    source_labels: list[str] | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    validate_patches: bool = False,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    execution_unit = _load_json(repo_root / execution_unit_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(execution_unit.get("packet_type", "")).strip() != "execution_unit":
        blockers.append("execution_unit_packet_type_invalid")
    if not patch_source_paths:
        blockers.append("patch_source_paths_missing")

    source_execution_unit_ref = str((repo_root / execution_unit_path).resolve())
    candidate_families = candidate_families or []
    source_labels = source_labels or []
    candidate_patches: list[dict[str, Any]] = []
    evidence_refs: list[str] = []

    for index, patch_source_path in enumerate(patch_source_paths, start=1):
        patch_path = Path(patch_source_path)
        if not patch_path.is_absolute():
            patch_path = repo_root / patch_source_path
        candidate_blockers: list[str] = []
        validation_refs: list[str] = []
        expected_changed_artifact_refs: list[str] = []
        if not patch_path.exists():
            candidate_blockers.append("patch_source_path_missing")
        elif not patch_path.is_file():
            candidate_blockers.append("patch_source_path_not_file")
        else:
            expected_changed_artifact_refs = _parse_patch_changed_paths(patch_path)
            if validate_patches:
                result, validation_ref = _run_patch_check(
                    repo_root=repo_root,
                    patch_path=patch_path,
                    run_root=run_root,
                    index=index,
                )
                validation_refs.append(validation_ref)
                evidence_refs.append(validation_ref)
                if result["status"] != "passed":
                    candidate_blockers.append("patch_validation_failed")

        family = (
            candidate_families[index - 1]
            if index <= len(candidate_families) and candidate_families[index - 1].strip()
            else "manual_patch"
        )
        source_label = (
            source_labels[index - 1]
            if index <= len(source_labels) and source_labels[index - 1].strip()
            else Path(patch_source_path).name
        )
        candidate_patches.append(
            {
                "candidate_id": f"candidate-patch:{index:03d}:{_slug(source_label)}",
                "patch_ref": patch_path.as_posix(),
                "candidate_family": family,
                "source_label": source_label,
                "producer_ref": COMMAND,
                "expected_changed_artifact_refs": expected_changed_artifact_refs,
                "validation_refs": validation_refs,
                "blockers": candidate_blockers,
            }
        )

    if all(_string_list(candidate.get("blockers", [])) for candidate in candidate_patches):
        blockers.append("all_candidate_patches_blocked")

    manifest_id = f"candidate-patch-manifest:{_slug(str(execution_unit.get('execution_unit_id', 'execution')))}"
    manifest = {
        "packet_type": "candidate_patch_manifest",
        "packet_version": "v1",
        "packet_id": f"{manifest_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "manifest_id": manifest_id,
        "source_execution_unit_ref": source_execution_unit_ref,
        "candidate_patches": candidate_patches,
        "validation_policy": {
            "validate_patches": validate_patches,
            "validation_command": "git apply --check" if validate_patches else "",
            "invalid_candidates_preserved": True,
        },
        "evidence_refs": sorted(set(evidence_refs)),
        "blockers": sorted(set(blockers)),
    }
    manifest_path = write_json(run_root / "candidate-patch-manifest.packet.json", manifest)

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "execution_unit_path": source_execution_unit_ref,
            "candidate_patch_manifest_path": manifest_path.as_posix(),
            "candidate_count": len(candidate_patches),
            "unblocked_candidate_count": sum(
                1 for candidate in candidate_patches if not _string_list(candidate.get("blockers", []))
            ),
            "evidence_refs": sorted(set(evidence_refs)),
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "candidate-patch-manifest.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-unit-path", required=True)
    parser.add_argument("--patch-source-path", action="append", default=[])
    parser.add_argument("--candidate-family", action="append", default=[])
    parser.add_argument("--source-label", action="append", default=[])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--validate-patches", action="store_true")
    args = parser.parse_args()
    try:
        code, report = materialize_candidate_patch_manifest(
            root=args.root,
            execution_unit_path=args.execution_unit_path,
            patch_source_paths=args.patch_source_path,
            candidate_families=args.candidate_family,
            source_labels=args.source_label,
            output_root=args.output_root,
            validate_patches=args.validate_patches,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
