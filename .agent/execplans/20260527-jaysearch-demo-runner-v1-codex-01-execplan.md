---
id: "20260527-jaysearch-demo-runner-v1-codex-01"
title: "Jaysearch Demo Runner V1"
owner: "agent/codex"
created: "2026-05-27T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/jaysearch-demo-runner-v1.md
  - artifacts/planner/research/jaysearch-demo-runner-v1-dag.json
  - src/platform_tools/run_jaysearch_demo.py
  - bin/run-jaysearch-demo
  - src/platform_tools/run_jaysearch_ci.py
  - tests/test_run_jaysearch_demo.py
  - tests/test_run_jaysearch_ci.py
  - README.md
  - docs/index.html
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "demo-runner-tests"
      command: "uv run pytest tests/test_run_jaysearch_demo.py tests/test_run_jaysearch_ci.py"
      expected_exit: 0
    - name: "jaysearch-ci"
      command: "bin/run-jaysearch-ci"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define demo scope and non-claims"
    priority: "P0"
  - title: "Implement fixture-backed demo runner"
    priority: "P0"
  - title: "Emit demo report and summary"
    priority: "P0"
  - title: "Document demo command"
    priority: "P0"
  - title: "Wire demo tests into Jaysearch CI"
    priority: "P0"

depends_on:
  - "20260526-candidate-dag-selection-v1-codex-01"
  - "20260526-selected-dag-execution-units-v1-codex-01"
  - "20260521-execution-era-loop-smoke-v1-codex-01"
source_artifacts:
  - docs/jaysearch-demo-runner-v1.md
  - artifacts/planner/research/jaysearch-demo-runner-v1-dag.json
  - docs/candidate-dag-selection-v1.md
  - docs/selected-dag-execution-units-v1.md
  - docs/execution-era-loop-v1.md
---

## Objective

Create the fastest credible Jaysearch demo path for an interview.

The demo should show real working tools, not slides only: candidate DAG selection, selected DAG materialization into execution units, and the existing ERA packet loop.

## Scope

In scope:

- fixture-backed candidate DAGs
- real `select_candidate_dag`
- real `materialize_selected_dag_execution_units`
- one metadata-only `run_execution_era_loop_smoke`
- `demo-report.json`
- `demo-summary.md`
- README and site instructions

Out of scope:

- autonomous candidate generation
- patch application
- production artifact retention
- hosted CI permission repair

## Acceptance

- `bin/run-jaysearch-demo --root .` works locally
- targeted tests pass
- Jaysearch CI passes locally
- design iteration reports no blockers
