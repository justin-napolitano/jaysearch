# Governance Loader

This engine supports two runtime modes:

- `standalone`: use local governance specs from this repository.
- `managed`: load external governance baseline and merge with local codex overlays.

Runtime config file: `platform.engine.yaml`.

Environment overrides:

- `PLATFORM_ENGINE_MODE`
- `PLATFORM_GOVERNANCE_SOURCE`
- `PLATFORM_PROJECT_RULES_SOURCE`

Deterministic precedence:

1. External baseline (managed mode only).
2. Local codex overlays.
3. Project overlay (`project.rules.yaml` by default).

Managed mode non-weakening rule:

- Local policy may tighten baseline controls.
- Local policy may not remove required baseline checks.

Project overlay rule:

- Overlay may add required checks and forbidden branches.
- Overlay may remove allowed branch patterns (tighten).
- Overlay may not remove required checks or forbidden branches.

Validation commands:

- `bin/governance-loader-check`
- `PLATFORM_ENGINE_MODE=managed PLATFORM_GOVERNANCE_SOURCE=test-vectors/governance/managed-profile-pass.yaml bin/governance-loader-check`
- `bin/bootstrap-profile-check`
