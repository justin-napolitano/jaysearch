# Queued ExecPlans

## Objective

This document turns the remaining-work graph into an explicit near-term queue of planned slices.

## Initial Queue

1. `20260311-machine-readable-output-hardening-codex-01-execplan`
   - status: `completed`
   - goal: add stable JSON contracts across key orchestrator-facing commands

2. `20260311-composite-orchestrator-status-codex-01-execplan`
   - status: `completed`
   - goal: expose ready work, blockers, rule constraints, and required validations in one command
   - implementation branch: `impl-execplan/20260311-composite-orchestrator-status-codex-01-execplan-codex-01-20260311`

3. `20260311-game-graph-validator-and-status-codex-01-execplan`
   - status: `completed`
   - goal: validate the nested game graph and expose active game/subgame status for orchestration

4. `20260311-implementation-orchestrator-runtime-codex-01-execplan`
   - status: `completed`
   - goal: execute implementation-phase moves against the shared board and evidence model

5. `20260311-runtime-constraint-canonicalization-codex-01-execplan`
   - status: `completed`
   - goal: move remaining runtime-critical queue and readiness rules into validated canonical artifacts
   - implementation branch: `impl-execplan/20260311-runtime-constraint-canonicalization-codex-01-execplan-codex-01-20260311`

6. `20260311-provider-sync-scaffold-codex-01-execplan`
   - status: `completed`
   - goal: scaffold provider adapters without granting external authority

7. `20260311-github-projects-bootstrap-runtime-codex-01-execplan`
   - status: `completed`
   - goal: bootstrap one governed GitHub Projects board from canonical provider schema

8. `20260311-github-projects-provider-sync-runtime-codex-01-execplan`
   - status: `completed`
   - goal: project canonical slice state into the governed GitHub Projects review board

9. `20260312-execplan-finalization-completion-reconciliation-codex-01-execplan`
   - status: `completed`
   - goal: reconcile merged ExecPlans to `status: completed` from signed merge history

10. `20260312-human-operations-review-runtime-codex-01-execplan`
   - status: `completed`
   - goal: formalize board review, takeover, and merge reconciliation as machine-readable runtime state
   - implementation branch: `impl-execplan/20260312-human-operations-review-runtime-codex-01-execplan-codex-01-20260312`

11. `20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan`
   - status: `completed`
   - goal: formalize global board law, game layers, and extension readiness for future subgames
   - implementation branch: `impl-execplan/20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan-codex-01-20260312`

12. `20260312-game-policy-compliance-codex-01-execplan`
   - status: `completed`
   - goal: create `game-policy-compliance` and its `game-commit-structure` subgame so governed slices cannot advance by assertion alone
   - must also formalize graph-action-required and stale-queue blocking so merge/readiness cannot advance on stale backlog state
   - draft branch: `draft-execplan/20260312-game-policy-compliance-codex-01-execplan-codex-01-20260312`
   - implementation branch: `impl-execplan/20260312-game-policy-compliance-codex-01-execplan-codex-01-20260312`
   - completion ref: `merged:pr-72`

13. `20260313-game-hostile-review-runtime-codex-01-execplan`
   - status: `completed`
   - goal: add machine hostile review before human approval gates
   - draft branch: `draft-execplan/20260313-game-hostile-review-runtime-codex-01-execplan-codex-01-20260313`
   - implementation branch: `impl-execplan/20260313-game-hostile-review-runtime-codex-01-execplan-codex-01-20260313`
   - completion ref: `merged:pr-75`

14. `future:game-branching`
   - status: `decision_gated`
   - goal: formalize branch-cut legality and branch-choice policy as its own game

15. `future:game-citation`
   - status: `decision_gated`
   - goal: formalize citation-backed claim verification and anti-hallucination evidence rules

16. `future:game-documentation`
   - status: `decision_gated`
   - goal: formalize documentation completeness for code, games, and relationships

17. `future:game-board-integrity`
   - status: `decision_gated`
   - goal: formalize provider-board reuse, item identity reuse, and sync integrity

18. `graph-action-required-and-stale-queue-enforcement`
   - status: `completed`
   - goal: require every governed work action to map to graph state and block advancement when queue reconciliation is stale
   - implemented in: `20260312-game-policy-compliance-codex-01-execplan`

19. `20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan`
   - status: `completed`
   - goal: formalize deterministic graph actions, canonical ordering fields, and governed reorder/reconciliation behavior
   - draft branch: `draft-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312`
   - implementation branch: `impl-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312`
   - completion ref: `merged:pr-73`

20. `20260316-board-action-api-contract-and-event-log-codex-01-execplan`
   - status: `completed`
   - goal: define typed board/game actions, authority-preserving mutation rules, and a deterministic event log
   - draft branch: `draft-execplan/20260316-next-planning-codex-02`
   - implementation branch: `impl-execplan/20260316-board-action-api-contract-and-event-log-codex-01-execplan-codex-01-20260316`
   - completion ref: `merged:pr-79`

21. `20260316-anti-cheat-capability-enforcement-codex-01-execplan`
   - status: `completed`
   - goal: define protected surfaces, capability classes, and explicit exception paths so agents cannot self-authorize compliance
   - draft branch: `draft-execplan/20260316-next-planning-codex-02`
   - implementation branch: `impl-execplan/20260316-anti-cheat-capability-enforcement-codex-01-execplan-codex-01-20260316`
   - completion ref: `merged:pr-80`

22. `20260316-subgame-branch-state-transition-governance-codex-01-execplan`
   - status: `completed`
   - goal: replace implementation-branch commit-order legality with subgame branch contracts and state-transition legality
   - draft branch: `draft-execplan/20260316-next-planning-codex-02`
   - implementation branch: `impl-execplan/20260316-subgame-branch-state-transition-governance-codex-01-execplan-codex-01-20260316`
   - completion ref: `merged:pr-81`

23. `20260316-anti-cheat-rule-surface-authority-cleanup-codex-01-execplan`
   - status: `completed`
   - goal: make governance rule-surface legality explicit in anti-cheat policy so lawful slices do not pass with warning-only ambiguity
   - draft branch: `draft-execplan/20260316-anti-cheat-rule-surface-followup-codex-01`
   - completion ref: `merged:pr-88`

24. `20260318-rule-authority-consolidation-codex-01-execplan`
   - status: `completed`
   - goal: consolidate canonical rule authority, formalize draft self-review and additive PR structure, and execute the now-finalized slice on its dedicated implementation branch
   - draft branch: `draft-execplan/20260318-rule-authority-consolidation-codex-01-20260318`
   - implementation branch: `impl-execplan/20260318-rule-authority-consolidation-codex-01-execplan-codex-01-20260318`
   - canonical evidence: `merged:pr-83`
   - completion ref: `merged:pr-83`

25. `20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-execplan`
   - status: `completed`
   - goal: add rule-registry drift enforcement, introduce governed `initiative/*` parent branches for graph-backed multi-slice work, standardize provider-sync token and preflight contracts, validate field-map completeness, and harden merge reconciliation evidence selection
   - draft branch: `draft-execplan/20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-20260318`
   - implementation branch: `impl-execplan/20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-execplan-codex-01-20260318`
   - canonical evidence: `merged:pr-86`
   - completion ref: `merged:pr-86`

26. `20260318-graph-transition-automation-and-merge-gating-codex-01-execplan`
   - status: `completed`
   - goal: make routine graph state machine-derived from branch, PR, merge, and check evidence, and fail closed when merges would leave graph reconciliation missing or illegal
   - draft branch: `draft-execplan/20260318-graph-transition-automation-and-merge-gating-codex-01-20260318`
   - implementation branch: `impl-execplan/20260318-graph-transition-automation-and-merge-gating-codex-01-execplan-codex-01-20260319`
   - completion ref: `merged:pr-91`

27. `future:graph-priority-ranking-and-traversal-engine`
   - status: `decision_gated`
   - goal: add machine-readable priority and cost signals so the graph can emit deterministic sequential, parallel-safe, and lowest-cost execution plans

28. `20260319-managed-repo-orchestration-codex-01-execplan`
   - status: `ready`
   - goal: allow external repos such as `jayrun` to keep canonical graph and ExecPlan state locally while platform-template-bootstrap supplies deterministic bootstrap, project-board setup, completion-PR visibility, orchestration, and control-loop runtime by explicit repo-root targeting
   - draft branch: `draft-execplan/20260319-managed-repo-orchestration-bootstrap-codex-01-20260319`

29. `20260319-post-merge-graph-reconciliation-automation-codex-01-execplan`
   - status: `completed`
   - goal: make merged implementation evidence trigger deterministic local completion reconciliation so the graph does not stay stale after PR merge
   - draft branch: `draft-execplan/20260319-post-merge-graph-reconciliation-automation-codex-01-20260319`
   - completion ref: `merged:pr-94`

30. `20260319-local-git-hook-automation-codex-01-execplan`
   - status: `review_gated`
   - goal: install versioned local git hooks that invoke deterministic repo-owned reconciliation and governed pre-push checks instead of requiring manual command chains
   - draft branch: `draft-execplan/20260319-local-git-hook-automation-codex-01-20260319`
## Mirror Metadata

- canonical_last_graph_action_id: `rwg-action-20260319-016-promote_ready-rwg-029`
- canonical_ready_order: `20260319-managed-repo-orchestration-codex-01-execplan`
- projection_authority: `projection_only`

## Queue Discipline

Queued ExecPlans are not active merely because they are listed here. They become active only when:

- a branch is created for the slice
- the ExecPlan exists and validates
- all blocking dependencies are satisfied
- the slice is not held by review or decision gates

Under the current governance model, implementation execution should occur on a dedicated `impl-execplan/*` branch. `queue-execplan/*` branches may be used later for deliberate integration stacking only.

When a queued slice needs several commits inside one procedural step, Codex may split that artifact class into multiple adjacent commits so the branch stays under commit hard limits and each review unit remains human-sized.

When execution findings require updates to the active ExecPlan, Codex may make a bounded reconciliation commit for the active plan as long as the update stays within the same slice goal and records the reason for the change explicitly.

When branch-level governance or checker defects are discovered mid-slice, Codex should repair them with new bounded follow-up commits on the active branch. History rewrites are not the normal compliance path and require explicit human authorization.

When a governed implementation slice accumulates 10 failed repair cycles against its required referees, execution should stop for human review of the active ExecPlan, branch state, and failure evidence before the slice continues.

## Relationship to the Graph

This queue is a human-readable mirror of `artifacts/planner/research/remaining-work-graph.json` and `bin/remaining-work-graph-check`. If the two disagree, the canonical artifact and validator are authoritative.
