from __future__ import annotations
import re
from dataclasses import dataclass, field
from tasktool.model import Project, Phase, Slice, BlockedOn, Status


@dataclass(slots=True)
class _PhaseMatch:
    id: str
    title: str
    status: Status
    closed: str | None
    warning: str | None


@dataclass(slots=True)
class _SliceMatch:
    id: str
    title: str
    status: Status
    closed: str | None
    blocked_on: BlockedOn | None
    plan_path: str | None

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

SLICE_LINE_RE = re.compile(
    r"^-\s+(?P<emoji>[✅🚧⏸☐])\s+\*\*(?P<id>S\d+[a-z]?)\*\*"
    r"(?:\s+`(?P<tag>[^`]+)`)?"
    r"(?:\s+(?:—\s+)?(?P<rest>.+))?$"
)
SLICE_DONE_TAG_RE = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
SLICE_BLOCKED_TAG_RE = re.compile(r"^BLOCKED on\s+(?P<on>.+)$")
INLINE_PLAN_RE = re.compile(r"Plan:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")

# Stop sniffing for Spec:/Plan: once we hit another header or a non-empty
# structural marker. We accept a small window after the phase header.
_SNIFF_WINDOW = 10


@dataclass(slots=True)
class ParseResult:
    project: Project
    warnings: list[str] = field(default_factory=list)


def _match_phase_header(line: str) -> _PhaseMatch | None:
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
        return _PhaseMatch(
            id=m.group("id"),
            title=m.group("title").strip(),
            status=status,
            closed=closed,
            warning=None,
        )
    m = PHASE_HEADER_BLOCKED_RE.match(line)
    if m:
        # Plan says: blocked-fallback warns + coerces to READY.
        return _PhaseMatch(
            id=m.group("id"),
            title=m.group("title").strip(),
            status=Status.READY,
            closed=None,
            warning="blocked status not allowed on phase; coerced to ready",
        )
    return None


def _match_slice_line(line: str) -> _SliceMatch | None:
    m = SLICE_LINE_RE.match(line)
    if not m:
        return None
    emoji = m.group("emoji")
    tag = m.group("tag")
    rest = m.group("rest") or ""
    title = rest.split(". Plan:", 1)[0].strip() or "<untitled>"
    closed: str | None = None
    blocked_on: BlockedOn | None = None
    if tag:
        dm = SLICE_DONE_TAG_RE.match(tag)
        if dm:
            closed = dm.group("date")
        bm = SLICE_BLOCKED_TAG_RE.match(tag)
        if bm:
            on = bm.group("on").strip()
            if on.startswith("external:"):
                blocked_on = BlockedOn(kind="external", value=on[len("external:"):])
            else:
                blocked_on = BlockedOn(kind="id", value=on)
    plan_path: str | None = None
    pm = INLINE_PLAN_RE.search(rest)
    if pm:
        plan_path = pm.group("path")
    return _SliceMatch(
        id=m.group("id"),
        title=title,
        status=EMOJI_TO_STATUS[emoji],
        closed=closed,
        blocked_on=blocked_on,
        plan_path=plan_path,
    )


def parse_tasklist_md(text: str) -> ParseResult:
    """Forgiving parser for TASKLIST.md.

    At this stage the parser only recognises phase headers (and the
    Spec:/Plan: lines that may follow within a short window). Every other
    line is silently skipped. Slice, cross-cutting, and archive parsing —
    along with their associated warning policies — arrive in later tasks.
    The parser never raises; ambiguous tokens become entries in
    ``ParseResult.warnings`` for the caller to decide on.
    """
    project = Project(project="<imported>")
    warnings: list[str] = []
    current_phase: Phase | None = None

    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        header = _match_phase_header(line)
        if header is not None:
            if header.warning:
                warnings.append(f"line {i + 1}: {header.warning}")
            phase = Phase(
                id=header.id,
                title=header.title,
                # Sentinel: markdown has no real created-date for phases.
                created="1970-01-01",
                status=header.status,
                closed=header.closed,
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
            current_phase = phase
            i += 1
            continue
        if current_phase is not None:
            sm = _match_slice_line(line)
            if sm is not None:
                current_phase.slices.append(
                    Slice(
                        id=sm.id,
                        title=sm.title,
                        created="1970-01-01",
                        status=sm.status,
                        closed=sm.closed,
                        blocked_on=sm.blocked_on,
                        plan_path=sm.plan_path,
                    )
                )
                i += 1
                continue
        i += 1

    return ParseResult(project=project, warnings=warnings)
