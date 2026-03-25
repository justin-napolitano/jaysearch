from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.worker_runtime_artifact_check import check_worker_runtime_artifacts


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, payloads: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(item, sort_keys=True) for item in payloads) + "\n", encoding="utf-8")


def _seed_schemas(root: Path) -> None:
    _write(root / "spec" / "worker-runtime-event.schema.yaml", Path("spec/worker-runtime-event.schema.yaml").read_text(encoding="utf-8"))
    _write(root / "spec" / "worker-problem-artifact.schema.yaml", Path("spec/worker-problem-artifact.schema.yaml").read_text(encoding="utf-8"))


def test_worker_runtime_artifact_check_accepts_valid_artifacts(tmp_path: Path) -> None:
    _seed_schemas(tmp_path)
    _write_jsonl(
        tmp_path / "artifacts" / "governance" / "worker-runtime-events.jsonl",
        [
            {
                "specversion": "1.0",
                "id": "evt-1",
                "type": "platform.worker.run.started",
                "source": "platform_tools/governed_worker",
                "subject": "run-1",
                "time": "2026-03-25T00:00:00Z",
                "datacontenttype": "application/json",
                "data": {
                    "run_id": "run-1",
                    "trace_id": "trace-1",
                    "worker_id": "worker-1",
                    "branch": "impl-execplan/worker-1",
                    "initiative_id": "initiative-example",
                    "contract_id": "contract-1",
                    "summary": "started",
                },
            }
        ],
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "worker-runs" / "run-1.json",
        {
            "run_id": "run-1",
            "trace_id": "trace-1",
            "worker_id": "worker-1",
            "branch": "impl-execplan/worker-1",
            "executor_backend": "clone",
            "push_targets": [],
            "token_economy_policy": {},
            "problem_ref": "artifacts/governance/problems/run-1.problem.json",
        },
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "problems" / "run-1.problem.json",
        {
            "type": "https://platform.local/problems/test",
            "title": "problem",
            "status": 409,
            "detail": "compact detail",
            "instance": "run-1",
            "error_code": "TEST",
            "retryable": False,
            "initiative_id": "initiative-example",
            "worker_id": "worker-1",
            "contract_id": "contract-1",
            "execplan_id": "plan-id",
            "branch": "impl-execplan/worker-1",
            "executor_backend": "clone",
            "trace_id": "trace-1",
            "what_you_should_do": "repair and retry",
        },
    )
    _write(
        tmp_path / "artifacts" / "governance" / "problems" / "run-1.problem.md",
        "# problem\n",
    )

    code, report = check_worker_runtime_artifacts(root=tmp_path.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["counts"]["runtime_events"] == 1
    assert report["counts"]["runs"] == 1
    assert report["counts"]["problems"] == 1


def test_worker_runtime_artifact_check_rejects_invalid_artifacts(tmp_path: Path) -> None:
    _seed_schemas(tmp_path)
    _write_jsonl(
        tmp_path / "artifacts" / "governance" / "worker-runtime-events.jsonl",
        [
            {
                "specversion": "1.0",
                "id": "evt-1",
                "type": "bad.type",
                "source": "platform_tools/governed_worker",
                "subject": "run-1",
                "time": "2026-03-25T00:00:00Z",
                "datacontenttype": "application/json",
                "data": {
                    "run_id": "run-1",
                    "trace_id": "trace-1",
                    "worker_id": "worker-1",
                    "branch": "impl-execplan/worker-1",
                    "initiative_id": "initiative-example",
                    "contract_id": "contract-1",
                    "summary": "x" * 200,
                },
            }
        ],
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "worker-runs" / "run-1.json",
        {
            "run_id": "run-1",
            "trace_id": "trace-1",
            "worker_id": "worker-1",
            "branch": "impl-execplan/worker-1",
            "executor_backend": "clone",
            "push_targets": [],
            "token_economy_policy": {},
            "problem_ref": "artifacts/governance/problems/run-1.problem.json",
        },
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "problems" / "run-1.problem.json",
        {
            "type": "https://platform.local/problems/test",
            "title": "problem",
            "status": "409",
            "detail": "x" * 400,
            "instance": "run-1",
            "error_code": "TEST",
            "retryable": False,
            "initiative_id": "initiative-example",
            "worker_id": "worker-1",
            "contract_id": "contract-1",
            "execplan_id": "plan-id",
            "branch": "impl-execplan/worker-1",
            "executor_backend": "clone",
            "trace_id": "trace-1",
            "what_you_should_do": "repair and retry",
        },
    )

    code, report = check_worker_runtime_artifacts(root=tmp_path.as_posix())

    assert code == 1
    assert "invalid_runtime_event_type:1:bad.type" in report["errors"]
    assert "runtime_event_summary_too_long:1" in report["errors"]
    assert "invalid_problem_status_type:run-1.problem.json" in report["errors"]
    assert "problem_detail_too_long:run-1.problem.json" in report["errors"]
    assert "missing_problem_markdown:run-1.problem.md" in report["errors"]
