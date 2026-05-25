---
id: "20260522-patch-producing-implementation-attempt-v1-codex-01"
title: "Patch Producing Implementation Attempt V1"
owner: "agent/codex"
created: "2026-05-22T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/generate_implementation_attempt.py
  - tests/test_generate_implementation_attempt.py
  - docs/patch-producing-attempts-research-v1.md
  - docs/execution-era-runtime-research-v1.md
  - artifacts/planner/research/patch-producing-implementation-attempt-v1-dag.json
  - .agent/execplans/20260522-patch-producing-implementation-attempt-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/patch-producing-implementation-attempt-v1"
initiative_node_id: "initiative-patch-producing-implementation-attempt-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "patch-producing-attempt-tests"
      command: "uv run pytest tests/test_generate_implementation_attempt.py tests/test_run_execution_era_loop_smoke.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Accept patch source path"
    priority: "P0"
  - title: "Copy patch artifact into attempt run"
    priority: "P0"
  - title: "Validate patch with git apply --check"
    priority: "P0"
  - title: "Populate patch_ref and validation evidence"
    priority: "P0"
  - title: "Block invalid patches without applying them"
    priority: "P0"

depends_on:
  - "20260521-attempt-evaluation-command-execution-v1-codex-01"
source_artifacts:
  - docs/patch-producing-attempts-research-v1.md
  - spec/contracts/implementation-attempt.schema.yaml
---

## Objective

Add deterministic patch artifact support to `generate-implementation-attempt`.

This is the first step toward implementation attempts that carry real code-change artifacts.

## Research Basis

- `git apply --check` validates patches without applying them.
- SWE-bench motivates patch-oriented repository-grounded evaluation.
- Agentless motivates simple patch/validate stages before broad autonomy.
- SWE-agent and OpenHands motivate explicit tool surfaces and recorded artifacts.

## Scope

In scope:

- optional `--patch-source-path`
- optional `--validate-patch`
- copy supplied patch into attempt run directory
- set `implementation_attempt.patch_ref`
- run `git apply --check` when requested
- write patch validation artifact
- block invalid patches

Out of scope:

- applying patches
- generating patches from LLM prompts
- autonomous code editing
- test execution
- solution emission

## Acceptance

- default no-patch attempt generation still works
- valid supplied patch emits non-empty `patch_ref`
- patch validation artifact records `git apply --check` result
- invalid supplied patch blocks and does not emit promoted attempt
- missing patch source path blocks

## Anti-Drift Rules

- generator does not mutate source files
- generator only copies supplied patch artifacts
- patch validation uses `git apply --check`
- patch validation does not replace command-backed test evaluation
