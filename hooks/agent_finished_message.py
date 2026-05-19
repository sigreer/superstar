#!/usr/bin/env python3
"""Derive a short spoken Superstar milestone from a finished-agent hook payload."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ID_RE = re.compile(
    r"\bP(?P<phase>\d+)(?:\.S(?P<slice>\d+[A-Za-z]?))?(?:\.T(?P<task>\d+))?\b",
    re.I,
)
FINAL_MARKERS = (
    "assistant",
    "final",
    "result",
    "summary",
    "message",
    "text",
    "content",
)


def _flatten(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_flatten(item) for item in value)
    if isinstance(value, dict):
        parts: list[str] = []
        for key, child in value.items():
            key_s = str(key).lower()
            if key_s in FINAL_MARKERS or key_s.endswith("_message"):
                parts.append(_flatten(child))
        if parts:
            return "\n".join(parts)
        return "\n".join(_flatten(child) for child in value.values())
    return str(value)


def _payload_text(payload: str) -> str:
    payload = payload.strip()
    if not payload:
        return ""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return payload

    if isinstance(data, dict):
        direct = data.get("last_assistant_message")
        if isinstance(direct, str) and direct.strip():
            return direct

    texts = [_flatten(data)]
    if isinstance(data, dict):
        transcript = (
            data.get("agent_transcript_path")
            or data.get("transcript_path")
            or data.get("transcriptPath")
        )
        if transcript:
            try:
                path = Path(str(transcript)).expanduser()
                if path.is_file():
                    texts.append(path.read_text(encoding="utf-8", errors="replace")[-30000:])
            except OSError:
                pass
    return "\n".join(text for text in texts if text)


def _ids(text: str) -> list[str]:
    seen: set[str] = set()
    found: list[str] = []
    for match in ID_RE.finditer(text):
        phase = f"P{match.group('phase')}"
        slice_id = match.group("slice")
        task = match.group("task")
        work_id = phase
        if slice_id:
            work_id += f".S{slice_id.upper()}"
        if task:
            work_id += f".T{task}"
        if work_id not in seen:
            seen.add(work_id)
            found.append(work_id)
    return found


def _most_specific(
    ids: list[str],
    *,
    task: bool = False,
    slice_: bool = False,
    phase: bool = False,
) -> str | None:
    candidates = ids
    if task:
        candidates = [item for item in candidates if ".T" in item]
    elif slice_:
        candidates = [item for item in candidates if ".S" in item and ".T" not in item]
    elif phase:
        candidates = [item for item in candidates if ".S" not in item]
    if not candidates:
        return None
    return candidates[-1]


def milestone(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lower = compact.lower()
    ids = _ids(compact)
    if not ids:
        return ""

    # Static Superstar process milestones, ordered from most specific/urgent to broad.
    question_patterns = (
        "questions for",
        "i have questions",
        "need your input",
        "blocked on your input",
        "please answer",
    )
    if "?" in compact or any(pattern in lower for pattern in question_patterns):
        work_id = _most_specific(ids, task=True) or _most_specific(ids, slice_=True) or ids[-1]
        return f"Questions for {work_id}"

    done_pattern = r"\b(complete|completed|ready|reviewed|approved|written|saved)\b"

    if re.search(r"\bspec(?:ification)?\b", lower) and re.search(done_pattern, lower):
        work_id = _most_specific(ids, phase=True) or ids[-1].split(".")[0]
        return f"Spec complete for {work_id}"

    if re.search(r"\bplan\b", lower) and re.search(done_pattern, lower):
        work_id = _most_specific(ids, slice_=True) or _most_specific(ids, task=True) or ids[-1]
        if ".T" in work_id:
            work_id = ".".join(work_id.split(".")[:2])
        return f"Plan complete for {work_id}"

    closed_pattern = r"\b(complete|completed|closed|done|ready|passed)\b"

    if re.search(r"\b(post-slice|slice)\b", lower) and re.search(closed_pattern, lower):
        work_id = _most_specific(ids, slice_=True) or _most_specific(ids, task=True) or ids[-1]
        if ".T" in work_id:
            work_id = ".".join(work_id.split(".")[:2])
        return f"Completed slice {work_id}"

    phase_closed_pattern = r"\b(complete|completed|closed|done|ready|passed|archived)\b"

    if re.search(r"\b(post-phase|phase)\b", lower) and re.search(phase_closed_pattern, lower):
        work_id = _most_specific(ids, phase=True) or ids[-1].split(".")[0]
        return f"Completed phase {work_id}"

    work_id = _most_specific(ids, task=True) or _most_specific(ids, slice_=True) or ids[-1]
    return f"Finished {work_id}"


def main() -> int:
    text = _payload_text(sys.stdin.read())
    result = milestone(text)
    if result:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
