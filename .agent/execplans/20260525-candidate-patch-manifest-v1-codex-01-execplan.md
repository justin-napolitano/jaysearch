---
id: "20260525-candidate-patch-manifest-v1-codex-01"
title: "Candidate Patch Manifest V1"
owner: "agent/codex"
created: "2026-05-25T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/candidate-patch-manifest-research-v1.md
  - artifacts/planner/research/candidate-patch-manifest-v1-dag.json
  - spec/contracts/candidate-patch-manifest.schema.yaml
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/materialize_candidate_patch_manifest.py
  - bin/materialize-candidate-patch-manifest
  - src/platform_tools/generate_implementation_attempt.py
  - src/platform_tools/run_execution_era_loop_smoke.py
  - tests/test_candidate_patch_manifest_contracts.py
  - tests/test_materialize_candidate_patch_manifest.py
  - tests/test_generate_implementation_attempt.py
  - tests/test_run_execution_era_loop_smoke.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "candidate-patch-manifest-tests"
      command: "uv run pytest tests/test_candidate_patch_manifest_contracts.py tests/test_materialize_candidate_patch_manifest.py"
      expected_exit: 0
    - name: "execution-era-regression"
      command: "uv run pytest tests/test_select_implementation_attempt.py tests/test_attempt_selection_contracts.py tests/test_apply_solution_artifact.py tests/test_applied_solution_contracts.py tests/test_run_execution_era_loop_smoke.py tests/test_generate_implementation_attempt.py tests/test_evaluate_implementation_attempt.py tests/test_emit_solution_artifact.py tests/test_execution_era_contracts.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Research deterministic candidate patch manifests"
    priority: "P0"
  - title: "Define candidate_patch_manifest contract"
    priority: "P0"
  - title: "Implement manifest materializer"
    priority: "P0"
  - title: "Integrate manifest with attempt generation"
    priority: "P0"
  - title: "Wire smoke runner manifest path"
    priority: "P0"
  - title: "Test candidate diversity path"
    priority: "P0"

depends_on:
  - "20260522-execution-era-multi-attempt-selection-v1-codex-01"
source_artifacts:
  - docs/candidate-patch-manifest-research-v1.md
  - artifacts/planner/research/candidate-patch-manifest-v1-dag.json
  - docs/execution-era-multi-attempt-selection-research-v1.md
  - docs/patch-producing-attempts-research-v1.md
---

## Objective

Add deterministic multi-patch candidate ingestion before implementation attempt generation.

This gives the existing multi-attempt selector genuinely different patch artifacts to evaluate without introducing autonomous patch synthesis yet.

## Scope

In scope:

- add `candidate_patch_manifest` contract
- add manifest materializer CLI
- support repeated patch source paths
- validate candidate patches with `git apply --check`
- preserve invalid candidate blockers
- generate implementation attempts from a manifest
- allow the execution ERA smoke runner to consume a manifest

Out of scope:

- LLM patch synthesis
- current-worktree mutation
- candidate selection inside the manifest stage
- autonomous repair loops

## Acceptance

- manifest packet preserves every candidate patch
- valid patch candidates carry validation refs
- invalid candidates remain visible with blockers
- manifest-backed attempt generation emits one attempt per unblocked candidate
- smoke runner can run manifest-backed multi-attempt selection
- existing single-patch path remains compatible
- design iteration reports no blockers
