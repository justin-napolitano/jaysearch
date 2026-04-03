# Platform Template

Canonical template repository for Codex-operated projects.

This repository is the baseline shape for a governed, plan-driven project. It is meant to be copied or used as a template when starting a new repository that should preserve ExecPlan-first execution, machine-readable validation, auditable branch workflow, and human-controlled finalization.

## What This Template Gives You

- ExecPlan-driven work in `.agent/execplans/`
- canonical governance and policy text in `policy/`
- machine-readable workflow and rules in `spec/`
- validation and orchestration entrypoints in `bin/`
- Python implementation and repo tooling in `src/`
- starter docs for onboarding, maintenance, and operating model in `docs/`

The intent is not to centralize every future project into one shared codebase. New repositories should start from this structure, then evolve independently unless you intentionally port template improvements across.

## Working Model

The platform assumes this flow:

`ExecPlan -> Graph/Queue State -> PR -> Human Finalization -> Reconciliation -> Metrics`

In practice that means:

- agents draft and execute bounded work on policy-compliant non-`main` branches
- validation commands emit deterministic, machine-readable outputs
- review happens through pull requests rather than ad hoc local integration
- humans retain final authority for approval and signed merge/finalization

## Bootstrap A New Project

If you are scaffolding from a local platform checkout:

```bash
bin/bootstrap-project /tmp --name my-codex-project --profile full
```

Recommended next steps:

1. Clone or template this repository into the new project repository.
2. Rename the repository and replace the top-level product docs.
3. Install dependencies for the spawned project.
4. Run the required platform checks:
   `bin/bootstrap-profile-check`
   `bin/governance-loader-check`
   `bin/distribution-check`
   `bin/run-local-ci`
5. Create the first ExecPlan in `.agent/execplans/`.
6. Start implementation on a compliant non-`main` branch.

## Repository Map

- `bin/`: operator-facing commands and validation wrappers
- `docs/`: human-facing platform guides and design notes
- `examples/`: templates and example artifacts
- `policy/`: normative governance text
- `spec/`: canonical machine-readable rules and workflow metadata
- `src/`: Python implementation for platform tooling
- `tests/`: automated coverage for the platform toolchain

## Start Reading Here

- [Getting Started](docs/getting-started.md)
- [Platform Overview](docs/platform-overview.md)
- [Template Maintenance](docs/template-maintenance.md)
- [ExecPlans](docs/execplans.md)

## Default Expectations For Spawned Repos

Repositories created from this template are expected to preserve:

- ExecPlan-first execution
- canonical graph-backed work state
- local validation entrypoints in `bin/`
- branch and governance enforcement
- human-only finalization
- machine-readable evidence and validation outputs

Projects may customize product docs, application code, UI, assets, deployment configuration, and project-specific rules immediately, but they should not discard the governed operating model by accident.
