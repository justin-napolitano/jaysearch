---
id: "20260522-patch-aware-attempt-evaluation-v1-codex-01"
title: "Patch Aware Attempt Evaluation V1"
owner: "agent/codex"
created: "2026-05-22T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/evaluate_implementation_attempt.py
  - tests/test_evaluate_implementation_attempt.py
  - docs/patch-aware-attempt-evaluation-research-v1.md
  - docs/patch-producing-attempts-research-v1.md
  - docs/execution-era-runtime-research-v1.md
  - artifacts/planner/research/patch-aware-attempt-evaluation-v1-dag.json
  - .agent/execplans/20260522-patch-aware-attempt-evaluation-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/patch-aware-attempt-evaluation-v1"
initiative_node_id: "initiative-patch-aware-attempt-evaluation-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "patch-aware-attempt-evaluation-tests"
      command: "uv run pytest tests/test_evaluate_implementation_attempt.py tests/test_generate_implementation_attempt.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Detect patch_ref on implementation_attempt"
    priority: "P0"
  - title: "Validate patch_ref existence"
    priority: "P0"
  - title: "Optionally run git apply --check"
    priority: "P0"
  - title: "Attach patch validation evidence"
    priority: "P0"
  - title: "Block invalid patch refs"
    priority: "P0"

depends_on:
  - "20260522-patch-producing-implementation-attempt-v1-codex-01"
source_artifacts:
  - docs/patch-aware-attempt-evaluation-research-v1.md
  - docs/patch-producing-attempts-research-v1.md
  - spec/contracts/attempt-evaluation.schema.yaml
---

## Objective

Make `evaluate-implementation-attempt` aware of patch-bearing attempts.

The evaluator should preserve and optionally verify `implementation_attempt.patch_ref` so invalid patch artifacts cannot reach promoted evaluations unnoticed.

## Research Basis

- `git apply --check` validates patch applicability without applying the patch.
- SWE-bench motivates patch-oriented repository-grounded evaluation.
- Agentless motivates simple repair/validate stage separation.
- CRITIC motivates tool-backed evaluation instead of self-approval.
- PROV-DM motivates retaining patch validation evidence as provenance.

## Scope

In scope:

- inspect `implementation_attempt.patch_ref`
- block missing patch files when `patch_ref` is non-empty
- add `--validate-patch-ref`
- run `git apply --check` only when requested
- write patch validation result artifact
- add patch validation artifact to `attempt_evaluation.evidence_refs`
- block failed patch checks

Out of scope:

- applying patches
- generating patches
- patch sandbox worktrees
- solution artifact policy changes
- autonomous retries

## CLI Contract Changes

Existing command:

- `bin/evaluate-implementation-attempt`

New argument:

- `--validate-patch-ref`

Default behavior:

- preserve patch refs but do not re-check patch applicability unless flag is passed

## Acceptance

- valid patch with `--validate-patch-ref` emits patch validation evidence
- invalid patch with `--validate-patch-ref` blocks
- missing patch file blocks
- no-patch attempt behavior remains unchanged
- command-backed validation still works with patch-aware evaluation

## Anti-Drift Rules

- evaluator does not apply patches
- evaluator does not mutate files
- patch validity is not equivalent to test success
- invalid patches cannot promote
- patch validation evidence must be explicit
