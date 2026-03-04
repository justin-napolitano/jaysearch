---
id: repo-health-engine-20260304
title: Implement repository health validation engine
owner: "github:jay.napolitano"
created: "2026-03-04T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260304-repo-health-engine-jay-execplan.md
  - tools/repo_health.py
  - bin/repo-health-check
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "github:jay.napolitano"
draft_branch: draft-execplan/repo-health-engine-jay-20260304
draft_created: "2026-03-04T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

tasks:
  - title: Validate ExecPlan structure
    priority: P1
  - title: Validate TODO integrity
    priority: P1
  - title: Run security scanning checks
    priority: P1
  - title: Validate governance file presence
    priority: P1
  - title: Compute maturity score and level
    priority: P2
  - title: Implement repo-health-check CLI
    priority: P1

validation:
  tests:
    - name: repo_health_check
      command: bin/repo-health-check
      expected_exit: 0

depends_on:
  - todo-automation-20260304
---

# Purpose / Big Picture

Implement repository health validation.

Outputs created:

- `bin/repo-health-check`
- `tools/repo_health.py`

## Progress

- [ ] Create ExecPlan draft
- [ ] Implement `tools/repo_health.py`
- [ ] Implement `bin/repo-health-check`
- [ ] Validate exit codes and deterministic output
- [ ] Human finalize via signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: Health reporting will return deterministic, machine-readable data plus stable human-readable summary.

Rationale: supports both automated gates and operator review.

Date/Author: 2026-03-04 / github:jay.napolitano

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

The platform needs a single command to check whether repository governance and execution health are intact. This includes ExecPlan validity, TODO consistency, security posture, governance file presence, and a maturity score.

## Plan of Work

1. Build health engine in `tools/repo_health.py`.
2. Implement check modules for structure, TODO integrity, security, and governance files.
3. Calculate maturity level and numeric score.
4. Expose checks via `bin/repo-health-check`.

## Concrete Steps

1. Implement `tools/repo_health.py` with checks for:
   - ExecPlan structure
   - TODO integrity
   - Security scanning
   - Governance file presence (`.agent/AGENTS.md`, `.agent/PLANS.md`, `.agent/metrics.yml`)
   - Repository maturity scoring
2. Implement `bin/repo-health-check` CLI wrapper.
3. Ensure deterministic output ordering and stable score calculation.
4. Run `bin/repo-health-check` and verify exit behavior.

Expected output example:

    Repository Health Report
    ------------------------
    ExecPlans: OK
    TODO integrity: OK
    Security: OK
    Maturity Level: 3
    Score: 87

## Validation and Acceptance

Plan is accepted when:

- `bin/repo-health-check` exits `0` when repository is valid.
- Errors are reported when governance files are missing.
- A deterministic maturity level and score are generated.
- Output format is stable for identical repository state.

## Idempotence and Recovery

Health checks are read-only and safe to repeat. If checks fail, fix reported issues and rerun without requiring cleanup.

## Artifacts and Notes

- Repository health report output
- Optional JSON report artifact if implemented

## Interfaces and Dependencies

Interfaces:

- `tools/repo_health.py`
- `bin/repo-health-check`

Dependencies:

- `.agent/AGENTS.md`
- `.agent/PLANS.md`
- `.agent/metrics.yml`
- `todo-automation-20260304`
