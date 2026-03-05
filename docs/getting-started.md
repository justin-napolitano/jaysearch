
# Getting Started

1. Clone the repository
2. Run bootstrap: `bin/bootstrap-project /tmp --name my-codex-project`
3. Create ExecPlan
4. Generate TODOs
5. Implement tasks
6. Finalize ExecPlan with signed commit

Adoption pilot gate:

1. Maintain pilot status in `.agent/adoption/pilot-status.yaml`.
2. Run `bin/adoption-check`.
3. Run `bin/run-local-ci`.
4. Promote next wave only when pilot pass-rate meets spec thresholds.
