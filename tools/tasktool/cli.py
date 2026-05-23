# tools/tasktool/cli.py
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from tasktool import commands
from tasktool import hook_handshake

def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "docs").is_dir() or (p / ".git").exists():
            return p
    return cur

def _is_project_marker(path: Path) -> bool:
    return (path / "docs").is_dir() or (path / ".git").exists() or (path / ".tasktool").exists()

def _resolve_project_root(args: argparse.Namespace) -> Path:
    if args.project_root is not None:
        return args.project_root
    cwd = Path.cwd()
    if (
        args.cmd == "config"
        and args.config_cmd in {"init-authority", "init-local"}
        and not _is_project_marker(cwd)
    ):
        return cwd.resolve()
    return _find_repo_root(cwd)

def _comma_split(values: list[str]) -> list[str]:
    return [item for value in values for item in value.split(",") if item]

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

    p_config = sub.add_parser("config")
    config_sub = p_config.add_subparsers(dest="config_cmd", required=True)
    p_config_auth = config_sub.add_parser("init-authority")
    p_config_auth.add_argument("--branch", default="main")
    config_sub.add_parser("init-local")
    p_config_migrate = config_sub.add_parser("migrate-from-local")
    p_config_migrate.add_argument("--authority-root", type=Path)
    p_config_migrate.add_argument("--local-root", type=Path)
    p_config_migrate.add_argument("--dry-run", action="store_true")
    migrate_policy = p_config_migrate.add_mutually_exclusive_group()
    migrate_policy.add_argument("--accept-local", action="store_true")
    migrate_policy.add_argument("--accept-authoritative", action="store_true")

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
    p_set.add_argument("--allow-ready-close", action="store_true")
    p_set.add_argument("--reason")

    p_start = sub.add_parser("start")
    p_start.add_argument("id", nargs="?")
    p_start.add_argument("--resume", action="store_true")
    p_start_mode = p_start.add_mutually_exclusive_group()
    p_start_mode.add_argument("--in-place", action="store_true")
    p_start_mode.add_argument("--adopt", metavar="PATH")
    p_start_mode.add_argument("--ad-hoc", metavar="SLUG")

    p_wt = sub.add_parser("worktree")
    wt_sub = p_wt.add_subparsers(dest="wt_cmd", required=True)
    p_wt_list = wt_sub.add_parser("list")
    p_wt_list.add_argument("--all", action="store_true", dest="show_all")
    p_wt_status = wt_sub.add_parser("status")
    p_wt_status.add_argument("id")
    p_wt_adopt = wt_sub.add_parser("adopt")
    p_wt_adopt.add_argument("id")
    p_wt_adopt.add_argument("path")
    wt_sub.add_parser("ensure-gitignore")
    p_wt_legacy = wt_sub.add_parser("check-legacy")
    p_wt_legacy.add_argument("--project", required=True)

    p_wt_prune = wt_sub.add_parser("prune")
    p_wt_prune.add_argument("id")
    prune_excl = p_wt_prune.add_mutually_exclusive_group()
    prune_excl.add_argument("--keep-branch", action="store_true")
    prune_excl.add_argument("--force", action="store_true")
    prune_excl.add_argument("--finalize", action="store_true")

    p_wt_repair = wt_sub.add_parser("repair")
    p_wt_repair.add_argument("id")

    p_close = sub.add_parser("close")
    p_close.add_argument("id")
    p_close.add_argument(
        "--refs", action="append", default=[],
        help="Comma-separated refs. May be passed more than once.",
    )
    p_close.add_argument("--closed-date")
    p_close.add_argument("--note")
    p_close.add_argument("--reviewer-chain", type=Path)
    p_close.add_argument("--skip-review-gate", action="store_true")
    p_close.add_argument("--allow-ready-close", action="store_true")
    p_close.add_argument("--reason")
    p_close.add_argument("--no-archive", action="store_true")

    p_cancel = sub.add_parser("cancel")
    p_cancel.add_argument("id")
    p_cancel.add_argument("--reason", required=True)
    p_cancel.add_argument("--cascade", action="store_true")
    p_cancel.add_argument("--no-archive", action="store_true")

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

    p_artifact = sub.add_parser("artifact")
    artifact_sub = p_artifact.add_subparsers(dest="artifact_cmd", required=True)
    p_artifact_add = artifact_sub.add_parser("add")
    p_artifact_add.add_argument("id")
    p_artifact_add.add_argument("--kind", required=True, choices=["spec", "plan", "handoff", "reviewer", "archive"])
    p_artifact_add.add_argument("--path", required=True, type=Path)
    p_artifact_add.add_argument("--allow-missing", action="store_true")
    p_artifact_status = artifact_sub.add_parser("status")
    p_artifact_status.add_argument("id", nargs="?")
    p_artifact_status.add_argument("--format", choices=["text", "json"], default="text")
    p_artifact_status.add_argument("--strict", action="store_true")
    p_artifact_commit = artifact_sub.add_parser("commit")
    p_artifact_commit.add_argument("id")
    p_artifact_commit.add_argument("--message", required=True)

    p_prepare = sub.add_parser("prepare")
    prepare_sub = p_prepare.add_subparsers(dest="prepare_mode", required=True)
    p_prepare_cross = prepare_sub.add_parser("cross")
    p_prepare_cross.add_argument("--title", required=True)
    p_prepare_cross.add_argument("--spec")
    p_prepare_cross.add_argument("--plan")
    p_prepare_cross.add_argument("--handoff")
    p_prepare_phase = prepare_sub.add_parser("phase")
    p_prepare_phase.add_argument("--title", required=True)
    p_prepare_phase.add_argument("--spec")
    p_prepare_phase.add_argument("--plan")
    p_prepare_phase.add_argument("--handoff")
    p_prepare_slice = prepare_sub.add_parser("slice")
    p_prepare_slice.add_argument("phase_id")
    p_prepare_slice.add_argument("--title", required=True)
    p_prepare_slice.add_argument("--plan")
    p_prepare_slice.add_argument("--handoff")
    p_prepare_existing = prepare_sub.add_parser("existing")
    p_prepare_existing.add_argument("id")
    p_prepare_existing.add_argument("--spec")
    p_prepare_existing.add_argument("--plan")
    p_prepare_existing.add_argument("--handoff")

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
    p_list.add_argument("--all", dest="show_all", action="store_true")
    p_list.add_argument("--format", choices=["text", "json"], default="text")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--format", choices=["text", "json"], default="text")
    p_validate.add_argument("--strict-format", action="store_true")
    p_validate.add_argument("--normalise", action="store_true")
    p_validate.add_argument("--check-orphans", nargs="*", default=None,
                            help="Spec/plan filepaths to check against tasklist.json IDs.")
    p_validate.add_argument("--no-path-warnings", action="store_true",
                            help="Skip warnings for refs/spec_path/plan_path that don't exist on disk. "
                                 "Used by the pre-commit hook, which validates a sandboxed copy of "
                                 "tasklist.json where peer files are intentionally absent.")

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

    p_arch_cross = sub.add_parser("archive-cross")
    p_arch_cross.add_argument("id")

    p_nextid = sub.add_parser("next-id")
    p_nextid.add_argument("--kind", required=True, choices=["phase", "slice", "task", "cross"])
    p_nextid.add_argument("--phase")
    p_nextid.add_argument("--slice")
    return parser

def main(argv: list[str]) -> int:
    hook_drift_msg = hook_handshake.check_pre_commit_hook()
    if hook_drift_msg is not None:
        print(hook_drift_msg, file=sys.stderr)
        return 1
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = _resolve_project_root(args)
    # Plumb --no-stage into the commands module's process-global toggle.
    commands.STAGE_AFTER_WRITE = not args.no_stage

    try:
        if args.cmd == "config":
            if args.config_cmd == "init-authority":
                commands.cmd_config_init_authority(
                    repo_root=root,
                    branch=args.branch,
                )
            elif args.config_cmd == "init-local":
                commands.cmd_config_init_local(repo_root=root)
            elif args.config_cmd == "migrate-from-local":
                commands.cmd_config_migrate_from_local(
                    repo_root=root,
                    authority_root=args.authority_root,
                    local_root=args.local_root,
                    dry_run=args.dry_run,
                    accept_local=args.accept_local,
                    accept_authoritative=args.accept_authoritative,
                    stdin_is_tty=sys.stdin.isatty(),
                )
        elif args.cmd == "init":
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
                allow_ready_close=args.allow_ready_close, reason=args.reason,
            )
        elif args.cmd == "start":
            if args.ad_hoc is not None:
                if args.id is not None:
                    parser.error("--ad-hoc cannot be combined with a positional id")
            elif not args.id:
                parser.error("start requires <id> unless --ad-hoc <slug> is given")
            commands.cmd_start(
                repo_root=root, id=args.id, resume=args.resume,
                in_place=args.in_place, adopt=args.adopt, ad_hoc=args.ad_hoc,
            )
        elif args.cmd == "worktree":
            if args.wt_cmd == "list":
                sys.stdout.write(commands.cmd_worktree_list(repo_root=root, show_all=args.show_all))
            elif args.wt_cmd == "status":
                sys.stdout.write(commands.cmd_worktree_status(repo_root=root, id=args.id))
            elif args.wt_cmd == "adopt":
                commands.cmd_worktree_adopt(repo_root=root, id=args.id, path=Path(args.path))
            elif args.wt_cmd == "ensure-gitignore":
                sys.stdout.write(commands.cmd_worktree_ensure_gitignore(repo_root=root))
            elif args.wt_cmd == "check-legacy":
                text, rc = commands.cmd_worktree_check_legacy(repo_root=root, project_name=args.project)
                sys.stdout.write(text)
                if rc != 0:
                    return rc
            elif args.wt_cmd == "prune":
                commands.cmd_worktree_prune(
                    repo_root=root,
                    id=args.id,
                    keep_branch=args.keep_branch,
                    force=args.force,
                    finalize=args.finalize,
                )
            elif args.wt_cmd == "repair":
                commands.cmd_worktree_repair(repo_root=root, id=args.id)
        elif args.cmd == "close":
            refs = _comma_split(args.refs) or None
            commands.cmd_close(
                repo_root=root, id=args.id, refs=refs,
                closed_date=args.closed_date, note=args.note,
                reviewer_chain=args.reviewer_chain, skip_review_gate=args.skip_review_gate,
                allow_ready_close=args.allow_ready_close, reason=args.reason,
                no_archive=args.no_archive,
            )
        elif args.cmd == "cancel":
            commands.cmd_cancel(
                repo_root=root, id=args.id, reason=args.reason,
                cascade=args.cascade, no_archive=args.no_archive,
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
        elif args.cmd == "artifact":
            if args.artifact_cmd == "add":
                commands.cmd_artifact_add(
                    repo_root=root,
                    id=args.id,
                    kind=args.kind,
                    path=args.path,
                    allow_missing=args.allow_missing,
                )
            elif args.artifact_cmd == "status":
                return commands.cmd_artifact_status(
                    repo_root=root,
                    id=args.id,
                    strict=args.strict,
                    format=args.format,
                )
            elif args.artifact_cmd == "commit":
                commands.cmd_artifact_commit(
                    repo_root=root,
                    id=args.id,
                    message=args.message,
                )
        elif args.cmd == "prepare":
            commands.cmd_prepare(
                repo_root=root,
                mode=args.prepare_mode,
                id=getattr(args, "id", None),
                phase_id=getattr(args, "phase_id", None),
                title=getattr(args, "title", None),
                spec=getattr(args, "spec", None),
                plan=getattr(args, "plan", None),
                handoff=getattr(args, "handoff", None),
            )
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
                kind=args.kind, open_only=args.open_only,
                show_all=args.show_all, format=args.format,
            ))
        elif args.cmd == "validate":
            rc, text = commands.cmd_validate(
                repo_root=root, format=args.format,
                strict_format=args.strict_format, normalise=args.normalise,
                check_orphans=args.check_orphans,
                no_path_warnings=args.no_path_warnings,
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
        elif args.cmd == "archive-cross":
            commands.cmd_archive_cross(repo_root=root, id=args.id)
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
