# Design Iteration Validator Spec V1

## Objective

Define the machine-checkable validator set for `design-iteration-tool v1`.

This document turns design iteration into a concrete validation layer over:

- shared contracts
- DAG semantics
- tool boundaries
- workflow handoffs

The goal is to ensure the iteration tool emits real findings grounded in explicit checks rather than only prose critique.

## Core Principle

Every design finding should be traceable to:

- a check
- an artifact
- a violated invariant
- a severity level

If a finding cannot be backed by a validator or an explicit heuristic rule, it should not automatically become a blocking design finding.

## Validator Families

V1 should define three main validator families:

1. `contract_consistency_checks`
2. `dag_consistency_checks`
3. `boundary_leakage_checks`

An optional fourth family may be added later:

4. `run_observation_checks`

## Validator Output Contract

Every validator should emit findings in a common shape.

### `validator_finding`

Required fields:

- `finding_id`
- `validator_family`
- `check_id`
- `severity`
- `blocking`
- `finding_type`
- `artifact_refs`
- `violated_invariant`
- `summary`

Recommended optional fields:

- `evidence_refs`
- `suggested_fix`
- `related_contract_refs`
- `related_node_refs`

## Severity Model

Use a small severity model.

- `critical`
  likely to create immediate drift or duplicate authority
- `high`
  likely to create inconsistent handoff semantics
- `medium`
  likely to create operational ambiguity or extraction risk
- `low`
  useful refinement but not current drift risk

## Blocking Rule

A finding is `blocking=true` only if it can cause:

- duplicate authority over one shared concept
- incompatible interpretation of the same packet
- execution flow breakage across DAG nodes
- governance inability to evaluate runnable state safely
- silent versioning drift

Everything else should default to non-blocking unless explicitly promoted.

## Contract Consistency Checks

These checks validate the shared contracts and cross-tool packet semantics.

### `contract_owner_defined`

Check:

- every shared contract has one canonical owner

Failure type:

- `missing_contract_owner`

Blocking:

- yes

### `contract_version_defined`

Check:

- every shared contract declares a version

Failure type:

- `missing_contract_version`

Blocking:

- yes

### `contract_required_fields_defined`

Check:

- every shared contract lists required fields explicitly

Failure type:

- `missing_required_fields_definition`

Blocking:

- yes

### `optional_field_required_downstream`

Check:

- a field marked optional upstream is required by a downstream consumer

Failure type:

- `optional_field_causes_drift`

Blocking:

- yes

### `duplicate_contract_authority`

Check:

- more than one contract claims authority over the same shared concept

Failure type:

- `duplicate_authority`

Blocking:

- yes

### `missing_transform_contract`

Check:

- two packet families are linked operationally but no canonical transform contract is defined

Failure type:

- `missing_transform_contract`

Blocking:

- yes

### `versioning_policy_missing`

Check:

- a contract family lacks a declared compatibility policy

Failure type:

- `versioning_policy_missing`

Blocking:

- yes

### `registry_entry_missing`

Check:

- a shared packet or DAG/run contract exists in use but is absent from the canonical registry

Failure type:

- `missing_registry_entry`

Blocking:

- yes

## DAG Consistency Checks

These checks validate orchestration and implementation graph semantics.

### `dag_node_type_valid`

Check:

- every node uses an allowed node type

Failure type:

- `invalid_node_type`

Blocking:

- yes

### `dag_edge_relation_valid`

Check:

- every edge uses an allowed edge relation

Failure type:

- `invalid_edge_relation`

Blocking:

- yes

### `dag_dependency_cycle`

Check:

- no cycle exists in dependency edges

Failure type:

- `dependency_cycle`

Blocking:

- yes

### `dag_unsatisfied_input_contract`

Check:

- a node requires an input packet that no predecessor can produce

Failure type:

- `unsatisfied_input_contract`

Blocking:

- yes

### `workflow_to_implementation_link_missing`

Check:

- planner output is expected to become executable work but no canonical workflow-to-implementation link contract is declared

Failure type:

- `missing_workflow_graph_link`

Blocking:

- yes

### `linked_implementation_graph_missing`

Check:

- a workflow DAG references an implementation graph that does not exist

Failure type:

- `missing_linked_implementation_graph`

Blocking:

- yes

### `implementation_node_shape_invalid`

Check:

- an implementation graph node is missing the machine-readable fields needed for bounded execution

Failure type:

- `invalid_implementation_node_shape`

Blocking:

- yes

### `implementation_dependency_missing_node`

Check:

- an implementation dependency or edge references a node that does not exist

Failure type:

- `invalid_implementation_dependency_reference`

Blocking:

- yes

### `implementation_edge_relation_invalid`

Check:

- an implementation graph edge uses an unsupported relation

Failure type:

- `invalid_implementation_edge_relation`

Blocking:

- yes

### `implementation_dependency_cycle`

Check:

- the implementation graph contains a dependency cycle

Failure type:

- `implementation_dependency_cycle`

Blocking:

- yes

### `planning_graph_shape_invalid`

Check:

- a discovered planning graph lacks the machine-readable node and edge shape needed for inspection

Failure type:

- `invalid_planning_graph_shape`

Blocking:

- yes

### `planning_dependency_missing_node`

Check:

- a discovered planning graph references dependency nodes that do not exist

Failure type:

- `invalid_planning_dependency_reference`

Blocking:

- yes

### `planning_edge_relation_invalid`

Check:

- a discovered planning graph uses an unsupported planning edge relation

Failure type:

- `invalid_planning_edge_relation`

Blocking:

- yes

### `planning_dependency_cycle`

Check:

- a discovered planning graph contains a dependency cycle

Failure type:

- `planning_dependency_cycle`

Blocking:

- yes

### `governance_gate_without_runnable_contract`

Check:

- governance is expected to evaluate runnable state but the planner-origin execution contract lacks required runnable fields

Failure type:

- `missing_runnable_contract_fields`

Blocking:

- yes

### `graph_level_misuse`

Check:

- a workflow DAG is being used to carry long-term memory or a memory record structure is being treated as an execution DAG

Failure type:

- `graph_level_misuse`

Blocking:

- high, but not always blocking by default

## Boundary Leakage Checks

These checks validate tool boundary discipline.

### `research_absorbs_evidence_search`

Check:

- research contract or flow directly owns external evidence retrieval semantics that belong to evidence-search

Failure type:

- `boundary_leakage_research_evidence`

Blocking:

- high, non-blocking until it affects contracts or packets

### `research_absorbs_memory_authority`

Check:

- research becomes authoritative for reusable solved-case storage rather than calling memory contracts

Failure type:

- `boundary_leakage_research_memory`

Blocking:

- medium, escalates if packet authority drifts

### `governance_reconstructs_plan_structure`

Check:

- governance behavior assumes missing planner semantics instead of blocking

Failure type:

- `boundary_leakage_governance_planner`

Blocking:

- yes

### `runner_owns_domain_logic`

Check:

- orchestration runner makes tool-specific research, planning, or governance decisions

Failure type:

- `boundary_leakage_runner_domain_logic`

Blocking:

- yes

### `design_iteration_owns_execution_orchestration`

Check:

- design-iteration workflow is being used as the general execution orchestrator

Failure type:

- `boundary_leakage_design_runner`

Blocking:

- yes

### `question_tool_replaces_design_iteration`

Check:

- question generation is being used to critique design architecture directly instead of consuming bounded iteration outputs

Failure type:

- `boundary_leakage_question_design`

Blocking:

- medium

## Run Observation Checks

These are later-stage validators for when real orchestration runs exist.

### `observed_packet_shape_drift`

Check:

- emitted runtime packets deviate from the declared contract family

Failure type:

- `runtime_packet_shape_drift`

Blocking:

- yes

### `observed_retry_without_idempotency`

Check:

- retries occur without stable packet refs or node identity

Failure type:

- `retry_without_idempotency`

Blocking:

- yes

### `observed_hidden_failure`

Check:

- a run outcome appears successful while failed steps were not surfaced in packets or logs

Failure type:

- `hidden_failure`

Blocking:

- yes

## Real-Finding Promotion Rules

Only promote a validator output to a top-level design finding when:

- the finding maps to a shared concept
- the violated invariant is explicit
- the drift risk is plausible and concrete
- the finding can affect downstream interpretation or execution

Do not promote:

- naming preferences
- prose style concerns
- speculative worries without artifact linkage

## Minimum V1 Validator Set

The first implementation should include these checks:

1. `contract_owner_defined`
2. `contract_version_defined`
3. `optional_field_required_downstream`
4. `duplicate_contract_authority`
5. `missing_transform_contract`
6. `registry_entry_missing`
7. `dag_dependency_cycle`
8. `dag_unsatisfied_input_contract`
9. `governance_gate_without_runnable_contract`
10. `governance_reconstructs_plan_structure`
11. `runner_owns_domain_logic`
12. `design_iteration_owns_execution_orchestration`

These are enough to detect the most dangerous early drift patterns.

## Integration With Design Iteration DAG

Map validator families to the iteration DAG nodes:

- `run_contract_consistency_checks`
  - executes `contract_consistency_checks`
- `run_dag_consistency_checks`
  - executes `dag_consistency_checks`
- `compare_tool_boundaries_against_contracts`
  - executes `boundary_leakage_checks`
- later `run_observation_checks`
  - executes `run_observation_checks`

## Exit Criteria

The validator spec is ready when:

- every major design finding type maps to a concrete validator
- blocking vs non-blocking findings are explicit
- validator outputs can be emitted as machine-readable packets
- design iteration can distinguish real drift from cosmetic critique
