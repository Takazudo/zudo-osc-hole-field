# #247 joined power feasibility follow-up

Ready for scoped coordinator review; **architecture, realized continuity and physical qualification remain BLOCKED**. Accepted K1402 stays retained. This adds executable checks and quantified constraints rather than changing production power geometry.

- Integration input/branch parent: `9e0aceda2f1d55052a8c9c03f958e8d93271a81c`.
- Topic: `agent/247-joined-power-1011`; base `integration/epic-242-core-routing`.
- Independent mechanical input: PR #270, `b3d72e107c166e472ba6fe6476d34304e807b4ad`, consumed with `git show`, never applied.
- Historical/accepted main: `65cefd41fc39e064d38319115ad96016a1c6b71c`.
- Only `design/partition/core-split/power/**` and the power research MDX are changed. Existing study outputs, mechanical proposals, boards, circuits, generators, source boundaries and fixed/non-core geometry remain unchanged.

## Concrete additions

`check.py` generates `interfaces.json`, `budget.json` and `manifest.json`. It verifies exact immutable source bytes, matches all 195 legacy harnesses / 390 endpoints and 18 main wires, binds candidate aliases/owners, compares both endpoint pin/Ref/pose records and exact K main-land sets, and gives every new wire two distinct net-matched logical terminals. Missing/duplicate feeds, coordinated wrong owners, changed Refs and duplicate routes reject. New logical IDs are not fabricated native Refs: **zero CS247 terminals exist** in current candidate placements, and no satellite main-feed land exists. Copied rail/AGND islands therefore cannot pass the end-to-end gate.

The resistor checker includes all 380 GH returns (333 powered core/front, 12 EL, 35 octave), plus 12/15 main returns for two/three. For all five mechanical alternatives it solves all-present, every one-return, each same-branch two-return, and every full branch-return removal. No patch sleeve is credited. The source-only solver uses positive resistors, rejects disconnected alternatives as a full-current bound and audits Kirchhoff residuals. `test_joined.py` has 13 analytical/mutation tests; it is not a native KiCad substitute.

Every result is conditional on the explicit source current/resistance class and a complete connected access network. The global omitted-access resistance **sum** ≤0.5mΩ is a sufficient, stronger-than-path certificate, not a proposed per-board allocation or an observed physical value. The model produces actionable residual access budgets without relaxing the existing limits. Full 4.6 A peripheral bounds deliberately remain conservative; their exceedances do not establish actual overload.

The 333-conductor powered core/front all-present subset reaches 0.48813554A in two-deep and 0.48641169A in three-deep under that conditional model. Compact bounds 0.70399040 / 0.70829497A cannot certify 0.5 A. All complete alternatives remain blocked because the 47 peripheral bounds need a supported port/access model, and geometry, actual copper/feeds and protection are missing. Fault-state arithmetic never bypasses #59.

Global-once two-section voltage drops are 26.242 / 25.816 / 19.426 mV at two 110 mm sections, unlike the earlier duplicated-copper diagnostic. +12/−12 fail 20 mV; +5 passes only this scalar screen. With two termination pairs, analog combined cut limits are 148.335 / 152.214 mm when rail and return use the same aggregate length; each section still must be ≤110 mm. KA is the abstract load-side star: no upstream AWG14 section, source/inlet realization or raw/load bridge is invented.

## Mechanical coordination

[Initial exchange](https://github.com/Takazudo/zudo-osc-hole-field/issues/246#issuecomment-6108930286) and [reconciliation](https://github.com/Takazudo/zudo-osc-hole-field/issues/246#issuecomment-6109022261) bind the mechanical lane task `01a12973-e002-77de-aeb8-856a17e8a0be`. The second comment corrects the first comment's ambiguous upstream-route wording.

All input hashes in PR #270's report match. Its continuous cardinal screen gives zero KA origins for the unchanged 91×34 mm row/corridor, 24 horizontal KB event origins, and zero cardinal outside escape rectangles. 34.6mm pitch meets 28+5+1.6 only at zero margin and does not solve KA XY. Its 40 capacitor-shift proposals are not applied. The prior 3.6 mm bare-gap deficit is retained in each original alternative; the newer source result strengthens the blocker rather than overwriting it.

The next mechanical/power contract must evidence a segmented/swept envelope or service lifecycle while retaining the six W1…W6 identities/nets, 4×4 lands / 5×5 courtyards / 6×6 reserves, ≥25.908 mm bends, ≤110 mm cuts including preparation/slack/travel, independently supported strain relief and every retained tool/loom/copper obligation. No service clearance is discarded on the basis of wire diameter alone. No complete alternative is currently admitted.

## Verification and reproduction

See `verification.json` for actual command output, elapsed time and available cumulative child peak RSS. The final focused suite has 13 tests; the original power suite has 11. Both generators, pre/post circuit validation and `pnpm check` passed. Circuit scope remains manual inventory, 68 lines, zero declared placements: **schematic/placement binding was not performed**. Independent current/return and connector reviewers found semantic/numerical gaps that were fixed and regression-tested.

```sh
# Only if the separately pinned object is absent; fetching does not apply proposals.
git fetch origin b3d72e107c166e472ba6fe6476d34304e807b4ad
python3 design/partition/core-split/power/joined/check.py --check
python3 -m unittest discover -s design/partition/core-split/power/joined -p 'test_*.py' -v
python3 design/partition/core-split/power/build.py --check
python3 -m unittest discover -s design/partition/core-split/power -p 'test_*.py' -v
pnpm circuit:check
pnpm check
```

No native job, heavy run or slot was requested. Aggregate `scripts/checks/regen-all.sh` remains NOT RUN because it writes shared outputs and enters native work without admission. Heavy CI remains deferred; `[skip ci]` prevents the default four-native-job workflow from violating the global limit. No manufacturing, energization or adoption is authorized. #57/#59/#65 remain open.

Coordinator task `01a12972-5482-766c-97c0-fb9a182940a4` owns incorporation and any later source refresh. Consume this exact head, retain G1/G2 holds and the matched-interface realization gates, and only admit native work after a reviewed, physically possible source arrangement exists. Architecture selection remains with #253.

Startup limitation: automatic approval review rejected runtime-link restoration and the read-only personal-context loader for protected home/runtime access. No workaround or profile rebuild was attempted. Repository AGENTS/workflow and relevant local component skills were read; personal runtime context remains unverified.
