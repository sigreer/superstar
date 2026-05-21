from __future__ import annotations
from tasktool.model import Project, Phase, Slice, CrossCutting, Status

STATUS_EMOJI = {
    Status.DONE: "✅",
    Status.IN_PROGRESS: "🚧",
    Status.BLOCKED: "⏸",
    Status.READY: "☐",
}

def _slice_tag(s: Slice) -> str:
    if s.status is Status.DONE and s.closed:
        return f" `DONE {s.closed}`"
    if s.status is Status.IN_PROGRESS:
        return " `IN PROGRESS`"
    if s.status is Status.BLOCKED and s.blocked_on:
        prefix = "external:" if s.blocked_on.kind == "external" else ""
        return f" `BLOCKED on {prefix}{s.blocked_on.value}`"
    return ""

def _non_slice_emoji(status: Status) -> str:
    # Spec §6.6: blocked is slice-only. Defensively coerce to READY for phases/cross-cutting.
    if status is Status.BLOCKED:
        return STATUS_EMOJI[Status.READY]
    return STATUS_EMOJI[status]

def _phase_tag(ph: Phase) -> str:
    if ph.status is Status.DONE and ph.closed:
        return f" `DONE {ph.closed}`"
    if ph.status is Status.IN_PROGRESS:
        return " `IN PROGRESS`"
    return ""

def _started_part(item) -> str:
    started = getattr(item, "started", None)
    return f" Started: {started}." if started else ""

def render_project(p: Project) -> str:
    lines: list[str] = [f"# {p.project}", ""]
    if p.last_reviewed:
        lines += [f"**Last reviewed:** {p.last_reviewed}.", ""]
    if p.north_star:
        lines += ["## North Star", "", p.north_star, ""]
    for ph in p.phases:
        lines.append(f"## {ph.id} — {ph.title} {_non_slice_emoji(ph.status)}{_phase_tag(ph)}")
        lines.append("")
        if ph.started:
            lines.append(f"Started: {ph.started}.")
            lines.append("")
        if ph.spec_path or ph.plan_path:
            spec = f"[`{ph.spec_path}`]({ph.spec_path})" if ph.spec_path else "_none_"
            plan = f"[`{ph.plan_path}`]({ph.plan_path})" if ph.plan_path else "_pending_"
            lines.append(f"Spec: {spec}. Plan: {plan}.")
            lines.append("")
        if ph.planning_path:
            lines.append(f"Phase planning: [`{ph.planning_path}`]({ph.planning_path}).")
            lines.append("")
        for s in ph.slices:
            title = s.title
            plan_part = f" Plan: [`{s.plan_path}`]({s.plan_path})." if s.plan_path else ""
            dep_part = f" Depends on: {', '.join(s.depends_on)}." if s.depends_on else ""
            group_part = f" Group: `{s.parallel_group}`." if s.parallel_group else ""
            planning_part = f" Planning: `{s.planning_status.value}`."
            lines.append(
                f"- {STATUS_EMOJI[s.status]} **{s.id}**{_slice_tag(s)} — "
                f"{title}.{_started_part(s)}{planning_part}{group_part}{dep_part}{plan_part}"
            )
        lines.append("")
    if p.cross_cutting:
        lines += ["## Cross-cutting (`X*`)", ""]
        for c in p.cross_cutting:
            lines.append(f"- {_non_slice_emoji(c.status)} **{c.id}** — {c.title}.{_started_part(c)}")
        lines.append("")
    if p.archived_phases:
        lines += ["## Archived phases", ""]
        for a in p.archived_phases:
            lines.append(f"- **{a.id}** — {a.title} → [`{a.archived_path}`]({a.archived_path}) ({a.archived_date})")
        lines.append("")
    if p.archived_cross_cutting:
        lines += ["## Archived cross-cutting (`X*`)", ""]
        for a in p.archived_cross_cutting:
            lines.append(f"- **{a.id}** — {a.title} → [`{a.archived_path}`]({a.archived_path}) ({a.archived_date})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
