from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
from typing import Any

import yaml

REQUIRED_HEADINGS = [
    "Purpose / Big Picture",
    "Progress",
    "Surprises & Discoveries",
    "Decision Log",
    "Outcomes & Retrospective",
    "Context and Orientation",
    "Plan of Work",
    "Concrete Steps",
    "Validation and Acceptance",
    "Idempotence and Recovery",
    "Artifacts and Notes",
    "Interfaces and Dependencies",
]

REQUIRED_FRONTMATTER_FIELDS = [
    "id",
    "title",
    "owner",
    "created",
    "status",
    "base_branch",
    "changes",
    "approve_policy",
    "reviewers",
    "draft_by",
    "draft_branch",
    "draft_created",
    "finalized_by",
    "finalized_at",
    "finalized_in_pr",
]

VALID_STATUS_VALUES = {
    "draft",
    "proposed",
    "approved",
    "executing",
    "completed",
    "archived",
}


@dataclass(frozen=True)
class ParsedPlan:
    path: Path
    text: str
    frontmatter: dict[str, Any]
    body: str


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        return {}, body
    return data, body


def parse_plan(path: Path) -> ParsedPlan:
    text = load_text(path)
    frontmatter, body = parse_frontmatter(text)
    return ParsedPlan(path=path, text=text, frontmatter=frontmatter, body=body)


def list_execplans(
    execplans_glob: str = ".agent/execplans/*.md",
    tracked_only: bool = False,
) -> list[Path]:
    if not tracked_only:
        return sorted(Path(".").glob(execplans_glob))

    proc = subprocess.run(
        ["git", "ls-files", execplans_glob],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []
    return sorted(Path(line.strip()) for line in proc.stdout.splitlines() if line.strip())


def timestamp_in_future(value: str, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return False
    return parsed > now + timedelta(hours=1)
