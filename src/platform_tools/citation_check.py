from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED_ARTIFACTS = {
    "docs/planner-game-model.md",
    "docs/implementation-game-model.md",
    "docs/game-scoring-model.md",
    "docs/research-assumptions.md",
    "spec/task-graph.schema.yaml",
}
COMMAND = "citation-check"
ARTIFACT_ID = "planner-research-citations"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _report(
    *,
    ok: bool,
    blockers: list[str],
    registry_path: str,
    graph_path: str,
    artifact_count: int = 0,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    ordered_blockers = sorted(blockers)
    return {
        "command": COMMAND,
        "artifact_id": ARTIFACT_ID,
        "status": "ok" if ok else "blocked",
        "blockers": ordered_blockers,
        "next_validations": [],
        "ok": ok,
        "registry_path": registry_path,
        "graph_path": graph_path,
        "artifact_count": artifact_count,
        "error_count": len(ordered_blockers),
        "errors": ordered_blockers,
        "evidence_refs": sorted(evidence_refs or []),
    }


def check_citations(root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root)
    registry_path = base / "artifacts" / "planner" / "research" / "claim-registry.json"
    graph_path = base / "artifacts" / "planner" / "research" / "bibliography-graph.json"
    schema_path = base / "spec" / "claim-registry.schema.yaml"
    errors: list[str] = []
    evidence_refs = [path.as_posix() for path in (registry_path, graph_path, schema_path) if path.exists()]

    if not registry_path.exists():
        return 1, _report(
            ok=False,
            blockers=["missing_claim_registry"],
            registry_path=registry_path.as_posix(),
            graph_path=graph_path.as_posix(),
            evidence_refs=evidence_refs,
        )
    if not graph_path.exists():
        return 1, _report(
            ok=False,
            blockers=["missing_bibliography_graph"],
            registry_path=registry_path.as_posix(),
            graph_path=graph_path.as_posix(),
            evidence_refs=evidence_refs,
        )
    if not schema_path.exists():
        return 1, _report(
            ok=False,
            blockers=["missing_claim_registry_schema"],
            registry_path=registry_path.as_posix(),
            graph_path=graph_path.as_posix(),
            evidence_refs=evidence_refs,
        )

    registry = _load_json(registry_path)
    graph = _load_json(graph_path)
    schema = _load_yaml(schema_path)

    for field in schema.get("registry", {}).get("required_fields", []):
        if field not in registry:
            errors.append(f"missing_registry_field:{field}")

    graph_nodes = {node["id"]: node for node in graph.get("nodes", []) if isinstance(node, dict) and "id" in node}
    allowed_categories = set(schema.get("claim_entry", {}).get("category_allowed", []))

    artifact_entries = registry.get("artifacts", [])
    seen_artifacts: set[str] = set()
    for entry in artifact_entries:
        if not isinstance(entry, dict):
            errors.append("invalid_artifact_entry_type")
            continue
        for field in schema.get("artifact_entry", {}).get("required_fields", []):
            if field not in entry:
                errors.append(f"missing_artifact_entry_field:{entry.get('artifact_path', '?')}:{field}")
        artifact_path = str(entry.get("artifact_path", "")).strip()
        if artifact_path:
            seen_artifacts.add(artifact_path)
            if not (base / artifact_path).exists():
                errors.append(f"missing_artifact_file:{artifact_path}")
        artifact_node_id = str(entry.get("artifact_node_id", "")).strip()
        if artifact_node_id and artifact_node_id not in graph_nodes:
            errors.append(f"missing_artifact_node:{artifact_path}:{artifact_node_id}")
        claims = entry.get("claims", [])
        if not claims:
            errors.append(f"missing_claims:{artifact_path}")
        for claim in claims:
            if not isinstance(claim, dict):
                errors.append(f"invalid_claim_entry_type:{artifact_path}")
                continue
            for field in schema.get("claim_entry", {}).get("required_fields", []):
                if field not in claim:
                    errors.append(f"missing_claim_field:{artifact_path}:{field}")
            category = str(claim.get("category", "")).strip()
            if category not in allowed_categories:
                errors.append(f"invalid_claim_category:{artifact_path}:{category}")
            source_ids = claim.get("source_ids", [])
            bibliography_claim_ids = claim.get("bibliography_claim_ids", [])
            if category == "source-backed" and not source_ids:
                errors.append(f"source_backed_missing_sources:{artifact_path}:{claim.get('claim_id', '?')}")
            if category == "design-inference" and not (source_ids or bibliography_claim_ids):
                errors.append(f"design_inference_missing_refs:{artifact_path}:{claim.get('claim_id', '?')}")
            if category in {"policy-choice", "open-assumption"} and not str(claim.get("rationale", "")).strip():
                errors.append(f"category_missing_rationale:{artifact_path}:{claim.get('claim_id', '?')}")
            for source_id in source_ids:
                node = graph_nodes.get(source_id)
                if node is None or node.get("type") != "source":
                    errors.append(f"unknown_source_id:{artifact_path}:{source_id}")
            for claim_id in bibliography_claim_ids:
                node = graph_nodes.get(claim_id)
                if node is None or node.get("type") != "claim":
                    errors.append(f"unknown_bibliography_claim_id:{artifact_path}:{claim_id}")

    for artifact in sorted(REQUIRED_ARTIFACTS - seen_artifacts):
        errors.append(f"missing_required_artifact_registry_entry:{artifact}")

    report = _report(
        ok=not errors,
        blockers=errors,
        registry_path=registry_path.as_posix(),
        graph_path=graph_path.as_posix(),
        artifact_count=len(artifact_entries),
        evidence_refs=evidence_refs,
    )
    return (1 if errors else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    try:
        code, report = check_citations(args.root)
    except (FileNotFoundError, PermissionError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        code = 1
        report = _report(
            ok=False,
            blockers=[f"{exc.__class__.__name__}:{exc}"],
            registry_path=(Path(args.root) / "artifacts" / "planner" / "research" / "claim-registry.json").as_posix(),
            graph_path=(Path(args.root) / "artifacts" / "planner" / "research" / "bibliography-graph.json").as_posix(),
            evidence_refs=[],
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
