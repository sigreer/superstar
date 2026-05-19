from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, BlockedOn,
    Status, PlanningStatus, SCHEMA_VERSION,
)

def to_dict(p: Project) -> dict:
    def _coerce(obj):
        if isinstance(obj, (Status, PlanningStatus)):
            return obj.value
        return obj
    raw = asdict(p)
    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return _coerce(node)
    return walk(raw)

def from_dict(d: dict) -> Project:
    def _status(v):
        return Status(v) if isinstance(v, str) else v
    def _planning_status(v):
        return PlanningStatus(v) if isinstance(v, str) else v
    def _task(td):
        return Task(
            id=td["id"], title=td["title"], created=td["created"],
            started=td.get("started"),
            status=_status(td.get("status", "ready")),
            closed=td.get("closed"),
            refs=list(td.get("refs", [])),
            notes=td.get("notes", ""),
        )
    def _blocked(b):
        return None if b is None else BlockedOn(kind=b["kind"], value=b["value"])
    def _slice(sd):
        return Slice(
            id=sd["id"], title=sd["title"], created=sd["created"],
            started=sd.get("started"),
            status=_status(sd.get("status", "ready")),
            closed=sd.get("closed"),
            blocked_on=_blocked(sd.get("blocked_on")),
            depends_on=list(sd.get("depends_on", [])),
            planning_status=_planning_status(sd.get("planning_status", "proposed")),
            parallel_group=sd.get("parallel_group"),
            plan_path=sd.get("plan_path"),
            refs=list(sd.get("refs", [])),
            notes=sd.get("notes", ""),
            reviewer_chain=sd.get("reviewer_chain"),
            tasks=[_task(t) for t in sd.get("tasks", [])],
        )
    def _phase(pd):
        return Phase(
            id=pd["id"], title=pd["title"], created=pd["created"],
            started=pd.get("started"),
            status=_status(pd.get("status", "ready")),
            closed=pd.get("closed"),
            spec_path=pd.get("spec_path"),
            plan_path=pd.get("plan_path"),
            planning_path=pd.get("planning_path"),
            phase_reviewer_chain=pd.get("phase_reviewer_chain"),
            notes=pd.get("notes", ""),
            slices=[_slice(s) for s in pd.get("slices", [])],
        )
    def _cross(xd):
        return CrossCutting(
            id=xd["id"], title=xd["title"], created=xd["created"],
            started=xd.get("started"),
            status=_status(xd.get("status", "ready")),
            closed=xd.get("closed"),
            refs=list(xd.get("refs", [])),
            notes=xd.get("notes", ""),
        )
    def _arch(ad):
        return ArchivedPhase(
            id=ad["id"], title=ad["title"],
            archived_path=ad["archived_path"], archived_date=ad["archived_date"],
        )
    return Project(
        project=d["project"],
        schema_version=d.get("schema_version", SCHEMA_VERSION),
        north_star=d.get("north_star", ""),
        last_reviewed=d.get("last_reviewed"),
        phases=[_phase(p) for p in d.get("phases", [])],
        cross_cutting=[_cross(x) for x in d.get("cross_cutting", [])],
        archived_phases=[_arch(a) for a in d.get("archived_phases", [])],
    )

def dumps_canonical(p: Project) -> str:
    body = json.dumps(to_dict(p), indent=2, sort_keys=True, ensure_ascii=False)
    return body + "\n"

def loads_project(text: str) -> Project:
    return from_dict(json.loads(text))

def load_project(path: Path) -> Project:
    return loads_project(path.read_text(encoding="utf-8"))

def save_project(p: Project, path: Path) -> None:
    """Atomic write: tempfile + rename. Always canonical bytes."""
    text = dumps_canonical(p)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
