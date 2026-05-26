# Candidate Generation Request/Result V1

## Objective

Define the first safe autonomous-candidate boundary for the execution ERA loop.

This slice turns:

```text
execution_unit + evidence refs + generation policy
```

into:

```text
candidate_generation_request
  -> candidate_generation_result
  -> candidate_patch_manifest
```

The goal is not broad autonomous repo mutation. The goal is a governed producer that can create or collect multiple candidate patch artifacts and hand them to the existing manifest/evaluation/selection loop.

## Research Basis

Canonical local sources:

- `docs/execution-era-loop-v1.md`
- `docs/candidate-patch-manifest-research-v1.md`
- `docs/patch-producing-attempts-research-v1.md`
- `docs/patch-aware-attempt-evaluation-research-v1.md`
- `docs/research-candidate-tree-search-v1.md`
- `docs/current-research-bibliography.md`

External sources checked for this slice:

- AlphaEvolve: https://arxiv.org/abs/2506.13131
- SWE-bench: https://arxiv.org/abs/2310.06770
- Agentless: https://arxiv.org/abs/2407.01489
- CRITIC: https://arxiv.org/abs/2305.11738
- W3C PROV-DM: https://www.w3.org/TR/prov-dm/
- Git apply: https://git-scm.com/docs/git-apply

Design implications:

- AlphaEvolve supports generate/evaluate/select loops, but the selection value depends on candidate diversity and executable feedback.
- SWE-bench supports representing software work as concrete repository tasks and patches rather than prose-only answers.
- Agentless supports staged, bounded repair flows before complex autonomous agents.
- CRITIC supports tool-grounded critique over unsupported self-correction.
- PROV-DM supports preserving derivation between requests, producers, generated artifacts, and downstream selections.
- `git apply --check` supports validating patch applicability without mutating the worktree.

## Core Boundary

The candidate generation tool is a producer, not an evaluator or applier.

It may:

- read an `execution_unit`
- read evidence and research refs
- read generation instructions
- create or collect candidate patch artifacts
- validate patch applicability when requested
- emit `candidate_generation_result`
- emit or reference `candidate_patch_manifest`

It must not:

- apply patches to the source worktree
- select the winning candidate
- claim completion
- hide failed candidate generation attempts
- mutate files outside an isolated output directory
- treat model rationale as validation evidence

## Candidate Generation Request Packet

Purpose:

- machine-readable request to generate candidate patches for one execution unit

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `request_id`
- `source_execution_unit_ref`
- `generation_goal`
- `candidate_budget`
- `candidate_families`
- `evidence_refs`
- `allowed_artifact_refs`
- `owned_change_refs`
- `validation_policy`
- `generation_policy`
- `non_goals`
- `blockers`

`candidate_budget` should include:

- `max_candidates`
- `max_candidate_families`
- `timeout_seconds`

`candidate_families` should initially allow:

- `baseline_minimal`
- `contract_first`
- `runtime_first`
- `test_first`
- `novel_synthesized`

`generation_policy` should include:

- `mode`: `collect_existing_patch`, `template_patch`, or `llm_patch_proposal`
- `requires_patch_artifact`: boolean
- `requires_patch_validation`: boolean
- `allow_unvalidated_candidates`: boolean
- `preserve_invalid_candidates`: boolean

## Candidate Generation Result Packet

Purpose:

- record what candidate generation produced, failed to produce, and handed off

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `result_id`
- `source_request_ref`
- `source_execution_unit_ref`
- `candidate_generation_runs`
- `candidate_patch_manifest_ref`
- `generated_artifact_refs`
- `validation_refs`
- `blockers`
- `follow_up_question_refs`

Each `candidate_generation_run` should include:

- `run_id`
- `candidate_family`
- `producer_ref`
- `prompt_or_instruction_ref`
- `patch_ref`
- `status`
- `validation_refs`
- `blockers`
- `evidence_refs`

Allowed statuses:

- `generated`
- `collected`
- `validation_failed`
- `blocked`
- `deferred`

## V1 Implementation Strategy

V1 should be intentionally conservative:

1. Materialize a `candidate_generation_request` from an execution unit plus optional evidence refs.
2. Support `collect_existing_patch` mode first.
3. Optionally support `template_patch` for trivial fixture-backed smoke tests.
4. Emit `candidate_generation_result`.
5. Reuse `materialize-candidate-patch-manifest` semantics for the final candidate set.
6. Wire the smoke runner so it can consume a generation result or its manifest ref.

This gives the system a real producer boundary without pretending autonomous synthesis is solved.

## Design Questions For Implementation

- Should `candidate_generation_result` embed a candidate patch manifest or only reference it?
- Should `llm_patch_proposal` be blocked until prompt/provenance contracts exist?
- Should generated patches be required to touch only `execution_unit.owned_changes` in V1?
- Should candidate generation call research tools directly or consume evidence packets prepared before execution?

Recommended V1 answers:

- Reference the manifest rather than embed it.
- Keep `llm_patch_proposal` contract-defined but disabled by default.
- Require generated patches to stay within owned changes.
- Consume evidence refs; do not perform open-ended research during generation.

## Acceptance

V1 is acceptable when:

- request/result contracts exist and are registered
- request materialization preserves execution unit, evidence refs, owned changes, and generation limits
- result materialization preserves every generation run and blocker
- generated or collected patch refs can feed `candidate_patch_manifest`
- invalid generated candidates remain visible
- smoke runner can run request/result-backed candidate generation through selection
- design iteration reports no blockers

## Anti-Drift Rules

- candidate generation is not selection
- candidate generation is not application
- candidate generation is not completion
- evidence refs must be explicit
- every patch candidate must be artifact-backed
- failed generation attempts remain inspectable
- tool output must preserve provenance from request to manifest to attempts
