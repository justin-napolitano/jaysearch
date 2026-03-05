# Platform Definition v1

This document defines the minimum standard for this repository to qualify as a true AI engineering platform template.

## Scope

This platform standard covers:

- ExecPlan-driven execution
- Agent/human governance
- Deterministic validation
- TODO lifecycle automation
- Repository health scoring
- Spec test execution
- Signed finalization and audit evidence

## Core Invariants

These invariants are mandatory:

1. All meaningful work originates from an ExecPlan in `.agent/execplans/`.
2. Agents only draft; humans finalize with SSH-signed commits.
3. Validation outputs are deterministic and machine-readable (JSON).
4. Exit codes are stable and documented (`0` success, `1` structural, `2` security).
5. ExecPlan schema and required headings are strictly enforced.
6. Task extraction to `TODO.md` is deterministic and idempotent.
7. Repository health checks are deterministic and reproducible.
8. Validation tests declared in ExecPlans are executable by a single test runner.
9. Finalized plans produce verifiable audit artifacts.

## Architecture Contract

## Execution Surface

- Human/operator entrypoints: `bin/*`
- Core logic: `src/platform_tools/*` (canonical; `tools/*` may only contain thin wrappers)
- Local orchestration: `bin/run-local-ci`

## Data Contracts

- ExecPlan: markdown + YAML frontmatter defined by `.agent/PLANS.md`
- TODO: deterministic entries in `TODO.md`, keyed by `(execplan_id, task_title)`
- Health report: deterministic summary + machine-readable JSON
- Test report: deterministic per-test pass/fail with expected/actual exits
- Audit artifact: `.agent/audit/<plan-id>.<commit-sha>.signed.json`

## Required Commands

Minimum required command surface:

- `bin/execplan-validate`
- `bin/run-local-ci`
- `bin/sync-todos`
- `bin/repo-health-check`
- `bin/execplan-test`

## Acceptance Checklist (Template Qualification Gate)

A repository qualifies as this template only when all checks pass:

- [ ] `bin/execplan-validate .agent/execplans/*.md` exits `0` on valid inputs.
- [ ] Validator returns deterministic JSON and machine-readable errors.
- [ ] Validator enforces required frontmatter fields and required headings.
- [ ] Validator enforces branch naming, task cap (<= 20), and draft TTL (14 days).
- [ ] Validator enforces signature/finalization policy for finalized plans.
- [ ] `bin/sync-todos` deterministically updates `TODO.md` from ExecPlan tasks.
- [ ] `bin/sync-todos` does not create duplicates on repeated runs.
- [ ] `bin/repo-health-check` exits `0` on healthy repo, non-zero on violations.
- [ ] Repo health includes governance presence, ExecPlan integrity, TODO integrity, security, and maturity score.
- [ ] `bin/execplan-test` executes `validation.tests` blocks from ExecPlans.
- [ ] `bin/execplan-test` returns non-zero when any test fails.
- [ ] `bin/run-local-ci` runs all platform gates in deterministic order.
- [ ] `.agent/audit/` exists and finalized plans can produce signed audit artifacts.
- [ ] Command/docs consistency: every documented command exists and is executable.
- [ ] No placeholder implementations remain in production command path.

## Current Gap Map -> ExecPlan Ownership

This map assigns each observed platform gap to the ExecPlan that must close it.

1. Placeholder validator/security/score/diff implementations
- Gap: `src/platform_tools/execplan_lint.py`, `src/platform_tools/security_scan.py`, `src/platform_tools/agent_score.py`, `src/platform_tools/diff_analyzer.py` are placeholders.
- Owner plan: `20260304-platform-validator-jay-execplan`
- Done when: all four tools return deterministic JSON + documented exit codes.

2. Missing TODO automation command
- Gap: `bin/sync-todos` missing; TODO generation not implemented as governed behavior.
- Owner plan: `20260304-todo-automation-jay-execplan`
- Done when: TODO generation is deterministic, deduplicated, and linked to plan IDs.

3. Missing repository health engine implementation
- Gap: `src/platform_tools/repo_health.py` and robust `bin/repo-health-check` behavior missing.
- Owner plan: `20260304-repo-health-engine-jay-execplan`
- Done when: health report + maturity scoring + proper exit behavior implemented.

4. Missing spec test runner
- Gap: `src/platform_tools/spec_test_runner.py` and `bin/execplan-test` missing.
- Owner plan: `20260304-spec-test-runner-jay-execplan`
- Done when: validation tests from ExecPlans execute deterministically with non-zero failure semantics.

5. Command surface drift vs docs
- Gap: docs reference commands not yet implemented consistently.
- Owner plans: `20260304-platform-validator-jay-execplan`, `20260304-todo-automation-jay-execplan`, `20260304-repo-health-engine-jay-execplan`, `20260304-spec-test-runner-jay-execplan`
- Done when: docs and command surface match exactly.

6. Duplicate implementation paths (`tools/` and `src/platform_tools/`)
- Gap: duplicate code paths create drift risk.
- Owner plan: `20260304-platform-validator-jay-execplan`
- Done when: `src/platform_tools/` is the only source of logic and `tools/` is wrappers-only or removed.

7. Missing audit artifact location
- Gap: `.agent/audit/` not present.
- Owner plan: `20260304-platform-validator-jay-execplan`
- Done when: directory exists and artifact creation path is wired.

8. Encoding/formatting inconsistencies in docs
- Gap: mojibake and mixed symbol encoding in docs/governance text.
- Owner plan: `docs-governance-bootstrap-20260304` (or dedicated docs cleanup ExecPlan)
- Done when: UTF-safe, consistent markdown formatting across governance docs.

## Execution Order (Platform Completion)

Platform implementation order remains:

1. `20260304-platform-validator-jay-execplan`
2. `20260304-todo-automation-jay-execplan`
3. `20260304-repo-health-engine-jay-execplan`
4. `20260304-spec-test-runner-jay-execplan`

After these complete and are human-finalized, platform-layer work is considered complete and subsequent ExecPlans should be project-domain work.


