---
id: "20260522-apply-solution-artifact-v1-codex-01"
title: "Apply Solution Artifact V1"
owner: "agent/codex"
created: "2026-05-22T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/apply-solution-artifact-policy-v1.md
  - artifacts/planner/research/apply-solution-artifact-v1-dag.json
  - spec/contracts/applied-solution.schema.yaml
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/apply_solution_artifact.py
  - bin/apply-solution-artifact
  - tests/test_apply_solution_artifact.py
  - tests/test_applied_solution_contracts.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/apply-solution-artifact-v1"
initiative_node_id: "initiative-apply-solution-artifact-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "apply-solution-artifact-tests"
      command: "uv run pytest tests/test_apply_solution_artifact.py tests/test_applied_solution_contracts.py"
      expected_exit: 0
    - name: "execution-era-regression"
      command: "uv run pytest tests/test_run_execution_era_loop_smoke.py tests/test_generate_implementation_attempt.py tests/test_evaluate_implementation_attempt.py tests/test_emit_solution_artifact.py tests/test_execution_era_contracts.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Formalize apply policy"
    priority: "P0"
  - title: "Define applied_solution schema"
    priority: "P0"
  - title: "Implement isolated apply runner"
    priority: "P0"
  - title: "Enforce owned-change patch boundary"
    priority: "P0"
  - title: "Run post-apply validation commands"
    priority: "P0"
  - title: "Emit applied_solution only after passing validation"
    priority: "P0"

depends_on:
  - "20260522-patch-producing-implementation-attempt-v1-codex-01"
  - "20260522-patch-aware-attempt-evaluation-v1-codex-01"
source_artifacts:
  - docs/apply-solution-artifact-policy-v1.md
  - docs/patch-producing-attempts-research-v1.md
  - docs/patch-aware-attempt-evaluation-research-v1.md
  - artifacts/planner/research/apply-solution-artifact-v1-dag.json
  - spec/contracts/solution-artifact.schema.yaml
---

## Objective

Build the first governed mutating executor: `apply-solution-artifact`.

The executor consumes a promoted `solution_artifact`, applies its patch in an isolated target, runs post-apply validation, and emits an `applied_solution` packet only when all gates pass.

## Research Basis

- `git apply --check` supports non-mutating patch applicability checks.
- Git worktrees support isolated working trees attached to a repository.
- SWE-bench motivates repository-grounded patch evaluation.
- Agentless motivates simple bounded repair and validation stages.
- CRITIC motivates tool-backed evaluation instead of model self-approval.
- PROV-DM motivates retaining derivation refs from solution artifact to applied result.

## Scope

In scope:

- add `applied_solution` contract
- add `bin/apply-solution-artifact`
- read execution unit, attempt, evaluation, and solution artifact packets
- validate promoted evaluation and solution refs
- validate non-empty patch ref
- reject patches that modify files outside `execution_unit.owned_changes`
- run `git apply --check`
- apply patch in isolated target
- run validation commands in isolated target
- emit apply result and validation evidence
- emit `applied_solution.packet.json` only on success

Out of scope:

- current-worktree mutation by default
- autonomous patch repair
- multiple attempt ranking
- retry loops
- merge conflict resolution
- commit creation

## CLI Contract

Command:

- `bin/apply-solution-artifact`

Required arguments:

- `--execution-unit-path`
- `--attempt-path`
- `--evaluation-path`
- `--solution-artifact-path`

Optional arguments:

- `--root`
- `--output-root`
- `--timeout-seconds`

Deferred argument:

- `--allow-current-worktree`

`--allow-current-worktree` must remain blocked or unsupported in the first implementation unless a stricter rollback and clean-worktree policy is added.

## Acceptance

- valid promoted solution with valid patch applies in isolated target
- emitted `applied_solution` contains source refs, patch ref, apply result ref, validation result refs, and applied artifact refs
- source worktree is unchanged in default mode
- non-promoted evaluation blocks
- missing patch ref blocks
- invalid patch blocks
- outside-owned-change patch blocks
- failed post-apply validation blocks
- execution ERA regression still passes
- design iteration reports no blockers

## Anti-Drift Rules

- applying is a separate state transition after solution emission
- default mode must not mutate the source worktree
- apply success without post-apply validation is not completion
- failed apply emits evidence and blockers only
- governance gates must block before mutation whenever possible
