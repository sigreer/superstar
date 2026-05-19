from __future__ import annotations
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, Status
from tasktool.ids import parse_id


def _find(p: Project, qid: str):
    parts = qid.split(".")
    if len(parts) == 1:
        if qid.startswith("P"):
            return next((ph for ph in p.phases if ph.id == qid), None)
        if qid.startswith("X"):
            return next((c for c in p.cross_cutting if c.id == qid), None)
        return None
    if len(parts) == 2:
        ph = next((ph for ph in p.phases if ph.id == parts[0]), None)
        if ph is None:
            return None
        return next((s for s in ph.slices if s.id == parts[1]), None)
    if len(parts) == 3:
        ph = next((ph for ph in p.phases if ph.id == parts[0]), None)
        if ph is None:
            return None
        s = next((s for s in ph.slices if s.id == parts[1]), None)
        if s is None:
            return None
        return next((t for t in s.tasks if t.id == parts[2]), None)
    return None


def _phase_for(p: Project, qid: str) -> Phase | None:
    return next((ph for ph in p.phases if ph.id == qid.split(".")[0]), None)


def _slice_for(p: Project, qid: str) -> Slice | None:
    parts = qid.split(".")
    if len(parts) < 2:
        return None
    ph = _phase_for(p, qid)
    if ph is None:
        return None
    return next((s for s in ph.slices if s.id == parts[1]), None)


def brief(p: Project, qid: str) -> str:
    item = _find(p, qid)
    if item is None:
        raise ValueError(f"{qid}: not found")
    kind = parse_id(qid)[0]
    lines: list[str] = []
    if kind == "slice":
        assert isinstance(item, Slice)
        ph = _phase_for(p, qid)
        assert ph is not None
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.started:
            lines.append(f"started: {item.started}")
        if item.plan_path:
            lines.append(f"plan: {item.plan_path}")
        if item.depends_on:
            lines.append("depends_on:")
            for dep in item.depends_on:
                lines.append(f"  - {dep}")
        lines.append(f"planning_status: {item.planning_status.value}")
        if item.parallel_group:
            lines.append(f"parallel_group: {item.parallel_group}")
        if item.reviewer_chain:
            lines.append(f"reviewer_chain: {item.reviewer_chain}")
        lines.append("")
        lines.append(f"Parent phase: {ph.id} — {ph.title} [{ph.status.value}]")
        lines.append("")
        lines.append("Sibling slices:")
        for s in ph.slices:
            lines.append(f"  {s.id}  [{s.status.value}]  {s.title}")
        lines.append("")
        lines.append("Open tasks:")
        for t in item.tasks:
            if t.status is not Status.DONE:
                lines.append(f"  {t.id}  [{t.status.value}]  {t.title}")
    elif kind == "phase":
        assert isinstance(item, Phase)
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.started:
            lines.append(f"started: {item.started}")
        if item.spec_path:
            lines.append(f"spec: {item.spec_path}")
        if item.plan_path:
            lines.append(f"plan: {item.plan_path}")
        if item.planning_path:
            lines.append(f"planning: {item.planning_path}")
        lines.append("")
        lines.append("Slices:")
        for s in item.slices:
            deps = f" deps={','.join(s.depends_on)}" if s.depends_on else ""
            group = f" group={s.parallel_group}" if s.parallel_group else ""
            started = f" started={s.started}" if s.started else ""
            lines.append(
                f"  {s.id}  [{s.status.value}]{started} planning={s.planning_status.value}"
                f"{group}{deps}  {s.title}"
            )
    elif kind == "task":
        assert isinstance(item, Task)
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.started:
            lines.append(f"started: {item.started}")
        if item.notes:
            lines.append(f"notes:\n{item.notes}")
        s = _slice_for(p, qid)
        if s is not None:
            lines.append("")
            lines.append(f"Parent slice: {s.id} — {s.title} [{s.status.value}]")
    elif kind == "cross":
        assert isinstance(item, CrossCutting)
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.started:
            lines.append(f"started: {item.started}")
        if item.refs:
            lines.append("refs:")
            for r in item.refs:
                lines.append(f"  - {r}")
        if item.notes:
            lines.append(f"notes:\n{item.notes}")
    return "\n".join(lines) + "\n"
