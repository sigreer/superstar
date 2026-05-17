# External Reviewer Provider Flipping and Sandboxing — Design Spec

**Date:** 2026-05-17
**Target:** `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, and the `reviewer-agent` wrapper installed by project setup.

## Incident Summary

On 2026-05-16 at 22:58:19 UTC, a Codex reviewer subprocess launched through `reviewer-agent` ran this command in `/home/simon/Dev/sigreer/ags`:

```bash
readlink -f ~/.config/ags && XDG_CONFIG_HOME=$(mktemp -d) scripts/superstar-tasklist scan && rm -rf "$XDG_CONFIG_HOME"
```

Because `VAR=value command` scopes the variable assignment only to that one command, the final `rm -rf "$XDG_CONFIG_HOME"` expanded against the reviewer process environment instead of the temporary directory. In Simon's desktop session that value was `/home/simon/.config`, so the reviewer deleted the real config tree.

The direct enabling cause was the installed wrapper:

```bash
#!/bin/bash
exec codex exec --dangerously-bypass-approvals-and-sandbox "$@"
```

That gives the reviewer unsandboxed user-level write access. The external-review bridge did not instruct Codex to run that command, but the bridge spawned a reviewer with enough authority for an independently composed cleanup command to damage unrelated user state.

## Forensics Conclusions

The proposed mitigation is directionally correct:

1. The reviewer must not run with `--dangerously-bypass-approvals-and-sandbox`.
2. The reviewed repository must be readable but not writable by the reviewer.
3. Reviewer write access must be limited to a short-lived scratch directory plus a dedicated response-output directory.
4. The bridge must pass enough path context to the wrapper for the wrapper to construct that sandbox per invocation.
5. Provider selection should be automatic in normal use: Claude callers get Codex reviewers, Codex callers get Claude reviewers.

One refinement is needed: for Codex, do not make the reviewed repository the Codex workspace root when using `workspace-write`, because that would make the repository writable. Instead, run Codex with a scratch directory as `--cd`, add only the dedicated response-output directory as writable, and grant broad read access through Codex's read-access configuration. The reviewed repository path is passed in the prompt and environment as read-only context.

## Goals

- Prevent reviewer agents from writing outside explicitly assigned reviewer scratch/output locations.
- Preserve the current file-based review flow: `external-reviewer.py` still writes request/response artifacts and chain metadata.
- Keep `AGENT_REVIEWER_CMD` and `--reviewer-cmd` as explicit overrides for custom setups.
- Add a first-class provider-selection layer so the default reviewer is external to the caller.
- Support both directions:
  - Claude coordinator -> Codex reviewer.
  - Codex coordinator -> Claude reviewer.
- Make sandbox paths visible and testable in artifacts/manifest metadata.

## Non-Goals

- Prevent all destructive commands inside the scratch directory.
- Guarantee perfect safety for arbitrary custom `AGENT_REVIEWER_CMD` templates.
- Replace the existing prompt, verdict parsing, rate-limit handling, or chain-folder model.
- Make the reviewer a non-agent static linter. The reviewer may still run read-only inspection commands.

## Design

### 1. Bridge-Owned Reviewer Context

`external-reviewer.py` will compute and export these environment variables for every reviewer subprocess, including primary and sweep reviewers:

```text
AGENT_REVIEWER_REPO_ROOT=/absolute/repo/root
AGENT_REVIEWER_CHAIN_DIR=/absolute/docs/reviewer/<chain>
AGENT_REVIEWER_REQUEST_FILE=/absolute/docs/reviewer/<chain>/rN-...-request.md
AGENT_REVIEWER_RESPONSE_DIR=/absolute/docs/reviewer/<chain>/.reviewer-output/rN-primary
AGENT_REVIEWER_SCRATCH_DIR=/tmp/superstar-reviewer-<chain>-<round>-<role>-XXXXXX
AGENT_REVIEWER_TARGET_FILE=/absolute/path/to/target.md
AGENT_REVIEWER_KIND=spec|plan|post-slice|post-phase|...
AGENT_REVIEWER_ROLE=primary|sweep
AGENT_REVIEWER_SWEEP_INDEX=
```

The bridge creates `AGENT_REVIEWER_RESPONSE_DIR` and `AGENT_REVIEWER_SCRATCH_DIR` before spawning the reviewer. The response directory is private to one reviewer invocation, not the chain root, so a sandbox that grants directory-level write access does not expose existing request/response artifacts.

The bridge removes `AGENT_REVIEWER_SCRATCH_DIR` after the subprocess exits unless `--keep-reviewer-scratch` is set. Cleanup must use the Python `TemporaryDirectory`/`shutil.rmtree` path object retained by the parent process, never a shell-expanded environment variable.

### 2. New Placeholders

The existing command-template expansion gains these placeholders:

```text
{repo_root}
{response_dir}
{scratch_dir}
{request_file}
```

Existing placeholders remain unchanged:

```text
{prompt_file} {prompt_text} {target_file} {kind}
{chain_dir} {round} {previous_response} {resolution_file} {session_file}
```

Template commands still run through the shell for backward compatibility, but the bridge passes the same environment variables to both template and argv execution paths.

### 3. Provider Selection

Add options:

```bash
--reviewer-provider auto|codex|claude|custom
--caller-provider auto|claude|codex|unknown
```

Environment equivalents:

```text
AGENT_REVIEWER_PROVIDER
AGENT_REVIEWER_CALLER
```

Resolution order:

1. If `--reviewer-cmd` or `AGENT_REVIEWER_CMD` is explicitly set, use it and treat provider as `custom`.
2. Else resolve caller:
   - explicit `--caller-provider` / `AGENT_REVIEWER_CALLER`;
   - known harness environment detection where reliable;
   - `unknown`.
3. With `--reviewer-provider auto`:
   - caller `claude` -> reviewer provider `codex`;
   - caller `codex` -> reviewer provider `claude`;
   - caller `unknown` -> fail closed with a clear error that asks for `AGENT_REVIEWER_PROVIDER` or `AGENT_REVIEWER_CMD`.

Failing closed for unknown callers avoids silently choosing the same provider as the coordinator.

### 4. Codex Reviewer Wrapper

The Codex branch of `reviewer-agent` must run without the bypass flag. It should use this shape:

```bash
codex exec \
  --sandbox workspace-write \
  --ask-for-approval never \
  --ephemeral \
  --cd "$AGENT_REVIEWER_SCRATCH_DIR" \
  --add-dir "$AGENT_REVIEWER_RESPONSE_DIR" \
  -c 'sandbox_permissions=["disk-full-read-access"]' \
  --output-last-message "$AGENT_REVIEWER_RESPONSE_DIR/last-message.md" \
  -
```

The wrapper feeds the prompt on stdin and prints `last-message.md` to stdout after Codex exits so `external-reviewer.py` can continue to own the canonical response artifact.

Expected permission model:

- Repository and context files: readable through disk-full-read access.
- Scratch directory: writable because it is the Codex workspace root.
- Response directory: writable via `--add-dir`.
- Home/config/project directories: not writable from model-generated shell commands.
- Approval escalation: disabled; write attempts outside the sandbox fail instead of prompting.
- Session persistence: disabled with `--ephemeral` so the CLI does not need to write reviewer sessions under `~/.codex`.

If a future Codex CLI supports an exact read-only-root plus exact writable-path policy, the wrapper can use that stronger primitive without changing the bridge contract.

### 5. Claude Reviewer Wrapper

The Claude branch should run non-interactively and in a read-only review posture:

```bash
claude --print \
  --permission-mode plan \
  --add-dir "$AGENT_REVIEWER_REPO_ROOT" \
  --add-dir "$AGENT_REVIEWER_RESPONSE_DIR"
```

The implementation should additionally restrict tools where Claude Code supports reliable allowlists:

- Allow read/search tools.
- Allow narrowly scoped read-only shell commands such as `git status`, `git diff`, `rg`, `sed`, `nl`, `cat`, `find`, and `pwd`.
- Disallow edit/write tools and broad shell execution.

As with Codex, Claude's final output is written to `$AGENT_REVIEWER_RESPONSE_DIR/last-message.md` when possible and echoed to stdout for the bridge. If Claude cannot provide an exact output-file flag in the installed version, stdout capture remains the source of truth and the response directory exists only for temporary wrapper state.

Claude's exact flag set should be verified in implementation against the installed CLI because permission-mode semantics and tool allowlist syntax can drift between versions.

### 6. Bridge Artifact Metadata

Each reviewer entry in `chain.json` gains:

```json
{
  "provider": "codex",
  "caller_provider": "claude",
  "sandbox": {
    "repo_root": "/home/simon/Dev/sigreer/ags",
    "scratch_dir": "/tmp/superstar-reviewer-...",
    "response_dir": "docs/reviewer/<chain>/.reviewer-output/r1-primary",
    "mode": "workspace-write-with-read-access"
  }
}
```

The persisted human response artifact should include a compact line:

```markdown
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
```

Do not persist absolute scratch directory contents unless `--keep-reviewer-scratch` is set.

### 7. Documentation Updates

`skills/external-review/SKILL.md` must document:

- Default provider flipping.
- How to force a provider.
- How to override with a custom command.
- The sandbox contract wrappers must honor.
- The safety rule that reviewer wrappers must not use bypass/no-sandbox flags unless the caller has supplied an external OS sandbox and explicitly opted into `custom`.

Project setup docs must install or update `reviewer-agent` as a provider-aware wrapper, not a hardcoded Codex bypass wrapper.

## Alternatives Considered

### A. Keep the bridge provider-neutral and only patch `~/.local/bin/reviewer-agent`

This is too weak. The wrapper needs per-invocation paths that only the bridge knows cleanly: repo root, chain dir, role-specific output dir, and scratch dir. Without bridge changes, every local wrapper would rediscover or guess context.

### B. Make the repository writable but rely on reviewer instructions

Rejected. The incident was caused by a reviewer composing a command it believed was safe. Instructions reduce probability; sandboxing reduces blast radius.

### C. Use Codex `read-only` sandbox and no writable directories

Rejected for the Codex reviewer path because the CLI may need a place for final-message output and temporary command artifacts. The safer practical pattern is writable scratch as the workspace, plus a narrow writable output directory, with the reviewed repository readable but outside the writable workspace.

## Testing Plan

### Unit Tests

- Provider auto-selection:
  - `caller=claude` resolves `codex`.
  - `caller=codex` resolves `claude`.
  - explicit `AGENT_REVIEWER_CMD` resolves `custom` and bypasses auto selection.
  - unknown caller with auto provider exits with an operational error.
- Environment injection:
  - fake reviewer records `AGENT_REVIEWER_REPO_ROOT`, `AGENT_REVIEWER_RESPONSE_DIR`, `AGENT_REVIEWER_SCRATCH_DIR`, role, and kind.
  - primary and sweep reviewers receive distinct response/scratch dirs.
- Placeholder expansion includes `{repo_root}`, `{response_dir}`, `{scratch_dir}`, and `{request_file}`.
- Scratch cleanup removes the scratch directory after success/failure unless `--keep-reviewer-scratch` is set.
- Chain metadata records provider and sandbox summary.

### Wrapper Tests

Use fake `codex` and `claude` executables on `PATH` to assert argv without invoking real providers:

- Codex wrapper never passes `--dangerously-bypass-approvals-and-sandbox`.
- Codex wrapper passes `--sandbox workspace-write`, `--ask-for-approval never`, `--ephemeral`, `--cd "$AGENT_REVIEWER_SCRATCH_DIR"`, and `--add-dir "$AGENT_REVIEWER_RESPONSE_DIR"`.
- Claude wrapper passes `--print` and a read-only/plan permission mode.
- Both wrappers fail fast when required env vars are missing.

### Live Safety Smoke Test

Run against a temporary git repo with a fake home/config path:

1. Invoke the Codex reviewer through the bridge.
2. Prompt attempts:
   - write inside repo;
   - write inside `$HOME/.config`;
   - write inside scratch;
   - write inside response dir.
3. Expected:
   - repo and home writes fail;
   - scratch and response writes succeed;
   - bridge receives and persists the final reviewer text.

Run the equivalent Claude smoke test with the installed Claude CLI's actual permission controls.

## Rollout

1. Add bridge env/context plumbing and unit tests with fake reviewers.
2. Add provider-resolution logic behind defaults that preserve explicit `AGENT_REVIEWER_CMD`.
3. Add/update `reviewer-agent` wrapper template in project setup.
4. Update external-review docs.
5. Run fake-wrapper tests.
6. Run one live Codex safety smoke test.
7. Run one live Claude safety smoke test.
8. Replace Simon's installed `~/.local/bin/reviewer-agent` only after the fake tests pass.

## Acceptance Criteria

- No shipped or documented default wrapper uses `--dangerously-bypass-approvals-and-sandbox`.
- Default review from Claude selects Codex; default review from Codex selects Claude.
- Explicit `AGENT_REVIEWER_CMD` still works for custom reviewers.
- Reviewer subprocesses receive repo, scratch, request, target, role, and response path context via environment.
- Codex reviewer cannot write to the reviewed repository or `$HOME/.config` in the live safety smoke test.
- Existing external-review unit tests continue to pass.
- New provider/sandbox tests pass.

## Self-Review

- No implementation is prescribed that requires changing the existing chain-folder architecture.
- The spec distinguishes bridge responsibilities from wrapper responsibilities.
- The Codex mitigation does not rely on shell-scoped cleanup variables.
- Unknown caller behavior is fail-closed rather than silently unsafe.
- The design keeps backward compatibility for explicit custom commands while improving the default path.
