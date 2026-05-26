# Jaysearch Runtime CI V1

## Objective

Define the runtime validation boundary for Jaysearch as a separate project.

Jaysearch inherited a broad platform-template test suite. That suite still has value as legacy platform coverage, but it is no longer the correct readiness gate for Jaysearch tool development.

The Jaysearch runtime boundary should validate the product spine:

```text
design iteration
  -> execution unit
  -> candidate patch manifest
  -> implementation attempts
  -> attempt evaluation
  -> attempt selection
  -> solution artifact
  -> applied solution
```

## Research Basis

Local design sources:

- `docs/execution-era-loop-v1.md`
- `docs/candidate-patch-manifest-research-v1.md`
- `docs/candidate-generation-request-result-v1.md`
- `docs/design-iteration-tool-v1.md`
- `docs/project-format-and-state-v1.md`

External sources:

- GitHub Actions supports repository-specific workflows and path filters, so Jaysearch can define its own CI workflow rather than inheriting the template gate wholesale: https://docs.github.com/actions
- Pytest supports explicit test selection by path and marker, which allows product-specific validation profiles: https://docs.pytest.org/
- SWE-bench motivates repository-grounded validation through concrete tests and patches: https://arxiv.org/abs/2310.06770
- Agentless motivates simple staged software-agent pipelines before broad autonomous runtime complexity: https://arxiv.org/abs/2407.01489
- CRITIC motivates tool-grounded critique and correction over unsupported self-judgment: https://arxiv.org/abs/2305.11738

## Decision

Add `run-jaysearch-ci` as the project readiness gate.

Keep `run-local-ci` as the legacy platform-template gate.

This is a separation, not a deletion:

- Jaysearch PRs should run `bin/run-jaysearch-ci`.
- Legacy platform compatibility work may still run `bin/run-local-ci` or full `uv run pytest`.
- Platform control-plane, worker lease, branch rewrite, and GitHub Projects tests should not block normal Jaysearch tool slices unless that slice directly edits those systems.

## Jaysearch CI Scope

Required checks:

- candidate patch manifest contracts and materializer
- execution ERA loop smoke path
- implementation attempt generation
- attempt evaluation
- attempt selection
- solution artifact emission
- solution application
- execution unit materialization
- node readiness validation
- design iteration tests
- live design iteration over repository planning graphs

Excluded from default Jaysearch CI:

- governed worker session orchestration
- old platform merge-readiness policy
- old branch rewrite policy exceptions
- GitHub Projects sync
- platform distribution/adoption checks
- template bootstrap checks

## Anti-Drift Rules

- Jaysearch CI must not silently become full legacy platform CI.
- Legacy checks may remain available but must be explicitly invoked.
- Every new Jaysearch tool should add itself to `run-jaysearch-ci` once it affects the product spine.
- If a legacy platform test fails because of date-sensitive governance fixtures, that is not automatically a Jaysearch blocker.
- If a Jaysearch core test fails, the branch is not ready.

## Acceptance

- `bin/run-jaysearch-ci` exists and emits a machine-readable JSON report.
- GitHub Actions runs `bin/run-jaysearch-ci` on pushes and pull requests.
- README documents the Jaysearch CI boundary.
- Design iteration reports no blockers.
