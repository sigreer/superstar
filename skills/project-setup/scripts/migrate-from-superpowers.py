#!/usr/bin/env python3
"""Migrate a project from upstream `superpowers` to the superstar fork layout.

Three classes of change, applied in order:

1. Reference rewrites (in-place, all text file types):
     docs/superpowers/specs/  -> docs/specs/
     docs/superpowers/plans/  -> docs/plans/
     docs/superpowers/        -> docs/
     superpowers:requesting-code-review -> superstar:requesting-internal-review
     superpowers:receiving-code-review  -> superstar:receiving-internal-review
     superpowers:using-superpowers      -> superstar:using-superstar
     superpowers:                       -> superstar:           (catch-all)
     obra/superpowers                   -> sigreer/superstar
     superpowers@                       -> superstar@

2. Path moves (git mv, history-preserving):
     docs/superpowers/specs/** -> docs/specs/**
     docs/superpowers/plans/** -> docs/plans/**
     docs/superpowers/* (loose files) -> docs/*

3. Cleanup: rmdir docs/superpowers/ once empty.

Dry-run by default. Pass --apply to write. No commit is made;
review with `git status` and commit at your discretion.

Usage:
  migrate-from-superpowers.py                          # dry-run, both phases
  migrate-from-superpowers.py --apply                  # default: paths=migrate, refs=update
  migrate-from-superpowers.py --apply --paths=duplicate --refs=update
  migrate-from-superpowers.py --refs=list              # print refs as file:line, no writes
  migrate-from-superpowers.py --emit=json              # machine-readable plan
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


# Ordered, most-specific first. Plain string replacement (not regex).
REF_MAPPINGS: list[tuple[str, str]] = [
    # Path references — trailing slash required so we don't mangle e.g. docs/superpowers-old.md
    ("docs/superpowers/specs/", "docs/specs/"),
    ("docs/superpowers/plans/", "docs/plans/"),
    ("docs/superpowers/", "docs/"),
    # Renamed skills (must precede the generic superpowers: rewrite)
    ("superpowers:requesting-code-review", "superstar:requesting-internal-review"),
    ("superpowers:receiving-code-review", "superstar:receiving-internal-review"),
    ("superpowers:using-superpowers", "superstar:using-superstar"),
    # Catch-all skill namespace
    ("superpowers:", "superstar:"),
    # Plugin / repo references
    ("obra/superpowers", "sigreer/superstar"),
    ("superpowers@", "superstar@"),
]

LEGACY_DIR = Path("docs/superpowers")
SPECS_SRC = LEGACY_DIR / "specs"
PLANS_SRC = LEGACY_DIR / "plans"
SPECS_DST = Path("docs/specs")
PLANS_DST = Path("docs/plans")
LOOSE_DST = Path("docs")

# Files exempt from reference rewrites. These either *define* the mapping
# (the script itself, the SKILL.md that documents it) or list legacy refs
# as historical record (CHANGELOGs, release notes). Matched as substrings
# against the relpath; one match exempts the file.
EXEMPT_PATH_SUBSTRINGS: tuple[str, ...] = (
    "migrate-from-superpowers.py",
    "skills/project-setup/SKILL.md",
    "RELEASE-NOTES.md",
    "CHANGELOG.md",
)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def repo_root() -> Path:
    return Path(_run(["git", "rev-parse", "--show-toplevel"]).stdout.strip())


def _is_text(path: Path, sample: int = 4096) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(sample)
        if b"\x00" in chunk:
            return False
        chunk.decode("utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def tracked_files(root: Path) -> list[Path]:
    """git-tracked + untracked-not-ignored files, text only."""
    out = _run(["git", "-C", str(root), "ls-files",
                "--cached", "--others", "--exclude-standard"]).stdout.splitlines()
    files: list[Path] = []
    for rel in out:
        if not rel:
            continue
        p = root / rel
        if p.is_file() and _is_text(p):
            files.append(p)
    return files


def plan_paths(root: Path) -> dict:
    legacy = root / LEGACY_DIR
    if not legacy.exists():
        return {"specs": [], "plans": [], "loose": [], "has_legacy_dir": False}

    specs_src = root / SPECS_SRC
    plans_src = root / PLANS_SRC
    specs = sorted(p for p in specs_src.rglob("*") if p.is_file()) if specs_src.exists() else []
    plans = sorted(p for p in plans_src.rglob("*") if p.is_file()) if plans_src.exists() else []

    loose = sorted(p for p in legacy.iterdir() if p.is_file())

    return {
        "specs": [p.relative_to(root) for p in specs],
        "plans": [p.relative_to(root) for p in plans],
        "loose": [p.relative_to(root) for p in loose],
        "has_legacy_dir": True,
    }


def _is_exempt(relpath: Path) -> bool:
    rel_str = str(relpath)
    return any(sub in rel_str for sub in EXEMPT_PATH_SUBSTRINGS)


def plan_refs(root: Path) -> dict[Path, list[tuple[str, str, int]]]:
    """Returns {relpath: [(old, new, occurrences), ...]} for files containing any mapping."""
    result: dict[Path, list[tuple[str, str, int]]] = {}
    for f in tracked_files(root):
        relpath = f.relative_to(root)
        if _is_exempt(relpath):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits: list[tuple[str, str, int]] = []
        for old, new in REF_MAPPINGS:
            count = text.count(old)
            if count > 0:
                hits.append((old, new, count))
        if hits:
            result[relpath] = hits
    return result


def apply_refs(root: Path, ref_plan: dict[Path, list[tuple[str, str, int]]]) -> int:
    """Rewrite refs in-place. Returns count of files written."""
    written = 0
    for relpath in ref_plan:
        path = root / relpath
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text = text
        for old, new in REF_MAPPINGS:
            new_text = new_text.replace(old, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            written += 1
    return written


def apply_paths_migrate(root: Path, plan: dict) -> None:
    (root / SPECS_DST).mkdir(parents=True, exist_ok=True)
    (root / PLANS_DST).mkdir(parents=True, exist_ok=True)

    for rel_src in plan["specs"]:
        rel_dst = SPECS_DST / rel_src.relative_to(SPECS_SRC)
        _git_mv(root, rel_src, rel_dst)
    for rel_src in plan["plans"]:
        rel_dst = PLANS_DST / rel_src.relative_to(PLANS_SRC)
        _git_mv(root, rel_src, rel_dst)
    for rel_src in plan["loose"]:
        rel_dst = LOOSE_DST / rel_src.name
        _git_mv(root, rel_src, rel_dst)

    _rmdir_if_empty(root / LEGACY_DIR)


def apply_paths_duplicate(root: Path, plan: dict) -> None:
    (root / SPECS_DST).mkdir(parents=True, exist_ok=True)
    (root / PLANS_DST).mkdir(parents=True, exist_ok=True)

    for rel_src in plan["specs"]:
        rel_dst = SPECS_DST / rel_src.relative_to(SPECS_SRC)
        _cp(root, rel_src, rel_dst)
    for rel_src in plan["plans"]:
        rel_dst = PLANS_DST / rel_src.relative_to(PLANS_SRC)
        _cp(root, rel_src, rel_dst)
    for rel_src in plan["loose"]:
        rel_dst = LOOSE_DST / rel_src.name
        _cp(root, rel_src, rel_dst)


def _git_mv(root: Path, src: Path, dst: Path) -> None:
    dst_abs = root / dst
    dst_abs.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "-C", str(root), "mv", str(src), str(dst)])


def _cp(root: Path, src: Path, dst: Path) -> None:
    src_abs, dst_abs = root / src, root / dst
    dst_abs.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_abs, dst_abs)
    _run(["git", "-C", str(root), "add", "-N", str(dst)])


def _rmdir_if_empty(d: Path) -> None:
    if not d.exists():
        return
    # Bottom-up cleanup
    for sub in sorted([p for p in d.rglob("*") if p.is_dir()],
                      key=lambda p: -len(p.parts)):
        try:
            sub.rmdir()
        except OSError:
            pass
    try:
        d.rmdir()
    except OSError:
        print(f"[warn] {d} not empty after migration; leaving in place",
              file=sys.stderr)


def summarize(path_plan: dict, ref_plan: dict, *, paths_action: str, refs_action: str) -> str:
    lines: list[str] = []
    lines.append("# Migration plan")
    lines.append("")
    lines.append(f"- paths: {paths_action}")
    lines.append(f"- refs:  {refs_action}")
    lines.append("")

    lines.append("## Path operations")
    if not path_plan["has_legacy_dir"]:
        lines.append("- docs/superpowers/ not present — nothing to move.")
    elif paths_action == "nothing":
        lines.append("- skipped (paths=nothing)")
    else:
        verb = "MOVE" if paths_action == "migrate" else "COPY"
        if path_plan["specs"]:
            lines.append(f"- {verb} docs/superpowers/specs/ → docs/specs/ — {len(path_plan['specs'])} files")
        if path_plan["plans"]:
            lines.append(f"- {verb} docs/superpowers/plans/ → docs/plans/ — {len(path_plan['plans'])} files")
        if path_plan["loose"]:
            lines.append(f"- {verb} {len(path_plan['loose'])} loose files → docs/:")
            for p in path_plan["loose"]:
                lines.append(f"    - {p.name}")
        if paths_action == "migrate":
            lines.append("- rmdir docs/superpowers/ once empty")
    lines.append("")

    lines.append("## Reference rewrites")
    if not ref_plan:
        lines.append("- no references to rewrite.")
    elif refs_action == "nothing":
        lines.append(f"- skipped (refs=nothing); {len(ref_plan)} files would otherwise change.")
    elif refs_action == "list":
        lines.append(f"- list-only mode; {len(ref_plan)} files. Per-file hits:")
        for rel, hits in sorted(ref_plan.items()):
            for old, new, count in hits:
                lines.append(f"    {rel}: {count}x `{old}` → `{new}`")
    else:  # update
        totals: dict[str, int] = {}
        for hits in ref_plan.values():
            for old, _, _ in hits:
                totals[old] = totals.get(old, 0) + 1
        lines.append(f"- {len(ref_plan)} files contain rewritable references.")
        for old, count in sorted(totals.items(), key=lambda kv: -kv[1]):
            new = next(n for o, n in REF_MAPPINGS if o == old)
            lines.append(f"    - `{old}` → `{new}`: in {count} files")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate a project from upstream superpowers to superstar layout.")
    parser.add_argument("--apply", action="store_true",
                        help="Execute the migration (default: dry-run).")
    parser.add_argument("--paths", choices=["migrate", "duplicate", "nothing"], default="migrate",
                        help="Path action (default: migrate).")
    parser.add_argument("--refs", choices=["update", "list", "nothing"], default="update",
                        help="Reference action (default: update).")
    parser.add_argument("--emit", choices=["text", "json"], default="text",
                        help="Output format for the summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    path_plan = plan_paths(root)
    ref_plan = plan_refs(root)

    if args.emit == "json":
        out = {
            "paths_action": args.paths,
            "refs_action": args.refs,
            "apply": args.apply,
            "paths": {
                "has_legacy_dir": path_plan["has_legacy_dir"],
                "specs": [str(p) for p in path_plan["specs"]],
                "plans": [str(p) for p in path_plan["plans"]],
                "loose": [str(p) for p in path_plan["loose"]],
            },
            "refs": {
                str(rel): [{"old": o, "new": n, "occurrences": c} for o, n, c in hits]
                for rel, hits in ref_plan.items()
            },
        }
        print(json.dumps(out, indent=2))
    else:
        print(summarize(path_plan, ref_plan, paths_action=args.paths, refs_action=args.refs))

    if not args.apply:
        if args.emit == "text":
            print("\n(dry-run; pass --apply to execute)")
        return 0

    # Apply: refs first (so file contents are correct before paths shift), then paths.
    if args.refs == "update" and ref_plan:
        written = apply_refs(root, ref_plan)
        print(f"\n[refs] rewrote {written} files", file=sys.stderr)

    if path_plan["has_legacy_dir"]:
        if args.paths == "migrate":
            apply_paths_migrate(root, path_plan)
            print("[paths] migrated docs/superpowers/ to docs/", file=sys.stderr)
        elif args.paths == "duplicate":
            apply_paths_duplicate(root, path_plan)
            print("[paths] duplicated docs/superpowers/ contents under docs/", file=sys.stderr)

    print("\nDone. Review with `git status` and commit when ready.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
