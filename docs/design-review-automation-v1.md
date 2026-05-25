# Design Review Automation V1

## Objective

Define the automation layer that lets `design-iteration-tool` request bounded tool calls during review without turning the design tool into the general workflow runner.

The point of this layer is:

- let design review ask for evidence when a claim needs support
- let design review replay planner or governance checks when a boundary needs validation
- preserve explicit authority boundaries
- keep every tool call replayable and auditable

## Why This Layer Exists

The current system can already:

- review contracts and planning artifacts
- compare plans
- materialize execution slices
- validate governance handoff

What it cannot yet do automatically is:

- decide that a finding needs supporting research
- request the right bounded tool call
- route that request through the runner
- fold the results back into the design review packet stream

That is the gap this layer fills.

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

The automation should follow tool-assisted critique, not pure self-reflection:

- `Self-Refine` supports iterative feedback loops, but still relies on self-generated critique when no external tools are used: https://arxiv.org/abs/2303.17651
- `Reflexion` supports iterative improvement with memory and feedback, but again depends on explicit feedback signals rather than implicit trust in first-pass reasoning: https://arxiv.org/abs/2303.11366
- `CRITIC` is the strongest direct match here because it shows that external tool interaction improves critique quality over unsupported introspection: https://arxiv.org/abs/2305.11738

The architectural consequence is:

- `design-iteration-tool` should decide *what needs checking*
- `orchestration-runner` should execute *the bounded tool calls*
- evidence and validation tools should provide *the supporting results*

## Hard Boundary

`design-iteration-tool` must not become:

- the general execution runner
- a hidden evidence-search engine
- a hidden planner
- a hidden governance engine

`orchestration-runner` must not become:

- the owner of critique semantics
- the owner of design findings
- the place where ranking or evidence judgment quietly accumulates

## Operating Model

The automation loop has four layers:

1. `review request`
   Human or upstream workflow asks for a bounded design review.

2. `review program`
   `design-iteration-tool` turns that request into a bounded review program with explicit review nodes and stop conditions.

3. `tool-call execution`
   `orchestration-runner` executes the requested bounded calls.

4. `finding synthesis`
   `design-iteration-tool` folds the returned artifacts into findings, gaps, and next-question candidates.

## Core Contracts

### `design_review_request_packet`

Purpose:

- canonical request to start an automated design review

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

### `design_review_program_packet`

Purpose:

- bounded design-review program emitted by `design-iteration-tool`

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

Invariant:

- review nodes must be bounded and replayable

### `tool_call_request_packet`

Purpose:

- canonical request from review logic into the runner for a bounded tool invocation

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

Invariant:

- requests must target one bounded operation on one tool

### `tool_call_result_packet`

Purpose:

- canonical result envelope for a bounded tool call

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

Invariant:

- result packets must never silently inline large tool outputs when artifact refs are available

## Allowed Tool Calls In V1

The review program may request:

- `evidence-search-tool`
  - retrieve supporting papers, docs, or benchmark refs for a design claim

- `memory-tool`
  - retrieve prior similar findings or solved boundary patterns

- `plan-quality-score`
  - compare alternative structural plans if the review is about planning quality

- `governance-execution-intake`
  - validate whether an execution-ready handoff is actually governance-safe

- `design-iteration-tool`
  - run the machine-checkable validator families on artifacts already in scope

The review program must not request:

- open-ended recursive tool spawning
- arbitrary code execution without a declared artifact target
- direct code-writing as part of review

## Review Modes

V1 should support a small set of explicit review modes:

- `contract_review`
- `workflow_dag_review`
- `implementation_dag_review`
- `planning_quality_review`
- `governance_handoff_review`
- `evidence_backed_claim_review`
- `self_loop_review`
- `question_research_handoff_review`
  Reviews whether the `question -> evidence -> research` handoff is sufficiently specified to build against.
  V2 expectation:
  It should inspect not only docs and the shared registry, but also whether concrete packet examples and transform surfaces exist.

Each requested mode should map to one or more bounded review nodes.

`self_loop_review` is special:

- it reviews the automation loop artifacts themselves
- it must stay bounded to explicit automation artifacts and contracts
- it must not recurse into unbounded self-spawning review programs

`question_research_handoff_review` is also special:

- it focuses on the upstream handoff from question generation to evidence assembly to research problem materialization
- it should inspect shared contracts and boundary docs directly
- it should not pretend the full research runtime is being executed

## Node Model

Each review node should declare:

- `node_id`
- `review_mode`
- `target_artifact_refs`
- `tool_call_requirements`
- `success_condition`
- `failure_routing`

This keeps the review program structured enough for runner execution.

## Stop Conditions

V1 stop conditions should include:

- `max_tool_calls`
- `max_blocking_findings`
- `time_budget_seconds`
- `evidence_sufficiency_reached`
- `no_new_material_findings`

This prevents the loop from growing into an unbounded agent swarm.

## Review Synthesis Rule

The design tool should synthesize findings only from:

- validated local artifact checks
- explicit tool-call result packets
- attributable evidence refs

It should not treat unsupported intuition as final evidence.

## Recommended V1 Workflow

1. accept `design_review_request_packet`
2. emit `design_review_program_packet`
3. runner executes review nodes
4. collect `tool_call_result_packet[]`
5. emit:
   - `design_findings_packet`
   - `design_gap_packet[]`
   - `next_question_candidate_packet[]`

## First Use In This Repo

The first practical use should be:

- review the current toolchain architecture
- request evidence only when a major design claim needs support
- request plan/governance replay when a handoff claim needs verification
- keep the rest contract- and DAG-driven

That is enough to back a whole-plan review with both local artifacts and external sources without overbuilding the automation layer.
