# Apply Solution Artifact Policy V1

## Purpose

Define the governed boundary for turning a promoted `solution_artifact` into an applied repository change.

This is the first mutating execution boundary. V1 must preserve the safety properties established by patch-producing attempts and patch-aware evaluation.

## Sources

### Git Apply

Source:

- https://git-scm.com/docs/git-apply

Relevant claim:

- `git apply --check` verifies whether a patch applies without applying it.

Design implication:

- the apply executor must re-run `git apply --check` immediately before applying a patch.

### Git Worktree

Source:

- https://git-scm.com/docs/git-worktree

Relevant claim:

- Git worktrees allow multiple working trees attached to the same repository.

Design implication:

- V1 should apply patches in an isolated worktree or explicitly isolated apply directory before current-worktree mutation is allowed.

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Relevant claim:

- repository-grounded software work is evaluated as concrete code changes against task context.

Design implication:

- a promoted solution is not complete until the patch is applied in a repository context and validation commands run against the changed tree.

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- simple localization, repair, and validation stages can be effective without broad autonomous mutation.

Design implication:

- V1 should keep patch application as a small, deterministic executor step, not an autonomous repair loop.

### CRITIC

Source:

- https://arxiv.org/abs/2305.11738

Relevant claim:

- tool-interactive critique is stronger than unsupported self-correction.

Design implication:

- post-apply promotion must rely on command output and recorded artifacts, not model judgment.

### W3C PROV-DM

Source:

- https://www.w3.org/TR/prov-dm/

Relevant claim:

- generated entities and derivations should preserve provenance.

Design implication:

- applied changes must retain refs to the source execution unit, selected attempt, evaluation, solution artifact, patch, apply result, and validation results.

## Design Decision

Build `apply-solution-artifact-v1` as a governed executor that consumes one promoted `solution_artifact`.

Default V1 mode:

- isolated apply worktree
- no current-worktree mutation
- no patch synthesis
- no repair retries

The executor may later gain a current-worktree mode, but only behind a stricter policy gate.

## Required Inputs

- `execution_unit` packet
- `implementation_attempt` packet
- `attempt_evaluation` packet
- `solution_artifact` packet
- non-empty `solution_artifact.patch_ref`
- patch validation evidence in `solution_artifact.completion_evidence_refs`

## Required Gates

The executor must block unless all gates pass:

- `solution_artifact.packet_type == "solution_artifact"`
- selected attempt and evaluation refs match the solution artifact
- evaluation `promotion_status == "promoted"`
- evaluation has no blockers
- `patch_ref` is non-empty and resolves to an existing file
- patch path is inside an allowed artifact area or explicitly absolute under the repo root
- patch only changes paths listed in `execution_unit.owned_changes`
- `git apply --check` passes immediately before apply
- apply target is isolated unless `--allow-current-worktree` is explicitly supplied
- validation commands from the execution unit run after apply
- post-apply validation commands pass before emitting `applied_solution`

## State Transition

```text
solution_artifact(promoted)
  -> apply_solution_artifact(policy gates)
  -> applied_solution(success)
```

Blocked transition:

```text
solution_artifact(promoted)
  -> apply_solution_artifact(policy gates)
  -> apply_blocked(reason, evidence_refs)
```

## Applied Solution Packet

V1 should emit an `applied_solution` packet after successful apply and validation.

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `applied_solution_id`
- `source_solution_artifact_ref`
- `source_execution_unit_ref`
- `selected_attempt_ref`
- `evaluation_ref`
- `patch_ref`
- `apply_target_ref`
- `apply_result_ref`
- `validation_result_refs`
- `applied_artifact_refs`
- `status`
- `blockers`

## Runtime Contract

Command:

- `bin/apply-solution-artifact`

Required args:

- `--execution-unit-path`
- `--attempt-path`
- `--evaluation-path`
- `--solution-artifact-path`

Default behavior:

- create isolated apply target under `artifacts/apply-solution/runs/<run-id>/worktree`
- run `git apply --check`
- apply the patch in the isolated target
- run execution-unit validation commands in the isolated target
- emit apply result artifacts
- emit `applied_solution.packet.json` only if all gates pass

Optional args:

- `--output-root`
- `--timeout-seconds`
- `--allow-current-worktree`

`--allow-current-worktree` is out of scope for first implementation unless the policy file is extended with explicit clean-worktree and rollback requirements.

## Required Tests

- blocks non-promoted evaluation
- blocks missing patch ref
- blocks patch that changes files outside `owned_changes`
- blocks invalid patch before apply
- applies valid patch in isolated target
- runs validation commands after apply
- blocks failed post-apply validation
- emits `applied_solution` with apply and validation evidence
- does not mutate the source worktree in default mode

## Anti-Drift Rules

- apply is a separate transition after solution emission
- patch applicability is not correctness
- post-apply validation is required for `applied_solution`
- default mode must not mutate the source worktree
- current-worktree mutation requires an explicit future policy extension
- failed apply must emit evidence, not claim completion

## Recommendation

Build the policy, DAG, and exec plan before implementation.

Then implement isolated apply first. Do not implement current-worktree apply until isolated apply is passing and governed by tests.
