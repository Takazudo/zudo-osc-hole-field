# Consolidated evidence and qualification update to ENGINE-SOURCE-REVIEW.md

Requested by coordinator review `osc-moya-engine-evidence-review-a24487dd`.
The review (3e995b18...) and all earlier artifacts are unchanged; this note
qualifies them. No native work, no new retrieval of source files; two public
GitLab API reads were added for commit resolution (recorded below).

## 1. Windows-readable evidence copies (new flat directory)

`C:\Users\takaz\Dropbox\cclogs\zudo-osc-hole-field\osc-local-wsl\derive-run-4-failed-engine-evidence\`
holds ordinary file copies (no subdirectories, no links) of the cited sources:
`pcbnew_zone_filler.cpp`, `pcbnew_zone_filler.h`, `pcbnew_zone_settings.h`,
`pcbnew_zone.cpp`, the s-expression parser and writer, `connectivity_algo.cpp`,
`connectivity_items.h/.cpp`, `pcbnew_python_swig_zone.i`, the retrieval log, the
full 18-file retrieval hash list, the three kicad-cli-docker files, the two API
responses and this note, with `SHA256SUMS`. The per-file hashes equal those in
the review's table (checked for every copied file against the retrieval list).

## 2. Resolved commits (public GitLab API, read-only)

- `https://gitlab.com/api/v4/projects/kicad%2Fcode%2Fkicad/repository/tags/10.0.6`
  (HTTP 200, 2026-10-23T07:42:21Z): tag `10.0.6` is an annotated tag object
  `e757247bdec054f139487cc5c63ce6a5e76f7432` pointing at commit
  `caf7377e9cb6fa1535ec3596dcb8c99bf44a996e` ("Tag stable version 10.0.6.",
  2026-08-28T14:01:37-04:00). The raw files retrieved at `/-/raw/10.0.6/` are
  therefore the tree of that commit.
- `.../projects/kicad%2Fkicad-ci%2Fkicad-cli-docker/repository/branches/main`
  (HTTP 301 then 200 after one redirect, 07:43:03Z): `main` is at
  `131ab51f246671f73ce4be97d13a71fcb54d6795` ("Add option to skip qa",
  2026-09-22T08:49:14-04:00 = 12:49Z), which precedes the pinned image's creation
  time 2026-09-22T14:31:54Z by about 1.7 h, and no later commit exists on `main`.
  So the `Dockerfile.10.0-stable` read here is the revision that was `main` at
  image build time if the image was built from `main`.
- What this does and does not establish: the recipe's release path clones
  `-b $KICAD_VERSION` from the repository whose tag 10.0.6 resolves to commit
  caf7377e; the pinned image reports 10.0.6 at runtime. The image's own build
  (which pipeline run, which Dockerfile revision, which compiler) is not recorded
  in the image or in retained metadata. Source-to-binary correspondence is
  supported, not proven; every engine statement below is conditional on it.

## 3. The pair-specific inference, with the evidence it rests on

Saved facts (run 3, derived copy 4a55e0c1..., zone.json `reloaded` phase):

| item | value | source |
| --- | --- | --- |
| U1105.12 pad | footprint `zudo-osc-hole-field:SOIC-16_3.9x9.9mm_P1.27mm`, `(attr smd)`, on F.Cu; pad `smd roundrect`, size 1.95 x 0.6, `(layers "F.Cu" "F.Mask" "F.Paste")`, net AGND, uuid 608c587b-... | frozen board text |
| C1111.2 pad | footprint `C0603`, `(attr smd)`, on F.Cu; pad `smd rect` 0.8 x 0.9, `(layers "F.Cu" "F.Mask" "F.Paste")`, net AGND, uuid 6e370474-... | frozen board text |
| cluster of U1105.12 (`cluster_b`) | size 2: 1 PAD (U1105.12), 1 ZONE (601e02b2, F.Cu); layers {F.Cu: 2}; vias 0 (not truncated); tracks 0; other pads 0 | zone.json |
| cluster of C1111.2 (`cluster_a`) | size 558: 447 PAD, 85 PCB_TRACK, 25 PCB_VIA, 1 ZONE; layers B.Cu 140 / F.Cu 448 / In1-In4 30 each | zone.json |
| F.Cu outline holding U1105.12 | outline 177, 75 points, 3.30 mm2, no via centre and no other pad inside | independent review (REVIEW-2) |
| AGND through-hole pads on the board | 5 in total (U6101.2/.6/.8 and two more), nearest 212 mm from U1105.12 | frozen board text, static scan |
| AGND vias | 177, all `(layers "F.Cu" "B.Cu")` through vias; none inside or adjacent to outline 177 | frozen board text; REVIEW-2 |

Inference, stated conditionally: if (a) the F.Cu AGND fill geometry of the parent
is preserved unchanged by a later `Fill` that does not select the F.Cu zone, which
the tagged source supports (zone_filler.cpp: only `aZones` are un-filled and
written, lines 717-741, 799-813, 1037-1265) but which has not been observed on
this board, and (b) the pinned binaries behave as the tag-10.0.6 source read here,
then no fill of B.Cu or In1.Cu can join U1105.12's cluster: the connectivity graph
joins items only through copper overlap on a shared layer or through vias and
multilayer pads (connectivity_algo.cpp:823-990, items built per layer at
500-523), the pad exists on F.Cu only, its outline touches no via, track, other
pad or through-hole pad, and the nearest AGND through-hole pad is 212 mm away. Under
those conditions the pair would stay open after any fill of the remaining AGND
zones, in either order. This is an inference from saved partial-fill data and
source reading, not an observed native classification; the recorded class stays
`UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN` until the oracle produces a result.

## 4. Island removal wording reconciled

"ALWAYS deletes every orphaned outline" in the review is too broad. Per
zone_filler.cpp:956-1035 the sequence is: (i) for each selected zone and layer,
if every outline on that layer is isolated, the layer is recorded as initially
fully isolated (973-986); (ii) if that holds for all of the zone's layers, the
zone is skipped entirely and its outlines are preserved as-is (988-989); (iii)
otherwise, on each layer with isolated outlines, mode ALWAYS deletes each isolated
outline (1013-1016), mode AREA deletes those below the minimum area (1018-1021),
and the rest are flagged as islands (1023-1025). The iterative refill then
repeats the check on layers that changed (1269-1330) and keeps a layer whose
outlines are all still islands (1292-1300). Consequence for the order question:
in a sequential run the exception can also preserve a whole layer of islands
that a batched run, with more copper present, would partly connect and partly
delete; the direction of the difference is therefore not one-sided, and the
review's "deleted in sequential, kept in batched" example is one of the
possible divergences, not the only one.

## 5. Withdrawn and retained statements

- Withdrawn: "two single-zone chained runs would be sufficient for this pair's
  question" as a recommendation basis. Any native run needs its own concrete
  proposal and authorization; this note recommends none, and no grant is
  requested.
- Retained: the class `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN`; the consumed
  status of both grants; the minimal three-order comparison experiment as an
  unapproved proposal only.
- Remaining uncertainties: source-to-binary correspondence (section 2);
  unobserved preservation of the parent's F.Cu geometry on this board; whether
  order-dependent islands occur elsewhere on the board; any runtime.
