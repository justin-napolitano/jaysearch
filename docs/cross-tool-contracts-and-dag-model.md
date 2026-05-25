# Cross-Tool Contracts And DAG Model

## Objective

Define the shared packet contracts and DAG orchestration model used across the tool ecosystem.

This document establishes:

- how tools pass information
- how orchestration represents workflows
- what a DAG node means
- what a DAG edge means
- how runs advance, block, retry, and complete

This is the shared substrate for all tool coordination.

## Core Principle

Use DAGs as the orchestration substrate, not as the universal storage model.

That means:

- packets are the handoff contract
- DAGs represent execution structure and dependency order
- memory remains typed records plus links
- tool logic stays inside tools, not in the DAG itself

## Architecture Layers

The system should be understood in layers:

1. `tool contract layer`
   Each tool has explicit inputs, outputs, rules, and failure modes.

2. `packet layer`
   Typed packets are passed between tools.

3. `DAG/orchestration layer`
   Runs are represented as DAGs of tool invocations and gated execution steps.

4. `memory layer`
   Reusable records and links are stored outside the orchestration DAG.

5. `evaluation/governance layer`
   Outcome quality and legality are checked against emitted packets and node results.

## Shared Packet Taxonomy

All cross-tool data exchange should use named packet types.

### Upstream Discovery Packets

- `project_context_packet`
- `question_candidate_packet`
- `ranked_question_packet`
- `research_question_packet`

### External Evidence Packets

- `source_record`
- `claim_record`
- `evidence_packet`

### Reuse And Memory Packets

- `problem_record`
- `solution_record`
- `artifact_record`
- `evaluation_record`
- `plan_fragment_record`
- `policy_record`

### Research Packets

- `research_problem_packet`
- `research_candidate_packet`
- `research_evaluation_packet`
- `ranked_candidate_packet`
- `research_recommendation_packet`
- `selected_solution_scope`

### Planning Packets

- `planning_request_packet`
- `work_item_packet`
- `implementation_graph_packet`
- `execution_packet`

### Governance Packets

- `governance_request_packet`
- `validation_result_packet`
- `runnable_state_packet`
- `transition_result_packet`
- `governance_decision_packet`

### Orchestration Packets

- `workflow_request_packet`
- `message_envelope`
- `run_status_packet`
- `step_result_packet`
- `failure_packet`

## Packet Rules

Every packet should follow these rules:

- stable packet type
- stable version field
- stable id
- creation timestamp
- producer identity
- payload fields that are machine-readable
- artifact refs instead of huge inline blobs where practical

Recommended shared fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `artifact_refs`

## Packet Boundary Rule

Packets are the only supported cross-tool authority boundary.

A tool may:

- read its input packets
- emit output packets
- read shared artifact refs

A tool may not:

- silently depend on another tool’s hidden local state
- require reading raw internal memory structures from another tool
- infer missing packet meaning from undocumented conventions

For research-to-planning handoff specifically:

- planner must not infer final selection authority from raw research ranking output
- canonical solution selection must be carried by `selected_solution_scope`

## DAG Purpose

The DAG model exists to represent workflow execution structure.

The DAG should answer:

- what step comes next
- what depends on what
- what can run in parallel
- what is blocked
- what produced which packet

It should not try to represent all historical knowledge or memory.

## DAG Levels

The system may use DAGs at more than one level, but each DAG must have one clear purpose.

### Workflow DAG

Represents orchestration across tools.

Examples:

- question generation
- evidence retrieval
- research run
- planning
- governance check

### Implementation DAG

Represents build work produced by the planner.

Examples:

- contract definition
- runtime implementation
- integration
- hardening

### Decision DAG

Optional later layer for complex decision trees.

This should not be required in V1.

## DAG Node Types

V1 should use a small node taxonomy.

### `tool_invocation`

Represents one call to one tool API.

Examples:

- `question-tool.derive_question_candidates`
- `evidence-search-tool.search_sources`
- `research-tool.rank_candidates`

### `packet_transform`

Represents deterministic packet shaping or normalization.

Use sparingly.

### `human_gate`

Represents a required human review, selection, or approval step.

### `governance_gate`

Represents a governance validation or readiness decision.

### `artifact_check`

Represents machine verification against emitted artifacts.

## Node Contract

Every DAG node should define:

- `node_id`
- `node_type`
- `title`
- `tool_name` if applicable
- `operation_name` if applicable
- `input_packet_refs`
- `output_packet_refs`
- `blocking_dependencies`
- `status`
- `retry_policy`
- `timeout_policy`
- `artifact_refs`

Recommended optional fields:

- `owner`
- `priority`
- `expected_outputs`
- `failure_policy`
- `human_instructions`

## Node Statuses

Recommended V1 node statuses:

- `pending`
- `ready`
- `running`
- `blocked`
- `failed`
- `completed`
- `cancelled`
- `review_gated`

These statuses should be machine-readable and consistent across workflows.

## Edge Semantics

V1 should keep edge meanings explicit.

### `depends_on`

Node A cannot run until node B completes successfully.

### `produces`

Node A produces packet or artifact B.

### `consumes`

Node A consumes packet or artifact B.

### `blocks`

Node A prevents node B from running until a condition is resolved.

### `gated_by`

Node A requires a human or governance gate before it can proceed.

The critical execution edge is `depends_on`.

## DAG Validity Rules

A valid DAG must satisfy:

- no dependency cycles
- all node refs exist
- all edge refs exist
- all required input packets are satisfiable
- all blocking dependencies are explicit
- node types are valid

If a graph violates these rules, the runner should block execution.

## Run Lifecycle

Each orchestration run should move through explicit lifecycle states.

Recommended run states:

- `draft`
- `queued`
- `running`
- `blocked`
- `failed`
- `completed`
- `cancelled`

### State Meaning

- `draft`
  created but not yet dispatchable
- `queued`
  dispatchable but not yet running
- `running`
  one or more executable nodes active
- `blocked`
  cannot progress without new input, approval, or dependency resolution
- `failed`
  terminated due to unrecoverable error
- `completed`
  all required nodes and gates completed
- `cancelled`
  intentionally stopped

## Node Execution Rules

A node is executable only if:

- its status is `ready`
- all `depends_on` predecessors are `completed`
- no unresolved `gated_by` condition exists
- required input packets exist
- no active exclusivity conflict prevents it

If any of those are false, the node must remain blocked or pending.

## Retry Rules

Retries belong to orchestration policy, not tool semantics.

Recommended V1 retry fields:

- `max_retries`
- `retryable_error_classes`
- `backoff_policy`

Retries should preserve:

- `run_id`
- `node_id`
- input packet refs

This makes retries idempotent and replayable.

## Failure Semantics

Every node failure should end in one of three categories:

### `retryable`

Transient failure; orchestration may try again.

### `blocking`

Progress cannot continue until new information or approval arrives.

### `terminal`

The node or run cannot continue without changing the workflow or packet inputs.

Every failure should emit a `failure_packet`.

## Failure Packet

Minimum fields:

- `failure_id`
- `run_id`
- `node_id`
- `failure_class`
- `failure_reason`
- `retryable`
- `artifact_refs`
- `recorded_at`

## Tool Invocation Contract

Every tool invocation node should follow the same contract:

Input:

- packet refs
- operation name
- tool policy refs if needed

Output:

- output packet refs
- execution metadata
- failure packet if needed

Required execution metadata:

- `invocation_id`
- `started_at`
- `completed_at`
- `status`
- `tool_name`
- `operation_name`

## Human Gate Contract

Human gates should be explicit DAG nodes, not hidden pauses.

Minimum fields:

- `node_id`
- `gate_type`
- `decision_required`
- `allowed_outcomes`
- `decision_ref`
- `status`

This keeps approval and selection visible inside the run.

## Governance Gate Contract

Governance gates should consume planner or execution packets and emit explicit decisions.

Minimum fields:

- `node_id`
- `governance_request_ref`
- `decision_packet_ref`
- `status`

Governance should not be implied by narrative state.

## Message Envelope

All runner-level communication should use a shared envelope.

Minimum fields:

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

## Event Log Rule

Every important run event should be append-only.

Required event classes:

- node queued
- node started
- node completed
- node failed
- run blocked
- run completed
- run cancelled
- packet emitted

If a run cannot be replayed from its event log and packet refs, the orchestration model is too weak.

## Artifact Reference Rule

Packets and nodes should prefer references to external artifacts over embedding large bodies directly.

Use refs for:

- source documents
- generated code bundles
- evaluation outputs
- graph artifacts
- failure reports

This keeps both DAG nodes and messages lightweight.

## Scope Locking

If you already have orchestration concepts that lock scope, that should remain a first-class DAG concern.

Scope should be locked through:

- explicit input packet refs
- explicit node ownership
- explicit output expectations
- explicit conflict domains

A node should not be able to silently widen its mission without producing a changed packet or graph update.

## Conflict Domains

Conflict domains exist to preserve execution sanity.

They should be declared per relevant node when:

- two nodes write the same artifacts
- two nodes require exclusive control of the same work surface
- a governance rule permits only one active branch of a kind

Conflict domains are orchestration-time control metadata, not memory structure.

## Graph-First Rule

You have chosen to use DAGs broadly. To keep that decision healthy:

- use DAGs for execution coordination
- keep node and edge semantics small
- do not overload the DAG with memory or research content that belongs in packets

This preserves the advantages of graph orchestration without recreating one giant graph object model.

## Design Law

Prefer the cheapest representation that preserves:

- correctness
- replayability
- downstream utility
- scope control

In this system:

- packets carry meaning
- DAGs carry execution structure
- event logs carry history
- memory records carry reusable knowledge

## V1 Implementation Sequence

1. define shared packet base schema
2. define message envelope schema
3. define workflow DAG node schema
4. define edge relation schema
5. define run lifecycle and failure packet schemas
6. define tool invocation contract
7. integrate tool-specific packet schemas against this shared model

## V1 Exit Criteria

V1 is successful when:

- tools can exchange packets without hidden assumptions
- orchestration DAGs can be validated before execution
- runs can be replayed from logs and packet refs
- scope and dependency control are explicit
- the DAG remains an execution model rather than a universal storage model
