---
id: "20260310-planner-control-plane-design-codex-01-execplan"
title: "Design the terminal-first planner control plane and canonical task graph"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-planner-control-plane-design-codex-01-execplan.md
  - docs/adr/ADR-0001-graph-canonical-execplan-projection.md
  - docs/implementation-game-model.md
  - docs/game-scoring-model.md
  - docs/references.md
  - docs/research-assumptions.md
  - docs/planner-cli-contract.md
  - docs/planner-control-plane.md
  - docs/planner-execplan-projection.md
  - docs/planner-game-model.md
  - spec/game-transitions.yaml
  - spec/bibliography-graph.schema.yaml
  - spec/scoring.yaml
  - artifacts/planner/research/bibliography-graph.json
  - docs/planner-phase-2-backlog.md
  - docs/prompts.md
  - prompts/20260310-design-planner-control-plane-codex-01.md
  - prompts/20260310-review-planner-control-plane-codex-01.md
  - spec/planner-contract-import.yaml
  - spec/planner-session.yaml
  - spec/task-graph.schema.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-planner-control-plane-design-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-planner-control-plane-design-codex-01-execplan.md"
      expected_exit: 0
    - name: "sync-todos"
      command: "bin/sync-todos"
      expected_exit: 0
    - name: "repo-health-check"
      command: "bin/repo-health-check"
      expected_exit: 0
    - name: "execplan-test"
      command: "bin/execplan-test"
      expected_exit: 0

tasks:
  - title: "Define planner control-plane architecture and invariants"
    priority: "P1"
  - title: "Define canonical task graph schema and lifecycle"
    priority: "P1"
  - title: "Define planner session artifact model and CLI contract"
    priority: "P1"
  - title: "Define ExecPlan projection contract from planner state"
    priority: "P1"
  - title: "Define GitHub Projects adapter scaffold contract"
    priority: "P2"
  - title: "Define prompt catalog additions for design and critique"
    priority: "P1"
  - title: "Write ADR for graph-as-source-of-truth"
    priority: "P1"
  - title: "Produce implementation backlog for phase 2"
    priority: "P1"

depends_on: []
---

# Purpose / Big Picture

Design a terminal-first planner control plane for this platform that converts hard planning dialogue into explicit, auditable local state. The planner must use a canonical local task graph as the source of truth, preserve planner session artifacts as durable local records, and treat ExecPlans as governed execution contracts rather than as the planning system itself.

This phase is architecture and governance only. It does not implement the planner, build a UI, create live provider integrations, or permit any direct code-writing execution path from planner ideation. Its purpose is to produce a design package strong enough that implementation can proceed later without re-litigating core boundaries, state ownership, or command semantics.

## Progress

- [ ] Confirm design-phase scope, non-goals, and invariants
- [ ] Define planner control-plane architecture
- [ ] Define planner session artifact model
- [ ] Define canonical task graph schema and transitions
- [ ] Define `bin/planner` CLI contract
- [ ] Define ExecPlan projection and handoff contract
- [ ] Define GitHub Projects adapter scaffold contract
- [ ] Define planner/control-plane prompt artifacts
- [ ] Write ADR for canonical graph and contract projection model
- [ ] Produce phase-2 implementation backlog
- [ ] Validate all design artifacts against repo governance

## Surprises & Discoveries

Expected discoveries to capture during execution:

- Existing repo governance is stronger around markdown and document validation than around canonical executable state models; the design must improve that without creating a competing governance stack.
- The term `planner` becomes sloppy immediately if session state, graph state, prompt behavior, and ExecPlan contracts are not separated cleanly.
- “Typical Codex session” is a user expectation, not an implementation contract; the design must define interactive terminal behavior without faking runtime details.
- External sync can bloat the architecture if not constrained. GitHub Projects remains scaffold-only in this phase, while Jira and Microsoft Lists remain placeholders under a provider-agnostic adapter model.
- If the graph schema is vague, every downstream contract becomes vague with it. The graph spec is therefore a gating deliverable.

## Decision Log

- 2026-03-10 / agent-codex-01 / Canonical source of truth is local graph state, not chat transcript, not ExecPlan, and not external PM systems.
- 2026-03-10 / agent-codex-01 / Planner session artifacts are durable local files and must not rely on hidden state.
- 2026-03-10 / agent-codex-01 / ExecPlan is an execution contract projection from planner and graph state, not the planning system itself.
- 2026-03-10 / agent-codex-01 / Planner interaction is terminal-first under `bin/planner`; no UI is in scope.
- 2026-03-10 / agent-codex-01 / Planner default tone is hard/direct; friendly behavior is opt-in only.
- 2026-03-10 / agent-codex-01 / External systems are downstream operational views for project management, not workflow authorities.
- 2026-03-10 / agent-codex-01 / GitHub Projects is the only named provider in this design phase and only at scaffold/spec level.
- 2026-03-10 / agent-codex-01 / Selective pullback is allowed by contract, but local canonical state wins by default when conflicts are unresolved.
- 2026-03-10 / agent-codex-01 / No direct code-writing path is allowed from planner ideation mode.

## Outcomes & Retrospective

On completion, this plan should yield a design package that defines:

- planner role and boundaries in the platform
- game model for planning and implementation as governed play
- formal move-transition model for planner and implementation phases
- source-informed scoring model for planner and implementation phases
- explicit citation and bibliography requirements for design and implementation
- explicit phase-2 backlog coverage for runtime, citation validation, CLI/runtime contracts, and scoring engine implementation
- canonical task graph entities, edges, statuses, provenance fields, and lifecycle
- planner session artifact structure and persistence rules
- `bin/planner` CLI surface and command semantics
- conversion rules from planner and graph state to ExecPlan draft contract
- provider adapter model for downstream sync, with GitHub Projects scaffolded and other providers left as placeholders
- validation and artifact expectations for future implementation
- ADR documenting that the graph is canonical and ExecPlan is a contract projection
- phase-2 implementation backlog with bounded, testable follow-on work

Retrospective notes must capture:

- unresolved design questions that are acceptable to defer to implementation planning
- any questions discovered to be foundational and therefore required before coding
- any mismatch found between the planned control plane and current repo governance assumptions

## Context and Orientation

This repository already contains governed primitives that the planner control plane must compose with rather than bypass:

- ExecPlan lifecycle and required structure in `docs/execplans.md`
- prompt governance in `docs/prompts.md`
- workflow lifecycle rules in `spec/workflow.yaml`
- ExecPlan template in `examples/execplan-template.md`
- validation and parsing logic in `src/platform_tools/plan_utils.py`
- existing command-oriented workflow in `bin/`

Current architectural intent established for this design:

- local canonical graph state is the source of truth
- planner session artifacts are durable and auditable
- ExecPlan remains a contract artifact for governed implementation work
- external PM systems exist for project-manager visibility rather than workflow authority
- no UI is desired; the system is terminal-first
- no hidden memory or hidden operational state is acceptable
- no direct code-writing path should exist from planner ideation mode
- GitHub Projects is the only explicit external sync target in this design phase, and only as scaffold/spec rather than live integration
- selective pullback is acceptable in principle, but unresolved sync conflicts default to local canonical state

Proposed CLI direction for design:

- `bin/planner session start`
- `bin/planner session chat`
- `bin/planner session show`
- `bin/planner session summarize`
- `bin/planner graph build`
- `bin/planner graph show`
- `bin/planner graph ready`
- `bin/planner graph blocked`
- `bin/planner graph validate`
- `bin/planner contract draft-execplan`
- `bin/planner contract show`
- `bin/planner validate`
- `bin/planner sync github-projects`

Design assumptions about this CLI:

- `planner` is the top-level command surface.
- `session chat` opens an interactive terminal session with Codex-style conversational flow rather than acting as a single-shot prompt command.
- the planner may use governed internal roles for critique, synthesis, and contract drafting, but those roles cannot become hidden authorities or hidden state.
- `graph build` derives or refreshes canonical graph state from planner session artifacts.
- `contract draft-execplan` generates a governed contract draft only when readiness conditions are satisfied.
- no `execute` command is included in this design phase because execution authority is intentionally not defined here.

## Plan of Work

The work should proceed in five layers, each building on the previous layer and reducing ambiguity rather than spreading it around:

1. Define boundaries and invariants.
   Specify what the planner control plane owns, what it projects, and what it explicitly does not do.
2. Define canonical structures.
   Specify planner session artifacts, canonical task graph schema, and state transitions with enough rigor to support validation and later provider adapters.
3. Define projections and interfaces.
   Specify how canonical state becomes ExecPlan drafts, summaries, validation targets, and downstream sync payloads without allowing projections to become sources of truth.
4. Define operator surface.
   Specify `bin/planner` command semantics, interactive terminal behavior, prompt families, output artifacts, and validation expectations.
5. Define implementation runway.
   Produce ADRs, prompt additions, and a phase-2 backlog that can be executed later under existing governance.

This design must prefer explicit schema, artifact paths, transition rules, and command contracts over prose-only explanation.

## Concrete Steps

1. Review current governance and workflow artifacts that constrain planner design:
   - `docs/execplans.md`
   - `docs/prompts.md`
   - `spec/workflow.yaml`
   - `examples/execplan-template.md`
   - `src/platform_tools/plan_utils.py`
2. Write a planner control-plane architecture spec that defines planner responsibilities, graph responsibilities, ExecPlan responsibilities, validation boundaries, external sync boundaries, and non-goals for this phase.
3. Write a canonical task graph schema spec that defines node types, edge types, status model, provenance and evidence fields, external reference model, validation invariants, and lifecycle transitions.
4. Write a planner session artifact spec that defines session identity, transcript storage expectations, extracted structured state, relationship to graph build inputs, artifact directories, naming, and no-hidden-state guarantees.
5. Write a CLI contract spec for `bin/planner` that defines command groups, interactive `session chat` behavior, `graph build` semantics, `graph show` and readiness views, `contract draft-execplan` readiness expectations, `sync github-projects` limitations, and top-level `validate` behavior.
6. Write an ExecPlan projection and handoff spec that defines readiness thresholds for contract drafting, required mapping from planner and graph state into ExecPlan headings and frontmatter, unresolved-question handling, operator review expectations, and relationship between contract artifacts and local canonical state.
7. Write a GitHub Projects adapter scaffold spec that defines provider-agnostic adapter expectations, one-way and selective-pull assumptions, local-wins default conflict posture, field mapping boundaries, and explicit placeholder status for Jira and Microsoft Lists.
8. Add planner/control-plane prompt catalog artifacts that define direct/adversarial planning behavior, synthesis behavior, contract drafting behavior, critique behavior, and expected inputs and outputs for each prompt family.
9. Write an ADR documenting the architectural rule that canonical graph state is the source of truth, planner artifacts are durable local records, ExecPlan is contract projection, and external systems are downstream views only.
10. Produce a phase-2 implementation backlog with sequenced follow-on work packages for planner session runtime, graph persistence and validation, CLI implementation, ExecPlan drafting implementation, provider adapter scaffolding, and future provider placeholders.
11. Run governance validation and adjust design artifacts until they comply with repository rules.

## Validation and Acceptance

This design phase is accepted only if all of the following are true:

- A reviewer can identify the canonical source of truth, planner boundaries, graph boundaries, and ExecPlan boundaries without inference.
- The task graph schema is specific enough to support future provider adapters without redesigning core entities.
- The planner session artifact model is explicit enough that no hidden state is required.
- The CLI contract is explicit enough that implementation can begin without guessing command intent.
- `session chat` is clearly defined as interactive terminal behavior rather than ambiguous single-shot invocation.
- The ExecPlan projection model clearly defines when planning state is ready to become governed execution work.
- The GitHub Projects sync design is constrained to scaffold/spec scope and does not imply provider authority.
- Prompt additions are cataloged as governed artifacts and tied to planner objectives.
- The ADR states the canonical architectural decision in durable form.
- The phase-2 backlog is concrete enough to turn into one or more follow-on ExecPlans.

Validation commands:

1. `bin/execplan-validate .agent/execplans/20260310-planner-control-plane-design-codex-01-execplan.md`
2. `bin/sync-todos`
3. `bin/repo-health-check`
4. `bin/execplan-test`

Additional manual review checks:

- verify that no design artifact implies UI dependency
- verify that no design artifact permits direct code-writing from planner ideation mode
- verify that graph semantics remain local and provider-agnostic
- verify that unresolved questions are either answered in the design package or explicitly deferred to phase 2
- verify that sync conflict posture does not weaken local canonical authority

## Idempotence and Recovery

This plan is architecture and document focused, so reruns should be safe if these rules are maintained:

- design artifacts are updated in place with decision log entries when assumptions change
- unresolved questions are tracked explicitly rather than overwritten silently
- generated summaries and backlog documents are reproducible from the authoritative design artifacts
- if a design direction is reversed, the ADR and affected specs are updated in the same change set to avoid architectural split-brain

If partial work is completed, recovery consists of:

- reviewing completed design artifacts against the task list
- re-opening unresolved design questions in the decision log
- re-running validation tools after each material spec update
- ensuring TODO synchronization reflects current design work state

## Artifacts and Notes

Expected artifacts to create during execution:

- planner control-plane architecture spec
- planner game model spec
- implementation game model spec
- move-transition spec
- scoring model spec
- bibliography graph spec and artifact
- assumptions and design-inference register
- canonical task graph schema spec
- planner session artifact spec
- CLI contract spec for `bin/planner`
- ExecPlan projection and handoff spec
- GitHub Projects adapter scaffold spec
- prompt catalog additions for planner/control-plane work
- ADR for graph canonicality and ExecPlan projection
- implementation backlog for phase 2

Likely artifact locations:

- `docs/`
- `spec/`
- `prompts/`
- `.agent/execplans/`

Open design questions intentionally left for this plan to resolve:

- exact planner session artifact layout and file naming
- readiness threshold for `contract draft-execplan`
- transcript retention versus summary retention policy
- exact sync metadata required in canonical graph schema
- whether top-level `bin/planner validate` aggregates sub-validators or remains planner-specific

## Interfaces and Dependencies

Primary existing dependencies:

- ExecPlan lifecycle rules in `docs/execplans.md`
- prompt governance model in `docs/prompts.md`
- workflow lifecycle policy in `spec/workflow.yaml`
- required headings and frontmatter enforced by `src/platform_tools/plan_utils.py`
- existing command surface under `bin/`

Planned interfaces to define:

- planner session artifact interface
- canonical task graph schema interface
- planner CLI contract
- ExecPlan projection contract
- provider adapter contract

External provider dependency stance for this phase:

- GitHub Projects: scaffold/spec only
- Jira: placeholder only
- Microsoft Lists: placeholder only

Non-negotiable constraints:

- no UI
- no hidden state
- no external system as source of truth
- no direct code-writing path from planner ideation mode
- planner default tone is hard/direct unless explicitly overridden
