from __future__ import annotations

import argparse
import json

from platform_tools.planner_runtime import (
    build_graph,
    create_session,
    session_chat,
    show_graph,
    summarize_session,
    validate_all,
    validate_graph,
    validate_research,
    load_session,
)


def _print(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


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

    graph_validate = graph_sub.add_parser("validate")
    graph_validate.add_argument("--graph-id", required=True)

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
        if args.graph_command == "show":
            _print(show_graph(graph_id=args.graph_id))
            return 0
        if args.graph_command == "ready":
            _print(show_graph(graph_id=args.graph_id, status="ready"))
            return 0
        if args.graph_command == "blocked":
            _print(show_graph(graph_id=args.graph_id, status="blocked"))
            return 0
        if args.graph_command == "validate":
            code, report = validate_graph(graph_id=args.graph_id)
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
