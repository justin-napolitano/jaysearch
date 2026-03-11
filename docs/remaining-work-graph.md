# Remaining Work Graph

## Objective

The remaining platform work must be schedulable by Codex without collapsing into a vague list of "next steps." This graph makes the backlog canonical, dependency-aware, and safe for controlled parallel execution.

## Canonical Role

The remaining-work graph is canonical for:

- backlog node identity
- dependency ordering
- conflict domains
- queued ExecPlan readiness classification
- chaining posture for future orchestration

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

These areas are not equivalent in readiness. The graph artifact defines which are already completed, which are ready for a dedicated `impl-execplan/*` branch now, and which remain blocked or gated.
