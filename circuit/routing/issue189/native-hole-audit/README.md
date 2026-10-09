# Complete native warning evidence for the saved core ground trial

**The saved core1402 candidate is provisional, not eligible for adoption.** Canonical core remains1441. Hole and all-added-copper evidence passed; outer-zone silk classification37976003780 is still running. `reassessment.json` records the block. Earlier `reassessment-before-zone-scope.json` is retained as explicitly provisional history, not acceptance.

Native KiCad10.0.6 caps hole_to_hole, silk_overlap and silk_over_copper at199reports. The ordinary raw gate rejects1441→1402 because one old unchanged hole pair appears only in the candidate's capped report. Complete evidence must cover all affected capped domains; equal report counts alone prove nothing. Exact provider/source URLs and hashes are in `silk-scope-sources.json` and `../core-finer-ground-batch/warning-cap-sources.json`.

## Verified evidence

- Corrected hole audit37972238437,source2c3afde:9815/9853holes,128fixtures per source,1407identical UUID and geometry-object warning identities,zero new/removed. All256raw report hashes and fixture project/rule bytes independently verified; all original full-board hole identities are covered. Artifact11637606039,ZIP48c8b07dea13eeb4f2e257908e2ee49a80e460e6582e011a5d57cf8047d3e8db. `context-*.json` is authoritative.
- All382added-copper audit37975999346,sourcebacd089:344segments/38vias,zero new silk_overlap or silk_over_copper identities. Maximum80/0reports per fixture, below199. All382raw hashes/context files verified. Artifact11639436792,ZIP9a3cd7c803a956cc5d5d82c426543f3f9717b6b4994dac0620dd3e2b6c7ef5f0. `all-copper-silk-*.json` is authoritative for added copper.
- Native zone growth37975143005: unchanged metadata/outlines; F.Cu grows25.535mm²/four regions and B.Cu23.415mm²/six regions. They are not subsets of the old fill. Artifact11637879760,ZIPf676bb4b70145249e9f948df1410bc4749fbb20cc5c53aa6d44b752166b804a4. `zone-growth-*.json` establishes scope, not clean interactions.
- Read-only zone classification37976003780 compares before/after native zone/artwork pairs near the added filled regions. Complete classification and independent raw evidence validation remain pending.

Hole fixtures contain at most14round holes, bounding possible reports at182 even if native via/pad pairs are visited twice. Native DRC classifies each pair; Python only conservatively enumerates coverage. Geometry-derived keys preserve legacy equal-UUID objects at distinct positions, while fixture partitioning keeps UUIDs unambiguous. Unsupported custom constraints, nearby duplicateUUID pairs or identical duplicates fail closed. Fixture serialization restores the exact source project/rules and verifies them around native DRC.

Silk fixtures preserve exact native source artwork/context, verify rendered text and native copper geometry, and test both warning codes below their caps. The all-copper audit includes unmasked tracks because native silk_overlap also tests Cu geometry. Zone fixtures preserve the whole native filled shape and compare paired identities against conservatively selected native bounding-box artwork. Zone metadata/outline and nonrouting source objects must remain unchanged. Missing or stale evidence rejects.

`complete_native_warnings.py` validates complete raw evidence, then only appends complete native hole observations to both full-board reports. No original finding is removed or waived. The unchanged ordinary promotion gate still rejects errors, parity differences, new warnings, original-group splits or lack of strict connectivity gain. Fresh agreement and source/publication checks remain mandatory.

`route_shards.py merge --complete-native-warnings` regenerates all audits for the actual native before/after boards. The `finer-ground-complete-warnings` workflow choice is prepared but **not run**. The saved candidate may be reconsidered only after full zone classification passes; new zone warning identities require a changed proposal.

## Superseded diagnostic evidence

37966866612 failed before fixtures on ambiguous legacy UUIDs. Geometry-keyed37967430188 produced1407identities but is **invalid-context diagnostic only**: native SaveBoard replaced fixture project settings. The validator caught this before promotion. The corrected context-preserving run above supersedes it.

37968944848 failed on GetShownText API usage. 37969719809 was cancelled/superseded after discovering a missing silk category; neither passed. The38via-only run37970119956 passed its limited scope, but omits344new tracks and changed zone fills. `silk-*.json` is partial history; it cannot establish complete warning scope.

Core19run37965185751 is terminal and rejected for original AGND splits; its receipt-only commit is reconciled. No core writer is active. See `../checkpoint.md` for precise continuation, immutable board/replay hashes and current worker status.
