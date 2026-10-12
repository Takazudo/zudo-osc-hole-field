# Two-A rail projection accounting correction

The accounting is corrected; physical A/B rail projection remains blocked. No board or fixture is changed. All 40 historical rail objects and their 14 directly contacted B pads were already absent from the authenticated two-A fixture. Retaining the original shared rails in the earlier F3 screen was a conservative obstruction policy, not a validated A supply/return topology.

The complete discrete branch trace also disproves treating the 40 objects as B-exclusive merely because their immediate contacts were B pads. The 21 +5V seeds belong to the original 5,653-object discrete component reaching **38 A pads and 510 B pads**. The other 19 seeds reach seven B-only discrete components, whose plane interfaces remain coupled or unresolved. No object omission, copy, removal or adoption is authorized.

## Exact contract and branches

[projection-contract.json](projection-contract.json) assigns every exact seed a canonical, existing-fixture, future-A and future-B disposition. Future dispositions remain unresolved; B terminal obligations are preserved without asserting every old object is indispensable. Source spans are Unicode codepoint offsets into the sealed source, paired with SHA256 of the UTF-8 object text. UUIDs are supplementary because the inherited source contains duplicate UUIDs.

| Component | Net | Selected / total objects | Reached pads | Plane evidence |
| --- | --- | ---: | --- | --- |
| 0 | AGND | 4 / 4 | B: U4521.7 | One valid F.Cu contact; 13 unresolved ring-bounds records |
| 1 | −12V | 6 / 6 | B: C8234.1 | In3 ring interface unresolved |
| 2 | −12V | 1 / 3 | B: C4567.1 | In3 ring interface unresolved |
| 3 | +12V | 3 / 3 | B: Q4505.2 | In4 ring interface unresolved |
| 4 | +12V | 2 / 2 | B: C8229.1 | In4 ring interface unresolved |
| 5 | +12V | 2 / 2 | B: C8201.1 | In4 ring interface unresolved |
| 6 | +12V | 1 / 2 | B: C8237.1 | In4 ring interface unresolved |
| 7 | +5V | 21 / 5,653 | A: 38; B: 510 | No +5V zone exists |

[evidence/components.json.gz](evidence/components.json.gz) retains all 16,751 copper edges and 793 pad incidences, including exact terminal identities/owners. [reached-source-objects.json.gz](evidence/reached-source-objects.json.gz) binds all 5,675 reached source objects. [seed-dispositions.json](evidence/seed-dispositions.json) maps the 40 seeds to components. These are complete **discrete copper/pad** components; the method does not union planes or prove cut safety.

The recovered original K settled board contains five zones and 440 filled polygons. Of those rings, 151 are invalid as simple Shapely polygons. They were not repaired or treated as solid planes. The trace records one valid historical geometric contact and 19 possible interfaces based only on invalid-ring bounding boxes. Exact source-zone and settled-fill spans/hashes are retained in [zones.json](evidence/zones.json), [filled-polygon-index.json.gz](evidence/filled-polygon-index.json.gz) and [zone-contact-records.json.gz](evidence/zone-contact-records.json.gz). Valid historical contact still does not establish future candidate plane continuity. Global outline overlap is not a contact test.

## Actual fixture and genuine supply needs

Independent [full physical PCB review](evidence/physical-fixture-review.json) authenticated the 54,083,143-byte two-A PCB against the frozen route-1641 lock: SHA256 `66710513146c22f31595f794d608914fcfb8b61552c82fc5fd680f9ac4b0b978`. All top-level segments/vias were inspected; each of the four rail nets has zero tracks and zero vias. All 40 selected historical objects, all 14 B pads and their parent Refs, and all CS247 footprints are absent. The archived PCB already has five provisionally refilled zones with 520 filled polygons; none is +5V. The generator first strips rail tracks/vias and old fills, then historical native refill supplies the diagnostic fixture. These distinct stages must not be confused with accepted supply topology.

| Owned source pads | +12V | −12V | +5V | AGND |
| --- | ---: | ---: | ---: | ---: |
| A | 289 | 220 | 38 | 1,015 |
| B | 292 | 192 | 510 | 1,281 |

Both boards genuinely require all four nets. These counts include passive/header/reference contacts and are not current estimates. A's +5V consumers include O1–O5 SN74HC14 pin 14 and comparator pullups; B's nearby E5 contacts do not define A's requirement. The [feed/source review](evidence/feed-source-review.json.gz) retains exact pad identities, module responsibilities and source seals.

The 18 old K main load lands are provisionally assigned to A; B has none. CS247-KA-KB-W1…W6 proposes +12V, −12V, +5V and three AGND conductors, with paired SRC-1…6 / DST-1…6 logical pin-1 endpoints. **All 12 native terminal Refs/pads are absent.** Logical pairing, shared rail names and provisional zones confer no physical cross-board continuity. CN301/XB301 remain abstract raw-to-load source/protection boundaries without footprint bridges. Physical board current maxima and measured source capacity remain unqualified.

## Missing electrical/design decision

Freeze a candidate-specific branch, plane and return topology: exact A/B owned pads, source-component split boundaries, replacement/local copper obligations, and feed/return attachments. In particular, the mixed +5V component needs an explicit split/reconnection design; the seven B-only discrete branches need their unresolved plane context resolved before omission on A can be justified. Realize the proposed CS247 terminals with new unique Refs/pins/UUIDs, footprints and physical conductors while preserving legacy harness IDs/Refs/full pin order. Resolve upstream raw-to-load protection, physical current bounds, return/fault behavior and the existing voltage-drop budgets. Neither signal/patch returns nor net names can substitute for feeds.

Stop at that decision. No fixture correction is justified by the present evidence: the alleged removable objects are absent already, and topology-preserving future projection is unselected. Preserve the sealed diagnostic packets. This does not fix the independent U2312.7/W2-FOLD corridor obstruction, prove global F3 infeasibility, or authorize another placement/construction attempt.

## Evidence and validation

One reviewed source-only census at commit `8df5172d` completed in 23.019 seconds (23.283 parent), peak 1,039,028 KiB, within 180 seconds / 2 GiB / one worker. No native, placement, reconstruction or routing run occurred. Input files were hashed before and after; external dump/settled inputs were rehashed and their board hashes matched. The sealed full-footprint join binds 3,793 byte-identical canonical/settled footprints. Numerical contact tolerance is 1e-7 mm using saved native effective pad polygons; no fresh native geometry is claimed.

[Independent output review](evidence/independent-output-review.json) rejoined the saved graph, verified all 5,675 source spans/hashes and confirmed eight disjoint components without repeating spatial queries. [provenance.json](evidence/provenance.json) records exact recovered source/artifact members and hashes. The grid dump's absent +5V island key alone proves neither disconnection nor closure; its current reader filters out nets with at most one island and the artifact lacks an exact producer-script binding.

Run `python3 design/partition/core-split/candidates/planning/two-a-rail-projection-v1/check-contract.py` for source identity/accounting regression checks, including rejection of 13 unsafe mutations. No geometry or native rerun is part of that check. Repository `pnpm circuit:check`, `pnpm check` and the baseline verifier are recorded with final review in this packet.

Canonical JL117/JR129/K1402 and DRC/parity 0/0 remain unchanged. This source-only correction earns no original BP/AGND closure credit, architecture adoption, merge, fabrication or energization authority.
