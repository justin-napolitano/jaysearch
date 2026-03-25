# Problem Details and Agent Error Contracts

This note is intentionally incomplete. It is a design direction, not a finalized contract.

The platform should adopt `RFC 9457` Problem Details as the base error wire format for worker execution, kernel reconciliation failures, and executor/runtime rejection paths. The important design move is not merely returning structured JSON. It is committing to one stable machine-readable error contract and then rendering that same semantic payload in multiple operator-friendly formats.

Cloudflare's recent RFC 9457 agent-error work is a strong reference because it shows the right layering model: standard base fields, stable extension members, and explicit operational guidance instead of opaque human-only prose. That maps cleanly onto a terminal-first governed worker system.

Local bibliography for this note:

- `resources/biblio/agent-error-contract-standards.md`
- `resources/biblio/execution-and-observability-standards.md`

## Why This Matters

Today, many agent and worker systems still fail through a mix of:

- ad hoc stderr text
- brittle tool-specific error objects
- HTML-oriented failure pages
- retry behavior inferred from guesswork

That is weak for a governed execution kernel. The kernel needs deterministic answers to a few core questions:

- what failed
- where it failed
- whether retry is allowed
- how long to wait before retry
- whether owner escalation is required
- which initiative, worker contract, and trace the failure belongs to

RFC 9457 gives a clean base shape for that.

## Recommended Contract Shape

Use RFC 9457 base members:

- `type`
- `title`
- `status`
- `detail`
- `instance`

Then add governed platform extension members such as:

- `error_code`
- `error_category`
- `retryable`
- `retry_after`
- `owner_action_required`
- `initiative_id`
- `worker_id`
- `contract_id`
- `executor_backend`
- `trace_id`
- `artifact_refs`
- `what_you_should_do`
- `suggested_next_state`

These extension fields should be stable enough that worker runtimes, kernel reducers, hostile review surfaces, and terminal UX can all make consistent decisions without special-case parsing.

## One Contract, Two Formats

The recommended serving pattern is:

1. `application/problem+json` for programmatic consumers.
2. Markdown for terminal operators and model-first review flows.

The JSON and markdown forms should carry the same semantic information. The markdown form should not invent extra meaning. It should simply render the same stable fields in a clearer human-facing presentation.

## Example Direction

Illustrative JSON shape:

```json
{
  "type": "https://example.local/problems/worker-policy-missing",
  "title": "Required worker policy is unavailable",
  "status": 409,
  "detail": "The requested worker execution cannot proceed because its required policy artifact could not be loaded.",
  "instance": "trace-01HQXYZ",
  "error_code": "POLICY_CONTEXT_MISSING",
  "error_category": "policy",
  "retryable": false,
  "retry_after": null,
  "owner_action_required": true,
  "initiative_id": "rwg-041",
  "worker_id": "worker-capability-policy-a",
  "contract_id": "contract-capability-policy-v1",
  "executor_backend": "local_container",
  "trace_id": "01HQXYZ",
  "artifact_refs": [
    ".agent/execplans/20260324-policy-driven-ranking-and-capability-engine.md"
  ],
  "what_you_should_do": "Do not retry automatically. Restore or validate the required policy artifact, then rerun the worker."
}
```

Illustrative markdown rendering:

```md
---
error_code: POLICY_CONTEXT_MISSING
error_category: policy
status: 409
retryable: false
owner_action_required: true
initiative_id: rwg-041
worker_id: worker-capability-policy-a
trace_id: 01HQXYZ
---

# Required worker policy is unavailable

## What Happened

The requested worker execution could not proceed because its required policy artifact could not be loaded.

## What You Should Do

Do not retry automatically. Restore or validate the required policy artifact, then rerun the worker.
```

## Design Implications For This Repo

- Worker runtimes should emit problem details instead of raw ad hoc failures when possible.
- Kernel reducers should understand retry and escalation fields directly instead of guessing from text.
- Terminal surfaces should prefer markdown problem rendering for readability, while preserving the raw JSON payload for automation and archival.
- Hostile review should treat the problem document as evidence, not just a presentation artifact.

## Open Questions

- Which error categories should be canonical at the kernel level versus executor-specific?
- Should markdown be a first-class stored artifact or a derived rendering from canonical JSON?
- How much of the retry policy should be advisory versus enforced by the kernel?
- Should non-HTTP execution paths still use RFC 9457 objects as the internal failure model even when no HTTP response is involved?
