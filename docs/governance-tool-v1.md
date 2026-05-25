# Governance Tool V1

## Objective

Define a standalone governance API that takes planned execution work and enforces bounded approval, validation, execution-state, and merge-control rules.

This tool is not the research runtime and not the planner.

Its purpose is to:

- validate execution packets and graph state
- gate work before execution
- track legal state transitions
- record approvals and validations
- control merge and completion readiness

## Role In The System

The intended split is:

- `evidence-search-tool`
  external evidence retrieval
- `memory-tool`
  reusable record storage and retrieval
- `research-tool`
  candidate generation and evaluation
- `planner-tool`
  DAG generation and execution packet creation
- `governance-tool`
  execution legality, validation, and merge control

The governance tool does not choose solutions and does not invent work structure. It enforces how approved work may proceed.

## Hard Boundary With Planner

Governance consumes planner structure. It does not create planner structure.

Governance should reject or block incomplete planner packets rather than silently invent:

- dependencies
- task structure
- output expectations
- completion criteria

If a planner packet is underspecified, the correct result is a blocker, not governance-side reconstruction.

## Core Principle

Governance should be small, explicit, and use-case-bounded.

It should answer:

- is this work allowed to start
- what validations are required
- what state transitions are legal
- what is ready to merge or promote

## V1 Use Case

V1 should support:

- validating planner-generated execution packets
- determining whether a node is runnable now
- checking completion evidence
- deciding whether a work slice is ready to merge or advance

The first version should be simpler than the existing large platform harness.

## Rewrite Guidance

Do not rewrite the existing large governance harness before the new packet boundaries are stable.

The correct order is:

1. define cross-tool packet contracts
2. define planner-to-governance runnable contract
3. implement small governance use cases against those packets
4. simplify or replace the large harness incrementally

If governance is rewritten before those contracts harden, the likely result is another oversized system.

## Non-Goals

V1 should not become:

- a monolithic all-project platform
- a giant rules engine with hidden behavior
- a planner
- a research runtime

It should stay focused on execution legality and state control.

## End-To-End Flow

1. accept `governance_request_packet`
2. validate the execution packet or graph slice
3. evaluate required approvals and checks
4. determine legal current state
5. emit `governance_decision_packet`
6. record state transition or blocker set

## API Surface

### `validate_execution_packet`

Purpose:

- check whether a planner-emitted work packet is structurally and procedurally valid

Input:

- `execution_packet`
- `governance_policy`

Output:

- `validation_result_packet`

### `check_runnable_state`

Purpose:

- determine whether a work item is legal to start now

Input:

- `graph_slice_packet`
- `execution_packet`
- `current_state_packet`

Output:

- `runnable_state_packet`

### `record_transition`

Purpose:

- register a legal state transition

Input:

- `transition_request_packet`

Output:

- `transition_result_packet`

### `check_completion_readiness`

Purpose:

- determine whether a work slice is ready for completion, promotion, or merge

Input:

- `completion_evidence_packet`
- `governance_policy`

Output:

- `governance_decision_packet`

## Primary Packets

### `governance_request_packet`

Purpose:

- canonical governance input wrapper

Minimum fields:

- `request_id`
- `project_id`
- `target_type`
- `target_ref`
- `policy_ref`
- `current_state`

### `validation_result_packet`

Purpose:

- structural and policy validation result

Minimum fields:

- `target_ref`
- `valid`
- `errors`
- `warnings`
- `required_actions`

### `runnable_state_packet`

Purpose:

- determination of whether work may start now

Minimum fields:

- `target_ref`
- `runnable`
- `blockers`
- `missing_dependencies`
- `required_approvals`

### `transition_result_packet`

Purpose:

- result of requested state transition

Minimum fields:

- `target_ref`
- `from_state`
- `to_state`
- `allowed`
- `blockers`
- `recorded_at`

### `governance_decision_packet`

Purpose:

- final readiness decision for merge, promotion, or completion

Minimum fields:

- `target_ref`
- `decision`
- `blockers`
- `evidence_refs`
- `required_followups`

## Minimal State Model

Keep the state model small in V1.

Recommended states:

- `draft`
- `ready`
- `active`
- `blocked`
- `review_gated`
- `completed`
- `merge_ready`

Only explicit transitions should be legal.

## Core Governance Checks

V1 should enforce only a few high-value checks:

- packet structure valid
- dependencies satisfied
- required validations passed
- required approvals present
- completion evidence attached
- merge criteria met

Do not start with a huge abstract rule universe.

## Policy Model

Governance policy should be data-driven and small.

V1 policy dimensions:

- required validations
- required approvals
- allowed state transitions
- merge readiness requirements
- conflict-domain exclusivity rules

## Runnable Decision Rules

A work item is runnable only if:

- planner marked it ready or dependencies are complete
- no required dependency is incomplete
- no blocking governance policy applies
- no exclusive conflict-domain collision is active

Planner output should therefore provide explicit runnable preconditions. Governance validates those conditions but should not author them.
- required start approvals are present

## Completion And Merge Rules

A work item is merge-ready only if:

- expected outputs are present
- required validations passed
- required evidence refs attached
- completion criteria satisfied
- no unresolved blocker remains

## Integration With Planner Tool

The governance tool consumes:

- `implementation_graph_packet`
- `execution_packet`
- completion criteria
- validation targets

Governance should never have to infer the plan structure from prose.

## Integration With Research Tool

The governance tool may consume:

- recommendation packets
- evidence refs
- selected solution refs

Only to validate promotion or planning handoff, not to re-run research.

## Integration With Memory Tool

The governance tool may retrieve:

- prior policy patterns
- prior validation precedents

But current decisions must still be made from current packets and current evidence.

## Simplification Guidance

To avoid recreating the current oversized harness, V1 governance should be split by use case:

- execution packet validation
- runnable-state decision
- transition recording
- completion or merge readiness

Each API should do one thing well.

## Failure Modes To Avoid

- hidden state transitions
- giant cross-cutting rules
- governance deciding plan structure
- governance re-running research decisions
- merge readiness depending on undocumented operator knowledge

## V1 Implementation Sequence

1. define governance packet schemas
2. define minimal policy schema
3. implement execution packet validation
4. implement runnable-state check
5. implement transition recorder
6. implement completion-readiness check

## V1 Exit Criteria

V1 is successful when:

- planner output can be checked deterministically
- runnable vs blocked work is machine-readable
- legal state transitions are explicit
- completion and merge readiness are based on attached evidence
