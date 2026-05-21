# Submodule guard for using-git-worktrees

Load this reference **only** when `tasktool start` reports a worktree-detection conflict caused by a submodule, or when the early-exit block in `SKILL.md` cannot decide whether the current directory is a linked worktree or a submodule checkout.

## Why this matters

`GIT_DIR != GIT_COMMON_DIR` is true in two distinct situations:

1. The current directory is a linked git worktree (e.g. `.worktrees/worktree-p5-s3-…`).
2. The current directory is a git submodule checkout.

The submodule case must **not** be treated as a worktree. Treating a submodule as a linked worktree skips legitimate worktree creation and corrupts the slice's evidence boundary.

## Disambiguating

Run:

```sh
git rev-parse --show-superproject-working-tree 2>/dev/null
```

- Empty output (or non-zero exit): you are **not** in a submodule. The `GIT_DIR != GIT_COMMON_DIR` signal is genuine — treat the directory as a linked worktree.
- Non-empty output (a path): you are inside a submodule of that superproject. Treat the directory as a normal repo checkout and do not skip the worktree creation step.

## What to do

If you discover you are in a submodule and tasktool refuses to proceed, leave the submodule (`cd` to the superproject root, or to the authoritative checkout) and re-run `tasktool start <id>` from there. Do not attempt to nest a worktree inside the submodule.
