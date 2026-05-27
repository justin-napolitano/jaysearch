from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any

from platform_tools.materialize_candidate_dags_from_research import (
    materialize_candidate_dags_from_research,
)
from platform_tools.materialize_research_candidate_tree import materialize_research_candidate_tree
from platform_tools.materialize_research_evaluations import materialize_research_evaluations
from platform_tools.materialize_research_hypotheses import materialize_research_hypotheses
from platform_tools.materialize_research_recommendation import materialize_research_recommendation
from platform_tools.materialize_selected_dag_execution_units import (
    materialize_selected_dag_execution_units,
)
from platform_tools.orchestrate_question_research_handoff import (
    run_question_research_handoff_workflow,
)
from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json
from platform_tools.select_candidate_dag import select_candidate_dag


COMMAND = "run-jaysearch-question-dag-demo"
DEFAULT_OUTPUT_ROOT = Path("artifacts/demo/question-dag-runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("qdag-%Y%m%dT%H%M%SZ")


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in normalized.split("-") if part)[:80] or "question"


def _question_packet(*, question: str, topic: str, run_id: str) -> dict[str, Any]:
    question_id = f"research-question:{_slug(topic or question)}"
    return {
        "packet_type": "research_question_packet",
        "packet_version": "v1",
        "packet_id": f"{question_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "question_id": question_id,
        "project_id": "jaysearch-demo",
        "question_text": question,
        "question_type": "implementation_strategy",
        "goal": "Turn an ambiguous user question into a researched candidate DAG and execution-unit handoff.",
        "decision_target": "Which bounded plan graph should be developed next?",
        "decision_consequence": "The selected DAG becomes the source of implementation-ready execution units.",
        "blocked_work_if_unanswered": [
            "candidate DAG generation",
            "execution-unit materialization",
            "implementation planning",
        ],
        "constraints": [
            "use bounded fixture evidence in V1",
            "preserve packet lineage",
            "do not claim autonomous code generation",
        ],
        "evaluation_targets": [
            "acyclic candidate DAG",
            "explicit evidence refs",
            "execution units emitted from selected DAG",
            "clear implementation boundary",
        ],
        "artifact_targets": [
            "candidate_dag_manifest",
            "candidate_dag_selection",
            "dag_execution_unit_manifest",
            "execution_unit",
        ],
    }


def _evidence_packet(*, question_ref: str, topic: str, run_id: str) -> dict[str, Any]:
    return {
        "packet_type": "evidence_packet",
        "packet_version": "v1",
        "packet_id": f"bounded-evidence:{run_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "evidence_id": f"bounded-evidence:{run_id}",
        "problem_id": f"jaysearch-demo:{_slug(topic)}",
        "source_question_ref": question_ref,
        "topic": topic,
        "evidence_mode": "curated_fixture",
        "source_refs": [
            "docs/question-tool-v1.md",
            "docs/research-tool-v1.md",
            "docs/candidate-dag-selection-v1.md",
            "docs/selected-dag-execution-units-v1.md",
            "docs/question-to-dag-demo-v1.md",
            "https://www.w3.org/TR/prov-dm/",
            "https://json-schema.org/understanding-json-schema/reference/object",
            "https://networkx.org/documentation/stable/reference/algorithms/dag.html",
            "https://arxiv.org/abs/2310.06770",
        ],
        "claim_refs": [
            "lineage-must-be-explicit",
            "dag-plans-must-be-validated",
            "implementation-boundary-must-be-honest",
        ],
        "method_refs": [
            "contract-first packet handoff",
            "DAG hard-gate validation",
            "transparent heuristic candidate scoring",
        ],
        "benchmark_refs": [
            "question-to-DAG demo emits selected graph and execution units",
            "local CI validates graph contracts and design iteration",
        ],
        "evidence_summary": (
            "Curated V1 evidence supports explicit provenance, schema-backed packet "
            "handoffs, DAG validation, and an honest implementation boundary."
        ),
        "evidence_refs": [
            "docs/question-tool-v1.md",
            "docs/research-tool-v1.md",
            "docs/candidate-dag-selection-v1.md",
            "docs/selected-dag-execution-units-v1.md",
            "docs/question-to-dag-demo-v1.md",
            "https://www.w3.org/TR/prov-dm/",
            "https://json-schema.org/understanding-json-schema/reference/object",
            "https://networkx.org/documentation/stable/reference/algorithms/dag.html",
            "https://arxiv.org/abs/2310.06770",
        ],
        "claims": [
            {
                "claim_id": "lineage-must-be-explicit",
                "claim": "Question, evidence, DAG selection, and execution-unit outputs should preserve provenance refs.",
                "evidence_refs": ["https://www.w3.org/TR/prov-dm/", "docs/core-contract-spec-v1.md"],
            },
            {
                "claim_id": "dag-plans-must-be-validated",
                "claim": "Candidate plan graphs should be checked for acyclicity, dependency structure, and execution readiness.",
                "evidence_refs": [
                    "https://networkx.org/documentation/stable/reference/algorithms/dag.html",
                    "docs/candidate-dag-selection-v1.md",
                ],
            },
            {
                "claim_id": "implementation-boundary-must-be-honest",
                "claim": "The demo should stop at execution units until candidate generation and code execution are production-ready.",
                "evidence_refs": [
                    "docs/candidate-generation-request-result-v1.md",
                    "docs/selected-dag-execution-units-v1.md",
                ],
            },
        ],
        "limitations": [
            "This V1 demo uses curated fixture evidence rather than live autonomous web research.",
            "Evidence refs are sufficient for presentation lineage, not exhaustive literature review.",
        ],
    }


def _node(
    node_id: str,
    *,
    node_type: str,
    title: str,
    goal: str,
    question_ref: str,
    evidence_ref: str,
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "title": title,
        "node_type": node_type,
        "status": "planned",
        "goal": goal,
        "owned_changes": [f"demo/question-dag/{node_id}.artifact"],
        "expected_outputs": [f"{title} output"],
        "validation_commands": ["uv run pytest tests/test_run_jaysearch_question_dag_demo.py"],
        "source_question_refs": [question_ref],
        "evidence_refs": [
            evidence_ref,
            "docs/question-to-dag-demo-v1.md",
            "docs/selected-dag-execution-units-v1.md",
        ],
    }


def _dag(
    *,
    graph_id: str,
    purpose: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, str]],
    question_ref: str,
    evidence_ref: str,
) -> dict[str, Any]:
    return {
        "graph_id": graph_id,
        "graph_type": "implementation_dag",
        "version": "v1",
        "purpose": purpose,
        "source_question_refs": [question_ref],
        "source_artifacts": [
            evidence_ref,
            "docs/question-to-dag-demo-v1.md",
            "docs/candidate-dag-selection-v1.md",
        ],
        "nodes": nodes,
        "edges": edges,
    }


def _write_candidate_dags(
    *,
    repo_root: Path,
    run_root: Path,
    question_ref: str,
    evidence_ref: str,
    topic_slug: str,
) -> str:
    input_root = run_root / "candidate-dags"
    balanced_nodes = [
        _node(
            "clarify_question",
            node_type="documentation",
            title="Clarify question",
            goal="Normalize the user question into a bounded research question packet.",
            question_ref=question_ref,
            evidence_ref=evidence_ref,
        ),
        _node(
            "collect_evidence",
            node_type="runtime",
            title="Collect bounded evidence",
            goal="Attach curated source refs and explicit claims to support the plan graph.",
            question_ref=question_ref,
            evidence_ref=evidence_ref,
        ),
        _node(
            "draft_candidate_dag",
            node_type="runtime",
            title="Draft candidate DAG",
            goal="Create a compact candidate plan DAG from the question and evidence packet.",
            question_ref=question_ref,
            evidence_ref=evidence_ref,
        ),
        _node(
            "materialize_execution_units",
            node_type="validation",
            title="Materialize execution units",
            goal="Convert the selected DAG into execution-unit packets and stop at implementation boundary.",
            question_ref=question_ref,
            evidence_ref=evidence_ref,
        ),
    ]
    balanced_path = write_json(
        input_root / "balanced-question-dag.json",
        _dag(
            graph_id=f"{topic_slug}-balanced-question-dag",
            purpose="Balanced question-to-DAG flow with explicit evidence and execution boundary.",
            nodes=balanced_nodes,
            edges=[
                {
                    "edge_id": "e1",
                    "from_node_id": "collect_evidence",
                    "to_node_id": "clarify_question",
                    "relation": "depends_on",
                },
                {
                    "edge_id": "e2",
                    "from_node_id": "draft_candidate_dag",
                    "to_node_id": "collect_evidence",
                    "relation": "depends_on",
                },
                {
                    "edge_id": "e3",
                    "from_node_id": "materialize_execution_units",
                    "to_node_id": "draft_candidate_dag",
                    "relation": "depends_on",
                },
            ],
            question_ref=question_ref,
            evidence_ref=evidence_ref,
        ),
    )
    over_split_path = write_json(
        input_root / "over-split-question-dag.json",
        _dag(
            graph_id=f"{topic_slug}-over-split-question-dag",
            purpose="Over-split question-to-DAG flow used as a weaker comparison candidate.",
            nodes=[
                _node(
                    f"micro_question_step_{index}",
                    node_type="runtime",
                    title=f"Micro question step {index}",
                    goal="Over-split the question-to-DAG flow into too many serial steps.",
                    question_ref=question_ref,
                    evidence_ref=evidence_ref,
                )
                for index in range(1, 11)
            ],
            edges=[
                {
                    "edge_id": f"e{index}",
                    "from_node_id": f"micro_question_step_{index + 1}",
                    "to_node_id": f"micro_question_step_{index}",
                    "relation": "depends_on",
                }
                for index in range(1, 10)
            ],
            question_ref=question_ref,
            evidence_ref=evidence_ref,
        ),
    )
    cyclic_path = write_json(
        input_root / "invalid-question-cycle-dag.json",
        _dag(
            graph_id=f"{topic_slug}-invalid-cycle-question-dag",
            purpose="Invalid cyclic question-to-DAG candidate used to show hard-gate preservation.",
            nodes=[
                _node(
                    "research_before_question",
                    node_type="runtime",
                    title="Research before question",
                    goal="Invalidly requires research before the question is clarified.",
                    question_ref=question_ref,
                    evidence_ref=evidence_ref,
                ),
                _node(
                    "question_after_research",
                    node_type="runtime",
                    title="Question after research",
                    goal="Invalidly requires the question after research is complete.",
                    question_ref=question_ref,
                    evidence_ref=evidence_ref,
                ),
            ],
            edges=[
                {
                    "edge_id": "cycle-1",
                    "from_node_id": "research_before_question",
                    "to_node_id": "question_after_research",
                    "relation": "depends_on",
                },
                {
                    "edge_id": "cycle-2",
                    "from_node_id": "question_after_research",
                    "to_node_id": "research_before_question",
                    "relation": "depends_on",
                },
            ],
            question_ref=question_ref,
            evidence_ref=evidence_ref,
        ),
    )
    manifest_path = write_json(
        input_root / "candidate-dag-manifest.packet.json",
        {
            "packet_type": "candidate_dag_manifest",
            "packet_version": "v1",
            "packet_id": f"candidate-dag-manifest:{topic_slug}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "manifest_id": f"question-dag-demo:{topic_slug}",
            "source_problem_ref": question_ref,
            "source_execplan_ref": ".agent/execplans/20260527-question-to-dag-demo-v1-codex-01-execplan.md",
            "candidate_dag_refs": [
                {
                    "candidate_id": "balanced_question_dag",
                    "dag_ref": balanced_path.relative_to(repo_root).as_posix(),
                    "candidate_family": "balanced",
                    "source_label": "balanced question-to-DAG graph",
                    "producer_ref": COMMAND,
                    "evidence_refs": [evidence_ref],
                    "blockers": [],
                },
                {
                    "candidate_id": "over_split_question_dag",
                    "dag_ref": over_split_path.relative_to(repo_root).as_posix(),
                    "candidate_family": "over_split",
                    "source_label": "over-split graph",
                    "producer_ref": COMMAND,
                    "evidence_refs": [evidence_ref],
                    "blockers": [],
                },
                {
                    "candidate_id": "cyclic_question_dag",
                    "dag_ref": cyclic_path.relative_to(repo_root).as_posix(),
                    "candidate_family": "invalid",
                    "source_label": "cyclic graph",
                    "producer_ref": COMMAND,
                    "evidence_refs": [evidence_ref],
                    "blockers": [],
                },
            ],
            "selection_policy_ref": "docs/candidate-dag-selection-v1.md",
            "evidence_refs": [
                evidence_ref,
                "docs/question-to-dag-demo-v1.md",
                "docs/candidate-dag-selection-v1.md",
            ],
            "blockers": [],
        },
    )
    return manifest_path.relative_to(repo_root).as_posix()


def _selected_candidate_id(selection_report: dict[str, Any]) -> tuple[str, list[str]]:
    selected_dag_ref = str(selection_report.get("selected_dag_ref", ""))
    selected = ""
    rejected: list[str] = []
    for item in selection_report.get("score_summary", []):
        if not isinstance(item, dict):
            continue
        candidate_id = str(item.get("candidate_id", ""))
        if str(item.get("candidate_dag_ref", "")) == selected_dag_ref:
            selected = candidate_id
        else:
            rejected.append(candidate_id)
    return selected, rejected


def _relative_label(path: str) -> str:
    if not path:
        return ""
    return Path(path).name or path


def _artifact_link(path: str, label: str = "") -> str:
    if not path:
        return "<span class=\"muted\">not emitted</span>"
    escaped_path = html.escape(path)
    escaped_label = html.escape(label or _relative_label(path))
    return f"<a href=\"{escaped_path}\">{escaped_label}</a>"


def _mermaid_graph(report: dict[str, Any]) -> str:
    return """flowchart LR
  Q["User question"]
  RQ["research_question_packet"]
  EV["bounded evidence"]
  CDM["candidate DAG manifest"]
  SEL["selected DAG"]
  EUM["execution-unit manifest"]
  EU["execution units"]
  BOUND["implementation boundary"]

  Q --> RQ --> EV --> CDM --> SEL --> EUM --> EU --> BOUND
"""


def _summary_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Question To DAG Demo Summary",
            "",
            "## User Question",
            "",
            str(report.get("question", "")),
            "",
            "## Flow",
            "",
            "- Research question packet emitted.",
            "- Contract-compatible evidence packet emitted in bounded fixture mode.",
            "- Existing question-to-research handoff tool materialized a research problem packet.",
            "- Existing research tools generated hypotheses, research candidates, evaluations, and a recommendation.",
            "- Research candidate intent was adapted into candidate DAG artifacts.",
            "- Existing DAG selector selected the best graph.",
            "- Existing materializer emitted execution units.",
            "- Demo stops at the implementation boundary.",
            "",
            "## Result",
            "",
            f"- Selected DAG candidate: `{report.get('selected_candidate_id', '')}`",
            f"- Rejected DAG candidates: `{', '.join(report.get('rejected_candidate_ids', []))}`",
            f"- Research problem packet: `{report.get('research_problem_ref', '')}`",
            f"- Research candidates emitted: `{len(report.get('research_candidate_refs', []))}`",
            f"- Execution units emitted: `{len(report.get('execution_unit_refs', []))}`",
            "",
            "## Implementation Boundary",
            "",
            str(report.get("implementation_boundary", "")),
            "",
        ]
    )


def _html_page(report: dict[str, Any]) -> str:
    units = "\n".join(
        "<article class=\"unit-card\">"
        f"<strong>{html.escape(Path(path).stem.replace('execution-unit-', '').replace('-', ' ').title())}</strong>"
        f"<p>{_artifact_link(path, Path(path).name)}</p>"
        "</article>"
        for path in report.get("execution_unit_refs", [])
    )
    rejected = "\n".join(
        f"<li><code>{html.escape(candidate)}</code></li>"
        for candidate in report.get("rejected_candidate_ids", [])
    )
    non_claims = "\n".join(
        f"<li>{html.escape(item)}</li>" for item in report.get("explicit_non_claims", [])
    )
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Jaysearch Question To DAG Demo</title>
    <script type=\"module\">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
      mermaid.initialize({{ startOnLoad: true, securityLevel: "strict", theme: "base" }});
    </script>
    <style>
      :root {{
        --ink: #1f1a10;
        --muted: #675d4a;
        --paper: #fffaf0;
        --field: #f6ecd2;
        --line: #d8c79a;
        --accent: #1f6f5b;
        --warn: #9a5c2e;
        --shadow: 0 22px 60px rgba(37, 31, 17, 0.14);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(31, 111, 91, 0.18), transparent 34rem),
          linear-gradient(135deg, #fbf7ea 0%, #efe3bf 100%);
        font-family: Georgia, 'Times New Roman', serif;
        line-height: 1.55;
      }}
      main {{ width: min(1120px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0; }}
      a {{ color: #124d41; font-weight: 700; }}
      code {{ background: #eadfbd; padding: 0.1rem 0.3rem; border-radius: 0.3rem; }}
      .hero {{
        padding: 2.5rem;
        border: 1px solid rgba(106, 86, 38, 0.35);
        border-radius: 1.5rem;
        background: rgba(255, 250, 240, 0.88);
        box-shadow: var(--shadow);
      }}
      .eyebrow {{ color: var(--accent); font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }}
      h1 {{ font-size: clamp(2.2rem, 7vw, 5.5rem); line-height: 0.95; margin: 0.2rem 0 1rem; max-width: 900px; }}
      h2 {{ font-size: clamp(1.4rem, 3vw, 2.4rem); margin: 0 0 0.75rem; }}
      .lede {{ font-size: 1.25rem; max-width: 760px; color: var(--muted); }}
      .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin: 1rem 0; }}
      section, .card {{
        border: 1px solid var(--line);
        background: rgba(255, 250, 240, 0.9);
        padding: 1.25rem;
        border-radius: 1rem;
      }}
      .flow {{ margin: 1rem 0; }}
      .mermaid {{ background: #fffdf6; border-radius: 1rem; padding: 1rem; overflow-x: auto; }}
      .unit-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.85rem; }}
      .unit-card {{ background: var(--field); border: 1px solid var(--line); border-radius: 0.85rem; padding: 1rem; }}
      .boundary {{ border-color: #bf7d3e; background: #fff1db; }}
      .artifact-list {{ columns: 2; padding-left: 1.2rem; }}
      .muted {{ color: var(--muted); }}
      @media (max-width: 760px) {{
        main {{ padding: 1rem 0; }}
        .hero {{ padding: 1.25rem; }}
        .grid, .unit-grid {{ grid-template-columns: 1fr; }}
        .artifact-list {{ columns: 1; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header class=\"hero\">
        <p class=\"eyebrow\">Jaysearch Demo</p>
        <h1>From question to evidence-backed DAG.</h1>
        <p class=\"lede\">
          Jaysearch turns an ambiguous problem into traceable packets, evaluates candidate graph plans,
          selects a DAG, and materializes execution units for development.
        </p>
      </header>

      <section>
        <p class=\"eyebrow\">Input</p>
        <h2>User Question</h2>
        <p>{html.escape(str(report.get("question", "")))}</p>
      </section>

      <section class=\"flow\">
        <p class=\"eyebrow\">Lineage</p>
        <h2>Packet Flow</h2>
        <pre class=\"mermaid\">{html.escape(_mermaid_graph(report))}</pre>
      </section>

      <div class=\"grid\">
        <section>
          <p class=\"eyebrow\">Research</p>
          <h2>Bounded Evidence</h2>
          <p>The V1 demo uses curated evidence refs so the interview flow is deterministic and inspectable.</p>
          <p>{_artifact_link(str(report.get("evidence_ref", "")), "Open evidence.packet.json")}</p>
        </section>
        <section>
          <p class=\"eyebrow\">Selection</p>
          <h2>Selected DAG</h2>
          <p>Selected candidate: <code>{html.escape(str(report.get("selected_candidate_id", "")))}</code></p>
          <p>Rejected candidates:</p>
          <ul>{rejected}</ul>
        </section>
      </div>

      <section>
        <p class=\"eyebrow\">Execution Boundary</p>
        <h2>Execution Units</h2>
        <div class=\"unit-grid\">{units}</div>
      </section>

      <section class=\"boundary\">
        <p class=\"eyebrow\">Honest Boundary</p>
        <h2>What Is Still In Progress</h2>
        <p>{html.escape(str(report.get("implementation_boundary", "")))}</p>
        <ul>{non_claims}</ul>
      </section>

      <section>
        <p class=\"eyebrow\">Raw Artifacts</p>
        <h2>Inspect The Lineage</h2>
        <ul class=\"artifact-list\">
          <li>{_artifact_link(str(report.get("question_ref", "")), "question.packet.json")}</li>
          <li>{_artifact_link(str(report.get("evidence_ref", "")), "evidence.packet.json")}</li>
          <li>{_artifact_link(str(report.get("candidate_dag_manifest_ref", "")), "candidate-dag-manifest.packet.json")}</li>
          <li>{_artifact_link(str(report.get("candidate_dag_selection_ref", "")), "candidate-dag-selection.packet.json")}</li>
          <li>{_artifact_link(str(report.get("dag_execution_unit_manifest_ref", "")), "dag-execution-unit-manifest.packet.json")}</li>
          <li>{_artifact_link(str(report.get("demo_report_path", "")), "question-dag-demo.report.json")}</li>
        </ul>
      </section>
    </main>
  </body>
</html>
"""


def run_jaysearch_question_dag_demo(
    *,
    root: str = ".",
    question: str,
    topic: str = "",
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    normalized_question = question.strip()
    repo_root = Path(root)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    if not normalized_question:
        blockers.append("question_missing")

    topic_value = topic.strip() or normalized_question[:80]
    topic_slug = _slug(topic_value)
    question_path = ""
    evidence_path = ""
    manifest_path = ""
    selection_report: dict[str, Any] = {}
    materialization_report: dict[str, Any] = {}
    handoff_report: dict[str, Any] = {}
    hypotheses_report: dict[str, Any] = {}
    candidate_tree_report: dict[str, Any] = {}
    evaluation_report: dict[str, Any] = {}
    recommendation_report: dict[str, Any] = {}
    candidate_dag_adapter_report: dict[str, Any] = {}
    selection_code = 1
    materialization_code = 1
    handoff_code = 1
    hypotheses_code = 1
    candidate_tree_code = 1
    evaluation_code = 1
    recommendation_code = 1
    candidate_dag_adapter_code = 1
    step_reports: list[dict[str, Any]] = []

    if not blockers:
        question_packet_path = write_json(
            run_root / "question.packet.json",
            _question_packet(question=normalized_question, topic=topic_value, run_id=run_id),
        )
        question_path = question_packet_path.as_posix()
        evidence_packet_path = write_json(
            run_root / "evidence.packet.json",
            _evidence_packet(
                question_ref=question_packet_path.as_posix(),
                topic=topic_value,
                run_id=run_id,
            ),
        )
        evidence_path = evidence_packet_path.as_posix()
        handoff_code, handoff_report = run_question_research_handoff_workflow(
            root=repo_root.as_posix(),
            research_question_path=question_packet_path.relative_to(repo_root).as_posix(),
            evidence_packet_path=evidence_packet_path.relative_to(repo_root).as_posix(),
            output_root=f"{output_root}/{run_id}/question-research-handoff",
        )
        step_reports.append(
            {
                "step": "orchestrate_question_research_handoff",
                "status": str(handoff_report.get("status", "")).strip(),
                "ok": handoff_report.get("ok") is True,
                "report": handoff_report,
            }
        )
        blockers.extend(
            f"orchestrate_question_research_handoff:{item}"
            for item in handoff_report.get("blockers", [])
        )

        if handoff_code == 0:
            research_problem_path = str(handoff_report.get("research_problem_path", "")).strip()
            hypotheses_code, hypotheses_report = materialize_research_hypotheses(
                root=repo_root.as_posix(),
                research_problem_path=research_problem_path,
                output_root=f"{output_root}/{run_id}/research",
            )
            step_reports.append(
                {
                    "step": "materialize_research_hypotheses",
                    "status": str(hypotheses_report.get("status", "")).strip(),
                    "ok": hypotheses_report.get("ok") is True,
                    "report": hypotheses_report,
                }
            )
            blockers.extend(
                f"materialize_research_hypotheses:{item}"
                for item in hypotheses_report.get("blockers", [])
            )

        if hypotheses_code == 0:
            hypothesis_paths = [
                str(path)
                for path in hypotheses_report.get("hypothesis_packet_paths", [])
                if str(path).strip()
            ]
            candidate_tree_code, candidate_tree_report = materialize_research_candidate_tree(
                root=repo_root.as_posix(),
                research_problem_path=str(handoff_report.get("research_problem_path", "")).strip(),
                hypothesis_paths=hypothesis_paths,
                output_root=f"{output_root}/{run_id}/research",
                max_candidates=4,
            )
            step_reports.append(
                {
                    "step": "materialize_research_candidate_tree",
                    "status": str(candidate_tree_report.get("status", "")).strip(),
                    "ok": candidate_tree_report.get("ok") is True,
                    "report": candidate_tree_report,
                }
            )
            blockers.extend(
                f"materialize_research_candidate_tree:{item}"
                for item in candidate_tree_report.get("blockers", [])
            )

        if candidate_tree_code == 0:
            candidate_paths = [
                str(path)
                for path in candidate_tree_report.get("candidate_packet_paths", [])
                if str(path).strip()
            ]
            evaluation_code, evaluation_report = materialize_research_evaluations(
                root=repo_root.as_posix(),
                candidate_search_tree_path=str(candidate_tree_report.get("candidate_search_tree_path", "")).strip(),
                candidate_paths=candidate_paths,
                output_root=f"{output_root}/{run_id}/research",
            )
            step_reports.append(
                {
                    "step": "materialize_research_evaluations",
                    "status": str(evaluation_report.get("status", "")).strip(),
                    "ok": evaluation_report.get("ok") is True,
                    "report": evaluation_report,
                }
            )
            blockers.extend(
                f"materialize_research_evaluations:{item}"
                for item in evaluation_report.get("blockers", [])
            )

        if evaluation_code == 0:
            candidate_paths = [
                str(path)
                for path in candidate_tree_report.get("candidate_packet_paths", [])
                if str(path).strip()
            ]
            evaluation_paths = [
                str(path)
                for path in evaluation_report.get("evaluation_packet_paths", [])
                if str(path).strip()
            ]
            recommendation_code, recommendation_report = materialize_research_recommendation(
                root=repo_root.as_posix(),
                candidate_search_tree_path=str(candidate_tree_report.get("candidate_search_tree_path", "")).strip(),
                candidate_paths=candidate_paths,
                evaluation_paths=evaluation_paths,
                evaluation_summary_path=str(evaluation_report.get("evaluation_summary_packet_path", "")).strip(),
                output_root=f"{output_root}/{run_id}/research",
            )
            step_reports.append(
                {
                    "step": "materialize_research_recommendation",
                    "status": str(recommendation_report.get("status", "")).strip(),
                    "ok": recommendation_report.get("ok") is True,
                    "report": recommendation_report,
                }
            )
            blockers.extend(
                f"materialize_research_recommendation:{item}"
                for item in recommendation_report.get("blockers", [])
            )

        if recommendation_code == 0:
            candidate_paths = [
                str(path)
                for path in candidate_tree_report.get("candidate_packet_paths", [])
                if str(path).strip()
            ]
            candidate_dag_adapter_code, candidate_dag_adapter_report = (
                materialize_candidate_dags_from_research(
                    root=repo_root.as_posix(),
                    research_recommendation_path=str(
                        recommendation_report.get("recommendation_packet_path", "")
                    ).strip(),
                    candidate_paths=candidate_paths,
                    evidence_packet_path=evidence_packet_path.relative_to(repo_root).as_posix(),
                    output_root=f"{output_root}/{run_id}/candidate-dags",
                    max_dags=3,
                )
            )
            step_reports.append(
                {
                    "step": "materialize_candidate_dags_from_research",
                    "status": str(candidate_dag_adapter_report.get("status", "")).strip(),
                    "ok": candidate_dag_adapter_report.get("ok") is True,
                    "report": candidate_dag_adapter_report,
                }
            )
            blockers.extend(
                f"materialize_candidate_dags_from_research:{item}"
                for item in candidate_dag_adapter_report.get("blockers", [])
            )
            manifest_path = str(candidate_dag_adapter_report.get("candidate_dag_manifest_path", "")).strip()

        if candidate_dag_adapter_code == 0:
            selection_code, selection_report = select_candidate_dag(
                root=repo_root.as_posix(),
                manifest_path=manifest_path,
                output_root=f"{output_root}/{run_id}/selection",
            )
            step_reports.append(
                {
                    "step": "select_candidate_dag",
                    "status": str(selection_report.get("status", "")).strip(),
                    "ok": selection_report.get("ok") is True,
                    "report": selection_report,
                }
            )
            blockers.extend(f"select_candidate_dag:{item}" for item in selection_report.get("blockers", []))

        if selection_code == 0:
            materialization_code, materialization_report = materialize_selected_dag_execution_units(
                root=repo_root.as_posix(),
                selection_path=str(selection_report.get("candidate_dag_selection_path", "")),
                output_root=f"{output_root}/{run_id}/execution-units",
            )
            step_reports.append(
                {
                    "step": "materialize_selected_dag_execution_units",
                    "status": str(materialization_report.get("status", "")).strip(),
                    "ok": materialization_report.get("ok") is True,
                    "report": materialization_report,
                }
            )
            blockers.extend(
                f"materialize_selected_dag_execution_units:{item}"
                for item in materialization_report.get("blockers", [])
            )

    selected_candidate_id, rejected_candidate_ids = _selected_candidate_id(selection_report)
    implementation_boundary = (
        "Execution units are ready for development planning. Autonomous candidate generation, "
        "code synthesis, patch application, and production execution remain the next build slices."
    )
    demo_report = {
        "command": COMMAND,
        "status": "ok"
        if not blockers
        and handoff_code == 0
        and hypotheses_code == 0
        and candidate_tree_code == 0
        and evaluation_code == 0
        and recommendation_code == 0
        and candidate_dag_adapter_code == 0
        and selection_code == 0
        and materialization_code == 0
        else "blocked",
        "ok": not blockers
        and handoff_code == 0
        and hypotheses_code == 0
        and candidate_tree_code == 0
        and evaluation_code == 0
        and recommendation_code == 0
        and candidate_dag_adapter_code == 0
        and selection_code == 0
        and materialization_code == 0,
        "run_id": run_id,
        "question": normalized_question,
        "topic": topic_value,
        "question_ref": question_path,
        "evidence_ref": evidence_path,
        "research_problem_ref": str(handoff_report.get("research_problem_path", "")),
        "question_research_transform_ref": str(handoff_report.get("transform_packet_path", "")),
        "research_hypothesis_refs": [
            str(path) for path in hypotheses_report.get("hypothesis_packet_paths", [])
        ],
        "candidate_search_tree_ref": str(candidate_tree_report.get("candidate_search_tree_path", "")),
        "research_candidate_refs": [
            str(path) for path in candidate_tree_report.get("candidate_packet_paths", [])
        ],
        "research_evaluation_refs": [
            str(path) for path in evaluation_report.get("evaluation_packet_paths", [])
        ],
        "research_recommendation_ref": str(recommendation_report.get("recommendation_packet_path", "")),
        "candidate_dag_manifest_ref": str((repo_root / manifest_path).resolve()) if manifest_path else "",
        "candidate_dag_selection_ref": str(selection_report.get("candidate_dag_selection_path", "")),
        "selected_candidate_id": selected_candidate_id,
        "selected_dag_ref": str(selection_report.get("selected_dag_ref", "")),
        "rejected_candidate_ids": rejected_candidate_ids,
        "dag_execution_unit_manifest_ref": str(
            materialization_report.get("dag_execution_unit_manifest_path", "")
        ),
        "execution_unit_refs": [
            str(path) for path in materialization_report.get("execution_unit_paths", [])
        ],
        "implementation_boundary": implementation_boundary,
        "explicit_non_claims": [
            "no live autonomous web research",
            "no autonomous code synthesis",
            "no patch application",
            "contract-compatible evidence packet uses bounded fixture sources in V1",
        ],
        "step_reports": step_reports,
        "blockers": sorted(set(blockers)),
    }
    demo_report_path = write_json(run_root / "question-dag-demo.report.json", demo_report)
    demo_report["demo_report_path"] = demo_report_path.as_posix()
    summary_path = run_root / "question-dag-demo-summary.md"
    summary_path.write_text(_summary_markdown(demo_report), encoding="utf-8")
    html_path = run_root / "demo.html"
    html_path.write_text(_html_page(demo_report), encoding="utf-8")

    report = envelope(
        command=COMMAND,
        status=str(demo_report["status"]),
        ok=bool(demo_report["ok"]),
        payload={
            **demo_report,
            "demo_report_path": demo_report_path.as_posix(),
            "demo_summary_path": summary_path.as_posix(),
            "demo_html_path": html_path.as_posix(),
        },
    )
    write_json(run_root / "run-jaysearch-question-dag-demo.report.json", report)
    return (0 if report["ok"] else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--question", required=True)
    parser.add_argument("--topic", default="")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = run_jaysearch_question_dag_demo(
            root=args.root,
            question=args.question,
            topic=args.topic,
            output_root=args.output_root,
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
