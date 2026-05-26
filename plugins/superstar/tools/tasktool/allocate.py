# tools/tasktool/allocate.py
from __future__ import annotations
import re
from pathlib import Path
from tasktool.model import Project

_PHASE_PAT = re.compile(r"\bP(\d+)\b", re.IGNORECASE)
_SLICE_PAT = re.compile(r"\bS(\d+)([a-z]?)\b", re.IGNORECASE)
_TASK_PAT = re.compile(r"\bT(\d+)\b", re.IGNORECASE)
_CROSS_PAT = re.compile(r"\bX(\d+)\b", re.IGNORECASE)

def scan_orphan_ids(repo_root: Path, kind: str) -> set[int]:
    """Scan docs/specs, docs/plans, docs/reviewer folder names for IDs of the given kind.
    kind ∈ {phase, slice, task, cross}. Returns the set of integer suffixes seen."""
    out: set[int] = set()
    pat = {"phase": _PHASE_PAT, "slice": _SLICE_PAT, "task": _TASK_PAT, "cross": _CROSS_PAT}[kind]
    for sub in ("docs/specs", "docs/plans"):
        d = repo_root / sub
        if not d.exists():
            continue
        for p in d.iterdir():
            for m in pat.finditer(p.name):
                out.add(int(m.group(1)))
    rev = repo_root / "docs/reviewer"
    if rev.exists():
        for d in rev.iterdir():
            for m in pat.finditer(d.name):
                out.add(int(m.group(1)))
    return out

def _phase_nums(p: Project) -> set[int]:
    nums = {int(ph.id[1:]) for ph in p.phases}
    nums |= {int(a.id[1:]) for a in p.archived_phases}
    return nums

def next_phase_id(p: Project, repo_root: Path) -> str:
    used = _phase_nums(p) | scan_orphan_ids(repo_root, "phase")
    n = max(used, default=0) + 1
    return f"P{n}"

def next_slice_id(p: Project, phase_id: str, repo_root: Path) -> str:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise KeyError(f"phase {phase_id} not found")
    used: set[int] = set()
    for s in phase.slices:
        m = _SLICE_PAT.match(s.id)
        if m:
            used.add(int(m.group(1)))
    # also pull orphan slice IDs that reference this phase
    for sub in ("docs/specs", "docs/plans"):
        d = repo_root / sub
        if not d.exists():
            continue
        for fp in d.iterdir():
            if phase_id.lower() in fp.name.lower():
                for m in _SLICE_PAT.finditer(fp.name):
                    used.add(int(m.group(1)))
    rev = repo_root / "docs/reviewer"
    if rev.exists():
        for fp in rev.iterdir():
            if phase_id.lower() in fp.name.lower():
                for m in _SLICE_PAT.finditer(fp.name):
                    used.add(int(m.group(1)))
    n = max(used, default=0) + 1
    return f"S{n}"

def next_followup_letter(p: Project, phase_id: str, base_slice: str, repo_root: Path) -> str:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise KeyError(f"phase {phase_id} not found")
    base_num = re.match(r"^S(\d+)", base_slice)
    if not base_num:
        raise ValueError(f"bad slice id: {base_slice}")
    base = base_num.group(1)
    used_letters: set[str] = set()
    for s in phase.slices:
        m = re.match(rf"^S{base}([a-z])$", s.id)
        if m:
            used_letters.add(m.group(1))
    nxt = "a"
    while nxt in used_letters:
        nxt = chr(ord(nxt) + 1)
        if nxt > "z":
            raise RuntimeError(f"exhausted follow-up letters under S{base}")
    return f"S{base}{nxt}"

def next_task_id(p: Project, phase_id: str, slice_id: str) -> str:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise KeyError(f"phase {phase_id} not found")
    slc = next((s for s in phase.slices if s.id == slice_id), None)
    if slc is None:
        raise KeyError(f"slice {phase_id}.{slice_id} not found")
    used = {int(t.id[1:]) for t in slc.tasks}
    n = max(used, default=0) + 1
    return f"T{n}"

def next_cross_id(p: Project, repo_root: Path) -> str:
    used = {int(c.id[1:]) for c in p.cross_cutting}
    used |= {int(c.id[1:]) for c in p.archived_cross_cutting}
    used |= scan_orphan_ids(repo_root, "cross")
    n = max(used, default=0) + 1
    return f"X{n}"
