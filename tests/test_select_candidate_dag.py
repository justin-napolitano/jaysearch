from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.select_candidate_dag import select_candidate_dag


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _dag(*, graph_id: str, nodes: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, object]:
    return {
        "graph_id": graph_id,
        "graph_type": "implementation_dag",
        "version": "v1",
        "purpose": "test DAG",
        "source_artifacts": ["docs/candidate-dag-selection-v1.md"],
        "nodes": nodes,
        "edges": edges,
    }


def _node(node_id: str, *, evidence: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "node_id": node_id,
        "title": node_id,
        "node_type": "runtime",
        "status": "planned",
        "goal": f"Build {node_id}",
        "owned_changes": [f"src/{node_id}.py"],
        "expected_outputs": [f"{node_id} output"],
    }
    if evidence:
        payload["evidence_refs"] = ["docs/candidate-dag-selection-v1.md"]
    return payload


def _manifest(root: Path, candidates: list[dict[str, object]]) -> str:
    payload = {
        "packet_type": "candidate_dag_manifest",
        "packet_version": "v1",
        "packet_id": "candidate-dag-manifest:test",
        "created_at": "2026-05-26T00:00:00Z",
        "producer": "test",
        "manifest_id": "test-manifest",
        "source_problem_ref": "problem-node.packet.json",
        "source_execplan_ref": "execplan.packet.json",
        "candidate_dag_refs": candidates,
        "selection_policy_ref": "docs/candidate-dag-selection-v1.md",
        "evidence_refs": ["docs/plan-quality-metrics-v1.md"],
        "blockers": [],
    }
    return _write_json(root / "artifacts" / "manifest.packet.json", payload)


def test_select_candidate_dag_selects_best_valid_dag(tmp_path: Path) -> None:
    compact = _write_json(
        tmp_path / "artifacts" / "compact.json",
        _dag(
            graph_id="compact",
            nodes=[_node("define"), _node("implement"), _node("test")],
            edges=[
                {"from_node_id": "implement", "to_node_id": "define", "relation": "depends_on"},
                {"from_node_id": "test", "to_node_id": "implement", "relation": "depends_on"},
            ],
        ),
    )
    bloated = _write_json(
        tmp_path / "artifacts" / "bloated.json",
        _dag(
            graph_id="bloated",
            nodes=[_node(f"node-{index}") for index in range(1, 13)],
            edges=[
                {
                    "from_node_id": f"node-{index + 1}",
                    "to_node_id": f"node-{index}",
                    "relation": "depends_on",
                }
                for index in range(1, 12)
            ],
        ),
    )
    manifest = _manifest(
        tmp_path,
        [
            {
                "candidate_id": "bloated",
                "dag_ref": bloated,
                "candidate_family": "over_split",
                "source_label": "bloated",
                "producer_ref": "test",
                "evidence_refs": [],
                "blockers": [],
            },
            {
                "candidate_id": "compact",
                "dag_ref": compact,
                "candidate_family": "baseline",
                "source_label": "compact",
                "producer_ref": "test",
                "evidence_refs": [],
                "blockers": [],
            },
        ],
    )

    code, report = select_candidate_dag(root=tmp_path.as_posix(), manifest_path=manifest)

    assert code == 0
    assert report["ok"] is True
    assert report["selected_dag_ref"].endswith("compact.json")
    selection = json.loads(Path(report["candidate_dag_selection_path"]).read_text(encoding="utf-8"))
    assert selection["packet_type"] == "candidate_dag_selection"
    assert selection["selection_policy"]["uses_networkx"] is True


def test_select_candidate_dag_preserves_cyclic_dag_blocker(tmp_path: Path) -> None:
    cyclic = _write_json(
        tmp_path / "artifacts" / "cyclic.json",
        _dag(
            graph_id="cyclic",
            nodes=[_node("a"), _node("b")],
            edges=[
                {"from_node_id": "a", "to_node_id": "b", "relation": "depends_on"},
                {"from_node_id": "b", "to_node_id": "a", "relation": "depends_on"},
            ],
        ),
    )
    manifest = _manifest(
        tmp_path,
        [
            {
                "candidate_id": "cyclic",
                "dag_ref": cyclic,
                "candidate_family": "invalid",
                "source_label": "cyclic",
                "producer_ref": "test",
                "evidence_refs": [],
                "blockers": [],
            }
        ],
    )

    code, report = select_candidate_dag(root=tmp_path.as_posix(), manifest_path=manifest)

    assert code == 1
    assert "no_eligible_candidate_dags" in report["blockers"]
    evaluation_path = Path(report["evaluation_packet_paths"][0])
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    assert evaluation["promotion_status"] == "blocked"
    assert "dag_contains_cycle" in evaluation["hard_gate_blockers"]
