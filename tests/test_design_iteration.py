from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.design_iteration import run_design_iteration
from platform_tools.public_orchestration_api import API_VERSION


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_docs(root: Path) -> None:
    _write(root / "docs" / "design-iteration-tool-v1.md", "design iteration critique only\n")
    _write(root / "docs" / "governance-tool-v1.md", "governance evaluates explicit runnable contracts\n")
    _write(root / "docs" / "orchestration-runner-v1.md", "runner executes workflows and routes packets\n")
    _write(root / "docs" / "question-tool-v1.md", "question tool refines bounded research questions\n")


def _seed_plan_quality_policy(root: Path) -> None:
    _write(
        root / "spec" / "plan-quality-scoring.yaml",
        "\n".join(
            [
                "version: v1",
                "decision_policy:",
                "  type: gated_lexicographic",
                "hard_gates:",
                "  - gate_id: acyclic_execution_graph",
                "primary_metrics:",
                "  - metric_id: BDS",
                "    weight: 0.24",
            ]
        )
        + "\n",
    )


def test_design_iteration_blocks_on_missing_artifacts(tmp_path: Path) -> None:
    code, report = run_design_iteration(root=tmp_path.as_posix())

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert report["command"] == "design-iteration"
    assert report["status"] == "blocked"
    assert "registry_path_missing" in report["blockers"]
    assert "plan_quality_scoring_path_missing" in report["blockers"]


def test_design_iteration_emits_required_field_findings_for_registry(tmp_path: Path) -> None:
    _seed_docs(tmp_path)
    _seed_plan_quality_policy(tmp_path)
    _write(
        tmp_path / "spec" / "contracts" / "packet-schema-registry.yaml",
        "\n".join(
            [
                "version: 1",
                "contract_families:",
                "  - contract_name: packet_base",
                "    contract_kind: packet",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    status: active",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "contracts" / "design-iteration-checks.yaml",
        "\n".join(
            [
                "version: 1",
                "validator_families:",
                "  - family: contract_consistency_checks",
                "    checks:",
                "      - check_id: contract_required_fields_defined",
                "        finding_type: missing_required_fields_definition",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: every_shared_contract_lists_required_fields",
                "      - check_id: registry_entry_missing",
                "        finding_type: missing_registry_entry",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: shared_contracts_must_be_in_registry",
                "      - check_id: contract_owner_defined",
                "        finding_type: missing_contract_owner",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: every_shared_contract_has_one_canonical_owner",
                "      - check_id: contract_version_defined",
                "        finding_type: missing_contract_version",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: every_shared_contract_has_one_declared_version",
                "      - check_id: versioning_policy_missing",
                "        finding_type: versioning_policy_missing",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: packet_families_must_declare_compatibility_policy",
                "  - family: dag_consistency_checks",
                "    checks:",
                "      - check_id: dag_dependency_cycle",
                "        finding_type: dependency_cycle",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: dependency_graph_must_be_acyclic",
                "      - check_id: dag_unsatisfied_input_contract",
                "        finding_type: unsatisfied_input_contract",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: node_inputs_must_be_satisfiable",
                "      - check_id: dag_node_type_valid",
                "        finding_type: invalid_node_type",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: dag_nodes_use_allowed_types",
                "      - check_id: dag_edge_relation_valid",
                "        finding_type: invalid_edge_relation",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: dag_edges_use_allowed_relations",
                "      - check_id: workflow_to_implementation_link_missing",
                "        finding_type: missing_workflow_graph_link",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: workflow_and_implementation_graph_link_must_be_canonical",
                "  - family: boundary_leakage_checks",
                "    checks: []",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "design-iteration-tool-dag-v1.json",
        json.dumps(
            {
                "graph_id": "design-iteration-tool-dag-v1",
                "graph_kind": "workflow_dag",
                "nodes": [
                    {
                        "node_id": "dit-001",
                        "node_type": "tool_invocation",
                        "output_packet_refs": ["normalized_design_context"],
                        "input_packet_refs": [],
                    }
                ],
                "edges": [],
            }
        )
        + "\n",
    )

    code, report = run_design_iteration(root=tmp_path.as_posix())

    assert code == 1
    assert report["api_version"] == API_VERSION
    findings_packet = json.loads(Path(report["findings_packet_path"]).read_text(encoding="utf-8"))
    check_ids = {item["check_id"] for item in findings_packet["findings"]}
    assert "contract_required_fields_defined" in check_ids
    assert "registry_entry_missing" in check_ids


def test_design_iteration_detects_cycle_and_unsatisfied_input(tmp_path: Path) -> None:
    _seed_docs(tmp_path)
    _seed_plan_quality_policy(tmp_path)
    _write(
        tmp_path / "spec" / "contracts" / "packet-schema-registry.yaml",
        "\n".join(
            [
                "version: 1",
                "contract_families:",
                "  - contract_name: packet_base",
                "    contract_kind: packet",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [packet_type]",
                "  - contract_name: message_envelope",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [command]",
                "  - contract_name: workflow_request_packet",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [workflow_id]",
                "  - contract_name: run_status_packet",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [status]",
                "  - contract_name: failure_packet",
                "    contract_kind: packet",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [summary]",
                "  - contract_name: research_question_packet",
                "    contract_kind: packet",
                "    owner: question-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [question_id]",
                "  - contract_name: evidence_packet",
                "    contract_kind: packet",
                "    owner: evidence-search-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [evidence_id]",
                "  - contract_name: research_problem_packet",
                "    contract_kind: packet",
                "    owner: research-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [problem_id]",
                "  - contract_name: question_to_research_problem_transform",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [transform_id]",
                "  - contract_name: research_recommendation_packet",
                "    contract_kind: packet",
                "    owner: research-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [recommendation_id]",
                "  - contract_name: selected_solution_scope",
                "    contract_kind: packet",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [solution_scope_id]",
                "  - contract_name: planning_request_packet",
                "    contract_kind: packet",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [planning_request_id]",
                "  - contract_name: implementation_graph_packet",
                "    contract_kind: dag",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [graph_id]",
                "  - contract_name: execution_packet",
                "    contract_kind: packet",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [execution_id]",
                "  - contract_name: planner_to_governance_runnable_contract",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [contract_id]",
                "  - contract_name: governance_decision_packet",
                "    contract_kind: packet",
                "    owner: governance-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [decision_id]",
                "  - contract_name: dag_node",
                "    contract_kind: dag",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [node_id]",
                "  - contract_name: dag_edge",
                "    contract_kind: dag",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [edge_id]",
                "  - contract_name: workflow_dag_to_implementation_dag_link_contract",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [link_id]",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "contracts" / "design-iteration-checks.yaml",
        "\n".join(
            [
                "version: 1",
                "validator_families:",
                "  - family: contract_consistency_checks",
                "    checks:",
                "      - check_id: contract_required_fields_defined",
                "        finding_type: missing_required_fields_definition",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: every_shared_contract_lists_required_fields",
                "      - check_id: registry_entry_missing",
                "        finding_type: missing_registry_entry",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: shared_contracts_must_be_in_registry",
                "      - check_id: contract_owner_defined",
                "        finding_type: missing_contract_owner",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: every_shared_contract_has_one_canonical_owner",
                "      - check_id: contract_version_defined",
                "        finding_type: missing_contract_version",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: every_shared_contract_has_one_declared_version",
                "      - check_id: versioning_policy_missing",
                "        finding_type: versioning_policy_missing",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: packet_families_must_declare_compatibility_policy",
                "      - check_id: missing_transform_contract",
                "        finding_type: missing_transform_contract",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: operationally_linked_packet_families_need_canonical_transform",
                "  - family: dag_consistency_checks",
                "    checks:",
                "      - check_id: dag_dependency_cycle",
                "        finding_type: dependency_cycle",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: dependency_graph_must_be_acyclic",
                "      - check_id: dag_unsatisfied_input_contract",
                "        finding_type: unsatisfied_input_contract",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: node_inputs_must_be_satisfiable",
                "      - check_id: dag_node_type_valid",
                "        finding_type: invalid_node_type",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: dag_nodes_use_allowed_types",
                "      - check_id: dag_edge_relation_valid",
                "        finding_type: invalid_edge_relation",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: dag_edges_use_allowed_relations",
                "      - check_id: workflow_to_implementation_link_missing",
                "        finding_type: missing_workflow_graph_link",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: workflow_and_implementation_graph_link_must_be_canonical",
                "      - check_id: governance_gate_without_runnable_contract",
                "        finding_type: missing_runnable_contract_fields",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: governance_needs_explicit_runnable_contract",
                "  - family: boundary_leakage_checks",
                "    checks: []",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "design-iteration-tool-dag-v1.json",
        json.dumps(
            {
                "graph_id": "design-iteration-tool-dag-v1",
                "graph_kind": "workflow_dag",
                "nodes": [
                    {
                        "node_id": "dit-001",
                        "node_type": "tool_invocation",
                        "input_packet_refs": ["missing_input"],
                        "output_packet_refs": ["normalized_design_context"],
                    },
                    {
                        "node_id": "dit-002",
                        "node_type": "tool_invocation",
                        "input_packet_refs": ["normalized_design_context"],
                        "output_packet_refs": ["contract_artifact_set"],
                    },
                ],
                "edges": [
                    {"edge_id": "e-1", "from_node_id": "dit-001", "to_node_id": "dit-002", "relation": "depends_on"},
                    {"edge_id": "e-2", "from_node_id": "dit-002", "to_node_id": "dit-001", "relation": "depends_on"},
                ],
            }
        )
        + "\n",
    )

    code, report = run_design_iteration(root=tmp_path.as_posix())

    assert code == 1
    findings_packet = json.loads(Path(report["findings_packet_path"]).read_text(encoding="utf-8"))
    check_ids = {item["check_id"] for item in findings_packet["findings"]}
    assert "dag_dependency_cycle" in check_ids
    assert "dag_unsatisfied_input_contract" in check_ids
    assert report["question_candidate_count"] >= 1


def test_design_iteration_inspects_linked_implementation_graph(tmp_path: Path) -> None:
    _seed_docs(tmp_path)
    _seed_plan_quality_policy(tmp_path)
    _write(
        tmp_path / "spec" / "contracts" / "packet-schema-registry.yaml",
        "\n".join(
            [
                "version: 1",
                "contract_families:",
                "  - contract_name: packet_base",
                "    contract_kind: packet",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [packet_type]",
                "  - contract_name: message_envelope",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [command]",
                "  - contract_name: workflow_request_packet",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [workflow_id]",
                "  - contract_name: run_status_packet",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [status]",
                "  - contract_name: failure_packet",
                "    contract_kind: packet",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [summary]",
                "  - contract_name: research_question_packet",
                "    contract_kind: packet",
                "    owner: question-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [question_id]",
                "  - contract_name: evidence_packet",
                "    contract_kind: packet",
                "    owner: evidence-search-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [evidence_id]",
                "  - contract_name: research_problem_packet",
                "    contract_kind: packet",
                "    owner: research-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [problem_id]",
                "  - contract_name: question_to_research_problem_transform",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [transform_id]",
                "  - contract_name: research_recommendation_packet",
                "    contract_kind: packet",
                "    owner: research-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [recommendation_id]",
                "  - contract_name: selected_solution_scope",
                "    contract_kind: packet",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [solution_scope_id]",
                "  - contract_name: planning_request_packet",
                "    contract_kind: packet",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [planning_request_id]",
                "  - contract_name: implementation_graph_packet",
                "    contract_kind: dag",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [graph_id]",
                "  - contract_name: execution_packet",
                "    contract_kind: packet",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [execution_id]",
                "  - contract_name: planner_to_governance_runnable_contract",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [contract_id]",
                "  - contract_name: governance_decision_packet",
                "    contract_kind: packet",
                "    owner: governance-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [decision_id]",
                "  - contract_name: dag_node",
                "    contract_kind: dag",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [node_id]",
                "  - contract_name: dag_edge",
                "    contract_kind: dag",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [edge_id]",
                "  - contract_name: workflow_dag_to_implementation_dag_link_contract",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [link_id]",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "contracts" / "design-iteration-checks.yaml",
        "\n".join(
            [
                "version: 1",
                "validator_families:",
                "  - family: contract_consistency_checks",
                "    checks: []",
                "  - family: dag_consistency_checks",
                "    checks:",
                "      - check_id: workflow_to_implementation_link_missing",
                "        finding_type: missing_workflow_graph_link",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: workflow_and_implementation_graph_link_must_be_canonical",
                "      - check_id: linked_implementation_graph_missing",
                "        finding_type: missing_linked_implementation_graph",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: workflow_linked_implementation_graph_must_exist",
                "      - check_id: implementation_node_shape_invalid",
                "        finding_type: invalid_implementation_node_shape",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: implementation_nodes_must_be_buildable_and_machine_readable",
                "      - check_id: implementation_dependency_missing_node",
                "        finding_type: invalid_implementation_dependency_reference",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: implementation_dependencies_must_reference_existing_nodes",
                "      - check_id: implementation_edge_relation_invalid",
                "        finding_type: invalid_implementation_edge_relation",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: implementation_edges_use_allowed_relations",
                "      - check_id: implementation_dependency_cycle",
                "        finding_type: implementation_dependency_cycle",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: implementation_dependency_graph_must_be_acyclic",
                "  - family: boundary_leakage_checks",
                "    checks: []",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "design-iteration-tool-dag-v1.json",
        json.dumps(
            {
                "graph_id": "design-iteration-tool-dag-v1",
                "graph_kind": "workflow_dag",
                "implementation_graph_ref": "artifacts/planner/research/design-iteration-tool-implementation-graph-v1.json",
                "nodes": [
                    {
                        "node_id": "dit-001",
                        "node_type": "tool_invocation",
                        "input_packet_refs": [],
                        "output_packet_refs": ["normalized_design_context"],
                    }
                ],
                "edges": [],
            }
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "design-iteration-tool-implementation-graph-v1.json",
        json.dumps(
            {
                "graph_id": "design-iteration-tool-implementation-graph-v1",
                "graph_kind": "implementation_dag",
                "nodes": [
                    {
                        "node_id": "impl-001",
                        "node_type": "task",
                        "title": "",
                        "status": "ready",
                        "blocking_dependencies": ["missing-node"],
                        "changes": [],
                    }
                ],
                "edges": [
                    {
                        "edge_id": "impl-e-001",
                        "from_node_id": "impl-001",
                        "to_node_id": "missing-node",
                        "relation": "unsupported",
                    }
                ],
            }
        )
        + "\n",
    )

    code, report = run_design_iteration(root=tmp_path.as_posix())

    assert code == 1
    findings_packet = json.loads(Path(report["findings_packet_path"]).read_text(encoding="utf-8"))
    check_ids = {item["check_id"] for item in findings_packet["findings"]}
    assert "implementation_node_shape_invalid" in check_ids
    assert "implementation_dependency_missing_node" in check_ids
    assert "implementation_edge_relation_invalid" in check_ids


def test_design_iteration_inspects_discovered_planning_graphs(tmp_path: Path) -> None:
    _seed_docs(tmp_path)
    _seed_plan_quality_policy(tmp_path)
    _write(
        tmp_path / "spec" / "contracts" / "packet-schema-registry.yaml",
        "\n".join(
            [
                "version: 1",
                "contract_families:",
                "  - contract_name: packet_base",
                "    contract_kind: packet",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [packet_type]",
                "  - contract_name: message_envelope",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [command]",
                "  - contract_name: workflow_request_packet",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [workflow_id]",
                "  - contract_name: run_status_packet",
                "    contract_kind: run",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [status]",
                "  - contract_name: failure_packet",
                "    contract_kind: packet",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [summary]",
                "  - contract_name: research_question_packet",
                "    contract_kind: packet",
                "    owner: question-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [question_id]",
                "  - contract_name: evidence_packet",
                "    contract_kind: packet",
                "    owner: evidence-search-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [evidence_id]",
                "  - contract_name: research_problem_packet",
                "    contract_kind: packet",
                "    owner: research-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [problem_id]",
                "  - contract_name: question_to_research_problem_transform",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [transform_id]",
                "  - contract_name: research_recommendation_packet",
                "    contract_kind: packet",
                "    owner: research-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [recommendation_id]",
                "  - contract_name: selected_solution_scope",
                "    contract_kind: packet",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [solution_scope_id]",
                "  - contract_name: planning_request_packet",
                "    contract_kind: packet",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [planning_request_id]",
                "  - contract_name: implementation_graph_packet",
                "    contract_kind: dag",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [graph_id]",
                "  - contract_name: execution_packet",
                "    contract_kind: packet",
                "    owner: planner-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [execution_id]",
                "  - contract_name: planner_to_governance_runnable_contract",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [contract_id]",
                "  - contract_name: governance_decision_packet",
                "    contract_kind: packet",
                "    owner: governance-tool",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [decision_id]",
                "  - contract_name: dag_node",
                "    contract_kind: dag",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [node_id]",
                "  - contract_name: dag_edge",
                "    contract_kind: dag",
                "    owner: orchestration-runner",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [edge_id]",
                "  - contract_name: workflow_dag_to_implementation_dag_link_contract",
                "    contract_kind: transform",
                "    owner: shared-contract-layer",
                "    current_version: v1",
                "    compatibility_policy: additive_minor_breaking_major",
                "    required_fields: [link_id]",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec" / "contracts" / "design-iteration-checks.yaml",
        "\n".join(
            [
                "version: 1",
                "validator_families:",
                "  - family: contract_consistency_checks",
                "    checks: []",
                "  - family: dag_consistency_checks",
                "    checks:",
                "      - check_id: planning_graph_shape_invalid",
                "        finding_type: invalid_planning_graph_shape",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: planning_graphs_must_expose_machine_readable_nodes_and_edges",
                "      - check_id: planning_dependency_missing_node",
                "        finding_type: invalid_planning_dependency_reference",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: planning_graph_dependencies_must_reference_existing_nodes",
                "      - check_id: planning_edge_relation_invalid",
                "        finding_type: invalid_planning_edge_relation",
                "        severity: high",
                "        blocking: true",
                "        violated_invariant: planning_graph_edges_use_allowed_relations",
                "      - check_id: planning_dependency_cycle",
                "        finding_type: planning_dependency_cycle",
                "        severity: critical",
                "        blocking: true",
                "        violated_invariant: planning_dependency_graph_must_be_acyclic",
                "  - family: boundary_leakage_checks",
                "    checks: []",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "design-iteration-tool-dag-v1.json",
        json.dumps(
            {
                "graph_id": "design-iteration-tool-dag-v1",
                "graph_kind": "workflow_dag",
                "implementation_graph_ref": "artifacts/planner/research/design-iteration-tool-implementation-graph-v1.json",
                "nodes": [{"node_id": "dit-001", "node_type": "tool_invocation", "input_packet_refs": [], "output_packet_refs": ["normalized_design_context"]}],
                "edges": [],
            }
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "design-iteration-tool-implementation-graph-v1.json",
        json.dumps({"graph_id": "impl", "graph_kind": "implementation_dag", "nodes": [], "edges": []}) + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "graphs" / "legacy.json",
        json.dumps(
            {
                "graph_id": "legacy",
                "nodes": [{"id": "n1"}],
                "edges": [{"from": "n1", "to": "missing", "relation": "bad"}],
            }
        )
        + "\n",
    )

    code, report = run_design_iteration(root=tmp_path.as_posix())

    assert code == 1
    findings_packet = json.loads(Path(report["findings_packet_path"]).read_text(encoding="utf-8"))
    check_ids = {item["check_id"] for item in findings_packet["findings"]}
    assert "planning_dependency_missing_node" in check_ids
    assert "planning_edge_relation_invalid" in check_ids
