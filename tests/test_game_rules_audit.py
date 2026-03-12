from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.game_rules_audit import run_game_rules_audit


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_repo(root: Path, *, omit_game_doc_claim: bool = False) -> None:
    _write(root / "docs/games/README.md", "# Games\n")
    _write(root / "docs/games/game-inheritance.md", "# Inheritance\n")
    _write(root / "docs/games/platform-game.md", "# Platform\n")
    _write(root / "docs/games/execplan-game.md", "# ExecPlan\n")
    _write(root / "docs/games/planning-game.md", "# Planning\n")
    _write(root / "docs/games/implementation-game.md", "# Implementation\n")
    _write(root / "docs/games/policy-compliance-game.md", "# Policy Compliance\n")
    _write(root / "docs/games/commit-structure-game.md", "# Commit Structure\n")
    _write(root / "docs/games/planning-merge-readiness-game.md", "# Planning Proof\n")
    _write(root / "docs/games/implementation-merge-readiness-game.md", "# Implementation Proof\n")
    _write(root / "docs/governance.md", "gov\n")
    _write(root / "docs/agent-game-rules-v1.md", "rules\n")
    _write(root / "bin/execplan-validate", "#!/usr/bin/env bash\n")
    _write(root / "bin/run-local-ci", "#!/usr/bin/env bash\n")
    _write(
        root / "spec/games.schema.yaml",
        "\n".join(
            [
                "version: v1",
                "graph:",
                "  required_fields: [graph_id, created_at, nodes, edges]",
                "node:",
                "  required_fields: [id, type, label, title]",
                "  type_allowed: [game, artifact, rule, validator, phase, authority]",
                "edge:",
                "  required_fields: [from, to, relation]",
                "  relation_allowed: [contains, terminates_in, hands_off_to, links_to, documented_in, inherits, applies_to, enforced_by, satisfied_by, requires]",
                "game_node:",
                "  required_fields: [layer, scope, spec_path]",
                "  allowed_layers: [platform, authority, work, review, truth, projection, assurance]",
                "  allowed_scopes: [global_board_law, domain_game, proof_game, subgame_local]",
                "game_graph:",
                "  required_game_ids: [game-platform, game-execplan, game-planning, game-implementation, game-policy-compliance, game-commit-structure, game-planning-proof, game-implementation-proof]",
                "  root_game_id: game-platform",
                "  required_edges:",
                "    - from: game-platform",
                "      to: game-execplan",
                "      relation: contains",
                "    - from: game-execplan",
                "      to: game-planning",
                "      relation: contains",
                "    - from: game-execplan",
                "      to: game-implementation",
                "      relation: contains",
                "    - from: game-implementation",
                "      to: game-policy-compliance",
                "      relation: contains",
                "    - from: game-policy-compliance",
                "      to: game-commit-structure",
                "      relation: contains",
                "    - from: game-planning",
                "      to: game-planning-proof",
                "      relation: terminates_in",
                "    - from: game-implementation",
                "      to: game-implementation-proof",
                "      relation: terminates_in",
                "    - from: game-planning",
                "      to: game-implementation",
                "      relation: hands_off_to",
            ]
        )
        + "\n",
    )
    _write(root / "spec/games/inheritance-rules.yaml", "inheritance:\n  referee_order: [global_board_law, active_domain_game, active_subgame]\n")
    _write(
        root / "spec/ruleset.yaml",
        "global_board_law:\n  required: [forbidden_moves, scope_compliance, no_hidden_state, canonical_state_ownership, determinism, human_authority_boundaries]\n  referee_order: [global_board_law, active_domain_game, active_subgame]\n  planned_domain_layers: [authority, work, review, truth, projection, assurance]\n",
    )
    _write(root / "spec/workflow.yaml", "execution_requirements:\n  referee_order: [global_board_law, active_domain_game, active_subgame]\n")
    for relpath, body in {
        "spec/games/platform-game.yaml": "\n".join(
            [
                "game_id: game-platform",
                "type: platform",
                "title: Platform Game",
                "layer: platform",
                "rule_scope: global_board_law",
                "parent_game: null",
                "objective: root",
                "board: board",
                "players: [human_authority]",
                "referees: [bin/execplan-validate]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "global_board_law: [forbidden_moves, scope_compliance, no_hidden_state, canonical_state_ownership, determinism, human_authority_boundaries]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/execplan-game.yaml": "\n".join(
            [
                "game_id: game-execplan",
                "type: execplan",
                "title: ExecPlan Game",
                "layer: authority",
                "rule_scope: domain_game",
                "parent_game: game-platform",
                "objective: contract",
                "board: board",
                "players: [human_authority]",
                "referees: [bin/execplan-validate]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/planning-game.yaml": "\n".join(
            [
                "game_id: game-planning",
                "type: planning",
                "title: Planning Game",
                "layer: work",
                "rule_scope: domain_game",
                "parent_game: game-execplan",
                "objective: plan",
                "board: board",
                "players: [planner]",
                "referees: [bin/planner]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [ambiguity_reduction]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/implementation-game.yaml": "\n".join(
            [
                "game_id: game-implementation",
                "type: implementation",
                "title: Implementation Game",
                "layer: work",
                "rule_scope: domain_game",
                "parent_game: game-execplan",
                "objective: implement",
                "board: board",
                "players: [implementer]",
                "referees: [bin/run-local-ci]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [scoped_file_changes]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/policy-compliance-game.yaml": "\n".join(
            [
                "game_id: game-policy-compliance",
                "type: policy_compliance",
                "title: Policy Compliance Game",
                "layer: assurance",
                "rule_scope: domain_game",
                "parent_game: game-implementation",
                "objective: legality",
                "board: board",
                "players: [implementer]",
                "referees: [bin/policy-compliance-check]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [latest_main_branching, clean_merge_state]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/commit-structure-game.yaml": "\n".join(
            [
                "game_id: game-commit-structure",
                "type: policy_compliance",
                "title: Commit Structure Game",
                "layer: assurance",
                "rule_scope: subgame_local",
                "parent_game: game-policy-compliance",
                "objective: legal commits",
                "board: board",
                "players: [implementer]",
                "referees: [bin/policy-compliance-check]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [procedural_commit_order, human_sized_commits]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/planning-merge-readiness-game.yaml": "\n".join(
            [
                "game_id: game-planning-proof",
                "type: merge_readiness",
                "title: Planning Proof",
                "layer: assurance",
                "rule_scope: proof_game",
                "parent_game: game-planning",
                "objective: prove",
                "board: board",
                "players: [planner]",
                "referees: [bin/execplan-validate]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [proof_obligations]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/implementation-merge-readiness-game.yaml": "\n".join(
            [
                "game_id: game-implementation-proof",
                "type: merge_readiness",
                "title: Implementation Proof",
                "layer: assurance",
                "rule_scope: proof_game",
                "parent_game: game-implementation",
                "objective: prove",
                "board: board",
                "players: [implementer]",
                "referees: [bin/run-local-ci]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [proof_obligations]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
    }.items():
        _write(root / relpath, body + "\n")

    _write_json(
        root / "artifacts/planner/research/game-graph.json",
        {
            "graph_id": "nested-game-system-20260311",
            "created_at": "2026-03-11T00:00:00Z",
            "nodes": [
                {"id": "game-platform", "type": "game", "label": "Platform Game", "title": "Platform", "layer": "platform", "scope": "global_board_law", "spec_path": "spec/games/platform-game.yaml"},
                {"id": "game-execplan", "type": "game", "label": "ExecPlan Game", "title": "ExecPlan", "layer": "authority", "scope": "domain_game", "spec_path": "spec/games/execplan-game.yaml"},
                {"id": "game-planning", "type": "game", "label": "Planning Game", "title": "Planning", "layer": "work", "scope": "domain_game", "spec_path": "spec/games/planning-game.yaml"},
                {"id": "game-implementation", "type": "game", "label": "Implementation Game", "title": "Implementation", "layer": "work", "scope": "domain_game", "spec_path": "spec/games/implementation-game.yaml"},
                {"id": "game-policy-compliance", "type": "game", "label": "Policy Compliance Game", "title": "Policy Compliance", "layer": "assurance", "scope": "domain_game", "spec_path": "spec/games/policy-compliance-game.yaml"},
                {"id": "game-commit-structure", "type": "game", "label": "Commit Structure Game", "title": "Commit Structure", "layer": "assurance", "scope": "subgame_local", "spec_path": "spec/games/commit-structure-game.yaml"},
                {"id": "game-planning-proof", "type": "game", "label": "Planning Proof", "title": "Planning Proof", "layer": "assurance", "scope": "proof_game", "spec_path": "spec/games/planning-merge-readiness-game.yaml"},
                {"id": "game-implementation-proof", "type": "game", "label": "Implementation Proof", "title": "Implementation Proof", "layer": "assurance", "scope": "proof_game", "spec_path": "spec/games/implementation-merge-readiness-game.yaml"},
                {"id": "artifact-rule-graph", "type": "artifact", "label": "Rule Graph", "title": "artifacts/planner/research/rule-graph.json"},
                {"id": "artifact-bibliography-graph", "type": "artifact", "label": "Bibliography", "title": "artifacts/planner/research/bibliography-graph.json"},
                {"id": "artifact-claim-registry", "type": "artifact", "label": "Claims", "title": "artifacts/planner/research/claim-registry.json"},
                {"id": "artifact-games-readme", "type": "artifact", "label": "README", "title": "docs/games/README.md"},
                {"id": "artifact-game-inheritance", "type": "artifact", "label": "Inheritance", "title": "docs/games/game-inheritance.md"},
                {"id": "artifact-platform-game-doc", "type": "artifact", "label": "Platform", "title": "docs/games/platform-game.md"},
                {"id": "artifact-execplan-game-doc", "type": "artifact", "label": "ExecPlan", "title": "docs/games/execplan-game.md"},
                {"id": "artifact-planning-game-doc", "type": "artifact", "label": "Planning", "title": "docs/games/planning-game.md"},
                {"id": "artifact-implementation-game-doc", "type": "artifact", "label": "Implementation", "title": "docs/games/implementation-game.md"},
                {"id": "artifact-policy-compliance-game-doc", "type": "artifact", "label": "Policy Compliance", "title": "docs/games/policy-compliance-game.md"},
                {"id": "artifact-commit-structure-game-doc", "type": "artifact", "label": "Commit Structure", "title": "docs/games/commit-structure-game.md"},
                {"id": "artifact-planning-proof-game", "type": "artifact", "label": "Planning Proof", "title": "docs/games/planning-merge-readiness-game.md"},
                {"id": "artifact-implementation-proof-game", "type": "artifact", "label": "Implementation Proof", "title": "docs/games/implementation-merge-readiness-game.md"}
            ],
            "edges": [
                {"from": "game-platform", "to": "game-execplan", "relation": "contains"},
                {"from": "game-execplan", "to": "game-planning", "relation": "contains"},
                {"from": "game-execplan", "to": "game-implementation", "relation": "contains"},
                {"from": "game-implementation", "to": "game-policy-compliance", "relation": "contains"},
                {"from": "game-policy-compliance", "to": "game-commit-structure", "relation": "contains"},
                {"from": "game-planning", "to": "game-planning-proof", "relation": "terminates_in"},
                {"from": "game-implementation", "to": "game-implementation-proof", "relation": "terminates_in"},
                {"from": "game-planning", "to": "game-implementation", "relation": "hands_off_to"},
                {"from": "game-platform", "to": "artifact-rule-graph", "relation": "links_to"},
                {"from": "game-platform", "to": "artifact-bibliography-graph", "relation": "links_to"},
                {"from": "game-platform", "to": "artifact-claim-registry", "relation": "links_to"},
                {"from": "game-platform", "to": "artifact-games-readme", "relation": "documented_in"},
                {"from": "game-platform", "to": "artifact-game-inheritance", "relation": "documented_in"},
                {"from": "game-platform", "to": "artifact-platform-game-doc", "relation": "documented_in"},
                {"from": "game-execplan", "to": "artifact-execplan-game-doc", "relation": "documented_in"},
                {"from": "game-planning", "to": "artifact-planning-game-doc", "relation": "documented_in"},
                {"from": "game-implementation", "to": "artifact-implementation-game-doc", "relation": "documented_in"},
                {"from": "game-policy-compliance", "to": "artifact-policy-compliance-game-doc", "relation": "documented_in"},
                {"from": "game-commit-structure", "to": "artifact-commit-structure-game-doc", "relation": "documented_in"},
                {"from": "game-planning-proof", "to": "artifact-planning-proof-game", "relation": "documented_in"},
                {"from": "game-implementation-proof", "to": "artifact-implementation-proof-game", "relation": "documented_in"}
            ],
        },
    )
    _write_json(
        root / "artifacts/planner/research/rule-graph.json",
        {
            "graph_id": "planner-rule-graph-20260310",
            "created_at": "2026-03-10T00:00:00Z",
            "nodes": [
                {"id": "rule-smoke-test-required", "type": "rule", "label": "Smoke Test Required", "title": "Smoke"},
                {"id": "rule-clean-merge-state", "type": "rule", "label": "Clean Merge State", "title": "Clean"},
                {"id": "rule-human-sized-commits", "type": "rule", "label": "Human Sized Commits", "title": "Commit"},
                {"id": "rule-procedural-commit-order", "type": "rule", "label": "Procedural Commit Order", "title": "Order"},
                {"id": "rule-latest-main-branching", "type": "rule", "label": "Latest Main Branching", "title": "Branch"},
                {"id": "rule-execplan-validation", "type": "rule", "label": "ExecPlan Validation", "title": "ExecPlan"},
                {"id": "rule-human-finalization", "type": "rule", "label": "Human Finalization", "title": "Human"},
                {"id": "artifact-agent-game-rules", "type": "artifact", "label": "Agent Rules", "title": "docs/agent-game-rules-v1.md"},
                {"id": "artifact-governance-doc", "type": "artifact", "label": "Gov", "title": "docs/governance.md"},
                {"id": "artifact-governance-spec", "type": "artifact", "label": "Gov Spec", "title": "spec/governance.yaml"},
                {"id": "artifact-ruleset-spec", "type": "artifact", "label": "Ruleset", "title": "spec/ruleset.yaml"},
                {"id": "artifact-workflow-spec", "type": "artifact", "label": "Workflow", "title": "spec/workflow.yaml"},
                {"id": "validator-execplan-validate", "type": "validator", "label": "Execplan", "title": "bin/execplan-validate"},
                {"id": "validator-run-local-ci", "type": "validator", "label": "CI", "title": "bin/run-local-ci"},
                {"id": "validator-smoke-test", "type": "validator", "label": "Smoke", "title": "bin/run-local-ci"},
                {"id": "validator-policy-compliance-check", "type": "validator", "label": "Policy Compliance", "title": "bin/policy-compliance-check"},
                {"id": "phase-merge-readiness", "type": "phase", "label": "Merge", "title": "Merge"},
                {"id": "authority-human", "type": "authority", "label": "Human", "title": "Human"}
            ],
            "edges": [
                {"from": "rule-smoke-test-required", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-smoke-test-required", "to": "validator-smoke-test", "relation": "enforced_by"},
                {"from": "rule-clean-merge-state", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-clean-merge-state", "to": "validator-policy-compliance-check", "relation": "enforced_by"},
                {"from": "rule-human-sized-commits", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-human-sized-commits", "to": "validator-policy-compliance-check", "relation": "enforced_by"},
                {"from": "rule-procedural-commit-order", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-procedural-commit-order", "to": "validator-policy-compliance-check", "relation": "enforced_by"},
                {"from": "rule-latest-main-branching", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-latest-main-branching", "to": "validator-policy-compliance-check", "relation": "enforced_by"},
                {"from": "rule-execplan-validation", "to": "phase-merge-readiness", "relation": "applies_to"},
                {"from": "rule-execplan-validation", "to": "validator-execplan-validate", "relation": "enforced_by"},
                {"from": "rule-human-finalization", "to": "authority-human", "relation": "requires"},
                {"from": "rule-human-finalization", "to": "artifact-ruleset-spec", "relation": "satisfied_by"}
            ],
        },
    )
    _write_json(
        root / "artifacts/planner/research/bibliography-graph.json",
        {
            "graph_id": "bibliography-test",
            "created_at": "2026-03-10T00:00:00Z",
            "nodes": [
                {"id": "src-maskin-2007", "type": "source", "label": "Mechanism Design", "title": "Mechanism Design"},
                {"id": "src-harel-1987", "type": "source", "label": "Statecharts", "title": "Statecharts"},
                {"id": "claim-nested-game-system", "type": "claim", "label": "Nested Games", "title": "Nested Games"},
                {"id": "artifact-games-readme", "type": "artifact", "label": "README", "title": "docs/games/README.md"},
                {"id": "artifact-game-inheritance", "type": "artifact", "label": "Inheritance", "title": "docs/games/game-inheritance.md"},
                {"id": "artifact-platform-game-doc", "type": "artifact", "label": "Platform", "title": "docs/games/platform-game.md"},
                {"id": "artifact-execplan-game-doc", "type": "artifact", "label": "ExecPlan", "title": "docs/games/execplan-game.md"},
                {"id": "artifact-planning-game-doc", "type": "artifact", "label": "Planning", "title": "docs/games/planning-game.md"},
                {"id": "artifact-implementation-game-doc", "type": "artifact", "label": "Implementation", "title": "docs/games/implementation-game.md"},
                {"id": "artifact-policy-compliance-game-doc", "type": "artifact", "label": "Policy Compliance", "title": "docs/games/policy-compliance-game.md"},
                {"id": "artifact-commit-structure-game-doc", "type": "artifact", "label": "Commit Structure", "title": "docs/games/commit-structure-game.md"},
                {"id": "artifact-planning-proof-game", "type": "artifact", "label": "Planning Proof", "title": "docs/games/planning-merge-readiness-game.md"},
                {"id": "artifact-implementation-proof-game", "type": "artifact", "label": "Implementation Proof", "title": "docs/games/implementation-merge-readiness-game.md"}
            ],
            "edges": [
                {"from": "claim-nested-game-system", "to": "artifact-games-readme", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-game-inheritance", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-platform-game-doc", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-execplan-game-doc", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-planning-game-doc", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-implementation-game-doc", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-policy-compliance-game-doc", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-commit-structure-game-doc", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-planning-proof-game", "relation": "cited_in"},
                {"from": "claim-nested-game-system", "to": "artifact-implementation-proof-game", "relation": "cited_in"}
            ],
        },
    )
    artifacts = [
        ("docs/games/README.md", "artifact-games-readme", "ngr-001"),
        ("docs/games/game-inheritance.md", "artifact-game-inheritance", "gin-001"),
        ("docs/games/platform-game.md", "artifact-platform-game-doc", "pgd-001"),
        ("docs/games/execplan-game.md", "artifact-execplan-game-doc", "egd-001"),
        ("docs/games/planning-game.md", "artifact-planning-game-doc", "plgd-001"),
        ("docs/games/implementation-game.md", "artifact-implementation-game-doc", "igd-001"),
        ("docs/games/policy-compliance-game.md", "artifact-policy-compliance-game-doc", "pcg-001"),
        ("docs/games/commit-structure-game.md", "artifact-commit-structure-game-doc", "csg-001"),
        ("docs/games/planning-merge-readiness-game.md", "artifact-planning-proof-game", "pmr-001"),
        ("docs/games/implementation-merge-readiness-game.md", "artifact-implementation-proof-game", "imr-001"),
    ]
    if omit_game_doc_claim:
        artifacts = [item for item in artifacts if item[0] != "docs/games/platform-game.md"]
    _write_json(
        root / "artifacts/planner/research/claim-registry.json",
        {
            "registry_id": "claim-test",
            "created_at": "2026-03-10T00:00:00Z",
            "artifacts": [
                {
                    "artifact_path": path,
                    "artifact_node_id": node_id,
                    "required": True,
                    "claims": [
                        {
                            "claim_id": claim_id,
                            "summary": "Nested game claim",
                            "category": "design-inference",
                            "source_ids": ["src-maskin-2007", "src-harel-1987"],
                            "bibliography_claim_ids": ["claim-nested-game-system"]
                        }
                    ]
                }
                for path, node_id, claim_id in artifacts
            ]
        },
    )


def test_game_rules_audit_passes_for_layered_repo(tmp_path: Path) -> None:
    _seed_repo(tmp_path)
    code, report = run_game_rules_audit(tmp_path.as_posix())
    assert code == 0
    assert report["ok"] is True
    assert report["board_model"]["referee_order"] == [
        "global_board_law",
        "active_domain_game",
        "active_subgame",
    ]
    assert any(item["layer"] == "authority" for item in report["layers"])
    assert report["commit_structure"]["recommended_subgame"] == "game-commit-structure"


def test_game_rules_audit_blocks_when_required_game_doc_lacks_claims(tmp_path: Path) -> None:
    _seed_repo(tmp_path, omit_game_doc_claim=True)
    code, report = run_game_rules_audit(tmp_path.as_posix())
    assert code == 1
    assert report["ok"] is False
    assert "missing_claim_registry_entry:docs/games/platform-game.md" in report["blockers"]
