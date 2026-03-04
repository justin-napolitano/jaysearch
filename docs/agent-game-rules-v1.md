# Agent Game Rules v1

This document defines the game agents must play to execute ExecPlans in this repository.

Status: `DRAFT-RULESET`

Implementation freeze: no platform or project implementation work may begin until this document is marked `APPROVED-RULESET` by a human maintainer.

## 1. Objective

The objective is to complete approved ExecPlans with maximum rule compliance, deterministic evidence, and minimum human correction.

Primary win condition per plan:

- Plan status is moved by a human from `draft` to `proposed`/`approved`, then to `completed`.
- Required validations pass with deterministic output.
- Finalization is completed by SSH-signed human commit with valid metadata.

Platform match win condition:

- Required platform plans are completed in required order:
  1. `platform-validator-20260304`
  2. `todo-automation-20260304`
  3. `repo-health-engine-20260304`
  4. `spec-test-runner-20260304`

## 2. Players and Roles

- Agent player: drafts plans, proposes edits, runs validators, reports evidence.
- Human authority: approves/finalizes plans, resolves disputes, performs signed finalization commits.
- Referee: deterministic validator stack (`bin/execplan-validate`, `bin/run-local-ci`, other required checks).

## 3. Board State

A turn operates on repository state:

- Governance state: `.agent/AGENTS.md`, `.agent/PLANS.md`, `.agent/metrics.yml`
- Plan state: `.agent/execplans/*.md`
- Task state: `TODO.md`
- Evidence state: command outputs and audit artifacts

A move is valid only if it leaves board state policy-compliant.

## 4. Allowed Moves

Allowed agent moves:

1. Read files and inspect repository state.
2. Create/edit ExecPlan drafts under `.agent/execplans/`.
3. Edit files listed in an active draft plan `changes` field.
4. Run deterministic validation commands.
5. Produce machine-readable reports and summarize findings.

Forbidden agent moves:

1. Finalize plans (`finalized_by`, `finalized_at`, status beyond allowed draft workflow for agents).
2. Bypass branch protections or CODEOWNERS.
3. Modify governance files without an approved governing ExecPlan.
4. Hide failures, forge signatures, or suppress referee evidence.

## 5. Turn Protocol

Each turn must follow:

1. Declare active plan id.
2. State intended move(s).
3. Execute move(s).
4. Run referee checks required by plan phase.
5. Record evidence (deterministic outputs, pass/fail).
6. Update plan `Progress` and logs.

If any required check fails, turn outcome is `FAIL` and state must return to compliant draft execution.

## 6. Scoring Function

Score range: `0-100`.

Composite score:

`S = 100 * (DQ*w_dq + HED*w_hed + VPR*w_vpr + SLS*w_sls + BC*w_bc) - P`

Weights from `.agent/metrics.yml`:

- `w_dq = 0.25`
- `w_hed = 0.25`
- `w_vpr = 0.20`
- `w_sls = 0.15`
- `w_bc = 0.15`

Metric definitions (normalized `0.0-1.0`):

- `DQ` (Draft Quality): schema completeness + required section coverage + clarity checks.
- `HED` (Human Edit Distance): 1 - normalized post-agent human rewrite size.
- `VPR` (Validation Pass Rate): passing required checks / total required checks.
- `SLS` (Security Lint Score): 1 when no security violations, decays by severity count.
- `BC` (Behavioral Correctness): compliance with allowed move set and workflow order.

Penalty `P` is additive from rule violations (Section 7).

## 7. Penalties

Hard penalties:

- Critical policy breach (forbidden move, governance bypass, signature forgery): `P += 100` and automatic turn loss.
- Non-deterministic required output: `P += 40`.
- Missing required ExecPlan fields/headings: `P += 30`.
- Out-of-scope edits not declared in `changes`: `P += 25`.
- Missing required evidence artifact: `P += 20`.
- Command/docs mismatch introduced: `P += 15`.

Any hard policy breach sets match state to `ESCALATE_TO_HUMAN`.

## 8. Determinism Contract

Required deterministic behavior:

1. Stable file processing order (lexicographic path order).
2. Stable error/warning ordering.
3. Stable JSON key ordering in emitted reports where feasible.
4. Stable exit code mapping:
   - `0` success
   - `1` structural/policy failure
   - `2` security failure
5. Same inputs must produce byte-equivalent machine-readable outputs, except timestamps when explicitly allowed.

## 9. Referee Protocol

Minimum referee checks per phase:

Draft quality gate:

- `bin/execplan-validate .agent/execplans/*.md`

Platform gate:

- `bin/run-local-ci`

Optional supplemental gates (when implemented):

- `bin/repo-health-check`
- `bin/execplan-test`
- `bin/sync-todos`

Referee output must include:

- command executed
- exit code
- deterministic machine-readable result
- concise human summary

## 10. Match Flow and Stop Conditions

Lifecycle flow:

1. `draft`
2. `proposed` (human)
3. `approved` (human)
4. `executing`
5. `completed`

Stop conditions:

- Required check failure not resolved within active turn.
- Rule breach with escalation requirement.
- Draft TTL exceeded (14 days) without refresh/finalization.

## 11. Human Override and Tie-Breaks

Human decisions are authoritative when:

- score conflicts with governance policy,
- ambiguous interpretation of rules exists,
- security or compliance risk is non-trivial.

Override must be documented in plan `Decision Log` with rationale and date.

## 12. Go/No-Go Gate

`NO-GO` until a human marks this document approved.

To activate the game:

1. Human marks status at top of this document as `APPROVED-RULESET`.
2. Human confirms referee command set is available.
3. Agent work resumes under these rules.

---

Version: `v1`
Date: `2026-03-04`
Owner: `github:jay.napolitano`
