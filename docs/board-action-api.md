# Board-Action API

## Purpose

This contract turns governed board and game mutations into typed local actions. Humans and agents may request legal transitions through one explicit model instead of editing canonical artifacts ad hoc.

The current canonical backend remains local repository state:

- `artifacts/planner/research/remaining-work-graph.json`
- `.agent/execplans/*.md`
- other governed local artifacts referenced by the action family

Git and GitHub are operator and evidence surfaces. They are not authority sources.

## Authority Model

- Canonical authority: local repo artifacts validated by local referees
- Projection surfaces: queue mirrors, GitHub Projects, PR status, check runs
- Evidence surfaces: Git commits, branch refs, merge-base state, PR review and merge metadata
- Human override: final authority remains human review and merge approval

The API contract is intentionally storage-abstractable. A later control-plane repo or service may host the same action model, but this slice does not externalize authority.

## Action Model

Every action request uses the same envelope:

- `action_id`
- `action_family`
- `actor_id`
- `actor_class`
- `object_id`
- `source_state`
- `target_state`
- `requested_mutation_surfaces`
- `canonical_artifact_refs`
- `git_evidence_refs`
- `github_evidence_refs`

The action family defines which surfaces are mutable, which evidence is required, and which rejection reasons are legal.

### Minimum Action Families

- `backlog_graph_action`
  - changes canonical backlog state
- `queue_projection_reconcile`
  - reconciles projection surfaces from canonical backlog state
- `implementation_branch_publish`
  - records a published implementation branch as evidence-backed readiness state
- `merge_completion_reconcile`
  - records slice completion from merge-backed evidence
- `exception_record`
  - records exception request, denial, approval, and expiry actions

## Event Log

Every accepted or rejected action emits one deterministic event record.

- storage format: canonical JSON Lines
- one record per line
- sorted keys
- stable list ordering by lexical sort
- explicit `decision`
- explicit artifact and evidence refs

The event log is an audit surface for downstream referees. It does not replace the canonical artifacts that the action modifies.

## Git and GitHub Mapping

The contract binds transitions to Git and GitHub evidence without making either authoritative:

- branch creation and publish: Git branch refs plus optional GitHub branch visibility
- PR open/review/merge: GitHub evidence only, paired with local merge and tree state
- commit/tree/merge-base state: Git evidence
- board sync and check runs: projection evidence only

GitHub Projects remains a projection surface. A board card, label, or check result may reflect state, but it may not define canonical legality by itself.

## Rejection Semantics

Rejected actions must be deterministic and machine-readable.

- no partial canonical writes
- rejection reason must be from the action family contract
- event record must still be written
- replay of the same rejected request against unchanged state should return the same result

## Future Compatibility

This contract is designed so later slices can:

- attach capability classes and protected-surface rules
- replace implementation-branch commit-order legality with state-transition legality
- move storage to an external control plane without changing the action envelope
