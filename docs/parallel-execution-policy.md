# Parallel Execution Policy

## Objective

Codex should execute work in parallel only when the repository can prove that the slices are dependency-safe and conflict-safe.

## Preconditions for Parallel Work

Two queued slices may run in parallel only if all of the following are true:

- neither node depends on the other
- neither node is blocked by a shared unfinished dependency
- the nodes do not share a conflict domain
- both nodes have active ExecPlans
- both nodes retain their own merge-readiness path

## Forbidden Parallelism

Parallel execution is forbidden when:

- two slices mutate the same canonical artifact family
- two slices redefine the same validator or command contract
- one slice changes a graph/schema that the other slice consumes
- one slice is review-gated and that review has not happened

## Chaining Policy

Queued work should be classified as:

- `auto_runnable`
  - may start automatically once dependencies are satisfied
- `review_gated`
  - requires human review before execution
- `decision_gated`
  - requires human decision before execution

The next orchestration layer should prefer `auto_runnable` work but must still stop when merge-readiness cannot be satisfied deterministically.

## Expected Near-Term Parallelism

Initial safe parallelism is narrow:

- research-governance hardening may proceed separately from provider-sync scaffolding
- game-graph validation work may proceed separately from provider-sync scaffolding

Initial unsafe parallelism includes:

- planner CLI contract work alongside orchestrator status work
- merge-readiness engine changes alongside orchestration aggregation changes

These should remain serialized until the remaining-work graph says otherwise.
