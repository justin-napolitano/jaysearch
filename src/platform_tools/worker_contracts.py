from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CONTRACTS_DIR = Path("artifacts/governance/initiative-worker-contracts")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "initiative"


def registry_path(*, root: Path, initiative_branch: str) -> Path:
    return root / CONTRACTS_DIR / f"{slugify(initiative_branch)}.json"


def load_registry(*, root: Path, initiative_branch: str) -> dict[str, Any] | None:
    path = registry_path(root=root, initiative_branch=initiative_branch)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def registry_contracts(registry: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(registry, dict):
        return []
    contracts = registry.get("contracts", [])
    if not isinstance(contracts, list):
        return []
    return [item for item in contracts if isinstance(item, dict)]


def save_registry(*, root: Path, initiative_branch: str, registry: dict[str, Any]) -> Path:
    path = registry_path(root=root, initiative_branch=initiative_branch)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def worker_id_from_branch(branch: str) -> str:
    if branch.startswith("impl-execplan/"):
        return branch.split("/", 1)[1]
    return branch


def contract_scope_findings(contract: dict[str, Any] | None) -> list[str]:
    if not isinstance(contract, dict):
        return ["worker_contract_missing"]
    scope = contract.get("scope", {})
    if not isinstance(scope, dict):
        return ["worker_contract_scope_missing"]
    findings: list[str] = []
    owned_surfaces = scope.get("owned_surfaces", [])
    non_goals = scope.get("non_goals", [])
    validations = scope.get("validations", [])
    if not isinstance(owned_surfaces, list) or not [str(item).strip() for item in owned_surfaces if str(item).strip()]:
        findings.append("worker_contract_owned_surfaces_missing")
    if not isinstance(non_goals, list) or not [str(item).strip() for item in non_goals if str(item).strip()]:
        findings.append("worker_contract_non_goals_missing")
    if not isinstance(validations, list) or not [str(item).strip() for item in validations if str(item).strip()]:
        findings.append("worker_contract_validations_missing")
    return findings


def find_contract(
    registry: dict[str, Any] | None,
    *,
    branch: str | None = None,
    worker_id: str | None = None,
    contract_id: str | None = None,
) -> dict[str, Any] | None:
    for contract in registry_contracts(registry):
        if contract_id and str(contract.get("contract_id", "")).strip() == contract_id:
            return contract
        if branch and str(contract.get("branch", "")).strip() == branch:
            return contract
        if worker_id and str(contract.get("worker_id", "")).strip() == worker_id:
            return contract
    return None
