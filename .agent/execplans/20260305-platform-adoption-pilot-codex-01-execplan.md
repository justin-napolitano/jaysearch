---
id: 20260305-platform-adoption-pilot-codex-01-execplan
title: Execute controlled platform adoption pilot and rollout decision gate
owner: "agent/codex-01"
created: "2026-03-05T00:00:00Z"
status: executing
base_branch: main
changes:
  - .agent/execplans/20260305-platform-adoption-pilot-codex-01-execplan.md
  - docs/getting-started.md
  - docs/platform-overview.md
  - docs/commands.md
  - spec/adoption.yaml
  - .agent/adoption/pilot-status.yaml
  - src/platform_tools/adoption_check.py
  - src/platform_tools/repo_health.py
  - src/platform_tools/run_local_ci.py
  - bin/adoption-check
  - policy/README.md
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
    - name: adoption_check
      command: bin/adoption-check
      expected_exit: 0
    - name: repo_health_check
      command: bin/repo-health-check
      expected_exit: 0

tasks:
  - title: Select pilot repositories and risk tiers
    priority: P1
  - title: Apply baseline adoption process and collect evidence
    priority: P1
  - title: Evaluate promotion criteria and decide next rollout wave
    priority: P1

depends_on:
  - 20260305-platform-distribution-codex-01-execplan
---

# Purpose / Big Picture

Run a controlled pilot to validate platform adoption readiness before broad rollout.

## Progress

- [x] Create adoption pilot plan
- [x] Run pilot execution and evidence capture
- [x] Evaluate promotion criteria
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: no broad rollout without pilot evidence.

Rationale: pilot-first lowers operational risk.

Date/Author: 2026-03-05 / agent/codex-01

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

Adoption pilot is the final lane after architecture, kernel, governance, and distribution are stable.

## Plan of Work

1. Execute pilot selection and migration.
2. Validate required checks and rollout criteria.

## Concrete Steps

1. Define pilot list and migration checklist.
2. Run required checks and capture evidence.
3. Record go/no-go recommendation.

## Validation and Acceptance

Accepted when pilot metrics and required checks satisfy promotion thresholds.

## Idempotence and Recovery

Pilot operations must support rollback to known-good baseline.

## Artifacts and Notes

- `.agent/execplans/20260305-platform-adoption-pilot-codex-01-execplan.md`
- `spec/adoption.yaml`
- `.agent/adoption/pilot-status.yaml`
- `src/platform_tools/adoption_check.py`
- `bin/adoption-check`

## Interfaces and Dependencies

Interfaces:

- `docs/getting-started.md`
- `spec/adoption.yaml`
- `.agent/adoption/pilot-status.yaml`
- `src/platform_tools/adoption_check.py`
- `bin/adoption-check`

Dependencies:

- `20260305-platform-distribution-codex-01-execplan`
