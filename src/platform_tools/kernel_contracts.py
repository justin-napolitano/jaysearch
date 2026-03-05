from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any

COMMAND_CONTRACTS: list[dict[str, Any]] = [
    {
        "name": "execplan_validate",
        "command": "bin/execplan-validate .agent/execplans/*.md",
        "expected_exit": 0,
        "required_top_level_keys": ["tool", "error_count", "results", "branch_policy"],
    },
    {
        "name": "sync_todos",
        "command": "bin/sync-todos",
        "expected_exit": 0,
        "required_top_level_keys": ["tool", "task_count", "todo_path", "warnings", "changed"],
    },
    {
        "name": "repo_health_check",
        "command": "bin/repo-health-check",
        "expected_exit": 0,
        "required_top_level_keys": ["tool", "checks", "maturity"],
    },
]


def _run_command(command: str) -> tuple[int, str]:
    proc = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def _validate_json_contract(output: str, required_keys: list[str]) -> tuple[bool, str]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        return False, f"invalid_json:{exc.msg}"
    missing = [k for k in required_keys if k not in payload]
    if missing:
        return False, f"missing_keys:{','.join(missing)}"
    return True, ""


def run_contract_check() -> tuple[int, dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for contract in COMMAND_CONTRACTS:
        command = str(contract["command"])
        expected_exit = int(contract["expected_exit"])
        required_keys = list(contract["required_top_level_keys"])

        first_exit, first_out = _run_command(command)
        second_exit, second_out = _run_command(command)

        json_ok, json_reason = _validate_json_contract(first_out, required_keys)
        stable_exit = first_exit == second_exit
        stable_output = first_out == second_out
        expected_ok = first_exit == expected_exit and second_exit == expected_exit

        status = "PASS"
        reasons: list[str] = []
        if not expected_ok:
            status = "FAIL"
            reasons.append("exit_mismatch")
        if not json_ok:
            status = "FAIL"
            reasons.append(json_reason)
        if not stable_exit:
            status = "FAIL"
            reasons.append("non_deterministic_exit")
        if not stable_output:
            status = "FAIL"
            reasons.append("non_deterministic_output")

        results.append(
            {
                "name": contract["name"],
                "command": command,
                "expected_exit": expected_exit,
                "first_exit": first_exit,
                "second_exit": second_exit,
                "stable_exit": stable_exit,
                "stable_output": stable_output,
                "json_contract_ok": json_ok,
                "status": status,
                "reasons": reasons,
            }
        )

    fail_count = sum(1 for item in results if item["status"] == "FAIL")
    report = {
        "tool": "kernel_contracts",
        "contract_count": len(results),
        "fail_count": fail_count,
        "results": results,
    }
    return (1 if fail_count else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    code, report = run_contract_check()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
