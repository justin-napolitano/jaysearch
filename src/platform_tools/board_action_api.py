from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from yaml import YAMLError


COMMAND = "board-action-api-check"
SPEC_PATH = Path("spec/board-action-api.yaml")
EVENT_SCHEMA_PATH = Path("spec/board-event-log.schema.yaml")
ALLOWED_AUTHORITY_TIERS = {"canonical_local", "projection_only", "evidence_only"}
EVENT_LIST_FIELDS = (
    "requested_mutation_surfaces",
    "applied_mutation_surfaces",
    "canonical_artifact_refs",
    "git_evidence_refs",
    "github_evidence_refs",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _as_clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def _require_fields(entry: dict[str, Any], required_fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in required_fields:
        if field not in entry:
            errors.append(f"missing_field:{prefix}:{field}")


def check_board_action_api(*, root: str = ".") -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    spec_path = cwd / SPEC_PATH
    event_schema_path = cwd / EVENT_SCHEMA_PATH
    errors: list[str] = []

    if not spec_path.exists():
        return 1, {"command": COMMAND, "status": "blocked", "ok": False, "errors": ["missing_board_action_api_spec"]}
    if not event_schema_path.exists():
        return 1, {"command": COMMAND, "status": "blocked", "ok": False, "errors": ["missing_board_event_log_schema"]}

    try:
        spec = _load_yaml(spec_path)
        event_schema = _load_yaml(event_schema_path)
    except (OSError, YAMLError, UnicodeDecodeError) as exc:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "errors": [f"invalid_board_action_api_yaml:{exc.__class__.__name__}"],
        }

    authority_model = spec.get("authority_model", {})
    if not isinstance(authority_model, dict):
        errors.append("invalid_authority_model")
        authority_model = {}
    if str(authority_model.get("canonical_backend", "")).strip() != "local_repo_artifacts":
        errors.append("invalid_canonical_backend")
    if authority_model.get("local_referees_authoritative") is not True:
        errors.append("local_referees_must_be_authoritative")
    if str(authority_model.get("github_projects_authority", "")).strip() != "projection_only":
        errors.append("github_projects_must_be_projection_only")

    actor_classes = spec.get("actor_classes", [])
    surface_classes = spec.get("surface_classes", [])
    action_families = spec.get("action_families", [])
    envelope = spec.get("action_envelope", {})
    if not isinstance(actor_classes, list):
        errors.append("invalid_actor_classes")
        actor_classes = []
    if not isinstance(surface_classes, list):
        errors.append("invalid_surface_classes")
        surface_classes = []
    if not isinstance(action_families, list):
        errors.append("invalid_action_families")
        action_families = []
    if not isinstance(envelope, dict):
        errors.append("invalid_action_envelope")
        envelope = {}

    envelope_required = _as_clean_list(envelope.get("required_fields", []))
    for field in ("action_id", "action_family", "actor_class", "canonical_artifact_refs", "git_evidence_refs", "github_evidence_refs"):
        if field not in envelope_required:
            errors.append(f"missing_action_envelope_field:{field}")

    actor_ids: set[str] = set()
    for actor in actor_classes:
        if not isinstance(actor, dict):
            errors.append("invalid_actor_class_entry")
            continue
        _require_fields(actor, ["id", "label", "may_request_actions"], "actor_class", errors)
        actor_id = str(actor.get("id", "")).strip()
        if actor_id in actor_ids:
            errors.append(f"duplicate_actor_class:{actor_id}")
        actor_ids.add(actor_id)

    surfaces: dict[str, dict[str, Any]] = {}
    for surface in surface_classes:
        if not isinstance(surface, dict):
            errors.append("invalid_surface_class_entry")
            continue
        _require_fields(surface, ["id", "authority_tier", "mutable_via_api", "path_refs"], "surface_class", errors)
        surface_id = str(surface.get("id", "")).strip()
        authority_tier = str(surface.get("authority_tier", "")).strip()
        if surface_id in surfaces:
            errors.append(f"duplicate_surface_class:{surface_id}")
        surfaces[surface_id] = surface
        if authority_tier not in ALLOWED_AUTHORITY_TIERS:
            errors.append(f"invalid_surface_authority_tier:{surface_id}:{authority_tier}")
        if authority_tier == "evidence_only" and bool(surface.get("mutable_via_api", False)):
            errors.append(f"evidence_surface_mutable:{surface_id}")

    action_family_ids: list[str] = []
    for family in action_families:
        if not isinstance(family, dict):
            errors.append("invalid_action_family_entry")
            continue
        _require_fields(
            family,
            ["id", "governed_objects", "mutable_surfaces", "required_evidence", "request_fields", "rejection_reasons"],
            "action_family",
            errors,
        )
        family_id = str(family.get("id", "")).strip()
        if family_id in action_family_ids:
            errors.append(f"duplicate_action_family:{family_id}")
        action_family_ids.append(family_id)
        mutable_surfaces = _as_clean_list(family.get("mutable_surfaces", []))
        if not mutable_surfaces:
            errors.append(f"action_family_without_mutable_surfaces:{family_id}")
        for surface_id in mutable_surfaces:
            surface = surfaces.get(surface_id)
            if surface is None:
                errors.append(f"unknown_mutable_surface:{family_id}:{surface_id}")
                continue
            if str(surface.get("authority_tier", "")).strip() == "evidence_only":
                errors.append(f"evidence_only_mutable_surface:{family_id}:{surface_id}")
        evidence = family.get("required_evidence", {})
        if not isinstance(evidence, dict):
            errors.append(f"invalid_required_evidence:{family_id}")
            continue
        canonical_evidence = evidence.get("canonical_artifact_refs", {})
        if not isinstance(canonical_evidence, dict) or int(canonical_evidence.get("min_items", 0)) < 1:
            errors.append(f"canonical_evidence_required:{family_id}")

    log_schema = event_schema.get("event_log", {})
    if not isinstance(log_schema, dict):
        errors.append("invalid_event_log_schema")
        log_schema = {}
    for field in (
        "required_record_fields",
        "decisions_allowed",
        "actor_classes_allowed",
        "action_families_allowed",
        "deterministic_rules",
    ):
        if field not in log_schema:
            errors.append(f"missing_event_log_field:{field}")

    event_actor_classes = set(_as_clean_list(log_schema.get("actor_classes_allowed", [])))
    missing_actor_classes = sorted(actor_ids - event_actor_classes)
    if missing_actor_classes:
        errors.extend(f"missing_event_actor_class:{actor_id}" for actor_id in missing_actor_classes)

    event_action_families = _as_clean_list(log_schema.get("action_families_allowed", []))
    if event_action_families != sorted(action_family_ids):
        errors.append("event_action_families_mismatch")

    deterministic_rules = log_schema.get("deterministic_rules", {})
    if not isinstance(deterministic_rules, dict):
        errors.append("invalid_deterministic_rules")
        deterministic_rules = {}
    if bool(deterministic_rules.get("json_keys_sorted")) is not True:
        errors.append("event_log_json_keys_must_be_sorted")
    if str(deterministic_rules.get("timestamp_format", "")).strip() != "iso8601_utc":
        errors.append("event_log_timestamp_format_invalid")

    report = {
        "command": COMMAND,
        "status": "ok" if not errors else "blocked",
        "ok": not errors,
        "errors": errors,
        "authority_model": {
            "canonical_backend": str(authority_model.get("canonical_backend", "")).strip(),
            "local_referees_authoritative": bool(authority_model.get("local_referees_authoritative", False)),
            "github_projects_authority": str(authority_model.get("github_projects_authority", "")).strip(),
        },
        "action_family_ids": sorted(action_family_ids),
        "surface_ids": sorted(surfaces),
        "evidence_refs": [spec_path.as_posix(), event_schema_path.as_posix()],
    }
    return (0 if not errors else 1), report


def build_event_record(record: dict[str, Any], *, root: str = ".") -> dict[str, Any]:
    _, report = check_board_action_api(root=root)
    if not report.get("ok", False):
        raise ValueError("board_action_api_invalid")

    cwd = Path(root)
    event_schema = _load_yaml(cwd / EVENT_SCHEMA_PATH).get("event_log", {})
    required_fields = _as_clean_list(event_schema.get("required_record_fields", []))
    cleaned: dict[str, Any] = {}
    for field in required_fields:
        if field not in record:
            raise ValueError(f"missing_event_field:{field}")
        value = record[field]
        if field in EVENT_LIST_FIELDS:
            cleaned[field] = _as_clean_list(value)
        else:
            cleaned[field] = str(value).strip() if value is not None else ""

    if cleaned["decision"] not in _as_clean_list(event_schema.get("decisions_allowed", [])):
        raise ValueError(f"invalid_event_decision:{cleaned['decision']}")
    if cleaned["actor_class"] not in _as_clean_list(event_schema.get("actor_classes_allowed", [])):
        raise ValueError(f"invalid_event_actor_class:{cleaned['actor_class']}")
    if cleaned["action_family"] not in _as_clean_list(event_schema.get("action_families_allowed", [])):
        raise ValueError(f"invalid_event_action_family:{cleaned['action_family']}")

    return dict(sorted(cleaned.items()))


def append_event_record(*, root: str = ".", event_log_path: str, record: dict[str, Any]) -> dict[str, Any]:
    cleaned = build_event_record(record, root=root)
    path = Path(root) / event_log_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(cleaned, sort_keys=True) + "\n")
    return cleaned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the board-action API contract and deterministic event log.")
    subparsers = parser.add_subparsers(dest="subcommand")

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--root", default=".")

    write_parser = subparsers.add_parser("write-event")
    write_parser.add_argument("--root", default=".")
    write_parser.add_argument("--event-log", required=True)
    write_parser.add_argument("--record-json", required=True)

    args = parser.parse_args(argv)
    if args.subcommand in {None, "check"}:
        root = getattr(args, "root", ".")
        code, report = check_board_action_api(root=root)
        print(json.dumps(report, indent=2, sort_keys=True))
        return code

    record_path = Path(args.record_json)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    written = append_event_record(root=args.root, event_log_path=args.event_log, record=record)
    print(json.dumps({"command": "board-action-event-log-write", "ok": True, "event_log": args.event_log, "record": written}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
