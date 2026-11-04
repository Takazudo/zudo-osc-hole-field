# OSC2: K power/return small-scale comparison

Status: three bounded trials on isolated copies of an unvalidated draft. Nothing
was promoted, no file under `boards/` changed, and no fabrication output exists.
Electrical, thermal and physical qualification are NOT RUN.

## Recommendation: route ±12 V by plane escapes first, then +5 V trunks, then guarded links for the remainder

All three hypotheses lowered open edges without splitting a connected pad group
and without a new listed warning. They are complementary, not competing: H1 only
touches ±12 V, H2 only +5 V, and H3 is the combined, guarded form of both.

The next K routing step should be one sequenced pilot on K3409:

1. H1 plane escapes for every ±12 V supply pin (per-pin vias into In4/In3, shortest
   decoupling and return path, no new inner-layer rail copper).
2. H2 +5 V trunks (+5 V has no plane, so its 13 clusters need links).
3. The H3 guarded rail-escapes only on whatever ±12 V is still open after step 1.

Each step stays a separate native-checked stage so a failure keeps the earlier gain.
The remaining 23 supply pins that no trial reached need the local structural change
described below, not a longer search.

Adoption is not yet possible for any candidate: see "Complete warning evidence" below.

## Starting point (same for every trial)

| Item | Value |
| --- | --- |
| Adopted board | `boards/osc-core/osc-core.kicad_pcb`, `dda33a25479c9993f71e33d49129cf16414828b3dd2083b6d4f91a65421c728c` (unchanged on `main` 702b447) |
| Native state | 3409 open edges: +12 V 26, −12 V 25, +5 V 12, AGND 22, other signals 3324; 0 errors, 0 parity |
| Island signature | `c9c6561f…2d39c98`, equal to OSC1's three-pass record in `boards/osc-core/reports/routing.json` |
| Layers | F.Cu and B.Cu AGND pours, In1 AGND plane, In2 signals, In3 −12 V fill plus signals, In4 +12 V plane. +5 V has no plane |
| Tool | KiCad 10.0.6 through `scripts/kicad/run.sh`, pinned image |

What the open rail edges are, from the native islands (`baseline.json`):

- **±12 V:** 24 op-amp/TMUX supply pins stranded as single pads (OPA4197, OPA4196,
  TMUX6112 V+ and V−), plus one 95-object −12 V copper island of 10 pads
  (U4239–U4245 V− and C4259–C4271) that the In3 fill does not join.
- **+5 V:** 13 routed clusters. The largest gaps are 19.6 mm and 19.7 mm (two
  west-side clusters), 7.7–10.1 mm for three others.
- **AGND:** 22 stranded pads. No trial targets AGND; each was required not to
  disconnect any of it.

## Trials

Each trial is one stage spec handed unchanged to `scripts/pcbgen/route_jack_grid.py`
(`stage()`, `stitched()`, `complete_gate()`); `trial.py` imports that driver and
does not edit it. Inputs, kept copper and limits are recorded in each receipt.

| | H1 plane escapes | H2 +5 V trunks | H3 guarded rail-escapes |
| --- | --- | --- | --- |
| Changes | Through-via escapes from stranded ±12 V into In4/In3 | +5 V island links, 0.25 mm, 24 mm windows | The rejected `rail-escapes` spec with the AGND split guard (`agnd_guard`) |
| Keeps | All copper, no rip-up, no pour | All copper, no rip-up, no pour | All copper, no rip-up |
| New copper | 28 vias, 47 mm (F 16, B 31) | 5 vias, 109 mm (In2 99, In3 8, B 2) | 8 vias, 276 mm (In2 198, F 43, B 28, In3 8) |
| Open edges | 3409 → **3381** | 3409 → **3401** | 3409 → **3365** |
| +12 V / −12 V / +5 V | 12 / 11 / 12 | 26 / 25 / 4 | 8 / 7 / 4 |
| AGND open / main AGND group | 22 / 3071 pads, unchanged | 22 / 3071, unchanged | 22 / 3071, unchanged |
| Split pad groups | 0 | 0 | 0 |
| Native errors / parity | 0 / 0 | 0 / 0 | 0 / 0 |
| New listed warning identities | 0 | 0 (`track_dangling` −2) | 0 (`track_dangling` −2) |
| Culprit links dropped by the AGND guard | 2 | 0 | 1 |
| Raw `promotion_gate` | would adopt | would adopt | would adopt |
| Complete warning evidence | see below | see below | see below |

Notes:

- The earlier `rail-escapes` run reached 3359 and was rejected for splitting the
  2270-pad AGND group. H3 shows the split came from a single attributable link:
  dropping the nearest link keeps 44 of the 50 edges and splits nothing.
- H1 closes fewer ±12 V edges than H3 (23 vs 15 left), but every connection is a
  per-pin via into the plane. H3 joins some ±12 V pins by surface links, and it
  puts 198 mm of +5 V on In2, directly under the In1 AGND plane.
- None of the trials changed the other 3324 signal edges.

## Pins no trial reached: a local structural change is needed

23 ±12 V items stay open in both H1 and H3:

- The −12 V island of U4239, U4240, U4241, U4243, U4244, U4245 (pin 11) with
  C4259, C4261, C4263, C4267, C4269, C4271 (x 296–340, y 284–325 mm). The In3 fill
  around it is cut by In3 signal copper; a via escape from each pad lands in the
  island, not in the main fill. It needs one stitch from the island to the main
  −12 V copper, or the In3 signal that encloses it moved to In2.
- Single supply pins on TSSOP-14/16 parts: U4308.13, U4341.4, U4439.4/.11,
  U4540.11, U4541.4/.11, U7404.11, U7405.4/.11, and SOIC U2308.4. With a 0.65 mm
  pitch and existing escapes on both sides, no via site exists within the 3 mm
  plane window. These need a local rip-up of the blocking signal escapes (the
  `repair` stage family) or a decoupling capacitor move to free a via site.

This is a bounded statement: it covers the 0.25 mm rail width, 0.05 mm raster and
3 mm plane window used here. It is not a proof that no route exists.

## Precision returns

No trial changed AGND membership: 22 open AGND edges and a 3071-pad main group
before and after, with no AGND pad leaving the main group. H1 adds no copper on
In2, the layer next to the In1 AGND plane. H2 and H3 add 99 mm and 198 mm of +5 V
on In2. Coupling of that +5 V copper to precision signals and its current capacity
(OSC contract +5 V: 0.3 A continuous, 0.4 A for 20 ms) are NOT RUN; a narrow inner
trunk between clusters can carry a share of the cluster current that this
comparison did not compute.

## Complete warning evidence

Both K reports cap `silk_over_copper` and `silk_overlap` at 199, so the mandatory
gate needs source-bound complete evidence before any adoption.

- H1: the first audit was killed by the kernel (exit 137, out of memory) while
  three trials ran at once on a 15 GiB host. The gate rejected it as incomplete
  evidence, which is the intended fail-closed result. It is being rerun alone.
- H2 and H3: audits were still running when the time limit or a container restart
  ended them; they are being rerun one at a time.

Until a trial's receipt shows `COMPLETE: source-bound native evidence`, its raw
gate result is not an adoption decision.

## In2/In3 dedicated planes were not tried

In2 has 32,546 and In3 14,265 signal segments on K3409. Making either a power
plane would move tens of thousands of segments. That is a separate change that
needs its own impact count first, as the review says.

## Files

| File | Content |
| --- | --- |
| `trial.py` | Trial driver; `--resume` gates a verified candidate that an interrupted run left behind |
| `baseline.json` | K3409 native summary used by every trial |
| `h1-plane-escapes.json`, `h2-5v-trunks.json`, `h3-escapes-split-repair.json` | Trial receipts (spec, keeps, limits, native counts, gate result, timing) |
| `*-copper.json` | Copper delta of each candidate against K3409, for replay |

Limits per trial: 150–180 min wall clock, one native check settled by three equal
refills (at most six), at most eight drop-and-retry passes. A trial is not
repeated with unchanged inputs; the reruns only redo the evidence step that a
restart or the memory limit interrupted.
