from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from typing import Any


COMMAND = "run-jaysearch-ci"


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str]


CORE_TESTS = [
    "tests/test_run_jaysearch_demo.py",
    "tests/test_dag_execution_unit_manifest_contracts.py",
    "tests/test_materialize_selected_dag_execution_units.py",
    "tests/test_candidate_dag_contracts.py",
    "tests/test_select_candidate_dag.py",
    "tests/test_candidate_patch_manifest_contracts.py",
    "tests/test_materialize_candidate_patch_manifest.py",
    "tests/test_select_implementation_attempt.py",
    "tests/test_attempt_selection_contracts.py",
    "tests/test_apply_solution_artifact.py",
    "tests/test_applied_solution_contracts.py",
    "tests/test_run_execution_era_loop_smoke.py",
    "tests/test_generate_implementation_attempt.py",
    "tests/test_evaluate_implementation_attempt.py",
    "tests/test_emit_solution_artifact.py",
    "tests/test_execution_era_contracts.py",
    "tests/test_materialize_execution_unit.py",
    "tests/test_validate_node_readiness.py",
]

DESIGN_TESTS = [
    "tests/test_design_iteration.py",
]

RUNTIME_TESTS = [
    "tests/test_run_jaysearch_ci.py",
]


def check_plan(*, include_design_iteration: bool = True) -> list[Check]:
    checks = [
        Check(name="jaysearch-runtime-tests", command=["uv", "run", "pytest", *RUNTIME_TESTS]),
        Check(name="jaysearch-core-tests", command=["uv", "run", "pytest", *CORE_TESTS]),
        Check(name="jaysearch-design-tests", command=["uv", "run", "pytest", *DESIGN_TESTS]),
    ]
    if include_design_iteration:
        checks.append(Check(name="jaysearch-design-iteration", command=["bin/design-iteration", "--root", "."]))
    return checks


def run_jaysearch_ci(*, include_design_iteration: bool = True) -> tuple[int, dict[str, Any]]:
    results: list[dict[str, Any]] = []
    overall_exit = 0
    for check in check_plan(include_design_iteration=include_design_iteration):
        proc = subprocess.run(check.command, capture_output=True, text=True, check=False)
        output = proc.stdout if proc.stdout else proc.stderr
        result = {
            "name": check.name,
            "command": check.command,
            "exit_code": proc.returncode,
            "output": output,
        }
        results.append(result)
        if proc.returncode != 0 and overall_exit == 0:
            overall_exit = 1

    report = {
        "command": COMMAND,
        "status": "ok" if overall_exit == 0 else "blocked",
        "ok": overall_exit == 0,
        "profile": "jaysearch-core",
        "legacy_platform_ci_excluded": True,
        "checks": results,
    }
    return overall_exit, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-design-iteration",
        action="store_true",
        help="Run pytest-based Jaysearch checks only.",
    )
    args = parser.parse_args()
    code, report = run_jaysearch_ci(include_design_iteration=not args.skip_design_iteration)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
