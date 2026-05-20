#!/usr/bin/env python3
"""Compatibility shim for old Superstar handoffs.

The canonical bridge is the global `external-reviewer` command.
"""

from __future__ import annotations

import os
import shutil
import sys


def main() -> int:
    target = shutil.which("external-reviewer")
    if target is None:
        print(
            "scripts/external-reviewer.py is a compatibility shim, but "
            "`external-reviewer` is not on PATH. Install it with Superstar's "
            "skills/external-review/install.sh.",
            file=sys.stderr,
        )
        return 127

    script_path = os.path.realpath(__file__)
    target_path = os.path.realpath(target)
    if target_path == script_path:
        print(
            "scripts/external-reviewer.py resolved `external-reviewer` back to "
            "itself. Fix PATH so the global Superstar bridge appears before "
            "this repo-local compatibility shim.",
            file=sys.stderr,
        )
        return 127

    os.execvp(target, [target, *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
