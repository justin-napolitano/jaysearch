---
id: "20260310-citation-inference-validator-codex-01-execplan"
title: "Implement citation and inference validation for governed artifacts"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-citation-inference-validator-codex-01-execplan.md
  - artifacts/planner/research/bibliography-graph.json
  - artifacts/planner/research/claim-registry.json
  - bin/citation-check
  - bin/citation-smoke-test
  - docs/research-assumptions.md
  - pyproject.toml
  - spec/claim-registry.schema.yaml
  - src/platform_tools/citation_check.py
  - tests/test_citation_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-citation-inference-validator-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-citation-inference-validator-codex-01-execplan.md"
      expected_exit: 0
    - name: "citation-pytest"
      command: "uv run pytest tests/test_citation_check.py"
      expected_exit: 0
    - name: "citation-check"
      command: "bin/citation-check"
      expected_exit: 0
    - name: "citation-smoke-test"
      command: "bin/citation-smoke-test"
      expected_exit: 0

tasks:
  - title: "Define machine-readable claim registry for governed artifacts"
    priority: "P1"
  - title: "Implement citation and inference validator"
    priority: "P1"
  - title: "Link governed docs to bibliography graph and claim registry"
    priority: "P1"
  - title: "Add focused tests for citation enforcement"
    priority: "P1"

depends_on:
  - "20260310-planner-control-plane-design-codex-01-execplan"
---

# Purpose / Big Picture

Implement a deterministic validator that checks whether governed design and implementation artifacts classify major claims as source-backed, design-inference, policy-choice, or open-assumption, and whether those claims resolve to machine-readable bibliography graph references where required.

This slice strengthens the research-governance layer so future implementation work cannot quietly drift back into unsupported design claims.

## Progress

- [ ] Add claim registry schema and artifact
- [ ] Implement citation validator
- [ ] Update bibliography graph and assumptions guidance
- [ ] Add focused tests
- [ ] Run targeted validation

## Surprises & Discoveries

- Existing docs define the requirement conceptually but do not yet expose a deterministic claim-level registry.
- The validator should enforce structure without pretending to semantically understand prose.

## Decision Log

- 2026-03-10 / agent-codex-01 / Claim enforcement will be registry-based rather than NLP-based.
- 2026-03-10 / agent-codex-01 / Source-backed and design-inference claims must resolve to bibliography graph nodes.

## Outcomes & Retrospective

Expected outcomes:

- machine-readable claim registry
- deterministic citation validator and CLI
- graph-linked coverage for core governed docs
- one-command smoke test for pre-merge validation
- focused passing tests

## Context and Orientation

The design package already requires citation-or-inference labeling, bibliography graph coverage, and explicit separation of source-backed versus inferred claims. This plan turns those requirements into an executable validator.

## Plan of Work

1. Define a claim registry schema and artifact format.
2. Implement a validator that checks artifact coverage, claim categories, and graph references.
3. Update the bibliography graph and assumptions guidance to support the validator.
4. Add focused tests and run validation.

## Concrete Steps

1. Add `spec/claim-registry.schema.yaml`.
2. Add `artifacts/planner/research/claim-registry.json`.
3. Implement `src/platform_tools/citation_check.py`.
4. Add `bin/citation-check` and register it in `pyproject.toml`.
5. Add `bin/citation-smoke-test` for one-command pre-merge validation.
6. Add focused tests in `tests/test_citation_check.py`.
7. Run `bin/execplan-validate`, `bin/citation-check`, `bin/citation-smoke-test`, and `uv run pytest tests/test_citation_check.py`.

## Validation and Acceptance

Acceptance criteria:

- validator fails when governed artifacts are missing from the registry
- validator fails when source-backed or design-inference claims point to unknown graph nodes
- validator passes on the in-repo registry and bibliography graph
- focused tests pass

## Idempotence and Recovery

- validation is read-only
- registry and graph edits should be deterministic and reviewable
- if claim coverage changes, registry and graph updates must happen in the same change set

## Artifacts and Notes

- `artifacts/planner/research/claim-registry.json`
- `spec/claim-registry.schema.yaml`
- `src/platform_tools/citation_check.py`
- `tests/test_citation_check.py`

## Interfaces and Dependencies

- `docs/research-assumptions.md`
- `docs/references.md`
- `artifacts/planner/research/bibliography-graph.json`
- `spec/bibliography-graph.schema.yaml`
