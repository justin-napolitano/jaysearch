# Agent Policy

Agent move legality is defined in `spec/ruleset.yaml`.

Normative policy statements:

- Agents may read, draft, edit in-scope files, run validators, and report evidence.
- Agents may not finalize plans, bypass protections, forge signatures, or suppress evidence.
- Agents may not execute repository actions directly on `main`; all actions must occur on a dedicated non-`main` branch.
- Codex-authored commits must include agent identity in commit message metadata (prefix + `Agent:` trailer), preferably via `bin/codex-commit`.
- Bypass approval authority is human-only and must include owner, rationale, and expiry evidence.
- Governance-required check names and command mappings must remain stable per `spec/governance.yaml`.
- Rule interpretation precedence is fixed: `spec/*` first, then `policy/*`, then `docs/*`.
- Any critical policy breach escalates to human authority.

Scoring inputs and penalties are defined in `spec/scoring.yaml`.
