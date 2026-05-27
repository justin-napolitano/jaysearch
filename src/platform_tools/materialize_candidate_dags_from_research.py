from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "materialize-candidate-dags-from-research"
DEFAULT_OUTPUT_ROOT = Path("artifacts/research-candidate-dags/runs")
DEFAULT_EXECPLAN_REF = ".agent/execplans/20260527-research-candidate-to-dag-adapter-v1-codex-01-execplan.md"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("rcdag-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in normalized.split("-") if part)[:80] or "candidate"


def _candidate_slug(value: str) -> str:
    slug = _slug(value)
    if len(slug) < 64:
        return slug
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{slug[:52]}-{digest}"


def _candidate_by_id(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        if candidate_id:
            by_id[candidate_id] = candidate
    return by_id


def _ranked_candidate_ids(recommendation: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for item in _dict_list(recommendation.get("ranked_candidates", [])):
        candidate_id = str(item.get("candidate_id", "")).strip()
        if candidate_id:
            ids.append(candidate_id)
    recommended = str(recommendation.get("recommended_candidate_id", "")).strip()
    if recommended and recommended not in ids:
        ids.insert(0, recommended)
    return ids


def _promotion_status_by_candidate_id(recommendation: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for item in _dict_list(recommendation.get("ranked_candidates", [])):
        candidate_id = str(item.get("candidate_id", "")).strip()
        if candidate_id:
            statuses[candidate_id] = str(item.get("promotion_status", "")).strip() or "unknown"
    return statuses


def _risk_level(candidate: dict[str, Any]) -> str:
    priors = candidate.get("feasibility_priors", {})
    if not isinstance(priors, dict):
        return "medium"
    if str(priors.get("implementation_risk", "")).strip() == "high":
        return "high"
    if str(priors.get("dependency_risk", "")).strip() == "high":
        return "high"
    if str(priors.get("implementation_risk", "")).strip() == "low":
        return "low"
    return "medium"


def _surface_node(
    *,
    candidate: dict[str, Any],
    candidate_ref: str,
    family: str,
    node_id: str,
    title: str,
    changes: list[str],
    fallback_change: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    owned_changes = changes or [fallback_change]
    expected_outputs = [f"{title}: {item}" for item in owned_changes]
    return {
        "node_id": node_id,
        "title": title,
        "node_type": "runtime" if family in {"runtime", "handoff"} else family,
        "status": "planned",
        "goal": f"{title} for research candidate {candidate_id}: {str(candidate.get('approach_summary', '')).strip()}",
        "owned_changes": owned_changes,
        "expected_outputs": expected_outputs,
        "validation_commands": ["uv run pytest tests/test_materialize_candidate_dags_from_research.py"],
        "acceptance_checks": [
            f"{title} preserves candidate intent from {candidate_id}",
            "candidate DAG remains consumable by select-candidate-dag",
        ],
        "source_research_candidate_ref": candidate_ref,
        "source_research_candidate_id": candidate_id,
        "evidence_refs": evidence_refs,
        "risk_level": _risk_level(candidate),
        "non_goals": _string_list(candidate.get("non_goals", [])),
    }


def _candidate_dag(
    *,
    candidate: dict[str, Any],
    candidate_ref: str,
    recommendation_ref: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    slug = _candidate_slug(candidate_id)
    contract_changes = _string_list(candidate.get("contract_changes", []))
    runtime_changes = _string_list(candidate.get("runtime_changes", []))
    validation_changes = _string_list(candidate.get("validation_changes", []))
    docs_changes = _string_list(candidate.get("docs_changes", []))
    handoff_requirements = _string_list(candidate.get("handoff_requirements", []))
    candidate_evidence = sorted(set(evidence_refs + _string_list(candidate.get("evidence_refs", []))))

    nodes = [
        _surface_node(
            candidate=candidate,
            candidate_ref=candidate_ref,
            family="contract",
            node_id=f"{slug}_contract_surface",
            title="Contract surface",
            changes=contract_changes,
            fallback_change="confirm no contract surface changes are required",
            evidence_refs=candidate_evidence,
        ),
        _surface_node(
            candidate=candidate,
            candidate_ref=candidate_ref,
            family="runtime",
            node_id=f"{slug}_runtime_surface",
            title="Runtime surface",
            changes=runtime_changes,
            fallback_change="confirm no runtime surface changes are required",
            evidence_refs=candidate_evidence,
        ),
        _surface_node(
            candidate=candidate,
            candidate_ref=candidate_ref,
            family="validation",
            node_id=f"{slug}_validation_surface",
            title="Validation surface",
            changes=validation_changes,
            fallback_change="validate generated candidate DAG intent",
            evidence_refs=candidate_evidence,
        ),
        _surface_node(
            candidate=candidate,
            candidate_ref=candidate_ref,
            family="documentation",
            node_id=f"{slug}_documentation_surface",
            title="Documentation surface",
            changes=docs_changes,
            fallback_change="document generated candidate DAG handoff",
            evidence_refs=candidate_evidence,
        ),
        _surface_node(
            candidate=candidate,
            candidate_ref=candidate_ref,
            family="handoff",
            node_id=f"{slug}_handoff_surface",
            title="Handoff surface",
            changes=handoff_requirements,
            fallback_change="carry selected candidate intent into execution units",
            evidence_refs=candidate_evidence,
        ),
    ]
    return {
        "graph_id": f"{slug}-research-candidate-dag",
        "graph_type": "implementation_dag",
        "version": "v1",
        "purpose": f"Candidate DAG materialized from research candidate {candidate_id}.",
        "source_recommendation_ref": recommendation_ref,
        "source_research_candidate_ref": candidate_ref,
        "source_artifacts": sorted(set([recommendation_ref, candidate_ref] + candidate_evidence)),
        "nodes": nodes,
        "edges": [
            {
                "edge_id": "runtime-depends-on-contract",
                "from_node_id": f"{slug}_runtime_surface",
                "to_node_id": f"{slug}_contract_surface",
                "relation": "depends_on",
            },
            {
                "edge_id": "validation-depends-on-runtime",
                "from_node_id": f"{slug}_validation_surface",
                "to_node_id": f"{slug}_runtime_surface",
                "relation": "depends_on",
            },
            {
                "edge_id": "documentation-depends-on-contract",
                "from_node_id": f"{slug}_documentation_surface",
                "to_node_id": f"{slug}_contract_surface",
                "relation": "depends_on",
            },
            {
                "edge_id": "handoff-depends-on-validation",
                "from_node_id": f"{slug}_handoff_surface",
                "to_node_id": f"{slug}_validation_surface",
                "relation": "depends_on",
            },
            {
                "edge_id": "handoff-depends-on-documentation",
                "from_node_id": f"{slug}_handoff_surface",
                "to_node_id": f"{slug}_documentation_surface",
                "relation": "depends_on",
            },
        ],
    }


def materialize_candidate_dags_from_research(
    *,
    root: str = ".",
    research_recommendation_path: str,
    candidate_paths: list[str],
    evidence_packet_path: str | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    max_dags: int = 3,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    recommendation = _load_json(repo_root / research_recommendation_path)
    candidates = [_load_json(repo_root / path) for path in candidate_paths]
    evidence_packet = _load_json(repo_root / evidence_packet_path) if evidence_packet_path else None
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(recommendation.get("packet_type", "")).strip() != "research_recommendation_packet":
        blockers.append("research_recommendation_packet_type_invalid")
    if max_dags < 1:
        blockers.append("max_dags_invalid")
    problem_id = str(recommendation.get("problem_id", "")).strip()
    if not problem_id:
        blockers.append("research_recommendation_missing_problem_id")
    if not candidates:
        blockers.append("research_candidate_packets_missing")
    for index, candidate in enumerate(candidates, start=1):
        if str(candidate.get("packet_type", "")).strip() != "research_candidate_packet":
            blockers.append(f"research_candidate_packet_type_invalid:{index}")
        if problem_id and str(candidate.get("problem_id", "")).strip() != problem_id:
            blockers.append(f"research_candidate_problem_mismatch:{index}")
    if evidence_packet is not None and str(evidence_packet.get("packet_type", "")).strip() != "evidence_packet":
        blockers.append("evidence_packet_type_invalid")

    candidates_by_id = _candidate_by_id(candidates)
    ranked_ids = _ranked_candidate_ids(recommendation)
    promotion_statuses = _promotion_status_by_candidate_id(recommendation)
    missing_ranked = [candidate_id for candidate_id in ranked_ids if candidate_id not in candidates_by_id]
    for candidate_id in missing_ranked:
        blockers.append(f"ranked_candidate_packet_missing:{candidate_id}")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "research_recommendation_path": str((repo_root / research_recommendation_path).resolve()),
                "candidate_paths": [str((repo_root / path).resolve()) for path in candidate_paths],
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "candidate-dag-adapter.report.json", report)
        return 1, report

    evidence_refs = _string_list(recommendation.get("evidence_refs", []))
    if evidence_packet_path:
        evidence_refs.append(evidence_packet_path)

    candidate_dag_refs: list[dict[str, Any]] = []
    generated_dag_paths: list[str] = []
    skipped_candidate_ids: list[str] = []
    recommendation_ref = str((repo_root / research_recommendation_path).resolve())
    candidate_path_by_id = {
        str(_load_json(repo_root / path).get("candidate_id", "")).strip(): path
        for path in candidate_paths
    }
    for candidate_id in ranked_ids[:max_dags]:
        candidate = candidates_by_id[candidate_id]
        candidate_ref = str((repo_root / candidate_path_by_id[candidate_id]).resolve())
        dag = _candidate_dag(
            candidate=candidate,
            candidate_ref=candidate_ref,
            recommendation_ref=recommendation_ref,
            evidence_refs=evidence_refs,
        )
        candidate_slug = _candidate_slug(candidate_id)
        dag_path = write_json(run_root / f"{candidate_slug}.candidate-dag.json", dag)
        dag_ref = dag_path.relative_to(repo_root).as_posix()
        generated_dag_paths.append(dag_ref)
        candidate_blockers = []
        if promotion_statuses.get(candidate_id, "promoted") != "promoted":
            candidate_blockers.append(f"research_candidate_not_promoted:{candidate_id}")
        candidate_dag_refs.append(
            {
                "candidate_id": f"research_candidate_{candidate_slug}",
                "source_research_candidate_id": candidate_id,
                "dag_ref": dag_ref,
                "candidate_family": str(candidate.get("candidate_family", "")).strip() or "research_candidate",
                "source_label": f"research candidate {candidate_id}",
                "producer_ref": COMMAND,
                "evidence_refs": sorted(set(evidence_refs + _string_list(candidate.get("evidence_refs", [])))),
                "blockers": candidate_blockers,
            }
        )
    skipped_candidate_ids = ranked_ids[max_dags:]

    if not candidate_dag_refs:
        blockers.append("no_promoted_research_candidates_for_dag")

    manifest = {
        "packet_type": "candidate_dag_manifest",
        "packet_version": "v1",
        "packet_id": f"candidate-dag-manifest:{run_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "manifest_id": f"research-candidate-dag-manifest:{run_id}",
        "source_problem_ref": problem_id,
        "source_execplan_ref": DEFAULT_EXECPLAN_REF,
        "source_recommendation_ref": recommendation_ref,
        "candidate_dag_refs": candidate_dag_refs,
        "selection_policy_ref": "docs/candidate-dag-selection-v1.md",
        "evidence_refs": sorted(set(evidence_refs)),
        "blockers": sorted(set(blockers)),
    }
    manifest_path = write_json(run_root / "candidate-dag-manifest.packet.json", manifest)

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "research_recommendation_path": recommendation_ref,
            "candidate_paths": [str((repo_root / path).resolve()) for path in candidate_paths],
            "candidate_dag_manifest_path": manifest_path.relative_to(repo_root).as_posix(),
            "candidate_dag_paths": generated_dag_paths,
            "generated_candidate_count": len(generated_dag_paths),
            "skipped_candidate_ids": skipped_candidate_ids,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "candidate-dag-adapter.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--research-recommendation-path", required=True)
    parser.add_argument("--candidate", action="append", dest="candidates", required=True)
    parser.add_argument("--evidence-packet-path", default=None)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--max-dags", type=int, default=3)
    args = parser.parse_args()
    try:
        code, report = materialize_candidate_dags_from_research(
            root=args.root,
            research_recommendation_path=args.research_recommendation_path,
            candidate_paths=args.candidates,
            evidence_packet_path=args.evidence_packet_path,
            output_root=args.output_root,
            max_dags=args.max_dags,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
