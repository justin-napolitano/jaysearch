# Planner Tool V1

## Objective

Define a standalone planner API that takes selected solutions and project scope, decomposes them into buildable work, and emits dependency-aware graphs that can be executed as real implementation programs.

This tool is not the research runtime and not the governance engine.

Its purpose is to:

- take selected solution packets
- identify implementation problems worth solving
- decompose work into bounded nodes
- model dependencies and workflow order
- emit machine-readable DAGs and execution packets

## Role In The System

The intended split is:

- `evidence-search-tool`
  external evidence retrieval
- `memory-tool`
  reusable solved-case retrieval
- `research-tool`
  candidate generation, evaluation, and recommendation
- `planner-tool`
  implementation decomposition and DAG generation
- `governance-tool`
  execution gating, approval, and merge control

The planner turns chosen directions into buildable work. It does not decide which solution wins and it does not approve execution.

Canonical project-level model:

- `docs/node-based-project-plan-v1.md`

Planner must route major work through problem nodes, node options, and execution units.

## Hard Boundary With Governance

The planner owns:

- decomposition of selected solutions into work items
- dependency modeling
- conflict-domain declaration
- completion criteria declaration
- execution packet structure

The governance tool owns:

- legality of execution
- approval requirements
- validation requirements
- state transitions
- completion or merge readiness

Governance must not reconstruct plan structure from prose or invent missing planner fields. Planner must emit the machine-readable structure governance needs.

## Core Principle

Large projects should be modeled as many bounded implementation problems with explicit dependencies, not one giant plan blob.

The planner must answer:

- what needs to be built
- in what order
- what can run in parallel
- what is blocked on what
- what artifacts prove completion

The planner ranks problem nodes, but it executes only execution units.

## V1 Use Case

V1 should support:

- one selected solution or a small selected solution set
- one project scope packet
- decomposition into a DAG of implementation work
- generation of worker-ready execution packets

The initial planner should optimize for clarity and buildability, not perfect forecasting.

## Non-Goals

V1 should not become:

- a full PM suite
- an autonomous executor
- a governance engine
- a massive project portfolio system

It should stay focused on turning selected solutions into executable work graphs.

## End-To-End Flow

1. accept `planning_request_packet`
2. normalize selected solutions and scope constraints
3. identify or import `problem_node` records
4. rank problem nodes and choose a frontier
5. generate or attach `node_option` records
6. select options and materialize `execution_unit` records
7. detect dependencies and conflicts
8. emit `implementation_graph_packet`
9. materialize the chosen structural plan into execution-ready form
10. emit worker-ready execution packets

## API Surface

### `define_scope`

Purpose:

- normalize the selected solution and implementation scope

Input:

- `planning_request_packet`

Output:

- `normalized_scope_packet`
- `scope_validation_results`

### `derive_work_items`

Purpose:

- identify bounded implementation problems implied by the selected solution

Input:

- `normalized_scope_packet`

Output:

- `work_item_packet[]`

This API should evolve toward `problem_node[]`.

### `build_dependency_graph`

Purpose:

- create dependency-aware graph structure across work items

Input:

- `work_item_packet[]`
- `dependency_policy`

Output:

- `implementation_graph_packet`

### `materialize_execution_slices`

Purpose:

- convert a chosen structural plan into an execution-ready plan with runnable slices

Input:

- chosen structural `implementation_graph_packet`
- `execution_materialization_policy`

Output:

- `execution_ready_plan_packet`
- `execution_packet[]`

This API should consume `execution_unit[]` once the execution-unit contract is active.

### `emit_execution_packets`

Purpose:

- project execution-ready slices into worker-usable execution packets

Input:

- `execution_ready_plan_packet`
- `execution_policy`

Output:

- `execution_packet[]`

## Primary Packets

### `planning_request_packet`

Purpose:

- canonical planner input

Minimum fields:

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

Required upstream contract rule:

- `selected_solution_refs` must reference one or more `selected_solution_scope` packets
- raw `research_recommendation_packet` output is not a sufficient authoritative planner input by itself

### `work_item_packet`

Purpose:

- one bounded implementation problem worth solving

Minimum fields:

- `work_item_id`
- `title`
- `problem_statement`
- `goal`
- `inputs`
- `outputs`
- `completion_criteria`
- `dependency_refs`
- `conflict_domains`

### `implementation_graph_packet`

Purpose:

- machine-readable project DAG

Minimum fields:

- `graph_id`
- `project_id`
- `nodes`
- `edges`
- `workflow_groups`
- `ready_nodes`
- `blocked_nodes`

### `execution_ready_plan_packet`

Purpose:

- canonical planner-produced execution-ready handoff before governance

Minimum fields:

- `plan_id`
- `selected_solution_scope_ref`
- `source_structural_plan_ref`
- `plan_readiness`
- `execution_slices`
- `materialization_policy_ref`
- `materialization_warnings`

### `execution_packet`

Purpose:

- a planner-produced packet for one execution-ready build slice

Minimum fields:

- `execution_id`
- `work_item_id`
- `graph_id`
- `task_summary`
- `required_inputs`
- `expected_outputs`
- `validation_targets`
- `blocking_dependencies`

Required upstream contract rule:

- `execution_packet` must be derived from an `execution_ready_plan_packet`, not directly from a raw structural `implementation_graph_packet`

Recommended governance-facing fields:

- `declared_ready_inputs`
- `conflict_domains`
- `required_approvals`
- `completion_evidence_requirements`
- `runnable_preconditions`

## Required Upstream Selection Contract

Before planning begins, research output must be converted into a canonical selected-solution contract.

The planner should therefore consume:

- `selected_solution_scope`

through:

- `planning_request_packet`

The planner must not become the place where recommendation ranking is reinterpreted into final selection authority.

## Node Model

Each node should represent one bounded buildable problem.

V1 node properties:

- stable id
- clear goal
- explicit dependencies
- explicit conflict domains
- artifact outputs
- completion checks
- estimated parallelizability

Good node examples:

- define API schema for memory tool packets
- implement ranking engine normalization helpers
- add evidence packet assembler
- wire planner handoff packet generation

Bad node examples:

- build the whole planner
- make research better
- fix architecture generally

## Edge Model

V1 edges should stay simple.

Supported edge relations:

- `depends_on`
- `blocks`
- `conflicts_with`
- `informs`

The critical relation is `depends_on`. The graph should remain a DAG for execution ordering.

## Workflow Groups

The planner should cluster nodes into coarse workflows.

Recommended workflow groups:

- `contracts`
- `runtime`
- `evaluation`
- `integration`
- `hardening`

These are grouping aids, not authority boundaries.

## Dependency Rules

The planner should infer dependencies from:

- artifact prerequisites
- API producer/consumer relationships
- validation order
- migration or rollout sequencing
- shared conflict domains

The planner should avoid inventing unnecessary dependencies. A DAG that is too dense destroys parallelism.

## Parallelism Rules

A node is parallelizable only when:

- it has no unmet dependencies
- it does not collide on conflict domains
- it does not require the same exclusive artifact ownership

The planner should explicitly mark:

- `ready_now`
- `blocked`
- `parallel_safe`
- `review_gated`

## Planner Outputs

The planner should emit:

- full implementation DAG
- topological order
- ready queue
- blocked queue
- execution packets
- unresolved ambiguity list

This makes the graph operational, not merely descriptive.

## Runnable Contract

The planner must emit enough structure for governance to evaluate runnable state without re-planning the work.

At minimum, a planner-produced runnable contract should identify:

- unmet dependency refs
- required inputs
- exclusive conflict domains
- expected outputs
- validation targets
- completion evidence requirements

If governance has to infer these from free text, the planner output is incomplete.

## Integration With Research Tool

The planner consumes:

- selected solution packets
- recommendation reasoning
- supporting artifacts
- open questions

It should not consume raw internal research search state by default.

## Integration With Memory Tool

The planner may retrieve:

- prior DAG fragments
- reusable workflows
- reusable execution packet patterns

These should help decomposition but should not overwrite current project reality.

## Integration With Governance Tool

The planner hands governance:

- graph packets
- execution packets
- completion criteria
- validation targets

The planner proposes work structure. Governance decides what is legal to run and merge.

## Failure Modes To Avoid

- giant plan nodes that cannot be executed
- dense graphs with fake dependencies
- missing completion criteria
- planner outputs that require prose interpretation to act on
- planning becoming hidden governance

## V1 Implementation Sequence

1. define planner packet schemas
2. implement scope normalization
3. implement bounded work-item derivation
4. implement dependency inference
5. implement DAG emitter
6. implement execution packet emitter
7. integrate with governance-tool

## V1 Exit Criteria

V1 is successful when:

- one selected solution can be decomposed into bounded work items
- the work items form a real DAG
- the planner can identify ready vs blocked work
- execution packets are specific enough for downstream implementation
