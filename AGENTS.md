# Agent instructions

Read [circuit/WORKFLOW.md](circuit/WORKFLOW.md) first. It is the canonical workflow for this circuit project; this file only points to it.

For ongoing WSL development coordination, also read the current operating agreement
and recovery checkpoint in [the existing joined-feed work note](design/partition/core-split/candidates/planning/joined-feed-construction-v2/WORK.md#ongoing-wsl-coordination--2026-10-14).
Continue authorized planning and development locally across increments; resolve
genuine owner decisions with the user in this WSL session. Apply the later
[explicit E16 local delegation](design/partition/core-split/candidates/planning/joined-feed-construction-v2/WORK.md#owner-decision-single-owner-local-delegation--2026-10-14)
for signing and exact computational admission; ordinary planning delegation alone
grants neither. Integration ownership and merge permission remain excluded.

- Exact-component evidence lives in the owner bundles under `.claude/skills/component-*/`, indexed by `.claude/skills/component-spec-audit/references/inventory.json`. Cross-component rules live in `.claude/skills/circuit-spec-integration/references/rules.json`.
- Run `pnpm circuit:check` before editing and again after.
- Never hand-edit the generated pages under `doc/src/content/docs/components/`; change the evidence and run `pnpm circuit:generate`.

## zudo-osc-hole-field project rules

Follow these eight rules across project work:

1. **Keep hardware positions fixed.** Use `design/grid/placements.lock.json`, derived from the R21 grid, for panel hardware coordinates. Report fit conflicts with dimensions; do not move jacks or controls. Keep generated geometry separate from owner styling.
2. **Report status honestly.** Every schematic and PCB is an unvalidated draft. Report unavailable checks as `NOT RUN` with the reason. Never create fabrication order files or call a draft validated, qualified, or released.
3. **Treat specifications as the source.** Edit specifications or generators, then regenerate. Re-run regeneration after merges and regenerate conflicts in aggregate outputs instead of hand-merging. Start each sub-issue with `bash scripts/checks/regen-all.sh`; commit any tracked regeneration before task edits.
4. **Use one KiCad oracle.** Run KiCad 10.0.6 through `scripts/kicad/run.sh`, using the pinned image. A missing oracle is a failure, not a skip; see [scripts/kicad/README.md](scripts/kicad/README.md).
5. **Keep sibling repositories read-only.** Read them at the pinned commits recorded in the epic and never change their checkout. Use a remote or `git show` at the pinned commit when a local checkout may be stale.
6. **Take no outward actions.** Do not buy, request quotes, contact suppliers, order fabrication, deploy the site, or read or write Cloudflare credentials.
7. **Use the circuit evidence workflow.** Follow `circuit/WORKFLOW.md` for exact identities, retained evidence, integration rules, publication, and generated ownership. [scripts/schgen/README.md](scripts/schgen/README.md) documents schematic source and generation.
8. **Write project materials in English.** This includes docs, labels, comments, and commit messages.
