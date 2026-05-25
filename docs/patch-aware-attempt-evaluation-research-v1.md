# Patch Aware Attempt Evaluation Research V1

## Purpose

Design patch-aware `attempt_evaluation` behavior.

The current generator can attach a patch artifact to `implementation_attempt.patch_ref` and optionally validate that patch with `git apply --check`.

The evaluator should also understand patch-bearing attempts so invalid or unverified patch artifacts cannot flow into solution artifacts unnoticed.

## Sources

### Git Apply

Source:

- https://git-scm.com/docs/git-apply

Relevant claim:

- `git apply --check` checks whether a patch applies without applying it.

Design implication:

- evaluator can safely re-check a patch artifact without mutating source files.

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Relevant claim:

- software-engineering benchmark tasks are repository-grounded and patch-oriented.

Design implication:

- attempt evaluation should treat `patch_ref` as a first-class evidence-bearing artifact, not an optional note.

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- simple repair and patch validation stages can be useful without complex autonomous tool loops.

Design implication:

- patch-aware evaluation should be a bounded verifier stage, not a repair loop.

### CRITIC

Source:

- https://arxiv.org/abs/2305.11738

Relevant claim:

- tool-interactive critique is stronger than unsupported self-correction.

Design implication:

- patch acceptance should rely on tool output such as `git apply --check`, not model belief.

### W3C PROV-DM

Source:

- https://www.w3.org/TR/prov-dm/

Relevant claim:

- generated entities and derivations should preserve provenance.

Design implication:

- patch validation evidence should be linked into the evaluation and later solution artifact.

## Design Decision

Add `patch_ref` handling to `evaluate-implementation-attempt`.

When an attempt has `patch_ref`, evaluator should:

- verify the patch file exists
- optionally run `git apply --check`
- record patch validation output artifact
- include patch validation artifact in `attempt_evaluation.evidence_refs`
- block on invalid patch before command-backed validation can promote the attempt

Patch validity is necessary but not sufficient.

Passing `git apply --check` only proves the patch can apply. It does not prove the patch is correct.

## Proposed Runtime Additions

Update:

- `src/platform_tools/evaluate_implementation_attempt.py`

New args:

- `--validate-patch-ref`

Behavior:

- default: if `patch_ref` exists, preserve it but do not re-check unless flag is provided
- if `--validate-patch-ref` is provided and `patch_ref` is non-empty, run `git apply --check`
- if `patch_ref` is non-empty but missing from disk, block
- if patch check fails, block
- if patch check passes, add patch validation artifact ref to evaluation evidence refs

## Required Tests

- patch-bearing attempt with valid patch and `--validate-patch-ref` promotes when commands/evidence pass
- patch-bearing attempt with invalid patch blocks
- patch-bearing attempt with missing patch file blocks
- no-patch attempt behavior remains unchanged
- patch validation evidence appears in `attempt_evaluation.evidence_refs`

## Anti-Drift Rules

- evaluator does not apply patches
- evaluator does not modify files
- patch validity does not replace test validation
- invalid patch blocks promotion
- solution artifacts must not rely on patch refs that were never checked or explicitly accepted as unchecked

## Recommendation

Build `patch-aware-attempt-evaluation-v1` before patch application or patch synthesis.

This closes the current gap between patch-producing attempts and solution artifacts while preserving the non-mutating execution boundary.
