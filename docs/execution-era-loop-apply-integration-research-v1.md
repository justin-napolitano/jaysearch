# Execution ERA Loop Apply Integration Research V1

## Purpose

Design the optional apply phase for the execution ERA smoke loop.

The loop currently proves:

```text
execution_unit -> implementation_attempt -> attempt_evaluation -> solution_artifact
```

The new optional path should prove:

```text
execution_unit -> implementation_attempt -> attempt_evaluation -> solution_artifact -> applied_solution
```

## Sources

### W3C PROV-DM

Source:

- https://www.w3.org/TR/prov-dm/

Relevant claim:

- generated entities and derivations should preserve source relationships.

Design implication:

- the smoke packet should retain separate refs for `solution_artifact` and `applied_solution` instead of collapsing them.

### CRITIC

Source:

- https://arxiv.org/abs/2305.11738

Relevant claim:

- critique and acceptance improve when grounded in external tool outputs.

Design implication:

- the loop should record apply and post-apply validation result refs, not just claim that apply succeeded.

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Relevant claim:

- repository-grounded software work is evaluated through concrete code changes.

Design implication:

- an end-to-end execution smoke should optionally verify that the selected patch can be applied and validated in a repository-like target.

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- simple staged pipelines can be useful without autonomous repair loops.

Design implication:

- apply integration should route to the bounded `apply-solution-artifact` executor instead of adding repair or mutation logic to the smoke runner.

### Apply Solution Artifact Policy V1

Source:

- `docs/apply-solution-artifact-policy-v1.md`

Relevant claim:

- applying is a separate governed transition after solution emission.

Design implication:

- `run-execution-era-loop-smoke` must keep apply optional and explicit with `--apply-solution`.

## Design Decision

Add optional apply integration to `run-execution-era-loop-smoke`.

Do:

- add `--apply-solution`
- call `apply_solution_artifact` only after solution emission succeeds
- keep existing non-apply behavior unchanged
- add `applied_solution_path` to the report and smoke packet
- include apply step report in `step_reports`
- block the loop if optional apply fails

Do not:

- make apply default
- mutate current source worktree
- merge `solution_artifact` and `applied_solution`
- add autonomous retries
- skip post-apply validation

## Required Tests

- default loop still stops at `solution_artifact`
- `--apply-solution` produces `applied_solution`
- failed optional apply blocks the loop
- smoke packet records `applied_solution_ref`
- source worktree remains unchanged when apply is enabled

## Anti-Drift Rules

- apply is opt-in
- apply remains a separate step report
- apply uses the existing `apply_solution_artifact` tool
- post-apply validation evidence stays on `applied_solution`
- source worktree mutation remains out of scope
