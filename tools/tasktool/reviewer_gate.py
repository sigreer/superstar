# tools/tasktool/reviewer_gate.py
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

ACCEPTABLE_VERDICTS = {"ready", "ready with small edits"}

class GateError(RuntimeError):
    pass

@dataclass(slots=True)
class GatePass:
    chain: Path
    verdict: str

def _id_token(work_id: str) -> str:
    return work_id.replace(".", "-").lower()

def _token_matches_name(token: str, name: str) -> bool:
    """Return True iff token appears as a hyphen-bounded segment in name."""
    import re
    return bool(re.search(rf"(^|-){re.escape(token)}(-|$)", name))

def discover_chain(repo_root: Path, work_id: str, kind: str, *, explicit: Path | None = None) -> Path:
    """Find the reviewer chain folder. kind ∈ {post-slice, post-phase}.
    If explicit is given, just validate it. Otherwise search docs/reviewer/."""
    if explicit is not None:
        # Resolve relative paths against repo_root so callers can pass relative paths.
        if not explicit.is_absolute():
            explicit = (repo_root / explicit).resolve()
        if not (explicit / "chain.json").is_file():
            raise GateError(f"{explicit}: not a reviewer chain folder (missing chain.json)")
        return explicit
    base = repo_root / "docs/reviewer"
    if not base.exists():
        raise GateError(f"no docs/reviewer/ directory in {repo_root}")
    token = _id_token(work_id)
    suffix = f"-{kind}"
    candidates = [
        d for d in base.iterdir()
        if d.is_dir() and d.name.endswith(suffix) and _token_matches_name(token, d.name.lower()[:-len(suffix)])
    ]
    if not candidates:
        raise GateError(
            f"no reviewer chain found for {work_id} {kind} under docs/reviewer/"
        )
    if len(candidates) > 1:
        names = ", ".join(c.name for c in candidates)
        raise GateError(
            f"multiple reviewer chains match {work_id} {kind}: {names}. "
            f"Pass --reviewer-chain to disambiguate."
        )
    return candidates[0]

def read_latest_verdict(chain: Path) -> str | None:
    manifest = json.loads((chain / "chain.json").read_text(encoding="utf-8"))
    rounds = manifest.get("rounds", [])
    if not rounds:
        return None
    last = rounds[-1]
    return last.get("merged_verdict") or last.get("verdict")

def check_gate(repo_root: Path, work_id: str, kind: str, *, explicit: Path | None = None) -> GatePass:
    chain = discover_chain(repo_root, work_id, kind, explicit=explicit)
    verdict = read_latest_verdict(chain)
    if verdict not in ACCEPTABLE_VERDICTS:
        raise GateError(
            f"{chain.name}: latest verdict is {verdict!r}; need one of "
            f"{sorted(ACCEPTABLE_VERDICTS)}. Apply findings and re-run the reviewer."
        )
    return GatePass(chain=chain, verdict=verdict)
