from __future__ import annotations

from typing import Final


API_VERSION: Final[str] = "local-orchestration.v1"

ROUTE_TARGETS: Final[tuple[str, ...]] = (
    "local_planner",
    "planning_worker",
    "local_execution_worker",
    "remote_execution_worker",
    "human_escalation",
)

REASON_CODES: Final[tuple[str, ...]] = (
    "task_is_local_planning",
    "task_requires_graph_or_contract_changes",
    "task_requires_code_changes",
    "task_requires_specialized_execution",
    "task_requires_internet_access",
    "local_runtime_unavailable",
    "managed_repo_target_missing",
    "managed_repo_target_ambiguous",
    "governance_authority_ambiguous",
    "human_approval_required",
    "policy_forbids_requested_mode",
    "existing_public_api_can_serve_request",
)

POLICY_BASIS_CODES: Final[tuple[str, ...]] = (
    "workflow.execution_requirements",
    "ruleset.execution_constraints",
    "codex_orchestrator.authority",
    "codex_orchestrator.stop_conditions",
    "agent_capability_policy.capability_rules",
    "local_orchestration.authority_model",
    "local_orchestration.routing",
    "public_orchestration_api.contract",
)

NEXT_ACTIONS: Final[tuple[str, ...]] = (
    "none",
    "bin/local-runtime-check",
    "bin/local-task-router",
    "bin/get-graph-state",
    "bin/resolve-worker-contract",
    "bin/run-worker-contract",
    "bin/start-next-worker",
    "bin/get-worker-status",
    "human_review_required",
)

VALIDATION_IDS: Final[tuple[str, ...]] = (
    "bin/local-runtime-check",
    "bin/local-task-router",
    "bin/get-graph-state",
    "bin/resolve-worker-contract",
    "bin/run-worker-contract",
    "bin/start-next-worker",
    "bin/get-worker-status",
    "bin/public-orchestration-api-check",
    "bin/remaining-work-graph-check",
    "bin/execplan-validate",
)

BLOCKER_CODES: Final[tuple[str, ...]] = (
    "required_local_runtime_missing",
    "configured_model_unavailable",
    "governance_authority_is_ambiguous",
    "internet_access_is_required_but_not_approved",
    "target_repo_root_is_missing",
    "target_repo_root_is_ambiguous",
    "required_target_artifact_missing",
    "unsupported_backend",
    "unsupported_mode",
    "runtime_endpoint_unreachable",
)

PROBLEM_TYPES: Final[dict[str, str]] = {
    "required_local_runtime_missing": "urn:local-orchestration:problem:required-local-runtime-missing",
    "configured_model_unavailable": "urn:local-orchestration:problem:configured-model-unavailable",
    "governance_authority_is_ambiguous": "urn:local-orchestration:problem:governance-authority-ambiguous",
    "internet_access_is_required_but_not_approved": "urn:local-orchestration:problem:internet-access-not-approved",
    "target_repo_root_is_missing": "urn:local-orchestration:problem:target-repo-root-missing",
    "target_repo_root_is_ambiguous": "urn:local-orchestration:problem:target-repo-root-ambiguous",
    "required_target_artifact_missing": "urn:local-orchestration:problem:required-target-artifact-missing",
    "unsupported_backend": "urn:local-orchestration:problem:unsupported-backend",
    "unsupported_mode": "urn:local-orchestration:problem:unsupported-mode",
    "runtime_endpoint_unreachable": "urn:local-orchestration:problem:runtime-endpoint-unreachable",
}

EVIDENCE_KINDS: Final[tuple[str, ...]] = ("spec", "doc", "artifact", "command")
