# ExecPlan Policy

ExecPlan requirements are defined in `spec/execplan.schema.yaml`.

Normative policy statements:

- All meaningful work must originate from an ExecPlan.
- ExecPlan identity uses canonical plan key format and matching filename stem.
- Required frontmatter and required sections are mandatory, but ExecPlans should stay contract-first and prose-thin.
- Task limit is 20 and draft TTL is 14 days.
- Agents draft; humans finalize.
- The authoritative in-flight planning location for governed work is the parent `initiative/*` branch.
- Dedicated `draft-execplan/*` branches are optional review/isolation branches, not the default planning location.
- ExecPlan implementation changes must execute on a dedicated `impl-execplan/*` branch; direct implementation commits to `main` are prohibited.
- Universal execution rule: repository actions (read/validate/edit/commit) must occur on a dedicated non-`main` branch.
- Branch compliance must satisfy workflow-specific branch naming patterns declared in `spec/ruleset.yaml` and `spec/workflow.yaml`.
- ExecPlan `changes` must respect architecture layer boundaries from `spec/platform-architecture.yaml`.
- If docs conflict with policy/spec, enforcement follows precedence `spec > policy > docs`.

Validator implementation must consume the schema spec directly instead of duplicating rule constants.
