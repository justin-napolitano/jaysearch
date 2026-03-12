---
id: "20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan"
title: "Audit the game rules engine and formalize extensibility for future subgames"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan.md
  - .agent/AGENTS.md
  - .agent/PLANS.md
  - docs/agent-game-rules-v1.md
  - docs/games/README.md
  - docs/games/game-inheritance.md
  - docs/games/platform-game.md
  - docs/games/execplan-game.md
  - docs/games/planning-game.md
  - docs/games/implementation-game.md
  - docs/governance.md
  - spec/games.schema.yaml
  - spec/games/inheritance-rules.yaml
  - spec/games/platform-game.yaml
  - spec/games/execplan-game.yaml
  - spec/games/planning-game.yaml
  - spec/games/implementation-game.yaml
  - spec/games/planning-merge-readiness-game.yaml
  - spec/games/implementation-merge-readiness-game.yaml
  - spec/game-transitions.yaml
  - spec/ruleset.yaml
  - spec/workflow.yaml
  - artifacts/planner/research/game-graph.json
  - artifacts/planner/research/bibliography-graph.json
  - artifacts/planner/research/claim-registry.json
  - src/platform_tools/game_graph_check.py
  - src/platform_tools/game_status.py
  - src/platform_tools/orchestrator_status.py
  - bin/game-graph-check
  - bin/game-status
  - bin/game-rules-audit
  - bin/game-rules-audit-smoke-test
  - tests/test_game_rules_audit.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan-codex-01-20260312"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan.md"
      expected_exit: 0
    - name: "game-rules-audit-smoke-test"
      command: "bin/game-rules-audit-smoke-test"
      expected_exit: 0
tasks:
  - title: "Inventory which game rules are machine-enforced versus prose-only"
    priority: "P1"
  - title: "Inventory which rule and design decisions are citation-backed versus unsupported"
    priority: "P1"
  - title: "Classify commit-structure rules as enforced, partial, or prose-only"
    priority: "P1"
  - title: "Clarify inheritance, override, and referee binding in canonical game specs"
    priority: "P1"
  - title: "Add deterministic audit command for rule-engine completeness and extension readiness"
    priority: "P1"
  - title: "Record hostile review as the next planned subgame once extension points are sound"
    priority: "P1"
depends_on:
  - "20260311-game-graph-validator-and-status-codex-01-execplan"
  - "20260312-human-operations-review-runtime-codex-01-execplan"
---

# Purpose / Big Picture

Audit the current game rules engine so the platform knows exactly which rules are canonical and machine-enforced, which are only documented in prose, and which extension points are still underspecified for adding future subgames.

This slice exists to make the nested game system trustworthy before the next major addition. In particular, it should distinguish inherited platform-wide board law from domain-specific games, and prepare the substrate for a future hostile-review game without implementing that game yet.

## Progress

- [ ] Inventory canonical rule sources and classify enforcement status
- [ ] Distinguish inherited global board-law rules from domain-local game rules
- [ ] Distinguish global board-law rules, domain-game rules, and subgame-local rules
- [ ] Clarify game inheritance and override boundaries in canonical artifacts
- [ ] Clarify referee order across inherited board law, domain games, and subgames
- [ ] Add deterministic audit/report command for rules-engine completeness
- [ ] Record hostile-review game as the next follow-on subgame
- [ ] Validate the slice

## Surprises & Discoveries

- the repository already has a documented nested game hierarchy, but the relationship between prose game docs, machine-readable specs, and referee/runtime enforcement is still only partially explicit
- some high-value rules are now machine-enforced through branch policy, remaining-work validation, finalization reconciliation, and board/runtime status, but the full game layer has not yet been audited end to end
- citation tooling exists, but the repository has not yet audited which active rule and design claims are actually backed by linked evidence versus asserted in prose
- some rules such as forbidden moves, scope compliance, no hidden state, and authority boundaries behave more like inherited board law than local domain-game rules, and the audit should make that distinction explicit
- the game stack is better modeled as one shared platform board with inherited global law plus domain-specific games, not as a flat set of peer games
- commit-order and commit-structure rules exist in governance, but they are not yet clearly modeled as a first-class game/referee obligation
- the next planned hostile-review game should only be added after the underlying hierarchy, inheritance model, and referee bindings are explicit enough to support new subgames cleanly

## Decision Log

- 2026-03-12 / agent-codex-01 / The platform should audit the existing game/rule engine before adding new games to it.
- 2026-03-12 / agent-codex-01 / Rules should be gated to games in the hierarchy, with inherited constraints flowing downward unless explicitly overridden.
- 2026-03-12 / agent-codex-01 / Forbidden moves, scope compliance, no hidden state, determinism, and authority boundaries should be modeled as inherited platform board law rather than only as local compliance subgames.
- 2026-03-12 / agent-codex-01 / The platform should be modeled as one shared board with inherited global law, domain games with local move sets, and subgames that narrow those rules further.
- 2026-03-12 / agent-codex-01 / Referees should enforce each active subgame deterministically and kick failed moves back with explicit blockers.
- 2026-03-12 / agent-codex-01 / Referees should check moves in order against inherited global board law, active domain-game rules, and active subgame-local rules.
- 2026-03-12 / agent-codex-01 / High-value rule and design decisions should be research-backed with explicit citation links so humans can verify whether an agent is inventing unsupported claims.
- 2026-03-12 / agent-codex-01 / Commit-structure rules should be audited as part of the rules engine so the platform can decide whether they belong in a dedicated game or a policy-compliance referee.
- 2026-03-12 / agent-codex-01 / A hostile-review game is the intended next follow-on, but it should be implemented only after the audit confirms the extension model is sound.

## Outcomes & Retrospective

On completion, the repository should have:

- a clear inventory of game-rule sources and their enforcement status
- a clear inventory of which rule and design claims are citation-backed, inferred, or unsupported
- a clear split between inherited platform board-law rules and domain/subgame-local rules
- a clear layered hierarchy separating global board law, domain games, and subgames
- a clear classification of current commit-order and commit-structure rules as enforced, partial, or prose-only
- a machine-readable audit result identifying prose-only, enforced, and duplicated rules
- explicit extension points for adding new games and binding referees to them
- a committed record that hostile review is the next planned subgame after the audit

Expected implemented outcome:

- `bin/game-rules-audit` emits deterministic results about hierarchy completeness, inheritance coverage, and enforcement gaps
- the audit reports citation/provenance gaps for rule and design claims that should be human-verifiable
- the audit reports which rules are global inherited board law, domain-game constraints, or subgame-local constraints
- the audit reports whether current referees are checking global law before local game rules
- the audit explicitly reports whether commit-structure rules are merely governed policy today or already part of a referee-enforced game
- the game graph and related specs clarify which rules belong to which game and how subgames inherit or narrow them
- the repository can add a future hostile-review game without inventing ad hoc rule channels

## Context and Orientation

The platform is operating as a nested game system:

- platform game with inherited board law
- domain games with local move sets
- subgames inside those domains
- merge-readiness proof games

New runtime work has already made execution, review, and finalization more machine-readable. The next architectural question is whether the underlying game/rule layer is itself complete and extensible enough to support more subgames, especially the planned hostile-review game.

That means the repository needs an explicit audit of:

- inherited global board-law rules
- global board-law rules that apply to every move on the shared platform board
- canonical game hierarchy
- inheritance rules
- referee bindings
- referee evaluation order across global board law, domain games, and subgames
- move legality sources
- source-of-truth boundaries
- which rules are still only prose
- which rule and design claims have citation support linked through canonical provenance artifacts
- whether commit-order and commit-structure rules are attached to a current game/referee or only documented in policy

## Plan of Work

1. Inventory current game and rule artifacts across docs, specs, graphs, and runtimes.
2. Classify each active rule as global board law, domain-game rule, or subgame-local rule.
3. Classify each active rule as machine-enforced, partially enforced, or prose-only.
4. Classify active rule and design claims as citation-backed, inferred, or unsupported.
5. Classify commit-structure rules and decide whether they belong in a dedicated game or a broader policy-compliance referee.
6. Clarify inheritance, override, and referee-order expectations where the current model is underspecified.
7. Add a deterministic audit command that reports rule-engine completeness, provenance coverage, extension readiness, and referee coverage.
8. Record hostile-review as the next planned subgame once the audit reports the substrate is ready.

## Concrete Steps

1. Audit:
   - `docs/games/*.md`
   - `docs/agent-game-rules-v1.md`
   - `spec/games/*.yaml`
   - `spec/games.schema.yaml`
   - `spec/game-transitions.yaml`
   - `artifacts/planner/research/game-graph.json`
   - `artifacts/planner/research/bibliography-graph.json`
   - `artifacts/planner/research/claim-registry.json`
   - current game-aware runtime surfaces
2. Update canonical artifacts to make clear:
   - which rules are inherited platform board law
   - which rules are owned by domain games versus subgames
   - which rules inherit by default
   - which rules may be overridden locally
   - how referees are attached to each game/subgame
   - in what order referees must check global law versus local game rules
   - which rule and design claims require citation support and where that support must link back
   - whether commit-structure rules are governed by an existing game/referee or need their own formal game
3. Implement `bin/game-rules-audit` and supporting runtime logic.
4. Add `tests/test_game_rules_audit.py` and `bin/game-rules-audit-smoke-test`.
5. Record the future hostile-review game structure in the audit outputs/notes as the next intended extension, without implementing its runtime yet.
6. Run:
   - `bin/execplan-validate .agent/execplans/20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan.md`
   - `bin/game-rules-audit-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- the repository can report which rules are inherited platform law versus domain/subgame-local rules
- the repository can report which rules are global board law versus domain-game rules versus subgame-local rules
- the repository can report which current rules are enforced, partial, or prose-only
- the repository can report which active rule and design claims are citation-backed, inferred, or unsupported
- inheritance and override rules are explicit enough to support adding new subgames safely
- referee bindings and referee evaluation order for current games are visible in canonical artifacts or deterministic audit output
- the game board and hierarchy are complete enough that failed moves can be kicked back at the correct game boundary
- hostile-review is recorded as the next follow-on game, not left as chat-only intent
- focused tests and smoke pass

## Idempotence and Recovery

- rerunning the audit should produce stable output for the same repo state
- if a rule source is missing or contradictory, the audit must emit explicit blockers rather than inventing structure
- the audit should be useful to a human, Codex, Claude, or future tool with no prior session memory

## Artifacts and Notes

Expected artifacts:

- updated game/rule docs and specs
- deterministic game-rules audit command
- focused tests and smoke coverage
- explicit follow-on note for the hostile-review game

## Interfaces and Dependencies

Primary dependencies:

- `docs/games/README.md`
- `docs/games/game-inheritance.md`
- `docs/agent-game-rules-v1.md`
- `spec/games.schema.yaml`
- `spec/games/inheritance-rules.yaml`
- `spec/game-transitions.yaml`
- `artifacts/planner/research/game-graph.json`
- `src/platform_tools/game_graph_check.py`
- `src/platform_tools/game_status.py`
