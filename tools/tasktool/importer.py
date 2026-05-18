from __future__ import annotations
import re
from dataclasses import dataclass, field
from tasktool.model import Project, Phase, Status

EMOJI_TO_STATUS = {
    "✅": Status.DONE,
    "🚧": Status.IN_PROGRESS,
    "⏸": Status.BLOCKED,
    "☐": Status.READY,
}

PHASE_HEADER_RE = re.compile(
    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
    r"(?P<emoji>[✅🚧☐])(?:\s+`(?P<tag>[^`]+)`)?\s*$"
)
PHASE_HEADER_BLOCKED_RE = re.compile(
    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
    r"⏸(?:\s+`(?P<tag>[^`]+)`)?\s*$"
)
PHASE_DONE_TAG_RE = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
SPEC_RE = re.compile(r"Spec:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")
PLAN_RE = re.compile(r"Plan:\s*(?:\[`(?P<path>[^`]+)`\]\([^)]+\)|_pending_)")

# Stop sniffing for Spec:/Plan: once we hit another header or a non-empty
# structural marker. We accept a small window after the phase header.
_SNIFF_WINDOW = 10


@dataclass(slots=True)
class ParseResult:
    project: Project
    warnings: list[str] = field(default_factory=list)


def _match_phase_header(line: str):
    """Return (id, title, status, closed, warning) or None."""
    m = PHASE_HEADER_RE.match(line)
    if m:
        emoji = m.group("emoji")
        status = EMOJI_TO_STATUS[emoji]
        tag = m.group("tag")
        closed: str | None = None
        if status is Status.DONE and tag:
            dm = PHASE_DONE_TAG_RE.match(tag)
            if dm:
                closed = dm.group("date")
        return m.group("id"), m.group("title").strip(), status, closed, None
    m = PHASE_HEADER_BLOCKED_RE.match(line)
    if m:
        # Plan says: blocked-fallback warns + coerces to READY.
        warn = "blocked status not allowed on phase; coerced to ready"
        return m.group("id"), m.group("title").strip(), Status.READY, None, warn
    return None


def parse_tasklist_md(text: str) -> ParseResult:
    """Forgiving parser for TASKLIST.md.

    Currently handles phase headers and post-header Spec:/Plan: lines.
    Anything else is ignored (silently — slice/cross-cut/archive parsing
    arrives in later tasks). Lines that look header-shaped but fail to
    match are surfaced as warnings.
    """
    project = Project(project="<imported>")
    warnings: list[str] = []

    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        header = _match_phase_header(line)
        if header is not None:
            pid, title, status, closed, warn = header
            if warn:
                warnings.append(f"line {i + 1}: {warn}")
            phase = Phase(
                id=pid,
                title=title,
                created="1970-01-01",
                status=status,
                closed=closed,
            )
            # Sniff a short window of following lines for Spec:/Plan:.
            j = i + 1
            end = min(n, i + 1 + _SNIFF_WINDOW)
            while j < end:
                sl = lines[j]
                # Stop early if we hit another markdown header.
                if sl.startswith("## ") or sl.startswith("# "):
                    break
                sm = SPEC_RE.search(sl)
                if sm and phase.spec_path is None:
                    phase.spec_path = sm.group("path")
                pm = PLAN_RE.search(sl)
                if pm and phase.plan_path is None:
                    # _pending_ branch has no path group
                    path = pm.group("path")
                    if path:
                        phase.plan_path = path
                j += 1
            project.phases.append(phase)
            i += 1
            continue
        i += 1

    return ParseResult(project=project, warnings=warnings)
