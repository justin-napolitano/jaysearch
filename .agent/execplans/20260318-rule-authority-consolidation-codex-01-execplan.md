---
id: "20260318-rule-authority-consolidation-codex-01-execplan"
title: "Consolidate canonical rule authority and align enforcement surfaces"
owner: "agent/codex-01"
created: "2026-03-18T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260318-rule-authority-consolidation-codex-01-execplan.md
  - artifacts/planner/research/rule-graph.json
  - docs/agent-capability-boundaries.md
  - docs/platform-definition-v1.md
  - docs/platform-overview.md
  - docs/repo-health.md
  - docs/todos.md
  - spec/agent-capability-policy.yaml
  - spec/governance.yaml
  - spec/rule-graph.schema.yaml
  - spec/rule-registry.yaml
  - src/platform_tools/anti_cheat_check.py
  - src/platform_tools/governance_check.py
  - src/platform_tools/repo_health.py
  - src/platform_tools/rule_graph_check.py
  - tests/test_anti_cheat_check.py
  - tests/test_governance_check.py
  - tests/test_repo_health.py
  - tests/test_rule_graph_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260318-rule-authority-consolidation-codex-01-20260318"
draft_created: "2026-03-18T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260318-rule-authority-consolidation-codex-01-execplan.md"
      expected_exit: 0
    - name: "rule-graph-check"
      command: "bin/rule-graph-check"
      expected_exit: 0
    - name: "governance-check"
      command: "bin/governance-check"
      expected_exit: 0
tasks:
  - title: "Add canonical rule registry and classify active rules by enforceability"
    priority: "P1"
  - title: "Make capability policy complete for documented draft and implementation branch classes"
    priority: "P1"
  - title: "Normalize governance check identifiers across spec, validators, and command surface"
    priority: "P1"
  - title: "Deprecate TODO as a required health invariant in favor of canonical graph state"
    priority: "P1"
  - title: "Reconcile platform docs and repo-health gates to current machine-readable authority"
    priority: "P1"
depends_on:
  - "20260310-rule-graph-codex-01-execplan"
  - "20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan"
  - "20260316-anti-cheat-capability-enforcement-codex-01-execplan"
---

# Purpose / Big Picture

Consolidate the repository's rule system so every active rule is either machine-readable and enforceable, explicitly human-gated with machine-detectable escalation semantics, or formally marked as backlog or deprecated.

This slice exists because the repository already has a partial rule graph and later audit work, but newer governance, capability, and projection rules have drifted outside that inventory. The result is contract inconsistency: real checks enforce rules that the canonical rule inventory does not fully enumerate, and some obsolete invariants still block health despite no longer being authoritative.

## Progress

- [ ] Add a canonical rule registry in `spec/`
- [ ] Expand the rule graph from partial inventory to validated projection of the active rule registry
- [ ] Close capability-policy gaps for documented draft and implementation workflows
- [ ] Normalize governance check identifiers and required-check mappings
- [ ] Remove TODO completeness as a required health gate if graph state is canonical
- [ ] Reconcile platform docs and health reporting with the live enforcement model
- [ ] Validate the slice

## Surprises & Discoveries

- The repository already has a machine-readable rule-inventory phase-1 implementation through `spec/rule-graph.schema.yaml`, `artifacts/planner/research/rule-graph.json`, and `bin/rule-graph-check`, but that inventory is intentionally partial.
- The later rules-engine audit already recognized that several rule domains remain only partially explicit and that newer game and governance surfaces were not yet folded back into one complete inventory.
- `bin/governance-check` currently emits high-noise findings because canonical check identifiers and executable command names are being conflated.
- `TODO.md` appears to have become a deprecated projection now that remaining-work and related graph artifacts are the canonical work surface.

## Decision Log

- 2026-03-18 / agent-codex-01 / The repository should move from a partial rule graph to a complete canonical rule registry plus validated graph projection.
- 2026-03-18 / agent-codex-01 / Machine-enforced rule identifiers should be canonicalized independently from CLI command names.
- 2026-03-18 / agent-codex-01 / Deprecated projections such as TODO must not remain blocking health invariants once canonical graph state supersedes them.
- 2026-03-18 / agent-codex-01 / Documented branch classes must have complete capability coverage so valid governed workflows cannot fail due to missing policy rows.

## Outcomes & Retrospective

On completion, the repository should have:

- one canonical machine-readable rule registry
- one validated rule-graph projection derived from that registry
- complete capability coverage for documented branch and goal-area classes
- one normalized governance check identifier scheme
- repo-health and merge-readiness gates aligned to active canonical authority
- explicit deprecation of TODO as a required projection if the graph is canonical
- docs that explain current enforcement rather than preserve historical gap narratives

Expected implemented outcome:

- every active enforced rule is registered, scoped, and mapped to a referee or human-gated authority boundary
- no checker enforces an unregistered rule
- no deprecated projection remains a required health invariant
- the repository can detect rule drift mechanically rather than through manual review

## Context and Orientation

The repository's current rule system evolved in phases:

- phase 1 added a rule graph for major merge-readiness rules
- phase 2 added a rules-engine audit and broader game hierarchy analysis
- later governance work introduced capability policy, anti-cheat, state-transition, remaining-work ordering, and board/projection rules

Those newer rule surfaces are real, but they are not all represented in one canonical inventory. This slice reconciles that drift by making rule authority explicit and complete.

## Plan of Work

1. Inventory active rules across specs, validator runtimes, and governed docs.
2. Add a canonical `spec/rule-registry.yaml` with rule ids, classes, scopes, authorities, enforcement mappings, and deprecation status.
3. Update the rule-graph schema and validator so the graph becomes a projection over the rule registry rather than a hardcoded seven-rule set.
4. Fix capability-policy completeness for documented draft and implementation branch classes.
5. Normalize required-check identifiers in governance so machine ids and command strings are no longer conflated.
6. Reclassify TODO from required invariant to deprecated or optional projection if canonical graph state supersedes it.
7. Update repo-health and platform docs to follow the reconciled rule authority.

## Concrete Steps

1. Add `spec/rule-registry.yaml` with at least:
   - rule id
   - rule class (`enforced`, `derived`, `human_gated`, `backlog`, `deprecated`)
   - scope
   - authority class
   - source artifacts
   - enforced-by commands or human-gated boundary
   - blocking semantics
2. Move the current rule-graph coverage into the registry and add newer rule domains, including:
   - governance required-check contract rules
   - capability-policy rules
   - anti-cheat / protected-surface rules
   - remaining-work ordering and projection-authority rules
   - TODO deprecation status
3. Update `src/platform_tools/rule_graph_check.py` to validate graph completeness against the registry instead of a hardcoded required-rule list.
4. Update `spec/agent-capability-policy.yaml` and related runtime/tests so documented draft-governance workflows have explicit capability coverage.
5. Update `spec/governance.yaml` and `src/platform_tools/governance_check.py` so canonical check ids are normalized and command strings remain separate executable mappings.
6. Update `src/platform_tools/repo_health.py` and docs so TODO is no longer a required health invariant if the graph is canonical.
7. Rewrite the affected docs to describe current enforcement and deprecation state explicitly.

## Validation and Acceptance

Acceptance criteria:

- every active enforced rule has an entry in `spec/rule-registry.yaml`
- the rule graph validator fails when an enforced registry rule is missing from the graph projection
- valid documented draft-governance branches no longer fail due to `missing_capability_rule`
- `bin/governance-check` no longer fails due to naming-format drift between canonical ids and CLI commands
- repo health does not fail solely because `TODO.md` is incomplete if TODO is deprecated
- platform docs no longer describe obsolete required invariants or missing implementations that are no longer true

## Idempotence and Recovery

- rerunning the inventory and projection validators should be deterministic for the same repo state
- the migration from partial rule graph to registry-backed projection must not remove existing rule coverage while new entries are being added
- if a rule cannot yet be fully enforced, the registry must classify it explicitly rather than silently leaving it prose-only

## Artifacts and Notes

Expected artifacts:

- `spec/rule-registry.yaml`
- updated `spec/rule-graph.schema.yaml`
- updated `artifacts/planner/research/rule-graph.json`
- updated `spec/agent-capability-policy.yaml`
- updated `spec/governance.yaml`
- updated health and validation runtimes

Planned implementation branch:

- `impl-execplan/20260318-rule-authority-consolidation-codex-01-execplan-codex-01-20260318`

## Interfaces and Dependencies

Primary interfaces:

- `spec/rule-registry.yaml`
- `spec/rule-graph.schema.yaml`
- `artifacts/planner/research/rule-graph.json`
- `spec/governance.yaml`
- `spec/agent-capability-policy.yaml`
- `src/platform_tools/rule_graph_check.py`
- `src/platform_tools/governance_check.py`
- `src/platform_tools/repo_health.py`
- `src/platform_tools/anti_cheat_check.py`

Primary dependencies:

- the existing rule-graph and rules-engine audit slices
- the active capability-policy and anti-cheat surfaces
- canonical graph authority remaining downstream from docs and projections
