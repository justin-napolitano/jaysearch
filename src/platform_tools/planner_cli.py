from __future__ import annotations

import argparse
import json

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


def _print(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _parse_evidence(raw: str) -> dict[str, object]:
    if not raw:
        return {}
    return json.loads(raw)


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
    draft = contract_sub.add_parser("draft-execplan")
    draft.add_argument("--graph-id", required=True)
    draft.add_argument("--title", required=True)
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

    if args.command == "session":
        if args.session_command == "start":
            _print(create_session(title=args.title, objective=args.objective, mode=args.mode))
            return 0
        if args.session_command == "chat":
            _print(session_chat(session_id=args.session_id))
            return 0
        if args.session_command == "show":
            _print(load_session(session_id=args.session_id))
            return 0
        if args.session_command == "summarize":
            _print(summarize_session(session_id=args.session_id))
            return 0

    if args.command == "graph":
        if args.graph_command == "build":
            _print(build_graph(session_id=args.session_id))
            return 0
        status_map = {
            "show": None,
            "ready": "ready",
            "blocked": "blocked",
            "review": "in_review",
            "validated": "validated",
            "recovery": "recovery_required",
        }
        if args.graph_command in status_map:
            _print(show_graph(graph_id=args.graph_id, status=status_map[args.graph_command]))
            return 0
        if args.graph_command == "validate":
            code, report = validate_graph(graph_id=args.graph_id)
            _print(report)
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
            _print(report)
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
            _print(report)
            return code

    if args.command == "contract":
        if args.contract_command == "draft-execplan":
            code, report = draft_execplan(graph_id=args.graph_id, title=args.title)
            _print(report)
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
            _print(report)
            return code

    if args.command == "validate":
        if args.research_only:
            code, report = validate_research()
            _print(report)
            return code
        code, report = validate_all(graph_id=args.graph_id)
        _print(report)
        return code

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
