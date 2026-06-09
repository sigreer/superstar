1. Findings

F1. Severity: blocking. Acceptance criterion 4 contradicts the referenced-path design for inline code. The design says dangling backtick-quoted repo paths are scanned and reported as warnings (`docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md:102-109`), but AC4 says “paths inside fenced code blocks and inline-code spans produce no finding” (`docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md:211-213`). That makes the fixture expectations mutually incompatible: a dangling backtick path is both required to warn and required to produce no finding.

F2. Severity: important. Auto-preflight ordering is internally inconsistent and drift-prone against the current CLI. The spec says preflight runs after the round number is known (`docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md:165-167`) but also says preflight runs before the manifest is read (`docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md:157-160`). In current code, the manifest is read before `round_num = next_round_number(chain_dir)` (`skills/external-review/scripts/external-reviewer.py:2617-2625`, `skills/external-review/scripts/external-reviewer.py:2715`). The spec should choose the intended ordering, especially because this affects whether preflight failures can mask schema-too-new failures and whether a failed preflight creates/touches a chain folder.

2. Open questions / assumptions

- Should auto-preflight avoid creating the chain folder on failure, or is `chain_dir.mkdir(...)` before the gate acceptable?
- For inline code, I assume the intended split is: placeholder scan ignores inline code; path scan intentionally inspects inline-code spans and warns on dangling repo paths.

3. Suggested document edits

- Fix AC4 to say placeholders inside fenced/inline code produce no placeholder finding, paths inside fenced code produce no path finding, and dangling inline-code paths produce warnings unless exempted.
- Replace the “preflight runs before the manifest is read” sentence with the exact intended sequence, for example: resolve target/context, discover/read manifest to determine round, run preflight only when `round_num == 1`, then stop before prompt construction/provider spawn. If the intended behavior is no chain-folder I/O before preflight, specify how round 1 is determined without reading the manifest.

4. Verification gaps / commands that should be run

- Add a unit test for `run_preflight_checks` covering dangling inline-code path warning vs fenced-code path exemption.
- Add subprocess tests for `external-reviewer preflight --emit json` exit 0/4 behavior.
- Add subprocess tests proving round-1 `review` fails before spawning the reviewer and `--no-preflight` reaches the reviewer command.
- Add a regression test for the chosen manifest/preflight ordering, including a schema-too-new chain plus a failing target if that precedence matters.

Overall verdict: revise