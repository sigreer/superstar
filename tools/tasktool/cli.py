from __future__ import annotations

def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("tasktool — see docs/specs/2026-05-17-P2-tasktool-design.md")
        return 0
    print(f"tasktool: unknown command: {argv[0]}", flush=True)
    return 2
