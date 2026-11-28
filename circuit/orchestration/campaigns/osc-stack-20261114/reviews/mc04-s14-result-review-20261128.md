# MC04-S14 result review: ACCEPT WITH CORRECTIONS (1 blocking, 11 non-blocking)

2026-11-28. Independent review of the completed MC04-S14 study at `e9fb1184` on
`local/cloud-engineering-20261127`. The reviewer is not the executor and not the brief author. Read-only, except
for this file. No ngspice deck and no container was run. Model evidence only; every board and schematic stays an
unvalidated draft and nothing is adopted.

Reviewed: the brief Revision 3 (SHA-256 `c6904428218df07858d0ef3a604fe391be3e7c81c6a7d4615538be5160ae9ec2`,
verified), `mc04-s14-report-20261128.md`, DS-175 to DS-182, and
`scripts/stack/studies/mc04_s14_feedback_capacitor/` (`results.jsonl`, `whatif.json`, `rescore.json`,
`result.json`, `checkpoints/`, the driver and the copies).

## The study conclusion stands: no IC is unblocked, and every limit and zero-stray status matches the records

- **Limits re-derived, 0 differences.** A separate script written for this review applied Rulings S2 to S5 and the
  per-corner candidate rule to `results.jsonl` and the pinned S13 `results.jsonl`. All 13 arm W and arm G corners
  and all 10 arm R corners (A 2, C 6, D 2) give the same status, `C_lim`, lowest failing value and deciding
  criterion as `whatif.json` and `rescore.json`. The K1-to-K5-only limits also match.
- **Per-IC table.** `rescore.json` `per_ic` marks all four ICs `supported: false`. The report table matches it row
  for row: U5110 4 rows, U8409 12, U5209 7, U5210 17. No what-if, relative-form or PROVISIONAL row is counted as
  support.
- **Controls.** The report figures for P2 to P10 equal `checkpoints/arm0.json`. P4 equals the S13 record (33.1644°,
  11.9501°, 53.2807°). P5, P7 and P8 are inside the brief's tolerances against the retained figures.
- **P10 spot check, 4 decks.** The cached what-if decks of `0841e309` 16 pF loop, H-REF9 8 pF closed, `932a592b`
  50 pF closed and class G IABC high 50 pF closed each hold exactly one `Cwhatif out inm 10p` line. With that line
  removed they equal the specification deck of the same point byte for byte, `.nodeset` block included.
- **Clipping.** The clip flag agrees with the recorded swing in all 347 closed and re-score records. The four
  rescale factors (0.86, 0.875, 0.851, 0.827) equal 0.9 × (11 V − |Vq|) / peak excursion from the records, and no
  second deck clipped.
- **Arm R binding.** 152 of 152 records are bound from the cache with waveform hashes; 0 replays.
- **End checks re-run by the reviewer.** `s14.py --check`: 594 records rebuilt, 0 mismatches, both tables
  identical. `test_s14.py`: 49 tests, OK. Neither changed a tracked file, and no `.spiceinit` was left.
- **Allowed paths.** `ca187c2e..e9fb1184` adds only the report and the new study directory. No S13 file changed.
  The seven study file hashes in `result.json` equal the committed files.

## The four study fixes and the dockerd restart did not change what the brief measures

- **Fix 1 (08:05Z).** `checkpoints/discarded-arm0-try1.json` shows the stop on the non-existent path
  `…mc04-s13-result-review-20261128.md` with 0 invocations. The pinned hash is unchanged in `pins14()`.
- **Fixes 2 and 4 (08:08Z, 08:38Z).** Table builder only. `--check` reproduces both tables from the records.
- **Fix 3 (08:26Z).** The 56 discarded lines are all `outpair` points with `attempts: []`, `key: null` and
  `wall_s: 0.0`, so no deck ran. The 14 pairs re-ran in slice-02 (56 ledger lines: 48 non-G, 8 class G) with
  their time charged to the right ceiling. The final code rebuilds every slice-01 deck text to its recorded key.
- **Order change.** The non-G pairs ran after class G. Every arm had finished inside its own ceiling by then, so
  the reservation the order protects was not at risk.
- **dockerd.** P2 ran after the restart and records the pinned image ID, KiCad 10.0.6 and ngspice-44.2. Every
  guard summary lists no pinned-image container afterwards.

## Caps and ceilings were kept; two stated counts need correcting (findings 3 and 5)

| Bound | Record | Limit |
| --- | --- | --- |
| Invocations | 457 (`invocations.jsonl`, 457 lines) | 900 |
| Seeds / seed invocations | 42 / 46 | 60 / 180 |
| Replays | 0 | 200 |
| Arm W points | 129 (121 swept, 8 bracket check) | 140 |
| Output-pair decks | 56 | 64 (a count, not a stop) |
| Non-G sweep time | 989 s over both slices | 6300 s |
| Class G time | 510 s over both slices | 2700 s |
| Arm 0 | 383 s | 1200 s |

## The directory name needs no correction

The brief names `scripts/stack/studies/mc04_s14_feedback_capacitor/` twice ("How the oracle is invoked" and
"Outputs"), and DS-182 names no directory. The executor used the brief's path. The shorter name appears only in
the admission message, which is not a repository record. Reading 1 of the report already states this.

## Findings

### 1. BLOCKING: a failing Ruling 6 output pair keeps its limit as PROVISIONAL, by an unlisted reading that is not the stricter one

- **Location.** `s14.py` `whatif_table()` and `rescore_table()` (the "Ruling 6 output pair fails at C_lim"
  reason); `rescore.json` and `whatif.json` labels; report sections "What-if", "Re-score" and the per-IC table;
  report "Readings made" (no entry).
- **Defect.** Neither brief says what a failing output pair does to a row. The executor kept the limit and added
  a PROVISIONAL reason, which is the behaviour of the copied S13 code that S13 never exercised (its pairs were
  NOT RUN). STOP 6 requires the stricter reading and an entry under "Readings made"; neither was done. Ruling S2
  keeps K1 and K2 absolute at every value, and the records show these failures at `C_lim` with 100 pF on OUT:

  | Rows | `C_lim` | Phase margin | Gain margin |
  | --- | --- | --- | --- |
  | Class C `71a1a514` (7 nets) | 40 pF | 38.89° | 8.29 dB |
  | Class C `db770f45` (1 net) | 40 pF | 38.67° | 8.25 dB |
  | Class D `68dcfa21` (`/W1/C629978_W_SENSE`) | 32 pF | 38.65° | 8.47 dB |
  | Class G what-if, IABC low / high | 50 pF | 44.09° / 44.16° | passes |

  Eleven rows therefore carry a number that one ruled corner contradicts. The per-IC table shows four of their
  nets as "conditional on an owner decision": `/F3/C8c344f_W_SENSE` (U5209), `/M4A/C1c45d6_W_SENSE` and
  `/M4B/C1c45d6_W_SENSE` (U8409, U5210) and `/W1/PRE_GAIN_SUM` (U5110, U5209). S7 keeps an IC blocked by a
  failing row. The S7 conclusion does not change, because the stricter reading only adds blocking rows.
- **Required correction.** Table builder and report only; no new deck.
  1. List the reading under "Readings made" and say it is not the stricter one.
  2. Either apply the stricter reading, so that these eleven rows carry no usable limit (for example
     `NOT EVALUATED: Ruling 6 output pair fails K1/K2 at C_lim`) and count as "blocks" in the per-IC table, or
     record a design-authority ruling in `decisions.md` that a failing output pair makes a row PROVISIONAL.
  3. Change the report title and the re-score heading to match the outcome of step 2.

### 2. Non-blocking: the class A output pair failure is not reported

- **Location.** Report "Re-score", class A bullets; `rescore.json` class A `outpair`.
- **Defect.** The class A pair at 2 pF with 100 pF on OUT fails K1, K2, K3 and K4 (43.88°, 9.45 dB). The label
  is NO HEADROOM AT PAPER either way, so no row changes, but the report names pair failures only for classes C,
  D and G.
- **Required correction.** Add the class A pair result to the class A bullets.

### 3. Non-blocking: the invocation breakdown sums to 456, not 457

- **Location.** Report bounds table, row "Invocations"; `result.json` `invocations.by_kind`.
- **Defect.** The report gives "385 evaluation and rescaled, 46 seed, 25 control". The ledger holds 385 `eval`,
  1 `rescale`, 46 `seed` and 25 `control`. The three class G second decks are logged as `eval` and the class A
  second deck as `rescale`, so the kinds are also inconsistent.
- **Required correction.** State 386 evaluation and rescaled decks (382 evaluation, 4 rescaled) and note the
  ledger kind of the three class G second decks.

### 4. Non-blocking: P1 is reported as 37 pins, the record holds 35

- **Location.** Report controls table, P1; `checkpoints/arm0.json` `P1.count`; `result.json` `pinned_inputs`.
- **Defect.** Both records give 35 (23 S13 pins plus 13 named in `pins14()`, one shared). The five model hashes
  belong to P3.
- **Required correction.** State 35, or show the count that gives 37.

### 5. Non-blocking: the memory figures mix scopes, and the fingerprint is not in the report

- **Location.** Report bounds table, row "Memory"; `checkpoints/guard-*.json`.
- **Defect.** 428.8 MiB is the peak of the two sweep slices only. The lowest MemAvailable quoted (14 559.8 MiB)
  comes from the start `regen-all.sh` guard. Over all guards the peak is 995.0 MiB and the lowest MemAvailable
  is 14 445.4 MiB, both in `guard-end-regen-check.json`. All are far inside the 4 GiB budget and the 8 GiB
  floor. The brief also asks for the fingerprint in the report; it is only in `result.json`.
- **Required correction.** Give both figures per scope (study slices, and all guarded commands) and add the
  fingerprint line (4 CPU, MemAvailable 15.0 GiB at the start, no swap, 50.1 GiB free, commit `ca187c2e`).

### 6. Non-blocking: the H-REF9 rows show no S13 label, and the "exception" sentence is wrong

- **Location.** Report "What-if" table, column "S13 specification label", the two `e06fd44a` rows; first bullet
  under the table.
- **Defect.** The cells read "(S13 row)". The pinned S13 `budget.json` labels `/E2/REF9_FB` and `/E4/REF9_FB`
  FAILS AT ZERO STRAY, like every other non-G set. The sentence "H-REF9 is the exception" has no basis in the
  record.
- **Required correction.** Put FAILS AT ZERO STRAY in both cells and delete the exception sentence.

### 7. Non-blocking: "Run completed without a STOP" contradicts the study's own record

- **Location.** Report heading of the bounds section; `checkpoints/discarded-arm0-try1.json`.
- **Defect.** The driver recorded `STOP 1: input drift` on Arm 0 try 1. The cause was a study path typo and not
  drift, as the table row says, but the heading states that no STOP occurred.
- **Required correction.** Reword the heading, for example "Run completed: one STOP 1 from a study path typo
  before any deck, cleared by fix 1".

### 8. Non-blocking: fixes 2 and 3 were written while a guarded process was running, and the executed driver versions are not hashed

- **Location.** Report fix table; `result.json` `study_files`; `checkpoints/slices.jsonl`; `arm0.json` `started`.
- **Defect.** Arm 0 ran from 08:05:44Z to about 08:12:07Z and slice-01 from 08:12:23Z to 08:32:57Z. Fix 2
  (08:08Z) and fix 3 (08:26Z) fall inside those runs. `result.json` holds only the final `s14.py` hash
  (`e87f8bcd…`), so the versions that ran Arm 0 and slice-01 are not on record. This did not change a result:
  the final code rebuilds all 594 records with 0 mismatches.
- **Required correction.** Say in the fix table which process was running at each fix, and that the recorded
  hash is the final file.

### 9. Non-blocking: the U5110 sentence claims a slot-level result the study does not hold

- **Location.** Report, paragraph under the per-IC table.
- **Defect.** "This matches the expectation" and "cannot support any of its slots" are both too strong. The
  brief's best case was support for 60 of 66 slots by what-if rows. The result is worse: `/W1/C01cf3e_FB`
  (class A, 2 pF against 10.45 pF) blocks U5110 under the IC-level rule of S7. The S13 brief gives its slot
  counts as C5218 in 29 and R5268 in 24 of 66 slots; S14 has no slot-level record.
- **Required correction.** State that U5110 stays blocked under S7 at IC level, that this is below the brief's
  best case, and that the slot-level effect is not evaluated here.

### 10. Non-blocking: the relative-form rows do not state the margin used

- **Location.** Report "Re-score", class A and class D bullets.
- **Defect.** Ruling S2 asks for the zero-stray figure, the margin used and the statement that the absolute
  form gives no limit. The first and third are present. The margins (5 percentage points for K4, 1.0 dB for K3
  at the class A harness corner) are not.
- **Required correction.** Add the margins to both bullets.

### 11. Non-blocking: two more readings are not listed

- **Location.** Report "Readings made".
- **Defect.**
  - Class G what-if pairs ran at both IABC corners (8 decks). The brief counts one pair per topology at its
    deciding corner (4 decks). Both corners have the same `C_lim`, so this is the stricter reading.
  - A pair deck is judged against the zero-stray deck of the sweep at the 20 pF output stray.
- **Required correction.** Add both as numbered readings.

### 12. Non-blocking: three small figures differ from the records

- **Location.** Report class G heading; P9 row; environment note.
- **Defect.**
  - The heading says 3.7° at both IABC corners; the records give 3.65° and 3.85°.
  - P9 gives the class C margins as 0.002 to 0.01 %; the K8 margin is 0.0009 %.
  - The dockerd restart has no time and no record besides this note.
- **Required correction.** Give both class G figures, extend the P9 range to 0.0009 %, and add the restart time.

## Wording passes on every output

- The status line "MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT" is on the report, the README and
  the three JSON outputs.
- No text calls a draft validated, qualified or released, and no part is adopted.
- All nine NOT RUN items the brief names are listed with reasons.
- Every what-if row of `whatif.json` carries the 20 kHz gain and phase difference against the specification
  cell. The four E-audio and class G rows carry the note that it exceeds the 2° of K7. The arithmetic agrees:
  100 kΩ with 10 pF gives −7.16° and −0.068 dB, 59.9 kΩ gives −4.30°.

## NOT RUN by this review

- **ngspice decks, KiCad, docker.** Excluded by the review instruction; P4, P5, P7 and P8 were checked against
  the records and the retained figures, not re-simulated.
- **`regen-all.sh --check` and `pnpm circuit:check`.** Not repeated; the two end guard summaries record exit 0.
- **The three intermediate driver versions.** Not recoverable; see finding 8.
