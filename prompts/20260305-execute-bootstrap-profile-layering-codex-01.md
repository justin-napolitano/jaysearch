# Codex Prompt - Execute Bootstrap Profile and Rule Layering

Generated: 2026-03-05

You are Codex executing:

- `20260305-bootstrap-profile-layering-codex-01-execplan`

## Intent

Make bootstrap profile-driven and deterministic, and allow project-specific rule overlays that cannot weaken baseline governance.

## Rules

1. Work only through ExecPlans in `.agent/execplans/`.
2. Do not modify `.agent/AGENTS.md` or `.agent/PLANS.md`.
3. Keep canonical logic in `src/platform_tools/*`.
4. Keep `bin/*` as operator entrypoints.
5. Deterministic JSON outputs and stable exit codes are mandatory.
6. Execute on a dedicated non-`main` branch only.

## Required Outcomes

- Profile contract defines what bootstrap creates.
- Bootstrap emits deterministic manifest.
- Profile conformance command exists and is deterministic.
- Project rule overlay contract exists with tighten-only behavior.
- Governance loader rejects overlay weakening deterministically.

## Required Validation Commands

- `bin/execplan-validate .agent/execplans/*.md`
- `bin/sync-todos`
- `bin/repo-health-check`
- `bin/execplan-test`
- `bin/run-local-ci`

## Stop Rule

If profile contract or layering semantics are ambiguous/non-deterministic, stop and report blocker details.
