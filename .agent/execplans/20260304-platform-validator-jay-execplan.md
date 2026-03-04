---
id: 20260304-platform-validator-jay-execplan
title: Implement platform validation engine
owner: "github:jay.napolitano"
created: "2026-03-04T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260304-platform-validator-jay-execplan.md
  - src/platform_tools/execplan_lint.py
  - src/platform_tools/security_scan.py
  - src/platform_tools/agent_score.py
  - src/platform_tools/diff_analyzer.py
  - bin/execplan-validate
  - bin/run-local-ci
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "github:jay.napolitano"
draft_branch: draft-execplan/platform-validator-jay-20260304
draft_created: "2026-03-04T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: execplan_validate
      command: bin/execplan-validate .agent/execplans/*.md
      expected_exit: 0
    - name: run_local_ci
      command: bin/run-local-ci
      expected_exit: 0

tasks:
  - title: Implement ExecPlan lint validator
    priority: P1
  - title: Implement security scan
    priority: P1
  - title: Implement agent scoring
    priority: P1
  - title: Implement diff analyzer
    priority: P2
  - title: Implement execplan-validate CLI
    priority: P1
  - title: Implement run-local-ci CLI
    priority: P1
  - title: Validate deterministic JSON outputs
    priority: P1

depends_on:
  - docs-governance-bootstrap-20260304
---

# Purpose / Big Picture

The repository currently contains governance rules for ExecPlans, agents, and documentation but no tooling exists to enforce those rules.

This ExecPlan implements the platform validation engine.

After completion a developer (or Codex agent) will be able to run:

    bin/execplan-validate .agent/execplans/*.md

and receive a deterministic validation report showing whether the ExecPlans follow the governance rules.

Observable behavior:

    bin/execplan-validate .agent/execplans/platform-validator.md

returns:

    Validation successful
    0 errors

or

    Validation failed
    3 errors

The validation engine is the foundation for:

- ExecPlan linting
- agent scoring
- repository health checks
- local CI
- Codex task evaluation

## Progress

- [ ] (2026-03-04T00:00:00Z) ExecPlan created
- [ ] Implement execplan_lint.py
- [ ] Implement security_scan.py
- [ ] Implement agent_score.py
- [ ] Implement diff_analyzer.py
- [ ] Implement bin/execplan-validate
- [ ] Implement bin/run-local-ci
- [ ] Run validation tests
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

(To be updated during implementation.)

## Decision Log

Decision: Validation tools will produce JSON output to enable machine evaluation by agents.

Rationale: Agents must optimize behavior using deterministic outputs.

Date/Author: 2026-03-04 / github:jay.napolitano

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

The repository structure currently contains placeholder validator tooling.

Relevant directories:

    src/platform_tools/
    bin/
    .agent/
    docs/

ExecPlans exist under:

    .agent/execplans/

The validation engine will be implemented using Python and executed using uv.

Python tools will live in:

    src/platform_tools/

Command interfaces will live in:

    bin/

The system must validate ExecPlans according to:

    .agent/AGENTS.md
    .agent/PLANS.md

## Plan of Work

The platform validation engine consists of four Python modules and two command entrypoints.

Modules:

    src/platform_tools/execplan_lint.py
    src/platform_tools/security_scan.py
    src/platform_tools/agent_score.py
    src/platform_tools/diff_analyzer.py

CLI commands:

    bin/execplan-validate
    bin/run-local-ci

The validator will perform the following checks:

ExecPlan structure validation:

Required headings:

- Purpose / Big Picture
- Progress
- Surprises & Discoveries
- Decision Log
- Outcomes & Retrospective
- Context and Orientation
- Plan of Work
- Concrete Steps
- Validation and Acceptance
- Idempotence and Recovery
- Artifacts and Notes
- Interfaces and Dependencies

Frontmatter validation ensuring required fields exist.

Security scan detecting secrets or keys.

Agent scoring computing Draft Quality, Human Edit Distance, Validation Pass Rate, and Security Lint Score.

Diff analysis detecting changes between plan revisions.

## Concrete Steps

Run inside the repository root.

1. Create tool modules under `src/platform_tools/`:
   - `src/platform_tools/execplan_lint.py`
   - `src/platform_tools/security_scan.py`
   - `src/platform_tools/agent_score.py`
   - `src/platform_tools/diff_analyzer.py`
2. Implement `execplan_lint.py` with `validate_execplan(path)` returning deterministic JSON.
3. Implement `security_scan.py` with `scan_repository(path)` and exit code `2` on security findings.
4. Implement `agent_score.py` to compute Draft Quality, Human Edit Distance, Validation Pass Rate, and Security Lint Score.
5. Implement `diff_analyzer.py` to produce structured summaries from Git diffs.
6. Create `bin/execplan-validate` to run lint and produce machine-readable output.
7. Create `bin/run-local-ci` to execute validation pipeline locally.

JSON output example for lint:

    {
      "plan": "20260304-platform-validator-jay-execplan",
      "errors": [],
      "warnings": []
    }

Exit codes:

    0 success
    1 structural error
    2 security failure

## Validation and Acceptance

Plan is complete when:

- `bin/execplan-validate .agent/execplans/*.md` exits `0`
- `bin/run-local-ci` exits `0`
- validators detect structural errors with exit `1`
- validators detect security issues with exit `2`
- validation output is deterministic JSON for identical inputs

## Idempotence and Recovery

Validation tools are safe to run repeatedly and do not modify repository state.

If a validation command fails:

1. Fix the reported issue.
2. Re-run the same command.
3. Confirm identical inputs produce identical outputs.

## Artifacts and Notes

Validation output should be JSON structured for machine consumption.

Expected artifacts produced during execution:

- Validator command output logs
- Local CI run output
- Updated Progress, Surprises & Discoveries, and Decision Log sections

## Interfaces and Dependencies

Primary interfaces:

- `src/platform_tools/execplan_lint.py`
- `src/platform_tools/security_scan.py`
- `src/platform_tools/agent_score.py`
- `src/platform_tools/diff_analyzer.py`
- `bin/execplan-validate`
- `bin/run-local-ci`

Dependencies:

- `.agent/AGENTS.md`
- `.agent/PLANS.md`
- `.agent/metrics.yml`

