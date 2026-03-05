
# Template Maintenance

Changes to the platform follow:

ExecPlan → ADR → Template Update

Distribution contracts:

- Version contract source: `pyproject.toml` (`project.version`).
- Release registry: `.agent/distribution/releases.yaml`.
- Distribution validation: `bin/distribution-check`.

Deterministic template sync and drift controls:

- Required template paths are declared in `spec/distribution.yaml`.
- Active release entry must include exact template path set.
- Drift is detected when required template paths differ from active release registry paths.

Manual enterprise-safe update mechanics:

1. Create a dedicated non-`main` branch.
2. Update template files and `.agent/distribution/releases.yaml`.
3. Run `bin/distribution-check`.
4. Run `bin/run-local-ci`.
5. Open a reviewable PR and require human merge.
