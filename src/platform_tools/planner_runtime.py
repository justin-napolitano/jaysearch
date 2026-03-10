from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

import yaml


SESSION_COLLECTIONS = [
    "goals",
    "constraints",
    "assumptions",
    "decisions",
    "questions",
    "tasks",
    "risks",
    "evidence",
]


@dataclass
class PlannerPaths:
    root: Path

    @property
    def sessions_root(self) -> Path:
        return self.root / "artifacts" / "planner" / "sessions"

    @property
    def graphs_root(self) -> Path:
        return self.root / "artifacts" / "planner" / "graphs"

    @property
    def bibliography_graph(self) -> Path:
        return self.root / "artifacts" / "planner" / "research" / "bibliography-graph.json"

    @property
    def references_doc(self) -> Path:
        return self.root / "docs" / "references.md"

    @property
    def assumptions_doc(self) -> Path:
        return self.root / "docs" / "research-assumptions.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "session"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.as_posix()}: expected mapping")
    return loaded


def _session_dir(paths: PlannerPaths, session_id: str) -> Path:
    return paths.sessions_root / session_id


def create_session(
    *,
    root: str = ".",
    title: str,
    objective: str = "",
    mode: str = "adversarial",
) -> dict[str, Any]:
    paths = PlannerPaths(Path(root))
    session_id = f"ps-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_slugify(title)[:24]}"
    session_dir = _session_dir(paths, session_id)
    session = {
        "session_id": session_id,
        "title": title,
        "objective": objective,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "status": "active",
        "mode": mode,
        "related_graph_ids": [],
        "related_execplans": [],
        "commit_refs": [],
    }
    extracted = {name: [] for name in SESSION_COLLECTIONS}
    _write_json(session_dir / "session.json", session)
    _write_json(session_dir / "extracted-state.json", extracted)
    (session_dir / "transcript.jsonl").write_text("", encoding="utf-8")
    return {
        "tool": "planner_session_start",
        "ok": True,
        "session_id": session_id,
        "session_dir": session_dir.as_posix(),
    }


def load_session(*, root: str = ".", session_id: str) -> dict[str, Any]:
    paths = PlannerPaths(Path(root))
    session_dir = _session_dir(paths, session_id)
    session = _read_json(session_dir / "session.json")
    extracted = _read_json(session_dir / "extracted-state.json")
    transcript_path = session_dir / "transcript.jsonl"
    transcript = [
        json.loads(line)
        for line in transcript_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "tool": "planner_session_show",
        "session": session,
        "extracted_state": extracted,
        "transcript_count": len(transcript),
    }


def summarize_session(*, root: str = ".", session_id: str) -> dict[str, Any]:
    loaded = load_session(root=root, session_id=session_id)
    extracted = loaded["extracted_state"]
    counts = {key: len(value) for key, value in extracted.items()}
    return {
        "tool": "planner_session_summarize",
        "session_id": session_id,
        "title": loaded["session"]["title"],
        "status": loaded["session"]["status"],
        "mode": loaded["session"]["mode"],
        "counts": counts,
    }


def session_chat(*, root: str = ".", session_id: str) -> dict[str, Any]:
    paths = PlannerPaths(Path(root))
    session_dir = _session_dir(paths, session_id)
    transcript_path = session_dir / "transcript.jsonl"
    extracted_path = session_dir / "extracted-state.json"
    extracted = _read_json(extracted_path)

    print("planner chat: enter lines, /exit to stop")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if line in {"/exit", "/quit"}:
            break
        if not line:
            continue
        entry = {"timestamp": utc_now(), "speaker": "operator", "text": line}
        transcript_path.write_text(
            transcript_path.read_text(encoding="utf-8") + json.dumps(entry) + "\n",
            encoding="utf-8",
        )
        lowered = line.lower()
        if lowered.startswith("goal:"):
            extracted["goals"].append({"title": line[5:].strip(), "success_criteria": "", "scope": ""})
        elif lowered.startswith("constraint:"):
            extracted["constraints"].append(
                {"constraint": line[11:].strip(), "constraint_type": "platform"}
            )
        elif lowered.startswith("decision:"):
            extracted["decisions"].append(
                {
                    "decision": line[9:].strip(),
                    "rationale": "",
                    "alternatives_considered": [],
                    "title": line[9:].strip(),
                }
            )
        elif lowered.endswith("?"):
            extracted["questions"].append({"question": line, "blocking": True, "title": line})
        else:
            extracted["tasks"].append(
                {
                    "title": line,
                    "description": line,
                    "ready_definition": "",
                    "done_definition": "",
                }
            )
    _write_json(extracted_path, extracted)
    return {"tool": "planner_session_chat", "ok": True, "session_id": session_id}


def _normalize_item(node_type: str, item: Any, index: int, session_id: str) -> dict[str, Any]:
    if isinstance(item, str):
        item = {"title": item}
    if not isinstance(item, dict):
        item = {"title": str(item)}
    title = str(item.get("title") or item.get(node_type) or f"{node_type}-{index}").strip()
    summary = str(item.get("summary") or title).strip()
    base = {
        "node_id": f"{node_type}-{index}",
        "node_type": node_type,
        "title": title,
        "summary": summary,
        "status": item.get("status", "draft"),
        "priority": item.get("priority", "P2"),
        "owner": item.get("owner", "agent/codex-01"),
        "created_at": item.get("created_at", utc_now()),
        "updated_at": item.get("updated_at", utc_now()),
        "provenance": {
            "source_session": session_id,
            "source_artifact": "extracted-state.json",
            "recorded_at": utc_now(),
            "commit_refs": item.get("commit_refs", []),
        },
        "evidence_refs": item.get("evidence_refs", []),
        "external_refs": item.get("external_refs", []),
    }
    typed_defaults = {
        "goal": {"success_criteria": item.get("success_criteria", ""), "scope": item.get("scope", "")},
        "decision": {
            "decision": item.get("decision", title),
            "rationale": item.get("rationale", ""),
            "alternatives_considered": item.get("alternatives_considered", []),
        },
        "question": {"question": item.get("question", title), "blocking": item.get("blocking", True)},
        "constraint": {
            "constraint": item.get("constraint", title),
            "constraint_type": item.get("constraint_type", "platform"),
        },
        "task": {
            "description": item.get("description", title),
            "ready_definition": item.get("ready_definition", ""),
            "done_definition": item.get("done_definition", ""),
        },
        "risk": {
            "risk": item.get("risk", title),
            "impact": item.get("impact", ""),
            "mitigation": item.get("mitigation", ""),
        },
        "artifact": {"artifact_type": item.get("artifact_type", "note"), "path": item.get("path", "")},
        "validation": {
            "validation_type": item.get("validation_type", "check"),
            "command": item.get("command", ""),
            "expected_result": item.get("expected_result", ""),
        },
        "tool_run": {
            "tool_name": item.get("tool_name", ""),
            "inputs": item.get("inputs", []),
            "expected_outputs": item.get("expected_outputs", []),
        },
        "handoff": {
            "handoff_to": item.get("handoff_to", ""),
            "entry_criteria": item.get("entry_criteria", ""),
            "exit_criteria": item.get("exit_criteria", ""),
        },
    }
    base.update(typed_defaults.get(node_type, {}))
    return base


def build_graph(*, root: str = ".", session_id: str) -> dict[str, Any]:
    paths = PlannerPaths(Path(root))
    loaded = load_session(root=root, session_id=session_id)
    extracted = loaded["extracted_state"]
    nodes: list[dict[str, Any]] = []
    collection_map = {
        "goals": "goal",
        "constraints": "constraint",
        "assumptions": "artifact",
        "decisions": "decision",
        "questions": "question",
        "tasks": "task",
        "risks": "risk",
        "evidence": "artifact",
    }
    for collection, node_type in collection_map.items():
        for index, item in enumerate(extracted.get(collection, []), start=1):
            nodes.append(_normalize_item(node_type, item, index, session_id))
    graph = {
        "graph_id": f"pg-{session_id}",
        "session_id": session_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "nodes": nodes,
        "edges": [],
    }
    graph_path = paths.graphs_root / f"{graph['graph_id']}.json"
    _write_json(graph_path, graph)

    session_path = _session_dir(paths, session_id) / "session.json"
    session = _read_json(session_path)
    related_graphs = list(session.get("related_graph_ids", []))
    if graph["graph_id"] not in related_graphs:
        related_graphs.append(graph["graph_id"])
    session["related_graph_ids"] = related_graphs
    session["updated_at"] = utc_now()
    _write_json(session_path, session)

    return {
        "tool": "planner_graph_build",
        "ok": True,
        "graph_id": graph["graph_id"],
        "graph_path": graph_path.as_posix(),
        "node_count": len(nodes),
    }


def _load_graph(*, root: str = ".", graph_id: str) -> dict[str, Any]:
    paths = PlannerPaths(Path(root))
    return _read_json(paths.graphs_root / f"{graph_id}.json")


def show_graph(*, root: str = ".", graph_id: str, status: str | None = None) -> dict[str, Any]:
    graph = _load_graph(root=root, graph_id=graph_id)
    nodes = graph["nodes"]
    if status is not None:
        nodes = [node for node in nodes if node.get("status") == status]
    return {
        "tool": "planner_graph_show",
        "graph_id": graph_id,
        "node_count": len(nodes),
        "nodes": nodes,
    }


def _validate_graph_node(node: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = spec["node"]["required_fields"]
    for field in required_fields:
        if field not in node:
            errors.append(f"missing_node_field:{node.get('node_id', '?')}:{field}")
    if node.get("node_type") not in spec["node"]["node_type_allowed"]:
        errors.append(f"invalid_node_type:{node.get('node_id', '?')}")
    if node.get("status") not in spec["node"]["status_allowed"]:
        errors.append(f"invalid_node_status:{node.get('node_id', '?')}:{node.get('status')}")
    if node.get("priority") not in spec["node"]["priority_allowed"]:
        errors.append(f"invalid_node_priority:{node.get('node_id', '?')}:{node.get('priority')}")
    typed = spec.get("typed_node_requirements", {}).get(node.get("node_type"), {})
    for field in typed.get("required_fields", []):
        if field not in node:
            errors.append(f"missing_typed_field:{node.get('node_id', '?')}:{field}")
    return errors


def validate_graph(*, root: str = ".", graph_id: str) -> tuple[int, dict[str, Any]]:
    graph = _load_graph(root=root, graph_id=graph_id)
    graph_spec = _read_yaml(Path(root) / "spec" / "task-graph.schema.yaml")
    transition_spec = _read_yaml(Path(root) / "spec" / "game-transitions.yaml")
    errors: list[str] = []

    for field in graph_spec["graph"]["required_fields"]:
        if field not in graph:
            errors.append(f"missing_graph_field:{field}")
    shared_statuses = set(transition_spec["shared_statuses"])
    for node in graph.get("nodes", []):
        errors.extend(_validate_graph_node(node, graph_spec))
        if node.get("status") not in shared_statuses:
            errors.append(f"status_not_in_transition_spec:{node.get('node_id', '?')}:{node.get('status')}")

    code = 1 if errors else 0
    return code, {
        "tool": "planner_graph_validate",
        "ok": not errors,
        "graph_id": graph_id,
        "error_count": len(errors),
        "errors": errors,
    }


def validate_research(*, root: str = ".") -> tuple[int, dict[str, Any]]:
    paths = PlannerPaths(Path(root))
    errors: list[str] = []
    if not paths.references_doc.exists():
        errors.append("missing_references_doc")
    if not paths.assumptions_doc.exists():
        errors.append("missing_assumptions_doc")
    if not paths.bibliography_graph.exists():
        errors.append("missing_bibliography_graph")
    if errors:
        return 1, {"tool": "planner_research_validate", "ok": False, "errors": errors}

    graph = _read_json(paths.bibliography_graph)
    graph_spec = _read_yaml(Path(root) / "spec" / "bibliography-graph.schema.yaml")
    for field in graph_spec["graph"]["required_fields"]:
        if field not in graph:
            errors.append(f"missing_bibliography_graph_field:{field}")
    reference_links = set(re.findall(r"https?://\S+", paths.references_doc.read_text(encoding="utf-8")))
    graph_sources = [node for node in graph.get("nodes", []) if node.get("type") == "source"]
    graph_links = {node.get("link") for node in graph_sources if node.get("link")}
    if not reference_links:
        errors.append("references_doc_has_no_links")
    missing_links = sorted(reference_links - graph_links)
    if missing_links:
        errors.append(f"missing_reference_links_in_graph:{len(missing_links)}")
    assumptions_text = paths.assumptions_doc.read_text(encoding="utf-8")
    for marker in ("source-backed", "design-inference", "policy-choice", "open-assumption"):
        if marker not in assumptions_text:
            errors.append(f"missing_assumption_category:{marker}")
    for node in graph_sources:
        if not node.get("link"):
            errors.append(f"source_node_missing_link:{node.get('id', '?')}")
    code = 1 if errors else 0
    return code, {
        "tool": "planner_research_validate",
        "ok": not errors,
        "reference_link_count": len(reference_links),
        "graph_source_count": len(graph_sources),
        "error_count": len(errors),
        "errors": errors,
    }


def validate_all(*, root: str = ".", graph_id: str | None = None) -> tuple[int, dict[str, Any]]:
    research_code, research_report = validate_research(root=root)
    graph_report: dict[str, Any] | None = None
    graph_code = 0
    if graph_id is not None:
        graph_code, graph_report = validate_graph(root=root, graph_id=graph_id)
    code = 1 if research_code or graph_code else 0
    return code, {
        "tool": "planner_validate",
        "ok": code == 0,
        "research": research_report,
        "graph": graph_report,
    }
