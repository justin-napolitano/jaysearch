---
id: "20260312-game-policy-compliance-codex-01-execplan"
title: "Formalize policy-compliance as a governed game family with commit-structure enforcement"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md
  - .agent/AGENTS.md
  - .agent/PLANS.md
  - docs/agent-game-rules-v1.md
  - docs/governance.md
  - docs/games/README.md
  - docs/games/game-inheritance.md
  - docs/games/policy-compliance-game.md
  - docs/games/commit-structure-game.md
  - spec/games.schema.yaml
  - spec/games/inheritance-rules.yaml
  - spec/games/policy-compliance-game.yaml
  - spec/games/commit-structure-game.yaml
  - spec/game-transitions.yaml
  - spec/ruleset.yaml
  - spec/workflow.yaml
  - artifacts/planner/research/remaining-work-graph.json
  - artifacts/planner/research/game-graph.json
  - artifacts/planner/research/bibliography-graph.json
  - artifacts/planner/research/claim-registry.json
  - src/platform_tools/game_graph_check.py
  - src/platform_tools/game_status.py
  - src/platform_tools/game_rules_audit.py
  - src/platform_tools/policy_compliance_check.py
  - bin/game-rules-audit
  - bin/policy-compliance-check
  - bin/policy-compliance-smoke-test
  - docs/queued-execplans.md
  - tests/test_game_rules_audit.py
  - tests/test_policy_compliance_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260312-game-policy-compliance-codex-01-execplan-codex-01-20260312"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance-smoke-test"
      command: "bin/policy-compliance-smoke-test"
      expected_exit: 0
tasks:
  - title: "Formalize game-policy-compliance as a canonical game under the current layered hierarchy"
    priority: "P1"
  - title: "Formalize game-commit-structure as a subgame under policy compliance"
    priority: "P1"
  - title: "Bind currently partial policy rules to canonical rule ids, scopes, and referees"
    priority: "P1"
  - title: "Add deterministic policy-compliance runtime and smoke coverage"
    priority: "P1"
  - title: "Keep game-hostile-review queued behind policy compliance rather than implementing it in this slice"
    priority: "P1"
depends_on:
  - "20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan"
---

# Purpose / Big Picture

Turn the current partially formalized policy rules into an explicit governed game family so the platform can tell whether a move was legal before it ever reaches hostile review or human review.

This slice should take the partial rules surfaced by the game-rules audit and bind them into canonical games, rules, and referees. In particular, commit structure should become a first-class subgame under policy compliance rather than a prose-only expectation in governance documents.

## Progress

- [x] Formalize `game-policy-compliance`
- [x] Formalize `game-commit-structure` as a policy-compliance subgame
- [x] Bind partial policy rules to canonical rule ids and inheritance scope
- [x] Add deterministic referee/runtime coverage for policy compliance
- [x] Record `game-hostile-review` as dependent on policy-compliance completion
- [x] Validate the slice

## Surprises & Discoveries

- the rules audit established that several high-value rules are canonical but still only partially referee-enforced
- commit ordering and human-sized commits are important enough to block merge readiness, but they are not yet modeled as their own subgame
- some rules that look like "compliance" are actually inherited board law and must stay platform-wide rather than becoming local overrides inside policy compliance
- hostile review should consume policy-compliance results, not invent those legality checks for itself

## Decision Log

- 2026-03-12 / agent-codex-01 / `game-policy-compliance` should be introduced before `game-hostile-review`.
- 2026-03-12 / agent-codex-01 / `game-commit-structure` should live under `game-policy-compliance`.
- 2026-03-12 / agent-codex-01 / Merge readiness should consume policy-compliance outcomes rather than redefining policy rules itself.
- 2026-03-12 / agent-codex-01 / Global board-law rules must remain inherited platform constraints even after policy-compliance is added.
- 2026-03-12 / agent-codex-01 / The platform must not advance state by agent assertion, prose judgment, or board edits alone; required referee chains must pass before a slice can advance.
- 2026-03-12 / agent-codex-01 / Policy-compliance must also treat graph and queue reconciliation as legality inputs so governed work cannot advance on stale backlog state.

## Outcomes & Retrospective

On completion, the repository should have:

- a canonical `game-policy-compliance`
- a canonical `game-commit-structure` subgame
- explicit rule bindings for partial policy rules such as procedural commit order, human-sized commits, clean merge state, and latest-main branching expectations
- a deterministic referee command for policy compliance
- updated audit output that classifies these rules as enforced by policy-compliance rather than merely partial
- a clear dependency edge showing `game-hostile-review` builds on policy compliance instead of replacing it
- a primary inherited rule that the repo cannot advance a governed slice unless the required referee chain passes

Expected implemented outcome:

- `bin/policy-compliance-check` emits deterministic machine-readable blockers and pass/fail results
- the current game audit can point to policy-compliance and commit-structure as canonical games instead of planned follow-ons
- merge-readiness and later hostile-review work can consume policy-compliance results as upstream evidence
- slice progression surfaces such as review-readiness and merge-readiness can consume policy-compliance status instead of trusting agent narration
- remaining-work graph and queue reconciliation are first-class legality checks inside policy-compliance rather than follow-up chores

## Context and Orientation

The game-rules audit established the core platform model:

- one shared platform board
- inherited global board law
- domain games
- narrower subgames
- referee evaluation order of global board law, then active domain game, then active subgame

That audit also surfaced partial rules that need stronger formalization before the review layer grows further. This slice is the step that turns those partial rules into a durable legality surface.

This slice also establishes the project-level principle that governed work should advance only from passing referee evidence. Agents may propose or execute moves, but they should not be able to advance canonical state purely by assertion.

## Plan of Work

1. Inventory the currently partial policy rules and assign them canonical ownership under `game-policy-compliance` or `game-commit-structure`.
2. Add canonical game specs and graph nodes for policy compliance and commit structure.
3. Clarify which rules remain inherited platform law versus which are enforced locally by policy-compliance.
4. Implement a deterministic policy-compliance referee command.
5. Bind policy-compliance outcomes to advancement semantics so later review/merge gates can consume them deterministically.
6. Update the game-rules audit so it reports these rules as enforced by the new game family.
7. Keep hostile review queued behind this slice rather than implementing it here.

## Concrete Steps

1. Add canonical docs/specs for:
   - `game-policy-compliance`
   - `game-commit-structure`
2. Update rule catalogs and game graph artifacts to bind current partial policy rules.
3. Implement `src/platform_tools/policy_compliance_check.py`.
4. Add:
   - `bin/policy-compliance-check`
   - `bin/policy-compliance-smoke-test`
   - `tests/test_policy_compliance_check.py`
5. Update the relevant runtime/status surfaces so policy-compliance can serve as an advancement gate rather than only an advisory report.
6. Update `bin/game-rules-audit` and related tests to reflect the new game family.
7. Run:
   - `bin/execplan-validate .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md`
   - `bin/policy-compliance-smoke-test`

## Artifacts and Notes

- This slice should preserve the current global board-law model and only formalize the partial rules that the audit assigned to policy compliance.
- `game-hostile-review` remains a queued follow-on and should not be partially implemented here.
- The game audit should be updated so policy-compliance and commit-structure become current canonical games rather than only planned follow-ons.

## Interfaces and Dependencies

- depends on the merged audit plan `20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan`
- should align with current governance and game docs:
  - `docs/governance.md`
  - `docs/games/README.md`
  - `docs/games/game-inheritance.md`
- should update the current game/rules surfaces rather than creating parallel policy channels:
  - `spec/games.schema.yaml`
  - `spec/ruleset.yaml`
  - `spec/game-transitions.yaml`
  - `artifacts/planner/research/game-graph.json`
  - `src/platform_tools/game_rules_audit.py`

## Validation and Acceptance

Acceptance criteria:

- policy-compliance exists as a canonical game in the hierarchy
- commit structure exists as a canonical subgame under policy compliance
- the current partial policy rules are explicitly attached to that game family
- the platform can deterministically report policy-compliance blockers
- governed advancement can be blocked by policy-compliance failure instead of relying on agent assertions
- the game audit no longer reports commit-structure as a merely planned subgame
- hostile review remains queued behind policy compliance instead of being partially implemented here

Validation run:

- `bin/execplan-validate .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md`
- `bin/game-graph-check`
- `bin/game-rules-audit`
- `uv run pytest tests/test_game_graph_check.py tests/test_game_status.py tests/test_game_rules_audit.py tests/test_policy_compliance_check.py`

## Idempotence and Recovery

- rerunning the policy-compliance referee on the same repo state should produce stable results
- if rule ownership is ambiguous, the referee must block with explicit findings rather than guess
