# Control Plane API

This document defines the composite terminal control-plane layer for local orchestration.

These commands are read-only projections over existing repo-owned command surfaces. They do not replace graph state, runtime checks, merge-back rules, or worker execution contracts.

## Contract Source

- canonical schema catalog: `spec/control-plane-api.schema.yaml`
- version: `control-plane.v1`

## Design Rules

- this layer must stay subordinate to the underlying graph, worker, local runtime, and merge-back commands
- it may summarize or prioritize existing command results, but it must not invent alternate authority or skip fail-closed blockers
- if a next step cannot be determined from bounded command outputs, the composite layer should return blockers rather than guess

## Commands

`get-control-plane-status`
- purpose: summarize current operator state for the terminal
- required output focus:
  - current branch and branch role
  - initiative branch
  - graph check summary
  - local runtime summary
  - worker session summary
  - branch-preparation summary for initiative branches
  - merge-back summaries for implementation branches
  - aggregate blockers

`get-next-orchestration-action`
- purpose: reduce current control-plane state to one bounded next step
- required output focus:
  - current branch and branch role
  - initiative branch
  - recommended action id
  - command reference
  - blockers that explain why the next step is not yet runnable

## Relationship to Existing Surfaces

- graph state remains authoritative through `bin/get-graph-state`
- runtime reachability remains authoritative through `bin/local-runtime-check`
- worker runtime remains authoritative through `bin/get-worker-status`
- implementation branch gating remains authoritative through `bin/prepare-next-impl-branch`
- merge-back remains authoritative through `bin/get-merge-readiness` and `bin/get-pr-integration-contract`

If the orchestrator still needs prose to know what to do next once these commands are present, the control-plane contract is incomplete and should be widened before more automation is added.
