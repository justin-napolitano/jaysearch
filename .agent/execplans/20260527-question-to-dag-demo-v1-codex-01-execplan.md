---
id: "20260527-question-to-dag-demo-v1-codex-01"
title: "Question To DAG Demo V1"
owner: "agent/codex"
created: "2026-05-27T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/question-to-dag-demo-v1.md
  - artifacts/planner/research/question-to-dag-demo-v1-dag.json
  - artifacts/planner/research/question-to-dag-demo-v1-research-refresh.packet.json
  - src/platform_tools/run_jaysearch_question_dag_demo.py
  - bin/run-jaysearch-question-dag-demo
  - src/platform_tools/run_jaysearch_ci.py
  - tests/test_run_jaysearch_question_dag_demo.py
  - tests/test_run_jaysearch_ci.py
  - README.md
  - docs/index.html
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "question-dag-demo-tests"
      command: "uv run pytest tests/test_run_jaysearch_question_dag_demo.py tests/test_run_jaysearch_ci.py"
      expected_exit: 0
    - name: "jaysearch-ci"
      command: "bin/run-jaysearch-ci"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define question-to-DAG demo boundary"
    priority: "P0"
  - title: "Implement deterministic question-to-DAG CLI"
    priority: "P0"
  - title: "Emit local HTML run view"
    priority: "P0"
  - title: "Wire tests into Jaysearch CI"
    priority: "P0"

depends_on:
  - "20260527-jaysearch-demo-runner-v1-codex-01"
  - "20260526-candidate-dag-selection-v1-codex-01"
  - "20260526-selected-dag-execution-units-v1-codex-01"
source_artifacts:
  - docs/question-to-dag-demo-v1.md
  - artifacts/planner/research/question-to-dag-demo-v1-dag.json
  - artifacts/planner/research/question-to-dag-demo-v1-research-refresh.packet.json
  - docs/question-tool-v1.md
  - docs/research-tool-v1.md
  - docs/candidate-dag-selection-v1.md
  - docs/selected-dag-execution-units-v1.md
---

## Objective

Create the interview demo path from user question to researched DAG and execution-unit boundary.

## Scope

Slice 1:

- CLI accepts a question
- emits question packet, bounded evidence packet, candidate DAG manifest, selected DAG packet, execution-unit manifest, execution units, summary

Slice 2:

- emits a local `demo.html` presentation view over the same artifacts
- updates README and Pages with the demo story

Out of scope:

- live autonomous web research
- autonomous code generation
- patch application
- production orchestration retries

## Acceptance

- demo flow preserves lineage refs across all major packets
- report clearly states implementation/development automation is in progress
- tests and local Jaysearch CI pass
