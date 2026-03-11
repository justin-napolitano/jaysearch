---
id: "20260311-nested-game-system-design-codex-01-execplan"
title: "Design the nested game system for Codex-orchestrated platform execution"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-nested-game-system-design-codex-01-execplan.md
  - docs/games/README.md
  - docs/games/platform-game.md
  - docs/games/execplan-game.md
  - docs/games/planning-game.md
  - docs/games/implementation-game.md
  - docs/games/planning-merge-readiness-game.md
  - docs/games/implementation-merge-readiness-game.md
  - docs/games/game-inheritance.md
  - docs/games/game-system-phase-2-backlog.md
  - docs/research-assumptions.md
  - spec/games.schema.yaml
  - spec/games/platform-game.yaml
  - spec/games/execplan-game.yaml
  - spec/games/planning-game.yaml
  - spec/games/implementation-game.yaml
  - spec/games/planning-merge-readiness-game.yaml
  - spec/games/implementation-merge-readiness-game.yaml
  - spec/games/inheritance-rules.yaml
  - artifacts/planner/research/game-graph.json
  - artifacts/planner/research/claim-registry.json
  - artifacts/planner/research/bibliography-graph.json
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-nested-game-system-design-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-nested-game-system-design-codex-01-execplan.md"
      expected_exit: 0
    - name: "game-graph-json-parse"
      command: "python3 -m json.tool artifacts/planner/research/game-graph.json >/dev/null"
      expected_exit: 0
    - name: "claim-registry-check"
      command: "bin/citation-check"
      expected_exit: 0

tasks:
  - title: "Define top-level platform game"
    priority: "P1"
  - title: "Define ExecPlan game as governed contract layer"
    priority: "P1"
  - title: "Define planning game as ambiguity-reduction phase"
    priority: "P1"
  - title: "Define implementation game as validated execution phase"
    priority: "P1"
  - title: "Define planning merge-readiness game"
    priority: "P1"
  - title: "Define implementation merge-readiness game"
    priority: "P1"
  - title: "Define inheritance and override rules across games"
    priority: "P1"
  - title: "Define canonical game graph and graph-linkage rules"
    priority: "P1"
  - title: "Register nested-game claims and assumptions"
    priority: "P1"
  - title: "Produce implementation backlog for game-aware orchestrator/runtime work"
    priority: "P1"

depends_on:
  - "20260310-planner-control-plane-design-codex-01-execplan"
  - "20260310-rule-graph-codex-01-execplan"
  - "20260310-codex-orchestrator-contract-codex-01-execplan"
  - "20260310-merge-readiness-engine-codex-01-execplan"
---

# Purpose / Big Picture

Design the platform as a nested game system rather than a single undifferentiated workflow. The objective is to formalize how the platform game contains the ExecPlan game, how the ExecPlan game contains planning and implementation games, and how each phase terminates in its own merge-readiness proof game.

This phase is design only. It does not implement new runtime behavior. It defines the hierarchy, inheritance semantics, source-of-truth boundaries, graph relationships, and research provenance needed to keep future orchestrator work coherent.

## Progress

- [ ] Define game hierarchy
- [ ] Define shared game ontology
- [ ] Define planning and implementation phase games
- [ ] Define planning and implementation merge-readiness proof games
- [ ] Define inheritance and override rules
- [ ] Define source-of-truth boundaries across game, rule, and research graphs
- [ ] Register nested-game claims and assumptions
- [ ] Produce implementation backlog

## Surprises & Discoveries

Expected discoveries to capture during execution:

- some validators are inherited referees across all games, while others are phase-specific
- merge-readiness needs to be modeled as phase-specific proof games, not as one generic stage
- some concepts such as evidence and authority should inherit by default, while scoring and local move sets may permit controlled override
- the game graph must link to existing rule, bibliography, and claim artifacts without diluting their authority

## Decision Log

Planned foundational decisions to record during execution:

- 2026-03-11 / agent-codex-01 / The platform is a nested game system, not a single game
- 2026-03-11 / agent-codex-01 / The ExecPlan game governs both planning and implementation games
- 2026-03-11 / agent-codex-01 / Planning merge readiness and implementation merge readiness are distinct proof games
- 2026-03-11 / agent-codex-01 / Shared board, evidence, referee, and authority concepts are inherited by default unless explicitly overridden
- 2026-03-11 / agent-codex-01 / The game graph is canonical for hierarchy and handoff relations only
- 2026-03-11 / agent-codex-01 / The rule graph remains canonical for governance-rule relationships
- 2026-03-11 / agent-codex-01 / The bibliography graph remains canonical for research provenance relationships
- 2026-03-11 / agent-codex-01 / The claim registry remains canonical for artifact-level claim classification

## Outcomes & Retrospective

On completion, this plan should yield:

- a formal nested game hierarchy
- per-game docs and YAML specs
- explicit inheritance and override rules
- a canonical game graph artifact for hierarchy and handoff
- explicit source-of-truth boundaries across all graph artifacts
- registered nested-game claims and updated assumptions
- a named backlog for game-aware orchestrator implementation

## Context and Orientation

The repository already contains:

- planner and implementation game concepts
- merge-readiness contract and merge-readiness engine
- rule graph
- orchestrator contract
- scoring and citation enforcement

What is missing is the formal structure that connects these into one nested system with explicit parent-child relationships, inheritance rules, and graph boundaries.

## Plan of Work

1. Define the shared game ontology.
2. Define the hierarchy and parent-child relationships.
3. Define per-game objectives, moves, referees, and win conditions.
4. Define which properties inherit automatically, which may override locally, and which are forbidden to override.
5. Define source-of-truth boundaries between the game graph, rule graph, bibliography graph, and claim registry.
6. Encode the hierarchy in a canonical game graph.
7. Produce implementation backlog for runtime/orchestrator alignment.

## Concrete Steps

1. Write `docs/games/README.md` describing the nested game system and hierarchy.
2. Write per-game docs for:
   - platform game
   - ExecPlan game
   - planning game
   - implementation game
   - planning merge-readiness game
   - implementation merge-readiness game
3. Write `docs/games/game-inheritance.md` defining:
   - inherited-by-default concepts
   - locally overridable concepts
   - forbidden overrides
4. Write `spec/games.schema.yaml` as the common schema for all game specifications.
5. Write per-game specs under `spec/games/` as game-specific instances constrained by the common schema.
6. Write `spec/games/inheritance-rules.yaml`.
7. Write `artifacts/planner/research/game-graph.json` with:
   - parent-child game edges
   - handoff edges
   - shared referee edges
   - evidence-flow edges
   - linkage edges to canonical rule and research artifacts
8. Update `artifacts/planner/research/claim-registry.json` for nested-game claims.
9. Update `artifacts/planner/research/bibliography-graph.json` if new claim nodes or artifact nodes are required.
10. Update `docs/research-assumptions.md` to classify any new nested-game assumptions.
11. Write `docs/games/game-system-phase-2-backlog.md`.
12. Run:
   - `bin/execplan-validate .agent/execplans/20260311-nested-game-system-design-codex-01-execplan.md`
   - `python3 -m json.tool artifacts/planner/research/game-graph.json >/dev/null`
   - `bin/citation-check`

## Validation and Acceptance

Acceptance criteria:

- a reviewer can explain the game hierarchy without inference
- planning, implementation, and both merge-readiness games are modeled as distinct but connected games
- board semantics are explicit
- referee semantics are explicit
- authority semantics are explicit
- evidence semantics are explicit
- scoring inheritance semantics are explicit
- inheritance and override rules are defined clearly enough to guide runtime implementation
- the game graph explicitly links to the rule graph and research artifacts without redefining their authority
- nested-game claims are registered under the repo’s citation/inference procedure

Validation commands:

1. `bin/execplan-validate .agent/execplans/20260311-nested-game-system-design-codex-01-execplan.md`
2. `python3 -m json.tool artifacts/planner/research/game-graph.json >/dev/null`
3. `bin/citation-check`

Additional manual review checks:

- verify that merge-readiness is modeled as two phase-specific proof games
- verify that `spec/games.schema.yaml` is clearly the shared contract and `spec/games/*.yaml` are constrained instances
- verify that graph-linkage rules do not create contradictory sources of truth
- verify that inheritance semantics are explicit rather than implied
- verify that no new governing abstraction bypasses the existing rule graph

## Idempotence and Recovery

This is a design-only plan. Reruns are safe if changes to hierarchy, inheritance, override semantics, or graph boundaries are recorded explicitly and updated consistently across docs, specs, and research artifacts.

## Artifacts and Notes

Expected artifacts:

- `docs/games/README.md`
- `docs/games/platform-game.md`
- `docs/games/execplan-game.md`
- `docs/games/planning-game.md`
- `docs/games/implementation-game.md`
- `docs/games/planning-merge-readiness-game.md`
- `docs/games/implementation-merge-readiness-game.md`
- `docs/games/game-inheritance.md`
- `docs/games/game-system-phase-2-backlog.md`
- `spec/games.schema.yaml`
- `spec/games/*.yaml`
- `spec/games/inheritance-rules.yaml`
- `artifacts/planner/research/game-graph.json`
- updated research registry/graph artifacts
- updated assumptions register

## Interfaces and Dependencies

Primary dependencies:

- `docs/planner-game-model.md`
- `docs/implementation-game-model.md`
- `docs/merge-readiness-contract.md`
- `docs/codex-orchestrator-contract.md`
- `spec/codex-orchestrator.yaml`
- `spec/game-transitions.yaml`
- `spec/scoring.yaml`
- `artifacts/planner/research/rule-graph.json`
- `artifacts/planner/research/claim-registry.json`
- `artifacts/planner/research/bibliography-graph.json`

Planned interfaces to define:

- game hierarchy contract
- game inheritance contract
- game override contract
- game handoff contract
- game graph schema
- graph-linkage contract
- game-aware orchestrator backlog
