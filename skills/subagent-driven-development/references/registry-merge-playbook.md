# Centralized-registry merge playbook

Use this when a slice's worktree must integrate the current base branch and a
**coordinated sibling slice has already landed on a shared integration surface**
— a central registry, a parser allowlist/union, a schema or seed file, a renderer
dispatch table, a theme CSS tail, or a homepage/ordering array. These surfaces
collect *additive* entries from multiple slices, so a textual merge that keeps
only one side silently drops a sibling's feature.

This is invoked from the **integrate-current-main checkpoint** in
`[[subagent-driven-development]]`, before the post-slice external review.

## Rule: preserve both semantic additions

When base and your worktree both added to the same registry/array/union, the
merge result must contain **both** additions, not whichever side won the textual
conflict. Read both sides and reconstruct the union by hand:

1. **Identify the surface and the additions.** For each conflicting hunk, name
   what each side added (a block contract, a parser case, a schema/seed row, a
   dispatch entry, a CSS block, an ordering slot).
2. **Keep both additions.** Reassemble the registry/array/union so every sibling's
   entry survives. If two siblings added entries that must be ordered, apply the
   declared ordering; if they collide on a scarce slot (e.g. two `homepage-sort:15`),
   that is a reservation collision that should have been caught by `tasktool reserve
   add` — resolve it now by moving one side to a free value and recording why.
3. **Do not invent a merge the tool can do.** This playbook resolves *semantic*
   additive conflicts only. It does not auto-resolve genuine logic conflicts —
   escalate those.

## Rule: regenerate derived artifacts

Any file derived from the surface must be regenerated *after* the union is
correct, never hand-merged:

- checksums / lockfiles / content hashes,
- snapshot fixtures,
- generated types or generated indexes.

A hand-merged checksum is a lie; regenerate it from the merged source.

## Rule: rerun focused tests, then integrated verification

1. Rerun the **focused** parser / schema / seed tests for the surface you merged.
2. Then rerun the slice's **full** verification command, so the integrated tree
   (your work + the landed sibling) is proven green before the post-slice review.

If any focused test fails, the union was reconstructed wrong — return to "preserve
both semantic additions" before rerunning the full suite.
