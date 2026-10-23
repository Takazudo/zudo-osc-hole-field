# Correction note to TIMEOUT-ANALYSIS.md (original left unchanged, hash 4d9d5c52...)

Requested by coordinator review `osc-moya-timeout-analysis-review-7a38493c`.
Source-only; no native work. Where the original stated more than the evidence
supports, this note replaces the statement.

1. **Same-shape rerun.** The original said a rerun of the same shape "would only
   reproduce the cap". That is not supported: single-zone fills of the same zone
   on the same input took 150.8 s once and more than 260 s once (derive runs 3 and
   2), so the outcome of a same-shape rerun is uncertain. Its diagnostic value
   would be limited either way, because the telemetry still could not apportion
   the time, but it is not an inevitable timeout.

2. **What the wrapper proves about a split, and what it does not.** The wrapper
   supports chaining as bookkeeping: manifests record parent and ancestor zones,
   reuse checks recompute hashes and ownership, the payload refuses to refill a
   selected zone that is already filled and requires the input's filled zones to
   equal the declared parent set (`osc_derived_fill_payload.py:147-149`,
   `osc_derived_fill.py` `manifest_identity` / `verify_derived`). The wrapper also
   checks, after each fill, that the non-selected zones' fill counts are
   unchanged (`osc_derived_fill_payload.py`, "nonselected native fill changed").
   None of this shows that the engine preserves prior filled geometry during a
   selective fill: every completed derive run so far started from the unfilled
   source, so that check has never been exercised on an input that carried a
   fill cache; the one chained attempt (run 4) did not reach it. It also does not
   show that a sequential fill of two zones equals a batched fill of both. The
   original's phrases "the one cross-layer coupling", "identical" and the implied
   guarantee that run B's classification is the intended evaluation are
   withdrawn; they are hypotheses.

3. **The U1105.12 island.** The no-via observation is a partial saved-board
   observation (F.Cu AGND filled only, on a disposable copy). It is not proof that
   the full-net fill leaves the pad open, and it does not make the split question
   immaterial.

4. **Recommendation for now.** Retain `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN`.
   Do not request two single-zone runs solely to change the classification while
   sequential validity is unresolved.

5. **Exactly what would need confirming before a split proposal could be ready**
   (none of it is available from accessible source or saved traces; each needs
   either engine source or documentation, or a controlled native comparison,
   which would be a new authorization):
   - E1: that `ZONE_FILLER::Fill(selection, false)` on a board loaded with an
     existing fill cache leaves the non-selected zones' `filled_polygon` data
     byte-identical, and uses that cached data (not a refill) wherever the engine
     consults other zones' copper. The wrapper's post-fill check would observe
     the first half on a completed chained run; the second half needs the engine.
   - E2: whether the selected zones' fill geometry depends on other layers' fill
     state at all, including the meaning of `island_removal_mode 0` for this
     KiCad build and any other cross-layer step in the filler (thermal/via
     handling, connectivity rebuild). This decides whether batched and sequential
     fills are equivalent in geometry.
   - E3: whether the connectivity clusters and the pair classification computed
     after sequential fills equal those after a batched fill; a controlled
     comparison on a small synthetic board inside the existing containment would
     settle E2/E3 empirically but is a native run.
   - R1 (reuse semantics, wrapper side, verifiable offline): that the chained
     manifest/identity bookkeeping composes over two hops (parent of a parent),
     which the offline test `test_chained_derivation_and_worker_failure` covers
     for ancestors but no native run has exercised.

Uncertainties that remain after this note: the engine facts E1-E3; the cause of
the run-2 versus run-3 variance; B.Cu's own fill time. No profile, telemetry or
package change is made under this note.
