---
id: "<plan-id>-YYYYMMDD"
title: "<short human-readable title>"
owner: "agent/<agent-name>"
created: "YYYY-MM-DDTHH:MM:SSZ"
status: draft
base_branch: main
changes:
  - path/to/file1
  - path/to/file2
approve_policy: codeowners
reviewers:
  - "github:<reviewer-username>"

draft_by: "agent/<agent-name>"
draft_branch: "draft-execplan/<plan-id>-<agent-name>-YYYYMMDD"
draft_created: "YYYY-MM-DDTHH:MM:SSZ"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "<validator-name>"
      command: "<command>"
      expected_exit: 0

tasks:
  - title: "<task-title>"
    priority: "P1"

depends_on:
  - "<other-plan-id>"
---

# Purpose / Big Picture

State the objective, why it matters, and the observable outcome.

## Progress

- [ ] Create draft ExecPlan
- [ ] Implement scoped changes
- [ ] Run validation steps
- [ ] Prepare for human finalization

## Surprises & Discoveries

Record unexpected findings and how they affect the plan.

## Decision Log

Capture key decisions with rationale and date/author.

## Outcomes & Retrospective

Document final outcomes, gaps, and lessons after execution/finalization.

## Context and Orientation

Provide enough local context so a novice can execute this plan without external references.

## Plan of Work

Describe the implementation strategy and sequence.

## Concrete Steps

1. List exact commands and file edits.
2. Include deterministic verification commands.
3. Keep steps actionable and reproducible.

## Validation and Acceptance

Define pass/fail checks, expected command outputs, and acceptance criteria.

## Idempotence and Recovery

Explain how to rerun safely and how to recover from partial failures.

## Artifacts and Notes

List generated artifacts, logs, and any operator notes.

## Interfaces and Dependencies

List touched interfaces, tools, and dependencies (including plan dependencies).
