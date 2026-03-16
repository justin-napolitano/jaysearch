## Subgame Branch Governance

Implementation branches no longer need to prove legality through commit chronology alone. For `impl-execplan/*`, legality is accepted when the local state-transition referee proves that the branch:

- changed only declared files
- stayed inside the allowed surface classes for the branch role
- satisfied dependency state before advancing
- respected anti-cheat protected-surface policy

Git and GitHub remain the primary operator interface for the game:

- `git` carries the canonical artifact changes
- `gh` carries review, projection, and merge evidence
- local referees remain the authority for whether a transition is legal

## Branch Roles

The canonical branch contract defines two roles:

- `impl_execplan_root`
  - root implementation branch for a governed slice
  - may change declared canonical, projection, rule, capability-policy, and referee surfaces
  - does not require a handoff artifact
- `subgame_branch`
  - nested branch for a narrower independently-played subgame
  - must remain inside declared scope
  - must emit a handoff artifact under `.agent/handoffs/` before merge-back

## Merge-Back Legality

Merge-back legality is local-first and deterministic. An accepted merge-back must prove:

- dependencies for the active slice are completed
- changed files are declared in the active ExecPlan
- changed surface classes are allowed for the branch role
- protected surfaces were not crossed unlawfully
- required handoff artifacts exist for branch roles that require them

If any proof obligation fails, the referee rejects the transition with machine-readable blockers. GitHub status may mirror that result, but it does not override it.

## Migration From Commit Order

Procedural commit order remains a fallback safeguard outside implementation branches. On `impl-execplan/*`, the policy checker retires commit-order blocking only when `state-transition-legality-check` passes. If the state-transition referee fails, procedural order remains blocking until the branch becomes legal again.
