# Command Reference

These are repository-local platform commands expected to exist inside projects created from this template.

bin/bootstrap-project
bin/bootstrap-profile-check
bin/run-local-ci
bin/governance-loader-check
bin/kernel-contract-check
bin/governance-check
bin/distribution-check
bin/adoption-check
bin/execplan-validate
bin/sync-todos
bin/repo-health-check
bin/execplan-test
bin/rule-graph-check
bin/rule-registry-check
bin/remaining-work-graph-check
bin/auto-reconcile-main
bin/install-local-git-hooks
bin/run-governed-pre-push-checks
bin/bootstrap-managed-repo
bin/managed-repo-status
bin/orchestrate-governed-slice
bin/resolve-worker-contract
bin/run-worker-contract
bin/start-next-worker
bin/public-orchestration-api-check
bin/get-graph-state
bin/get-worker-status
bin/get-merge-readiness
bin/get-pr-integration-contract
bin/prepare-next-impl-branch
bin/github-projects-bootstrap
bin/github-projects-sync
bin/finalize-execplan
bin/codex-commit

Notes:

- `bin/sync-todos` is a projection command, not a canonical workflow authority.
- `bin/rule-graph-check` validates the rule-graph projection against the canonical rule registry.
- `bin/rule-registry-check` validates the canonical rule registry itself, including enforced-rule mappings and source artifact presence.
- `bin/remaining-work-graph-check` validates canonical work-state and queue projection reconciliation.
- `bin/auto-reconcile-main` is the local deterministic reconciliation entrypoint for `main` and `initiative/*` after merges or branch switches.
- `bin/install-local-git-hooks` installs the versioned `.githooks/` entrypoints by configuring local `core.hooksPath`.
- `bin/run-governed-pre-push-checks` runs safe branch-aware governance checks before push on governed branches.
- `bin/bootstrap-managed-repo` scaffolds a lightweight managed repo and writes repo-local provider-sync artifacts through platform-owned runtime code.
- `bin/managed-repo-status` validates that an external repo has the required canonical and board-bootstrap artifacts before orchestration proceeds.
- `bin/orchestrate-governed-slice` is the local control-loop entrypoint for both self-hosted and managed repos.
- `bin/resolve-worker-contract` resolves one runnable or explicit worker contract into a compact machine-shaped payload.
- `bin/run-worker-contract` is the orchestrator-agnostic worker execution entrypoint; it resolves one bounded worker contract and delegates execution to the governed worker runtime.
- `bin/start-next-worker` is a composite facade command for thin orchestrators that want “resolve next runnable contract and execute it” in one call.
- `bin/public-orchestration-api-check` validates that the facade commands still emit outputs compatible with the versioned public orchestration contract catalog.
- `bin/get-graph-state` provides a compact orchestration-facing view of canonical graph state without exposing the full raw graph payload.
- `bin/get-worker-status` provides a compact orchestration-facing view of worker session and recent run state.
- `bin/get-merge-readiness` projects whether the current implementation slice is ready to merge back into its lawful initiative target.
- `bin/get-pr-integration-contract` resolves the lawful initiative PR target and required validations for implementation merge-back.
- `bin/prepare-next-impl-branch` projects whether the next implementation slice may be cut from the current initiative head and returns the lawful branch target when it may proceed.
- the public orchestration facade commands emit a shared versioned envelope: `public-orchestration.v1`.
- `bin/github-projects-bootstrap` and `bin/github-projects-sync` are provider runtimes; they are meant to be invoked directly or by higher-level platform commands, not replaced by ad hoc shell usage.
