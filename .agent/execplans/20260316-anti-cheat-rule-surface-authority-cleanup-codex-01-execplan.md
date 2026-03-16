---
id: "20260316-anti-cheat-rule-surface-authority-cleanup-codex-01-execplan"
title: "Make anti-cheat rule-surface legality explicit for governance implementation slices"
owner: "agent/codex-01"
created: "2026-03-16T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260316-anti-cheat-rule-surface-authority-cleanup-codex-01-execplan.md
  - docs/agent-capability-boundaries.md
  - docs/governance.md
  - docs/queued-execplans.md
  - spec/agent-capability-policy.yaml
  - spec/protected-surfaces.schema.yaml
  - src/platform_tools/anti_cheat_check.py
  - tests/test_anti_cheat_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260316-anti-cheat-rule-surface-followup-codex-01"
draft_created: "2026-03-16T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260316-anti-cheat-rule-surface-authority-cleanup-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Make rule-surface edits explicit in anti-cheat capability rules"
    priority: "P1"
  - title: "Remove warning-only treatment for lawful governance rule-surface edits"
    priority: "P1"
depends_on:
  - "20260316-anti-cheat-capability-enforcement-codex-01-execplan"
  - "20260316-subgame-branch-state-transition-governance-codex-01-execplan"
---

# Purpose / Big Picture

Close the remaining anti-cheat contract gap exposed by slice 3: governance implementation branches can lawfully edit `rule_surface` files, but the current capability policy still treats those edits as warning-only rather than explicit allowed behavior.

## Progress

- [ ] Reconcile the merged slice-3 branch to `completed`
- [ ] Make rule-surface legality explicit for governance implementation slices
- [ ] Remove warning-only handling for this case from anti-cheat outputs

## Surprises & Discoveries

- Slice 3 passed lawfully, but it still emitted anti-cheat warnings because `rule_surface` is not explicitly listed in the active governance capability rule.
- This is a contract-cleanup slice, not a new authority-model change.

## Decision Log

- 2026-03-16 / agent-codex-01 / This follow-on should stay narrow: explicit anti-cheat policy cleanup only, not a broader redesign of governance capability classes.

## Outcomes & Retrospective

On completion, the anti-cheat contract should make governance rule-surface edits explicit for lawful implementation work so successful slices no longer pass with warning-only ambiguity.

## Context and Orientation

This slice exists because the merged subgame/state-transition work is correct but still leaves a small policy inconsistency:

- `rule_surface` edits are real governance surfaces
- governance implementation slices sometimes must change them
- the capability policy should model that explicitly rather than warn after the fact

## Plan of Work

1. Reconcile the canonical graph and queue for the merged slice-3 branch.
2. Update the anti-cheat capability policy so lawful governance rule-surface edits are explicit.
3. Update the anti-cheat referee/tests so the output is deterministic and non-ambiguous.

## Concrete Steps

1. Mark the merged slice-3 node completed in the remaining-work graph and queue mirror.
2. Add explicit `rule_surface` legality to the appropriate governance capability rule.
3. Tighten anti-cheat outputs/tests so lawful rule-surface edits do not degrade to warning-only behavior.

## Validation and Acceptance

Acceptance criteria:

- the follow-on is canonically queued after merged slice 3
- governance implementation slices have explicit `rule_surface` treatment in capability policy
- anti-cheat output no longer relies on warning-only fallback for lawful rule-surface edits

## Idempotence and Recovery

- repeated graph reconciliation should be deterministic
- the cleanup must not weaken exception-registry or referee-surface protections

## Artifacts and Notes

Expected artifacts:

- `spec/agent-capability-policy.yaml`
- `spec/protected-surfaces.schema.yaml`
- `src/platform_tools/anti_cheat_check.py`

## Interfaces and Dependencies

Primary interfaces:

- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`
- `spec/agent-capability-policy.yaml`
- `src/platform_tools/anti_cheat_check.py`
