# Decision packet (corrected): one proposed additional AGND diagnostic, not authorized, not implemented

Correction requested by coordinator instruction `osc-moya-decision-refinement-67a9d535`.
This packet proposes exactly ONE attempt. Nothing below is executed, scheduled or
implemented until a recorded approval and a serialized slot exist. No automatic
extension, retry or second run is implied.

## Technical goal

Establish, on the KiCad oracle's own output, whether the intended AGND
connection of U1105.12 (GND pin of the AS3340D) to the rest of AGND exists once
every AGND copper zone is filled. This is a question about the design's intended
connectivity, not a product choice: if the fully filled result still shows the
pair open, the mismatch against the intended net supports an ordinary repair
proposal. Any copper change or canonical adoption remains its own authorized
scope and is not part of this packet.

## Scope of the single attempt

| item | value |
| --- | --- |
| payload | `derive`, chained from the saved run-3 copy |
| parent | identity key `ecf170dbb48e07980d8c08e149ff6e5c223745b58cdd9f9abb09cfa4b5001d16`, board SHA256 `4a55e0c165efcc2215d920272da25476b54df1cc56ba59e95a31049b29ba4dc8` (F.Cu AGND filled only) |
| zones to fill | `e389d344-872d-538e-9bfc-39577adb1686` (AGND, B.Cu) and `e67a5bc7-b575-52b6-a78a-9c84381053da` (AGND, In1.Cu), one Fill call |
| pairs | `C1111.2 <-> U1105.12` (AGND), `C1129.1 <-> U1105.16` (+12V control) |
| source | frozen core `fa60b4e1...` read-only; the parent copy mounted read-only; output to a fresh disposable directory |
| expected result for the AGND pair | `OPEN_WITH_ALL_NET_ZONES_FILLED` or `CONNECTED_VIA_SELECTED_FILL` (evaluable either way) |
| expected result for the +12V control | stays `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN`: the +12V In4.Cu zone is not filled on this copy; this attempt does not make the control pair evaluable |

## Full deadline chain (standard time chain; only the output bound differs from `standard`)

| layer | seconds |
| --- | --- |
| derive stage caps prepare / fill / verify | 60 / 260 / 100 |
| worker deadline (payload minus 40 s reserve) | 380 |
| payload | 420 |
| docker start --attach | 430 |
| wrapper (run.sh command) | 450 |
| controller | 590 |
| outer stop (process-group SIGKILL) | 600 |
| post-stop owned cleanup | 60 |
| heavy-guard cap (`HEAVY_GUARD_MAX_RUN`) | 720 |

Resources unchanged: 1 CPU, 2 GiB, zero extra swap, 64 PIDs, network none,
read-only root and source. Output board bound 128 MiB (the standard 64 MiB
cannot hold the chained result). No autoextension: a fill-cap or output-bound
hit ends the attempt with the first failure preserved.

## Cost: what is measured and what is an estimate

- Measured: In1.Cu AGND fill 131.9 s on the unfilled source (derive run 1);
  F.Cu AGND fill 150.8 s on the unfilled source (derive run 3). **No B.Cu fill
  has ever been measured.**
- Unknown estimates: B.Cu fill time (its obstacle class resembles F.Cu: 21,730
  segments, 1,204 SMD pads, but that is not a measurement); the combined
  two-zone Fill time starting from a 61.3 MB parent; peak memory (1.58 GiB was
  observed on a 61 MB board; the chained input is larger); final board size
  (roughly 61.3 + 11 + 11 MB, so about 84 MB, under the 128 MiB bound; scratch
  tmpfs use about 61 + 84 MB under 256 MiB). The combined fill may exceed the
  260 s cap; if it does, that is the recorded outcome of the single attempt.
- First native use of the chained-derivation code path (offline-tested, never run
  natively); the profile `chained-agnd` would be a new table entry plus tests,
  committed and reviewed before any launch, implemented only after approval.

## What the attempt does not do

No DRC, no copper edit, no canonical write, no +12V zone fill, no second run.
It does not decide whether anything is a defect: it moves the AGND pair's class
out of `UNEVALUABLE` so that the oracle's output, not inference, carries the
observation.

## Decision requested from the parent

Authorize or decline this one attempt as specified. If declined, the saved
evidence (run 3, the independent review, the diagram) stands as the record and
the AGND pair remains `UNEVALUABLE`.
