# Governance

Authority model:

- Agents draft work.
- Humans finalize work.

Global board law:

- forbidden moves
- scope compliance
- no hidden state
- canonical state ownership
- determinism
- human authority boundaries

Referees should check global board law before active domain-game and
subgame rules.

Finalization requires:

- SSH signed commit
- Updated ExecPlan frontmatter
- Metadata reference to ExecPlan id

Bypass/exception approvals require:

- Human approver identity
- Accountable owner
- Explicit rationale
- Expiry timestamp

Required check contract:

- Canonical check contract is defined in `spec/governance.yaml`.
- Check names must be stable snake_case and map to one deterministic command.
- Current required checks: `execplan_validate`, `sync_todos`, `repo_health_check`, `execplan_spec_tests`, `run_local_ci`.

Implementation slice validation rule:

- Every implementation ExecPlan must include at least one dedicated smoke-test command in its validation section.
- The smoke-test command should exercise the primary path for that implementation slice in one invocation.
- A slice is not merge-ready until its smoke-test command passes.

Commit structuring rule:

- Codex-authored work must be committed in procedural order when the slice naturally spans multiple artifact types.
- Preferred order is:
  1. active ExecPlan
  2. canonical spec or schema
  3. implementation or runtime code
  4. tests and smoke-test scripts
  5. docs and runbooks
  6. research, claim-registry, or bibliography updates
  7. governance rule updates
- A commit should usually contain one artifact class from this sequence unless the slice is too small to justify separation.
- Codex may use multiple adjacent commits for the same artifact class when needed to stay under commit-size limits or keep each commit human-reviewable.
- When one class is split across multiple commits, those commits should remain contiguous in the procedural sequence rather than being interleaved with later classes.
- If a slice omits a class, Codex should skip it rather than collapsing unrelated classes together.
- Merge review should preserve this order so reviewers can inspect contract, implementation, and evidence in sequence.

Latest-main branching rule:

- Unless a human explicitly states otherwise, every new work branch must be created from the latest `main`.
- In practice this means Codex should refresh from `origin/main` before cutting a new branch rather than branching from a stale local base.
- If a branch is intentionally cut from some other base, that exception should be stated in the user request or the active ExecPlan.

Implementation-branch split rule:

- `draft-execplan/*` branches exist to draft and review ExecPlan artifacts.
- `impl-execplan/*` branches are the canonical execution branches for individual implementation ExecPlans.
- Parallel implementation ExecPlans must not share one implementation branch.
- `queue-execplan/*` branches are optional integration branches for deliberate stacking after slice-local implementation exists.
- A queue branch must not be the only execution branch for multiple active implementation slices.

Governed finalization authority rule:

- Governed ExecPlan finalization should be keyed to the signed merge commit on `main`, not to an intermediate draft or implementation commit.
- The signed merge commit is the canonical authority event for `finalized_by`, `finalized_at`, and merge-backed `finalized_in_pr` metadata.
- Signature verification must succeed for the selected merge commit before reconciliation may claim completion.
- When merge-backed evidence is deterministic, governed ExecPlans should be reconciled to `status: completed` from that canonical merge event.
- Reconciliation must prefer an `impl-execplan/*` merge over a `draft-execplan/*` merge for the same ExecPlan id when both exist.
- `finalized_by` must be resolved through the canonical signer identity map in `spec/governance.yaml`, not inferred from a single maintainer entry in repository prose.
- If merge history, signature verification, or finalizer identity is ambiguous, the reconciliation command must fail with explicit blockers rather than invent completion metadata.
- Future automation should derive finalization metadata from the signed merge event wherever possible.

Board review runtime rule:

- The GitHub Projects board is a projection surface for review and handoff, not an authority source.
- Live board sync requires a canonical field-map artifact and must reuse the existing project id when one is already known.
- When canonical item ids are already known, sync must prefer updating those items instead of creating new ones.
- Human operations runtime must expose takeover-safe state from canonical local evidence so another human or agent can resume without session memory.

Policy-compliance rule:

- Governed slices must not advance by agent assertion, prose judgment, or board edits alone.
- A required referee chain must pass before review-readiness, merge-readiness, or later completion may be claimed.
- `bin/policy-compliance-check` is the canonical legality surface for branch-level policy compliance.
- Policy compliance should block advancement when commit structure is illegal, when the branch is not aligned with latest `main`, or when graph and queue reconciliation are stale for the active slice.
- Graph and queue state are part of governed branch legality, not optional bookkeeping after the fact.
- `bin/remaining-work-graph-check` is the canonical legality surface for graph-action state, deterministic ready ordering, and stale queue-projection detection.
- Reorder operations are legal only when recorded as canonical graph actions; silent queue edits or board-only reprioritization are forbidden moves.

Game layering rule:

- The platform is one shared board with inherited global law.
- Domain games add local move sets on top of that law.
- Proof and other subgames narrow local obligations further.
- Failed moves should be rejected at the narrowest game boundary that
  still preserves any inherited board-law violation.

Exception lifecycle contract:

- Exception registry file: `.agent/governance/exceptions.yaml`.
- Required fields include owner, approver, rationale, created/expires timestamps, and bypass evidence.
- Active exceptions may not be expired.
- Exceptions nearing expiry (within renewal window) require renewal evidence.

Remaining-work ordering rule:

- The local remaining-work graph owns graph-action records, queue position, and deterministic ready ordering.
- `docs/queued-execplans.md` is a projection mirror and must advertise the latest reconciled graph action id and ready-order metadata from the graph.
- GitHub Projects or other provider boards may surface ordering and action-required state, but they must not author or override it.
