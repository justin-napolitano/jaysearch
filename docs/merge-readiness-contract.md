# Merge Readiness Contract

## Objective

Merge readiness must be machine-checkable. Codex must be able to determine whether a branch is ready to merge without relying on informal review memory.

## Required Conditions

A branch is merge-ready only if all of the following are true:

- the active ExecPlan validations pass
- the active ExecPlan is authoritative for the branch context:
  - initiative branch for in-flight initiative integration
  - implementation branch inheriting authority from its parent initiative branch
- the slice-specific smoke test passes
- required focused tests pass
- generated smoke artifacts are intentionally committed, removed, or stashed
- rule-graph validation passes
- citation or inference validation passes when the slice touches governed research or design artifacts
- commit-size rules have not been violated without documented ExecPlan justification
- no unresolved blockers remain on the active canonical graph for the scoped work
- no required human-only approval step has been bypassed

## Merge-Readiness Report

A later machine-readable merge-readiness report should include at least:

- branch name
- active ExecPlan id
- overall readiness status
- failing checks
- unresolved blockers
- dirty artifact status
- required human approvals
- recommended next action

## Blocking Categories

Merge readiness may be blocked by:

- validation failure
- smoke-test failure
- artifact hygiene failure
- rule-graph failure
- citation or provenance failure
- scope drift against the active ExecPlan
- authority boundary requiring human action

## Artifact Hygiene

Generated artifacts from smoke or validation runs must not be ignored at merge time. They must be:

- intentionally committed because they are part of the slice output
- removed because they are disposable
- stashed because they are temporary verification output

A dirty branch containing disposable generated artifacts is not merge-ready.

## Human Authority

Codex may prepare merge-readiness evidence but may not replace:

- human review
- human exception approval
- human historical approval and completion events on `main`

During an active initiative, merge readiness for implementation or initiative merge-back does not require that partial planning updates have already been merged to `main`. It does require that the initiative branch exposes one authoritative active ExecPlan and that the branch context and plan authority are unambiguous.

For `impl-execplan/*` branches, merge readiness should be evaluated for PR merge-back into the parent `initiative/*` branch. Local cherry-pick into the initiative branch is not the default governed merge path and should be treated as exception-only recovery or human-directed action.

## Design Consequence

This contract implies a later merge-readiness engine that aggregates validator results, artifact hygiene checks, and authority requirements into one machine-readable output.

## Research Framing

This contract is a design inference informed by provenance, transition legality, and inspection discipline rather than a direct restatement of any single source.
