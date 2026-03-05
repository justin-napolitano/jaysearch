---
id: 20260305-governance-dual-mode-loader-codex-01-execplan
title: Add dual-mode governance loader for standalone and managed operation
owner: "agent/codex-01"
created: "2026-03-05T00:00:00Z"
status: executing
base_branch: main
changes:
  - .agent/execplans/20260305-governance-dual-mode-loader-codex-01-execplan.md
  - prompts/20260305-execute-governance-dual-mode-loader-codex-01.md
  - spec/engine-runtime.yaml
  - platform.engine.yaml
  - src/platform_tools/governance_loader.py
  - src/platform_tools/branch_policy.py
  - src/platform_tools/governance_check.py
  - src/platform_tools/run_local_ci.py
  - bin/governance-loader-check
  - docs/governance-loader.md
  - docs/commands.md
  - docs/local-dev.md
  - policy/README.md
  - test-vectors/governance/managed-profile-pass.yaml
  - test-vectors/governance/managed-profile-fail.yaml
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/governance-dual-mode-loader-codex-01-20260305"
draft_created: "2026-03-05T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: governance_loader_standalone
      command: bin/governance-loader-check
      expected_exit: 0
    - name: governance_loader_managed
      command: PLATFORM_ENGINE_MODE=managed PLATFORM_GOVERNANCE_SOURCE=test-vectors/governance/managed-profile-pass.yaml bin/governance-loader-check
      expected_exit: 0
    - name: execplan_validate
      command: bin/execplan-validate .agent/execplans/*.md
      expected_exit: 0
    - name: repo_health_check
      command: bin/repo-health-check
      expected_exit: 0
    - name: run_local_ci
      command: bin/run-local-ci
      expected_exit: 0

tasks:
  - title: Define engine runtime mode contract for standalone and managed governance
    priority: P1
  - title: Implement governance loader normalization and deterministic precedence
    priority: P1
  - title: Enforce non-weakening merge rules for local codex overlays against external baseline
    priority: P1
  - title: Refactor core validators to consume effective loaded policy
    priority: P1
  - title: Add deterministic regression coverage for standalone and managed modes
    priority: P1

depends_on:
  - 20260305-platform-adoption-pilot-codex-01-execplan
---

# Purpose / Big Picture

Enable this platform engine to run in two explicit modes without policy drift:

- `standalone`: self-contained default governance
- `managed`: external organization governance baseline + local codex overlays

## Progress

- [x] Create dual-mode loader plan
- [x] Define mode contract and precedence model
- [x] Implement loader and validator integration
- [x] Add regression coverage for both modes
- [x] Validate deterministic outputs and exit codes
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

Using both internal and external governance contracts without a deterministic merge policy creates silent weakening risk.

## Decision Log

Decision: external governance baseline remains authoritative in managed mode; local codex policy may only tighten controls.

Rationale: preserves organization governance guarantees while allowing codex-specific specialization.

Date/Author: 2026-03-05 / agent/codex-01

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

The current platform enforces strong local contracts, and `git-tools` provides organization-level governance scaffolding. This plan introduces a deterministic loader layer so both can coexist safely and predictably.

## Plan of Work

1. Define runtime configuration contract for mode selection and governance source.
2. Implement governance loader + merge rules.
3. Integrate effective policy consumption into validators.
4. Add deterministic test coverage for standalone and managed execution.
5. Update docs and operator runbook.

## Concrete Steps

1. Add runtime mode spec/config:
   - mode enum (`standalone`, `managed`)
   - governance source path/identifier
   - deterministic precedence declaration
2. Implement loader module under `src/platform_tools/*`:
   - parse local defaults
   - optionally parse external governance profile
   - normalize into effective policy object
3. Enforce merge contract:
   - local overlays may tighten only
   - weakening attempts fail with machine-readable finding
4. Refactor existing checks (`branch`, `governance`, `distribution`, `adoption`, `health`, `ci`) to consume effective policy.
5. Add regression tests/vectors for both modes and run deterministic command sequence.

## Validation and Acceptance

Accepted when:

- engine runs in standalone mode with no external governance dependency;
- managed mode loads external governance and merges deterministically;
- weakening conflicts fail deterministically with stable machine-readable findings;
- validators and CI continue producing deterministic JSON and stable exit codes.

## Idempotence and Recovery

Loader and merge logic are pure read/normalize operations. Re-running checks is safe and must yield stable output for stable inputs.

## Artifacts and Notes

- `.agent/execplans/20260305-governance-dual-mode-loader-codex-01-execplan.md`
- `prompts/20260305-execute-governance-dual-mode-loader-codex-01.md`
- `spec/engine-runtime.yaml`
- `platform.engine.yaml`
- `src/platform_tools/governance_loader.py`
- `bin/governance-loader-check`
- `docs/governance-loader.md`

## Interfaces and Dependencies

Interfaces:

- `spec/engine-runtime.yaml`
- `platform.engine.yaml`
- `src/platform_tools/governance_loader.py`
- `src/platform_tools/branch_policy.py`
- `src/platform_tools/governance_check.py`
- `src/platform_tools/run_local_ci.py`
- `bin/governance-loader-check`
- `docs/governance-loader.md`
- `policy/README.md`

Dependencies:

- `20260305-platform-adoption-pilot-codex-01-execplan`
