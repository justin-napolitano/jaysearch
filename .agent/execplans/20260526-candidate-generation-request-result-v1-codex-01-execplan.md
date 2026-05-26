---
id: "20260526-candidate-generation-request-result-v1-codex-01"
title: "Candidate Generation Request/Result V1"
owner: "agent/codex"
created: "2026-05-26T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/candidate-generation-request-result-v1.md
  - artifacts/planner/research/candidate-generation-request-result-v1-dag.json
  - spec/contracts/candidate-generation-request.schema.yaml
  - spec/contracts/candidate-generation-result.schema.yaml
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/materialize_candidate_generation_request.py
  - bin/materialize-candidate-generation-request
  - src/platform_tools/generate_candidate_patch_manifest.py
  - bin/generate-candidate-patch-manifest
  - src/platform_tools/run_execution_era_loop_smoke.py
  - tests/test_candidate_generation_contracts.py
  - tests/test_materialize_candidate_generation_request.py
  - tests/test_generate_candidate_patch_manifest.py
  - tests/test_run_execution_era_loop_smoke.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "candidate-generation-contract-tests"
      command: "uv run pytest tests/test_candidate_generation_contracts.py"
      expected_exit: 0
    - name: "candidate-generation-runtime-tests"
      command: "uv run pytest tests/test_materialize_candidate_generation_request.py tests/test_generate_candidate_patch_manifest.py"
      expected_exit: 0
    - name: "execution-era-generation-regression"
      command: "uv run pytest tests/test_run_execution_era_loop_smoke.py tests/test_generate_implementation_attempt.py tests/test_evaluate_implementation_attempt.py tests/test_select_implementation_attempt.py tests/test_emit_solution_artifact.py tests/test_apply_solution_artifact.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Lock candidate generation request/result design"
    priority: "P0"
  - title: "Define request and result contracts"
    priority: "P0"
  - title: "Implement request materializer"
    priority: "P0"
  - title: "Implement conservative generation runner"
    priority: "P0"
  - title: "Bridge generated candidates into candidate_patch_manifest"
    priority: "P0"
  - title: "Wire execution ERA smoke runner"
    priority: "P0"
  - title: "Test invalid candidate preservation and non-mutating boundaries"
    priority: "P0"

depends_on:
  - "20260526-selected-dag-execution-units-v1-codex-01"
  - "20260525-candidate-patch-manifest-v1-codex-01"
  - "20260522-patch-aware-attempt-evaluation-v1-codex-01"
source_artifacts:
  - docs/candidate-generation-request-result-v1.md
  - artifacts/planner/research/candidate-generation-request-result-v1-dag.json
  - artifacts/planner/research/candidate-generation-request-result-v1-research-refresh.packet.json
  - docs/selected-dag-execution-units-v1.md
  - docs/candidate-patch-manifest-research-v1.md
  - docs/research-candidate-tree-search-v1.md
  - docs/patch-producing-attempts-research-v1.md
  - docs/patch-aware-attempt-evaluation-research-v1.md
  - docs/current-research-bibliography.md
---

## Objective

Add the first governed candidate-generation producer boundary before candidate patch manifest ingestion.

This turns a buildable `execution_unit` plus evidence refs and generation policy into a `candidate_generation_request`, a `candidate_generation_result`, and a `candidate_patch_manifest` that the existing ERA loop can evaluate and select from.

This slice now explicitly depends on selected DAG execution-unit materialization. Candidate generation consumes execution units, not planner DAG nodes.

## Scope

In scope:

- add `candidate_generation_request` and `candidate_generation_result` contracts
- add request materializer CLI
- add conservative generation runner CLI
- support `collect_existing_patch` as the first generation mode
- enforce owned-change boundaries by default
- record non-mutating patch applicability validation when requested
- optionally support fixture/template-backed patch generation for smoke tests
- preserve invalid generated candidates with blockers
- hand generated patch refs into `candidate_patch_manifest`
- wire the smoke runner to use the generated manifest

Out of scope:

- broad autonomous code mutation
- unbounded research during generation
- applying patches
- selecting winners inside candidate generation
- claiming execution-unit completion
- enabling LLM patch synthesis by default

## Research Basis

- AlphaEvolve supports generate/evaluate/select loops, but only when candidate generation is paired with evaluator feedback.
- SWE-bench supports patch-oriented repository tasks as the evaluation unit for software engineering.
- Agentless supports simple staged repair pipelines before complex autonomous agent loops.
- CRITIC supports tool-grounded critique instead of unsupported model self-correction.
- W3C PROV-DM supports explicit provenance between requests, generated entities, and selected outputs.
- Git `apply --check` supports non-mutating patch applicability validation.
- The selected DAG execution-unit materializer provides the upstream bridge from planning graphs to buildable work packets, so this producer should consume `execution_unit` refs.

## Implementation Plan

1. Define schemas for `candidate_generation_request` and `candidate_generation_result`.
2. Register both packet types in `spec/contracts/packet-schema-registry.yaml`.
3. Implement `materialize-candidate-generation-request` from an execution unit plus evidence refs and generation policy flags.
4. Implement `generate-candidate-patch-manifest` with `collect_existing_patch` first.
5. Enforce patch paths are inside `execution_unit.owned_changes` by default.
6. Reuse candidate patch manifest validation semantics instead of creating a second patch validation path.
7. Add smoke runner flags for request/result-backed candidate generation.
8. Add tests for contracts, materialization, generation result emission, invalid candidate preservation, and end-to-end smoke flow.
9. Run design iteration after implementation and preserve the generated evidence packet.

## Acceptance

- request packet preserves execution unit ref, evidence refs, owned changes, generation policy, and candidate budget
- result packet preserves every generation run, status, blocker, validation ref, and manifest ref
- generated manifest can drive existing implementation attempt generation
- invalid generated candidates remain visible and do not become attempts
- generation does not apply patches or mutate source files
- patch candidates are constrained to owned changes by default
- patch applicability checks are recorded as evidence but not treated as semantic validation
- smoke runner can execute the generation-backed ERA path
- design iteration reports no blockers

## Critical Risks

- If V1 tries to synthesize arbitrary code, it will drift into an unbounded agent before contracts are ready.
- If result packets hide failed candidate runs, selection will appear stronger than it is.
- If generated patches are not constrained by owned changes, the execution unit stops being a real safety boundary.
- If generation performs its own selection, it bypasses the ERA loop and weakens evaluation.

## Recommended Build Order

Build contracts first, then request materialization, then conservative generation, then smoke-runner integration.

Do not implement default-on LLM patch synthesis in this slice. Keep that as a later producer mode after prompt/provenance contracts exist.
