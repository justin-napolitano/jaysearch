from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.run_jaysearch_ci import CORE_TESTS, check_plan


def test_jaysearch_ci_excludes_legacy_platform_tests() -> None:
    assert "tests/test_governed_worker.py" not in CORE_TESTS
    assert "tests/test_policy_compliance_check.py" not in CORE_TESTS
    assert "tests/test_worker_session_coordinator.py" not in CORE_TESTS


def test_jaysearch_ci_includes_core_execution_path() -> None:
    commands = [item.command for item in check_plan()]
    flattened = [part for command in commands for part in command]

    assert "tests/test_run_jaysearch_demo.py" in flattened
    assert "tests/test_candidate_patch_manifest_contracts.py" in flattened
    assert "tests/test_materialize_selected_dag_execution_units.py" in flattened
    assert "tests/test_run_execution_era_loop_smoke.py" in flattened
    assert "tests/test_design_iteration.py" in flattened
    assert ["bin/design-iteration", "--root", "."] in commands
