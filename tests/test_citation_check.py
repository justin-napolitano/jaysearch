from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.citation_check import check_citations


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_repo(root: Path, *, invalid_design_inference: bool = False) -> None:
    _write_text(
        root / "spec" / "claim-registry.schema.yaml",
        "\n".join(
            [
                "registry:",
                "  required_fields:",
                "    - registry_id",
                "    - created_at",
                "    - artifacts",
                "artifact_entry:",
                "  required_fields:",
                "    - artifact_path",
                "    - artifact_node_id",
                "    - required",
                "    - claims",
                "claim_entry:",
                "  required_fields:",
                "    - claim_id",
                "    - summary",
                "    - category",
                "  category_allowed:",
                "    - source-backed",
                "    - design-inference",
                "    - policy-choice",
                "    - open-assumption",
            ]
        )
        + "\n",
    )
    _write_json(
        root / "artifacts" / "planner" / "research" / "bibliography-graph.json",
        {
            "graph_id": "g1",
            "created_at": "2026-03-10T00:00:00Z",
            "nodes": [
                {"id": "src-1", "type": "source", "label": "Source", "title": "Source", "link": "https://example.com/s"},
                {"id": "claim-1", "type": "claim", "label": "Claim", "title": "Claim"},
                {"id": "artifact-1", "type": "artifact", "label": "Planner Game", "title": "docs/planner-game-model.md"},
                {"id": "artifact-2", "type": "artifact", "label": "Impl Game", "title": "docs/implementation-game-model.md"},
                {"id": "artifact-3", "type": "artifact", "label": "Scoring", "title": "docs/game-scoring-model.md"},
                {"id": "artifact-4", "type": "artifact", "label": "Assumptions", "title": "docs/research-assumptions.md"},
                {"id": "artifact-5", "type": "artifact", "label": "Task Graph", "title": "spec/task-graph.schema.yaml"},
            ],
            "edges": [],
        },
    )
    _write_json(
        root / "artifacts" / "planner" / "research" / "claim-registry.json",
        {
            "registry_id": "r1",
            "created_at": "2026-03-10T00:00:00Z",
            "artifacts": [
                {
                    "artifact_path": "docs/planner-game-model.md",
                    "artifact_node_id": "artifact-1",
                    "required": True,
                    "claims": [
                        {
                            "claim_id": "c1",
                            "summary": "Planner game claim",
                            "category": "design-inference",
                            "source_ids": ([] if invalid_design_inference else ["src-1"]),
                            "bibliography_claim_ids": ([] if invalid_design_inference else ["claim-1"]),
                        }
                    ],
                },
                {
                    "artifact_path": "docs/implementation-game-model.md",
                    "artifact_node_id": "artifact-2",
                    "required": True,
                    "claims": [{"claim_id": "c2", "summary": "Impl claim", "category": "policy-choice", "rationale": "policy"}],
                },
                {
                    "artifact_path": "docs/game-scoring-model.md",
                    "artifact_node_id": "artifact-3",
                    "required": True,
                    "claims": [{"claim_id": "c3", "summary": "Score claim", "category": "policy-choice", "rationale": "policy"}],
                },
                {
                    "artifact_path": "docs/research-assumptions.md",
                    "artifact_node_id": "artifact-4",
                    "required": True,
                    "claims": [{"claim_id": "c4", "summary": "Assumption categories", "category": "policy-choice", "rationale": "policy"}],
                },
                {
                    "artifact_path": "spec/task-graph.schema.yaml",
                    "artifact_node_id": "artifact-5",
                    "required": True,
                    "claims": [{"claim_id": "c5", "summary": "Graph claim", "category": "design-inference", "source_ids": ["src-1"]}],
                },
            ],
        },
    )
    for path in [
        "docs/planner-game-model.md",
        "docs/implementation-game-model.md",
        "docs/game-scoring-model.md",
        "docs/research-assumptions.md",
        "spec/task-graph.schema.yaml",
    ]:
        _write_text(root / path, "placeholder\n")


def test_citation_check_passes_for_valid_registry(tmp_path: Path) -> None:
    _seed_repo(tmp_path)
    code, report = check_citations(tmp_path.as_posix())
    assert code == 0
    assert report["command"] == "citation-check"
    assert report["artifact_id"] == "planner-research-citations"
    assert report["status"] == "ok"
    assert report["blockers"] == []
    assert report["next_validations"] == []
    assert report["ok"] is True


def test_citation_check_fails_for_missing_source_reference(tmp_path: Path) -> None:
    _seed_repo(tmp_path, invalid_design_inference=True)
    code, report = check_citations(tmp_path.as_posix())
    assert code == 1
    assert report["command"] == "citation-check"
    assert report["status"] == "blocked"
    assert report["blockers"]
    assert report["errors"] == report["blockers"]
