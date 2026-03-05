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

## Governance Notes

- Prompts must align with canonical plan key format.
- Canonical implementation logic is `src/platform_tools/*`.
- Human SSH-signed commits remain required for authoritative finalization.
