from __future__ import annotations
import re
from typing import Literal

Kind = Literal["phase", "slice", "task", "cross"]

class IdParseError(ValueError):
    pass

_PHASE = r"P\d+"
_SLICE = r"S\d+[a-z]?"
_TASK = r"T\d+"
_CROSS = r"X\d+"

_SHORT_RE = re.compile(rf"^({_PHASE}|{_SLICE}|{_TASK}|{_CROSS})$")
_QUALIFIED_RE = re.compile(
    rf"^({_PHASE})(?:\.({_SLICE}))?(?:\.({_TASK}))?$"
)

def parse_id(value: str) -> tuple[Kind, str]:
    """Return (kind, normalised-id). Accepts short or qualified form."""
    if not value:
        raise IdParseError("empty id")
    if "." in value:
        m = _QUALIFIED_RE.match(value)
        if not m:
            raise IdParseError(f"malformed qualified id: {value!r}")
        phase, slice_, task = m.groups()
        if task:
            return ("task", value)
        if slice_:
            return ("slice", value)
        return ("phase", phase)
    m = _SHORT_RE.match(value)
    if not m:
        raise IdParseError(f"malformed id: {value!r}")
    head = value[0]
    return ({"P": "phase", "S": "slice", "T": "task", "X": "cross"}[head], value)

def kind_of(value: str) -> Kind:
    return parse_id(value)[0]

def is_slice_id(value: str) -> bool:
    return kind_of(value) == "slice"

def fully_qualify(value: str, *, phase: str | None = None, slice: str | None = None) -> str:
    parse_id(value)  # validate
    if "." in value:
        return value
    head = value[0]
    if head == "P" or head == "X":
        return value
    if head == "S":
        if not phase:
            raise IdParseError(f"cannot qualify slice {value!r} without phase context")
        return f"{phase}.{value}"
    if head == "T":
        if not phase or not slice:
            raise IdParseError(f"cannot qualify task {value!r} without phase+slice context")
        return f"{phase}.{slice}.{value}"
    raise IdParseError(f"unreachable: {value!r}")

def split_qualified(value: str) -> tuple[str | None, str | None, str | None]:
    """Return (phase, slice, task) components; None for missing levels."""
    parse_id(value)
    if "." not in value:
        head = value[0]
        if head == "P":
            return (value, None, None)
        if head == "S":
            return (None, value, None)
        if head == "T":
            return (None, None, value)
        return (None, None, None)  # cross
    m = _QUALIFIED_RE.match(value)
    assert m
    return tuple(m.groups())  # type: ignore[return-value]
