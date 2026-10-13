# F3 static region recovery: both bounded windows excluded

The separately authorized recovery completed once in **4.393316 seconds**
(4.206302 seconds worker time), using one source worker and 90,520 KiB peak RSS.
The unchanged limits were 30 seconds and 2 GiB address space. No retry followed.
This is the second project computation overall: one retained failed attempt,
then this explicitly authorized recovery. No candidate pose or PCB was created.

The exact reviewed repair was executed from
`ac2093dea2c6419e82fd04a08f4487c1fc687c5e`, source SHA256
`1fe0f4002eeb32fd3692b8742b43146befc5bab6b16dcf3a6dce94bc75c2d3b8`.
Its code and five input seals remain in `../f3-static-region-screen/`.
That earlier packet, including failed receipt, traceback, ledger and original
execution hash, is unchanged. This sibling packet records recovery separately.

## Actual bounded conclusions

| Window | Closed translation domain (mm) | Outcome |
| --- | --- | --- |
| N-two-A [124,88,164,168] | dx=[30.25,12.18], dy=[−51.75,−78.53] | Empty containment domain |
| E-two-A [164,48,244,168] | dx=[70.25,92.18], dy=[−91.75,−78.53] | Entire domain covered by conservative forbidden regions |

At the unchanged orientation, the whole 171-part F3 courtyard bounding box is
58.07×106.78 mm. It cannot fit wholly within the northern 40×80 mm rectangle.

The eastern domain has area **289.9146 mm²**. The union of inward-conservative
forbidden regions covers the complete closed domain, with an empty geometric
difference. This checks boundary translations as well as area. The guarded upper
construction also leaves an empty clear region, but that alone is not the basis
of exclusion. The retained lower coverage is the evidence.

There are 886 retained moving-obstacle pairs: 555 fixed-courtyard pairs,
228 reservation pairs, and 103 analytic service-hole pairs. Each category's
lower union independently covers the eastern domain. These categories can
represent overlapping physical obstructions; their counts are not a sum of
independent physical failures.

The saved eight-record coverage witness uses U2306 against U6103, U6102, R6114,
C6113 and C6106; U2311 against RV6101; U2316 against JR-K-15-K-hook; and R2335
against U6103. This greedy subset is a coverage certificate, not a minimal set.
Exact record indices, identities, and lower/upper polygons are retained in
`evidence/`. Independent review recombines these saved polygons; it does not
rerun the project screen or select a pose.

## What this establishes

Under this source model, **neither previously considered rectangular window
supports a rigid whole-F3 translation at the current orientation with complete
courtyard containment**. The method accounts for same-face fixed courtyards at
0.35 mm spacing, reservation polygons, analytic service holes at their actual
radii, and the 0.30 mm courtyard allocation margin inside the actual board
outline. Both windows are inside that inset outline.

The computation uses forbidden translation sets O⊕(−M), 1 nm integer-hull input
rounding and 1 µm inner/outer guards. Floating-point GEOS union/intersection
operations remain a source numerical certificate, not a formal exact-real proof
or fresh native validation. Source and library versions were checked by the
runner. The inherited C2325/U2306 0.349999 mm source gap remains a separate rigid
invariant below the strict 0.35 mm rule; it was excluded from external coverage.

This does not exclude other regions of two-A, rotations, or placements not wholly
contained in these rectangles. It establishes neither global impossibility nor
a need for wholesale repacking or internal-copper reconstruction. No copper,
pad, drill, routing-access, zone or native eligibility is claimed.

## Stop and evidence

The authorized recovery is complete; no expanded search, candidate, routing,
native run, physical redesign, canonical change, adoption or merge follows.
There is no unresolved technical blocker in this bounded computation. Any broader
design conclusion would require a separately defined domain or changed design
constraint; neither has been executed here.

Checks and review are retained alongside the complete run output. Historical
canonical receipts remain JL117/JR129/core1402, DRC/parity 0/0; these are not fresh
native evidence. Full regeneration was not run because it invokes native work.
