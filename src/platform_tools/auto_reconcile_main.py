from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.remaining_work_graph_check import check_remaining_work_graph
from platform_tools.reconcile_remaining_work_merge import reconcile_pending_merge_completions


COMMAND = "auto-reconcile-main"


def _eligible_branch(branch: str) -> bool:
    return branch == "main" or branch.startswith("initiative/")


def run_auto_reconcile_main(
    *,
    root: str = ".",
    branch: str | None = None,
    base_ref: str = "main",
    source_hook: str = "manual",
    checkout_kind: str = "",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    current_branch = branch or get_current_branch(root=root_path)
    normalized_checkout_kind = checkout_kind.strip().lower()

    if source_hook == "post-checkout" and normalized_checkout_kind not in {"", "branch"}:
        report = {
            "command": COMMAND,
            "status": "skipped",
            "ok": True,
            "root": root_path.as_posix(),
            "branch": current_branch,
            "source_hook": source_hook,
            "reason": "non_branch_checkout",
        }
        return 0, report

    if not _eligible_branch(current_branch):
        report = {
            "command": COMMAND,
            "status": "skipped",
            "ok": True,
            "root": root_path.as_posix(),
            "branch": current_branch,
            "source_hook": source_hook,
            "reason": "branch_not_eligible",
        }
        return 0, report

    reconciliation = reconcile_pending_merge_completions(repo_root=root_path, main_ref=base_ref)
    graph_code, graph_report = check_remaining_work_graph(root=root_path.as_posix(), branch=current_branch)
    blockers: list[str] = []
    if graph_code != 0:
        blockers.extend(f"remaining_work_graph:{item}" for item in graph_report.get("errors", []))

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "root": root_path.as_posix(),
        "branch": current_branch,
        "base_ref": base_ref,
        "source_hook": source_hook,
        "checkout_kind": normalized_checkout_kind,
        "reconciliation": reconciliation,
        "graph_check": {
            "status": graph_report.get("status", ""),
            "ok": graph_report.get("ok", False),
            "errors": graph_report.get("errors", []),
        },
        "blockers": blockers,
    }
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--source-hook", default="manual")
    parser.add_argument("--checkout-kind", default="")
    parser.add_argument("hook_args", nargs="*")
    args = parser.parse_args()
    code, report = run_auto_reconcile_main(
        root=args.root,
        branch=args.branch,
        base_ref=args.base_ref,
        source_hook=args.source_hook,
        checkout_kind=args.checkout_kind,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
