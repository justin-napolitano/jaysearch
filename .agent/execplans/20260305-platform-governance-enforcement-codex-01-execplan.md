---
id: 20260305-platform-governance-enforcement-codex-01-execplan
title: Implement governance enforcement for required checks and exceptions
owner: "agent/codex-01"
created: "2026-03-05T00:00:00Z"
status: executing
base_branch: main
changes:
  - .agent/execplans/20260305-platform-governance-enforcement-codex-01-execplan.md
  - spec/governance.yaml
  - .agent/governance/exceptions.yaml
  - src/platform_tools/governance_check.py
  - src/platform_tools/repo_health.py
  - src/platform_tools/run_local_ci.py
  - bin/governance-check
  - policy/README.md
  - policy/agents.md
  - docs/commands.md
  - docs/governance.md
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/platform-program-execution-prep-codex-01-20260305"
draft_created: "2026-03-05T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: governance_check
      command: bin/governance-check
      expected_exit: 0
    - name: execplan_validate
      command: bin/execplan-validate .agent/execplans/*.md
      expected_exit: 0
    - name: repo_health_check
      command: bin/repo-health-check
      expected_exit: 0

tasks:
  - title: Enforce required-check contracts and naming stability
    priority: P1
  - title: Implement exception lifecycle contract with expiry and ownership
    priority: P1
  - title: Enforce bypass evidence and renewal requirements
    priority: P1

depends_on:
  - 20260305-platform-kernel-implementation-codex-01-execplan
---

# Purpose / Big Picture

Implement enforceable governance controls for required checks, bypasses, and exceptions.

## Progress

- [x] Create governance plan
- [x] Implement governance controls
- [x] Validate governance checks
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: required checks and exception lifecycle are one governance lane.

Rationale: avoids duplicated policy logic across plans.

Date/Author: 2026-03-05 / agent/codex-01

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

This plan merges previously overlapping governance and exception scopes into one executable lane.

## Plan of Work

1. Enforce required check controls.
2. Enforce exception lifecycle and bypass policy.

## Concrete Steps

1. Update `spec/*`, `policy/*`, and governance docs.
2. Run deterministic governance validators.

## Validation and Acceptance

Accepted when governance failures are deterministic and machine-detectable.

## Idempotence and Recovery

Governance checks are rerunnable and policy-state consistent.

## Artifacts and Notes

- `.agent/execplans/20260305-platform-governance-enforcement-codex-01-execplan.md`
- `spec/governance.yaml`
- `.agent/governance/exceptions.yaml`
- `src/platform_tools/governance_check.py`
- `bin/governance-check`

## Interfaces and Dependencies

Interfaces:

- `spec/governance.yaml`
- `.agent/governance/exceptions.yaml`
- `src/platform_tools/governance_check.py`
- `bin/governance-check`
- `policy/*`
- `docs/governance.md`

Dependencies:

- `20260305-platform-kernel-implementation-codex-01-execplan`
