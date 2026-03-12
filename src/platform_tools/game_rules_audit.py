from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.game_graph_check import check_game_graph


COMMAND = "game-rules-audit"

GAME_DOC_PATHS = [
    "docs/games/README.md",
    "docs/games/game-inheritance.md",
    "docs/games/platform-game.md",
    "docs/games/execplan-game.md",
    "docs/games/planning-game.md",
    "docs/games/implementation-game.md",
    "docs/games/planning-merge-readiness-game.md",
    "docs/games/implementation-merge-readiness-game.md",
]

BOARD_LAW_SOURCE_REFS = {
    "forbidden_moves": ["spec/ruleset.yaml", "docs/agent-game-rules-v1.md"],
    "scope_compliance": ["docs/agent-game-rules-v1.md", "docs/governance.md"],
    "no_hidden_state": ["spec/games/inheritance-rules.yaml", "docs/games/game-inheritance.md"],
    "canonical_state_ownership": ["docs/governance.md", "docs/games/README.md"],
    "determinism": ["spec/ruleset.yaml", "docs/agent-game-rules-v1.md"],
    "human_authority_boundaries": ["spec/workflow.yaml", "docs/governance.md"],
}

BOARD_LAW_ENFORCEMENT = {
    "forbidden_moves": "enforced",
    "scope_compliance": "partial",
    "no_hidden_state": "partial",
    "canonical_state_ownership": "partial",
    "determinism": "enforced",
    "human_authority_boundaries": "enforced",
}

RULE_BINDINGS = {
    "rule-smoke-test-required": {
        "scope": "subgame_local",
        "bound_games": ["game-implementation-proof"],
        "candidate_game": "game-implementation-merge-readiness",
    },
    "rule-clean-merge-state": {
        "scope": "subgame_local",
        "bound_games": ["game-implementation-proof"],
        "candidate_game": "game-implementation-merge-readiness",
    },
    "rule-human-sized-commits": {
        "scope": "domain_game",
        "bound_games": ["game-implementation"],
        "candidate_game": "game-commit-structure",
    },
    "rule-procedural-commit-order": {
        "scope": "domain_game",
        "bound_games": ["game-implementation"],
        "candidate_game": "game-commit-structure",
    },
    "rule-latest-main-branching": {
        "scope": "global_board_law",
        "bound_games": ["game-platform", "game-execplan"],
        "candidate_game": "game-branching",
    },
    "rule-execplan-validation": {
        "scope": "subgame_local",
        "bound_games": ["game-execplan", "game-planning-proof", "game-implementation-proof"],
        "candidate_game": "game-execplan",
    },
    "rule-human-finalization": {
        "scope": "global_board_law",
        "bound_games": ["game-platform", "game-execplan"],
        "candidate_game": "game-finalization",
    },
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _citation_status_for_artifact(
    *,
    artifact_path: str,
    claim_registry_entries: dict[str, dict[str, Any]],
    bibliography_nodes: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    entry = claim_registry_entries.get(artifact_path)
    if entry is None:
        return "unsupported", [f"missing_claim_registry_entry:{artifact_path}"]
    blockers: list[str] = []
    artifact_node_id = str(entry.get("artifact_node_id", "")).strip()
    if artifact_node_id and artifact_node_id not in bibliography_nodes:
        blockers.append(f"missing_bibliography_artifact_node:{artifact_path}:{artifact_node_id}")
    claims = entry.get("claims", [])
    if not isinstance(claims, list) or not claims:
        blockers.append(f"missing_claims:{artifact_path}")
    for claim in claims:
        if not isinstance(claim, dict):
            blockers.append(f"invalid_claim_entry:{artifact_path}")
            continue
        for source_id in claim.get("source_ids", []):
            node = bibliography_nodes.get(str(source_id))
            if node is None or node.get("type") != "source":
                blockers.append(f"missing_source_ref:{artifact_path}:{source_id}")
        for claim_id in claim.get("bibliography_claim_ids", []):
            node = bibliography_nodes.get(str(claim_id))
            if node is None or node.get("type") != "claim":
                blockers.append(f"missing_bibliography_claim_ref:{artifact_path}:{claim_id}")
    return ("citation_backed" if not blockers else "unsupported"), blockers


def _enforcement_status_for_rule(rule_id: str, edges: list[dict[str, Any]]) -> str:
    enforced = any(
        edge.get("from") == rule_id and edge.get("relation") == "enforced_by"
        for edge in edges
    )
    authority_required = any(
        edge.get("from") == rule_id and edge.get("relation") == "requires"
        for edge in edges
    )
    supported_only = any(
        edge.get("from") == rule_id and edge.get("relation") == "satisfied_by"
        for edge in edges
    )
    if enforced or authority_required:
        return "enforced"
    if supported_only:
        return "partial"
    return "prose_only"


def run_game_rules_audit(root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root)
    blockers: list[str] = []

    graph_code, graph_report = check_game_graph(root)
    if graph_code != 0:
        blockers.extend(str(item) for item in graph_report.get("errors", []))

    game_graph_path = base / "artifacts" / "planner" / "research" / "game-graph.json"
    rule_graph_path = base / "artifacts" / "planner" / "research" / "rule-graph.json"
    bibliography_path = base / "artifacts" / "planner" / "research" / "bibliography-graph.json"
    claim_registry_path = base / "artifacts" / "planner" / "research" / "claim-registry.json"
    ruleset_path = base / "spec" / "ruleset.yaml"
    workflow_path = base / "spec" / "workflow.yaml"
    inheritance_path = base / "spec" / "games" / "inheritance-rules.yaml"

    for required_path in [
        game_graph_path,
        rule_graph_path,
        bibliography_path,
        claim_registry_path,
        ruleset_path,
        workflow_path,
        inheritance_path,
    ]:
        if not required_path.exists():
            blockers.append(f"missing_required_artifact:{required_path.as_posix()}")

    if blockers:
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "blockers": sorted(set(blockers)),
            "error_count": len(sorted(set(blockers))),
            "game_count": 0,
            "rule_count": 0,
            "evidence_refs": sorted(
                {
                    path.as_posix()
                    for path in [game_graph_path, rule_graph_path, bibliography_path, claim_registry_path]
                    if path.exists()
                }
            ),
        }
        return 1, report

    game_graph = _load_json(game_graph_path)
    rule_graph = _load_json(rule_graph_path)
    bibliography = _load_json(bibliography_path)
    claim_registry = _load_json(claim_registry_path)
    ruleset = _load_yaml(ruleset_path)
    workflow = _load_yaml(workflow_path)

    bibliography_nodes = {
        str(node.get("id")): node
        for node in bibliography.get("nodes", [])
        if isinstance(node, dict) and str(node.get("id", "")).strip()
    }
    claim_registry_entries = {
        str(entry.get("artifact_path")): entry
        for entry in claim_registry.get("artifacts", [])
        if isinstance(entry, dict) and str(entry.get("artifact_path", "")).strip()
    }

    game_nodes = [
        node
        for node in game_graph.get("nodes", [])
        if isinstance(node, dict) and node.get("type") == "game"
    ]
    layer_index: dict[str, list[str]] = {}
    game_specs: list[dict[str, Any]] = []
    for node in sorted(game_nodes, key=lambda item: str(item.get("id", ""))):
        layer = str(node.get("layer", "")).strip()
        scope = str(node.get("scope", "")).strip()
        spec_path = str(node.get("spec_path", "")).strip()
        layer_index.setdefault(layer, []).append(str(node.get("id", "")).strip())
        spec = _load_yaml(base / spec_path) if spec_path else {}
        if str(spec.get("game_id", "")).strip() != str(node.get("id", "")).strip():
            blockers.append(f"game_spec_id_mismatch:{node.get('id')}:{spec_path}")
        referee_order = spec.get("referee_order", [])
        if referee_order != ["global_board_law", "active_domain_game", "active_subgame"]:
            blockers.append(f"invalid_referee_order:{node.get('id')}")
        game_specs.append(
            {
                "game_id": str(node.get("id", "")).strip(),
                "title": str(node.get("title", "")).strip(),
                "layer": layer,
                "rule_scope": scope,
                "parent_game": spec.get("parent_game"),
                "spec_path": spec_path,
                "referees": spec.get("referees", []),
                "referee_order": referee_order,
                "local_rule_focus": spec.get("local_rule_focus", []),
            }
        )

    platform_spec = _load_yaml(base / "spec" / "games" / "platform-game.yaml")
    board_law = [str(item).strip() for item in platform_spec.get("global_board_law", []) if str(item).strip()]
    if not board_law:
        blockers.append("missing_global_board_law")

    citation_audit: list[dict[str, Any]] = []
    for artifact_path in GAME_DOC_PATHS:
        status, citation_blockers = _citation_status_for_artifact(
            artifact_path=artifact_path,
            claim_registry_entries=claim_registry_entries,
            bibliography_nodes=bibliography_nodes,
        )
        citation_audit.append(
            {
                "artifact_path": artifact_path,
                "citation_status": status,
                "blockers": sorted(set(citation_blockers)),
            }
        )
        blockers.extend(citation_blockers)

    ruleset_domains = ruleset.get("global_board_law", {}).get("planned_domain_layers", [])
    if not ruleset_domains:
        blockers.append("missing_planned_domain_layers")
    workflow_referee_order = workflow.get("execution_requirements", {}).get("referee_order", [])
    if workflow_referee_order != ["global_board_law", "active_domain_game", "active_subgame"]:
        blockers.append("workflow_referee_order_mismatch")

    rule_nodes = [
        node
        for node in rule_graph.get("nodes", [])
        if isinstance(node, dict) and node.get("type") == "rule"
    ]
    rule_audit: list[dict[str, Any]] = []
    partial_or_policy_rules: list[str] = []
    for rule_name in board_law:
        enforcement_status = BOARD_LAW_ENFORCEMENT.get(rule_name, "partial")
        if enforcement_status != "enforced":
            partial_or_policy_rules.append(rule_name)
        rule_audit.append(
            {
                "rule_id": f"board-law:{rule_name}",
                "label": rule_name,
                "scope": "global_board_law",
                "bound_games": ["game-platform"],
                "candidate_game": "game-platform",
                "enforcement_status": enforcement_status,
                "source_refs": BOARD_LAW_SOURCE_REFS.get(rule_name, []),
                "citation_status": "inferred",
            }
        )

    for node in sorted(rule_nodes, key=lambda item: str(item.get("id", ""))):
        rule_id = str(node.get("id", "")).strip()
        binding = RULE_BINDINGS.get(rule_id)
        if binding is None:
            blockers.append(f"missing_rule_binding:{rule_id}")
            continue
        enforcement_status = _enforcement_status_for_rule(rule_id, rule_graph.get("edges", []))
        if rule_id in {"rule-human-sized-commits", "rule-procedural-commit-order"} and enforcement_status == "enforced":
            enforcement_status = "partial"
        if enforcement_status != "enforced":
            partial_or_policy_rules.append(rule_id)
        rule_audit.append(
            {
                "rule_id": rule_id,
                "label": str(node.get("label", "")).strip(),
                "scope": binding["scope"],
                "bound_games": binding["bound_games"],
                "candidate_game": binding["candidate_game"],
                "enforcement_status": enforcement_status,
                "source_refs": sorted(
                    {
                        str(edge.get("to", "")).strip()
                        for edge in rule_graph.get("edges", [])
                        if edge.get("from") == rule_id and edge.get("relation") in {"satisfied_by", "enforced_by", "requires"}
                    }
                ),
                "citation_status": "inferred",
            }
        )

    commit_structure = {
        "rule_ids": ["rule-human-sized-commits", "rule-procedural-commit-order"],
        "status": "partial",
        "current_binding": "governed_policy",
        "recommended_parent_game": "game-policy-compliance",
        "recommended_subgame": "game-commit-structure",
    }

    extension_readiness = {
        "ok": not blockers,
        "planned_follow_on_games": [
            "game-policy-compliance",
            "game-commit-structure",
            "game-hostile-review",
        ],
        "partial_rules": sorted(set(partial_or_policy_rules)),
    }

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "error_count": len(sorted(set(blockers))),
        "board_model": {
            "shared_platform_board": True,
            "global_board_law": board_law,
            "referee_order": platform_spec.get("referee_order", []),
            "planned_domain_layers": ruleset_domains,
        },
        "layers": [
            {"layer": layer, "games": sorted(game_ids)}
            for layer, game_ids in sorted(layer_index.items())
        ],
        "games": game_specs,
        "rules": sorted(rule_audit, key=lambda item: str(item["rule_id"])),
        "citation_audit": citation_audit,
        "commit_structure": commit_structure,
        "extension_readiness": extension_readiness,
        "graph": {
            "graph_id": str(game_graph.get("graph_id", "")).strip(),
            "game_count": len(game_nodes),
            "rule_count": len(rule_audit),
        },
        "evidence_refs": sorted(
            {
                game_graph_path.as_posix(),
                rule_graph_path.as_posix(),
                bibliography_path.as_posix(),
                claim_registry_path.as_posix(),
                ruleset_path.as_posix(),
                workflow_path.as_posix(),
                inheritance_path.as_posix(),
            }
        ),
    }
    return (1 if blockers else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = run_game_rules_audit(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
