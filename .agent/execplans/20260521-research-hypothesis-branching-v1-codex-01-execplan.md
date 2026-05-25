---
id: "20260521-research-hypothesis-branching-v1-codex-01"
title: "Research Hypothesis Branching V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/research-hypothesis-branching-v1.md
  - docs/research-tool-v1.md
  - docs/core-contract-spec-v1.md
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/materialize_research_hypotheses.py
  - tests/test_materialize_research_hypotheses.py
  - artifacts/planner/research/research-hypothesis-branching-v1-dag.json
  - .agent/execplans/20260521-research-hypothesis-branching-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/research-hypothesis-branching-v1"
initiative_node_id: "initiative-research-hypothesis-branching-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "hypothesis-branching-runtime"
      command: "run focused pytest for hypothesis materialization and upstream handoff interoperability"
      expected_exit: 0
    - name: "real-hypothesis-example"
      command: "run hypothesis materialization on the canonical research problem example"
      expected_exit: 0

tasks:
  - title: "Define research_hypothesis_packet contract"
    priority: "P0"
  - title: "Add bounded hypothesis branching tool"
    priority: "P0"
  - title: "Emit canonical hypothesis example artifacts"
    priority: "P0"
  - title: "Verify interoperability with upstream research-problem materialization"
    priority: "P1"

depends_on:
  - "20260521-research-system-improvement-plan-v1-codex-01"
---

## Outcomes & Retrospective

This slice turns the first research-system improvement goal into a real runtime surface by materializing explicit hypothesis branches from a canonical research problem.

## Plan of Work

Phase 1 locks the contract and DAG. Phase 2 adds a bounded hypothesis materializer. Phase 3 verifies it on the canonical research problem artifacts.

## Validation and Acceptance

Acceptance means:

- `research_hypothesis_packet` exists in the shared contract layer
- one `research_problem_packet` can emit bounded hypothesis branches
- the runtime emits replayable branch artifacts
