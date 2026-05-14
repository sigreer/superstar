#!/usr/bin/env python3
"""
File-based bridge for third-party spec/plan review.

The script is intentionally provider-neutral. It builds a review prompt around
one target document, calls a configured reviewer command, and stores both the
request and the response under a per-chain folder at
docs/reviewer/<target-stem-no-date>-<kind>/. Each invocation is a new round —
existing rounds are never overwritten. Round number is derived from the count
of rN-*-request.md files already in the chain folder.

Configuration:
  AGENT_REVIEWER_CMD='reviewer-agent'
  AGENT_REVIEWER_TRANSPORT='arg'

If the command contains placeholders, it is executed through the shell after
substitution. If it contains no placeholders, the prompt is supplied according
to --prompt-transport: as one argument (default), as stdin, or as a prompt-file
path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Self-register in sys.modules so @dataclass works when this script is loaded
# via importlib.util.spec_from_file_location without prior registration
# (Python 3.12+ dataclasses inspect sys.modules[cls.__module__]).
if __name__ not in sys.modules:
    import types as _types
    _self_mod = _types.ModuleType(__name__)
    _self_mod.__dict__.update(globals())
    sys.modules[__name__] = _self_mod


REVIEW_PROMPT = """You are acting as an independent senior engineering reviewer.

Review stance:
- Lead with findings, ordered by severity.
- Focus on correctness, consistency, implementation risk, missing acceptance
  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
  from the codebase.
- Give exact file/line references when possible.
- If the document is sound, say that clearly and list residual risks.
- Keep the review actionable. Avoid broad rewrites unless the current structure
  creates concrete risk.

Repository root:
{repo_root}

Target kind:
{kind}

Review mode:
{mode_guidance}

Target document:
{target_file}

Additional context files:
{context_files}

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"

Read the files from disk. Do not rely only on the snippets in this prompt.
"""


MODE_GUIDANCE = {
    "spec": """Pre-implementation spec review. Check that the spec is complete,
internally consistent, grounded in the existing codebase, and specific enough to
drive an implementation plan. Do not review implemented code unless the spec
claims code already exists.""",
    "plan": """Pre-implementation plan review. Check that the plan faithfully
covers the associated spec, uses existing repo patterns, has executable tasks,
has realistic ordering, and includes concrete verification gates.""",
    "design": """Design artifact review. Check coverage, route/component mapping,
accessibility, responsive states, missing screens, and whether the design can be
implemented in the current repo without inventing unsupported abstractions.""",
    "implementation": """Implementation review. Check code changes against the
stated task, looking for behavioral regressions, missing tests, accidental
scope expansion, and repo-pattern drift.""",
    "post-slice": """Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.""",
    "post-phase": """Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.""",
    "other": """General document/code review. Apply the standard reviewer stance
and tailor findings to the supplied target and context.""",
}


PROMPT_SENTINEL_START = "<!-- superstar-prompt:start -->"
PROMPT_SENTINEL_END = "<!-- superstar-prompt:end -->"


def strip_prompt_echo(text: str) -> str:
    """Remove any superstar-prompt-sentinel-delimited region from `text`.

    Handles three cases beyond the simple full-block case:
    - End marker present but no start marker → delete from start of stream
      through (and including) the end marker. Models a tail-truncated echo
      where the beginning was capped off but the end marker survived.
    - Start marker present but no end marker → delete from the start marker
      to end of stream. Models a head-truncated echo.
    - Multiple full blocks → all removed.
    """
    if not text:
        return text
    out = text
    # Repeatedly strip full blocks first (greedy non-overlapping).
    while True:
        s = out.find(PROMPT_SENTINEL_START)
        e = out.find(PROMPT_SENTINEL_END)
        if s != -1 and e != -1 and e > s:
            out = out[:s] + out[e + len(PROMPT_SENTINEL_END):]
            continue
        break
    # Truncated-end case: end marker without a preceding start marker.
    e = out.find(PROMPT_SENTINEL_END)
    if e != -1 and out.find(PROMPT_SENTINEL_START) == -1:
        out = out[e + len(PROMPT_SENTINEL_END):]
    # Truncated-start case: start marker without a following end marker.
    s = out.find(PROMPT_SENTINEL_START)
    if s != -1 and out.find(PROMPT_SENTINEL_END) == -1:
        out = out[:s]
    return out


SUPPORTED_SCHEMA_VERSION = 1


class ManifestSchemaTooNew(Exception):
    """Raised when chain.json declares a schema_version newer than this script supports."""


def read_manifest(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("schema_version")
    if isinstance(version, int) and version > SUPPORTED_SCHEMA_VERSION:
        raise ManifestSchemaTooNew(
            f"chain.json schema_version {version} is newer than this script supports "
            f"(max {SUPPORTED_SCHEMA_VERSION}). Upgrade external-reviewer.py."
        )
    return data


def write_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def migrate_manifest_inplace(manifest: dict) -> None:
    """Add `status` and `returncode` keys to legacy round/reviewer entries.

    Legacy entries (pre-S1) lack these keys. We do not invent retroactive
    truth from `verdict_valid`: every legacy entry becomes `status: "unknown"`,
    `returncode: None`. Callers (preamble construction, resolution gate)
    treat `"unknown"` as untrusted-by-default per spec §S1.6.
    """
    if not isinstance(manifest, dict):
        return
    for r in manifest.get("rounds", []) or []:
        if "status" not in r:
            r["status"] = "unknown"
        if "returncode" not in r:
            r["returncode"] = None
        for rev in r.get("reviewers", []) or []:
            if "status" not in rev:
                rev["status"] = "unknown"
            if "returncode" not in rev:
                rev["returncode"] = None


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=True,
    )
    return Path(result.stdout.strip())


def rel_or_abs(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path.resolve())


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "document"


DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def chain_folder_name(target: Path, kind: str, work_id: str | None = None) -> str:
    stem = DATE_PREFIX_RE.sub("", target.stem)
    base = slugify(stem)
    if kind in ("post-slice", "post-phase") and work_id:
        work_id_slug = work_id.replace(".", "-")
        return f"{base}-{work_id_slug}-{kind}"
    return f"{base}-{kind}"


class AmbiguousLegacyChain(Exception):
    pass


def discover_legacy_chain(
    reviewer_root: Path,
    target_stem: str,
    kind: str,
    new_slug: str,
) -> Path | None:
    new_path = reviewer_root / new_slug
    if new_path.exists():
        return new_path
    if not reviewer_root.exists():
        return None
    legacy_old_name = f"{slugify(target_stem)}-{kind}"
    candidates = []
    for entry in reviewer_root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == legacy_old_name:
            # Only treat as legacy candidate if there is no chain.json — a chain.json
            # marks a new-regime chain (potentially for a different work-id) and must
            # never be silently reused.
            if not (entry / "chain.json").exists():
                candidates.append(entry)
        elif entry.name.startswith(f"{slugify(target_stem)}-") and entry.name.endswith(f"-{kind}"):
            # Legacy with embedded suffix (e.g. an interim variant). Treat as candidate.
            if entry.name != new_slug and not (entry / "chain.json").exists():
                candidates.append(entry)
    if not candidates:
        return None
    if len(candidates) > 1:
        names = ", ".join(c.name for c in candidates)
        raise AmbiguousLegacyChain(
            f"Multiple legacy chains match {slugify(target_stem)}-{kind}: {names}. "
            "Migrate manually or specify --chain-dir."
        )
    return candidates[0]


def next_round_number(chain_dir: Path) -> int:
    if not chain_dir.exists():
        return 1
    manifest = read_manifest(chain_dir / "chain.json")
    if manifest and isinstance(manifest.get("rounds"), list):
        return len(manifest["rounds"]) + 1
    return len(list(chain_dir.glob("r*-*-request.md"))) + 1


def numbered_preview(path: Path, root: Path, max_lines: int) -> str:
    rel = rel_or_abs(path, root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return f"### {rel}\n\n(binary or non-UTF-8 file omitted)\n"

    rendered = [f"### {rel}", ""]
    for idx, line in enumerate(lines[:max_lines], start=1):
        rendered.append(f"{idx:>5}\t{line}")
    if len(lines) > max_lines:
        rendered.append(f"\n[truncated: {len(lines) - max_lines} additional lines]")
    rendered.append("")
    return "\n".join(rendered)


def default_diff_paths(
    kind: str, target: Path, context: list, root: Path
) -> list | None:
    """Default scope for embedded diffs.

    Broad (all tracked changes) for post-slice/post-phase; for everything
    else, restrict to the target document plus any context files.
    """
    if kind in ("post-slice", "post-phase"):
        return None
    paths = [rel_or_abs(target, root)]
    for c in context:
        paths.append(rel_or_abs(c, root))
    return paths


def build_incremental_preamble(
    *,
    manifest: dict,
    chain_dir: Path,
    round_num: int,
    resolution_waiver: bool,
    legacy_first_round: bool,
    diff_section: str = "",
) -> str:
    chain = manifest.get("chain", "<unknown chain>")
    prior_rounds = manifest.get("rounds", [])
    summary_rows = ["| round | verdict | findings | blocking |", "|---|---|---|---|"]
    for r in prior_rounds:
        summary_rows.append(
            f"| {r['round']} | {r.get('merged_verdict') or r.get('verdict')} "
            f"| {r.get('findings_count')} | {r.get('blocking_findings_count')} |"
        )

    # Walk backward to the last round whose process status is "ok".
    # Skip rounds with status "failed" (process error, body is stderr-echo)
    # or "unknown" (legacy entries, untrusted by default).
    skipped_rounds: list[int] = []
    trusted = None
    for r in reversed(prior_rounds):
        if r.get("status") == "ok":
            trusted = r
            break
        skipped_rounds.append(r["round"])
    skipped_rounds.reverse()

    prior_response_text = ""
    if trusted is not None:
        merged_findings_file = chain_dir / f"r{trusted['round']}-merged-findings.md"
        if merged_findings_file.exists():
            prior_response_text = merged_findings_file.read_text(encoding="utf-8")
            prior_source = f"merged findings from r{trusted['round']} (authoritative)"
        elif trusted.get("response"):
            response_path = chain_dir / trusted["response"]
            if response_path.exists():
                prior_response_text = response_path.read_text(encoding="utf-8")
                prior_source = f"primary reviewer response from r{trusted['round']}"
            else:
                prior_source = f"r{trusted['round']} response file missing"
        else:
            prior_source = f"r{trusted['round']} has no response on record"
    else:
        prior_source = "no successful prior round; no prior review available"

    if skipped_rounds:
        skip_lo = skipped_rounds[0]
        skip_hi = skipped_rounds[-1]
        if skip_lo == skip_hi:
            skip_note = (
                f"\nNote: round {skip_lo} was a process failure or pre-S1 entry; skipped.\n"
            )
        else:
            skip_note = (
                f"\nNote: rounds {skip_lo}..{skip_hi} were process failures or "
                f"pre-S1 entries; skipped.\n"
            )
        prior_response_text = skip_note + prior_response_text

    resolution_file = chain_dir / f"r{round_num - 1}-resolution.md"
    if resolution_file.exists():
        resolution_text = resolution_file.read_text(encoding="utf-8")
    elif resolution_waiver:
        resolution_text = "MISSING — explicitly waived by caller via --allow-missing-resolution"
    elif legacy_first_round:
        resolution_text = (
            "MISSING — chain migrated from legacy artifacts; please verify whether "
            "changes occurred from the diff below."
        )
    else:
        resolution_text = "MISSING — please verify whether changes occurred."

    return f"""You are continuing an existing review chain. This is round {round_num} of {chain}.

In incremental mode:
- Verify whether prior findings are resolved per the resolution report below.
- Reuse the existing finding IDs (F1, F2, …). If a prior finding is resolved,
  mark it RESOLVED in your findings list with its original ID. If still
  unresolved, keep its ID.
- Only introduce new finding IDs for genuine regressions caused by the fix, or
  blocking issues clearly missed in earlier rounds. Do not reopen broad review
  unless prior fixes changed broad architecture.

## Review chain summary

{chr(10).join(summary_rows)}

## Prior-round findings

Source: {prior_source}

{prior_response_text}

## Resolution report for prior round

{resolution_text}

## Changes since prior round

{diff_section or 'Changes since prior round: not available for this round.'}
"""


def make_prompt(
    *,
    root: Path,
    target: Path,
    kind: str,
    context: list[Path],
    max_lines: int,
    mode: str = "broad",
    incremental_preamble: str | None = None,
) -> str:
    context_display = "\n".join(f"- {rel_or_abs(p, root)}" for p in context) or "- none"
    body = REVIEW_PROMPT.format(
        repo_root=root,
        kind=kind,
        mode_guidance=MODE_GUIDANCE[kind],
        target_file=rel_or_abs(target, root),
        context_files=context_display,
    )
    if mode == "incremental" and incremental_preamble:
        body = incremental_preamble + "\n---\n\n" + body
    body += "\n\n## Target Preview\n\n"
    body += numbered_preview(target, root, max_lines=max_lines)
    if context:
        body += "\n## Context Previews\n\n"
        for ctx in context:
            body += numbered_preview(ctx, root, max_lines=max(80, max_lines // 3))
    return f"{PROMPT_SENTINEL_START}\n{body}\n{PROMPT_SENTINEL_END}"


def expand_command_template(
    template: str,
    *,
    prompt_file: Path,
    prompt_text: str,
    target_file: Path,
    kind: str,
    chain_dir: Path,
    round_num: int,
    previous_response: Path | None,
    resolution_file: Path | None,
    session_file: Path,
) -> str:
    values = {
        "prompt_file": shlex.quote(str(prompt_file)),
        "prompt_text": shlex.quote(prompt_text),
        "target_file": shlex.quote(str(target_file)),
        "kind": shlex.quote(kind),
        "chain_dir": shlex.quote(str(chain_dir)),
        "round": str(round_num),
        "previous_response": shlex.quote(str(previous_response)) if previous_response else "",
        "resolution_file": shlex.quote(str(resolution_file)) if resolution_file else "",
        "session_file": shlex.quote(str(session_file)),
    }
    return template.format(**values)


def run_reviewer(
    *,
    command_template: str,
    prompt_file: Path,
    prompt_text: str,
    target_file: Path,
    kind: str,
    prompt_transport: str,
    timeout: int,
    chain_dir: Path,
    round_num: int,
    previous_response: Path | None,
    resolution_file: Path | None,
    session_file: Path,
) -> subprocess.CompletedProcess[str]:
    if "{" in command_template and "}" in command_template:
        command = expand_command_template(
            command_template,
            prompt_file=prompt_file,
            prompt_text=prompt_text,
            target_file=target_file,
            kind=kind,
            chain_dir=chain_dir,
            round_num=round_num,
            previous_response=previous_response,
            resolution_file=resolution_file,
            session_file=session_file,
        )
        return subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        )

    argv = shlex.split(command_template)
    stdin_text = None
    if prompt_transport == "arg":
        argv.append(prompt_text)
    elif prompt_transport == "file":
        argv.append(str(prompt_file))
    elif prompt_transport == "stdin":
        stdin_text = prompt_text
    else:
        raise ValueError(f"unknown prompt transport: {prompt_transport}")

    return subprocess.run(
        argv,
        input=stdin_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def write_review_artifact(
    *,
    root: Path,
    target: Path,
    kind: str,
    command_template: str,
    prompt_file: Path,
    response_file: Path,
    round_num: int,
    result: subprocess.CompletedProcess[str],
) -> Path:
    # Sentinel-strip both streams in full BEFORE any size cap or tail operation.
    stdout = strip_prompt_echo(result.stdout or "").strip()
    stderr = strip_prompt_echo(result.stderr or "").strip()
    ok = result.returncode == 0
    status = "ok" if ok else f"failed ({result.returncode})"

    content = [
        f"# Review — {target.name} ({kind}, round {round_num})",
        "",
        f"- Target: `{rel_or_abs(target, root)}`",
        f"- Request: `{rel_or_abs(prompt_file, root)}`",
        f"- Reviewer command: `{command_template}`",
        f"- Status: `{status}`",
        "",
        "---",
        "",
    ]

    if ok:
        content.append(stdout or "_Reviewer produced no stdout._")
        content.append("")
        if stderr:
            # Capped tail of sanitised stderr — diagnostic only.
            tail = stderr[-2048:]
            content.extend([
                "---", "", "## Reviewer stderr (tail)", "",
                "```text", tail, "```", "",
            ])
    else:
        # Failed: no stdout body, only a short sanitised stderr tail.
        tail = stderr[-4096:] if stderr else ""
        content.extend([
            "_Reviewer process failed; no stdout persisted._",
            "",
            "---", "", "## Reviewer stderr (tail, sanitised)", "",
            "```text", tail or "(no stderr captured)", "```", "",
        ])

    response_file.write_text("\n".join(content), encoding="utf-8")
    return response_file


def resolve_mode(mode: str, *, round_num: int) -> str:
    if mode == "incremental" and round_num == 1:
        raise ValueError("--mode incremental is not valid on round 1")
    if mode == "auto":
        return "broad" if round_num == 1 else "incremental"
    return mode


@dataclass
class SweepPlan:
    sweep_count: int
    checkpoint: str | None  # "first-round" | "final-ready" | None


@dataclass
class ReviewerResult:
    role: str            # "primary" | "sweep"
    sweep_index: int | None
    request_path: Path
    response_path: Path
    review_body: str
    verdict: str | None
    verdict_valid: bool
    returncode: int


def run_one_reviewer(
    *,
    role: str,
    sweep_index: int | None,
    chain_dir: Path,
    round_num: int,
    timestamp: str,
    prompt_text: str,
    args,
    target: Path,
    root: Path,
    namespaced: bool,
    previous_response: Path | None = None,
    resolution_file: Path | None = None,
) -> ReviewerResult:
    suffix = ""
    if namespaced:
        suffix = "-primary" if role == "primary" else f"-sweep{sweep_index}"
    basename = f"r{round_num}-{timestamp}{suffix}"
    request_path = chain_dir / f"{basename}-request.md"
    response_path = chain_dir / f"{basename}-response.md"
    request_path.write_text(prompt_text, encoding="utf-8")
    session_file = chain_dir / (
        "session.state" if role == "primary" else f"sweep{sweep_index}.session.state"
    )

    result = run_reviewer(
        command_template=args.reviewer_cmd,
        prompt_file=request_path, prompt_text=prompt_text,
        target_file=target, kind=args.kind,
        prompt_transport=args.prompt_transport, timeout=args.timeout,
        chain_dir=chain_dir, round_num=round_num,
        previous_response=previous_response, resolution_file=resolution_file,
        session_file=session_file,
    )
    write_review_artifact(
        root=root, target=target, kind=args.kind,
        command_template=args.reviewer_cmd,
        prompt_file=request_path, response_file=response_path,
        round_num=round_num, result=result,
    )
    body = response_path.read_text(encoding="utf-8")
    if result.returncode != 0:
        # Process failures cannot produce a valid verdict, regardless of what
        # parse_verdict extracts from echoed prompt text. See spec §S1.2.
        verdict, valid = None, False
    else:
        verdict, valid = parse_verdict(body)
    return ReviewerResult(
        role=role, sweep_index=sweep_index,
        request_path=request_path, response_path=response_path,
        review_body=body, verdict=verdict, verdict_valid=valid,
        returncode=result.returncode,
    )


def compute_merged_verdict(reviewer_results: list) -> str | None:
    """Merge per-reviewer verdicts per spec §S1.7.

    - If the primary reviewer failed (returncode != 0), return None: the round
      as a whole has no trustworthy verdict and the top-level status will be
      `failed`.
    - Otherwise, aggregate only the reviewers whose process succeeded.
    - Among the successful reviewers: any `revise` (or invalid verdict text)
      → revise; any `ready with small edits` → that; all `ready` → ready.
    """
    primary = next((r for r in reviewer_results if r.role == "primary"), None)
    if primary is not None and primary.returncode != 0:
        return None
    ok = [r for r in reviewer_results if r.returncode == 0]
    if not ok:
        return None
    if any((not r.verdict_valid) or r.verdict == "revise" for r in ok):
        return "revise"
    if any(r.verdict == "ready with small edits" for r in ok):
        return "ready with small edits"
    if all(r.verdict == "ready" for r in ok):
        return "ready"
    return None


def _renamespace_finding_ids(body: str, sweep_index: int) -> str:
    """Rewrite bare F<n> identifiers to S{k}.F<n>, leaving already-prefixed IDs alone."""
    return re.sub(r"(?<![.\w])F(\d+)\b", rf"S{sweep_index}.F\1", body)


def write_merged_findings(
    *,
    chain_dir: Path, round_num: int,
    primary: "ReviewerResult", sweeps: list,
) -> Path | None:
    """Concatenate successful reviewer bodies into a merged-findings artifact.

    Reviewers with non-zero returncode are excluded entirely — their bodies
    are stderr tails / failure stubs and would poison downstream parsing.
    If every reviewer in the round failed, return None and write no file.
    """
    ok_reviewers = [r for r in [primary, *sweeps] if r.returncode == 0]
    if not ok_reviewers:
        return None
    parts = [f"# Merged findings for r{round_num}\n"]
    primary_ok = next((r for r in ok_reviewers if r.role == "primary"), None)
    if primary_ok is not None:
        parts += ["## Primary\n", primary_ok.review_body, ""]
    for s in ok_reviewers:
        if s.role == "sweep":
            parts += [
                f"## Sweep {s.sweep_index}\n",
                _renamespace_finding_ids(s.review_body, s.sweep_index),
                "",
            ]
    path = chain_dir / f"r{round_num}-merged-findings.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


DEPTH_DEFAULTS = {
    "standard":   {"policy": "never",       "count_first": 0, "count_final": 0},
    "thorough":   {"policy": "both",        "count_first": 1, "count_final": 1},
    "exhaustive": {"policy": "both",        "count_first": 2, "count_final": 2},
}


def plan_sweeps(
    *,
    depth: str,
    policy: str | None,
    count: int | None,
    round_num: int,
    checkpoints: dict,
    primary_verdict_pre_run: str | None,
) -> SweepPlan:
    cfg = DEPTH_DEFAULTS[depth]
    effective_policy = policy or cfg["policy"]
    if effective_policy == "never":
        return SweepPlan(sweep_count=0, checkpoint=None)

    if round_num == 1 and effective_policy in ("first-round", "both"):
        if checkpoints.get("first-round") == "completed":
            return SweepPlan(sweep_count=0, checkpoint=None)
        n = count if count is not None else cfg["count_first"]
        return SweepPlan(sweep_count=n, checkpoint="first-round")

    if (
        round_num > 1
        and effective_policy in ("final-ready", "both")
        and primary_verdict_pre_run in ("ready", "ready with small edits")
        and checkpoints.get("final-ready") != "completed"
    ):
        n = count if count is not None else cfg["count_final"]
        return SweepPlan(sweep_count=n, checkpoint="final-ready")

    return SweepPlan(sweep_count=0, checkpoint=None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a document to the configured reviewer.")
    parser.add_argument("command", choices=["review"])
    parser.add_argument("--file", required=True, help="Target spec/plan/document to review.")
    parser.add_argument(
        "--kind",
        required=True,
        choices=["spec", "plan", "design", "implementation", "post-slice", "post-phase", "other"],
        help="Review type, used in prompt and artifact name.",
    )
    parser.add_argument(
        "--context",
        action="append",
        default=[],
        help="Additional context file. May be supplied multiple times.",
    )
    parser.add_argument(
        "--reviewer-cmd",
        default=os.environ.get("AGENT_REVIEWER_CMD", "reviewer-agent"),
        help="Command or template. Supports {prompt_file}, {prompt_text}, {target_file}, {kind}, {chain_dir}, {round}, {previous_response}, {resolution_file}, {session_file}.",
    )
    parser.add_argument(
        "--prompt-transport",
        choices=["arg", "file", "stdin"],
        default=os.environ.get("AGENT_REVIEWER_TRANSPORT"),
        help="How to pass the prompt when reviewer-cmd has no placeholders. "
             "If unset, defaults to 'arg' on round 1 / broad mode and 'stdin' on "
             "incremental rounds (round 2+) to avoid ARG_MAX overflow.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/reviewer",
        help="Root directory for review chain folders.",
    )
    parser.add_argument(
        "--work-id",
        default=None,
        help="Stable slice/phase ID (e.g. P2.S3 or P2). Required for post-slice/post-phase.",
    )
    parser.add_argument(
        "--allow-missing-resolution",
        action="store_true",
        help="Waive the resolution-required gate for post-slice/post-phase round 2+.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "broad", "incremental"],
        default="auto",
        help="Override the round-1-vs-N prompt mode. Default 'auto'.",
    )
    parser.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
                        default="standard")
    parser.add_argument("--independent-reviewers", type=int, default=None)
    parser.add_argument("--sweep-policy",
                        choices=["first-round", "final-ready", "both", "never"], default=None)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-lines", type=int, default=600)
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Override auto-computed diff base for this round.",
    )
    parser.add_argument(
        "--no-diff",
        action="store_true",
        help="Suppress diff embedding in incremental rounds.",
    )
    parser.add_argument(
        "--changed-files",
        nargs="+",
        default=None,
        help="Limit embedded diff to these paths (overrides auto discovery).",
    )
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=2000,
        help="Cap diff size. Truncation marker is embedded if exceeded.",
    )
    parser.add_argument(
        "--emit",
        choices=["paths", "review", "json"],
        default="paths",
        help="What to print to stdout after the reviewer finishes.",
    )
    return parser.parse_args()


def current_head_sha(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True, capture_output=True, check=True,
        )
        return out.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def is_dirty(root: Path) -> bool:
    out = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        text=True, capture_output=True,
    )
    return bool(out.stdout.strip())


def _cap_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines] + [f"[truncated: {len(lines) - max_lines} additional lines]"])


def compute_diff_section(
    root: Path,
    *,
    base_ref: str | None,
    paths: list[str] | None,
    max_lines: int,
) -> str:
    if base_ref is None:
        return "Changes since prior round: not available for this round (no base ref).\n"

    diff_args = ["git", "-C", str(root), "diff", f"{base_ref}..HEAD"]
    if paths:
        diff_args.append("--")
        diff_args.extend(paths)
    diff_proc = subprocess.run(diff_args, text=True, capture_output=True)
    diff_text = diff_proc.stdout

    status_args = ["git", "-C", str(root), "status", "--porcelain"]
    if paths:
        status_args.append("--")
        status_args.extend(paths)
    status = subprocess.run(status_args, text=True, capture_output=True).stdout
    dirty = bool(status.strip())

    parts = [f"Worktree status: {'dirty' if dirty else 'clean'}", "", "## git diff base..HEAD", ""]
    parts.append(_cap_lines(diff_text, max_lines))

    if dirty:
        head_diff = subprocess.run(
            ["git", "-C", str(root), "diff", "HEAD"] + (["--"] + paths if paths else []),
            text=True, capture_output=True,
        ).stdout
        parts += ["", "## git diff HEAD (uncommitted)", "", _cap_lines(head_diff, max_lines)]

    untracked = [line[3:] for line in status.splitlines() if line.startswith("?? ")]
    if untracked:
        parts += ["", "## Untracked files", ""]
        for rel in untracked:
            abs_path = root / rel
            try:
                content = abs_path.read_text(encoding="utf-8")
                preview = _cap_lines(content, max_lines)
                parts += [f"### {rel}", "", "```", preview, "```", ""]
            except (UnicodeDecodeError, OSError):
                parts += [f"- {rel} (omitted: binary or unreadable)"]

    return "\n".join(parts) + "\n"


def main() -> int:
    args = parse_args()
    if args.kind in ("post-slice", "post-phase") and not args.work_id:
        print(
            f"ERROR: --work-id is required for --kind {args.kind}. "
            "Use the slice ID (e.g. P2.S3) or phase ID (e.g. P2).",
            file=sys.stderr,
        )
        return 2
    root = repo_root()
    target = (root / args.file).resolve() if not Path(args.file).is_absolute() else Path(args.file).resolve()
    if not target.exists():
        print(f"ERROR: target file not found: {target}", file=sys.stderr)
        return 2

    context: list[Path] = []
    for raw in args.context:
        path = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not path.exists():
            print(f"ERROR: context file not found: {path}", file=sys.stderr)
            return 2
        context.append(path)

    new_slug = chain_folder_name(target, args.kind, args.work_id)
    reviewer_root = (root / args.output_dir).resolve()
    try:
        existing = discover_legacy_chain(
            reviewer_root=reviewer_root,
            target_stem=DATE_PREFIX_RE.sub("", target.stem),
            kind=args.kind,
            new_slug=new_slug,
        )
    except AmbiguousLegacyChain as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 5
    chain_dir = existing if existing else (reviewer_root / new_slug)
    chain_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = chain_dir / "chain.json"
    try:
        manifest = read_manifest(manifest_path)
    except ManifestSchemaTooNew as exc:
        print(
            f"ERROR: {rel_or_abs(manifest_path, root)}: {exc} "
            f"(supported schema_version: {SUPPORTED_SCHEMA_VERSION})",
            file=sys.stderr,
        )
        return 4
    if manifest is not None:
        migrate_manifest_inplace(manifest)
    if manifest is None and any(chain_dir.glob("r*-*-request.md")):
        manifest = synthesize_legacy_manifest(
            chain_dir=chain_dir,
            chain=chain_dir.name,
            kind=args.kind,
            target=rel_or_abs(target, root),
            work_id=args.work_id,
        )
        migrate_manifest_inplace(manifest)
        write_manifest(manifest_path, manifest)
    if manifest is None:
        manifest = {
            "schema_version": SUPPORTED_SCHEMA_VERSION,
            "chain": new_slug,
            "kind": args.kind,
            "target": rel_or_abs(target, root),
            "work_id": args.work_id,
            "legacy_migrated": False,
            "rounds": [],
            "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
        }
    else:
        # Existing manifest: refuse a work-id mismatch (someone trying to reuse a
        # chain folder for a different slice/phase). Stored work_id is the source
        # of truth; do not mutate it. Allow when stored work_id is None (legacy
        # synthesis path may have set it, or older manifests had None).
        stored_work_id = manifest.get("work_id")
        if (
            args.work_id is not None
            and stored_work_id is not None
            and stored_work_id != args.work_id
        ):
            print(
                f"ERROR: --work-id {args.work_id!r} does not match the stored "
                f"work_id {stored_work_id!r} in {rel_or_abs(manifest_path, root)}. "
                "Refusing to reuse this chain folder for a different slice/phase.",
                file=sys.stderr,
            )
            return 6
        # If the stored value is None and a CLI value was provided, backfill it.
        if stored_work_id is None and args.work_id is not None:
            manifest["work_id"] = args.work_id

    if (
        args.kind in ("post-slice", "post-phase")
        and manifest["rounds"]
        and not args.allow_missing_resolution
    ):
        prior = manifest["rounds"][-1]
        prior_round = prior["round"]
        prior_verdict = prior.get("merged_verdict") or prior.get("verdict")
        prior_valid = prior.get("verdict_valid", True)
        prior_status = prior.get("status")  # "ok" | "failed" | "unknown" | None
        prior_was_process_failure = prior_status == "failed"
        needs_resolution = (
            (prior_verdict == "revise") or (prior_valid is False)
        ) and not prior_was_process_failure
        if prior_was_process_failure:
            print(
                f"Note: prior round r{prior_round} was a process failure "
                f"(returncode={prior.get('returncode')}); "
                "resolution gate bypassed.",
                file=sys.stderr,
            )
        if needs_resolution:
            resolution_path = chain_dir / f"r{prior_round}-resolution.md"
            if not resolution_path.exists():
                rel = rel_or_abs(resolution_path, root)
                response_rel = (
                    rel_or_abs(chain_dir / prior["response"], root)
                    if prior.get("response")
                    else "<missing>"
                )
                print(
                    f"ERROR: Previous {args.kind} round returned revise, but {rel} is missing.\n\n"
                    f"Dispatch a fixer subagent with:\n"
                    f"  - previous response: {response_rel}\n"
                    f"  - required output:   {rel}\n\n"
                    f"Then re-run this review.\n"
                    f"Use --allow-missing-resolution only if you intentionally fixed outside the standard workflow.",
                    file=sys.stderr,
                )
                return 3

    round_num = next_round_number(chain_dir)
    timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")

    resolution_file = chain_dir / f"r{round_num - 1}-resolution.md"
    resolution_attached = resolution_file.name if (round_num > 1 and resolution_file.exists()) else None

    resolution_waiver = bool(
        args.allow_missing_resolution and round_num > 1 and not resolution_attached
    )

    mode = resolve_mode(args.mode, round_num=round_num)
    if args.prompt_transport is None:
        args.prompt_transport = "stdin" if mode == "incremental" else "arg"
    diff_section = ""
    base_ref: str | None = None
    base_source: str | None = None
    if mode == "incremental":
        if args.no_diff:
            diff_section = "Changes since prior round: diff suppressed via --no-diff.\n"
            base_ref = None
            base_source = "suppressed"
        else:
            if args.base_ref:
                base_ref = args.base_ref
                base_source = "explicit"
            else:
                prior_with_sha = next(
                    (r for r in reversed(manifest["rounds"]) if r.get("head_sha_after_round")),
                    None,
                )
                base_ref = prior_with_sha["head_sha_after_round"] if prior_with_sha else None
                base_source = "auto" if base_ref else "unavailable"
            paths = args.changed_files or default_diff_paths(args.kind, target, context, root)
            diff_section = compute_diff_section(
                root, base_ref=base_ref, paths=paths, max_lines=args.max_diff_lines,
            )

    incremental_preamble = None
    if mode == "incremental":
        incremental_preamble = build_incremental_preamble(
            manifest=manifest,
            chain_dir=chain_dir,
            round_num=round_num,
            resolution_waiver=resolution_waiver,
            legacy_first_round=(
                manifest.get("legacy_migrated", False)
                and not any(r.get("head_sha_after_round") for r in manifest["rounds"])
            ),
            diff_section=diff_section,
        )

    prompt_text = make_prompt(
        root=root, target=target, kind=args.kind,
        context=context, max_lines=args.max_lines,
        mode=mode, incremental_preamble=incremental_preamble,
    )

    head_sha_at_request = current_head_sha(root)
    worktree_dirty_at_request = is_dirty(root)

    # Plan sweep dispatch. `first-round` policy depends only on round_num /
    # checkpoint state; `final-ready` requires the CURRENT primary's verdict,
    # so we plan it AFTER the primary runs.
    checkpoints = manifest.setdefault(
        "sweep_checkpoints", {"first-round": "pending", "final-ready": "pending"}
    )
    # Pre-run plan: covers first-round only (passes None for primary verdict so
    # final-ready can never fire here).
    pre_sweep_plan = plan_sweeps(
        depth=args.review_depth,
        policy=args.sweep_policy,
        count=args.independent_reviewers,
        round_num=round_num,
        checkpoints=checkpoints,
        primary_verdict_pre_run=None,
    )
    namespaced = pre_sweep_plan.sweep_count > 0

    # Prior-round artefacts for primary template anchoring (round N+1, S6 contract).
    # Sweeps remain isolated and continue to receive None.
    previous_response_path: Path | None = None
    resolution_for_template: Path | None = None
    if round_num > 1 and manifest["rounds"]:
        prior_round_entry = manifest["rounds"][-1]
        prior_response_name = prior_round_entry.get("response")
        if prior_response_name:
            candidate = chain_dir / prior_response_name
            if candidate.exists():
                previous_response_path = candidate
        if resolution_attached:
            resolution_for_template = resolution_file

    try:
        primary = run_one_reviewer(
            role="primary", sweep_index=None,
            chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
            prompt_text=prompt_text, args=args, target=target, root=root,
            namespaced=namespaced,
            previous_response=previous_response_path,
            resolution_file=resolution_for_template,
        )

        # Post-run plan: now that primary has a verdict, evaluate final-ready.
        sweep_plan = plan_sweeps(
            depth=args.review_depth,
            policy=args.sweep_policy,
            count=args.independent_reviewers,
            round_num=round_num,
            checkpoints=checkpoints,
            primary_verdict_pre_run=primary.verdict,
        )

        # If final-ready fires but we ran primary without namespacing, rename
        # primary artefacts to add the `-primary` suffix.
        if sweep_plan.sweep_count > 0 and not namespaced:
            new_suffix = "-primary"
            new_basename = f"r{round_num}-{timestamp}{new_suffix}"
            new_request = chain_dir / f"{new_basename}-request.md"
            new_response = chain_dir / f"{new_basename}-response.md"
            primary.request_path.rename(new_request)
            primary.response_path.rename(new_response)
            primary = ReviewerResult(
                role=primary.role, sweep_index=primary.sweep_index,
                request_path=new_request, response_path=new_response,
                review_body=primary.review_body, verdict=primary.verdict,
                verdict_valid=primary.verdict_valid, returncode=primary.returncode,
            )
            namespaced = True

        sweeps: list = []
        for k in range(1, sweep_plan.sweep_count + 1):
            sweep_prompt = prompt_text
            if sweep_plan.checkpoint == "final-ready":
                sweep_prompt = make_prompt(
                    root=root, target=target, kind=args.kind,
                    context=context, max_lines=args.max_lines,
                    mode="broad", incremental_preamble=None,
                )
            sweeps.append(run_one_reviewer(
                role="sweep", sweep_index=k,
                chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
                prompt_text=sweep_prompt, args=args, target=target, root=root,
                namespaced=True,
            ))
    except FileNotFoundError as exc:
        print(f"ERROR: reviewer command not found: {exc}", file=sys.stderr)
        print("Set AGENT_REVIEWER_CMD, e.g. AGENT_REVIEWER_CMD='reviewer {prompt_file}'", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"ERROR: reviewer command timed out after {args.timeout}s", file=sys.stderr)
        return 124

    reviewer_results = [primary] + sweeps
    if sweeps:
        merged_path = write_merged_findings(
            chain_dir=chain_dir, round_num=round_num,
            primary=primary, sweeps=sweeps,
        )
        # merged_path may be None if every reviewer in the round failed.
        merged_verdict = compute_merged_verdict(reviewer_results)
        if sweep_plan.checkpoint:
            manifest["sweep_checkpoints"][sweep_plan.checkpoint] = "completed"
    else:
        merged_path = None
        merged_verdict = primary.verdict if primary.returncode == 0 else None

    findings_count, blocking_count = parse_findings(primary.review_body)

    head_sha_after_round = current_head_sha(root)
    resolution_parse = None
    if resolution_attached:
        parsed = parse_resolution(resolution_file.read_text(encoding="utf-8"))
        resolution_parse = parsed.status
    # Persist work_id on first creation / backfill.
    manifest["work_id"] = args.work_id or manifest.get("work_id")
    round_entry = {
        "round": round_num,
        "reviewers": [
            {
                "role": r.role,
                "sweep_group": r.sweep_index,
                "parent_round": round_num,
                "request": r.request_path.name,
                "response": r.response_path.name,
                "verdict": r.verdict,
                "verdict_valid": r.verdict_valid,
                "returncode": r.returncode,
                "status": "ok" if r.returncode == 0 else "failed",
            }
            for r in reviewer_results
        ],
        "status": "ok" if primary.returncode == 0 else "failed",
        "returncode": primary.returncode,
        "merged_verdict": merged_verdict,
        "merged_findings": merged_path.name if merged_path else None,
        "request": primary.request_path.name,
        "response": primary.response_path.name,
        "resolution": resolution_attached,
        "resolution_parse_status": resolution_parse,
        "resolution_waiver": resolution_waiver,
        "head_sha_at_request": head_sha_at_request,
        "head_sha_after_round": head_sha_after_round,
        "worktree_dirty_at_request": worktree_dirty_at_request,
        "verdict": primary.verdict,
        "verdict_valid": primary.verdict_valid,
        "findings_count": findings_count,
        "blocking_findings_count": blocking_count,
        "base_ref": base_ref,
        "base_ref_source": base_source,
        "diff_included": base_source in ("auto", "explicit") and not args.no_diff and bool(diff_section),
    }
    manifest["rounds"].append(round_entry)
    write_manifest(manifest_path, manifest)

    review_rel = rel_or_abs(primary.response_path, root)
    prompt_rel = rel_or_abs(primary.request_path, root)
    if args.emit == "paths":
        print(f"REVIEW_PATH={review_rel}")
        print(f"PROMPT_PATH={prompt_rel}")
        print(f"ROUND={round_num}")
    elif args.emit == "review":
        print(primary.review_body)
    elif args.emit == "json":
        merged_findings_text = merged_path.read_text(encoding="utf-8") if merged_path else None
        top_review = merged_findings_text or primary.review_body
        print(json.dumps({
            "review_path": review_rel,
            "prompt_path": prompt_rel,
            "chain": manifest["chain"],
            "round": round_num,
            "kind": args.kind,
            "work_id": manifest.get("work_id"),
            "status": "ok" if primary.returncode == 0 else "failed",
            "returncode": primary.returncode,
            "verdict": merged_verdict if merged_verdict is not None else primary.verdict,
            "verdict_valid": primary.verdict_valid,
            "findings_count": findings_count,
            "blocking_findings_count": blocking_count,
            "resolution_parse_status": resolution_parse,
            "resolution_waiver": resolution_waiver,
            "diff_included": round_entry["diff_included"],
            "base_ref": base_ref,
            "worktree_dirty_at_request": round_entry["worktree_dirty_at_request"],
            "review_depth": args.review_depth,
            "reviewers": [
                {
                    "role": r.role,
                    "verdict": r.verdict,
                    "verdict_valid": r.verdict_valid,
                    "review_path": rel_or_abs(r.response_path, root),
                    "review": r.review_body,
                    "returncode": r.returncode,
                    "status": "ok" if r.returncode == 0 else "failed",
                }
                for r in reviewer_results
            ],
            "merged_verdict": merged_verdict,
            "merged_findings_path": rel_or_abs(merged_path, root) if merged_path else None,
            "merged_findings": merged_findings_text,
            "review": top_review,
        }, indent=2))
    return primary.returncode


VERDICT_VALUES = ("ready with small edits", "ready", "revise")
VERDICT_LINE_RE = re.compile(
    r"overall\s+verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*(ready with small edits|ready|revise)[`*_\"'.\s]*",
    re.IGNORECASE,
)


def parse_verdict(text: str) -> tuple[str | None, bool]:
    matches = list(VERDICT_LINE_RE.finditer(text))
    if not matches:
        return None, False
    raw = matches[-1].group(1).strip().lower()
    if raw not in VERDICT_VALUES:
        return None, False
    return raw, True


HEADING_FINDING_RE = re.compile(r"^##\s+F(\d+)\b(.*)$", re.MULTILINE)
# Prose findings: `F<n>` followed by one of `.`, `-`, `—`, `:` separators, then
# the heading content. The heading content may be wrapped in markdown bold
# (`**...**`) and an explicit severity word may or may not be present
# immediately after the separator. We capture the rest of the line so the
# caller can inspect the paragraph for a `Blocking` marker.
PROSE_FINDING_RE = re.compile(
    r"^F(\d+)\s*[.\-—:]\s+(.*)$",
    re.MULTILINE,
)
PROSE_SEVERITY_RE = re.compile(
    r"\b(Blocking|Important|Minor|Critical|Major|Nit)\b",
    re.IGNORECASE,
)
PROSE_BLOCKING_PARAGRAPH_RE = re.compile(r"\bBlocking\b", re.IGNORECASE)
BULLET_FINDING_RE = re.compile(r"^\s*[-*]\s*\**F(\d+)\**[:\s\-](.*)$", re.MULTILINE)
INLINE_BLOCKING_RE = re.compile(r"\(blocking\)", re.IGNORECASE)
SEVERITY_BLOCKING_RE = re.compile(r"^severity\s*:\s*blocking", re.IGNORECASE | re.MULTILINE)
CRASH_SENTINEL_RE = re.compile(
    r"^(?:reviewer crashed|status\s*:\s*reviewer crashed)",
    re.IGNORECASE | re.MULTILINE,
)
# Recognised "explicit empty findings" markers. A reviewer that clearly
# declares zero findings (e.g. "## Findings\nnone" or "Findings: none") is
# parseable as (0, 0); anything else with no F-IDs is unparseable -> (None, None).
EMPTY_FINDINGS_RE = re.compile(
    r"(?:^##\s*Findings\s*\n+\s*(?:none|no findings|n/?a)\b"
    r"|^findings\s*:\s*(?:none|no findings|n/?a|0|zero)\b)",
    re.IGNORECASE | re.MULTILINE,
)


def _collect_findings(text: str) -> tuple[dict[str, bool], str]:
    """Return ({id: blocking?}, style) for the first style that yields matches.

    Style precedence: prose ('F1. Blocking: ...') > heading ('## F1') > bullet.
    Prose wins when present because real reviewer output uses it and may also
    incidentally contain heading/bullet shapes inside embedded previews.
    """
    findings: dict[str, bool] = {}
    # Collect prose matches with their span so we can scope each finding's
    # paragraph (up to the next prose finding, or end of text).
    prose_matches = list(PROSE_FINDING_RE.finditer(text))
    for idx, m in enumerate(prose_matches):
        fid = m.group(1)
        rest = m.group(2) or ""
        # Strip optional markdown-bold wrapper so a leading `**` does not hide
        # the severity word from the inline-severity check.
        rest_stripped = rest.lstrip()
        if rest_stripped.startswith("**"):
            rest_stripped = rest_stripped[2:]
        inline_sev = PROSE_SEVERITY_RE.match(rest_stripped)
        if inline_sev:
            is_blocking = inline_sev.group(1).lower() == "blocking"
        else:
            # No inline severity — inspect the finding's immediate paragraph
            # for a `Blocking` token. The paragraph runs from the finding's
            # heading line up to the first blank line (markdown paragraph
            # break) or the next prose finding, whichever comes first. This
            # keeps us from sweeping in unrelated `blocking` mentions that
            # appear in quoted previews further down the response.
            next_finding_start = (
                prose_matches[idx + 1].start()
                if idx + 1 < len(prose_matches)
                else len(text)
            )
            blank_line = re.search(r"\n\s*\n", text[m.end():next_finding_start])
            if blank_line:
                para_end = m.end() + blank_line.start()
            else:
                para_end = next_finding_start
            paragraph = text[m.start():para_end]
            is_blocking = bool(PROSE_BLOCKING_PARAGRAPH_RE.search(paragraph))
        # First occurrence wins; later duplicates from echoed/quoted content
        # do not change the blocking flag.
        if fid not in findings:
            findings[fid] = is_blocking
    if findings:
        return findings, "prose"

    for m in HEADING_FINDING_RE.finditer(text):
        fid = m.group(1)
        if fid not in findings:
            findings[fid] = False
    if findings:
        return findings, "heading"

    for m in BULLET_FINDING_RE.finditer(text):
        fid = m.group(1)
        rest = m.group(2) or ""
        if fid not in findings:
            findings[fid] = bool(INLINE_BLOCKING_RE.search(rest))
    return findings, "bullet"


def parse_findings(text: str) -> tuple[int | None, int | None]:
    """Return (findings_count, blocking_findings_count) per spec.

    Per docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md
    (Finding-count parsing): if no accepted finding form matches AND no
    explicit-empty marker is present, both counts are ``None`` and the
    coordinator inspects prose. A crash sentinel also yields ``(None, None)``.
    """
    if not text or text.strip() == "":
        return None, None
    # Crash sentinel short-circuits before everything else.
    if CRASH_SENTINEL_RE.search(text):
        return None, None
    findings, style = _collect_findings(text)
    if findings:
        n = len(findings)
        blocking = sum(1 for v in findings.values() if v)
        if style == "heading":
            # Heading style has no severity inline; fall back to severity-line
            # markers within the body.
            blocking = len(SEVERITY_BLOCKING_RE.findall(text))
        return n, blocking
    # No finding form matched. Honor explicit "no findings" declarations as
    # (0, 0); otherwise the response is unparseable for finding-count purposes.
    if EMPTY_FINDINGS_RE.search(text):
        return 0, 0
    return None, None


LEGACY_ROUND_FILE_RE = re.compile(r"^r(\d+)-([0-9T\-]+)-(request|response)\.md$")


def synthesize_legacy_manifest(
    *, chain_dir: Path, chain: str, kind: str, target: str, work_id: str | None
) -> dict:
    rounds_map: dict[int, dict] = {}
    for path in sorted(chain_dir.iterdir()):
        m = LEGACY_ROUND_FILE_RE.match(path.name)
        if not m:
            continue
        round_num = int(m.group(1))
        role = m.group(3)
        entry = rounds_map.setdefault(
            round_num,
            {
                "round": round_num,
                "request": None,
                "response": None,
                "resolution": None,
                "verdict": None,
                "verdict_valid": False,
                "findings_count": None,
                "blocking_findings_count": None,
                "head_sha_at_request": None,
                "head_sha_after_round": None,
                "worktree_dirty_at_request": None,
                "legacy": True,
            },
        )
        entry[role] = path.name
        if role == "response":
            body = path.read_text(encoding="utf-8", errors="replace")
            v, valid = parse_verdict(body)
            entry["verdict"], entry["verdict_valid"] = v, valid
            n, blocking = parse_findings(body)
            entry["findings_count"], entry["blocking_findings_count"] = n, blocking

    return {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "chain": chain,
        "kind": kind,
        "target": target,
        "work_id": work_id,
        "legacy_migrated": True,
        "migrated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rounds": [rounds_map[k] for k in sorted(rounds_map)],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }


class ResolutionParseResult:
    """Result of parsing a resolution doc. status is one of ok|partial|unparseable."""

    __slots__ = ("status", "findings", "unmatched")

    def __init__(self, status: str, findings: dict | None = None, unmatched: list | None = None):
        self.status = status
        self.findings = findings if findings is not None else {}
        self.unmatched = unmatched if unmatched is not None else []

    def __repr__(self) -> str:
        return (
            f"ResolutionParseResult(status={self.status!r}, "
            f"findings={self.findings!r}, unmatched={self.unmatched!r})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, ResolutionParseResult):
            return NotImplemented
        return (
            self.status == other.status
            and self.findings == other.findings
            and self.unmatched == other.unmatched
        )


RESOLUTION_HEADING_RE = re.compile(r"^##\s+(F\d+)\b", re.MULTILINE)
RESOLUTION_STATUS_RE = re.compile(
    r"^\s*status\s*:\s*(fixed|waived|deferred)\b", re.IGNORECASE | re.MULTILINE
)


def parse_resolution(text: str) -> ResolutionParseResult:
    headings = list(RESOLUTION_HEADING_RE.finditer(text))
    if not headings:
        return ResolutionParseResult(status="unparseable")

    findings: dict = {}
    unmatched: list = []
    spans = []
    for i, m in enumerate(headings):
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        spans.append((m.group(1), text[start:end]))

    for fid, body in spans:
        sm = RESOLUTION_STATUS_RE.search(body)
        if sm:
            findings[fid] = sm.group(1).lower()
        else:
            unmatched.append(fid)

    status = "ok" if not unmatched else "partial"
    return ResolutionParseResult(status=status, findings=findings, unmatched=unmatched)


if __name__ == "__main__":
    raise SystemExit(main())
