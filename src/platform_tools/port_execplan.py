from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.plan_utils import REQUIRED_HEADINGS, parse_plan


COMMAND = "port-execplan"
LEGACY_HEADINGS = {
    "Purpose / Big Picture",
    "Progress",
    "Surprises & Discoveries",
    "Decision Log",
    "Concrete Steps",
    "Idempotence and Recovery",
    "Interfaces and Dependencies",
}
OPTIONAL_DRAFT_FIELDS = {"draft_by", "draft_branch", "draft_created"}


def _parse_sections(body: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
            continue
        if line.startswith("# "):
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[2:].strip()
            current_lines = []
            continue
        current_lines.append(line)
    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return sections


def _nonempty(*values: str) -> list[str]:
    return [value.strip() for value in values if isinstance(value, str) and value.strip()]


def _join_blocks(blocks: list[str], *, fallback: str) -> str:
    cleaned = [block.strip() for block in blocks if block.strip()]
    return "\n\n".join(cleaned) if cleaned else fallback


def _normalize_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(frontmatter)
    base_branch = str(normalized.get("base_branch", "")).strip()
    initiative_branch = str(normalized.get("initiative_branch", "")).strip()
    if initiative_branch and base_branch == "main":
        normalized["base_branch"] = initiative_branch
    for field in OPTIONAL_DRAFT_FIELDS:
        normalized.pop(field, None)
    return normalized


def _render_section(heading: str, content: str) -> str:
    return f"## {heading}\n\n{content.strip()}\n"


def transform_execplan(plan_path: Path) -> tuple[str, dict[str, Any]]:
    parsed = parse_plan(plan_path)
    frontmatter = _normalize_frontmatter(parsed.frontmatter)
    sections = dict(_parse_sections(parsed.body))

    outcomes = _join_blocks(
        [
            sections.get("Outcomes & Retrospective", ""),
            sections.get("Progress", ""),
        ],
        fallback="- Pending execution.",
    )
    context = _join_blocks(
        _nonempty(
            sections.get("Context and Orientation", ""),
            sections.get("Purpose / Big Picture", ""),
        ),
        fallback="Review the active initiative, declared changes, and validation contract before execution.",
    )
    plan_of_work = _join_blocks(
        _nonempty(
            sections.get("Plan of Work", ""),
            sections.get("Concrete Steps", ""),
        ),
        fallback="1. Review scope.\n2. Implement the bounded slice.\n3. Run validation.",
    )
    validation = _join_blocks(
        _nonempty(
            sections.get("Validation and Acceptance", ""),
            sections.get("Idempotence and Recovery", ""),
        ),
        fallback="Run the declared validation commands and confirm acceptance criteria for the slice.",
    )

    artifact_blocks = []
    for heading in (
        "Artifacts and Notes",
        "Decision Log",
        "Surprises & Discoveries",
        "Interfaces and Dependencies",
    ):
        content = sections.get(heading, "").strip()
        if not content:
            continue
        if heading == "Artifacts and Notes":
            artifact_blocks.append(content)
        else:
            artifact_blocks.append(f"### {heading}\n\n{content}")
    artifacts = _join_blocks(artifact_blocks, fallback="- Migrated from legacy ExecPlan shape.")

    output = "---\n"
    output += yaml.safe_dump(frontmatter, sort_keys=False)
    output += "---\n\n"
    output += _render_section("Outcomes & Retrospective", outcomes)
    output += "\n"
    output += _render_section("Context and Orientation", context)
    output += "\n"
    output += _render_section("Plan of Work", plan_of_work)
    output += "\n"
    output += _render_section("Validation and Acceptance", validation)
    output += "\n"
    output += _render_section("Artifacts and Notes", artifacts)

    report = {
        "required_headings": list(REQUIRED_HEADINGS),
        "removed_headings": sorted(heading for heading in LEGACY_HEADINGS if heading in sections),
        "removed_frontmatter_fields": sorted(field for field in OPTIONAL_DRAFT_FIELDS if field in parsed.frontmatter),
        "updated_base_branch": frontmatter.get("base_branch", ""),
        "initiative_branch": frontmatter.get("initiative_branch", ""),
    }
    return output, report


def port_execplan(
    *,
    path: str,
    in_place: bool = False,
    output_path: str | None = None,
) -> tuple[int, dict[str, Any]]:
    plan_path = Path(path)
    transformed, transform_report = transform_execplan(plan_path)
    target_path = Path(output_path) if output_path else plan_path
    if in_place or output_path:
        target_path.write_text(transformed, encoding="utf-8")
    report = {
        "command": COMMAND,
        "ok": True,
        "status": "ok",
        "path": plan_path.as_posix(),
        "target_path": target_path.as_posix(),
        "wrote_file": bool(in_place or output_path),
        **transform_report,
    }
    if not in_place and output_path is None:
        report["preview"] = transformed
    return 0, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Port a legacy ExecPlan into the contract-first shape.")
    parser.add_argument("--path", required=True)
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args(argv)
    code, report = port_execplan(path=args.path, in_place=args.in_place, output_path=args.output_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
