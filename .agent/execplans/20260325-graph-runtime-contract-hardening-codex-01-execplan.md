---
id: "20260325-graph-runtime-contract-hardening-codex-01-execplan"
title: "Harden graph and worker runtime contracts with standards-aware events, failures, and token-economy policy"
owner: "agent/codex-01"
created: "2026-03-25T00:00:00Z"
status: draft
base_branch: initiative/platform-surface-simplification
changes:
  - .agent/execplans/20260325-graph-runtime-contract-hardening-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/graph-runtime-contracts-and-token-economy.md
  - docs/references.md
  - resources/biblio/README.md
  - resources/biblio/token-economy-and-api-first-execution.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/platform-surface-simplification"
initiative_node_id: "initiative-platform-surface-simplification"
graph_registration:
  node_id: "rwg-039"
  queue_position: 39
  goal_area: "orchestrator-runtime"
  conflict_domains:
    - "documentation"
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260325-graph-runtime-contract-hardening-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "docs/graph-runtime-contracts-and-token-economy.md"
    - "docs/references.md"
    - "resources/biblio/README.md"
    - "resources/biblio/token-economy-and-api-first-execution.md"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260325-graph-runtime-contract-hardening-codex-01-20260325"
draft_created: "2026-03-25T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260325-graph-runtime-contract-hardening-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Define graph-v2 event and provenance requirements without replacing the graph as canonical state"
    priority: "P1"
  - title: "Define one worker runtime contract for events, failures, lineage, executor backends, and push-target outcomes"
    priority: "P1"
  - title: "Define token-economy, API-centric, deterministic-contract-first, and code-over-verbose-context policy"
    priority: "P1"
  - title: "Sequence follow-on implementation work so local, container, and cloud executors can share one kernel contract"
    priority: "P1"
depends_on:
  - "20260319-platform-surface-simplification-codex-01-execplan"
---

# Purpose / Big Picture

Turn the current worker-governance prototype into a standards-aware execution contract plan before more orchestration is added. The graph should remain the canonical kernel state, while runtime events, problem details, telemetry correlation, and executor backends become explicit contracts around it. This slice also makes token economy a first-class governance policy so API-centric code and compact structured artifacts replace verbose prompt surfaces wherever possible.

## Progress

- [ ] define graph-v2 event, provenance, and runtime-linkage requirements
- [ ] define worker lifecycle event and failure artifact contracts
- [ ] define executor abstraction and push-target policy for local staging and GitHub durability
- [ ] define token-economy and API-centric execution policy with explicit non-goals
- [ ] sequence the follow-on implementation slices under this initiative

## Surprises & Discoveries

- the current initiative/worker/lease model is strong enough to expose the next real gap: runtime contracts are still thinner than the governance model around them
- the remaining-work graph is already useful as canonical state, but it is not yet rich enough to serve as the authoritative reconciliation surface for many parallel worker runs
- RFC 9457-style problem details, CloudEvents-like lifecycle envelopes, and W3C-trace-aligned identifiers fit this repo better as adapters around the kernel than as replacements for repo-native state
- token economy is not just prompt hygiene; it is a runtime policy choice about how much surface area the system exposes to the model
- for large tool surfaces, code written against bounded API contracts can be materially cheaper and more deterministic than loading large MCP or skill inventories into context

## Decision Log

- keep the remaining-work graph as canonical planner state rather than replacing it with an external event or lineage standard
- treat standards as contract influences:
  1. RFC 9457 for machine-readable failure payloads
  2. CloudEvents-like envelopes for lifecycle events
  3. W3C Trace Context and OpenTelemetry-style naming for correlation
  4. OCI only when a container executor is used
- make executor choice a backend field, not an architecture fork
- define token economy as enforceable governance policy rather than a best-effort prompting preference
- prefer API-centric code and compact typed surfaces over verbose skill or MCP context when the task can be served safely by bounded code execution

## Outcomes & Retrospective

- expected outcome: one coherent design and governance contract for graph state, runtime events, failures, observability, executor backends, and token economy
- expected retrospective question: which parts should be implemented directly in repo-native schemas versus projected through adapter layers

## Context and Orientation

- the current initiative already established the smaller public platform model and the governed worker runtime prototype
- worker bootstrap, leasing, isolated execution, staging-remote durability, and worker-contract enforcement now work locally
- those runtime surfaces still emit mostly custom reports and lease-centric summaries rather than one compact event/failure lineage contract
- the next useful step is not adding more worker features first; it is hardening the contract boundaries that local, container, and cloud execution should all share

## Plan of Work

1. define the graph-v2 changes needed for runtime-grade provenance without collapsing planning state into event history
2. define the worker runtime artifact model:
   - run metadata
   - lifecycle events
   - failure artifacts
   - validation outputs
   - push-target outcomes
3. define executor backend invariants shared across:
   - local clone or worktree
   - local container
   - cloud job
   - remote VM
4. define token-economy and API-centric execution policy:
   - compact structured outputs
   - bounded rationale fields
   - least-string surfaces
   - code-over-verbose-context when safe
5. sequence the follow-on implementation work so runtime hardening lands before broad worker fan-out

## Concrete Steps

1. register this slice in the remaining-work graph and queue mirror under the current initiative
2. write a durable design note that defines graph-v2 runtime contracts, worker runtime artifacts, executor abstraction, and token-economy policy
3. add a bibliography note for API-first, code-mode, and compact capability-surface references
4. update the repo reference pack so future slices cite the same local standards and token-economy sources
5. use this slice as the planning authority for follow-on runtime implementation work

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260325-graph-runtime-contract-hardening-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- the graph and queue mirror both register `rwg-039` under `initiative/platform-surface-simplification`
- the design note defines:
  1. graph-v2 event/provenance direction
  2. worker runtime event and failure contracts
  3. executor backend abstraction
  4. token-economy and API-centric execution policy
- the plan explicitly preserves future local-container and cloud-job execution without turning the current repo into a generic platform buildout

## Idempotence and Recovery

- rerunning validation should be safe as long as the graph node, queue mirror, and ExecPlan metadata stay aligned
- if later implementation discovers the graph-v2 scope is too broad, follow-on slices should split runtime artifacts, graph schema, and executor backends into separate adjacent contracts rather than silently widening one implementation branch
- if some surfaces still require skills or MCP servers, they should remain bounded adapters under the token-economy policy rather than becoming default context-loading behavior

## Artifacts and Notes

- supporting design note: `docs/graph-runtime-contracts-and-token-economy.md`
- supporting bibliography note: `resources/biblio/token-economy-and-api-first-execution.md`
- local runtime behavior this slice is meant to harden:
  1. initiative contract plus worker contract execution
  2. lease and audit lifecycle
  3. shared staging-remote durability model
  4. future dual-push policy
- this slice is planning and contract hardening, not the full runtime implementation itself

## Interfaces and Dependencies

- this slice depends on the completed platform-surface simplification work for the smaller public model and current worker-governance baseline
- follow-on implementation slices should preserve one kernel contract across local and remote executors
- this slice should not force containerization, Azure-specific execution, or cross-project governance platform work before the runtime contracts are stable
