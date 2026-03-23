---
id: "20260323-governed-super-agent-harness-research-codex-01-execplan"
title: "Research DeerFlow-style runtime capabilities before committing to a governed super-agent harness architecture"
owner: "agent/codex-01"
created: "2026-03-23T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260323-governed-super-agent-harness-research-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/bibliography-graph.json
  - artifacts/planner/research/claim-registry.json
  - artifacts/planner/research/remaining-work-graph.json
  - docs/agent-framework-comparison.md
  - docs/best-practices-for-agent-runtime-design.md
  - docs/bridge-contracts-between-runtime-and-kernel.md
  - docs/governed-super-agent-harness-research.md
  - docs/kernel-contract-draft.md
  - docs/kernel-vs-dev-harness-separation.md
  - docs/kernel-first-platform-direction.md
  - docs/microsoft-agent-framework-deep-dive.md
  - docs/references.md
  - docs/research-assumptions.md
  - docs/session-governance-platform-thesis.md
  - docs/terminal-first-platform-direction.md
  - docs/queued-execplans.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/governed-super-agent-harness"
initiative_node_id: "initiative-governed-super-agent-harness"
graph_registration:
  node_id: "rwg-038"
  queue_position: 38
  goal_area: "integration"
  conflict_domains:
    - "research-governance"
    - "super-agent-harness"
  expected_artifacts:
    - ".agent/execplans/20260323-governed-super-agent-harness-research-codex-01-execplan.md"
    - "docs/agent-framework-comparison.md"
    - "docs/best-practices-for-agent-runtime-design.md"
    - "docs/bridge-contracts-between-runtime-and-kernel.md"
    - "docs/governed-super-agent-harness-research.md"
    - "docs/kernel-contract-draft.md"
    - "docs/kernel-vs-dev-harness-separation.md"
    - "docs/kernel-first-platform-direction.md"
    - "docs/microsoft-agent-framework-deep-dive.md"
    - "docs/references.md"
    - "docs/research-assumptions.md"
    - "docs/session-governance-platform-thesis.md"
    - "docs/terminal-first-platform-direction.md"
    - "artifacts/planner/research/bibliography-graph.json"
    - "artifacts/planner/research/claim-registry.json"
  implementation_branch: "impl-execplan/20260323-governed-super-agent-harness-research-codex-01-20260323"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260323-governed-super-agent-harness-research-codex-01-20260323"
draft_created: "2026-03-23T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260323-governed-super-agent-harness-research-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Capture the current capability overlap and gaps between this repo and DeerFlow"
    priority: "P1"
  - title: "Separate source-backed DeerFlow facts from platform-specific design inferences"
    priority: "P1"
  - title: "Define the research questions that must be answered before architecture commitment"
    priority: "P1"
  - title: "Preserve the results in durable local research artifacts"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Create a durable research package for the DeerFlow-inspired governed super-agent harness idea before the repository commits to a concrete runtime architecture or implementation sequence.

## Progress

- [ ] capture source-backed DeerFlow capabilities relevant to this repository
- [ ] compare those capabilities against the current platform kernel
- [ ] record design inferences, policy choices, and open assumptions explicitly
- [ ] identify research questions that must be answered before planning expands into implementation slices
- [ ] define the kernel-first direction that keeps Git and GitHub as the durable integration substrate
- [ ] define the permanent terminal-first UX posture explicitly
- [ ] restate the platform thesis around governance, session orchestration, auditability, graphs, plans, and hostile review
- [ ] draft the kernel contract without pretending the design is settled

## Surprises & Discoveries

- the most important gap is not generic planning capability; it is the runtime product surface around skills, tools, memory, sandboxing, and user-facing service ingress
- the repo already has stronger canonical-state and governance properties than DeerFlow in several areas, which means direct imitation would likely weaken the system unless carefully adapted
- some attractive DeerFlow features may create hidden-state risks if they are adopted without explicit reconciliation rules

## Decision Log

- keep this slice research-only
- preserve the earlier planning spike as a separate decision-gated artifact rather than silently expanding it
- treat DeerFlow as an input to compare against, not a blueprint to transplant directly
- require source-backed versus inferred claims to remain explicit in the resulting research package

## Outcomes & Retrospective

- expected outcome: the repo has a reusable research document and provenance trail for future architecture decisions
- expected retrospective question: whether the research package narrows the space enough to justify a smaller set of follow-on planning slices

## Context and Orientation

- DeerFlow is compelling because it offers an integrated runtime harness with skills, tools, subagents, memory, sandboxing, and user-facing service surfaces
- this repository currently behaves more like a governed kernel than a batteries-included agent runtime
- the design challenge is to decide what should be adopted, what should be adapted, and what should be rejected because it conflicts with local invariants
- the emerging direction is a standard kernel layer that works extremely well with Git and GitHub and can host multiple runtime/harness choices above it

## Plan of Work

1. document DeerFlow-relevant capabilities in source-backed language
2. compare those capabilities against the current platform shape
3. identify the highest-risk architectural questions before commitment
4. define the kernel-first model that keeps runtime choices pluggable
5. preserve the result in canonical local research artifacts

## Concrete Steps

1. add a research document that records capability overlap, gaps, and open questions
2. add comparison and design notes for framework selection, runtime best practices, bridge contracts, and kernel-first platform direction
3. add DeerFlow as an explicit reference in the repository research package
4. update the assumptions and claim artifacts so future planning can distinguish source-backed facts from design inference
5. register the research slice in the remaining-work graph so it is not lost

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260323-governed-super-agent-harness-research-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes after the node is registered
- the resulting research package must not imply implementation readiness
- the resulting research package must make open questions more explicit, not less

## Idempotence and Recovery

- rerunning this slice should be safe because it only updates planning and research artifacts
- if later research changes the comparison materially, the research doc and provenance artifacts should be updated rather than overwritten implicitly by implementation work
- if DeerFlow evolves further, future updates should record the date and source used rather than relying on memory

## Artifacts and Notes

- external comparison target: `https://github.com/bytedance/deer-flow`
- this slice intentionally produces research, not a runtime scaffold
- future architecture and planning work should cite this slice rather than reconstructing the comparison from memory

## Interfaces and Dependencies

- this slice touches only planning and research artifacts
- it should inform, but not automatically trigger, later architecture or implementation planning
- likely follow-on consumers include the governed super-agent harness planning spike and any later runtime-contract planning artifacts
