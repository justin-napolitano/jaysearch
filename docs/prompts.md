# Prompt Catalog

This repository treats prompts as governed platform artifacts.

Prompt files live in `prompts/` and should be selected by objective.

## 1) MultiAgent Review Prompt

File:

- `prompts/20260305-multiagent-review-prompt-jay.md`

Use when:

- you need hostile repository review before execution
- you need strict ExecPlan-first enforcement

Expected outputs:

- JSON report with issues, missing plans, security findings, fixes
- concise human summary

## 2) Control Plane MVP Execution Prompt

File:

- `prompts/20260305-multiagent-control-plane-mvp-execution-jay.md`

Use when:

- you are building the operational multiagent control plane
- you need referee + scoring + evidence pipeline behavior

Expected outputs:

- deterministic JSON status report
- concise summary (<= 12 lines)

## 3) Execute Merged Platform Backlog Prompt

File:

- `prompts/20260305-execute-merged-platform-backlog-jay.md`

Use when:

- platform ExecPlans are merged but implementation is incomplete
- you need strict sequence execution and stop-on-blocker behavior

Required plan order:

1. `20260304-platform-validator-jay-execplan`
2. `20260304-todo-automation-jay-execplan`
3. `20260304-repo-health-engine-jay-execplan`
4. `20260304-spec-test-runner-jay-execplan`

Expected outputs:

- deterministic JSON execution report
- concise summary (<= 12 lines)

## 4) Design Planner Control Plane Prompt

File:

- `prompts/20260310-design-planner-control-plane-codex-01.md`

Use when:

- defining the planner control plane architecture
- defining session artifacts, graph schema, and contract projection rules
- defining players, moves, referee logic, and commitment stages for the planner game
- producing design-phase specs before implementation work begins

Expected outputs:

- architecture decisions with rationale
- explicit schema and contract proposals
- open questions with recommended disposition

## 5) Review Planner Control Plane Prompt

File:

- `prompts/20260310-review-planner-control-plane-codex-01.md`

Use when:

- hostile-reviewing planner design artifacts
- checking for hidden state, weak authority boundaries, or vague command semantics
- verifying that provider sync remains downstream from canonical local state
- checking that game roles, illegal moves, and referee semantics remain coherent

Expected outputs:

- ordered findings with file references
- explicit assumptions and residual risks

## Governance Notes

- Prompts must align with canonical plan key format.
- Canonical implementation logic is `src/platform_tools/*`.
- Human SSH-signed commits remain required for authoritative finalization.

## Hostile Review Runbook

Use this runbook with `prompts/20260305-multiagent-review-prompt-jay.md`.

1. Create a dedicated branch:
   - `draft-execplan/hostile-review-<agent>-YYYYMMDD`
2. Execute hostile review only on that branch.
3. Generate auditable artifacts in `artifacts/review/`:
   - `hostile-review-report.json`
   - `hostile-review-summary.md`
   - `validation-evidence.json`
4. Run deterministic checks in this order:
   - `bin/execplan-validate .agent/execplans/*.md`
   - `bin/sync-todos`
   - `bin/repo-health-check`
   - `bin/execplan-test`
   - `bin/run-local-ci`
5. Commit artifacts and findings on the hostile-review branch and open a PR.
