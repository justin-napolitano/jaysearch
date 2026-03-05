# Implement platform validation engine

This ExecPlan is a living document. The sections Progress, Surprises &
Discoveries, Decision Log, and Outcomes & Retrospective must be kept up
to date as work proceeds.

This document must be maintained according to `.agent/PLANS.md`.

## Purpose / Big Picture

The repository currently contains governance rules for ExecPlans,
agents, and documentation but no tooling exists to enforce those rules.

This ExecPlan implements the platform validation engine.

After completion a developer (or Codex agent) will be able to run:

    bin/execplan-validate .agent/execplans/*.md

and receive a deterministic validation report showing whether the
ExecPlans follow the governance rules.

Observable behavior:

    bin/execplan-validate .agent/execplans/platform-validator.md

returns:

    Validation successful
    0 errors

or

    Validation failed
    3 errors

The validation engine is the foundation for:

-   ExecPlan linting
-   agent scoring
-   repository health checks
-   local CI
-   Codex task evaluation

## Progress

-   [ ] (2026-03-04T00:00Z) ExecPlan created
-   [ ] Implement execplan_lint.py
-   [ ] Implement security_scan.py
-   [ ] Implement agent_score.py
-   [ ] Implement diff_analyzer.py
-   [ ] Implement bin/execplan-validate
-   [ ] Implement bin/run-local-ci
-   [ ] Run validation tests
-   [ ] Finalize ExecPlan via signed commit

## Surprises & Discoveries

(To be updated during implementation.)

## Decision Log

Decision: Validation tools will produce JSON output to enable machine
evaluation by agents.

Rationale: Agents must optimize behavior using deterministic outputs.

Date/Author: 2026-03-04 / github:jay.napolitano

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

The repository structure currently contains placeholder directories for
tooling.

Relevant directories:

    tools/
    bin/
    .agent/
    docs/

ExecPlans exist under:

    .agent/execplans/

The validation engine will be implemented using Python and executed
using uv.

Python tools will live in:

    tools/

Command interfaces will live in:

    bin/

The system must validate ExecPlans according to:

    .agent/AGENTS.md
    .agent/PLANS.md

## Plan of Work

The platform validation engine consists of four Python modules and two
command entrypoints.

Modules:

    tools/execplan_lint.py
    tools/security_scan.py
    tools/agent_score.py
    tools/diff_analyzer.py

CLI commands:

    bin/execplan-validate
    bin/run-local-ci

The validator will perform the following checks:

ExecPlan structure validation:

Required headings:

-   Purpose / Big Picture
-   Progress
-   Surprises & Discoveries
-   Decision Log
-   Outcomes & Retrospective
-   Context and Orientation
-   Plan of Work
-   Concrete Steps
-   Validation and Acceptance
-   Idempotence and Recovery
-   Artifacts and Notes
-   Interfaces and Dependencies

Frontmatter validation ensuring required fields exist.

Security scan detecting secrets or keys.

Agent scoring computing Draft Quality, Human Edit Distance, Validation
Pass Rate, and Security Lint Score.

Diff analysis detecting changes between plan revisions.

## Concrete Steps

Run inside the repository root.

Step 1

Create tool modules.

    mkdir -p tools

Create files:

    tools/execplan_lint.py
    tools/security_scan.py
    tools/agent_score.py
    tools/diff_analyzer.py

Step 2

Implement execplan_lint.py.

Function:

    validate_execplan(path)

Inputs:

    path to ExecPlan markdown file

Output:

    JSON validation report

Example output:

    {
      "plan": "platform-validator-20260304",
      "errors": [],
      "warnings": []
    }

Exit codes:

    0 success
    1 structural error

Step 3

Implement security_scan.py.

Function:

    scan_repository(path)

Detect patterns such as:

    BEGIN PRIVATE KEY
    API_KEY
    TOKEN
    PASSWORD

Exit codes:

    0 safe
    2 security violation

Step 4

Implement agent_score.py.

Compute metrics:

    Draft Quality
    Human Edit Distance
    Validation Pass Rate
    Security Lint Score

Return JSON score.

Step 5

Implement diff_analyzer.py.

Detect differences between plan revisions.

Input:

    git diff

Output:

    structured change summary

Step 6

Create CLI tool.

    bin/execplan-validate

Example command:

    bin/execplan-validate .agent/execplans/*.md

Expected output:

    Validating 1 ExecPlan
    0 errors

Step 7

Create local CI runner.

    bin/run-local-ci

This runner executes the validation pipeline locally.

## Validation and Acceptance

Plan is complete when:

-   execplan-validate runs successfully
-   run-local-ci executes validation pipeline
-   validators detect structural errors
-   validators detect security issues

## Idempotence and Recovery

Validation tools are safe to run repeatedly and do not modify repository
state.

## Artifacts and Notes

Validation output should be JSON structured for machine consumption.

## Interfaces and Dependencies

    tools/execplan_lint.py
    tools/security_scan.py
    tools/agent_score.py
    tools/diff_analyzer.py

    bin/execplan-validate
    bin/run-local-ci

