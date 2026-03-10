# Platform Template

Canonical template repository for Codex-operated projects.

This repository is intended to be copied or templated when starting a new project. Its primary value is repo-level structure: ExecPlans, TODO workflow, governance, validation commands, audit rules, and bootstrap conventions.

Default operating model:

- Use this repository as the base template for new projects.
- Treat spawned repositories as independent snapshots by default.
- Sync template improvements into existing projects intentionally, not automatically.
- Extract shared Python code into packages later only when it proves reusable across multiple repositories.

Bootstrap a new project:

`bin/bootstrap-project /tmp --name my-codex-project --profile full`

Core references:

- `docs/getting-started.md`
- `docs/template-maintenance.md`
- `docs/platform-overview.md`
