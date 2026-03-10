# Template Maintenance

This repository is the canonical template for new Codex-operated projects.

Changes to the template follow:

ExecPlan -> ADR -> Template Update

## Operating Model

- New repositories start from this template as snapshots.
- Spawned repositories do not receive upstream changes automatically.
- Template improvements are synced intentionally into existing projects when they are worth adopting.
- Shared packages should only be introduced for stable, repeated logic that no longer belongs at the repo-template layer.

## Ownership Guidance

Treat these areas as template-first in most repositories:

- `.agent/`
- `bin/`
- `spec/`
- `policy/`
- core platform docs
- core platform tooling under `src/platform_tools/`

Treat product code, content, assets, and deployment specifics as project-owned unless a project explicitly chooses to keep them aligned with the template.

## Distribution Contracts

- Version contract source: `pyproject.toml` (`project.version`).
- Release registry: `.agent/distribution/releases.yaml`.
- Distribution validation: `bin/distribution-check`.

## Sync Policy

Template improvements should be pulled into existing projects intentionally. Do not assume automatic updates between this repository and spawned repositories.

## Manual Update Mechanics

1. Create a dedicated non-`main` branch.
2. Update template files and `.agent/distribution/releases.yaml`.
3. Run `bin/distribution-check`.
4. Run `bin/run-local-ci`.
5. Open a reviewable PR and require human merge.
