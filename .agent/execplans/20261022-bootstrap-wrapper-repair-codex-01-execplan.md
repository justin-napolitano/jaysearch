---
id: 20261022-bootstrap-wrapper-repair-codex-01-execplan
title: Restore three missing canonical bootstrap wrappers
owner: agent/codex-01
created: 2026-10-22T15:25:00Z
status: draft
base_branch: main
initiative_branch: initiative/unified-brand-20261022
initiative_node_id: initiative-unified-brand-20261022
approve_policy: codeowners
reviewers: [github:justin-napolitano]
changes:
  - bin/get-control-plane-status
  - bin/control-plane-api-check
  - bin/public-orchestration-api-check
---

## Outcomes & Retrospective

Routine prerequisite repair authorized by the rollout coordinator within the user-requested swarm. No human finalization or policy change.

## Context and Orientation

Existing bootstrap fails solely on these missing wrappers after registering branding initiative. All corresponding Python modules already exist. Peer wrappers use bash, repository src PYTHONPATH, and python3 -m with forwarded arguments.

## Plan of Work

Restore the exact peer pattern for the three missing command wrappers; make only new wrappers executable. Do not alter module behavior, governance policies, checks, branch protection, or dependencies. Re-run bootstrap using the existing platform virtualenv (system Python lacks yaml).

## Validation and Acceptance

Invoke module-backed wrapper help where supported and bootstrap with the explicit branding initiative plan. Preserve output and report any remaining blockers without weakening checks.

## Artifacts and Notes

The bounded branding plan remains initiative authority for its worker. This prerequisite draft records infrastructure-neutral command restoration only. Revert this focused commit to recover.
