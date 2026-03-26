from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.next_worker_slice import get_next_worker_slice
from platform_tools.public_orchestration_api import envelope
from platform_tools.worker_contracts import contract_scope_findings, find_contract, load_registry


COMMAND = "resolve-worker-contract"


def resolve_worker_contract(
    *,
    root: str = ".",
    initiative_branch: str | None = None,
    contract_id: str | None = None,
    branch: str | None = None,
    worker_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    resolved_initiative = (initiative_branch or "").strip()

    if contract_id or branch or worker_id:
        if not resolved_initiative:
            resolved_initiative = get_current_branch(root=root_path)
        registry = load_registry(root=root_path, initiative_branch=resolved_initiative)
        if registry is None:
            return 1, envelope(
                command=COMMAND,
                status="blocked",
                ok=False,
                payload={
                    "initiative_branch": resolved_initiative,
                    "blockers": ["worker_contract_registry_missing"],
                },
            )
        contract = find_contract(registry, contract_id=contract_id, branch=branch, worker_id=worker_id)
        if contract is None:
            return 1, envelope(
                command=COMMAND,
                status="blocked",
                ok=False,
                payload={
                    "initiative_branch": resolved_initiative,
                    "blockers": ["worker_contract_not_found"],
                },
            )
        findings = contract_scope_findings(contract)
        if findings:
            return 1, envelope(
                command=COMMAND,
                status="blocked",
                ok=False,
                payload={
                    "initiative_branch": resolved_initiative,
                    "blockers": findings,
                    "selected": {
                        "contract_id": str(contract.get("contract_id", "")).strip(),
                        "execplan_id": str(contract.get("execplan_id", "")).strip(),
                        "branch": str(contract.get("branch", "")).strip(),
                        "worker_id": str(contract.get("worker_id", "")).strip(),
                        "title": str(contract.get("title", "")).strip(),
                    },
                },
            )
        return 0, envelope(
            command=COMMAND,
            status="ok",
            ok=True,
            payload={
                "initiative_branch": resolved_initiative,
                "selected": {
                    "contract_id": str(contract.get("contract_id", "")).strip(),
                    "execplan_id": str(contract.get("execplan_id", "")).strip(),
                    "branch": str(contract.get("branch", "")).strip(),
                    "worker_id": str(contract.get("worker_id", "")).strip(),
                    "title": str(contract.get("title", "")).strip(),
                    "status": str(contract.get("status", "")).strip(),
                },
            },
        )

    if not resolved_initiative:
        resolved_initiative = get_current_branch(root=root_path)
    code, report = get_next_worker_slice(root=root_path.as_posix(), initiative_branch=resolved_initiative)
    if code != 0:
        return code, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "initiative_branch": resolved_initiative,
                "blockers": list(report.get("blockers", [])),
                "candidates": report.get("candidates", []),
            },
        )
    selected = report.get("selected", {})
    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "initiative_branch": resolved_initiative,
            "selected": {
                "contract_id": str(selected.get("contract_id", "")).strip(),
                "execplan_id": str(selected.get("execplan_id", "")).strip(),
                "branch": str(selected.get("implementation_branch", "")).strip(),
                "worker_id": str(selected.get("worker_id", "")).strip(),
                "title": str(selected.get("title", "")).strip(),
                "status": str(selected.get("status", "")).strip(),
            },
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--initiative-branch", default=None)
    parser.add_argument("--contract-id", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--worker-id", default=None)
    args = parser.parse_args()
    code, report = resolve_worker_contract(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
