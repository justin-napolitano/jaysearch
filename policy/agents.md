# Agent Policy

Agent move legality is defined in `spec/ruleset.yaml`.

Normative policy statements:

- Agents may read, draft, edit in-scope files, run validators, and report evidence.
- Agents may not finalize plans, bypass protections, forge signatures, or suppress evidence.
- Agents may not implement ExecPlan changes directly on `main`; they must work on a dedicated `draft-execplan/*` branch for human review.
- Any critical policy breach escalates to human authority.

Scoring inputs and penalties are defined in `spec/scoring.yaml`.
