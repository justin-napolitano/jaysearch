---
id: "20260526-jaysearch-runtime-ci-v1-codex-01"
title: "Jaysearch Runtime CI V1"
owner: "agent/codex"
created: "2026-05-26T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/jaysearch-runtime-ci-v1.md
  - artifacts/planner/research/jaysearch-runtime-ci-v1-dag.json
  - src/platform_tools/run_jaysearch_ci.py
  - bin/run-jaysearch-ci
  - pyproject.toml
  - .github/workflows/jaysearch-ci.yml
  - tests/test_run_jaysearch_ci.py
  - README.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "jaysearch-ci"
      command: "bin/run-jaysearch-ci"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Document Jaysearch runtime validation boundary"
    priority: "P0"
  - title: "Implement run-jaysearch-ci"
    priority: "P0"
  - title: "Wire GitHub Actions to Jaysearch CI"
    priority: "P0"
  - title: "Update README validation instructions"
    priority: "P0"
  - title: "Preserve legacy platform CI as explicit non-default gate"
    priority: "P0"

depends_on:
  - "20260526-candidate-generation-request-result-v1-codex-01"
source_artifacts:
  - docs/jaysearch-runtime-ci-v1.md
  - artifacts/planner/research/jaysearch-runtime-ci-v1-dag.json
  - docs/execution-era-loop-v1.md
  - docs/candidate-patch-manifest-research-v1.md
  - docs/candidate-generation-request-result-v1.md
  - docs/design-iteration-tool-v1.md
---

## Objective

Create a Jaysearch-specific runtime validation gate before building more tools.

The inherited platform-template test suite is too broad for Jaysearch readiness. It includes control-plane, worker lease, branch rewrite, and project-management behaviors that should not block core Jaysearch tool development.

## Scope

In scope:

- define the Jaysearch CI boundary
- add `bin/run-jaysearch-ci`
- emit machine-readable CI results
- wire a GitHub Actions workflow for pushes and pull requests
- document that `run-local-ci` remains legacy platform CI

Out of scope:

- deleting legacy platform tests
- fixing legacy platform fixture drift
- making full `uv run pytest` mandatory for Jaysearch PRs
- changing core ERA tool behavior

## Acceptance

- `bin/run-jaysearch-ci` passes
- `bin/design-iteration --root .` passes
- README points contributors at Jaysearch CI
- legacy platform CI remains available but is not the default Jaysearch gate
