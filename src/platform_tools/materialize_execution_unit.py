from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json
from platform_tools.validate_node_readiness import validate_node_readiness


COMMAND = "materialize-execution-unit"
DEFAULT_OUTPUT_ROOT = Path("artifacts/execution-units/runs")
DEFAULT_POLICY_PATH = "spec/node-readiness-policy.yaml"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("meu-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _policy_path(repo_root: Path) -> str:
    root_policy = repo_root / DEFAULT_POLICY_PATH
    if root_policy.exists():
        return DEFAULT_POLICY_PATH
    return Path(__file__).resolve().parents[2].joinpath(DEFAULT_POLICY_PATH).as_posix()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in normalized.split("-") if part)[:80] or "node"


def _implementation_intent(scope: dict[str, Any]) -> dict[str, Any]:
    intent = scope.get("implementation_intent", {})
    return intent if isinstance(intent, dict) else {}


def _expected_changes(scope: dict[str, Any], intent: dict[str, Any]) -> list[str]:
    return (
        _string_list(scope.get("expected_changes", []))
        or _string_list(scope.get("in_scope", []))
        or _string_list(intent.get("contract_changes", []))
        + _string_list(intent.get("runtime_changes", []))
        + _string_list(intent.get("validation_changes", []))
        + _string_list(intent.get("docs_changes", []))
    )


def _looks_like_path(value: str) -> bool:
    if " " in value:
        return False
    prefixes = ("src/", "tests/", "docs/", "spec/", "bin/", "artifacts/", ".agent/")
    suffixes = (".py", ".md", ".yaml", ".yml", ".json", ".toml")
    return value.startswith(prefixes) or value.endswith(suffixes)


def _owned_changes(scope: dict[str, Any], intent: dict[str, Any]) -> list[str]:
    explicit = _string_list(scope.get("owned_changes", []))
    if explicit:
        return explicit
    return [item for item in _expected_changes(scope, intent) if _looks_like_path(item)]


def _looks_like_command(value: str) -> bool:
    return value.startswith(("uv ", "python", "python3 ", "bin/", "bash ")) or "pytest" in value


def _validation_commands(scope: dict[str, Any], intent: dict[str, Any]) -> list[str]:
    explicit = _string_list(scope.get("validation_commands", []))
    if explicit:
        return explicit
    candidates = (
        _string_list(scope.get("acceptance_checks", []))
        + _string_list(scope.get("validation_changes", []))
        + _string_list(intent.get("validation_changes", []))
    )
    commands: list[str] = []
    for item in candidates:
        if _looks_like_command(item) and item not in commands:
            commands.append(item)
    return commands


def materialize_execution_unit(
    *,
    root: str = ".",
    selected_scope_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    target_state: str = "implementation_ready",
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    scope = _load_json(repo_root / selected_scope_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(scope.get("packet_type", "")).strip() != "selected_solution_scope":
        blockers.append("selected_scope_packet_type_invalid")
    problem_id = str(scope.get("problem_id", "")).strip()
    selected_candidate_id = str(scope.get("selected_candidate_id", "")).strip()
    if not problem_id:
        blockers.append("selected_scope_missing_problem_id")
    if not selected_candidate_id:
        blockers.append("selected_scope_missing_selected_candidate_id")

    intent = _implementation_intent(scope)
    expected_changes = _expected_changes(scope, intent)
    owned_changes = _owned_changes(scope, intent)
    validation_commands = _validation_commands(scope, intent)
    non_goals = _string_list(scope.get("out_of_scope", [])) or _string_list(scope.get("non_goals", []))
    evidence_refs = _string_list(scope.get("evidence_refs", []))
    handoff_requirements = _string_list(scope.get("handoff_requirements", []))

    node_id = f"problem-node:{_slug(problem_id)}:{_slug(selected_candidate_id)}"
    option_id = f"node-option:{_slug(selected_candidate_id)}"
    execution_unit_id = f"execution-unit:{_slug(problem_id)}:{_slug(selected_candidate_id)}"

    problem_node = {
        "packet_type": "problem_node",
        "packet_version": "v1",
        "packet_id": f"{node_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "node_id": node_id,
        "node_version": "v1",
        "project_id": problem_id,
        "title": str(scope.get("selected_solution_summary", "")).strip() or problem_id,
        "node_type": "implementation_problem",
        "goal": str(scope.get("selection_reason", "")).strip() or "Materialize selected solution scope.",
        "problem_statement": str(scope.get("selected_solution_summary", "")).strip()
        or str(intent.get("summary", "")).strip(),
        "inputs": [str((repo_root / selected_scope_path).resolve())],
        "expected_outputs": expected_changes,
        "constraints": non_goals,
        "dependencies": [],
        "evidence_refs": evidence_refs,
        "option_refs": [],
        "selected_option_ref": "",
        "readiness_state": "planning_ready" if intent else "research_ready",
        "missing_fields": [],
        "evaluation_criteria": _string_list(scope.get("acceptance_checks", []))
        or _string_list(scope.get("acceptance_targets", [])),
        "feedback_refs": [],
    }
    problem_node_path = write_json(run_root / "problem-node.packet.json", problem_node)

    emitted_refs = {"problem_node_path": problem_node_path.as_posix()}
    node_option_path: Path | None = None
    execution_unit_path: Path | None = None
    readiness_report: dict[str, Any] | None = None

    if intent:
        node_option = {
            "packet_type": "node_option",
            "packet_version": "v1",
            "packet_id": f"{option_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "option_id": option_id,
            "source_node_ref": problem_node_path.as_posix(),
            "option_family": "selected_solution_scope",
            "approach_summary": str(intent.get("summary", "")).strip()
            or str(scope.get("selected_solution_summary", "")).strip(),
            "implementation_intent": intent,
            "expected_changes": expected_changes,
            "non_goals": non_goals,
            "assumptions": _string_list(scope.get("assumptions", [])),
            "risks": _string_list(scope.get("risks", [])),
            "evidence_refs": evidence_refs,
            "evaluation_refs": _string_list(scope.get("evaluation_refs", [])),
        }
        node_option_path = write_json(run_root / "node-option.packet.json", node_option)
        emitted_refs["node_option_path"] = node_option_path.as_posix()

        problem_node["option_refs"] = [node_option_path.as_posix()]
        problem_node["selected_option_ref"] = node_option_path.as_posix()
        write_json(problem_node_path, problem_node)

        execution_unit = {
            "packet_type": "execution_unit",
            "packet_version": "v1",
            "packet_id": f"{execution_unit_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "execution_unit_id": execution_unit_id,
            "source_problem_node_ref": problem_node_path.as_posix(),
            "selected_option_ref": node_option_path.as_posix(),
            "implementation_intent": intent,
            "owned_changes": owned_changes,
            "required_inputs": handoff_requirements or [str((repo_root / selected_scope_path).resolve())],
            "expected_outputs": expected_changes,
            "acceptance_checks": _string_list(scope.get("acceptance_checks", [])),
            "validation_commands": validation_commands,
            "rollback_plan": str(scope.get("rollback_plan", "")).strip()
            or "Revert owned changes from this execution unit.",
            "non_goals": non_goals,
            "dependency_refs": _string_list(scope.get("dependency_refs", [])),
            "evidence_refs": evidence_refs,
            "evaluation_method": "node_readiness_policy_v1",
            "completion_evidence_requirements": _string_list(
                scope.get("completion_evidence_requirements", [])
            )
            or validation_commands,
        }
        execution_unit_path = write_json(run_root / "execution-unit.packet.json", execution_unit)
        emitted_refs["execution_unit_path"] = execution_unit_path.as_posix()
        _, readiness_report = validate_node_readiness(
            root=repo_root.as_posix(),
            node_path=execution_unit_path.relative_to(repo_root).as_posix(),
            target_state=target_state,
            policy_path=_policy_path(repo_root),
        )
        if not readiness_report.get("ready", False):
            blockers.extend(str(item) for item in readiness_report.get("blockers", []))
            blockers.extend(f"missing:{item}" for item in readiness_report.get("missing_fields", []))
            execution_unit_path.unlink(missing_ok=True)
            emitted_refs.pop("execution_unit_path", None)

    else:
        blockers.append("selected_scope_missing_implementation_intent")

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "selected_scope_path": str((repo_root / selected_scope_path).resolve()),
            "target_state": target_state,
            "emitted_packet_refs": emitted_refs,
            "readiness_report": readiness_report or {},
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "execution-unit-materialization.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--selected-scope-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--target-state", default="implementation_ready")
    args = parser.parse_args()
    try:
        code, report = materialize_execution_unit(
            root=args.root,
            selected_scope_path=args.selected_scope_path,
            output_root=args.output_root,
            target_state=args.target_state,
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
