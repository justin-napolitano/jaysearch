# Orchestration Runner V1

## Objective

Define a small orchestration runner that can coordinate the tool APIs, move packets between them, track run state, and preserve enough event history to replay or inspect a workflow.

This runner is not a research tool, not a planner, and not governance.

Its purpose is to:

- start and track multi-step runs
- route packets between tools
- manage retries and failures
- record event history
- expose run status and artifacts

## Role In The System

The intended split is:

- `evidence-search-tool`
  external evidence retrieval
- `memory-tool`
  reusable record retrieval and storage
- `research-tool`
  candidate generation, evaluation, ranking
- `planner-tool`
  DAG generation and execution packet creation
- `plan-quality-score`
  valid-plan comparison and ranking
- `governance-tool`
  execution legality and completion checks
- `orchestration-runner`
  workflow coordination across tools

The runner coordinates. It does not replace tool logic.

## Hard Boundary

The orchestration runner must not own:

- research ranking logic
- evidence selection logic
- planning semantics
- plan ranking policy
- governance policy decisions

It may route packets, track status, and apply execution policy like retry or timeout. It must not become the place where domain logic quietly accumulates.

## Core Principle

The runner should move typed packets between small tools using explicit messages and append-only run events.

It should not become:

- a hidden state machine that owns business logic
- a giant workflow DSL too early
- a second planner
- a second governance engine

## What The Runner Must Handle

V1 should handle:

- start a run from a request packet
- invoke the next tool with the right input packet
- store tool outputs and references
- emit run events
- track current run status
- stop or retry on failure

That is enough for V1.

## Messaging Model

Use a typed message envelope for all tool-to-runner and runner-to-tool traffic.

### Message Envelope

Minimum fields:

- `message_id`
- `run_id`
- `step_id`
- `message_type`
- `source`
- `target`
- `created_at`
- `payload_ref` or `payload`
- `correlation_id`

Recommended optional fields:

- `causation_id`
- `retry_count`
- `priority`
- `deadline`

## Message Types

V1 should keep the type set small.

- `run_requested`
- `tool_invocation_requested`
- `tool_invocation_started`
- `tool_invocation_completed`
- `tool_invocation_failed`
- `packet_emitted`
- `run_blocked`
- `run_completed`
- `run_cancelled`

## Packet Transport

The message envelope should carry references to packets, not giant inline blobs by default.

Recommended pattern:

- small metadata in the message
- packet body stored in object storage, file storage, or a record store
- message points to `payload_ref`

This prevents huge messages and keeps replay simpler.

## Recommended V1 Transport

For V1, prefer a local-first and inspectable model:

1. append-only event log
2. packet store
3. small queue abstraction

Recommended first implementation:

- event log: `JSONL`
- packet store: typed JSON artifacts or SQLite-backed records
- queue: in-process or SQLite-backed pending-work table

This is better than introducing Kafka or a large broker immediately.

## Why Not A Heavy Broker First

A heavy distributed messaging stack is premature unless you already need:

- high-throughput multi-host dispatch
- long-lived distributed consumers
- large concurrent workflow volume

For V1, the important thing is explicit envelopes and replayable events, not broker sophistication.

## Run Model

Each orchestration run should have:

- `run_id`
- `workflow_type`
- `requested_by`
- `start_packet_ref`
- `current_status`
- `current_step`
- `step_history`
- `artifact_refs`
- `created_at`
- `updated_at`

## Workflow Types

V1 should support a small number of workflows.

### `research_only`

Flow:

- evidence search
- memory retrieval
- research run
- recommendation emission

### `research_to_planning`

Flow:

- evidence search
- memory retrieval
- research run
- planning request
- DAG emission

### `planning_to_governance`

Flow:

- planner output intake
- execution packet generation
- governance validation
- runnable-state decision

Do not start with arbitrary free-form workflows.

## Step Model

Each run should be composed of explicit steps.

Minimum step fields:

- `step_id`
- `tool_name`
- `input_packet_ref`
- `output_packet_ref`
- `status`
- `started_at`
- `completed_at`
- `error_ref`

## Status Model

Recommended run statuses:

- `queued`
- `running`
- `blocked`
- `failed`
- `completed`
- `cancelled`

Recommended step statuses:

- `pending`
- `running`
- `completed`
- `failed`
- `skipped`

## Orchestration Policy

The runner should not decide domain logic, but it does need policy for execution behavior.

V1 orchestration policy:

- max retries per step
- retryable error classes
- timeout per tool invocation
- cancellation behavior
- artifact retention policy

These policies control execution behavior only. They must not duplicate tool-specific decision logic.

## Failure Handling

V1 should support three failure outcomes:

### Retry

Use when:

- transport failure
- transient tool failure
- timeout likely recoverable

### Block

Use when:

- required input packet missing
- downstream dependency unresolved
- human decision needed

### Fail

Use when:

- packet invalid
- non-recoverable tool error
- workflow policy violation

The runner should record which one occurred and why.

## Observability

The runner must emit enough information to reconstruct a run.

Required observability artifacts:

- run event log
- step status table or log
- packet references
- failure records
- final outcome packet

If the run cannot be replayed or inspected from its artifacts, the runner is too opaque.

## Integration Contracts

### With Evidence Search

The runner sends:

- problem packet
- search constraints

The runner receives:

- evidence packet
- source refs

### With Memory

The runner sends:

- search and ranking requests

The runner receives:

- retrieved reusable records
- ranked reusable candidates

### With Research

The runner sends:

- problem packet
- evidence packet
- memory context

The runner receives:

- candidate packets
- evaluation packets
- recommendation packet

### With Planner

The runner sends:

- planning request packet
- selected solution refs

The runner receives:

- implementation graph packet
- execution packets

### With Governance

The runner sends:

- graph slice packet
- execution packet
- completion evidence

The runner receives:

- validation results
- runnable-state decision
- completion or merge decision

## Message Ordering

V1 should assume per-run ordering, not global ordering across all runs.

That means:

- events inside one run should be sequenced
- independent runs do not need total ordering

This simplifies implementation significantly.

## Idempotency

Every tool invocation should support idempotent retry by using:

- stable `run_id`
- stable `step_id`
- stable input packet refs

If a step is retried, the system should be able to detect duplicate completion or safely overwrite the same step result.

## Recommended V1 Storage Layout

Example local-first layout:

```text
artifacts/orchestration/
  runs/
    <run_id>/
      run.json
      events.jsonl
      steps/
        <step_id>.json
      packets/
        <packet_id>.json
      failures/
        <failure_id>.json
```

This is easy to inspect and migrate later.

## API Surface

### `start_run`

Purpose:

- create a run from an initial workflow request

Input:

- `workflow_request_packet`

Output:

- `run_record`

### `dispatch_step`

Purpose:

- invoke the next tool step

Input:

- `run_id`
- `step_request_packet`

Output:

- `step_result_packet`

### `get_run_status`

Purpose:

- inspect run state and current step

Input:

- `run_id`

Output:

- `run_status_packet`

### `record_event`

Purpose:

- append a typed run event

Input:

- `message_envelope`

Output:

- `recorded_event_ref`

### `cancel_run`

Purpose:

- cancel an active run

Input:

- `run_id`

Output:

- `run_status_packet`

## Workflow Request Packet

Minimum fields:

- `workflow_request_id`
- `workflow_type`
- `initial_packet_ref`
- `requested_outputs`
- `policy_ref`

## Run Status Packet

Minimum fields:

- `run_id`
- `workflow_type`
- `status`
- `current_step`
- `completed_steps`
- `failed_steps`
- `artifact_refs`
- `last_event_ref`

## Future Evolution

Possible later upgrades:

- broker-backed queue
- multi-worker dispatch
- step leasing
- scheduled runs
- human approval pauses
- cross-project orchestration routing

These should come after the basic local-first runner works.

## Failure Modes To Avoid

- orchestration logic swallowing tool outputs
- giant inline message payloads
- hidden mutable run state
- workflow logic duplicated across runner and tools
- non-replayable runs

## V1 Implementation Sequence

1. define message envelope schema
2. define workflow request and run status packets
3. implement append-only event log
4. implement packet store
5. implement step dispatcher
6. implement failure and retry handling
7. integrate with evidence, memory, research, planner, and governance tools

## V1 Exit Criteria

V1 is successful when:

- one multi-step run can be started and replayed
- typed packets move cleanly between tools
- failures are explicit and inspectable
- run state is visible without reading raw code
