# Review — 2026-05-19-p11-s5-final-guardrails-and-documentation.md (plan, round 1)

- Target: `docs/plans/2026-05-19-p11-s5-final-guardrails-and-documentation.md`
- Request: `docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r1-2026-05-19T0050-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# P11.S5 Plan Review

## Findings

### F1 — `p11-inventory-lint.sh` will fail after Task 4 Step 4 rewrites P11-UI-210 (Severity: blocking)

`scripts/p11-inventory-lint.sh:95` hard-codes a list of required substrings the inventory must contain, including the literal `'resolution is deferred to P11.S5'`. That phrase currently appears **only once** in `docs/design/_evidence/p11-ui-convergence-inventory.md` — inside the `P11-UI-210` rationale (line 236).

Task 4 Step 4 instructs the implementer to rewrite that rationale to "S5 aligned the IDE alias to `variants/base` while leaving runtime aliases in `next.config.js`" and flip status to `done`. Once that edit lands, the required substring disappears and `scripts/p11-inventory-lint.sh` exits non-zero — which then breaks `verify:pre-push` for the rest of S5 and beyond.

The spec already anticipates this ("`scripts/p11-inventory-lint.sh` continues to pass and still requires the alias evidence fields **until S5 updates the inventory status**") but the plan does not include the matching edit. Add an explicit step in Task 4 (or Task 3) that:

- Removes `'resolution is deferred to P11.S5'` from the required-strings loop in `scripts/p11-inventory-lint.sh`, **or**
- Preserves the phrase by leaving it in a historical note row / closeout cross-link.

The chosen option must also be reflected in the Task 3 fixture test's "valid inventory" template (currently it relies on the required-substring being present).

### F2 — Task 4 Step 3 JSON-import test has two real correctness issues (Severity: important)

```ts
const tsconfig = await import("../../../../tsconfig.json")
expect(tsconfig.default.compilerOptions.paths["@/components/ui/active/*"]).toEqual([...])
```

Two problems:

1. **Dynamic JSON import in Bun returns the parsed object as the module namespace, with the parsed value on `.default` only when using `with { type: "json" }` or when TS interop synthesises a default.** The existing sibling test (`variant-alias.test.ts`) uses `require()` against `next.config.js` precisely to avoid the import-assertion variance. The plan should pick one approach and verify it actually works locally before codifying it. The `fs.readFileSync` + `JSON.parse` fallback is fine, but…
2. The fallback snippet uses `path.resolve(import.meta.dir, …)` without importing `path`. Add `import path from "node:path"` (the working test in this same file already does this).

Recommend skipping `await import` entirely and going straight to `fs.readFileSync` + `JSON.parse`, mirroring the rest of the file.

### F3 — Allowlist reorganisation risks reordering line-anchored `static-layout-style:` entries (Severity: important)

`.lint/p11-site-variant-allowlist.txt` uses `static-layout-style:<path>:<line-number>` entries. Task 5 Step 2 says "Keep the exact allowlist entry lines, but group them under comments" and Step 2's prose says "Do not renumber or edit `static-layout-style:` line numbers". Good.

However, *reordering* entry lines themselves does not change `line-number` payloads — but Step 2's wording leaves it ambiguous whether the implementer may also resort the live entries inside their new comment sections. To prevent an honest mistake, state explicitly: "Move entries between sections is allowed; modifying the `<line-number>` suffix is not." Also add a verification step that compares the sorted `module-variant:`/`adhd-primitive:`/`static-layout-style:` line sets pre/post to confirm membership is identical (e.g. `diff <(rg ^module-variant before) <(rg ^module-variant after)`).

### F4 — Task 3 Step 4 changes pre-push semantics without an opt-out test (Severity: important)

The proposed `verify:pre-push` rewrite inserts `bun run test:p11-guardrails` **before** the live `scripts/p11-inventory-lint.sh` / `scripts/p11-site-variant-lint.sh` / `scripts/p9-structural-lint.sh` checks. This duplicates the P9 work (the new aggregate runs `p9-structural-audit.test.sh` + `p9-structural-lint.test.sh`, and pre-push then re-runs `scripts/p9-structural-lint.sh` for real). That's tolerable (~seconds), but:

- The spec says "inserted into `verify:pre-push` **before** the real-mode P9/P11 lint scripts" — plan complies. ✓
- But `verify:pre-push` already targets "under 60 seconds" (per `CLAUDE.md`). Add a step that times the new chain and records the delta in the closeout note so a regression doesn't surface later as opaque slowdown.

### F5 — Task 3 Step 2 fixture inventory may not satisfy all enum/regex checks (Severity: important)

The fixture inventory only contains row IDs `P11-UI-001` and `P11-UI-002`, plus the appended `P11-UI-003` for the failure case. The lint script reads rows via `rg '^\| P11-UI-[0-9]{3} \|'` (script line 93), so IDs are fine. But the script also requires:

- `scope_rows` (count of TSV rows minus header) must equal `inventory_rows` — fixture matches (2 rows in TSV body, 2 inventory rows). ✓
- All required substrings present anywhere in the file — fixture appends a free-form "Required fixture evidence mentions:" line. ✓

What is **not** verified by the plan: that the script's path-uniqueness check works on the fixture's relative paths (no quirks from leading `apps/…` vs. absolute). Recommend running the fixture once locally before committing the test to confirm green-on-baseline, and add that command to Task 3 Step 5's evidence list explicitly (e.g. `bash scripts/__tests__/p11-inventory-lint.test.sh | tee /tmp/p11-inv-test.log`).

Also: the trailing line `Required fixture evidence mentions:` is fragile — any future tightening of the script (e.g. moving from "anywhere in file" to "row rationale only") will silently break this test. A one-line comment in the fixture pointing at `scripts/p11-inventory-lint.sh:95` would prevent that drift.

### F6 — Plan asserts pre-push currently lacks guardrail-test wiring; pre-push already runs the real-mode scripts (Severity: minor)

Task 3 Step 1 says the grep "is expected to find no current pre-push/package wiring." That is accurate for `p11-site-variant-lint.test.sh` (the *self-test*), but pre-push **does** already run `scripts/p11-inventory-lint.sh && scripts/p11-site-variant-lint.sh && scripts/p9-structural-lint.sh` (confirmed in `package.json:48`). The plan's narrative ("turn one-off migration scripts into maintained guardrails") is fine, but the grep wording could mislead an implementer into thinking the live gates aren't wired. Sharpen Step 1's "Expected" to: "The self-tests are not wired; the live scripts already are."

### F7 — `tasktool ref P11.S5 --add <path>` only accepts one path per call (Severity: minor)

Task 1 Step 1 chains three `tasktool ref P11.S5 --add <path>` calls — that matches the verified CLI (`--add ADD | --remove REMOVE`, single value). ✓ No issue, but flagging for the implementer: this is one path per invocation, which is what the plan already does.

### F8 — `tasktool close --reviewer-chain --refs` arg structure (Severity: minor)

Task 6 Step 6 invokes:

```
tasktool close P11.S5 \
  --reviewer-chain docs/reviewer/... \
  --refs docs/design/_evidence/p11-s5/CLOSE-OUT-NOTE.md \
  --note "..."
```

Verified against `tasktool close -h`: all flags exist and are `REFS` (single value). ✓ If multiple refs are needed in S5, the plan needs adjustment (current schema appears to accept a single ref arg only — though it may be space- or comma-separated; verify with one extra ref before finalising the closeout commit).

### F9 — Plan claims runtime aliasing is "unchanged" but Task 4 Step 3 fallback dynamic-imports `tsconfig.json` from a file path that resolves through `import.meta.dir` (Severity: nit)

The fallback `path.resolve(import.meta.dir, "../../../../tsconfig.json")` reaches up four levels from `apps/storefront1/src/components/ui/__tests__/`. Count: `__tests__` → `ui` → `components` → `src` → `apps/storefront1/tsconfig.json`. That's three levels up, not four. The current test file is at `apps/storefront1/src/components/ui/__tests__/variant-alias.test.ts`, so `../../../../` lands at `apps/storefront1/`. ✓ Three `..` would land in `src/`. Four is correct. Withdraw — but the implementer should sanity-check with `ls` before committing.

### F10 — Task 2 Step 1 introduces a fenced code block inside a fenced code block (Severity: nit)

The replacement Markdown for `CLAUDE.md` "Project Task List" contains a triple-backtick `bash` block *inside* the outer triple-backtick `markdown` block. As written, this will terminate the outer fence at the first inner closing ``` and leave the rest of the section as prose. Use a quadruple-backtick outer fence in the plan document, or instruct the implementer to drop the outer fence entirely and treat the block as literal Markdown content. Same applies to Task 2 Step 2 (`apps/storefront1/CLAUDE.md`) and Task 2 Step 3 (`ui-convergence-policy.md`).

This is a plan-readability issue; the actual file edits will be fine if the implementer notices. Worth fixing in the plan to remove ambiguity.

## Open Questions / Assumptions

1. Is `scripts/external-reviewer.py` the canonical reviewer CLI? CLAUDE.md mentions a `reviewer` bridge but the plan calls `python3 scripts/external-reviewer.py`. Confirm before Task 6 Step 5.
2. Does the spec's "until S5 updates the inventory status" intend the `'resolution is deferred to P11.S5'` substring requirement to be dropped from the lint, or replaced with a different anchor (e.g. `'P11.S5 alias decision'`)? F1 hinges on this choice.
3. Task 5 Step 3 creates a tasktool `cross` item "only for true future work." There's no inspection step listing existing X items (X51-X53 referenced but not verified to exist in `docs/tasklist.json`). Add a quick `tasktool list --open | grep -i 'allowlist\|variant\|p11'` before creating to avoid the duplicate path that X45 was created to backstop against.

## Suggested Document Edits

- **Task 4**: insert a new Step (between current Steps 4 and 5) titled "Update inventory-lint required-substrings" that edits `scripts/p11-inventory-lint.sh:95` to remove or replace `'resolution is deferred to P11.S5'`. Mirror the edit in the Task 3 fixture template.
- **Task 4 Step 3**: replace the `await import("../../../../tsconfig.json")` form with the `fs.readFileSync` + `JSON.parse` form, and add the missing `import path from "node:path"`.
- **Task 2 Steps 1-3**: switch outer Markdown fences to `~~~markdown` or quadruple-backtick to avoid the fenced-in-fenced ambiguity.
- **Task 5 Step 2**: add explicit "modify `<line-number>` is forbidden; reordering between comment sections is allowed" sentence, plus a `diff` verification of pre/post entry membership.
- **Task 3 Step 1**: clarify that live scripts are already wired in `verify:pre-push`; only the self-tests are not.

## Verification Gaps

- Plan does not run the fixture self-test against the **current** `scripts/p11-inventory-lint.sh` once before committing — recommended to avoid green-on-mock / red-on-real surprise.
- No step times the new pre-push chain to confirm the <60s budget still holds.
- No step verifies `scripts/external-reviewer.py` exists / is the right entrypoint before Task 6 Step 5 fires.

## Overall Verdict

**revise** — primarily because F1 makes the plan deterministic-to-break-pre-push as written. F2 (test mechanics) and F3 (allowlist scope) are also real correctness concerns that need explicit handling before implementation. The rest are quality nits. After the F1/F2/F3 edits land and the fixture is exercised against the real script once, the plan should be solidly executable.
