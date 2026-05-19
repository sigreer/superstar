# tools/tasktool/cli.py
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from tasktool import commands

def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "docs").is_dir() or (p / ".git").exists():
            return p
    return cur

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasktool")
    parser.add_argument("--project-root", type=Path, default=None,
                        help="Project root (default: walk up from cwd)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress non-error output. Accepted but minimally used in S1; reserved for richer logging in later slices.")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose output. Same caveat as --quiet for S1.")
    parser.add_argument("--no-stage", action="store_true",
                        help="Skip `git add` after mutating writes (default: best-effort stage).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--project", default=None,
                        help="project name (defaults to repo_root directory name)")
    p_init.add_argument("--north-star", default="")
    p_init.add_argument("--force", action="store_true")

    p_create = sub.add_parser("create")
    create_sub = p_create.add_subparsers(dest="create_kind", required=True)
    p_phase = create_sub.add_parser("phase")
    p_phase.add_argument("--title", required=True)
    p_phase.add_argument("--spec")
    p_phase.add_argument("--plan")
    p_phase.add_argument("--planning")
    p_slice = create_sub.add_parser("slice")
    p_slice.add_argument("phase_id")
    p_slice.add_argument("--title", required=True)
    p_slice.add_argument("--follow-up")
    p_slice.add_argument("--plan")
    p_slice.add_argument(
        "--depends-on", action="append", default=[],
        help="Comma-separated slice dependencies. May be passed more than once.",
    )
    p_slice.add_argument("--parallel-group")
    p_task = create_sub.add_parser("task")
    p_task.add_argument("slice_id")
    p_task.add_argument("--title", required=True)
    p_cross = create_sub.add_parser("cross")
    p_cross.add_argument("--title", required=True)

    p_set = sub.add_parser("set")
    p_set.add_argument("id")
    p_set.add_argument("--status", required=True,
                       choices=["ready", "in_progress", "done"])
    p_set.add_argument("--reviewer-chain", type=Path)
    p_set.add_argument("--skip-review-gate", action="store_true")

    p_close = sub.add_parser("close")
    p_close.add_argument("id")
    p_close.add_argument("--refs", default="")
    p_close.add_argument("--closed-date")
    p_close.add_argument("--note")
    p_close.add_argument("--reviewer-chain", type=Path)
    p_close.add_argument("--skip-review-gate", action="store_true")

    p_block = sub.add_parser("block")
    p_block.add_argument("slice_id")
    p_block.add_argument("--on", required=True)

    p_unblock = sub.add_parser("unblock")
    p_unblock.add_argument("slice_id")
    p_unblock.add_argument("--resume", action="store_true")

    p_deps = sub.add_parser("deps")
    p_deps.add_argument("slice_id")
    g = p_deps.add_mutually_exclusive_group(required=True)
    g.add_argument("--add")
    g.add_argument("--remove")

    p_ratify = sub.add_parser("ratify")
    p_ratify.add_argument("slice_id")
    p_ratify.add_argument("--status", choices=["proposed", "ratified", "superseded"],
                          default="ratified")
    p_ratify.add_argument("--parallel-group")

    p_planning_path = sub.add_parser("planning-path")
    p_planning_path.add_argument("phase_id")
    p_planning_path.add_argument("--set", dest="path", required=True)

    p_note = sub.add_parser("note")
    p_note.add_argument("id")
    g = p_note.add_mutually_exclusive_group(required=True)
    g.add_argument("--append")
    g.add_argument("--replace")

    p_ref = sub.add_parser("ref")
    p_ref.add_argument("id")
    g = p_ref.add_mutually_exclusive_group(required=True)
    g.add_argument("--add")
    g.add_argument("--remove")

    p_title = sub.add_parser("title")
    p_title.add_argument("id")
    p_title.add_argument("--set", dest="new", required=True)

    p_show = sub.add_parser("show")
    p_show.add_argument("id")

    p_brief = sub.add_parser("brief")
    p_brief.add_argument("id")

    p_phase_status = sub.add_parser("phase-status")
    p_phase_status.add_argument("--recent", type=int, default=3)
    p_phase_status.add_argument("--format", choices=["text", "json"], default="text")

    p_schedule = sub.add_parser("schedule")
    p_schedule.add_argument("phase_id")
    p_schedule.add_argument("--format", choices=["text", "json"], default="text")

    p_ready = sub.add_parser("ready-slices")
    p_ready.add_argument("phase_id")
    p_ready.add_argument("--format", choices=["text", "json"], default="text")

    p_list = sub.add_parser("list")
    p_list.add_argument("--phase")
    p_list.add_argument("--status")
    p_list.add_argument("--kind", choices=["phase", "slice", "task", "cross"])
    p_list.add_argument("--open", dest="open_only", action="store_true")
    p_list.add_argument("--format", choices=["text", "json"], default="text")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--format", choices=["text", "json"], default="text")
    p_validate.add_argument("--strict-format", action="store_true")
    p_validate.add_argument("--normalise", action="store_true")
    p_validate.add_argument("--check-orphans", nargs="*", default=None,
                            help="Spec/plan filepaths to check against tasklist.json IDs.")

    sub.add_parser("schema")

    p_render = sub.add_parser("render")
    p_render.add_argument("--format", default="markdown", choices=["markdown"])

    p_import = sub.add_parser("import")
    p_import.add_argument("md_path", type=Path)
    p_import.add_argument("--dry-run", action="store_true")
    p_import.add_argument("--force", action="store_true")
    p_import.add_argument("--project")

    p_arch = sub.add_parser("archive-phase")
    p_arch.add_argument("phase_id")
    p_arch.add_argument("--reviewer-chain", type=Path)
    p_arch.add_argument("--skip-review-gate", action="store_true")

    p_nextid = sub.add_parser("next-id")
    p_nextid.add_argument("--kind", required=True, choices=["phase", "slice", "task", "cross"])
    p_nextid.add_argument("--phase")
    p_nextid.add_argument("--slice")
    return parser

def main(argv: list[str]) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = args.project_root or _find_repo_root(Path.cwd())
    # Plumb --no-stage into the commands module's process-global toggle.
    commands.STAGE_AFTER_WRITE = not args.no_stage

    try:
        if args.cmd == "init":
            commands.cmd_init(repo_root=root, project=args.project, north_star=args.north_star, force=args.force)
        elif args.cmd == "create":
            if args.create_kind == "phase":
                print(commands.cmd_create_phase(
                    repo_root=root, title=args.title, spec=args.spec,
                    plan=args.plan, planning=args.planning,
                ))
            elif args.create_kind == "slice":
                deps = [
                    dep
                    for value in args.depends_on
                    for dep in value.split(",")
                    if dep
                ]
                print(commands.cmd_create_slice(
                    repo_root=root, phase_id=args.phase_id, title=args.title,
                    follow_up=args.follow_up, plan=args.plan,
                    depends_on=deps, parallel_group=args.parallel_group,
                ))
            elif args.create_kind == "task":
                print(commands.cmd_create_task(repo_root=root, slice_id=args.slice_id, title=args.title))
            elif args.create_kind == "cross":
                print(commands.cmd_create_cross(repo_root=root, title=args.title))
        elif args.cmd == "set":
            commands.cmd_set(
                repo_root=root, id=args.id, status=args.status,
                reviewer_chain=args.reviewer_chain, skip_review_gate=args.skip_review_gate,
            )
        elif args.cmd == "close":
            refs = [r for r in args.refs.split(",") if r] if args.refs else None
            commands.cmd_close(
                repo_root=root, id=args.id, refs=refs,
                closed_date=args.closed_date, note=args.note,
                reviewer_chain=args.reviewer_chain, skip_review_gate=args.skip_review_gate,
            )
        elif args.cmd == "block":
            commands.cmd_block(repo_root=root, slice_id=args.slice_id, on=args.on)
        elif args.cmd == "unblock":
            commands.cmd_unblock(repo_root=root, slice_id=args.slice_id, resume=args.resume)
        elif args.cmd == "deps":
            commands.cmd_deps(repo_root=root, slice_id=args.slice_id, add=args.add, remove=args.remove)
        elif args.cmd == "ratify":
            commands.cmd_ratify(
                repo_root=root, slice_id=args.slice_id,
                status=args.status, parallel_group=args.parallel_group,
            )
        elif args.cmd == "planning-path":
            commands.cmd_phase_planning_path(repo_root=root, phase_id=args.phase_id, path=args.path)
        elif args.cmd == "note":
            commands.cmd_note(repo_root=root, id=args.id, append=args.append, replace=args.replace)
        elif args.cmd == "ref":
            commands.cmd_ref(repo_root=root, id=args.id, add=args.add, remove=args.remove)
        elif args.cmd == "title":
            commands.cmd_title(repo_root=root, id=args.id, new=args.new)
        elif args.cmd == "show":
            sys.stdout.write(commands.cmd_show(repo_root=root, id=args.id))
        elif args.cmd == "brief":
            sys.stdout.write(commands.cmd_brief(repo_root=root, id=args.id))
        elif args.cmd == "phase-status":
            sys.stdout.write(commands.cmd_phase_status(
                repo_root=root, recent=args.recent, format=args.format,
            ))
        elif args.cmd == "schedule":
            sys.stdout.write(commands.cmd_schedule(
                repo_root=root, phase_id=args.phase_id, format=args.format,
            ))
        elif args.cmd == "ready-slices":
            sys.stdout.write(commands.cmd_ready_slices(
                repo_root=root, phase_id=args.phase_id, format=args.format,
            ))
        elif args.cmd == "list":
            status_list = args.status.split(",") if args.status else None
            sys.stdout.write(commands.cmd_list(
                repo_root=root, phase=args.phase, status=status_list,
                kind=args.kind, open_only=args.open_only, format=args.format,
            ))
        elif args.cmd == "validate":
            rc, text = commands.cmd_validate(
                repo_root=root, format=args.format,
                strict_format=args.strict_format, normalise=args.normalise,
                check_orphans=args.check_orphans,
            )
            sys.stdout.write(text)
            return rc
        elif args.cmd == "schema":
            sys.stdout.write(commands.cmd_schema())
        elif args.cmd == "render":
            sys.stdout.write(commands.cmd_render(repo_root=root, format=args.format))
        elif args.cmd == "import":
            rc, out, warn = commands.cmd_import(
                repo_root=root, md_path=args.md_path,
                dry_run=args.dry_run, force=args.force, project=args.project,
            )
            if out:
                sys.stdout.write(out)
            if warn:
                sys.stderr.write(warn + "\n")
            return rc
        elif args.cmd == "archive-phase":
            commands.cmd_archive_phase(
                repo_root=root, phase_id=args.phase_id,
                reviewer_chain=args.reviewer_chain,
                skip_review_gate=args.skip_review_gate,
            )
        elif args.cmd == "next-id":
            print(commands.cmd_next_id(
                repo_root=root, kind=args.kind, phase=args.phase, slice=args.slice,
            ))
        else:
            print(f"unknown command: {args.cmd}", file=sys.stderr)
            return 2
    except commands.CommandError as e:
        print(f"tasktool: {e}", file=sys.stderr)
        return 1
    return 0
