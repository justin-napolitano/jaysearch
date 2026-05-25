# Patch Producing Attempts Research V1

## Purpose

Design the first safe version of patch-producing `implementation_attempt` packets.

This is the boundary where the system can begin producing code-change artifacts. V1 must generate patch files only and must not apply them automatically.

## Sources

### Git Apply

Source:

- https://git-scm.com/docs/git-apply

Relevant claim:

- `git apply --check` can verify whether a patch applies to the working tree without applying it.

Design implication:

- V1 should validate generated patch artifacts with `git apply --check` before allowing evaluation or solution emission to rely on them.

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Relevant claim:

- real software-engineering evaluation is patch-oriented and repository-grounded.

Design implication:

- `implementation_attempt.patch_ref` should become a real unified diff artifact, not just an empty placeholder.

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- a simple pipeline of localization, repair, and validation can be competitive without a complex autonomous agent.

Design implication:

- V1 should start with deterministic patch artifact generation and patch validation, not broad autonomous code mutation.

### SWE-agent / OpenHands

Sources:

- https://arxiv.org/abs/2405.15793
- https://arxiv.org/abs/2407.16741

Relevant claim:

- practical software agents need explicit tool surfaces and controlled runtime interactions.

Design implication:

- patch production should be an explicit tool mode with bounded inputs, owned-change checks, and recorded output artifacts.

## Design Decision

Build `patch-producing-implementation-attempt-v1` as a patch artifact generator.

Do:

- generate unified diff patch files
- write patch metadata
- run `git apply --check`
- store patch validation evidence
- update `implementation_attempt.patch_ref`

Do not:

- apply the patch
- mutate source files
- run arbitrary repair loops
- select solution artifacts

## V1 Patch Source

V1 should support a deterministic patch input rather than LLM patch synthesis.

Inputs:

- `--patch-source-path`

The generator copies or normalizes the supplied patch artifact into the attempt run directory, validates it with `git apply --check`, and records the result.

This lets us test the entire patch-bearing flow before adding generated patch synthesis.

## Required Runtime Changes

Update:

- `src/platform_tools/generate_implementation_attempt.py`

Add args:

- `--patch-source-path`
- `--validate-patch`

Behavior:

- if `--patch-source-path` is supplied, copy it into the run directory as `attempt-XX.patch`
- set `patch_ref`
- run `git apply --check attempt-XX.patch` when `--validate-patch` is true
- emit `patch_validation_ref`
- block if validation fails

## Required Tests

- supplied valid patch produces attempt with non-empty `patch_ref`
- patch validation evidence is emitted
- invalid patch blocks
- missing patch source blocks when patch source path is provided but absent
- default no-patch mode still works

## Critical Risks

- generated patches could target files outside `owned_changes`
- patch validation could accidentally apply changes if wrong git command is used
- path traversal through patch headers
- false confidence from patch-apply success without tests

## Anti-Drift Rules

- patch generation does not apply patches
- patch validation uses `git apply --check`
- successful patch validation is not equivalent to passing tests
- solution artifact still requires promoted attempt evaluation

## Recommendation

Build deterministic patch artifact support first. Once the graph can carry real patches safely, add LLM or tool-generated patch synthesis as a later, separate slice.
