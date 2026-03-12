---
id: "20260312-human-operations-review-runtime-codex-01-execplan"
title: "Formalize machine-readable human operations and board review runtime"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260312-human-operations-review-runtime-codex-01-execplan.md
  - .agent/AGENTS.md
  - .agent/PLANS.md
  - docs/governance.md
  - docs/agent-game-rules-v1.md
  - docs/agents.md
  - docs/queued-execplans.md
  - spec/governance.yaml
  - spec/ruleset.yaml
  - spec/workflow.yaml
  - spec/providers/github-projects.schema.yaml
  - artifacts/planner/research/remaining-work-graph.json
  - src/platform_tools/finalize_execplan.py
  - src/platform_tools/integrations/provider_adapter.py
  - src/platform_tools/integrations/github_projects_sync.py
  - src/platform_tools/orchestrator_status.py
  - src/platform_tools/implementation_orchestrator.py
  - bin/finalize-execplan
  - bin/github-projects-sync
  - bin/orchestrator-status
  - bin/human-operations-status
  - bin/human-operations-smoke-test
  - tests/test_finalize_execplan.py
  - tests/test_github_projects_sync.py
  - tests/test_human_operations_status.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260312-human-operations-review-runtime-codex-01-execplan-codex-01-20260312"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260312-human-operations-review-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "human-operations-smoke-test"
      command: "bin/human-operations-smoke-test"
      expected_exit: 0
tasks:
  - title: "Encode human review and takeover invariants in canonical governance specs"
    priority: "P1"
  - title: "Expose a deterministic board-aware human operations status command"
    priority: "P1"
  - title: "Project review and finalization reconciliation back into GitHub Projects state"
    priority: "P1"
  - title: "Add smoke coverage for review-ready, merged, and takeover-safe paths"
    priority: "P1"
depends_on:
  - "20260312-execplan-finalization-completion-reconciliation-codex-01-execplan"
  - "20260311-github-projects-provider-sync-runtime-codex-01-execplan"
  - "20260311-github-projects-bootstrap-runtime-codex-01-execplan"
---

# Purpose / Big Picture

Formalize the human-operations layer of the platform as machine-readable policy and runtime behavior. The repository now has canonical execution graphs, merge-backed finalization reconciliation, and a synced GitHub Projects review surface, but the human review, takeover, and board-reconciliation workflow is still only partially encoded.

This slice should turn human operations into an explicit governed runtime so a human, Codex, Claude, or a future tool can resume, review, merge, and reconcile work from canonical state without relying on prose memory or ad hoc board interpretation.

## Progress

- [x] Define canonical human-operations and board-review invariants
- [x] Add deterministic human-operations runtime/status command
- [x] Reconcile GitHub Projects review fields from canonical local evidence
- [x] Add focused tests and smoke coverage
- [x] Validate the slice

## Surprises & Discoveries

- the platform already has most of the underlying authority model in place, but the remaining gaps are about operational coordination rather than core execution logic
- GitHub Projects sync is now good enough to act as a real review surface, but the rules for when it may be updated, reused, or treated as stale are not yet fully machine-readable
- downstream work should not recreate boards, duplicate project items, or reopen already-completed provider-sync baselines, so those invariants need to be explicit policy rather than tribal knowledge
- human operations now spans multiple surfaces: merge history, remaining-work graph, implementation branches, and GitHub Projects projection; the platform needs one deterministic summary command for that combined state
- the provider projection layer was still deriving review fields from raw node status alone, so this slice needed a shared human-operations evidence helper to keep the board, orchestrator, and review runtime consistent

## Decision Log

- 2026-03-12 / agent-codex-01 / Board/review runtime should be a first-class governed surface, not a follow-up note after execution and finalization.
- 2026-03-12 / agent-codex-01 / Human operations must remain projection-driven from canonical local evidence; GitHub Projects remains a review surface, not workflow authority.
- 2026-03-12 / agent-codex-01 / Existing provider-sync work is baseline platform state and must be treated as completed infrastructure rather than re-scoped future work.
- 2026-03-12 / agent-codex-01 / Takeover and recovery rules must be machine-readable so any human or agent can continue a slice safely after session loss.

## Outcomes & Retrospective

On completion, the repository should have a governed human-operations runtime that:

- exposes review-ready, in-review, merged, reconciled, and takeover-needed states deterministically
- treats the GitHub Projects board as a synced review surface backed by canonical local evidence
- blocks duplicate board bootstrap or duplicate project-item creation once field-map and item ids exist
- makes handoff and takeover rules machine-readable
- lets downstream slices consume human-operations state without reopening already-completed platform work

Implemented outcome:

- `bin/human-operations-status` exposes deterministic board/runtime review state from canonical local evidence
- provider sync now derives review/finalization fields from the same human-operations evidence layer used by status commands
- machine-readable governance/workflow rules now encode board reuse, item-id reuse, and takeover-safe runtime expectations
- the remaining-work graph now reflects the completed provider-sync/finalization baseline and the active human-operations slice

## Context and Orientation

The platform is now close to the intended model:

- local graph and ExecPlans are canonical
- agents execute work on governed branches
- humans review and merge
- signed merge on `main` is the canonical finalization authority
- GitHub Projects mirrors the remaining-work graph as a shared board

What is still underspecified is how humans and agents should operate on top of that shared board once execution reaches the review boundary. The platform needs explicit machine-readable rules for review readiness, merge reconciliation, takeover safety, board reuse, and provider-sync baseline assumptions.

## Plan of Work

1. Extend governance and workflow specs with human-operations and board-reuse invariants.
2. Define or update canonical state so provider-sync baseline, field-map presence, existing item ids, and review/runtime reconciliation rules are explicit.
3. Add a deterministic command surface, likely `bin/human-operations-status`, that summarizes review, merge, reconciliation, and takeover state from canonical evidence.
4. Extend GitHub Projects sync/runtime behavior so review and finalization fields are refreshed from canonical local evidence without duplicating items or re-bootstraping boards.
5. Add focused tests and one smoke script proving review-ready, merged, reconciled, and takeover-safe scenarios.

## Concrete Steps

1. Update `.agent/AGENTS.md`, `.agent/PLANS.md`, `docs/governance.md`, `docs/agent-game-rules-v1.md`, `docs/agents.md`, `spec/governance.yaml`, `spec/ruleset.yaml`, and `spec/workflow.yaml` to define:
   - provider-sync baseline invariants
   - field-map and existing-item-id requirements for live board sync
   - prohibition on duplicate board bootstrap or duplicate item creation when canonical mappings already exist
   - human review, merge, reconciliation, and takeover rules
2. Update `artifacts/planner/research/remaining-work-graph.json` and related runtime surfaces as needed so board/review runtime state is canonical rather than prose-only.
3. Implement `bin/human-operations-status` and supporting runtime logic.
4. Update `bin/github-projects-sync`, `src/platform_tools/integrations/provider_adapter.py`, and `src/platform_tools/integrations/github_projects_sync.py` so board review fields reconcile from canonical state and respect existing baseline board artifacts.
5. Add focused tests and `bin/human-operations-smoke-test`.
6. Run:
   - `bin/execplan-validate .agent/execplans/20260312-human-operations-review-runtime-codex-01-execplan.md`
   - `bin/human-operations-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- machine-readable governance/spec files define review, takeover, and board-reuse invariants
- the platform exposes one deterministic command for human-operations status
- GitHub Projects sync respects existing board/item mappings and does not duplicate completed provider-sync setup
- review and finalization state on the board is derived from canonical local evidence
- downstream slices can detect completed provider-sync baseline and current review state without relying on prose
- focused tests and smoke pass

## Idempotence and Recovery

- rerunning human-operations reconciliation should be a no-op when board/item mappings and merge reconciliation are already current
- if board state, field-map state, or merge evidence is missing or ambiguous, the runtime must emit explicit blockers
- takeover-safe output must expose enough canonical context for another human or agent to continue without prior session memory
- smoke fixtures must not require live network access unless explicitly marked as execute-only integration tests

## Artifacts and Notes

Expected artifacts:

- updated governance/workflow/spec rules for human operations
- deterministic human-operations status command
- updated board-sync runtime that respects canonical board baseline and item reuse
- focused tests and smoke coverage

## Interfaces and Dependencies

Primary dependencies:

- `spec/governance.yaml`
- `spec/ruleset.yaml`
- `spec/workflow.yaml`
- `artifacts/planner/research/remaining-work-graph.json`
- `artifacts/provider-sync/github-projects-field-map.json`
- `src/platform_tools/finalize_execplan.py`
- `src/platform_tools/integrations/github_projects_sync.py`
- `src/platform_tools/orchestrator_status.py`
