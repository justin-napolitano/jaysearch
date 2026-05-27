from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.materialize_selected_dag_execution_units import (
    materialize_selected_dag_execution_units,
)
from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json
from platform_tools.run_execution_era_loop_smoke import run_execution_era_loop_smoke
from platform_tools.select_candidate_dag import select_candidate_dag


COMMAND = "run-jaysearch-demo"
DEFAULT_OUTPUT_ROOT = Path("artifacts/demo/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("demo-%Y%m%dT%H%M%SZ")


def _node(node_id: str, *, node_type: str, title: str, goal: str) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "title": title,
        "node_type": node_type,
        "status": "planned",
        "goal": goal,
        "owned_changes": [f"demo/{node_id}.artifact"],
        "expected_outputs": [f"{title} output"],
        "validation_commands": ["uv run pytest tests/test_run_jaysearch_demo.py"],
        "evidence_refs": [
            "docs/jaysearch-demo-runner-v1.md",
            "docs/selected-dag-execution-units-v1.md",
        ],
    }


def _dag(graph_id: str, nodes: list[dict[str, Any]], edges: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "graph_id": graph_id,
        "graph_type": "implementation_dag",
        "version": "v1",
        "purpose": "Demo candidate graph for Jaysearch graph-to-execution flow.",
        "source_artifacts": [
            "docs/jaysearch-demo-runner-v1.md",
            "docs/candidate-dag-selection-v1.md",
        ],
        "nodes": nodes,
        "edges": edges,
    }


def _write_fixture_inputs(repo_root: Path, run_root: Path) -> str:
    input_root = run_root / "inputs"
    compact_path = write_json(
        input_root / "compact-plan-dag.json",
        _dag(
            "demo-compact-plan",
            [
                _node(
                    "define_contract",
                    node_type="contract",
                    title="Define contract",
                    goal="Define the minimum packet contract needed for a bounded build step.",
                ),
                _node(
                    "implement_runtime",
                    node_type="runtime",
                    title="Implement runtime",
                    goal="Implement the command that consumes the contract.",
                ),
                _node(
                    "validate_flow",
                    node_type="validation",
                    title="Validate flow",
                    goal="Validate the contract and runtime as one executable slice.",
                ),
            ],
            [
                {
                    "edge_id": "e1",
                    "from_node_id": "implement_runtime",
                    "to_node_id": "define_contract",
                    "relation": "depends_on",
                },
                {
                    "edge_id": "e2",
                    "from_node_id": "validate_flow",
                    "to_node_id": "implement_runtime",
                    "relation": "depends_on",
                },
            ],
        ),
    )
    bloated_path = write_json(
        input_root / "over-split-plan-dag.json",
        _dag(
            "demo-over-split-plan",
            [
                _node(f"micro_step_{index}", node_type="runtime", title=f"Micro step {index}", goal="Over-split the work.")
                for index in range(1, 11)
            ],
            [
                {
                    "edge_id": f"e{index}",
                    "from_node_id": f"micro_step_{index + 1}",
                    "to_node_id": f"micro_step_{index}",
                    "relation": "depends_on",
                }
                for index in range(1, 10)
            ],
        ),
    )
    invalid_path = write_json(
        input_root / "invalid-cycle-dag.json",
        _dag(
            "demo-invalid-cycle",
            [
                _node("cycle_a", node_type="runtime", title="Cycle A", goal="Invalid cyclic node A."),
                _node("cycle_b", node_type="runtime", title="Cycle B", goal="Invalid cyclic node B."),
            ],
            [
                {
                    "edge_id": "cycle-1",
                    "from_node_id": "cycle_a",
                    "to_node_id": "cycle_b",
                    "relation": "depends_on",
                },
                {
                    "edge_id": "cycle-2",
                    "from_node_id": "cycle_b",
                    "to_node_id": "cycle_a",
                    "relation": "depends_on",
                },
            ],
        ),
    )
    manifest_path = write_json(
        input_root / "candidate-dag-manifest.packet.json",
        {
            "packet_type": "candidate_dag_manifest",
            "packet_version": "v1",
            "packet_id": "candidate-dag-manifest:jaysearch-demo:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "manifest_id": "jaysearch-demo",
            "source_problem_ref": "demo:interview-presentation",
            "source_execplan_ref": ".agent/execplans/20260527-jaysearch-demo-runner-v1-codex-01-execplan.md",
            "candidate_dag_refs": [
                {
                    "candidate_id": "compact",
                    "dag_ref": compact_path.relative_to(repo_root).as_posix(),
                    "candidate_family": "bounded",
                    "source_label": "compact graph",
                    "producer_ref": COMMAND,
                    "evidence_refs": ["docs/jaysearch-demo-runner-v1.md"],
                    "blockers": [],
                },
                {
                    "candidate_id": "over_split",
                    "dag_ref": bloated_path.relative_to(repo_root).as_posix(),
                    "candidate_family": "over_split",
                    "source_label": "over-split graph",
                    "producer_ref": COMMAND,
                    "evidence_refs": ["docs/jaysearch-demo-runner-v1.md"],
                    "blockers": [],
                },
                {
                    "candidate_id": "cycle",
                    "dag_ref": invalid_path.relative_to(repo_root).as_posix(),
                    "candidate_family": "invalid",
                    "source_label": "cyclic graph",
                    "producer_ref": COMMAND,
                    "evidence_refs": ["docs/jaysearch-demo-runner-v1.md"],
                    "blockers": [],
                },
            ],
            "selection_policy_ref": "docs/candidate-dag-selection-v1.md",
            "evidence_refs": [
                "docs/candidate-dag-selection-v1.md",
                "docs/selected-dag-execution-units-v1.md",
            ],
            "blockers": [],
        },
    )
    return manifest_path.relative_to(repo_root).as_posix()


def _load_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _summary_markdown(report: dict[str, Any]) -> str:
    selected = report.get("selected_candidate_id", "")
    execution_unit_paths = report.get("execution_unit_paths", [])
    rejected = report.get("rejected_candidate_ids", [])
    era_status = report.get("era_smoke_status", "")
    return "\n".join(
        [
            "# Jaysearch Demo Summary",
            "",
            "## What This Shows",
            "",
            "- Jaysearch evaluates multiple candidate DAGs.",
            "- Invalid or weaker DAGs remain visible.",
            "- The selected DAG becomes execution-unit packets.",
            "- One execution unit enters the existing ERA smoke loop.",
            "",
            "## Result",
            "",
            f"- Selected candidate: `{selected}`",
            f"- Rejected candidates: `{', '.join(rejected)}`",
            f"- Execution units emitted: `{len(execution_unit_paths)}`",
            f"- ERA smoke status: `{era_status}`",
            "",
            "## Important Non-Claims",
            "",
            "- This demo does not perform autonomous code synthesis.",
            "- This demo does not apply patches to the source worktree.",
            "- Candidate generation request/result is the next production slice.",
            "",
        ]
    )


def run_jaysearch_demo(
    *,
    root: str = ".",
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    include_era_smoke: bool = True,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    manifest_path = _write_fixture_inputs(repo_root, run_root)
    selection_code, selection_report = select_candidate_dag(
        root=repo_root.as_posix(),
        manifest_path=manifest_path,
        output_root=f"{output_root}/{run_id}/selection",
    )
    blockers = [f"select_candidate_dag:{item}" for item in selection_report.get("blockers", [])]

    materialization_report: dict[str, Any] = {}
    materialization_code = 1
    if selection_code == 0:
        materialization_code, materialization_report = materialize_selected_dag_execution_units(
            root=repo_root.as_posix(),
            selection_path=str(selection_report.get("candidate_dag_selection_path", "")),
            output_root=f"{output_root}/{run_id}/execution-units",
        )
        blockers.extend(
            f"materialize_selected_dag_execution_units:{item}"
            for item in materialization_report.get("blockers", [])
        )

    execution_unit_paths = [str(path) for path in materialization_report.get("execution_unit_paths", [])]
    era_report: dict[str, Any] = {}
    era_code = 0
    if include_era_smoke and not blockers and execution_unit_paths:
        first_execution_unit = Path(execution_unit_paths[0]).relative_to(repo_root).as_posix()
        validation_evidence_path = write_json(
            run_root / "demo-validation-evidence.result.json",
            {
                "packet_type": "demo_validation_evidence",
                "packet_version": "v1",
                "created_at": _utc_now(),
                "producer": COMMAND,
                "status": "passed",
                "summary": "Demo fixture validation evidence for metadata-only ERA smoke path.",
                "source_execution_unit_ref": execution_unit_paths[0],
            },
        )
        era_code, era_report = run_execution_era_loop_smoke(
            root=repo_root.as_posix(),
            execution_unit_path=first_execution_unit,
            output_root=f"{output_root}/{run_id}/era-smoke",
            validation_result_ref=validation_evidence_path.as_posix(),
        )
        blockers.extend(f"run_execution_era_loop_smoke:{item}" for item in era_report.get("blockers", []))

    score_summary = selection_report.get("score_summary", [])
    selected_dag_ref = str(selection_report.get("selected_dag_ref", ""))
    selected_candidate_id = ""
    rejected_candidate_ids: list[str] = []
    if isinstance(score_summary, list):
        for item in score_summary:
            if not isinstance(item, dict):
                continue
            candidate_id = str(item.get("candidate_id", ""))
            if str(item.get("candidate_dag_ref", "")) == selected_dag_ref:
                selected_candidate_id = candidate_id
            else:
                rejected_candidate_ids.append(candidate_id)

    demo_report = {
        "command": COMMAND,
        "status": "ok" if not blockers and selection_code == 0 and materialization_code == 0 and era_code == 0 else "blocked",
        "ok": not blockers and selection_code == 0 and materialization_code == 0 and era_code == 0,
        "run_id": run_id,
        "manifest_path": str((repo_root / manifest_path).resolve()),
        "candidate_dag_selection_path": str(selection_report.get("candidate_dag_selection_path", "")),
        "selected_candidate_id": selected_candidate_id,
        "selected_dag_ref": selected_dag_ref,
        "rejected_candidate_ids": rejected_candidate_ids,
        "dag_execution_unit_manifest_path": str(
            materialization_report.get("dag_execution_unit_manifest_path", "")
        ),
        "execution_unit_paths": execution_unit_paths,
        "era_smoke_report_path": str(era_report.get("smoke_packet_path", "")),
        "era_smoke_status": str(era_report.get("status", "skipped" if not include_era_smoke else "blocked")),
        "explicit_non_claims": [
            "no autonomous code synthesis",
            "no source worktree patch application",
            "fixture-backed demo inputs",
        ],
        "blockers": sorted(set(blockers)),
    }
    demo_report_path = write_json(run_root / "demo-report.json", demo_report)
    summary_path = run_root / "demo-summary.md"
    summary_path.write_text(_summary_markdown(demo_report), encoding="utf-8")

    report = envelope(
        command=COMMAND,
        status=str(demo_report["status"]),
        ok=bool(demo_report["ok"]),
        payload={
            **demo_report,
            "demo_report_path": demo_report_path.as_posix(),
            "demo_summary_path": summary_path.as_posix(),
        },
    )
    write_json(run_root / "run-jaysearch-demo.report.json", report)
    return (0 if report["ok"] else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--skip-era-smoke", action="store_true")
    args = parser.parse_args()
    try:
        code, report = run_jaysearch_demo(
            root=args.root,
            output_root=args.output_root,
            include_era_smoke=not args.skip_era_smoke,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
