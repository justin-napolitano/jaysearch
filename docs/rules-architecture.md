# Rules Architecture

This repository separates rules into three layers:

1. `spec/` machine-checkable canonical contracts
2. `policy/` concise normative governance text
3. `docs/` explanatory and onboarding material

If a rule is enforced by code, it must be defined in `spec/`.

Canonical rule inventory:

- `spec/rule-registry.yaml` is the canonical machine-readable inventory of active rules and their enforcement class.
- `artifacts/planner/research/rule-graph.json` is a validated projection over that registry.
- `docs/` may explain rules, but must not be the only normative source for an enforced rule.

## Locked Platform Architecture Contract

Canonical contract file: `spec/platform-architecture.yaml`

Architecture boundaries:

- `platform_core`: implementation logic only in `src/platform_tools/**`
- `operator_entrypoints`: `bin/**` wrappers only; they delegate to `src/platform_tools/*`
- `governance_contracts`: `spec/**`, `policy/**`, `.agent/execplans/**`
- `docs_guidance`: `docs/**` explanation and runbooks

Precedence contract:

- conflict resolution is fixed as `spec > policy > docs`
- validators and automation must follow `spec` when text conflicts exist

Authority contract:

- bypass approvals are human-only, time-bounded, and owner-attributed
- execplan finalization is human-only and SSH-signed
