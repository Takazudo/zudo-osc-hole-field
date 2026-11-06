# Stage20 — source-only reconciliation of retained XML

The unchanged KiCad 10.0.6 XML passes the corrected logical comparator for all
118 references, 561 physical pins, 154 source unit UUIDs and 196 explicit singleton
NCs. This is a new, separately attributed interpretation of the same observation.
The original Stage19 comparator FAIL, exhaustive diagnostic, raw receipts and
RUN002 FAIL remain unchanged. No schematic, embedded library, annotation flag,
net/pin identity, UUID, native input or native execution changed.

## Why the three differences are representational

The [pinned exporter source manifest](exporter-source.json) records exact source
hashes, URLs and line ranges, checked against the retained XML and embedded source.

- **61 unit labels:** `GetUnitPinInfo` enumerates library slots from 1 through
  `max(GetUnitCount(),1)`. Each affected source placement has unit 0 and a library
  with one slot, exported as A. The comparator derives the library slots, including
  per-placed-unit library overrides; it does not alias arbitrary observed labels.
  Original unit-0 metadata and every UUID remain independently required. Custom
  unit names, alternate bodies and slots above Z are outside this bounded parser.
- **9 components' properties:** the library parser promotes `ki_keywords` and
  `ki_fp_filters` into library metadata. The exporter adds nonempty values from
  the representative resolved library. Filters are ASCII-whitespace tokenized,
  unescaped per token and space-joined. Exact properties are required, including
  representative-unit metadata and exclusion flags. Aggregated fields still use
  correlated whole-dictionary outcomes of the separately derived running-minimum
  algorithm; all original per-unit metadata is retained separately.
- **3 U7101 NC pins (1, 7, 8):** their source electrical type is `no_connect`, and
  source geometry independently requires an explicit NC marker on each singleton.
  Connection-graph iteration may leave either that pin or the marker as the NC
  object. The XML exporter appends `+no_connect` only for a marker object, so these
  pins may emit exactly `no_connect` or `no_connect+no_connect`. Ordinary NC pins
  require their exact source electrical type plus the suffix. Connected pins must
  match their exact source type and cannot be NC. Singleton and exact connectivity
  checks remain mandatory; no net or endpoint is ignored or repaired.

The retained XML SHA256 is
`289f7771d87b81dafec5178dc42d1889a9671997c333dc42f51660f047ebc238`.
The original source is commit `91403f4d78b72757187d8cfdbb4d2dc436a3cf72`,
with native verifier `a57e02f6bfd770e55ebf448bc067e79fc6b08eb5` and consumed
request SHA256 `a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1`.
The replay checks all 72 native-input hashes, all published evidence hashes and
40 raw retained files. Deterministic regeneration verifies the unchanged Stage18
source report. All preexisting tracked files at f62c8650 are protected except
WORK.md; only new Stage20 implementation/evidence files are allowed.

## Regression and replay commands

Before implementation, the retained-evidence suite produced 3 positive-test errors
against the old comparator (unit slot roster mismatch C7101). The corrected suite
has 43 tests: complete real export, both supported source-NC representations,
original unit metadata, historical FAIL, and adversarial omissions, identity,
rewiring, NC shorts, types, properties/fields, unit slots, library pins and encoding
collision rejection. Historical suites cover additional source mutations.

```sh
python3 -m unittest discover -s scripts/architecture278/implementation -p test_stage20_observation.py
python3 scripts/architecture278/implementation/stage20_replay.py --check
python3 scripts/architecture278/implementation/check_source.py
pnpm circuit:check
pnpm check
```

`stage20_replay.py` without `--check` deterministically writes only the new
[replay report](replay-report.json). It launches no native executable. Reviewer
attribution and hashes are in the independent review receipts. Final commit and
check results are published to retained draft PR286.

## Acceptance boundary and next step

This closes the logical parity representation discrepancies for this exact,
unchanged candidate and observation. It grants no electrical acceptance, ERC/DRC,
simulation, PCB/routing, architecture adoption, procurement or hardware readiness.
19 unresolved passive MPNs and unbound DIN/land footprints remain blockers.
Canonical boards, locked placements, decision.json, KEEP_K1402_INCUMBENT and
parked PR260/277/285 are unchanged; PR286 stays draft and unmerged.

No fresh native export is needed for this representation-only reconciliation.
The consumed Stage19 approval/admission cannot be reused. The next bounded work
is source-only resolution/review of the procurement and footprint blockers, with
any source changes explicitly invalidating this observation as evidence for the
changed input. A later native need requires a new exact-commit/input request,
fresh run paths and approval, actual resource/ownership proof, independent live
admission and one bounded opportunity. Cloud is default; X0X is used only when
its capabilities are needed. No new native request or admission is granted here.
