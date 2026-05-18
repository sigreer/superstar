from __future__ import annotations
import re
from dataclasses import dataclass, field
from tasktool.model import Project, Phase, Slice, BlockedOn, CrossCutting, Status


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
    warning: str | None

UNTITLED = "<untitled>"
EXTERNAL_PREFIX = "external:"

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
DONE_TAG_RE = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
SPEC_RE = re.compile(r"Spec:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")
PLAN_RE = re.compile(r"Plan:\s*(?:\[`(?P<path>[^`]+)`\]\([^)]+\)|_pending_)")

SLICE_LINE_RE = re.compile(
    r"^-\s+(?P<emoji>[✅🚧⏸☐])\s+\*\*(?P<id>S\d+[a-z]?)\*\*"
    r"(?:\s+`(?P<tag>[^`]+)`)?"
    r"(?:\s+(?:—\s+)?(?P<rest>.+))?$"
)
BLOCKED_TAG_RE = re.compile(r"^BLOCKED on\s+(?P<on>.+)$")
INLINE_PLAN_RE = re.compile(r"Plan:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")

CROSS_HEADER_RE = re.compile(r"^##\s+Cross-cutting\b")
CROSS_LINE_RE = re.compile(
    r"^-\s+(?P<emoji>[✅🚧☐])\s+\*\*(?P<id>X\d+)\*\*"
    r"(?:\s+—\s+(?P<rest>.+))?$"
)
CROSS_LINE_BLOCKED_RE = re.compile(
    r"^-\s+⏸\s+\*\*(?P<id>X\d+)\*\*"
    r"(?:\s+—\s+(?P<rest>.+))?$"
)

BLOCKED_NOT_ALLOWED_ON_CROSS = "blocked status not allowed on cross; coerced to ready"
UNPARSED_BULLET = "unparsed bullet: {raw!r}"


@dataclass(slots=True)
class _CrossMatch:
    id: str
    title: str
    status: Status
    warning: str | None


def _match_cross_line(line: str) -> _CrossMatch | None:
    m = CROSS_LINE_RE.match(line)
    if m:
        rest = (m.group("rest") or "").strip()
        title = rest or UNTITLED
        return _CrossMatch(
            id=m.group("id"),
            title=title,
            status=EMOJI_TO_STATUS[m.group("emoji")],
            warning=None,
        )
    m = CROSS_LINE_BLOCKED_RE.match(line)
    if m:
        rest = (m.group("rest") or "").strip()
        title = rest or UNTITLED
        return _CrossMatch(
            id=m.group("id"),
            title=title,
            status=Status.READY,
            warning=BLOCKED_NOT_ALLOWED_ON_CROSS,
        )
    return None

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
            dm = DONE_TAG_RE.match(tag)
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
    sid = m.group("id")
    tag = m.group("tag")
    rest = m.group("rest") or ""
    title = rest.split(". Plan:", 1)[0].strip() or UNTITLED
    closed: str | None = None
    blocked_on: BlockedOn | None = None
    warning: str | None = None
    if tag:
        dm = DONE_TAG_RE.match(tag)
        bm = BLOCKED_TAG_RE.match(tag)
        if dm:
            closed = dm.group("date")
        elif bm:
            on = bm.group("on").strip()
            if on.startswith(EXTERNAL_PREFIX):
                blocked_on = BlockedOn(kind="external", value=on[len(EXTERNAL_PREFIX):])
            else:
                blocked_on = BlockedOn(kind="id", value=on)
        else:
            warning = f"unrecognised tag on slice {sid}: `{tag}`"
    plan_path: str | None = None
    pm = INLINE_PLAN_RE.search(rest)
    if pm:
        plan_path = pm.group("path")
    return _SliceMatch(
        id=sid,
        title=title,
        status=EMOJI_TO_STATUS[emoji],
        closed=closed,
        blocked_on=blocked_on,
        plan_path=plan_path,
        warning=warning,
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
    in_cross = False

    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if CROSS_HEADER_RE.match(line):
            in_cross = True
            current_phase = None
            i += 1
            continue
        header = _match_phase_header(line)
        if header is not None:
            in_cross = False
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
                # Stop at the first slice bullet so inline Plan: links on
                # slice lines cannot overwrite a phase's _pending_ plan.
                if sl.startswith("- "):
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
        if in_cross:
            cm = _match_cross_line(line)
            if cm is not None:
                if cm.warning:
                    warnings.append(f"line {i + 1}: {cm.warning}")
                project.cross_cutting.append(
                    CrossCutting(
                        id=cm.id,
                        title=cm.title,
                        created="1970-01-01",
                        status=cm.status,
                    )
                )
                i += 1
                continue
            if line.startswith("- "):
                warnings.append(
                    f"line {i + 1}: " + UNPARSED_BULLET.format(raw=line)
                )
            i += 1
            continue
        if current_phase is not None:
            sm = _match_slice_line(line)
            if sm is not None:
                if sm.warning:
                    warnings.append(f"line {i + 1}: {sm.warning}")
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
            if line.startswith("- "):
                warnings.append(
                    f"line {i + 1}: " + UNPARSED_BULLET.format(raw=line)
                )
        i += 1

    return ParseResult(project=project, warnings=warnings)
