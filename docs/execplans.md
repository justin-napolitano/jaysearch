# ExecPlans

ExecPlans define structured work execution.

Lifecycle:

draft -> proposed -> approved -> executing -> completed

Rules:

- Must contain required headings
- Must include frontmatter metadata
- Agents create drafts
- Humans finalize with SSH-signed commits
- Maximum 20 tasks per plan
- Draft TTL = 14 days

Draft Review Procedure:

1. Create a dedicated `draft-execplan/*` branch for the plan.
2. Draft or update the ExecPlan on that branch.
3. Perform agent self-review on the draft branch and reconcile the plan if needed before opening the PR.
4. Open one draft-plan PR using the governed pull-request template.
5. Treat the template as additive-only:
   - required sections stay present in every governed draft-plan PR
   - authors may add sections for extra evidence or nuance
   - authors may not remove baseline sections from the template
6. Human review and signed finalization on `main` make the plan authoritative.
7. Only after that finalization should governed implementation execution proceed on the dedicated `impl-execplan/*` branch.
8. Canonical graph and queue state must reflect the merged draft-plan status before the next implementation slice advances.

Initiative Branch Procedure:

1. Use `initiative/*` only for one higher-level graph-backed initiative node.
2. Treat the initiative branch as the home of one bounded authoritative ExecPlan for that initiative.
3. Worker `impl-execplan/*` branches may branch from and merge back into that initiative branch, but they inherit initiative plan authority rather than creating competing ExecPlans.
4. Worker contracts should define narrow owned scope, validations, merge criteria, and explicit non-goals for each worker branch.
5. Initiative branch legality is fail-closed:
   - if the branch does not map to one parent graph node, the workflow should block rather than warn
   - unknown initiative parent/child relationships are not valid governed execution
6. Merge to `main` should occur from the initiative branch only when the parent initiative node is complete.

Template:

Use `examples/execplan-template.md` as the starting point for new ExecPlan drafts.
