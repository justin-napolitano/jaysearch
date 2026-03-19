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
