"""Normalized tracker model for the timeline generator.

This is the ONLY module that knows the docs/tasklist.json schema. If a shared
tracker-model module is later extracted from tasktool, replace this module's
internals; TimelineItem is the seam consumed by extract/render/timeline.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

EPOCH_PLACEHOLDER = "1970-01-01"
TERMINAL_STATUSES = {"done", "cancelled"}
START_STATUSES = {"in_progress", "started"}


def parse_tracker_date(raw):
    """ISO 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM[:SS]' -> (datetime|None, precision)."""
    if not raw or raw == EPOCH_PLACEHOLDER:
        return None, "day"
    if "T" in raw:
        return dt.datetime.fromisoformat(raw), "minute"
    d = dt.date.fromisoformat(raw)
    return dt.datetime(d.year, d.month, d.day), "day"


@dataclass
class DateValue:
    when: dt.datetime | None = None
    precision: str = "day"      # "day" | "minute"
    source: str = "field"       # "field" | "replay" | "override"


@dataclass
class TimelineItem:
    key: str                    # "P21", "P21.S4", "X13"
    kind: str                   # "phase" | "slice" | "x"
    parent: str | None
    title: str
    status: str
    display_title: str | None = None
    created: DateValue = field(default_factory=DateValue)
    started: DateValue = field(default_factory=DateValue)
    closed: DateValue = field(default_factory=DateValue)
    excluded: bool = False

    def label(self):
        return self.display_title or self.title


def _date_value(obj, name):
    when, precision = parse_tracker_date(obj.get(name))
    return DateValue(when, precision, "field")


def _item(key, kind, parent, obj):
    return TimelineItem(
        key=key, kind=kind, parent=parent,
        title=obj.get("title") or key,
        status=obj.get("status", "unknown"),
        created=_date_value(obj, "created"),
        started=_date_value(obj, "started"),
        closed=_date_value(obj, "closed"),
    )


def items_from_project(doc):
    """Walk a project-shaped dict (live tasklist.json or an archived
    '## Full phase JSON' block) into TimelineItem records."""
    items = []
    for p in doc.get("phases", []):
        pk = p["id"]
        items.append(_item(pk, "phase", None, p))
        for s in p.get("slices", []):
            items.append(_item(f"{pk}.{s['id']}", "slice", pk, s))
    for c in doc.get("cross_cutting", []):
        items.append(_item(c["id"], "x", None, c))
    return items


def item_from_cross(obj):
    """A single archived cross-cutting item object
    (from a '## Full cross-cutting JSON' block)."""
    return _item(obj["id"], "x", None, obj)


def collect(live_doc, archive_project_docs, archive_x_objects):
    """Merge all sources into one item list. First occurrence of a key wins,
    and live is read first, so live data shadows any stale archive copy."""
    seen, items = set(), []
    sources = [items_from_project(live_doc)]
    sources += [items_from_project(d) for d in archive_project_docs]
    sources += [[item_from_cross(o)] for o in archive_x_objects]
    for source in sources:
        for it in source:
            if it.key not in seen:
                seen.add(it.key)
                items.append(it)
    return items
