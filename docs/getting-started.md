
# Getting Started

1. Clone the repository
2. Run bootstrap: `bin/bootstrap-project /tmp --name my-codex-project --profile full`
3. Validate scaffold profile: `bin/bootstrap-profile-check`
4. Create ExecPlan
5. Generate TODOs
6. Implement tasks
7. Finalize ExecPlan with signed commit

Adoption pilot gate:

1. Maintain pilot status in `.agent/adoption/pilot-status.yaml`.
2. Run `bin/adoption-check`.
3. Run `bin/run-local-ci`.
4. Promote next wave only when pilot pass-rate meets spec thresholds.

Project-specific rules:

- Edit `project.rules.yaml` to add stricter required checks/forbidden branches.
- Overlay rules are tighten-only and are enforced by `bin/governance-loader-check`.
