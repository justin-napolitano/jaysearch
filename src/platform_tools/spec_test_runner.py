from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from platform_tools.plan_utils import list_execplans, parse_plan


def _collect_tests() -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    for path in list_execplans():
        parsed = parse_plan(path)
        fm = parsed.frontmatter
        if not fm:
            continue
        plan_id = str(fm.get("id", "")).strip() or path.stem
        validation = fm.get("validation", {})
        if not isinstance(validation, dict):
            continue
        test_defs = validation.get("tests", [])
        if not isinstance(test_defs, list):
            continue
        for idx, t in enumerate(test_defs):
            if not isinstance(t, dict):
                continue
            tests.append(
                {
                    "plan_id": plan_id,
                    "order": idx,
                    "name": str(t.get("name", f"test_{idx}")),
                    "command": str(t.get("command", "")).strip(),
                    "expected_exit": int(t.get("expected_exit", 0)),
                }
            )
    tests.sort(key=lambda x: (x["plan_id"], x["order"], x["name"]))
    return tests


def run_tests() -> tuple[int, dict[str, Any]]:
    tests = _collect_tests()
    results: list[dict[str, Any]] = []

    for test in tests:
        cmd = test["command"]
        if not cmd:
            results.append({**test, "status": "FAIL", "actual_exit": None, "reason": "empty_command"})
            continue

        # Avoid infinite recursion for self-referential plan tests.
        if "bin/execplan-test" in cmd and os.environ.get("EXECPLAN_TEST_RUNNING") == "1":
            results.append({**test, "status": "SKIP", "actual_exit": 0, "reason": "recursive_self_reference"})
            continue

        env = dict(os.environ)
        env["EXECPLAN_TEST_RUNNING"] = "1"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env, check=False)
        actual = proc.returncode
        status = "PASS" if actual == test["expected_exit"] else "FAIL"
        results.append({**test, "status": status, "actual_exit": actual})

    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    skip_count = sum(1 for r in results if r["status"] == "SKIP")

    report = {
        "tool": "spec_test_runner",
        "test_count": len(results),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
        "results": results,
    }
    return (1 if fail_count else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    code, report = run_tests()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
