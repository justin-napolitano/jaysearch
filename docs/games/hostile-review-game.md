# Hostile-Review Game

## Objective

The hostile-review game emits deterministic adversarial findings from canonical local evidence before human approval gates.

## Layer

The hostile-review game is a review-layer child of the implementation game. It inherits global board law and depends on policy compliance rather than replacing it.

## Board

The hostile-review board is limited to canonical local authority surfaces:

- the active ExecPlan
- the canonical remaining-work graph
- the queue projection as a projection-only mirror
- deterministic hostile-review artifacts
- inherited merge-readiness and policy-compliance evidence

## Legal Moves

- inspect
- challenge
- emit_findings
- request_recovery
- attest_clean_review

## Illegal Moves

- bypass_policy_compliance
- invent_evidence
- treat_projection_board_as_authority
- approve_for_human_finalization

## Local Rule Focus

- deterministic findings
- fail-closed behavior when evidence is missing
- policy-compliance prerequisite inheritance
- reproducible review artifacts
- projection surfaces remain non-authoritative

## Referees

- `bin/policy-compliance-check`
- `bin/hostile-review`
- `bin/hostile-review-smoke-test`

Referees evaluate inherited board law first, then implementation-game legality, then hostile-review findings.

## Win Condition

The hostile-review game succeeds when it emits deterministic machine-readable findings, or a clean attestation, from canonical evidence without expanding authority beyond human final review.

## Loss Condition

The hostile-review game fails when findings are unsupported, non-deterministic, or attempt to convert review artifacts or projection surfaces into authority.
