# Merge-Back Orchestration API

This document defines the planned machine-readable API contract for implementation-slice merge-back into an initiative branch.

It does not claim that the commands already exist. It defines the contract a later implementation slice should satisfy so a thin orchestrator can determine:

- whether an `impl-execplan/*` branch is ready to merge back
- which `initiative/*` branch is the lawful target
- which validations and human actions are still required
- whether the next implementation slice may lawfully be cut from the current initiative head

## Contract Source

- canonical schema catalog: `spec/mergeback-orchestration-api.schema.yaml`
- version: `mergeback-orchestration.v1`

## Design Rules

- this surface is subordinate to `spec/workflow.yaml`, `spec/governance.yaml`, and `docs/merge-readiness-contract.md`
- it projects readiness and target resolution; it does not invent alternate branch or approval semantics
- if lawful initiative mapping or branch-role resolution is ambiguous, the surface must fail closed
- bounded blocker, next-action, and problem vocabularies are required

If a later orchestrator needs prose to decide where an implementation PR should go or whether the slice is merge-ready, the contract surface is incomplete and should be widened before automation proceeds.

## Planned Commands

`get-merge-readiness`
- purpose: project whether a source implementation branch is ready to merge into its lawful initiative target
- required output focus:
  - source branch
  - target branch
  - readiness checks
  - blockers
  - next validations
  - next action

`get-pr-integration-contract`
- purpose: resolve the lawful initiative merge-back target and the required integration contract for the PR
- required output focus:
  - source branch
  - target branch
  - integration mode
  - required validations
  - required human actions
  - blockers
  - next action

`prepare-next-impl-branch`
- purpose: fail closed unless the current initiative branch is current and older implementation slices for that initiative are already merged back
- required output focus:
  - initiative branch
  - selected execplan or node
  - suggested implementation branch
  - blockers
  - prior unmerged implementation slices
  - next action

## Relationship to Existing Surfaces

- `bin/merge-readiness-check` remains the underlying readiness authority
- workflow branch-role and initiative-authority rules remain the target-resolution authority
- initiative-head ancestry and prior-slice merge completion should be projected through this same API family rather than left to prose or operator memory
- this planned API should eventually align stylistically with `docs/public-orchestration-api.md` without pretending the commands are already live in that facade
