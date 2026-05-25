# Core Contract Spec V1

## Objective

Define the canonical shared contracts for the tool ecosystem so that:

- tools pass information through stable packets
- orchestration runs use one message and DAG model
- planner and governance consume the same execution semantics
- design iteration can critique real contracts instead of prose alone

This document is the interoperability layer for V1.

## Contract Philosophy

All cross-tool communication must use explicit, versioned, machine-readable packets.

The contract layer exists to prevent:

- duplicate authority
- hidden assumptions
- tool-specific reinterpretation of shared concepts
- drift between orchestration, planner, research, and governance

## Shared Contract Rules

Every shared contract should define:

- canonical owner
- packet type name
- version
- required fields
- optional fields
- invariants
- upstream producers
- downstream consumers

## Base Packet Contract

### `packet_base`

Purpose:

- common metadata envelope for all packets

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`

Recommended optional fields:

- `run_id`
- `artifact_refs`
- `source_packet_refs`
- `trace_refs`

Invariants:

- `packet_type` must be stable and explicit
- `packet_version` must be semantically versioned at the packet-family level
- `packet_id` must be unique within its packet family
- packet bodies must be machine-readable

## Message Contract

### `message_envelope`

Purpose:

- canonical runner-level message wrapper for tool invocations and run events

Required fields:

- `message_id`
- `message_type`
- `run_id`
- `node_id`
- `source`
- `target`
- `payload_ref`
- `created_at`
- `correlation_id`

Recommended optional fields:

- `causation_id`
- `retry_count`
- `priority`
- `deadline`

Invariants:

- messages should reference packets or artifacts, not large inline blobs by default
- every orchestration event should be traceable to a `run_id` and `node_id`

## Workflow Contracts

### `workflow_request_packet`

Purpose:

- canonical request to start an orchestration run

Required fields:

- `workflow_request_id`
- `workflow_type`
- `initial_packet_ref`
- `requested_outputs`
- `policy_ref`

Recommended optional fields:

- `requested_by`
- `deadline`
- `priority`

Invariants:

- must identify one initial packet as the run entry point
- must declare requested outputs explicitly

## Design Review Automation Contracts

### `design_review_request_packet`

Canonical owner:

- `design-iteration-tool`

Purpose:

- canonical request to start an evidence-aware automated design review

Required fields:

- all `packet_base` fields
- `review_id`
- `system_scope`
- `artifact_refs`
- `requested_review_modes`
- `requested_outputs`

Recommended optional fields:

- `focus_areas`
- `evidence_expectations`
- `known_blockers`
- `time_budget_seconds`

Invariants:

- review requests must stay bounded to explicit review modes and artifact targets

### `design_review_program_packet`

Canonical owner:

- `design-iteration-tool`

Purpose:

- bounded review program emitted by design iteration for runner execution

Required fields:

- all `packet_base` fields
- `review_id`
- `review_request_ref`
- `review_nodes`
- `stop_conditions`

Recommended optional fields:

- `evidence_policy_ref`
- `tool_call_budget`
- `priority_order`

Invariants:

- review programs must describe bounded, replayable review nodes rather than open-ended agent loops

### `tool_call_request_packet`

Canonical owner:

- `orchestration-runner`

Purpose:

- canonical bounded tool invocation request used by automated review and later workflows

Required fields:

- all `packet_base` fields
- `call_id`
- `run_id`
- `requester`
- `target_tool`
- `operation_name`
- `input_packet_refs`
- `policy_ref`

Recommended optional fields:

- `reason`
- `expected_output_packet_types`
- `deadline`
- `retry_policy_override`

Invariants:

- one request must target one bounded operation on one tool

### `tool_call_result_packet`

Canonical owner:

- `orchestration-runner`

Purpose:

- canonical result envelope for a bounded tool invocation

Required fields:

- all `packet_base` fields
- `call_id`
- `run_id`
- `target_tool`
- `operation_name`
- `outcome`
- `output_packet_refs`
- `event_refs`

Recommended optional fields:

- `failure_ref`
- `timing_summary`
- `warnings`

Invariants:

- result packets must preserve replayable refs to emitted packets and run events

### `run_status_packet`

Purpose:

- canonical run state projection

Required fields:

- `run_id`
- `workflow_type`
- `status`
- `current_step`
- `completed_steps`
- `failed_steps`
- `artifact_refs`
- `last_event_ref`

Invariants:

- status must be one of: `draft`, `queued`, `running`, `blocked`, `failed`, `completed`, `cancelled`

### `failure_packet`

Purpose:

- canonical failure representation for tool or orchestration failures

Required fields:

- `failure_id`
- `run_id`
- `node_id`
- `failure_class`
- `failure_reason`
- `retryable`
- `artifact_refs`
- `recorded_at`

Invariants:

- each failed node should emit exactly one primary failure packet per terminal failure event

## Discovery And Question Contracts

### `research_question_packet`

Canonical owner:

- `question-tool`

Purpose:

- downstream-ready bounded research question

Required fields:

- all `packet_base` fields
- `question_id`
- `project_id`
- `question_text`
- `question_type`
- `goal`
- `constraints`
- `evaluation_targets`
- `artifact_targets`
- `decision_target`
- `decision_consequence`
- `blocked_work_if_unanswered`

Recommended optional fields:

- `keywords`
- `likely_source_types`
- `why_now`
- `expected_downstream_change`

Invariants:

- every question must be tied to a concrete decision target
- every question must declare what downstream action could change if answered
- every question must be bounded enough for evidence search and research evaluation

## Evidence Contracts

### `evidence_packet`

Canonical owner:

- `evidence-search-tool`

Purpose:

- normalized external evidence package for one problem or question

Required fields:

- all `packet_base` fields
- `problem_id`
- `source_refs`
- `claim_refs`
- `method_refs`
- `benchmark_refs`
- `evidence_summary`

Recommended optional fields:

- `query_terms`
- `search_scope`
- `source_quality_summary`

Invariants:

- all claims must point to attributable source refs
- evidence packets must not be treated as long-term memory by default

## Research Contracts

### `research_problem_packet`

Canonical owner:

- `research-tool`

Purpose:

- canonical research-tool input

Required fields:

- all `packet_base` fields
- `problem_id`
- `title`
- `goal`
- `problem_statement`
- `constraints`
- `repo_context`
- `artifact_targets`
- `evaluation_criteria`
- `search_budget`
- `output_requirements`

Recommended optional fields:

- `language`
- `runtime_environment`
- `allowed_tools`
- `disallowed_tools`
- `baseline_artifact_refs`
- `reference_implementations`
- `evidence_packet_ref`
- `memory_context_refs`

Invariants:

- must be bounded enough for explicit candidate evaluation
- must identify evaluation criteria up front

### `research_hypothesis_packet`

Canonical owner:

- `research-tool`

Purpose:

- explicit research branch derived from one `research_problem_packet`

Required fields:

- all `packet_base` fields
- `hypothesis_id`
- `problem_id`
- `hypothesis_family`
- `hypothesis_statement`
- `approach_outline`
- `evaluation_focus`
- `evidence_refs`
- `branch_rank`
- `prune_conditions`

Recommended optional fields:

- `source_question_refs`
- `source_problem_ref`
- `risk_notes`
- `expected_advantages`
- `expected_tradeoffs`

Invariants:

- each hypothesis must remain traceable to one source research problem
- each hypothesis must be materially distinct from other emitted branches
- branch count must remain bounded in v1

### `candidate_search_tree_packet`

Canonical owner:

- `research-tool`

Purpose:

- machine-readable representation of bounded candidate generation tree

Required fields:

- all `packet_base` fields
- `problem_id`
- `root_node_id`
- `tree_nodes`
- `tree_edges`
- `search_policy`
- `candidate_packet_refs`

Invariants:

- the tree must be acyclic
- candidate nodes must trace to source hypotheses
- search policy limits must be explicit

### `research_candidate_packet`

Canonical owner:

- `research-tool`

Purpose:

- canonical candidate emitted by bounded research candidate search
- carries enough implementation intent for recommendation and planner handoff

Required fields:

- all `packet_base` fields
- `candidate_id`
- `problem_id`
- `source_hypothesis_id`
- `candidate_family`
- `approach_summary`
- `implementation_intent`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `expected_changes`
- `non_goals`
- `handoff_requirements`
- `planner_entry_notes`
- `assumptions`
- `proposed_changes`
- `artifact_refs`
- `source_type`
- `evidence_refs`
- `feasibility_priors`

`implementation_intent` required fields:

- `summary`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `handoff_requirements`

Invariants:

- candidates must be implementation-specific enough for downstream planner review
- candidates must not be build-authorizing contracts
- generic candidate-family labels are not sufficient implementation intent

### `candidate_expansion_decision_packet`

Canonical owner:

- `research-tool`

Purpose:

- record one candidate-search expansion, prune, or defer decision

Required fields:

- all `packet_base` fields
- `decision_id`
- `problem_id`
- `source_node_id`
- `decision`
- `reason`
- `evidence_refs`
- `resulting_node_refs`

Invariants:

- every generated candidate should be reachable from at least one expansion decision

### `candidate_evaluation_summary_packet`

Canonical owner:

- `research-tool`

Purpose:

- summarize evaluation results for one candidate search run

Required fields:

- all `packet_base` fields
- `problem_id`
- `candidate_search_tree_ref`
- `evaluation_packet_refs`
- `promoted_candidate_ids`
- `blocked_candidate_ids`
- `evaluation_policy`

Invariants:

- every candidate emitted by the search tree should have one evaluation packet before recommendation
 

### `question_to_research_problem_transform`

Canonical owner:

- shared contract layer

Purpose:

- canonical transform from question and evidence into research input

Required inputs:

- `research_question_packet`
- optional `evidence_packet`
- optional memory context refs

Required output:

- `research_problem_packet`

Invariants:

- `problem_id` must remain traceable to the source question
- evaluation targets from the question must map into evaluation criteria in the research problem
- evidence refs must be preserved as source refs, not silently absorbed

### `research_recommendation_packet`

Canonical owner:

- `research-tool`

Purpose:

- canonical downstream research result

Required fields:

- all `packet_base` fields
- `problem_id`
- `candidate_search_tree_ref`
- `evaluation_summary_ref`
- `evaluation_refs`
- `ranked_candidates`
- `recommended_candidate_id`
- `recommendation_reason`
- `winner_evidence_refs`
- `rejected_candidate_summaries`
- `open_questions`
- `artifact_refs`
- `evidence_refs`

Invariants:

- recommendation must be evidence-backed
- recommendation must be evaluation-backed
- ranked candidates must include score breakdowns
- this packet does not itself authorize build execution

### `ranked_candidate_packet`

Canonical owner:

- `research-tool`

Purpose:

- canonical ranked representation of one evaluated research candidate

Required fields:

- all `packet_base` fields
- `candidate_id`
- `problem_id`
- `rank`
- `total_score`
- `score_breakdown`
- `strengths`
- `weaknesses`
- `promotion_status`
- `evaluation_ref`
- `evidence_refs`
- `source_hypothesis_id`
- `implementation_intent`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `expected_changes`
- `non_goals`
- `handoff_requirements`
- `planner_entry_notes`

Invariants:

- every ranked candidate must reference a `research_evaluation_packet`
- ranked candidates must not be emitted for unevaluated candidates
- rank must be derived from the configured evaluation-backed ranking policy
- implementation intent must be preserved from the source research candidate

### `selected_solution_scope`

Canonical owner:

- shared handoff between research and planner

Purpose:

- canonical selected-solution contract used by planner and governance

Required fields:

- all `packet_base` fields
- `selection_id`
- `problem_id`
- `selected_candidate_id`
- `selection_reason`
- `selection_policy`
- `selected_solution_summary`
- `in_scope`
- `out_of_scope`
- `scope_in`
- `scope_out`
- `assumptions`
- `risks`
- `acceptance_checks`
- `acceptance_targets`
- `implementation_intent`
- `expected_changes`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `handoff_requirements`
- `artifact_refs`
- `evidence_refs`

Recommended optional fields:

- `open_questions`
- `follow_on_research_needed`
- `estimated_change_surface`

Invariants:

- this is the only supported contract for “the chosen answer” downstream
- planner must consume this packet rather than raw recommendation packets directly for authoritative solution selection
- governance may validate it but must not redefine it
- selection policy must preserve the source recommendation ref and required gate inputs
- selected scopes may carry candidate intent forward, but still do not authorize execution

### `problem_node`

Canonical owner:

- `planner-tool`

Purpose:

- canonical manageable project problem node

Required fields:

- all `packet_base` fields
- `node_id`
- `node_version`
- `project_id`
- `title`
- `node_type`
- `goal`
- `problem_statement`
- `inputs`
- `expected_outputs`
- `constraints`
- `dependencies`
- `evidence_refs`
- `option_refs`
- `selected_option_ref`
- `readiness_state`
- `missing_fields`
- `evaluation_criteria`
- `feedback_refs`

Invariants:

- problem nodes are not directly executable
- readiness state controls allowed next tools
- missing fields must explain why a node is not ready
- evidence and feedback refs preserve provenance

### `node_option`

Canonical owner:

- `planner-tool`

Purpose:

- canonical candidate way to solve or advance one problem node

Required fields:

- all `packet_base` fields
- `option_id`
- `source_node_ref`
- `option_family`
- `approach_summary`
- `implementation_intent`
- `expected_changes`
- `non_goals`
- `assumptions`
- `risks`
- `evidence_refs`
- `evaluation_refs`

Invariants:

- node options must have implementation intent
- expected changes must be concrete enough for planning
- options do not authorize execution without an execution unit

### `execution_unit`

Canonical owner:

- `planner-tool`

Purpose:

- canonical buildable and evaluable work contract derived from a selected node option

Required fields:

- all `packet_base` fields
- `execution_unit_id`
- `source_problem_node_ref`
- `selected_option_ref`
- `implementation_intent`
- `owned_changes`
- `required_inputs`
- `expected_outputs`
- `acceptance_checks`
- `validation_commands`
- `rollback_plan`
- `non_goals`
- `dependency_refs`
- `evidence_refs`
- `evaluation_method`
- `completion_evidence_requirements`

Invariants:

- execution units are the first implementation-ready work contract
- execution units require owned changes
- execution units require validation commands
- execution units require rollback plans
- selected solution scopes are not execution units

### `implementation_attempt`

Canonical owner:

- `implementation-orchestrator`

Purpose:

- one candidate implementation generated inside an execution-unit boundary

Required fields:

- all `packet_base` fields
- `attempt_id`
- `source_execution_unit_ref`
- `attempt_family`
- `implementation_summary`
- `changed_artifact_refs`
- `patch_ref`
- `validation_command_refs`
- `assumptions`
- `risks`
- `status`
- `created_by`

Invariants:

- attempts must reference one execution unit
- attempts must remain traceable even when rejected
- attempts do not complete execution units by themselves

### `attempt_evaluation`

Canonical owner:

- `governance-tool`

Purpose:

- evaluator output for one implementation attempt

Required fields:

- all `packet_base` fields
- `evaluation_id`
- `source_attempt_ref`
- `source_execution_unit_ref`
- `evaluation_method`
- `validation_results`
- `test_results`
- `review_findings`
- `score_breakdown`
- `promotion_status`
- `blockers`
- `evidence_refs`

Invariants:

- selected attempts require nonblocking evaluations
- evaluation must preserve validation evidence
- evaluation is separate from implementation generation

### `solution_artifact`

Canonical owner:

- `implementation-orchestrator`

Purpose:

- selected implementation result attached back to the execution unit

Required fields:

- all `packet_base` fields
- `solution_artifact_id`
- `source_execution_unit_ref`
- `selected_attempt_ref`
- `evaluation_ref`
- `artifact_refs`
- `patch_ref`
- `completion_evidence_refs`
- `validation_summary`
- `known_limitations`
- `follow_up_problem_node_refs`

Invariants:

- solution artifacts select one evaluated attempt
- solution artifacts complete or advance execution units
- rejected attempts must remain available through attempt and evaluation refs

## Planning Contracts

### `planning_request_packet`

Canonical owner:

- `planner-tool`

Purpose:

- canonical planner input

Required fields:

- all `packet_base` fields
- `request_id`
- `project_id`
- `selected_solution_refs`
- `project_goal`
- `scope_constraints`
- `acceptance_targets`
- `artifact_targets`

Recommended optional fields:

- `deadline`
- `team_constraints`
- `preferred_execution_order`
- `non_goals`

Invariants:

- `selected_solution_refs` should point to one or more `selected_solution_scope` packets

### `implementation_graph_packet`

Canonical owner:

- `planner-tool`

Purpose:

- canonical machine-readable implementation DAG

Required fields:

- all `packet_base` fields
- `graph_id`
- `project_id`
- `nodes`
- `edges`
- `workflow_groups`
- `ready_nodes`
- `blocked_nodes`

Invariants:

- graph must be a DAG for execution dependencies
- node and edge refs must be internally valid
- graph must be sufficient for structural plan comparison and later execution-slice materialization

### `execution_materialization_policy`

Canonical owner:

- `planner-tool`

Purpose:

- define deterministic rules for converting a chosen structural plan into execution-ready form

Required fields:

- `policy_id`
- `purpose`
- `grouping_rules`
- `warning_rules`
- `hard_fail_rules`
- `outputs`

Invariant:

- this policy may govern materialization but must not choose the winning plan or approve execution

### `execution_ready_plan_packet`

Canonical owner:

- `planner-tool`

Purpose:

- canonical planner-produced execution-ready handoff after structural plan selection and slice materialization

Required fields:

- all `packet_base` fields
- `plan_id`
- `selected_solution_scope_ref`
- `source_structural_plan_ref`
- `plan_readiness`
- `execution_slices`
- `materialization_policy_ref`
- `materialization_warnings`

Recommended optional fields:

- `evidence_refs`
- `trace_refs`

Invariants:

- `plan_readiness` must be `execution_ready`
- execution-ready plans must be derived from one chosen structural plan
- governance should consume execution-ready plans and execution packets, not raw structural plans

### `execution_packet`

Canonical owner:

- `planner-tool`

Purpose:

- canonical planner-produced build slice contract

Required fields:

- all `packet_base` fields
- `execution_id`
- `work_item_id`
- `graph_id`
- `task_summary`
- `required_inputs`
- `expected_outputs`
- `validation_targets`
- `blocking_dependencies`
- `declared_ready_inputs`
- `conflict_domains`
- `completion_evidence_requirements`
- `runnable_preconditions`

Recommended optional fields:

- `required_approvals`
- `owner`
- `priority`

Invariants:

- execution packets must be derived from an `execution_ready_plan_packet`
- planner-to-governance runnable contract depends on these fields being present
- governance must not infer these fields from prose if missing

## Governance Contracts

### `governance_decision_packet`

Canonical owner:

- `governance-tool`

Purpose:

- canonical governance result for readiness, transition, or completion

Required fields:

- all `packet_base` fields
- `target_ref`
- `decision`
- `blockers`
- `evidence_refs`
- `required_followups`

Recommended optional fields:

- `decision_reason`
- `policy_refs`
- `transition_refs`

Invariants:

- governance decisions must be explicit and machine-readable
- governance may validate or block; it must not invent missing planner structure

### `planner_to_governance_runnable_contract`

Canonical owner:

- shared contract layer

Purpose:

- define the minimal authoritative planner fields governance requires to assess runnable state

Required source:

- `execution_packet`

Required semantics:

- explicit dependencies
- explicit ready inputs
- explicit conflict domains
- explicit completion evidence requirements
- explicit validation targets
- explicit runnable preconditions

Invariant:

- if any required field is missing, governance should block with a contract error instead of reconstructing meaning

## DAG Contracts

### `dag_node`

Purpose:

- canonical workflow DAG node

Required fields:

- `node_id`
- `node_type`
- `title`
- `input_packet_refs`
- `output_packet_refs`
- `blocking_dependencies`
- `status`
- `retry_policy`
- `timeout_policy`

Recommended optional fields:

- `tool_name`
- `operation_name`
- `artifact_refs`
- `owner`
- `priority`
- `failure_policy`

### `dag_edge`

Purpose:

- canonical workflow DAG edge

Required fields:

- `edge_id`
- `from_node_id`
- `to_node_id`
- `relation`

Supported V1 relations:

- `depends_on`
- `produces`
- `consumes`
- `blocks`
- `gated_by`

Invariants:

- edge relations must be explicit and finite
- dependency cycles are illegal

### `workflow_dag_to_implementation_dag_link_contract`

Canonical owner:

- shared contract layer

Purpose:

- define how planner output becomes downstream orchestratable execution structure

Required behavior:

- workflow DAG may invoke planner-tool and consume an `implementation_graph_packet`
- implementation DAG remains planner-owned
- orchestration runner may schedule over emitted `execution_packet` nodes without changing planner semantics

Invariant:

- workflow DAG and implementation DAG may be linked, but they are not the same graph and must not silently overwrite each other

## Versioning Rules

### `packet_schema_registry`

Canonical owner:

- shared contract layer

Purpose:

- define authoritative ownership and compatibility rules for packet families

Registry shape:

- one canonical registry
- logical partitioning by `contract_kind`
- per-family ownership and compatibility rules

Supported initial `contract_kind` values:

- `packet`
- `dag`
- `run`
- `policy`
- `transform`

Each packet family should declare:

- owner
- current version
- backward compatibility policy
- deprecation policy

### Versioning Law

- additive field changes may increment a minor version
- breaking required-field or semantic changes require a major version
- no tool may silently reinterpret another tool’s packet family without updating the shared contract

Invariant:

- packet versioning must be centrally declared, not tool-local folklore
- the system should not maintain separate competing registries for packet and DAG/run contracts

## First Lock Set

The first contracts that must be treated as locked before broader building are:

1. `packet_base`
2. `message_envelope`
3. `research_question_packet`
4. `evidence_packet`
5. `research_problem_packet`
6. `question_to_research_problem_transform`
7. `research_recommendation_packet`
8. `selected_solution_scope`
9. `planning_request_packet`
10. `execution_packet`
11. `planner_to_governance_runnable_contract`
12. `governance_decision_packet`
13. `dag_node`
14. `dag_edge`
15. `failure_packet`
16. `run_status_packet`

## Separation Guidance

These contracts should be defined before repo extraction.

The correct order is:

1. lock contracts
2. wrap current capabilities
3. run real workflows
4. observe drift and mixed responsibility
5. extract tools or repos where justified

This keeps separation grounded in operational truth.
