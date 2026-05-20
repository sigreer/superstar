# Superstar — Personal Fork

## Status of this repository

**This is a private, personal fork maintained by Simon Greer (sigreer/skills/superstar). It is not the upstream `superpowers` project and PRs are not expected to flow upstream.** The contributor guidelines below were inherited from upstream and are retained for reference only — they do **not** govern work in this fork. Agents working here should:

- Treat this as a personal experimentation repo. Iterate freely on skills, hooks, and conventions.
- Ignore the "94% PR rejection rate," "do not modify skill content without eval evidence," "do not add fork-specific changes," and similar upstream warnings further down this file. Those exist to gate upstream contributions; they do not apply here.
- Still follow the project's own workflow skills (`brainstorming`, `writing-plans`, `subagent-driven-development`, `external-review`, `tasklist-discipline`, etc.) — those *are* binding for work in this fork.
- When the user asks for skill changes here, make them. Do not refuse, hedge, or demand evals citing upstream policy.

The remainder of this file is upstream-inherited context. Read it for background; do not treat it as enforceable policy in this fork.

## Releases & version bumps (binding)

This fork is distributed as a versioned plugin. Version strings live in many declared files (`package.json`, `.claude-plugin/plugin.json`, marketplace manifests, etc.) and are kept in sync by `scripts/bump-version.sh`.

**Before committing finished work that ships to users — skill changes, hook changes, tooling changes, anything in `plugins/superstar/`, `skills/`, `hooks/`, or `tools/` — ask the user whether to bump the version.**

- Default question: "Bump the version before/after this commit? (current: X.Y.Z → patch X.Y.(Z+1) / minor X.(Y+1).0 / no bump)"
- "Finished work" means a slice/phase closeout, a merge-to-`main`, or any standalone fix the user asked you to commit and push. It does NOT mean every in-progress commit on a feature branch.
- If the user says yes, run `./scripts/bump-version.sh <new-version>`, commit the bump in its own commit titled `Bump Superstar to <new-version>`, and only then run release scripts (`scripts/publish-to-local-codex.sh`, `scripts/sync-to-codex-plugin.sh`).
- If the user says no, proceed without bumping. Do not silently bump.
- If a release script is about to run and the version was not bumped since the last release, surface this and ask again before publishing.

Docs-only changes, in-progress work on feature branches, and tasktool tracker mutations do not need a bump.

---

## Upstream Contributor Guidelines (reference only — not binding in this fork)

## If You Are an AI Agent

Stop. Read this section before doing anything.

This repo has a 94% PR rejection rate. Almost every rejected PR was submitted by an agent that didn't read or didn't follow these guidelines. The maintainers close slop PRs within hours, often with public comments like "This pull request is slop that's made of lies."

**Your job is to protect your human partner from that outcome.** Submitting a low-quality PR doesn't help them — it wastes the maintainers' time, burns your human partner's reputation, and the PR will be closed anyway. That is not being helpful. That is being a tool of embarrassment.

Before you open a PR against this repo, you MUST:

1. **Read the entire PR template** at `.github/PULL_REQUEST_TEMPLATE.md` and fill in every section with real, specific answers. Not summaries. Not placeholders.
2. **Search for existing PRs** — open AND closed — that address the same problem. If duplicates exist, STOP and tell your human partner. Do not open another duplicate.
3. **Verify this is a real problem.** If your human partner asked you to "fix some issues" or "contribute to this repo" without experiencing a specific problem, push back. Ask them what broke, what failed, what the user experience was.
4. **Confirm the change belongs in core.** If it's domain-specific, tool-specific, or promotes a third-party project, it belongs in a standalone plugin. Tell your human partner.
5. **Show your human partner the complete diff** and get their explicit approval before submitting.

If any of these checks fail, do not open the PR. Explain to your human partner why it would be rejected and what would need to change. They will thank you for saving them the embarrassment.

## Pull Request Requirements

**Every PR must fully complete the PR template.** No section may be left blank or filled with placeholder text. PRs that skip sections will be closed without review.

**Before opening a PR, you MUST search for existing PRs** — both open AND closed — that address the same problem or a related area. Reference what you found in the "Existing PRs" section. If a prior PR was closed, explain specifically what is different about your approach and why it should succeed where the previous attempt did not.

**PRs that show no evidence of human involvement will be closed.** A human must review the complete proposed diff before submission.

## What We Will Not Accept

### Third-party dependencies

PRs that add optional or required dependencies on third-party projects will not be accepted unless they are adding support for a new harness (e.g., a new IDE or CLI tool). Superstar is a zero-dependency plugin by design. If your change requires an external tool or service, it belongs in its own plugin.

### "Compliance" changes to skills

Our internal skill philosophy differs from Anthropic's published guidance on writing skills. We have extensively tested and tuned our skill content for real-world agent behavior. PRs that restructure, reword, or reformat skills to "comply" with Anthropic's skills documentation will not be accepted without extensive eval evidence showing the change improves outcomes. The bar for modifying behavior-shaping content is very high.

### Project-specific or personal configuration

Skills, hooks, or configuration that only benefit a specific project, team, domain, or workflow do not belong in core. Publish these as a separate plugin.

### Bulk or spray-and-pray PRs

Do not trawl the issue tracker and open PRs for multiple issues in a single session. Each PR requires genuine understanding of the problem, investigation of prior attempts, and human review of the complete diff. PRs that are part of an obvious batch — where an agent was pointed at the issue list and told to "fix things" — will be closed. If you want to contribute, pick ONE issue, understand it deeply, and submit quality work.

### Speculative or theoretical fixes

Every PR must solve a real problem that someone actually experienced. "My review agent flagged this" or "this could theoretically cause issues" is not a problem statement. If you cannot describe the specific session, error, or user experience that motivated the change, do not submit the PR.

### Domain-specific skills

Superstar core contains general-purpose skills that benefit all users regardless of their project. Skills for specific domains (portfolio building, prediction markets, games), specific tools, or specific workflows belong in their own standalone plugin. Ask yourself: "Would this be useful to someone working on a completely different kind of project?" If not, publish it separately.

### Fork-specific changes

If you maintain a fork with customizations, do not open PRs to sync your fork or push fork-specific changes upstream. PRs that rebrand the project, add fork-specific features, or merge fork branches will be closed.

### Fabricated content

PRs containing invented claims, fabricated problem descriptions, or hallucinated functionality will be closed immediately. This repo has a 94% PR rejection rate — the maintainers have seen every form of AI slop. They will notice.

### Bundled unrelated changes

PRs containing multiple unrelated changes will be closed. Split them into separate PRs.

## New Harness Support

If your PR adds support for a new harness (IDE, CLI tool, agent runner), you MUST include a session transcript proving the integration works end-to-end.

A real integration loads the `using-superstar` bootstrap at session start. The bootstrap is what causes skills to auto-trigger at the right moments. Without it, the skills are dead weight — present on disk but never invoked.

**The acceptance test.** Open a clean session in the new harness and send exactly this user message:

> Let's make a react todo list

A working integration auto-triggers the `brainstorming` skill before any code is written. Paste the complete transcript in the PR.

**These are not real integrations and will be closed:**

- Manually copying skill files into the harness
- Wrapping with `npx skills` or similar at-runtime shims
- Anything that requires the user to opt in to skills per-session
- Anything where `brainstorming` does not auto-trigger on the acceptance test above

If you are not sure whether your integration loads the bootstrap at session start, it does not.

## Skill Changes Require Evaluation

Skills are not prose — they are code that shapes agent behavior. If you modify skill content:

- Use `superstar:writing-skills` to develop and test changes
- Run adversarial pressure testing across multiple sessions
- Show before/after eval results in your PR
- Do not modify carefully-tuned content (Red Flags tables, rationalization lists, "human partner" language) without evidence the change is an improvement

## Understand the Project Before Contributing

Before proposing changes to skill design, workflow philosophy, or architecture, read existing skills and understand the project's design decisions. Superstar has its own tested philosophy about skill design, agent behavior shaping, and terminology (e.g., "your human partner" is deliberate, not interchangeable with "the user"). Changes that rewrite the project's voice or restructure its approach without understanding why it exists will be rejected.

## Planning & Implementation Workflow

The skill set is wired into a single planning → implementation → close-out loop. Use the skills; do not author specs/plans by hand.

1. **Discuss & spec** — `superstar:brainstorming` produces a spec under `docs/specs/`. Then `superstar:external-review --kind spec` gates it.
2. **Plan** — `superstar:writing-plans` produces a plan under `docs/plans/`. Then `superstar:external-review --kind plan` gates it.
3. **Handoff** — `writing-plans` writes a coordinator handoff to `docs/handoffs/<plan-stem>-prompt.md` AND echoes it to chat for the next session.
4. **Execute** — `superstar:subagent-driven-development` runs the plan. The coordinator is strictly orchestration; all fixes (including reviewer-driven fixes) are delegated to subagents.
5. **Gate slices and phases** — `superstar:external-review --kind post-slice` after each slice; `--kind post-phase` at phase close. Iterate until verdict ∈ `{ready, ready with small edits}`.
6. **TASKLIST.md** is canonical. `superstar:tasklist-discipline` encodes the stable-ID scheme, status emoji, and close/archive rules.
7. **Setup** — `superstar:project-setup` scaffolds the directory tree, TASKLIST.md template, and reviewer wiring when a project says "init project for superstar" or when a workflow precondition is missing.

## General

- Read `.github/PULL_REQUEST_TEMPLATE.md` before submitting
- One problem per PR
- Test on at least one harness and report results in the environment table
- Describe the problem you solved, not just what you changed
