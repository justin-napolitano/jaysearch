from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "materialize-research-hypotheses"
DEFAULT_OUTPUT_ROOT = Path("artifacts/research-hypotheses/runs")
DEFAULT_FAMILIES = [
    "baseline_reference",
    "reuse_direct",
    "reuse_hybrid",
    "novel_synthesized",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("rhb-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _family_statement(*, family: str, problem_statement: str) -> str:
    if family == "baseline_reference":
        return f"Establish a simple baseline approach for: {problem_statement}"
    if family == "reuse_direct":
        return f"Prefer direct reuse of known references for: {problem_statement}"
    if family == "reuse_hybrid":
        return f"Combine reuse with new adaptation for: {problem_statement}"
    return f"Synthesize a novel approach for: {problem_statement}"


def _family_outline(*, family: str) -> str:
    outlines = {
        "baseline_reference": "Use the simplest compliant reference path to anchor later comparisons.",
        "reuse_direct": "Adapt a known-good reference implementation with minimal new synthesis.",
        "reuse_hybrid": "Blend reusable structure with targeted new logic where direct reuse is insufficient.",
        "novel_synthesized": "Generate a fresh approach under the stated constraints for comparison against reuse paths.",
    }
    return outlines.get(family, "Explore a bounded strategy branch.")


def _family_advantages(*, family: str) -> list[str]:
    advantages = {
        "baseline_reference": ["clear comparison anchor", "low interpretation ambiguity"],
        "reuse_direct": ["lower implementation risk", "faster path if references fit"],
        "reuse_hybrid": ["balances reuse with local adaptation", "can preserve known-good structure"],
        "novel_synthesized": ["highest flexibility", "can avoid reuse mismatch"],
    }
    return advantages.get(family, [])


def _family_tradeoffs(*, family: str) -> list[str]:
    tradeoffs = {
        "baseline_reference": ["may underperform", "limited optimization"],
        "reuse_direct": ["can inherit reference mismatch", "may constrain local fit"],
        "reuse_hybrid": ["higher adaptation complexity", "needs clear boundary management"],
        "novel_synthesized": ["higher execution risk", "weaker prior validation"],
    }
    return tradeoffs.get(family, [])


def materialize_research_hypotheses(
    *,
    root: str = ".",
    research_problem_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    families: list[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    problem = _load_json(repo_root / research_problem_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(problem.get("packet_type", "")).strip() != "research_problem_packet":
        blockers.append("research_problem_packet_type_invalid")

    problem_id = str(problem.get("problem_id", "")).strip()
    goal = str(problem.get("goal", "")).strip()
    problem_statement = str(problem.get("problem_statement", "")).strip()
    constraints = _string_list(problem.get("constraints", []))
    evaluation_criteria = _string_list(problem.get("evaluation_criteria", []))
    repo_context = problem.get("repo_context", {})
    if not isinstance(repo_context, dict):
        repo_context = {}
    source_question_refs = _string_list(problem.get("source_question_refs", []))
    evidence_packet_ref = str(problem.get("evidence_packet_ref", "")).strip()
    reference_implementations = _string_list(problem.get("reference_implementations", []))

    if not problem_id:
        blockers.append("research_problem_missing_problem_id")
    if not goal:
        blockers.append("research_problem_missing_goal")
    if not problem_statement:
        blockers.append("research_problem_missing_problem_statement")
    if not evaluation_criteria:
        blockers.append("research_problem_missing_evaluation_criteria")

    requested_families = [item for item in (families or DEFAULT_FAMILIES) if item in DEFAULT_FAMILIES]
    if len(requested_families) < 2:
        blockers.append("hypothesis_family_count_too_small")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "research_problem_path": str((repo_root / research_problem_path).resolve()),
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "research-hypothesis-branching.report.json", report)
        return 1, report

    evidence_refs = [evidence_packet_ref] if evidence_packet_ref else []
    hypothesis_packet_paths: list[str] = []
    emitted_families: list[str] = []
    for index, family in enumerate(requested_families, start=1):
        hypothesis_id = f"{problem_id}:hypothesis:{family}"
        hypothesis_packet = {
            "packet_type": "research_hypothesis_packet",
            "packet_version": "v1",
            "packet_id": f"{hypothesis_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "hypothesis_id": hypothesis_id,
            "problem_id": problem_id,
            "hypothesis_family": family,
            "hypothesis_statement": _family_statement(family=family, problem_statement=problem_statement),
            "approach_outline": _family_outline(family=family),
            "evaluation_focus": evaluation_criteria,
            "evidence_refs": evidence_refs,
            "branch_rank": index,
            "prune_conditions": [
                "fails required validity checks",
                "cannot satisfy evaluation criteria under constraints",
            ],
            "source_question_refs": source_question_refs,
            "source_problem_ref": str((repo_root / research_problem_path).resolve()),
            "risk_notes": _family_tradeoffs(family=family),
            "expected_advantages": _family_advantages(family=family),
            "expected_tradeoffs": _family_tradeoffs(family=family),
            "constraints": constraints,
            "repo_context": repo_context,
            "reference_implementations": reference_implementations,
        }
        path = write_json(run_root / f"research-hypothesis-{index:02d}.packet.json", hypothesis_packet)
        hypothesis_packet_paths.append(path.as_posix())
        emitted_families.append(family)

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "research_problem_path": str((repo_root / research_problem_path).resolve()),
            "hypothesis_packet_paths": hypothesis_packet_paths,
            "hypothesis_count": len(hypothesis_packet_paths),
            "families": emitted_families,
            "blockers": [],
        },
    )
    write_json(run_root / "research-hypothesis-branching.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--research-problem-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--family", action="append", default=[])
    args = parser.parse_args()
    try:
        code, report = materialize_research_hypotheses(
            root=args.root,
            research_problem_path=args.research_problem_path,
            output_root=args.output_root,
            families=args.family,
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
