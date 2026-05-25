# Node-Based Project Plan V1

## Objective

Make problem nodes and execution units the canonical project substrate.

The platform should not drift back into vague linear plans.

Major projects should be represented as DAGs of manageable problem nodes. Planner and implementation tooling should rank, expand, select, and execute those nodes.

Execution-level generate/evaluate/select semantics are defined in:

- `docs/execution-era-loop-v1.md`

## Core Thesis

A project is not one plan blob.

A project is a graph of problem nodes.

Each problem node can move through readiness states until it becomes an execution unit.

Only execution units are buildable.

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

Research support:

- Google-style evolutionary/tree-search coding systems motivate generating multiple candidate options, scoring them, and expanding high-value branches.
- `SWE-bench` supports grounding software work in concrete task definitions and evaluable repository changes: https://arxiv.org/abs/2310.06770
- `CRITIC` supports tool-grounded critique over unsupported introspection: https://arxiv.org/abs/2305.11738
- `Reflexion` supports retaining feedback from prior attempts and using it to improve future decisions: https://arxiv.org/abs/2303.11366
- W3C PROV supports explicit provenance across entities, activities, agents, usage, generation, and derivation: https://www.w3.org/TR/prov-dm/

Design consequence:

- nodes must carry provenance, options, evaluation state, selected intent, and feedback refs
- execution units must carry enough build and validation detail to be evaluated
- ranking should happen over graph nodes and options, not just over prose

## Canonical Objects

### `problem_node`

Purpose:

- represent one manageable problem in a larger project graph

Minimum fields:

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

Optional fields:

- `parent_node_refs`
- `child_node_refs`
- `conflict_domains`
- `risk_notes`
- `cost_estimate`
- `expected_value`
- `dependency_unlocks`
- `owner`

### `node_option`

Purpose:

- represent one candidate way to solve or advance a problem node

Minimum fields:

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

### `execution_unit`

Purpose:

- represent a buildable and evaluable unit of work derived from a selected node option

The execution unit is the work contract, not the solution.

Execution units are completed or advanced by `solution_artifact` records emitted by the execution ERA loop.

Minimum fields:

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

## Readiness States

Problem nodes should move through explicit readiness states:

- `draft`
- `research_ready`
- `option_generation_ready`
- `selection_ready`
- `planning_ready`
- `implementation_ready`
- `evaluation_ready`
- `complete`
- `blocked`

Readiness is not cosmetic. It controls what tools may do next.

The executable policy lives in:

- `spec/node-readiness-policy.yaml`

The local validator is:

- `bin/validate-node-readiness`

Selected scopes can be projected into problem nodes, node options, and execution units with:

- `bin/materialize-execution-unit`

The materializer must block instead of inventing owned changes or validation commands.

### State Rules

`research_ready` requires:

- goal
- problem statement
- constraints
- at least one evaluation criterion

`option_generation_ready` requires:

- research-ready fields
- evidence refs or explicit evidence-search requirement
- option generation policy

`selection_ready` requires:

- at least two options or an explicit single-option justification
- option evaluation criteria
- evidence refs

`planning_ready` requires:

- selected option
- implementation intent
- expected changes
- non-goals
- acceptance checks

`implementation_ready` requires:

- execution unit
- owned changes
- validation commands
- dependency refs
- rollback plan

`evaluation_ready` requires:

- produced artifacts
- validation output refs
- completion evidence

## Node Ranking

Planner should rank problem nodes by:

- expected value
- dependency unlocks
- readiness state
- evidence strength
- option quality
- implementation cost
- risk
- confidence
- time sensitivity where relevant

Ranking should not automatically imply execution.

Ranking chooses which nodes to expand, refine, or materialize next.

Execution requires an `execution_unit`.

## Project DAG

A major project should be represented as:

- `project_problem_graph`
- nodes: `problem_node[]`
- edges: dependency, gating, conflict, parent-child, informed-by relationships
- frontier: highest-value actionable nodes
- selected execution units: buildable work packets

Primary edge relations:

- `depends_on`
- `gated_by`
- `conflicts_with`
- `informed_by`
- `decomposes_into`
- `unlocks`

## ERA-Style Loop

The project loop should be:

1. generate or import problem nodes
2. rank problem nodes
3. select a frontier
4. generate options for frontier nodes
5. evaluate options
6. select options
7. materialize execution units
8. generate implementation attempts inside selected execution units
9. evaluate attempts
10. select best valid attempt
11. emit solution artifact
12. update feedback refs
13. rerank the graph

This loop is graph-first and non-linear.

## Anti-Drift Rules

The system must not:

- treat a selected solution scope as implementation-ready by default
- build from generic candidate-family labels
- execute nodes without implementation intent
- let planner reconstruct missing semantics from prose
- let governance approve execution units missing validation commands
- let solution artifacts overwrite execution units
- hide rejected implementation attempts

## Required Next Slices

1. `problem-node-execution-unit-contract-v1`
2. `implementation-intent-candidate-contract-v1`
3. `problem-node-ranker-v1`
4. `execution-unit-materializer-v1`
5. `planner-frontier-selector-v1`
6. `execution-era-loop-contract-v1`

## Immediate Consequence For A/B

The A/B flows are valid as research-to-selection orchestration exercises.

They are not final implementation specs until their selected options are converted into execution units with implementation intent, owned changes, validation commands, and completion evidence requirements.
