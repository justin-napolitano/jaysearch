from __future__ import annotations

import argparse
import json
import os
import subprocess
from typing import Any


def _command_list() -> list[str]:
    commands = [
        "bin/execplan-validate .agent/execplans/*.md",
        "bin/sync-todos",
        "bin/governance-check",
        "bin/distribution-check",
        "bin/repo-health-check",
        "bin/kernel-contract-check",
    ]
    if os.environ.get("EXECPLAN_TEST_RUNNING") != "1":
        commands.append("bin/execplan-test")
    return commands


def run_local_ci() -> tuple[int, dict[str, Any]]:
    commands = _command_list()
    results: list[dict[str, Any]] = []
    overall = 0

    for command in commands:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        code = proc.returncode
        results.append(
            {
                "command": command,
                "exit_code": code,
                "output": proc.stdout if proc.stdout else proc.stderr,
            }
        )
        if code == 2:
            overall = 2
        elif code != 0 and overall != 2:
            overall = 1

    report = {"tool": "run_local_ci", "overall_exit": overall, "commands": results}
    return overall, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    code, report = run_local_ci()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
