from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "materialize-research-candidate-tree"
DEFAULT_OUTPUT_ROOT = Path("artifacts/research-candidate-tree/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("rct-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _candidate_summary(family: str, hypothesis_statement: str) -> str:
    if family == "baseline_reference":
        return f"Baseline candidate derived from branch: {hypothesis_statement}"
    if family == "reuse_direct":
        return f"Direct-reuse candidate derived from branch: {hypothesis_statement}"
    if family == "reuse_hybrid":
        return f"Hybrid-reuse candidate derived from branch: {hypothesis_statement}"
    if family == "novel_synthesized":
        return f"Novel synthesized candidate derived from branch: {hypothesis_statement}"
    return f"Candidate derived from branch: {hypothesis_statement}"


def _feasibility_priors(family: str, evidence_refs: list[str]) -> dict[str, Any]:
    if family == "baseline_reference":
        complexity = "low"
        dependency_risk = "low"
        implementation_risk = "low"
    elif family == "reuse_direct":
        complexity = "low"
        dependency_risk = "medium"
        implementation_risk = "medium"
    elif family == "reuse_hybrid":
        complexity = "medium"
        dependency_risk = "medium"
        implementation_risk = "medium"
    else:
        complexity = "high"
        dependency_risk = "medium"
        implementation_risk = "high"
    return {
        "expected_complexity": complexity,
        "dependency_risk": dependency_risk,
        "implementation_risk": implementation_risk,
        "evidence_strength": "supported" if evidence_refs else "unsupported",
    }


def _targeted_intent(problem: dict[str, Any]) -> dict[str, list[str] | str]:
    problem_id = str(problem.get("problem_id", "")).strip()
    statement = str(problem.get("problem_statement", "")).lower()
    artifact_targets = _string_list(problem.get("artifact_targets", []))
    criteria = _string_list(problem.get("evaluation_criteria", []))

    contract_changes: list[str] = []
    runtime_changes: list[str] = []
    validation_changes: list[str] = []
    docs_changes: list[str] = []
    handoff_requirements: list[str] = []

    if "evaluation-strength-contract-001" in problem_id or "evaluation strength" in statement:
        contract_changes.extend(
            [
                "spec/contracts/packet-schema-registry.yaml",
                "docs/core-contract-spec-v1.md",
                "add evaluation_strength to research_evaluation_packet",
                "add evaluation_basis details to distinguish evaluation support level",
                "define static_contract, artifact_backed, and execution_backed evaluation levels",
            ]
        )
        runtime_changes.extend(
            [
                "src/platform_tools/materialize_research_evaluations.py",
                "src/platform_tools/materialize_research_recommendation.py",
                "src/platform_tools/materialize_selected_solution_scope.py",
                "propagate evaluation_strength into recommendation ranking",
                "propagate evaluation_strength into selection policy gates",
            ]
        )
        validation_changes.extend(
            [
                "tests/test_materialize_research_evaluations.py",
                "tests/test_materialize_research_recommendation.py",
                "tests/test_materialize_selected_solution_scope.py",
                "uv run pytest tests/test_materialize_research_evaluations.py tests/test_materialize_research_recommendation.py tests/test_materialize_selected_solution_scope.py",
                "add tests proving static-only evidence cannot be represented as execution-backed",
            ]
        )
        docs_changes.extend(
            [
                "docs/research-candidate-evaluation-v1.md",
                "docs/research-recommendation-v1.md",
                "document evaluation strength semantics and gate propagation",
            ]
        )
        handoff_requirements.append("selected scope must expose evaluation strength for planner intake")
    elif "evidence-search-runtime-001" in problem_id or "evidence search" in statement:
        contract_changes.extend(
            [
                "spec/contracts/packet-schema-registry.yaml",
                "docs/core-contract-spec-v1.md",
                "add source search request and response packet shape",
                "add source_record contract",
                "add source ranking output with accepted and rejected sources",
                "add rejection reason codes",
            ]
        )
        runtime_changes.extend(
            [
                "src/platform_tools/review_evidence_adapter.py",
                "src/platform_tools/question_to_research_problem_transform.py",
                "emit evidence_packet from ranked source records",
                "preserve accepted and rejected source provenance",
            ]
        )
        validation_changes.extend(
            [
                "tests/test_review_evidence_adapter.py",
                "tests/test_question_to_research_problem_transform.py",
                "uv run pytest tests/test_review_evidence_adapter.py tests/test_question_to_research_problem_transform.py",
                "add tests for rejected-source traceability and evidence packet emission",
            ]
        )
        docs_changes.extend(
            [
                "docs/evidence-search-tool-v1.md",
                "docs/research-tool-v1.md",
                "document evidence search packet flow and rejection reasons",
            ]
        )
        handoff_requirements.append("planner handoff must include ranked source records and evidence packet refs")
    else:
        contract_changes.extend(
            [
                f"update contract target {target}"
                for target in artifact_targets
                if "packet" in target or "contract" in target or target.endswith(".yaml")
            ]
        )
        runtime_changes.extend(
            [
                f"materialize artifact target {target}"
                for target in artifact_targets
                if "packet" not in target and "contract" not in target
            ]
        )
        validation_changes.extend(
            [f"validate criterion: {criterion}" for criterion in criteria]
        )
        docs_changes.append("document implementation intent and downstream handoff expectations")
        handoff_requirements.append("carry implementation intent into recommendation and selection packets")

    if not contract_changes:
        contract_changes.append("confirm no contract changes are required")
    if not runtime_changes:
        runtime_changes.append("confirm no runtime changes are required")
    if not validation_changes:
        validation_changes.append("add validation for generated candidate intent")

    summary = (
        "Implementation-specific candidate intent for "
        f"{problem_id or str(problem.get('title', '')).strip() or 'research problem'}."
    )
    return {
        "summary": summary,
        "contract_changes": contract_changes,
        "runtime_changes": runtime_changes,
        "validation_changes": validation_changes,
        "docs_changes": docs_changes,
        "handoff_requirements": handoff_requirements,
    }


def materialize_research_candidate_tree(
    *,
    root: str = ".",
    research_problem_path: str,
    hypothesis_paths: list[str],
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    max_candidates: int = 8,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    problem = _load_json(repo_root / research_problem_path)
    hypotheses = [_load_json(repo_root / path) for path in hypothesis_paths]
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(problem.get("packet_type", "")).strip() != "research_problem_packet":
        blockers.append("research_problem_packet_type_invalid")
    problem_id = str(problem.get("problem_id", "")).strip()
    if not problem_id:
        blockers.append("research_problem_missing_problem_id")
    if not hypotheses:
        blockers.append("research_hypothesis_packets_missing")
    if max_candidates < 1:
        blockers.append("candidate_budget_invalid")

    normalized_hypotheses: list[dict[str, Any]] = []
    for index, hypothesis in enumerate(hypotheses, start=1):
        if str(hypothesis.get("packet_type", "")).strip() != "research_hypothesis_packet":
            blockers.append(f"research_hypothesis_packet_type_invalid:{index}")
            continue
        hypothesis_problem_id = str(hypothesis.get("problem_id", "")).strip()
        hypothesis_id = str(hypothesis.get("hypothesis_id", "")).strip()
        hypothesis_family = str(hypothesis.get("hypothesis_family", "")).strip()
        if hypothesis_problem_id != problem_id:
            blockers.append(f"research_hypothesis_problem_mismatch:{index}")
        if not hypothesis_id:
            blockers.append(f"research_hypothesis_missing_id:{index}")
        if not hypothesis_family:
            blockers.append(f"research_hypothesis_missing_family:{index}")
        normalized_hypotheses.append(hypothesis)

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "research_problem_path": str((repo_root / research_problem_path).resolve()),
                "hypothesis_paths": [str((repo_root / path).resolve()) for path in hypothesis_paths],
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "research-candidate-tree.report.json", report)
        return 1, report

    root_node_id = f"{problem_id}:candidate-search-root"
    tree_nodes: list[dict[str, Any]] = [
        {
            "node_id": root_node_id,
            "node_type": "research_problem",
            "packet_ref": str((repo_root / research_problem_path).resolve()),
            "label": str(problem.get("title", "")).strip() or problem_id,
        }
    ]
    tree_edges: list[dict[str, str]] = []
    candidate_packet_paths: list[str] = []
    decision_packet_paths: list[str] = []

    emitted = 0
    for index, hypothesis in enumerate(normalized_hypotheses, start=1):
        if emitted >= max_candidates:
            break
        hypothesis_id = str(hypothesis["hypothesis_id"]).strip()
        family = str(hypothesis["hypothesis_family"]).strip()
        hypothesis_node_id = f"{hypothesis_id}:tree-node"
        candidate_id = f"{hypothesis_id}:candidate:001"
        candidate_node_id = f"{candidate_id}:tree-node"
        evidence_refs = _string_list(hypothesis.get("evidence_refs", []))
        hypothesis_statement = str(hypothesis.get("hypothesis_statement", "")).strip()
        approach_outline = str(hypothesis.get("approach_outline", "")).strip()
        implementation_intent = _targeted_intent(problem)
        expected_changes = (
            list(implementation_intent["contract_changes"])
            + list(implementation_intent["runtime_changes"])
            + list(implementation_intent["validation_changes"])
            + list(implementation_intent["docs_changes"])
        )
        non_goals = _string_list(problem.get("constraints", []))
        if not non_goals:
            non_goals = ["do not expand beyond the stated research problem boundary"]

        tree_nodes.append(
            {
                "node_id": hypothesis_node_id,
                "node_type": "research_hypothesis",
                "packet_ref": str((repo_root / hypothesis_paths[index - 1]).resolve()),
                "label": family,
            }
        )
        tree_edges.append(
            {
                "edge_id": f"edge-root-{index:02d}",
                "from_node_id": hypothesis_node_id,
                "to_node_id": root_node_id,
                "relation": "derived_from",
            }
        )

        candidate_packet = {
            "packet_type": "research_candidate_packet",
            "packet_version": "v1",
            "packet_id": f"{candidate_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "candidate_id": candidate_id,
            "problem_id": problem_id,
            "source_hypothesis_id": hypothesis_id,
            "candidate_family": family,
            "approach_summary": _candidate_summary(family, hypothesis_statement),
            "assumptions": _string_list(hypothesis.get("constraints", [])),
            "proposed_changes": [approach_outline] if approach_outline else [],
            "implementation_intent": implementation_intent,
            "contract_changes": list(implementation_intent["contract_changes"]),
            "runtime_changes": list(implementation_intent["runtime_changes"]),
            "validation_changes": list(implementation_intent["validation_changes"]),
            "docs_changes": list(implementation_intent["docs_changes"]),
            "expected_changes": expected_changes,
            "non_goals": non_goals,
            "handoff_requirements": list(implementation_intent["handoff_requirements"]),
            "planner_entry_notes": [
                "candidate intent must be preserved before selected scope or execution-unit planning"
            ],
            "artifact_refs": [],
            "source_type": "hypothesis_tree_search",
            "evidence_refs": evidence_refs,
            "feasibility_priors": _feasibility_priors(family, evidence_refs),
            "risk_notes": _string_list(hypothesis.get("risk_notes", [])),
            "source_hypothesis_ref": str((repo_root / hypothesis_paths[index - 1]).resolve()),
        }
        candidate_path = write_json(
            run_root / f"research-candidate-{index:02d}.packet.json",
            candidate_packet,
        )
        candidate_packet_paths.append(candidate_path.as_posix())

        decision_id = f"{hypothesis_id}:expand:001"
        decision_packet = {
            "packet_type": "candidate_expansion_decision_packet",
            "packet_version": "v1",
            "packet_id": f"{decision_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "decision_id": decision_id,
            "problem_id": problem_id,
            "source_node_id": hypothesis_node_id,
            "decision": "expanded",
            "reason": "V1 expands one bounded candidate for each viable hypothesis branch.",
            "evidence_refs": evidence_refs,
            "resulting_node_refs": [candidate_node_id],
        }
        decision_path = write_json(
            run_root / f"candidate-expansion-decision-{index:02d}.packet.json",
            decision_packet,
        )
        decision_packet_paths.append(decision_path.as_posix())

        tree_nodes.append(
            {
                "node_id": candidate_node_id,
                "node_type": "research_candidate",
                "packet_ref": candidate_path.as_posix(),
                "label": candidate_id,
            }
        )
        tree_edges.append(
            {
                "edge_id": f"edge-candidate-{index:02d}",
                "from_node_id": candidate_node_id,
                "to_node_id": hypothesis_node_id,
                "relation": "expanded_from",
            }
        )
        emitted += 1

    search_tree_packet = {
        "packet_type": "candidate_search_tree_packet",
        "packet_version": "v1",
        "packet_id": f"{problem_id}:candidate-search-tree",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "problem_id": problem_id,
        "root_node_id": root_node_id,
        "tree_nodes": tree_nodes,
        "tree_edges": tree_edges,
        "search_policy": {
            "strategy": "bounded_breadth_first",
            "max_depth": 2,
            "max_candidates": max_candidates,
            "candidate_per_hypothesis_v1": 1,
        },
        "candidate_packet_refs": candidate_packet_paths,
        "expansion_decision_refs": decision_packet_paths,
    }
    search_tree_path = write_json(run_root / "candidate-search-tree.packet.json", search_tree_packet)

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "research_problem_path": str((repo_root / research_problem_path).resolve()),
            "hypothesis_paths": [str((repo_root / path).resolve()) for path in hypothesis_paths],
            "candidate_search_tree_path": search_tree_path.as_posix(),
            "candidate_packet_paths": candidate_packet_paths,
            "expansion_decision_packet_paths": decision_packet_paths,
            "candidate_count": len(candidate_packet_paths),
            "blockers": [],
        },
    )
    write_json(run_root / "research-candidate-tree.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--research-problem-path", required=True)
    parser.add_argument("--hypothesis", action="append", dest="hypotheses", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--max-candidates", type=int, default=8)
    args = parser.parse_args()
    try:
        code, report = materialize_research_candidate_tree(
            root=args.root,
            research_problem_path=args.research_problem_path,
            hypothesis_paths=args.hypotheses,
            output_root=args.output_root,
            max_candidates=args.max_candidates,
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
