from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_candidate_patch_manifest import materialize_candidate_patch_manifest


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _execution_unit() -> dict[str, object]:
    return {
        "packet_type": "execution_unit",
        "packet_version": "v1",
        "packet_id": "execution-unit:001",
        "created_at": "2026-05-25T00:00:00Z",
        "producer": "test",
        "execution_unit_id": "execution-unit:test",
        "owned_changes": ["src/platform_tools/example.py"],
        "validation_commands": ["python3 -m py_compile src/platform_tools/example.py"],
    }


def _write_example_source(root: Path) -> None:
    source_file = root / "src" / "platform_tools" / "example.py"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("VALUE = 1\n", encoding="utf-8")


def _write_patch(path: Path, value: str = "2") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "diff --git a/src/platform_tools/example.py b/src/platform_tools/example.py",
                "index 43b23da..5a2f16f 100644",
                "--- a/src/platform_tools/example.py",
                "+++ b/src/platform_tools/example.py",
                "@@ -1 +1 @@",
                "-VALUE = 1",
                f"+VALUE = {value}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_materialize_candidate_patch_manifest_preserves_multiple_candidates(
    tmp_path: Path,
) -> None:
    _write_example_source(tmp_path)
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    _write_patch(tmp_path / "artifacts" / "candidate-a.patch", "2")
    _write_patch(tmp_path / "artifacts" / "candidate-b.patch", "3")

    code, report = materialize_candidate_patch_manifest(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_paths=["artifacts/candidate-a.patch", "artifacts/candidate-b.patch"],
        candidate_families=["manual_a", "manual_b"],
        validate_patches=True,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["candidate_count"] == 2
    assert report["unblocked_candidate_count"] == 2
    manifest = json.loads(Path(report["candidate_patch_manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["packet_type"] == "candidate_patch_manifest"
    assert [candidate["candidate_family"] for candidate in manifest["candidate_patches"]] == [
        "manual_a",
        "manual_b",
    ]
    assert all(candidate["validation_refs"] for candidate in manifest["candidate_patches"])
    assert all(candidate["blockers"] == [] for candidate in manifest["candidate_patches"])


def test_materialize_candidate_patch_manifest_preserves_invalid_candidate(
    tmp_path: Path,
) -> None:
    _write_example_source(tmp_path)
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    _write_patch(tmp_path / "artifacts" / "candidate-a.patch", "2")
    bad_patch = tmp_path / "artifacts" / "candidate-b.patch"
    bad_patch.parent.mkdir(parents=True, exist_ok=True)
    bad_patch.write_text("not a patch\n", encoding="utf-8")

    code, report = materialize_candidate_patch_manifest(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_paths=["artifacts/candidate-a.patch", "artifacts/candidate-b.patch"],
        validate_patches=True,
    )

    assert code == 0
    manifest = json.loads(Path(report["candidate_patch_manifest_path"]).read_text(encoding="utf-8"))
    assert report["candidate_count"] == 2
    assert report["unblocked_candidate_count"] == 1
    assert manifest["candidate_patches"][0]["blockers"] == []
    assert "patch_validation_failed" in manifest["candidate_patches"][1]["blockers"]


def test_materialize_candidate_patch_manifest_blocks_when_all_candidates_invalid(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )

    code, report = materialize_candidate_patch_manifest(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_paths=["artifacts/missing-a.patch", "artifacts/missing-b.patch"],
        validate_patches=True,
    )

    assert code == 1
    assert "all_candidate_patches_blocked" in report["blockers"]
    manifest = json.loads(Path(report["candidate_patch_manifest_path"]).read_text(encoding="utf-8"))
    assert len(manifest["candidate_patches"]) == 2
