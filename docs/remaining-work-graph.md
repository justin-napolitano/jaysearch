# Remaining Work Graph

## Jaysearch Workflow Status

This graph is historical for the current Jaysearch repo workflow.

Jaysearch preserves `artifacts/planner/research/remaining-work-graph.json` and its action history so prior platform-control-plane decisions remain inspectable. It is no longer the blocking authority for current pre-push development because the graph was inherited from the platform-template backlog and does not yet model the Jaysearch product DAG accurately.

Current Jaysearch development should be gated by branch policy, governance lint, ExecPlan lint, runtime checks, public API checks, tests, and the product DAG artifacts being built under `artifacts/planner/research/`. A future slice should replace this historical backlog with a Jaysearch-native work graph that models product nodes such as question intake, research loops, candidate DAG generation, DAG selection, execution units, and implementation attempts.

## Objective

The remaining platform work must be schedulable by Codex without collapsing into a vague list of "next steps." This graph makes the backlog canonical, dependency-aware, and safe for controlled parallel execution.

## Canonical Role

The remaining-work graph is canonical for:

- backlog node identity
- dependency ordering
- conflict domains
- queued ExecPlan readiness classification
- canonical graph-action records for governed backlog moves
- deterministic ready-order and queue-position fields
- chaining posture for future orchestration
- implementation-branch targeting for ready slices
- machine-checkable active-slice and ready-slice derivation when paired with `bin/remaining-work-graph-check`
- queue-projection freshness metadata for `docs/queued-execplans.md`

It is not canonical for:

- governance-rule relationships
- research provenance relationships
- merge-readiness results for a specific branch

Those remain governed by the rule graph, bibliography graph, claim registry, and merge-readiness engine.

## Node Model

Each remaining-work node should define:

- stable node id
- title
- goal area
- dependency list
- conflict domain list
- gating class
- expected artifact outputs
- target ExecPlan id
- implementation branch when the slice is runnable now
- explicit `status_reason` whenever the node is blocked or review/decision gated
- deterministic ordering metadata when the node participates in governed queue order
- machine-readable action state when governed work moves between blocked, ready, reordered, or completed states

Top-level graph state should also define:

- `graph_actions` as the canonical move log for governed backlog transitions
- `ordering_policy` as the deterministic ready-order contract
- `queue_projection` as the projection-only freshness handshake with `docs/queued-execplans.md`

## Gating Classes

- `ready`
  - may be drafted and executed now if branch conditions are satisfied
- `blocked`
  - dependency work is incomplete
- `review_gated`
  - technically unblocked, but requires explicit human review before execution
- `decision_gated`
  - requires a human decision on scope or policy before execution

## Conflict Domains

Parallel execution is legal only when nodes do not collide on conflict domains. Initial domains for this platform:

- `planner-cli`
- `orchestrator-status`
- `merge-readiness`
- `research-governance`
- `game-graph`
- `provider-sync`

## Initial Remaining Work Areas

The initial queued areas captured by this graph are:

1. machine-readable output hardening
2. composite orchestrator status surface
3. game-graph validator and game-aware status surface
4. implementation orchestrator runtime
5. provider-sync scaffolding

These areas are not equivalent in readiness. The graph artifact and `bin/remaining-work-graph-check` define which are already completed, which are ready for a dedicated `impl-execplan/*` branch now, and which remain blocked or gated.

## Ordering and Reorder Law

Ready work order is canonical only when all of the following are true:

- a ready node has explicit `ordering.ready_order`
- its `action_state.last_action` is `promote_ready`
- any reorder was recorded in `graph_actions`
- `queue_projection.last_reconciled_action_id` matches the latest canonical graph action
- `docs/queued-execplans.md` mirror metadata matches the graph

This means reorder operations are legal moves, not silent edits. GitHub Projects and other boards may display queue position or next action, but those values must be projected from the validated local graph rather than authored remotely.
