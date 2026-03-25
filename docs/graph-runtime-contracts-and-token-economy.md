# Graph Runtime Contracts And Token Economy

## Objective

Define one coherent contract surface for graph-driven worker execution before broader fan-out. The graph remains canonical planner state. Runtime events, failures, lineage, and executor backends become explicit contracts around it. Token economy is treated as governance policy, not prompt etiquette.

## Layering

The platform should keep three visible authority layers:

1. Remaining-work graph
   Canonical state for node identity, dependencies, gating, readiness, initiative linkage, and queue order.
2. Initiative contract
   Bounded scope, non-goals, acceptance, and policy authority for one initiative slice.
3. Worker contract
   Narrow owned surfaces, validations, merge criteria, and explicit non-goals for one worker branch under the initiative.

Runtime execution adds two more layers without replacing the three above:

4. Worker runtime contract
   Run metadata, lifecycle events, problem details, validations, pushed refs, and executor backend outcomes.
5. Executor backend
   The place where one worker run happens: local clone, local container, cloud job, or remote VM.

## Standards Posture

The repo should use standards where they clarify interfaces, but keep kernel state repo-native.

- RFC 9457 should shape machine-readable failure artifacts.
- CloudEvents should shape runtime event envelopes.
- W3C Trace Context and OpenTelemetry-style attribute naming should shape correlation ids and telemetry fields.
- OCI should shape packaging and runtime assumptions only when a container backend is used.
- MCP is an interoperability protocol, not the default authority model for this repo.
- OpenAPI is the preferred mental model for bounded API surfaces that code can discover and call compactly.

## Graph V2 Direction

The remaining-work graph should stay canonical for planning state, but it needs stronger execution-grade linkage.

Recommended additions:

- `node_kind`
- `initiative_contract_ref`
- `worker_contract_registry_ref`
- `active_worker_contract_id`
- `last_run_id`
- `last_trace_id`
- `last_problem_ref`
- `last_validation_ref`
- `preferred_executor`
- `allowed_executors`

`graph_actions` should evolve from a thin move log into a stronger event ledger with fields such as:

- `event_id`
- `event_type`
- `occurred_at`
- `actor_id`
- `initiative_id`
- `contract_id`
- `worker_id`
- `trace_id`
- `caused_by_event_id`
- `artifact_refs`

The graph should still answer "what exists, what depends on what, what is next." It should not become a generic event bus.

## Worker Runtime Contract

Every worker run should produce the same compact artifact family regardless of executor backend.

- run metadata
  - `run_id`
  - `trace_id`
  - `initiative_id`
  - `contract_id`
  - `worker_id`
  - `executor_backend`
  - `branch`
  - `push_targets`
- lifecycle events
  - lease issued
  - workspace prepared
  - task started
  - validation completed
  - commit created
  - push succeeded or failed
  - worker completed or failed
- failure artifacts
  - RFC 9457-style problem JSON
  - optional markdown rendering derived from the same payload
- lineage artifacts
  - pushed refs
  - validation refs
  - generated outputs

## Executor Abstraction

The kernel should not care where a worker ran. It should care whether the worker contract was honored and whether durable evidence came back.

Target backend family:

- `local_clone`
- `local_container`
- `cloud_job`
- `remote_vm`

Each backend should honor the same contract:

- isolated filesystem
- explicit capabilities
- explicit network policy
- durable event and artifact return path
- deterministic cleanup semantics

## Push Targets

Push targets should be explicit runtime policy.

- local mode:
  - shared local staging remote required
  - GitHub push optional or required by policy
  - PR creation requires an explicit secondary GitHub-style remote
- cloud mode:
  - GitHub push typically required
  - local staging remote optional

The worker contract should not imply a single push target. The runtime contract should declare push-target policy per mode.

## Token Economy Policy

Token economy should be enforced as a design and validation principle.

Rules:

- prefer structured fields over prose
- prefer ids and refs over repeated narrative restatement
- prefer deltas over full snapshots
- cap rationale and summary fields
- derive human renderings from compact canonical payloads when possible
- reject oversized or redundant runtime artifacts unless the contract explicitly allows them

## API-Centric And Code-First Policy

The default execution surface should be compact APIs and generated code against them, not large prompt catalogs.

Rules:

- graphs are APIs
- initiative and worker contracts are APIs
- runtime events are APIs
- failure artifacts are APIs
- use code against bounded typed surfaces when that is cheaper and safer than loading verbose skill or MCP descriptions
- use skills and MCP servers only when they materially improve capability access without inflating context unnecessarily

This policy does not ban MCP or skills. It demotes them from default authority surfaces to bounded adapters.

## Non-Goals

- no attempt to replace the graph with CloudEvents, OpenLineage, or another external standard
- no requirement to deploy containers or cloud jobs in this planning slice
- no generic multi-project platform buildout
- no reliance on verbose always-loaded skill packs as the default worker control plane

## Planned Follow-On Implementation Order

1. graph-v2 schema and event-ledger hardening
2. worker runtime event and problem artifact implementation
3. shared staging-remote and dual-push policy implementation
4. executor backend abstraction
5. local container backend
6. cloud job backend
