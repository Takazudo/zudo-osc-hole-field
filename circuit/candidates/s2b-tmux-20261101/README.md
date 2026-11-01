# S2b TMUX7412F + TMUX6112 candidate (UNADOPTED, isolated development record)

**Status: UNADOPTED isolated development candidate. Not canonical, not validated, not a
manufacturing or order input.** The canonical specification, schematics, board projects,
partition, BOM and placement lock are unchanged by this directory. Nothing here is a
fabrication file. No DRC, zone fill or #293 fill was run. Canonical adoption needs a
separate approval.

## Decision

The user chose S2b on the decision card of 2026-11-01 04:59Z. That choice accepts a change of
the protected-switch identity in the electrical standard. In the candidate it is recorded as
decision **E13** in `project/osc-hole-field/electrical-decisions.json` and as
`protection_identity_change` in `design/standard/electrical-standard.json`. The second entry
includes the F1-F11 fault-row table, with each row's previous ADG verdict, its TMUX verdict
and its disposition.

## What the candidate is

This is one cumulative change set against predecessor commit
`60c7c3ab78cba5e2fcd81973024894510e090cfb`. It contains all of
`circuit/candidates/opa4197idr-rexact-20261031` (OPA4197IDR option B, R-exact and the JR slot
swap) and adds the following S2b changes:

1. **Input fault switches.** Each of the 98 protected inputs has one TMUX7412FRRPR
   (WQFN-16 RRP, LCSC C2982617). Channel 1 carries S1 on the jack. Channels 2-4 are tied to
   AGND, FF is not connected, and EP is tied to AGND. This is packing **ADG-2**, one package
   per input. ADG-3 quad packing is not used because TI SCDS404B section 9.4.2 says only
   that the faulted input turns off. It does not say that the other channels keep operating,
   so fault row F9 is UNKNOWN.
2. **Envelope switches.** All 12 envelope switches are TMUX6112PWR (TSSOP-16, pin 12 NC,
   logic 1 = on). Each driven SEL net has a SEL hold: a 100 kOhm RC0603FR-07100KL in series
   from the logic net, plus a BAT54S,215 clamp to AGND and +12V. That adds 36 resistors and
   36 diodes per unit. All 72 new parts are numbered after every existing part, so no
   existing designator moves.
3. **Owner bundles:** `.claude/skills/component-ti-tmux7412frrpr/` and
   `.claude/skills/component-ti-tmux6112pwr/`. Both have source bytes, located facts, pin
   maps, coverage and interactions. Each bundle has its own inventory line,
   direct-routing case, publication selection, shortlist row, pin map and CAD receipt.
4. **WQFN-16 land.** `scripts/libgen/build_s2b_switch_assets.py` generates
   `TI_RRP0016A.kicad_mod`, its WRL envelope and both symbols from drawing 4224816/A. The
   land has 16 pads of 0.6 x 0.3 mm at 0.65 mm pitch on a 3.8 mm span, a 2.6 mm thermal pad
   with 4 x 1.15 mm paste apertures, and a 0.07 mm NSMD mask. The land, solder joints and
   physical fit are NEEDS BENCH.
5. **Rail data.** The candidate adds two rows to `rail-budget-preliminary.json`, using the
   125 C maxima of SCDS404B / SCDS383F. With the ADG5412F loads removed, the computed
   minimum continuous +12V falls from 1700 to 1600 mA, and the candidate
   `supply-architecture-input.json` declares 1600. The PD-facing power-contract text under
   `design/architecture-278/` still says 1700. Nothing is asked of PD.

## Contents

- `patches/source.patch` is the cumulative text diff of the 98 source files from the
  predecessor commit.
- `receipts/application-receipt.json` lists the 263 changed files with their before and
  after sha256 and their kind: source, generated or retained-source (the two TI PDFs).
- `receipts/checks.json` holds the phase-18 scratch results, the costs basis and the open
  items.
- `tools/reproduce.sh` gives the generation order in a disposable worktree.
- `tools/verify_record.py` checks file identity only.

## Reproduce

```sh
git worktree add --detach <wt> 60c7c3ab78cba5e2fcd81973024894510e090cfb
ln -s <main-repo>/node_modules <wt>/node_modules   # remove before any export
bash circuit/candidates/s2b-tmux-20261101/tools/reproduce.sh <wt> circuit/candidates/s2b-tmux-20261101 <main-repo>
python3 circuit/candidates/s2b-tmux-20261101/tools/verify_record.py --tree <wt>
```

`reproduce.sh` reads the main repository's ignored `.circuit-cache/sources` and checks the
sha256 of both TI PDFs. It never writes to the main repository.

## Known open results

- `scripts/checks/test_routing_placement_translations.py` FAILS. The WQFN reflow puts
  D4515 and R4507 inside RB4413's recorded issue189 source slot on JR. No same-footprint
  swap restores that exact slot. A TSSOP-sized courtyard reservation was tried, and it broke
  the floorplan bypass proximity check (216 errors), so it was reverted.
- The historical-stage test bindings fail as they do on the predecessor record.
  `test_mult_common_board` goes from 1 failure to 2.
- `test_ground_escape`: NOT RUN (shapely missing).
- An independent rebuild with `reproduce.sh` and `verify_record.py --tree` against a fresh
  tree was NOT RUN.
