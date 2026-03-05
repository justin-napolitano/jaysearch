# Governance Loader

This engine supports two runtime modes:

- `standalone`: use local governance specs from this repository.
- `managed`: load external governance baseline and merge with local codex overlays.

Runtime config file: `platform.engine.yaml`.

Environment overrides:

- `PLATFORM_ENGINE_MODE`
- `PLATFORM_GOVERNANCE_SOURCE`

Deterministic precedence:

1. External baseline (managed mode only).
2. Local codex overlays.

Managed mode non-weakening rule:

- Local policy may tighten baseline controls.
- Local policy may not remove required baseline checks.

Validation commands:

- `bin/governance-loader-check`
- `PLATFORM_ENGINE_MODE=managed PLATFORM_GOVERNANCE_SOURCE=test-vectors/governance/managed-profile-pass.yaml bin/governance-loader-check`
