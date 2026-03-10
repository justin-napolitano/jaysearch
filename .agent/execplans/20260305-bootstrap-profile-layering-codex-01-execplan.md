---
id: 20260305-bootstrap-profile-layering-codex-01-execplan
title: Formalize bootstrap profiles and project rule layering contract
owner: "agent/codex-01"
created: "2026-03-05T00:00:00Z"
status: executing
base_branch: main
changes:
  - .agent/execplans/20260305-bootstrap-profile-layering-codex-01-execplan.md
  - prompts/20260305-execute-bootstrap-profile-layering-codex-01.md
  - spec/bootstrap-profiles.yaml
  - spec/rule-layering.yaml
  - .agent/bootstrap-manifest.json
  - project.rules.yaml
  - platform.engine.yaml
  - src/platform_tools/bootstrap_project.py
  - src/platform_tools/bootstrap_profile_check.py
  - src/platform_tools/governance_loader.py
  - src/platform_tools/run_local_ci.py
  - bin/bootstrap-profile-check
  - docs/getting-started.md
  - docs/governance-loader.md
  - docs/commands.md
  - pyproject.toml
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/bootstrap-profile-layering-execution-codex-01-20260305"
draft_created: "2026-03-05T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: bootstrap_profile_check
      command: bin/bootstrap-profile-check
      expected_exit: 0
    - name: governance_loader_standalone
      command: bin/governance-loader-check
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
  - title: Formalize bootstrap output profiles as machine-readable contract
    priority: P1
  - title: Emit deterministic bootstrap manifest for generated repositories
    priority: P1
  - title: Add bootstrap profile validator for contract conformance
    priority: P1
  - title: Add project rule layering file with tighten-only semantics
    priority: P1
  - title: Enforce project-rule non-weakening in governance loader
    priority: P1
---

# Purpose / Big Picture

Make bootstrap deterministic and profile-driven, and allow project-specific rules without weakening baseline governance.

## Progress

- [x] Create bootstrap-profile-layering plan
- [x] Implement bootstrap profile + manifest contracts
- [x] Implement project rule layering and non-weakening checks
- [x] Validate deterministic behavior
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

Manual post-bootstrap deletions create drift and should be replaced by explicit profile contracts.

## Decision Log

Decision: bootstrap output must be profile-defined and validated; project rules may tighten or extend but not weaken baseline.

Rationale: gives repeatable scaffolding while preserving governance guarantees.

Date/Author: 2026-03-05 / agent/codex-01

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

Bootstrap and governance layering are now treated as first-class contracts instead of ad hoc conventions.

## Plan of Work

1. Add bootstrap profile and manifest contract.
2. Add validator for profile conformance.
3. Add tighten-only project rule layering.
4. Integrate checks into CI command flow.

## Concrete Steps

1. Create profile spec and default manifest.
2. Add `bootstrap-profile-check` command.
3. Extend bootstrap command with `--profile`.
4. Add `project.rules.yaml` and governance loader merge rules.
5. Run deterministic validation sequence.

## Validation and Acceptance

Accepted when bootstrap output is profile-governed, profile conformance is checkable, and project overlay weakening is rejected deterministically.

## Idempotence and Recovery

Bootstrap with `--force` and profile validation are rerunnable and deterministic for fixed inputs.

## Artifacts and Notes

- `.agent/execplans/20260305-bootstrap-profile-layering-codex-01-execplan.md`
- `prompts/20260305-execute-bootstrap-profile-layering-codex-01.md`

## Interfaces and Dependencies

Interfaces:

- `spec/*`
- `src/platform_tools/*`
- `bin/*`
- `docs/*`

Dependencies:

- `20260305-governance-dual-mode-loader-codex-01-execplan`
