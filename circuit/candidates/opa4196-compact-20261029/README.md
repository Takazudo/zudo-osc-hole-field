# OPA4196 compact candidate (UNADOPTED, isolated development record)

**Status: UNADOPTED isolated development candidate. Not canonical, not validated, not a
manufacturing or order input.** Canonical schematics, PCBs, BOM, placement lock and
`decision.json` are unchanged by this directory. Nothing here is a fabrication file.

## What the candidate is

Four separate, nonadditive alternatives of the predecessor development baseline
`approved-dev-baseline-07ac1be8-20261026` (variants `UNI_ROYAL/BA1`, `UNI_ROYAL/RevP`,
`YAGEO/BA1`, `YAGEO/RevP`). In each, U110/U210 (sample_hold, H1/H2) change from
`TL074HIDR` (LCSC C2878713) to `OPA4196IDR` (LCSC C2057385). Pins, nets, footprints
(`SOIC-14_3.9x8.7mm_P1.27mm`, sha256 `d686d259…2337`) and row counts are unchanged.
Unit 1 is the `magnitude_indicator` bridge driver; units 2–4 are grounded unused
followers. Exactly five files change per variant:

- `candidate/rendered/variant/sheets/sample_hold.kicad_sch`
- `candidate/source-records/candidate-bom.csv`
- `candidate/source-records/candidate-pin-map.csv`
- `views/source-facts.csv`
- `views/unadopted-procurement-candidate.csv`

Never apply more than one patch to one tree.

## Provenance identities (not GitHub commits)

| Identity | Meaning |
| --- | --- |
| `213e612be53756e6c9efbb52e1c9954e7212e041` | local proposal commit; proposal ZIP `e332aeec…5f78` |
| `5a2d02f4805ee1d5b3c5b22c0be58440f3015775` | local applied-overlay commit (owner WSL) |
| `a4ccc6cbbc6d0fb1eb04bf9abfc72c6b40299fdd` | local assembly-review commit, see `../../proposals/opa4196-assembly-review-20261029/` |

These are provenance labels recorded by the earlier sessions. They are not claimed to
be reachable from GitHub, and this directory is not a copy of those commits.

## Contents

| Path | Origin |
| --- | --- |
| `patches/*.patch`, `patches/checks.json` | compact-application packet (`osc-opa4196-compact-application-20261029.zip`, sha256 `8c3d7359…b70c`); byte-identical to the proposal packet |
| `cloud-application-receipt.json` | full predecessor and successor inventories of all 466 files |
| `receipts/member-hashes.json`, `receipts/safety-check.json`, `receipts/APPLICATION-HANDOFF.txt` | same packet (HANDOFF.txt renamed) |
| `receipts/opa-overlay-receipt.json` | handoff receipt binding the 20 before/proposed hashes |
| `receipts/cloud-reconstruction-receipt-20261031.json` | independent cloud reconstruction, 2026-10-31: all four PASS |
| `tools/apply_isolated.py` | preserved original application script (inspected, not executed in the cloud) |
| `tools/osc_reconstruct.py` | independent re-implementation used for the 2026-10-31 reconstruction |
| `tools/verify_record.py` | offline consistency check of this record |
| `review/` | 2026-10-31 technical review (model screen, land/assembly evaluation) |

The predecessor trees are **not** duplicated here. They come from the handoff source
archive `OSC-current-source-four-variants.zip`, sha256
`c1983dd86f7cc9c8a42d80fac61cc000ab68547c5d012608c5a164c2600a3e3b`, under
`osc/approved-dev-baseline-07ac1be8-20261026/after/`.

## Reproduce

```sh
python3 circuit/candidates/opa4196-compact-20261029/tools/verify_record.py            # receipts/patches only
python3 circuit/candidates/opa4196-compact-20261029/tools/verify_record.py --base <after-dir>
python3 -I circuit/candidates/opa4196-compact-20261029/tools/osc_reconstruct.py \
  <after-dir> circuit/candidates/opa4196-compact-20261029 <new-empty-destination>
```

`osc_reconstruct.py` copies each variant to the new destination, applies its own patch
with `patch --batch --fuzz=0 -p1`, and requires the full successor inventory and all
20 proposed hashes to match. It also checks that the originals are unchanged.

## Status

| Check | Status |
| --- | --- |
| File-level reconstruction (20 changed hashes, 466-file inventories) | PASS, 2026-10-31 |
| Record consistency (`verify_record.py`, with `--base`) | PASS |
| Native ERC, netlist, BOM and footprint load of the candidate trees vs predecessors | RUN 2026-10-31: 0 new ERC violations, identical nets, only U110/U210 fields changed; see `review/` |
| DRC, fill, board | NOT RUN (no board; not authorized) |
| Analog bridge-loop behaviour | model screen only, see `review/` |
| Land pattern / assembly | evaluated, not accepted, see `review/` |
| Sourcing, JLC assembly eligibility, stock | UNVERIFIED |

Historical TL074H golden fixtures of the predecessor stay unchanged. Do not run
original-identity goldens against this candidate and then edit goldens to pass.
TLV9364 is not a substitute here.
