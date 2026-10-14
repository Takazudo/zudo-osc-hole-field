# Independent resistance-analysis review

Reviewer: independent DRC workstream agent, separate from the resistance report author. Date: 2026-10-14. Scope: read-only source, retained JSON/GZIP evidence, report arithmetic, engineering interpretation and exact bindings. Disposition: no remaining findings after the corrections below. This review authorizes no execution and establishes no native, electrical, adoption or physical qualification result.

## Resolved findings

1. The first helper version read `process-cases.json` and `engineering-candidate-analysis.json` without checking an expected retained hash. These inputs directly control the barrel arithmetic and exact proposed via. The final helper binds process cases through the original attempt-5 request, whose decompressed bytes must match SHA-256 `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6`. Candidate analysis is pinned to SHA-256 `d04d7bfb7b0e1c05f48ccf6304e3e74b059797e8d5df96073636c56fa1959b08`. The compressed request is separately size/hash-indexed; its `matches_retained_binding: false` describes that compressed-file index, not absence of the independently checked original-byte request binding.
2. The first helper skipped the In4 tap while checking leaf contacts, without positively requiring an In4 sheet exit. The final helper asserts the exact six-layer tap set, 0.3 mm finished drill, and an In4 group containing sheet material. The actual retained descriptor already satisfied those conditions; this correction strengthens reproduction against changed evidence.

## Checks independently performed

- Read the complete narrative and arithmetic helper, then checked every one of the final 28 input entries against its actual file size and SHA-256. All matched. Verified the decompressed original request digest separately.
- Checked the descriptor's TP990026 F.Cu group: only the land and named original via are present. The In4 exit group contains sheet material; other reported taps are local leaf groups. This supports a local single-barrel transfer branch, not a claim that all board current crosses it.
- Independently recomputed the 1.224 mm axial-barrel estimates: nominal 1.405159974 mΩ, thin sensitivity 2.890664489 mΩ, legacy conditional 1.102899682 mΩ. Two equal barrels at equal end potentials halve only that barrel term; thin sensitivity remains 1.445332244 mΩ, above the 1 mΩ rail allowance even before other local terms.
- Verified the reported nominal class-energy fractions, including KA +12V barrel fraction 0.665193683 and +5V inner-copper fractions KA 0.775583881 / KB 0.972284142. These are simultaneous-load class energies, not object-level driving-point attribution.
- Verified the largest reported same-pad loaded return-removal delta, 0.471430059 mΩ, for KB pad `448df9e2-d06c-5225-b7b4-624a2e687b34`, thin sensitivity, remove-W5-W6.
- Checked the 1,536-row CSV, 302 distinct loaded-pad claim, ranking fields and exact service/mapping distinctions against the source/report structure. No package-current spreading or doubled package injection is introduced.
- Confirmed the retained numerical limit headroom is about 0.28005%, and the report does not transfer numerical PASS to changed inputs or platforms.

The author's final helper execution passed in approximately 0.403 seconds; that execution is author verification, not an independent rerun. This reviewer independently read and recomputed the checks above without running the output-writing helper, loading pickles, generating geometry or launching a solver/native process.

## Engineering scope assessment

The prioritized one-via TP990026 proposal identifies a demonstrated local transfer resistance with dimensions and conditional arithmetic. It explicitly retains the separate equipotential source lands, unknown object-level dominance, plane spreading, face/cap/contact losses and possible antipad collateral effects. It is not claimed to solve the highest +5V failures or establish whole-path compliance. Seven-via and long-B negative evidence remain distinct. Shared 1 mΩ rail / 0.5 mΩ AGND allowances, omitted source/load/return costs, incomplete load mapping, native enumeration and physical qualification remain open. These limitations are appropriate.

## Reviewed artifact SHA-256

| File | SHA-256 |
| --- | --- |
| `resistance-report.py.txt` | `ab8c754500f8da49a6b92d6b32db5b30b82dbf8f3ba35c7cc97472ddb5fa85a4` |
| `resistance-analysis.json` | `4a9f0dc7b4f15521595fa10e03fe650d2d401279246b32a7c5c7eb3a4b5d7aaf` |
| `resistance-analysis.md` | `2546e1c8afcbeda13269dd07ed62891450d08bd704c59204812c0e06e1aaa7fc` |
| `resistance-loaded-ranking.csv` | `4e34c74c8684db4b034e75186d693733b722db4f50839c4d632f629aac53ac41` |

## Publication normalization addendum

Independently compared the final publication correction against commit `afe00e6c`. The helper changes only `csv.DictWriter` to explicitly use `lineterminator='\n'`. The new CSV is byte-for-byte equal to the previously reviewed CSV after CRLF-to-LF replacement; all 1,536 parsed records are identical. `resistance-analysis.json` remains byte-identical. Every updated artifact-index size/hash matches its file. No engineering value, input binding or conclusion changed; no native/production work was performed. The earlier hashes above remain the historical reviewed artifact identities.

Current normalized publication hashes:

| File | SHA-256 |
| --- | --- |
| `resistance-report.py.txt` | `7f373680504b8bc4145c19a1995b7e308722fe7cf9922debadbe0dd9241a8a74` |
| `resistance-loaded-ranking.csv` | `860bc111aee1999a49a52e491f649666e7373f50a79bd567b6cf2e5586f03867` |
