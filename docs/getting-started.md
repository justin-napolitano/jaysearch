# Getting Started

This repository is meant to be the starting point for new Codex-operated repositories.

## Start a New Project

1. Clone or template this repository into a new project repository.
2. Rename the repository and update the top-level product docs for the new project.
3. Run bootstrap if you are scaffolding from a local platform checkout:
   `bin/bootstrap-project /tmp --name my-codex-project --profile full`
4. Enter the new repository and install project dependencies.
5. Run the required platform checks:
   - `bin/bootstrap-profile-check`
   - `bin/governance-loader-check`
   - `bin/distribution-check`
   - `bin/run-local-ci`
6. Create the first ExecPlan in `.agent/execplans/`.
7. If you want a local task projection, run `bin/sync-todos`.
8. Implement work on a compliant non-`main` branch.
9. Human-finalize with a signed commit.

## Required Platform Workflow

Every spawned repository is expected to preserve:

- ExecPlan-first execution
- canonical graph-backed work state
- local validation entrypoints in `bin/`
- human-only finalization
- branch and governance enforcement
- machine-readable validation outputs

## Project Customization

New projects may customize immediately:

- product README and product docs
- application code and UI
- assets and content
- deployment configuration
- stricter project rules in `project.rules.yaml`

## Adoption Pilot Gate

1. Maintain pilot status in `.agent/adoption/pilot-status.yaml`.
2. Run `bin/adoption-check`.
3. Run `bin/run-local-ci`.
4. Promote the next wave only when pilot pass-rate meets spec thresholds.
