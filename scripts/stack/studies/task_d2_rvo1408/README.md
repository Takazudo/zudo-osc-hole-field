# RVO1408's rear proposal would lengthen the scale path; moving R1452 with the trim would shorten it instead

Task D step 2, 2026-11-20. Reviews the ST-07 geometric relocation of `RVO1408` (O4 SCALE_TRIM,
`TC33X-2-102E`) against its circuit role. The trim is a 1 kΩ rheostat from `SCALE_ADJ` to AGND;
`R1452` (1.5 kΩ) joins `SCALE_ADJ` to `SCALE_PIN`, which is AS3340 `U1405` pin 14 with bypass `C1410`
(`design/spec/modules/oscillator.py`, `io-partition.json`).

```sh
python3 -B scripts/stack/studies/task_d2_rvo1408/scale_path.py --output scripts/stack/studies/task_d2_rvo1408/result.json
```

`result.json` sha256 `ae123432588d91db43ae1a41cd0e3e992aec89144b570d72c236901af236bdc9`.

## The path to the oscillator core is already about 30 mm in every case

Footprint-origin XY distances (mm) and faces; a face change means at least one via:

| Case | Trim → R1452 (`SCALE_ADJ`) | R1452 → U1405 (`SCALE_PIN`) | C1410 → U1405 |
| --- | --- | --- | --- |
| Canonical board | 6.19, B/B | 30.66, B/B | 13.94, B/B |
| After the link projection | 11.61, F/F | 32.56, F/F | 9.85, B/F |
| ST-07 rear proposal (29.36 mm move) | **26.43, B/F** | 32.56, F/F | 9.85, B/F |
| Same, with R1452 kept beside the trim (what-if) | 0, B/B | **18.60, B/F** | 9.85, B/F |

The ST-07 proposal adds about 15 mm and a via on `SCALE_ADJ` while leaving the 32.6 mm `SCALE_PIN` run.
Treating R1452 and RVO1408 as one unit at the proposed spot would cut the run to the core to 18.6 mm,
because the proposal lies closer to U1405 than the current R1452. The bypass sits on the opposite face
from U1405 after the projection.

## No position is selected

Recommendation to the reviewer: review RVO1408 and R1452 together as the scale-trim unit, placed near
U1405, rather than accept the trim-only move. The paired case is a what-if and was not checked against
any obstacle. Pad positions, routing, the scale-node sensitivity and the 5-cent tracking target
(`electrical-standard.json`) remain unassessed, and rear tool access is unmeasured.
