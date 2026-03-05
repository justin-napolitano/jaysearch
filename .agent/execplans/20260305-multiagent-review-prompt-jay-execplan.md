---
id: 20260305-multiagent-review-prompt-jay-execplan
title: Govern and operationalize multiagent Codex prompts
owner: "github:jay.napolitano"
created: "2026-03-05T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260305-multiagent-review-prompt-jay-execplan.md
  - prompts/20260305-multiagent-review-prompt-jay.md
  - prompts/20260305-multiagent-control-plane-mvp-execution-jay.md
  - prompts/20260305-execute-merged-platform-backlog-jay.md
  - docs/prompts.md
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "github:jay.napolitano"
draft_branch: draft-execplan/multiagent-review-prompt-jay-20260305
draft_created: "2026-03-05T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: execplan_validate
      command: bin/execplan-validate .agent/execplans/*.md
      expected_exit: 0

tasks:
  - title: Add versioned multiagent review prompt artifact
    priority: P1
  - title: Add control-plane MVP execution prompt
    priority: P1
  - title: Add merged-backlog execution prompt
    priority: P1
  - title: Add prompt usage documentation
    priority: P2
  - title: Validate prompt contracts against governance
    priority: P1

depends_on:
  - 20260304-platform-validator-jay-execplan
---

# Purpose / Big Picture

Establish a governed, reusable prompt kit for Codex sessions that supports hostile review, control-plane MVP execution, and ordered execution of merged platform backlog.

This plan turns prompt text into managed platform assets so session behavior is repeatable across future projects.

## Progress

- [ ] Create ExecPlan draft
- [ ] Add/revise prompt artifacts under `prompts/`
- [ ] Add concise prompt usage documentation
- [ ] Validate prompt content against governance rules
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: prompts are treated as governed artifacts and must be versioned with explicit usage contract.

Rationale: reusable platform behavior requires stable, reviewable session entrypoints.

Date/Author: 2026-03-05 / github:jay.napolitano

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

The repository now includes multiple operational prompts. They need explicit governance and a defined contract so they remain aligned with canonical rules (`spec/*`, `policy/*`, and ExecPlan governance).

Prompt categories in scope:

- hostile review + strict plan-driven execution
- multiagent control-plane MVP execution
- execution of merged but not fully implemented platform backlog

## Plan of Work

1. Ensure prompts are versioned and named consistently.
2. Align prompt constraints with canonical standards:
   - canonical plan identity format
   - `src/platform_tools/*` as logic location
   - human SSH-signed approval/finalization gates
3. Add operator-facing docs for when each prompt should be used.
4. Validate consistency with existing governance docs.

## Concrete Steps

1. Add/verify prompt files under `prompts/`:
   - `20260305-multiagent-review-prompt-jay.md`
   - `20260305-multiagent-control-plane-mvp-execution-jay.md`
   - `20260305-execute-merged-platform-backlog-jay.md`
2. Add `docs/prompts.md` with selection guidance and expected output format.
3. Ensure each prompt requires:
   - machine-readable JSON report
   - concise summary (<=12 lines)
   - explicit stop rules on governance conflicts
4. Run `bin/execplan-validate .agent/execplans/*.md`.

## Validation and Acceptance

Plan is accepted when:

- all three prompt files exist and are versioned under `prompts/`
- prompt instructions align with canonical identity and logic path rules
- `docs/prompts.md` defines purpose and usage for each prompt
- prompt outputs are specified as JSON + concise human summary
- ExecPlan validation succeeds

## Idempotence and Recovery

Prompt/document updates are safe to reapply. If wording drifts or conflicts are found, update prompt files and rerun validation.

## Artifacts and Notes

Artifacts:

- prompt markdown files under `prompts/`
- usage documentation in `docs/prompts.md`

## Interfaces and Dependencies

Interfaces:

- `prompts/*.md`
- `docs/prompts.md`

Dependencies:

- `.agent/AGENTS.md`
- `.agent/PLANS.md`
- `spec/*`
- `policy/*`
