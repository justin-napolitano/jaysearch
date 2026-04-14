from __future__ import annotations

import argparse
import json
from typing import Any

from platform_tools.planner_runtime import (
    apply_move,
    build_graph,
    create_session,
    draft_execplan,
    import_execplan,
    load_session,
    session_chat,
    show_graph,
    summarize_session,
    validate_all,
    validate_graph,
    validate_move,
    validate_research,
)


COMMAND = "planner"


def _print(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _parse_evidence(raw: str) -> dict[str, object]:
    if not raw:
        return {}
    return json.loads(raw)


def _planner_operation(args: argparse.Namespace) -> str:
    parts = [str(args.command)]
    for attr in ("session_command", "graph_command", "move_command", "contract_command"):
        value = getattr(args, attr, None)
        if value:
            parts.append(str(value))
    return ".".join(parts)


def _collect_blockers(payload: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    errors = payload.get("errors")
    if isinstance(errors, list):
        blockers.extend(str(item) for item in errors)
    for key in ("research", "graph"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            nested_errors = nested.get("errors")
            if isinstance(nested_errors, list):
                blockers.extend(f"{key}:{item}" for item in nested_errors)
    return sorted(blockers)


def _next_validations(args: argparse.Namespace, payload: dict[str, Any]) -> list[str]:
    operation = _planner_operation(args)
    if operation == "session.start" and payload.get("session_id"):
        return [f"bin/planner graph build --session-id {payload['session_id']}"]
    if operation == "graph.build" and payload.get("graph_id"):
        return [f"bin/planner graph validate --graph-id {payload['graph_id']}"]
    if operation == "move.apply" and payload.get("graph_id"):
        return [f"bin/planner graph validate --graph-id {payload['graph_id']}"]
    if operation == "contract.execplan" and payload.get("path"):
        return [f"bin/execplan-validate {payload['path']}"]
    return []


def _evidence_refs(payload: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("session_dir", "graph_path", "path", "report_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            refs.append(value)
    return sorted(refs)


def _normalize_payload(args: argparse.Namespace, payload: dict[str, Any], code: int) -> dict[str, Any]:
    normalized = dict(payload)
    if "status" in normalized:
        normalized["result_status"] = normalized.pop("status")
    normalized["command"] = COMMAND
    normalized["operation"] = _planner_operation(args)
    normalized["status"] = "ok" if code == 0 else "blocked"
    normalized["blockers"] = _collect_blockers(payload)
    normalized["next_validations"] = _next_validations(args, payload)
    evidence_refs = _evidence_refs(payload)
    if evidence_refs:
        normalized["evidence_refs"] = evidence_refs
    return normalized


def _error_report(args: argparse.Namespace, exc: Exception) -> dict[str, Any]:
    return {
        "command": COMMAND,
        "operation": _planner_operation(args),
        "status": "blocked",
        "blockers": [f"{exc.__class__.__name__}:{exc}"],
        "next_validations": [],
        "ok": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    session_parser = subparsers.add_parser("session")
    session_sub = session_parser.add_subparsers(dest="session_command", required=True)
    start = session_sub.add_parser("start")
    start.add_argument("--title", required=True)
    start.add_argument("--objective", default="")
    start.add_argument("--mode", default="adversarial")
    chat = session_sub.add_parser("chat")
    chat.add_argument("--session-id", required=True)
    show = session_sub.add_parser("show")
    show.add_argument("--session-id", required=True)
    summarize = session_sub.add_parser("summarize")
    summarize.add_argument("--session-id", required=True)

    graph_parser = subparsers.add_parser("graph")
    graph_sub = graph_parser.add_subparsers(dest="graph_command", required=True)
    build = graph_sub.add_parser("build")
    build.add_argument("--session-id", required=True)
    graph_show = graph_sub.add_parser("show")
    graph_show.add_argument("--graph-id", required=True)
    ready = graph_sub.add_parser("ready")
    ready.add_argument("--graph-id", required=True)
    blocked = graph_sub.add_parser("blocked")
    blocked.add_argument("--graph-id", required=True)
    review = graph_sub.add_parser("review")
    review.add_argument("--graph-id", required=True)
    validated = graph_sub.add_parser("validated")
    validated.add_argument("--graph-id", required=True)
    recovery = graph_sub.add_parser("recovery")
    recovery.add_argument("--graph-id", required=True)
    graph_validate = graph_sub.add_parser("validate")
    graph_validate.add_argument("--graph-id", required=True)

    move_parser = subparsers.add_parser("move")
    move_sub = move_parser.add_subparsers(dest="move_command", required=True)
    move_validate = move_sub.add_parser("validate")
    move_apply = move_sub.add_parser("apply")
    for move_cmd in (move_validate, move_apply):
        move_cmd.add_argument("--graph-id", required=True)
        move_cmd.add_argument("--node-id", required=True)
        move_cmd.add_argument("--phase", required=True, choices=["planner", "implementation"])
        move_cmd.add_argument("--move", required=True)
        move_cmd.add_argument("--to-status", required=True)
        move_cmd.add_argument("--evidence-json", default="")

    contract_parser = subparsers.add_parser("contract")
    contract_sub = contract_parser.add_subparsers(dest="contract_command", required=True)
    execplan_contract = contract_sub.add_parser("execplan")
    execplan_contract.add_argument("--graph-id", required=True)
    execplan_contract.add_argument("--title", required=True)
    contract_import = contract_sub.add_parser("import-execplan")
    contract_import.add_argument("--session-id", required=True)
    contract_import.add_argument("--graph-id", required=True)
    contract_import.add_argument("--execplan-id", required=True)
    contract_import.add_argument("--original-path", required=True)
    contract_import.add_argument("--edited-path", required=True)
    contract_import.add_argument("--operator", required=True)
    contract_import.add_argument("--referee", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--graph-id", default=None)
    validate_parser.add_argument("--research-only", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "session":
            if args.session_command == "start":
                report = create_session(title=args.title, objective=args.objective, mode=args.mode)
                code = 0
                _print(_normalize_payload(args, report, code))
                return code
            if args.session_command == "chat":
                report = session_chat(session_id=args.session_id)
                code = 0
                _print(_normalize_payload(args, report, code))
                return code
            if args.session_command == "show":
                report = load_session(session_id=args.session_id)
                code = 0
                _print(_normalize_payload(args, report, code))
                return code
            if args.session_command == "summarize":
                report = summarize_session(session_id=args.session_id)
                code = 0
                _print(_normalize_payload(args, report, code))
                return code

        if args.command == "graph":
            if args.graph_command == "build":
                report = build_graph(session_id=args.session_id)
                code = 0
                _print(_normalize_payload(args, report, code))
                return code
            status_map = {
                "show": None,
                "ready": "ready",
                "blocked": "blocked",
                "review": "in_review",
                "validated": "validated",
                "recovery": "recovery_required",
            }
            if args.graph_command in status_map:
                report = show_graph(graph_id=args.graph_id, status=status_map[args.graph_command])
                code = 0
                _print(_normalize_payload(args, report, code))
                return code
            if args.graph_command == "validate":
                code, report = validate_graph(graph_id=args.graph_id)
                _print(_normalize_payload(args, report, code))
                return code

        if args.command == "move":
            evidence = _parse_evidence(args.evidence_json)
            if args.move_command == "validate":
                code, report = validate_move(
                    graph_id=args.graph_id,
                    node_id=args.node_id,
                    phase=args.phase,
                    move=args.move,
                    target_status=args.to_status,
                    evidence=evidence,
                )
                _print(_normalize_payload(args, report, code))
                return code
            if args.move_command == "apply":
                code, report = apply_move(
                    graph_id=args.graph_id,
                    node_id=args.node_id,
                    phase=args.phase,
                    move=args.move,
                    target_status=args.to_status,
                    evidence=evidence,
                )
                _print(_normalize_payload(args, report, code))
                return code

        if args.command == "contract":
            if args.contract_command == "execplan":
                code, report = draft_execplan(graph_id=args.graph_id, title=args.title)
                _print(_normalize_payload(args, report, code))
                return code
            if args.contract_command == "import-execplan":
                code, report = import_execplan(
                    session_id=args.session_id,
                    graph_id=args.graph_id,
                    execplan_id=args.execplan_id,
                    original_path=args.original_path,
                    edited_path=args.edited_path,
                    operator=args.operator,
                    referee=args.referee,
                )
                _print(_normalize_payload(args, report, code))
                return code

        if args.command == "validate":
            if args.research_only:
                code, report = validate_research()
                _print(_normalize_payload(args, report, code))
                return code
            code, report = validate_all(graph_id=args.graph_id)
            _print(_normalize_payload(args, report, code))
            return code
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        _print(_error_report(args, exc))
        return 1

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
