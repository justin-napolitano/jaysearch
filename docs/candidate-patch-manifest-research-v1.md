# Candidate Patch Manifest Research V1

## Purpose

Design the first candidate-diversity boundary for the execution ERA loop.

The current loop can evaluate and select among multiple attempts, but V1 attempts are only meaningfully different when distinct patch artifacts are supplied. This slice defines a manifest that can carry multiple candidate patch refs into attempt generation.

## Current Workgraph

```text
execution_unit
  -> implementation_attempt[]
  -> attempt_evaluation[]
  -> attempt_selection
  -> solution_artifact
  -> applied_solution
```

## Target Workgraph

```text
execution_unit
  -> candidate_patch_manifest
  -> candidate_patch[]
  -> implementation_attempt[]
  -> attempt_evaluation[]
  -> attempt_selection
  -> solution_artifact
  -> applied_solution
```

## Sources

### AlphaEvolve

Source:

- https://arxiv.org/abs/2506.13131

Relevant claim:

- generate, evaluate, and select loops can improve candidate solutions.

Design implication:

- the platform needs a first-class candidate set before selection can become meaningful.

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Relevant claim:

- repository-grounded software work is evaluated through concrete code patches.

Design implication:

- candidate diversity should be represented as patch artifacts, not prose-only alternatives.

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- simple staged repair pipelines can be effective without broad autonomous control.

Design implication:

- V1 should ingest deterministic patch candidates before adding autonomous patch synthesis.

### CRITIC

Source:

- https://arxiv.org/abs/2305.11738

Relevant claim:

- tool-grounded critique is stronger than unsupported self-correction.

Design implication:

- candidate patches should be validated with `git apply --check` before becoming implementation attempts.

### W3C PROV-DM

Source:

- https://www.w3.org/TR/prov-dm/

Relevant claim:

- generated entities and derivations should preserve source relationships.

Design implication:

- the manifest should preserve candidate ids, patch refs, source labels, producer refs, and validation evidence refs.

## Design Decision

Build `candidate_patch_manifest_v1` as a deterministic multi-patch ingestion contract.

Do:

- accept multiple patch refs
- give each patch a stable candidate id
- record candidate family/source labels
- optionally validate every patch with `git apply --check`
- emit validation refs per candidate
- feed candidates into implementation attempt generation

Do not:

- synthesize patches
- apply patches
- mutate the source worktree
- use LLM rationale as validation evidence
- select winners inside the manifest stage

## Candidate Patch Manifest Packet

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `manifest_id`
- `source_execution_unit_ref`
- `candidate_patches`
- `validation_policy`
- `evidence_refs`
- `blockers`

Candidate patch item fields:

- `candidate_id`
- `patch_ref`
- `candidate_family`
- `source_label`
- `producer_ref`
- `expected_changed_artifact_refs`
- `validation_refs`
- `blockers`

## Tool Boundary

New tool:

- `materialize-candidate-patch-manifest`

Inputs:

- `--execution-unit-path`
- repeated `--patch-source-path`
- optional repeated `--candidate-family`
- optional `--validate-patches`

Output:

- `candidate-patch-manifest.packet.json`

## Attempt Generation Integration

`generate-implementation-attempt` should eventually accept:

- `--candidate-patch-manifest-path`

Behavior:

- one implementation attempt per candidate patch
- copy each candidate patch into the attempt run directory
- set `implementation_attempt.patch_ref`
- preserve candidate id/source labels in attempt metadata if contract allows

## Anti-Drift Rules

- manifest materialization does not select a winner
- manifest materialization does not apply patches
- invalid candidates stay visible with blockers
- patch validation is necessary but not sufficient
- candidate diversity must be artifact-backed
- autonomous patch synthesis is a later producer that emits the same manifest contract

## Recommendation

Build deterministic multi-patch ingestion first.

This lets the existing multi-attempt selector operate over genuinely different patch artifacts while preserving the same safety and provenance model. After that, add LLM/codegen patch producers as separate tools that output `candidate_patch_manifest` packets.
