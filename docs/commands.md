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
bin/finalize-execplan
bin/codex-commit

Notes:

- `bin/sync-todos` is a projection command, not a canonical workflow authority.
- `bin/rule-graph-check` validates the rule-graph projection against the canonical rule registry.
- `bin/rule-registry-check` validates the canonical rule registry itself, including enforced-rule mappings and source artifact presence.
- `bin/remaining-work-graph-check` validates canonical work-state and queue projection reconciliation.
