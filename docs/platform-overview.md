# Platform Overview

This repository is a plan-driven development platform template.

Its purpose is to serve as the canonical repository shape for Codex-operated projects so work stays auditable, reviewable, and deterministic across repositories.

Workflow:

ExecPlan -> Graph/Queue State -> PR -> Human Finalization -> Reconciliation -> Metrics

Agents draft work through ExecPlans. Humans finalize work with signed commits.

Operational lanes:

1. Architecture lock
2. Kernel contracts
3. Governance enforcement
4. Distribution contracts
5. Adoption pilot and promotion gate
