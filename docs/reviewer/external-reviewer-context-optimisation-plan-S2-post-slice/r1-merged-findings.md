# Merged findings for r1

## Primary

# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-slice, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/r1-2026-05-14T1628-primary-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. Findings

F1. Severity: minor - Slice 2 manual evidence is checked but not recorded.  
[docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2638) lists the synthetic large-chain check and expected `<200 KB` result, but does not capture the observed request size. I reran the check and got `84,854` bytes, so this is evidence hygiene, not a correctness blocker.

F2. Severity: minor - Worktree has an untracked review artifact directory.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. This appears to be the current review chain artifact, but it should be committed, ignored, or otherwise intentionally handled before final closeout.

2. Open questions / assumptions

- Assumption: this post-slice gate is for Slice 2, based on the checked Slice 2 tasks and the `S2-post-slice` review artifact path.
- No implementation-blocking questions.

3. Suggested document edits

- Under Task 2.6 Step 2, add the observed manual-check output, e.g. `Observed: r2 request was 84,854 bytes`.
- After this review completes, record or land the `docs/reviewer/...S2-post-slice/` artifacts according to the repo’s review-chain convention.

4. Verification gaps / commands run

Commands I ran:

```bash
python3 -m pytest skills/external-review/tests/test_incremental_budget.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_diff_caps.py -q
python3 -m pytest skills/external-review/tests/ -q
git status --short
```

Results:

- Focused Slice 2 tests: `8 passed`
- Full external-review suite: `141 passed, 1 warning`
- Manual synthetic check: r2 request `84,854` bytes, under the `<200 KB` acceptance gate

5. Overall verdict: ready with small edits

---

## Reviewer stderr (tail)

```text
s/external-review/tests/test_diff_caps.py
  2628	git commit -m "external-reviewer: global diff cap, untracked-file count + line limits"
  2629	```
  2630	

codex
1. Findings

F1. Severity: minor - Slice 2 manual evidence is checked but not recorded.  
[docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2638) lists the synthetic large-chain check and expected `<200 KB` result, but does not capture the observed request size. I reran the check and got `84,854` bytes, so this is evidence hygiene, not a correctness blocker.

F2. Severity: minor - Worktree has an untracked review artifact directory.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. This appears to be the current review chain artifact, but it should be committed, ignored, or otherwise intentionally handled before final closeout.

2. Open questions / assumptions

- Assumption: this post-slice gate is for Slice 2, based on the checked Slice 2 tasks and the `S2-post-slice` review artifact path.
- No implementation-blocking questions.

3. Suggested document edits

- Under Task 2.6 Step 2, add the observed manual-check output, e.g. `Observed: r2 request was 84,854 bytes`.
- After this review completes, record or land the `docs/reviewer/...S2-post-slice/` artifacts according to the repo’s review-chain convention.

4. Verification gaps / commands run

Commands I ran:

```bash
python3 -m pytest skills/external-review/tests/test_incremental_budget.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_diff_caps.py -q
python3 -m pytest skills/external-review/tests/ -q
git status --short
```

Results:

- Focused Slice 2 tests: `8 passed`
- Full external-review suite: `141 passed, 1 warning`
- Manual synthetic check: r2 request `84,854` bytes, under the `<200 KB` acceptance gate

5. Overall verdict: ready with small edits
tokens used
94,203
```


## Sweep 1

# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-slice, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/r1-2026-05-14T1628-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. Findings

S1.F1. Severity: important - The slice leaves untracked, incomplete review artifacts in the worktree.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. That directory contains only:

- `r1-2026-05-14T1628-primary-request.md`
- `r1-2026-05-14T1628-primary-response.md`
- `r1-2026-05-14T1628-sweep1-request.md`

There is no `chain.json` and no sweep response. For a post-slice completion gate, this should be resolved before claiming the slice is closed: commit the intended review artifacts, remove the partial chain, or rerun/land a complete chain.

S1.F2. Severity: minor - `--incremental-budget-chars` is documented as a cap, but `apply_budget()` can return a prompt over the requested budget.  
[external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:242) trims until `len(out) <= budget_chars`, then appends the budget note afterward. The test also allows overage: [test_incremental_budget.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/tests/test_incremental_budget.py:27). I reproduced `budget_chars=200` returning length `266`. This is small in normal use, but it weakens the “global cap” claim in the CLI help at [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:968).

S1.F3. Severity: minor - Slice 2 manual acceptance is checked off without recording the observed evidence in the plan.  
[the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2638) marks the synthetic large-chain check complete and states the expected `<200 KB` request size, but does not record the actual measured request size.

2. Open questions / assumptions

- I assume this gate is for Slice 2, based on the completed Slice 2 checkboxes and the untracked `S2-post-slice` review chain.
- I assume the untracked review directory is intended slice evidence, not disposable local scratch.

3. Suggested document edits

- Add the observed synthetic check result under Task 2.6 Step 2.
- Either land or discard the partial `docs/reviewer/...S2-post-slice/` artifacts.
- Tighten the budget implementation or docs/tests so “cap” means either exact `<= budget_chars` or explicitly “budget plus diagnostic note.”

4. Verification gaps / commands run

- `python3 -m pytest skills/external-review/tests/` -> `141 passed, 1 warning`
- `git status --short` -> one untracked review artifact directory
- `find docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice -maxdepth 2 -type f ...` -> showed incomplete artifact set
- Budget repro: `apply_budget(..., budget_chars=200)` returned length `266`

5. Overall verdict: revise

---

## Reviewer stderr (tail)

```text
00 KB` result, but does not capture the observed request size. I reran the check and got `84,854` bytes, so this is evidence hygiene, not a correctness blocker.

S1.F2. Severity: minor - Worktree has an untracked review artifact directory.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. This appears to be the current review chain artifact, but it should be committed, ignored, or otherwise intentionally handled before final closeout.

2. Open questions / assumptions

- Assumption: this post-slice gate is for Slice 2, based on the checked Slice 2 tasks and the `S2-post-slice` review artifact path.
- No implementation-blocking questions.

3. Suggested document edits

- Under Task 2.6 Step 2, add the observed manual-check output, e.g. `Observed: r2 request was 84,854 bytes`.
- After this review completes, record or land the `docs/reviewer/...S2-post-slice/` artifacts according to the repo’s review-chain convention.

4. Verification gaps / commands run

Commands I ran:

```bash
python3 -m pytest skills/external-review/tests/test_incremental_budget.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_diff_caps.py -q

codex
The suite is green: `141 passed, 1 warning`. I found no failing acceptance tests, but the repo still has an untracked and apparently incomplete post-slice review artifact directory, so the close-out state is not clean.
exec
/usr/bin/zsh -lc "python3 - <<'PY'
from pathlib import Path
import importlib.util
p=Path('skills/external-review/scripts/external-reviewer.py')
spec=importlib.util.spec_from_file_location('er', p)
er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
body = f\"{er.PROMPT_SENTINEL_START}\\n## Review chain summary\\nkeep\\n\\n## Target Preview\\n\" + (\"T\"*10000) + f\"\\n{er.PROMPT_SENTINEL_END}\"
out = er.apply_budget(body, budget_chars=200)
print(len(out))
print(out[:120].replace('\\n','\\\\n'))
PY" in /home/simon/Dev/sigreer/skills/superstar
 succeeded in 0ms:
266
```

