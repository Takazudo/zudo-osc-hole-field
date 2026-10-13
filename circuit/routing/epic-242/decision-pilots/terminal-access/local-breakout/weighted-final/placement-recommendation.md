# Recommended next candidate: F3 integrator cluster with reserved access

Recommend one disposable **two-A F3 integrator-cluster placement pilot** owned by
#245, with evidence returned to #253. Begin with U2306 fixed at its current pose;
repack U2312 and C2312 toward U2306.5, preserving their complete sensitive and
bypass closure. Treat U2313/C2313 as coupled LP-integrator constraints. This is
a concrete next placement task, not an applied placement, accepted layout, or
claim that movement alone fixes the rejected weighted path. Its purpose is to
reduce the long sensitive connection and reserve end-to-end escape space before
another independently admitted routing comparison.

## Source and initial placement objective

Use `design/partition/core-split/candidates/two.json`, board `two-A`, from
`f5626849b368fb17cf11ccb729a6460dae43b4e0`; recheck its digest against the
[source snapshot](placement-source-snapshot.json) when assigned. That snapshot
contains the exact current poses, pad UUID/net identities, packages, MPN fields,
six touching sensitive groups and bypass ownership. Pilot physical coordinates
equal candidate-local coordinates plus `(100,50)` mm, without rotation/flip.

| Anchor | Current physical position | Initial disposition |
|---|---|---|
| U2306 package | `(239.84,255.08)` mm, B.Cu, 270° | Fixed anchor for this first placement pilot |
| U2306.5, BP_INT | `(240.475,252.605)` mm | Required original destination |
| U2312 package | `(212.95,245.47)` mm, B.Cu, 270° | Repack toward U2306, orient BP_INT pad toward its escape corridor |
| U2312.12, BP_INT | `(211.68,247.945)` mm | Preserve/account for existing connection to C2312.1 |
| C2312 package | `(213.39,264.46)` mm, B.Cu, 180° | Place alongside the U2312↔U2306 BP_INT connection with adjacent AGND access |
| C2312.1, BP_INT | `(214.09,264.46)` mm | Required original source; do not replace with an arbitrary witness |
| C2312.2, AGND | `(212.69,264.46)` mm | Reserve local return access; original AGND test pair remains C2338.2 → U2312.5 |
| U2313 package | `(235.18,242.58)` mm, B.Cu, 90° | Coupled constraint, initially retain if legal |
| C2313 package | `(237.96,252.14)` mm, F.Cu, 270° | Coupled LP_INT constraint, initially retain if legal |

Placement design target: bring both C2312.1 and U2312.12 within **10 mm** of
U2306.5 and provide an explicitly checked full-width connection/return corridor.
The 10 mm value is a proposed measurable placement objective, not a native rule
or a proven feasible pose. Start the movable integrator bodies in the existing
hotspot envelope `[220,236,246,271]` mm (`xmin,ymin,xmax,ymax`); this is a search
preference, not proof of vacant area, a keepout waiver, or a restriction on
preserving the rest of the sensitive group. Do not silently expand to a new
module or displace other groups if that objective cannot fit.

Reserve actual 0.3 mm signal geometry plus 0.25 mm clearance on both sides
(0.8 mm total straight corridor envelope before corners/pads), existing AGND
return access, and any 0.6/0.3 mm through-via landing on every copper layer.
For every pair of proposed via centers, retain at least **0.700001 mm** separation
under the existing hole rule, plus all other via/copper/SMD checks. Model endpoint
attachment vias together with interior routing vias before accepting a corridor;
the final weighted path failed precisely this combined check. A one-site witness
or separate legal endpoint is insufficient.

## Complete minimum scope and ownership

The sensitive-net/bypass closure from `{C2312,U2306,U2312}` contains 24 refs:

```text
C2312 C2313 C2325 C2326 C2337 C2338 C2339 C2340
R2345 R2346 R2347 R2348 R2358 R2359 R2360 R2361
R2380 R2381 R2382 R2383 R2384 U2306 U2312 U2313
```

Preserve BP_INT, LP_INT, FREQ_SUM, HP_SUM, RES_CONTROL_INV and RES_CONTROL_SUM
as complete local groups. Keep C2325/C2326 with U2306, C2337/C2338 with U2312,
and C2339/C2340 with U2313. These refs have no intersection with the candidate's
mechanical_refs. Membership in this scope does not require moving every ref;
unchanged members and their copper remain fixed constraints. Preserve the wider
F3/FILTER_CORE:F3 and F3/IO_CORE:F3 island contracts and all local/crossing nets.

The local region is occupied. Do not use a blind U2312-only or capacitor-only
translation. Check all same-face transformed courtyards and their full 0.35 mm
separation, board-edge allocation of 0.30 mm, service/header/trim corridors and
fixed mechanical objects. If neighboring groups must move, first return a
source-derived expanded sensitive/bypass closure and explicit copper impact to
the coordinator; that is a changed placement scope, not permission to erase
obstacles. No trial pose is represented here as collision-free.

#245 owns `design/partition/core-split/candidates/**` and its assigned generator;
the integration coordinator owns this handoff and shared-generator serialization.
No new session, placement implementation, candidate data edit or lane assignment
is performed by this closeout. The fixed panel, harness IDs/Refs/full pin order,
circuit intent, noncore poses, board count and six-layer rules stay unchanged.

## Required handoff before another routing/native decision

1. Emit a new candidate-only pose epoch with exact old/new transforms and hashes,
   deterministic whole-group membership, original pad/net/UUID identity and
   same-face polygon checks. Retain failed placement results. Do not overwrite
   the frozen two-A input or label it as the prior matched experiment.
2. Inventory all copper touched by moved pads as exact original objects with
   preserve/replay/invalidate disposition, including the existing
   C2312.1↔U2312.12 connection. Preserve reusable copper and leave canonical
   accepted boards unchanged. No implicit cuts, wholesale discard, or adoption.
3. Show complete BP_INT and AGND terminal access and combined route/attachment
   geometry, including pairwise new-via spacing and cumulative original-baseline
   fill screening. Keep all four original demands explicit, including the
   original AGND pair C2338.2 → U2312.5; C2312.2 access does not replace it. Full signal closure
   cannot substitute for the unresolved return or positive/negative rails.
4. U2309's rail starts remain blocked by its own adjacent package pads. Whole
   package translation does not change this internal geometry. Retain this as
   a separate access blocker requiring a source-justified local escape method;
   do not promise the integrator placement fixes it or change package/pin intent.
5. Return source review and geometry evidence to #253 before requesting a new
   bounded comparison. Native KiCad10.0.6, full-warning/eligibility/DRC/parity
   and original-group gates remain NOT RUN until separately admitted. Keep the
   global limit of two workers, 6 GiB each / 12 GiB aggregate / 2 GiB free and
   existing timeguards. No native slot is reserved by this recommendation.

If the bounded placement objective cannot be met while preserving these groups
and obstacles, report the exact occupied regions and required expanded scope
under #245/#253. Do not return to the retired unchanged-placement search or
silently choose another architecture. Epic #242 remains open and unselected.
