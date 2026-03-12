# Agent Game Rules v1

## 0. Canonical Identifiers

Canonical ExecPlan id format is:

- `YYYYMMDD-<plan-name>-<owner>-execplan` (example: `20260304-platform-validator-jay-execplan`)

Filename remains:

- `YYYYMMDD-<plan-name>-<owner>-execplan.md`

Validation must treat the canonical plan key as the filename stem in this format. Frontmatter `id` must match the canonical plan key.
This document defines the game agents must play to execute ExecPlans in this repository.

Status: `APPROVED-RULESET`

Implementation freeze: no platform or project implementation work may begin until this document is marked `APPROVED-RULESET` by a human maintainer.

## 1. Objective

The objective is to complete approved ExecPlans with maximum rule compliance, deterministic evidence, and minimum human correction.

Primary win condition per plan:

- Plan status is moved by a human from `draft` to `proposed`/`approved`, then to `completed`.
- Required validations pass with deterministic output.
- Finalization is completed by SSH-signed human commit with valid metadata.

Platform match win condition:

- Required platform plans are completed in required order:
  1. `20260304-platform-validator-jay-execplan`
  2. `20260304-todo-automation-jay-execplan`
  3. `20260304-repo-health-engine-jay-execplan`
  4. `20260304-spec-test-runner-jay-execplan`

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

Global board law applies to every move before any local phase/game rule
is considered:

- forbidden moves
- scope compliance
- no hidden state
- canonical state ownership
- determinism
- human authority boundaries

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

Referees should evaluate moves in this order:

1. inherited global board law
2. active domain-game rules
3. active subgame or proof-game rules

Implementation-slice smoke-test rule:

- Every implementation ExecPlan must define at least one dedicated smoke-test command.
- The smoke-test command should validate the primary path for that slice in one invocation.
- The smoke-test command must pass before the slice is considered merge-ready.
- Smoke-test scripts should live under `bin/` when practical.

Procedural commit-order rule:

- Codex-authored slices should be committed in procedural order when multiple artifact classes are involved.
- Preferred order is:
  1. active ExecPlan
  2. canonical spec or schema
  3. implementation/runtime changes
  4. focused tests and smoke-test scripts
  5. docs and runbooks
  6. research provenance updates
  7. governance rule changes
- Agents may split one artifact class into multiple adjacent commits when needed to satisfy hard commit-size limits or preserve reviewer readability.
- Split commits for one class should stay contiguous; they should not be interleaved with later classes unless a human documents an exception.
- A slice may skip unused classes, but it should not collapse distant classes together without justification.
- Reviewers should be able to inspect the stack from contract to enforcement to explanatory material without reconstructing the intended sequence by hand.

Latest-main branching rule:

- Unless a human explicitly states otherwise, every new work branch should be cut from the latest `main`.
- Agents should prefer `origin/main` as the source of truth when local `main` is stale.
- Starting a new slice from a stale base is a governance failure unless the deviation is deliberate and documented.

Implementation-branch split rule:

- `draft-execplan/*` branches are for drafting and review of ExecPlan artifacts.
- `impl-execplan/*` branches are the canonical execution branches for individual implementation slices.
- Each parallel implementation ExecPlan must run on its own `impl-execplan/*` branch.
- `queue-execplan/*` branches are optional integration-only branches and do not replace slice-local implementation branches.
- Running multiple active implementation slices only on a shared queue branch is a governance failure unless a human documents an explicit exception.

Governed finalization authority rule:

- Signed merge commits on `main` are the canonical finalization event for governed ExecPlans.
- Intermediate draft or implementation commits may provide evidence, but they do not replace signed merge authority.
- Deterministic finalization automation should derive `finalized_by`, `finalized_at`, and `finalized_in_pr` from the signed merge event where feasible.
- Automated derivation of `finalized_by` must use the signer identity map in `spec/governance.yaml`; repository prose is explanatory, not authoritative, for finalizer identity.
- When merge evidence is deterministic, governed ExecPlans should be reconciled to `status: completed` from that same merge event.
- If both draft and implementation merges exist for the same ExecPlan id, the implementation merge should be treated as the stronger completion authority signal.
- If merge, signature verification, or identity derivation is ambiguous, the reconciliation move must fail explicitly rather than claiming completion.

Board/review runtime rule:

- The external review board is a projection-only surface.
- Live sync requires the canonical field-map artifact.
- Once project or item identities are known, moves must reuse them rather than duplicating board state.
- Human review and takeover moves are only valid if they remain reconstructable from canonical local evidence.

Policy-compliance rule:

- Governed slices must not advance by agent assertion, prose judgment, or board edits alone.
- Required referee chains must pass before a slice may become review-ready, merge-ready, or completed.
- Policy-compliance is the legality surface for implementation branches before hostile review or human review.
- Governed work must record the corresponding graph action and queue reconciliation on-branch; stale queue or graph state blocks advancement.
- Reorder moves must be explicit canonical graph actions. Editing queue prose or board order without a matching graph action is an illegal move.
- The queue mirror must advertise the latest reconciled graph action id and canonical ready order from the graph before advancement may continue.

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

1. Human updates status to `APPROVED-RULESET` in this document.
2. Human commits that change with SSH signing.
3. Commit message includes `Metadata: Ruleset: agent-game-rules-v1` and `Signed-off-by:`.
4. Human confirms referee command set is available.
5. Agent work resumes under these rules.

---

Version: `v1`
Date: `2026-03-04`
Owner: `github:jay.napolitano`



