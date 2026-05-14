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
from pathlib import Path


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


def make_prompt(
    *,
    root: Path,
    target: Path,
    kind: str,
    context: list[Path],
    max_lines: int,
) -> str:
    context_display = "\n".join(f"- {rel_or_abs(p, root)}" for p in context) or "- none"
    body = REVIEW_PROMPT.format(
        repo_root=root,
        kind=kind,
        mode_guidance=MODE_GUIDANCE[kind],
        target_file=rel_or_abs(target, root),
        context_files=context_display,
    )
    body += "\n\n## Target Preview\n\n"
    body += numbered_preview(target, root, max_lines=max_lines)
    if context:
        body += "\n## Context Previews\n\n"
        for ctx in context:
            body += numbered_preview(ctx, root, max_lines=max(80, max_lines // 3))
    return body


def run_reviewer(
    *,
    command_template: str,
    prompt_file: Path,
    prompt_text: str,
    target_file: Path,
    kind: str,
    prompt_transport: str,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    values = {
        "prompt_file": shlex.quote(str(prompt_file)),
        "target_file": shlex.quote(str(target_file)),
        "kind": shlex.quote(kind),
        "prompt_text": shlex.quote(prompt_text),
    }

    if "{" in command_template and "}" in command_template:
        command = command_template.format(**values)
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
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    status = "ok" if result.returncode == 0 else f"failed ({result.returncode})"

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
        stdout or "_Reviewer produced no stdout._",
        "",
    ]
    if stderr:
        content.extend(["---", "", "## Reviewer stderr", "", "```text", stderr, "```", ""])

    response_file.write_text("\n".join(content), encoding="utf-8")
    return response_file


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
        help="Command or template. Supports {prompt_file}, {prompt_text}, {target_file}, {kind}.",
    )
    parser.add_argument(
        "--prompt-transport",
        choices=["arg", "file", "stdin"],
        default=os.environ.get("AGENT_REVIEWER_TRANSPORT", "arg"),
        help="How to pass the prompt when reviewer-cmd has no placeholders.",
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
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-lines", type=int, default=600)
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
    manifest = read_manifest(manifest_path)
    if manifest is None and any(chain_dir.glob("r*-*-request.md")):
        manifest = synthesize_legacy_manifest(
            chain_dir=chain_dir,
            chain=chain_dir.name,
            kind=args.kind,
            target=rel_or_abs(target, root),
            work_id=args.work_id,
        )
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
    round_num = next_round_number(chain_dir)
    timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    basename = f"r{round_num}-{timestamp}"
    prompt_file = chain_dir / f"{basename}-request.md"
    response_file = chain_dir / f"{basename}-response.md"
    prompt_text = make_prompt(
        root=root, target=target, kind=args.kind,
        context=context, max_lines=args.max_lines,
    )
    prompt_file.write_text(prompt_text, encoding="utf-8")

    head_sha_at_request = current_head_sha(root)
    worktree_dirty_at_request = is_dirty(root)

    try:
        result = run_reviewer(
            command_template=args.reviewer_cmd,
            prompt_file=prompt_file, prompt_text=prompt_text,
            target_file=target, kind=args.kind,
            prompt_transport=args.prompt_transport, timeout=args.timeout,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: reviewer command not found: {exc}", file=sys.stderr)
        print("Set AGENT_REVIEWER_CMD, e.g. AGENT_REVIEWER_CMD='reviewer {prompt_file}'", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"ERROR: reviewer command timed out after {args.timeout}s", file=sys.stderr)
        return 124

    review_path = write_review_artifact(
        root=root, target=target, kind=args.kind,
        command_template=args.reviewer_cmd,
        prompt_file=prompt_file, response_file=response_file,
        round_num=round_num, result=result,
    )
    review_body = review_path.read_text(encoding="utf-8")
    verdict, verdict_valid = parse_verdict(review_body)
    findings_count, blocking_count = parse_findings(review_body)

    head_sha_after_round = current_head_sha(root)
    round_entry = {
        "round": round_num,
        "request": prompt_file.name,
        "response": response_file.name,
        "resolution": None,
        "head_sha_at_request": head_sha_at_request,
        "head_sha_after_round": head_sha_after_round,
        "worktree_dirty_at_request": worktree_dirty_at_request,
        "verdict": verdict,
        "verdict_valid": verdict_valid,
        "findings_count": findings_count,
        "blocking_findings_count": blocking_count,
    }
    manifest["rounds"].append(round_entry)
    write_manifest(manifest_path, manifest)

    review_rel = rel_or_abs(review_path, root)
    prompt_rel = rel_or_abs(prompt_file, root)
    if args.emit == "paths":
        print(f"REVIEW_PATH={review_rel}")
        print(f"PROMPT_PATH={prompt_rel}")
        print(f"ROUND={round_num}")
    elif args.emit == "review":
        print(review_body)
    elif args.emit == "json":
        print(json.dumps({
            "review_path": review_rel,
            "prompt_path": prompt_rel,
            "chain": manifest["chain"],
            "round": round_num,
            "kind": args.kind,
            "work_id": manifest.get("work_id"),
            "status": "ok" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "verdict": verdict,
            "verdict_valid": verdict_valid,
            "findings_count": findings_count,
            "blocking_findings_count": blocking_count,
            "review_depth": "standard",
            "reviewers": [{
                "role": "primary",
                "verdict": verdict,
                "verdict_valid": verdict_valid,
                "review_path": review_rel,
                "review": review_body,
            }],
            "merged_verdict": verdict,
            "merged_findings_path": None,
            "merged_findings": None,
            "review": review_body,
        }, indent=2))
    return result.returncode


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
