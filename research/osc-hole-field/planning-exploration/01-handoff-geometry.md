# 01 — Handoff geometry authority (R21) for zudo-osc-hole-field

Explorer 01 of 9. Read-only analysis. Nothing in the handoff or any repo was modified.

Path shorthand used below:

- `$HANDOFF` = `$DROPBOX_CCLOGS_DIR/zudo-osc-hole-field/handoff-r21/zudo-osc-playground-r21-handoff`
- `$WB` = `$HANDOFF/payload/project/osc-playground/workbench`
- `$PROJ` = `$HANDOFF/payload/project/osc-playground`
- Target repo = `$HOME/repos/circuits/zudo-osc-hole-field`

Verification method: every number below was produced by parsing the files with python3 (json / xml.etree / csv), not by reading names. Items I could not verify are marked UNVERIFIED. All 159 entries of `$HANDOFF/SHA256SUMS.json` hash-match the extracted bytes (0 mismatch, 0 missing), so the analysed handoff is intact.

---

## 1. Coordinate system is fully determined: 324/324 hardware centres and 114/114 LEDs reproduce panel.svg exactly

### Frame

| Property | Value | Source |
| --- | --- | --- |
| Units | millimetres | `$WB/src/render.js` line 1, SVG `width="318mm" height="298mm" viewBox="0 0 318 298"` |
| Origin | panel top-left corner, seen from the front (user side) | SVG frame |
| +X | right | SVG frame |
| +Y | DOWN | SVG frame (same direction as KiCad) |
| Panel size | 318 x 298 mm | `dims()`; PDF proof measured 317.99999 x 298.00001 mm |
| Columns | 18 (both fields) | `grid.json.columns` |
| Jack rows | 10 | `grid.json.jack_rows` |
| Control rows | 8 | `grid.json.control_rows` |
| Column pitch `px` | 17 mm | `grid.json.presets.compact.px` |
| Row pitch `py` | 14 mm | `grid.json.presets.compact.py` |
| Index base | zero-based `col`, `row`; row 0 is the TOP row of its field | `prepare_data.py` comment, verified |

### Margins and bands (all derived in `render.js` `dims()`, line 11)

```
jtop = 22                      top of jack field (title band is y 0..22)
div  = jtop + 10*py + 4 = 166  gold divider line y
ctop = div + 12        = 178   top of control field
w    = 18*px + 12      = 318   (6 mm left margin + 306 + 6 mm right margin)
h    = ctop + 8*py + 8 = 298   (8 mm bottom band)
```

| Band | Y range (mm) | Height |
| --- | --- | --- |
| Title band | 0 .. 22 | 22 |
| Jack field (18 x 10 cells) | 22 .. 162 | 140 |
| Gap above divider | 162 .. 166 | 4 |
| Divider line | y = 166 (x 6 .. 312, gold, 0.38 stroke) | - |
| Control heading band | 166 .. 178 | 12 |
| Control field (18 x 8 cells) | 178 .. 290 | 112 |
| Bottom band | 290 .. 298 | 8 |
| Left / right margin | x 0 .. 6 and 312 .. 318 | 6 each |

### The exact formula (`render.js` `pos()`, line 12)

```
x_mm = 6 + (col + 0.5) * 17                       = 14.5 + 17 * col
y_mm = 22  + (row + 0.5) * 14   (field == jacks)    = 29  + 14 * row
y_mm = 178 + (row + 0.5) * 14   (field == controls) = 185 + 14 * row
```

There is NO per-record offset anywhere in `grid.json`. Every one of the 324 hardware items sits exactly on a cell centre. The only offsets in the whole system are the three LED constants (section 2), which live in `render.js`, not in data.

Resulting lattice:

- Column X centres: 14.5, 31.5, 48.5, 65.5, 82.5, 99.5, 116.5, 133.5, 150.5, 167.5, 184.5, 201.5, 218.5, 235.5, 252.5, 269.5, 286.5, 303.5
- Jack row Y centres: 29, 43, 57, 71, 85, 99, 113, 127, 141, 155
- Control row Y centres: 185, 199, 213, 227, 241, 255, 269, 283
- All hardware coordinates are exact multiples of 0.5 mm.

### Verification against panel.svg

Each item group in `panel.svg` (`<g class="item" data-id="...">`) contains one focus circle (r=5.3 for jacks, r=4.7 for controls) whose `cx,cy` is the hardware centre. Comparing computed vs SVG for ALL items:

| File | Size | Items | Mismatches |
| --- | --- | --- | --- |
| `$WB/panels/panel.svg` | 318 x 298 | 324 | 0 |
| `$WB/panels/grid-proof.svg` | 318 x 298 | 324 | 0 |
| `$WB/panels/square-grid.svg` (py=17) | 318 x 352 | 324 | 0 |

Sample rows (computed == SVG in every case):

| uid | [col,row] | kind | panel mm (x, y) |
| --- | --- | --- | --- |
| `J:O1.1V` | [0,0] | jack | (14.5, 29.0) |
| `J:E6.STG` | [17,6] | jack | (303.5, 113.0) |
| `J:A06.OUT` | [17,9] | jack | (303.5, 155.0) |
| `J:N1.BROWN` | [11,9] | jack | (201.5, 155.0) |
| `J:B1.IN` | [0,8] | jack | (14.5, 141.0) |
| `J:H2.OUT` | [6,9] | jack | (116.5, 155.0) |
| `C:O1.OCT` | [0,0] | octave | (14.5, 185.0) |
| `C:H1.SLEW` | [7,6] | pot | (133.5, 269.0) |
| `C:H2.SLEW` | [7,7] | pot | (133.5, 283.0) |
| `C:E3.TRIG` | [14,3] | button | (252.5, 227.0) |
| `C:X2.SELECT` | [6,7] | toggle | (116.5, 283.0) |
| `C:M4B.LEVEL` | [11,5] | pot | (201.5, 255.0) |
| `C:A06.OFFSET` | [17,7] | pot | (303.5, 283.0) |

`osc-grid-authority.mdx` states H1.SLEW = (133.5, 269) and H2.SLEW = (133.5, 283): confirmed. `test_logic.cjs` asserts `dims == {w:318,h:298,jtop:22,ctop:178,div:166,margin:6}` and first jack `{x:14.5,y:29}`: consistent.

### Authority chain

1. `$WB/scripts/prepare_data.py` - hand-written register; regenerates `grid.json` (asserts 180 ports, 144 controls, all cells unique and full).
2. `$WB/layout/grid.json` - declared geometry authority (`current-spec.json.layout_authority`). sha256 `65230567...fbca0` matches `handoff-provenance.json.current_grid_sha256`.
3. `$WB/src/render.js` - the ONLY place the cell-to-mm mapping and LED offsets are defined. Shared by 2D, 3D and static exports.
4. `panel.svg` - a rendering. `current-spec.json.geometry_rule`: "Do not edit rendered SVG as geometry authority."

The embedded `window.GRID_DATA` inside `$WB/index.html` is byte-equivalent (as parsed JSON) to `layout/grid.json`.

---

## 2. grid.json holds 180 ports + 144 controls + 65 groups + 33 blocks; LEDs are boolean flags, not records

### Top level

| Key | Type | Value |
| --- | --- | --- |
| `schema_version` | int | 1 |
| `revision` | str | `R21` |
| `title` | str | `zudo-osc-playground` (old name) |
| `source` | str | `reference/user-jack-grid.png` |
| `columns` / `jack_rows` / `control_rows` | int | 18 / 10 / 8 |
| `ports` | list[180] | jacks |
| `controls` | list[144] | pots, octave selectors, toggles, buttons |
| `groups` | list[65] | 33 jack groups + 32 control groups (cell rectangles per block) |
| `blocks` | dict[33] | `{id, family, name}` |
| `presets` | dict | `compact {px:17, py:14}`, `square {px:17, py:17}` |
| `default_preset` | str | `compact` |
| `no_interblock_normals` | bool | true |
| `construction_note` | str | board planes are "pre-CAD assumptions" |

### `ports[]` record (all 17 keys present on all 180 records)

| Field | Meaning | Observed values |
| --- | --- | --- |
| `uid` | unique UI id, `J:` + id | 180 unique |
| `id` | electrical id `<block>.<key>` | NOT unique across ports+controls (section 9) |
| `block`, `key`, `label` | block id, key, printed label | 40 distinct labels |
| `col`, `row` | zero-based cell | full 18 x 10 coverage, each cell once |
| `field` | `jacks` | 180 |
| `kind` | `jack` | 180 |
| `direction` | `in` / `out` | in 98, out 82 |
| `accent` | bool, gold-bracket emphasis | true 114, false 66 |
| `led` | bool, magnitude LED present | true 92 |
| `clip` | bool, clip LED present | true 10 |
| `nut_diameter_mm` | dress-nut envelope | 8.3 on all 180 |
| `plug_diameter_mm` | plug envelope | 9.6 on all 180 (unused by renderer) |
| `component` | parts register id | `qingpu-wqp518ma` on all 180 |
| `geometry_status` | caveat string | "Nut and full footprint unqualified; 8.3 mm is a retained trial envelope." |

### `controls[]` record

Always present (144): `uid` (`C:` + id), `id`, `block`, `key`, `label`, `col`, `row`, `field`=`controls`, `kind`, `accent`, `component`, `diameter_mm`.
Optional: `positions` (35 records: 30 toggles + 5 octave), `stage` (12 records), `default_value` (2 records, the SLEW pots, 0.0).

### Counts by kind (identical in grid.json, changes.json, current-spec.json, block-contracts.json and panel.svg)

| Hardware | Count | `kind` | `component` | `diameter_mm` | How to distinguish |
| --- | --- | --- | --- | --- | --- |
| Jack IN | 98 | `jack` | `qingpu-wqp518ma` | - | `direction == "in"` |
| Jack OUT | 82 | `jack` | `qingpu-wqp518ma` | - | `direction == "out"` |
| Continuous pot (10k B) | 99 | `pot` | `bourns-ptv09a-4020f-b103` | 6 | `kind == "pot"` |
| Continuous pot (500k B, SLEW) | 2 | `pot` | `bourns-ptv09a-4020f-b504` | 6 | `H1.SLEW`, `H2.SLEW` |
| Octave selector (6-position) | 5 | `octave` | `alps-srbv160803` | 8 | `positions == [-2,-1,0,1,2,3]` |
| 2-position toggle | 19 | `switch` | `dailywell-2ms1` | 6 | `len(positions) == 2` |
| 3-position toggle | 11 | `switch` | `dailywell-2ms3` | 6 | `len(positions) == 3` |
| Button | 8 | `button` | `omron-b3f1020` | 5 | `kind == "button"` |
| **Total controls** | **144** | | | | |

Toggle position sets: `[LFO,VCO]` x5 (OSC RANGE), `[SOFT,OFF,HARD]` x5 (OSC SYNC), `[ASR,AR,LOOP]` x6 (ENV MODE), `[LINEAR,CURVED]` x6 (ENV SHAPE), `[RISE,FALL]` x6 (ENV STAGE), `[A,B]` x2 (SWITCH SELECT). 5+6+6+2 = 19 two-position; 5+6 = 11 three-position.

Buttons: 6 x `E*.TRIG` + 2 x `H*.SAMPLE`.

### The three LED families: derived at render time from flags

There are NO LED records in R21 `grid.json`. LEDs exist only as `led`/`clip` booleans on ports and a `stage` string on controls; positions come from constants hard-coded in `render.js` (lines 39 and 51).

| Family | Count | Trigger | Centre (panel mm) | Drawn bezel / emitter | Colour in preview |
| --- | --- | --- | --- | --- | --- |
| Magnitude | 92 | `port.led == true` | `(jack.x + 6.15, jack.y)` | r 0.66 / r 0.47 | white `#edece5` |
| Clip | 10 | `port.clip == true` | `(jack.x + 6.15, jack.y + 2.05)` | r 0.66 / r 0.47 | red `#ff5f50` |
| Stage | 12 | `"stage" in control` | `(pot.x + 5.9, pot.y)` | r 0.67 / r 0.48 | gold `#c6a35e` |

Verified: the multiset of 114 computed LED centres equals the multiset of `data-led` / `data-stage` circles in `panel.svg` (0 mismatch).

Leader lines (artwork): magnitude `x+4.82 .. x+5.45` at `y` (gold 0.17); stage `x+3.7 .. x+5.1` at `y` (gold 0.2).

Which jacks carry LEDs:

| Family | Jacks with magnitude LED | Without |
| --- | --- | --- |
| OSC | 0 | 40 (explicit rule "No OSC lamps") |
| VCF | 12 (the 4 inputs per filter) | 12 (outputs) |
| MIX5 | 12 (5 in + SUM, x2) | 0 |
| MIX4 | 12 (4 in + ATTEN + SUM, x2) | 0 |
| FOLD | 6 (3 inputs x2) | 2 (OUT) |
| AR | 18 (SIG, RISE, FALL x6) | 24 (ENV, BIP, EOC, STG) |
| AO (OFFSET) | 18 (IN, OFFSET, OUT x6) | 0 |
| MULT | 2 (IN x2) | 6 |
| SH | 6 (TRIGGER, IN, OUT x2) | 0 |
| SWITCH | 6 (IN-A, IN-B, OUT x2) | 0 |
| NOISE | 0 | 4 |
| **Total** | **92** | **88** |

By direction: 78 inputs + 14 outputs carry a magnitude LED. The 14 outputs are 4 x `M*.SUM`, 6 x `A0*.OUT`, 2 x `H*.OUT`, 2 x `X*.OUT`.
Clip LEDs (10): `M5A.SUM`, `M5B.SUM`, `M4A.SUM`, `M4B.SUM`, `A01.OUT` .. `A06.OUT`. Every clip jack also has a magnitude LED.
Stage LEDs (12): `E1..E6` `.RISE` (control row 4) and `.FALL` (control row 5).

Sample LED coordinates: `F1.IN` magnitude (105.65, 29.0); `M5A.SUM` magnitude (156.65, 99.0) + clip (156.65, 101.05); `A06.OUT` magnitude (309.65, 155.0) + clip (309.65, 157.05); `E1.RISE` stage (224.4, 241.0); `E6.FALL` stage (309.4, 255.0).

### `groups[]` and `blocks{}`

`groups[]`: `{block, field, col, row, cols, rows}` - one rectangle of cells. 33 in the jack field, 32 in the control field. H1 and H2 each have TWO control groups (SAMPLE cell and SLEW cell are not adjacent). MULT 1, MULT 2 and Noise have no control group (no controls). `validate.py` asserts every item falls in exactly one group of its block.

`blocks{}`: 33 entries, families: AR 6, AO 6, OSC 5, VCF 3, MIX5 2, MIX4 2, FOLD 2, MULT 2, SH 2, SWITCH 2, NOISE 1.

### Related files

| File | What it is | Trust |
| --- | --- | --- |
| `$WB/layout/changes.json` | R20 to R21 diff: 2 added controls, counts | consistent with grid.json |
| `$WB/reference/r20-grid.json` | byte copy of R20 grid | ports identical; controls 142; groups 63 |
| `$WB/layout/placements-review.csv` | mm table, 1-based col/row | STALE: 322 rows, missing both SLEW pots |
| `$PROJ/block-contracts.json` | 33 blocks with ports/controls + behaviour text | ids, col/row, kind, component all equal grid.json (0 diffs) |
| `$WB/reference/panel.json` | R17 legacy, 289 x 264 mm | OBSOLETE frame, do not use for coordinates |

---

## 3. Every hole diameter in the handoff is a preview proposal; LED apertures are not defined at all

No file in the handoff contains a drill table. The only hole sizes are radii hard-coded in the 3D preview (`three.js` `panelShape()`) and repeated in the 2D `artOnly` render. The handoff labels all of them as unqualified (`open-issues.json` G01, G02; `osc-board-stack.mdx` "What is not locked").

| Hardware | Count | Preview panel hole | grid.json dimension | What that dimension really is | Status |
| --- | --- | --- | --- | --- | --- |
| Jack (WQP518MA / Thonkiconn family) | 180 | r 3.10 = dia 6.2 mm | `nut_diameter_mm` 8.3, `plug_diameter_mm` 9.6 | dress-nut envelope, plug envelope | PROPOSAL (G01 open) |
| Pot (Bourns PTV09A-4020F) | 101 | r 3.15 = dia 6.3 mm | `diameter_mm` 6 | capless 6 mm F-shaft | PROPOSAL (G02 open) |
| Octave (Alps SRBV160803) | 5 | r 3.15 = dia 6.3 mm | `diameter_mm` 8 | "unselected cap envelope" | PROPOSAL (G02 open) |
| Toggle (Dailywell 2MS1 / 2MS3) | 30 | r 2.60 = dia 5.2 mm | `diameter_mm` 6 | meaningless fall-through default | PROPOSAL (G02 open) |
| Button (Omron B3F-1020) | 8 | r 2.50 = dia 5.0 mm | `diameter_mm` 5 | "5 mm circle as the finger target" | PROPOSAL (G02 open) |
| Magnitude LED | 92 | none (no hole in 3D panel shape) | flag only | drawn bezel dia 1.32, emitter dia 0.94 | UNDEFINED |
| Clip LED | 10 | none | flag only | drawn bezel dia 1.32, emitter dia 0.94 | UNDEFINED |
| Stage LED | 12 | none | flag only | drawn bezel dia 1.34, emitter dia 0.96 | UNDEFINED |

Total panel features: 324 hardware holes + 114 LED windows = 438.

Supplementary reference numbers that exist only in the obsolete R17 `reference/panel.json` (family reference, flagged `FAMILY_REFERENCE_NOT_EXACT_PART_CAD`): toggle bushing thread 10-48 UNS-2A, bushing reference height 5.59 mm, nut across flats 7.0 mm, lever dia 2.54 mm, lever reference height 9.4 mm, body 8.13 x 5.08 mm, throw axis "horizontal in panel view". LED apertures there are 1.2 mm (magnitude, clip) and 1.44 mm (stage), which disagree with R21 drawing sizes.

Body envelopes used by the previews (not footprints):

| Part | 2D `bodies` overlay | 3D box (w x h x z) | Source quote |
| --- | --- | --- | --- |
| Jack | 10 x 10 | 9.5 x 10 x 8 | - |
| Pot | 12 x 12 | 10 x 10 x 6.8 | "12 x 12 mm preview box is not qualified pad courtyard" |
| Octave | 16.2 x 18.5 | 16.2 x 18.5 x 7.5 | "leaves 0.8 mm body gap" at 17 mm pitch |
| Toggle | 8.13 x 5.08 | 8.13 x 5.08 x 8.64 | - |
| Button | 6 x 6 | 6 x 6 x 5 | "5 mm catalogue height is not an approved exposed button height" |

Derived clearances at the fixed pitch (using preview sizes):

| Pair | Value |
| --- | --- |
| Hole edge to hole edge, jacks, horizontal / vertical | 10.8 / 7.8 mm |
| Dress nut (8.3) edge to edge, horizontal / vertical | 8.7 / 5.7 mm |
| Plug (9.6) edge to edge, vertical | 4.4 mm |
| Magnitude LED centre to own nut edge | 2.0 mm (bezel edge 1.34 mm) |
| Plug barrel diameter that starts covering the LED bezel | 10.98 mm (app.js warning, = 2 x (6.15 - 0.66)) |
| Octave body (18.5 tall) bottom to RANGE toggle body top | 2.21 mm (octave body is taller than the 14 mm row pitch) |
| Octave body to octave body, horizontal | 0.8 mm |
| Rightmost LED centre to panel edge | 8.35 mm |
| Leftmost nut edge to panel edge | 10.35 mm |

---

## 4. Block layout: every cell of both fields is occupied, and the two fields share the same column ownership for the main bank

Task-name to handoff-id mapping: OSC1..5 = `O1..O5`; VCF1..3 = `F1..F3` (named FILTER n); MIX5 x2 = `M5A`, `M5B`; MIX4 x2 = `M4A`, `M4B`; AR x6 = `E1..E6` (named ENV n); FOLD x2 = `W2`, `W1` (FOLD 2 is LEFT of FOLD 1 by explicit user decision); OFFSET x6 = `A01..A06`; MULT x2 = `B1`, `B2` (1 in, 3 out); S&H+SLEW x2 = `H1`, `H2`; manual A/B x2 = `X1`, `X2` (named SWITCH n); NOISE = `N1`.

### Jack field (18 x 10), x centre = 14.5 + 17*col, y centre = 29 + 14*row

```
col   0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17
r0    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r1    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r2    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r3    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r4    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r5    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r6    O1   O2   O3   O4   O5   F1   F2   F3   W2   W2   W1   W1   E1   E2   E3   E4   E5   E6
r7    O1   O2   O3   O4   O5   F1   F2   F3   W2   W2   W1   W1   A01  A02  A03  A04  A05  A06
r8    B1   B1   B2   B2   H1   H1   H1   X1   X1   X1   N1   N1   A01  A02  A03  A04  A05  A06
r9    B1   B1   B2   B2   H2   H2   H2   X2   X2   X2   N1   N1   A01  A02  A03  A04  A05  A06
```

Jack keys (`<` input, `>` output, `m` magnitude LED, `c` clip LED):

```
col   0      1      2      3      4      5       6       7       8       9       10       11       12      13 .. 17
r0    1V<    1V<    1V<    1V<    1V<    IN<m    IN<m    IN<m    1<m     1<m     1<m      1<m      SIG<m   (same)
r1    FM<    FM<    FM<    FM<    FM<    FREQ<m  FREQ<m  FREQ<m  2<m     2<m     2<m      2<m      RISE<m
r2    PWM<   PWM<   PWM<   PWM<   PWM<   RES<m   RES<m   RES<m   3<m     3<m     3<m      3<m      FALL<m
r3    SYNC<  SYNC<  SYNC<  SYNC<  SYNC<  GAIN<m  GAIN<m  GAIN<m  4<m     4<m     4<m      4<m      ENV>
r4    SIN>   SIN>   SIN>   SIN>   SIN>   LP>     LP>     LP>     5<m     5<m     ATTEN<m  ATTEN<m  BIP>
r5    TRI>   TRI>   TRI>   TRI>   TRI>   BP>     BP>     BP>     SUM>mc  SUM>mc  SUM>mc   SUM>mc   EOC>
r6    SAW>   SAW>   SAW>   SAW>   SAW>   HP>     HP>     HP>     IN<m    FOLD<m  IN<m     FOLD<m   STG>
r7    PUL>   PUL>   PUL>   PUL>   PUL>   OUT>    OUT>    OUT>    BIAS<m  OUT>    BIAS<m   OUT>     IN<m
r8    IN<m   1>     IN<m   1>     TRIG<m IN<m    OUT>m   IN-A<m  IN-B<m  OUT>m   WHITE>   PINK>    OFFSET<m
r9    2>     3>     2>     3>     TRIG<m IN<m    OUT>m   IN-A<m  IN-B<m  OUT>m   BLUE>    BROWN>   OUT>mc
```

### Control field (18 x 8), x centre = 14.5 + 17*col, y centre = 185 + 14*row

```
col   0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17
r0    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r1    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r2    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r3    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r4    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r5    O1   O2   O3   O4   O5   F1   F2   F3   M5A  M5B  M4A  M4B  E1   E2   E3   E4   E5   E6
r6    O1   O2   O3   O4   O5   H1   H2   H1   W2   W2   W1   W1   A01  A02  A03  A04  A05  A06
r7    O1   O2   O3   O4   O5   X1   X2   H2   W2   W2   W1   W1   A01  A02  A03  A04  A05  A06
```

Control keys (`P` pot, `O` octave, `2`/`3` toggle, `B` button, `*` stage LED):

```
col   0..4 (OSC)    5..7 (FILTER)   8,9 (MIX5)   10,11 (MIX4)   12..17 (ENV / OFFSET)
r0    OCT:O         FREQ:P          1±:P         1±:P           MODE:3
r1    VCO/LFO:2     RES:P           2±:P         2±:P           SHAPE:2
r2    SYNC:3        FREQ±:P         3±:P         3±:P           STAGE:2
r3    TUNE:P        RES±:P          4±:P         4±:P           TRIG:B
r4    FINE:P        GAIN:P          5±:P         CV±:P          RISE:P*
r5    FM±:P         GAIN±:P         LEVEL:P      LEVEL:P        FALL:P*
r6    PW:P          (see below)     (FOLD)       (FOLD)         ATTEN:P   (OFFSET block)
r7    PWM±:P        (see below)     (FOLD)       (FOLD)         OFFSET:P  (OFFSET block)

Utility / fold cells, rows 6-7:
col   5            6            7            8         9         10        11
r6    H1.SAMPLE:B  H2.SAMPLE:B  H1.SLEW:P    W2.FOLD:P W2.FOLD±:P W1.FOLD:P W1.FOLD±:P
r7    X1.SELECT:2  X2.SELECT:2  H2.SLEW:P    W2.BIAS:P W2.LEVEL:P W1.BIAS:P W1.LEVEL:P
```

### Per-block hardware

| Block(s) | Jacks in / out | Controls |
| --- | --- | --- |
| O1..O5 | 4 / 4 | 1 octave, 1 toggle-2, 1 toggle-3, 5 pots |
| F1..F3 | 4 / 4 | 6 pots |
| M5A, M5B | 5 / 1 | 6 pots |
| M4A, M4B | 5 / 1 | 6 pots |
| W2, W1 | 3 / 1 | 4 pots |
| E1..E6 | 3 / 4 | 1 toggle-3, 2 toggle-2, 1 button, 2 pots |
| A01..A06 | 2 / 1 | 2 pots |
| B1, B2 | 1 / 3 | none |
| H1, H2 | 2 / 1 | 1 button, 1 pot |
| X1, X2 | 2 / 1 | 1 toggle-2 |
| N1 | 0 / 4 | none |

Layout peculiarities the generators must not "tidy up":

- H1 jacks are on jack row 8 and H2 on row 9, but `H1.SAMPLE` [5,6] and `H2.SAMPLE` [6,6] sit side by side, while `H1.SLEW` [7,6] and `H2.SLEW` [7,7] are stacked.
- `X1.SELECT` [5,7] and `X2.SELECT` [6,7] are below the SAMPLE buttons, not near the X jacks (cols 7-9).
- Utility jack blocks (rows 8-9) sit under OSC/FILTER/MIX columns they have no relation to.

---

## 5. Panel artwork exists as a complete SVG, but only hardware centres and text content are fixed; every drawn size is styling

### Inventory of `panel.svg` (parsed)

| Element | Count | Geometry rule | Colour / stroke | Class |
| --- | --- | --- | --- | --- |
| Background | 1 rect | 0,0 318 x 298 | `#101211` | styling |
| Border line | 1 rect | inset 2.2 mm, 313.6 x 293.6, rx 1.3 | gold `#c6a35e` 0.27 | styling |
| Title | 1 text | "ZUDO / OSC PLAYGROUND" at (8, 9.2), size 2.6, bold | white | styling + RENAME needed |
| Header note | 1 text | "R21 · 318 × 298 mm · 17 / 14 mm GRID" at (311, 8.5) end-anchored, size 1.45 | white | review annotation |
| Footer note | 1 text | "INTEGER CELLS / FIXED HARDWARE SCALE / FACTORY SOLDERING / MECHANICAL STACK NOT RELEASED" at (159, 294.2), size 1.15 | white | review annotation |
| Divider | 1 line | (6,166) to (312,166) | gold 0.38 | styling |
| Module headings | 65 groups | icon + title, formula below | gold text size 1.6 bold | text fixed, placement styling |
| Separators | 151 segments (65 vertical, 86 horizontal) | right and bottom edge of each group, clipped around text and hardware | dim gold `#695935` 0.13 | styling |
| Jack labels | 180 texts | `(x, y + 6.25)`, size 1.6, bold | white | text fixed, placement styling |
| Control labels | 142 texts | `(x, y + 5.75)`, size 1.5, bold when accent | white | text fixed, placement styling |
| Toggle position words | 71 texts | 2-pos: `x -/+ 4.75`; 3-pos: `x - 5, x, x + 5`; all at `y - 4.7`; size 0.85 | white | text fixed, placement styling |
| Accent corner brackets | 155 items x 4 paths | gold, leg 2.05, stroke 0.42 | gold | data-driven (`accent`), size styling |
| Plain corner brackets | 131 items x 4 paths | white, leg 1.15, stroke 0.18 | white | styling |
| Magnitude LED leader | 92 lines | section 2 | gold 0.17 | styling |
| Stage LED leader | 12 lines | section 2 | gold 0.2 | styling |
| MIX relation lines | 26 lines | vertical bus at `x - 6`, ticks to `x - 4.2` | gold 0.14 | styling |
| Button ring | 8 circles | r 2.5 | gold 0.23 | styling |
| Hardware pictures | nuts, bushings, knobs, levers | - | greys, red | NOT artwork (preview only) |

Corner bracket half-size: jacks 4.6 mm (9.2 mm square); pots `diameter/2 + 0.55` = 3.55 mm; octave 4.55 mm. Toggles and buttons get no brackets.

Control labels: 142, not 144. The two `X*.SELECT` records (label "A / B") are never printed; instead the module heading "SWITCH n" is placed BELOW the toggle at `y + 5.75`.

### Module heading formula (verified 65/65 against panel.svg)

```
first = first item of the group sorted by (row, col)
cy    = first.y - 8.8      if control group starting at control row 0
      = first.y + 5.75     if control group of an X block (SWITCH)
      = first.y - 5.6      otherwise
total = len(title) * 1.6 * 0.55 + 2.3
left  = group_x + group_w / 2 - total / 2
icon  : translate(left, cy - 1.22) scale(0.064)   (24-unit icon box = 1.536 mm)
text  : anchor start at (left + 2.1, cy), size 1.6
```

### Icons and glyphs

| File | Content | Used by renderer |
| --- | --- | --- |
| `$WB/reference/icons.json` | 9 families x 20 alternative SVG icons (OSC, MIX5, MIX4, VCF, AR, FOLD, MULT, AO, NOISE), 24 x 24 unit art, `currentColor` | YES, index 0 of each family by default |
| (hard-coded in `render.js`) | fallback paths for SH and SWITCH families | YES, because icons.json has no SH / SWITCH |
| `$WB/reference/switch-glyphs.json` | 3 styles (`contour`, `axis`, `framed`) x 12 state glyphs (ar, asr, curved, fall, fast, hard, linear, loop, off, rise, slow, soft) | NO - not referenced by any src or build script |
| `$WB/reference/switch-functions.json` | 5 switch functions with positions, state keys, defaults, explanations | NO - not referenced; positions match grid.json |

Default icons in the exported panel: OSC "Sine", VCF "Low pass", AR "Linear rise fall", AO "Scale and offset", MIX5 "Mix5 / 01", MIX4 "Mix3 / 01", FOLD "Fold / 01", MULT "Mult / 01", NOISE "Noise / 01".

The renderer has a `switchLabels: 'symbols'` mode that replaces only three toggle families with Unicode characters; the exported panel uses `'words'`.

### IN-black / OUT-red convention

- Data: `direction` on each port (98 in, 82 out). This is FIXED data.
- Preview: nut ring fill `#282f2c` (in) vs `#ba3733` (out).
- It is a HARDWARE convention (dress nut colour), stated in `current-spec.json` hard constraints: "IN dress nuts black; OUT red."
- Nothing printed on the panel distinguishes IN from OUT. In `artOnly` mode (the image mapped on the 3D panel face) jacks are plain background-colour discs. If the owner wants a printed cue, that is new styling work.

### Accent regions

`accent` is a per-record boolean, not an area. It selects gold thick brackets instead of white thin ones and bold control labels. 114 ports + 43 controls are accented; 2 of the 43 are buttons and draw no brackets. There are no filled accent regions in the artwork.

### Fixed versus tweakable

| FIXED (owner: "positions are all fixed") | STYLING (owner may tweak later) |
| --- | --- |
| Panel 318 x 298 mm | Fonts (SVG uses Arial/Helvetica), every text size |
| 324 hardware centres | Label offsets (+6.25, +5.75, -4.7, heading offsets) |
| Block membership and group rectangles | Bracket sizes and strokes, separator strokes and clipping |
| Label TEXT content, toggle position words | Icon choice (20 alternatives per family), words vs symbols |
| `direction`, `accent`, `led`, `clip`, `stage` flags | LED leader style (`line` vs `bracket`), MIX relation lines |
| LED centre offsets (treat as fixed by default, see open decision) | Title, header and footer strings, border, divider |
| | Which colour maps to silk / copper / mask |

---

## 6. Board domains have z planes on file, but their XY outlines exist only as code in three.js, and all of it is proposal

`$WB/mechanical/board-planes.json` and `$WB/mechanical/core-allocations.json` are NOT authored data: `scripts/test_browser.py` dumps them from the running 3D scene (`window.GRID_3D_LAYERS`, `window.GRID_3D_ALLOCATION`). `board-planes.json` holds only `{name, z}`. The outlines below were reconstructed by evaluating the expressions in `$WB/src/three.js` with px=17, py=14, ctop=178.

Datum (`board-contracts.json`): "Panel rear plane z=0, positive toward user; negative into case". In the model the panel is extruded from z=0 to z=+1.6 (preview thickness 1.6 mm). Each board is a 1.6 mm slab whose TOP face (component side, facing the panel) is at the listed z.

| Domain | Role | x0 .. x1 (mm) | y0 .. y1 (mm) | Size (mm) | z top | Hardware landing on it |
| --- | --- | --- | --- | --- | --- | --- |
| Front panel | panel | 0 .. 318 | 0 .. 298 | 318 x 298 | 0 (rear) | 324 holes |
| J | jack board | 6 .. 312 | 22 .. 162 | 306 x 140 | -10 | 180 jacks |
| O | octave strip | 7 .. 90 | 174.5 .. 195.5 | 83 x 21 | -10.6 | 5 octave selectors |
| OS | OSC selectors | 7 .. 90 | 195.6 .. 219.8 | 83 x 24.2 | -11.5 | 10 toggles (RANGE, SYNC) |
| OP | OSC pots | 7 .. 90 | 220.1 .. 289 | 83 x 68.9 | -13 | 25 pots |
| MP | filters, mixers, folders | L-shape, see below | | | -13 | 50 pots (F 18, M 24, W 8) |
| ES | envelope selectors | 210 .. 312 | 178 .. 220 | 102 x 42 | -11.5 | 18 toggles (MODE, SHAPE, STAGE) |
| ET | envelope triggers | 210 .. 312 | 221 .. 233 | 102 x 12 | -4.5 | 6 buttons |
| EP | envelope / offset pots | 210 .. 312 | 235 .. 289 | 102 x 54 | -13 | 24 pots (E 12, A 12) |
| UT | S&H buttons | 91 .. 125 | 263 .. 275 | 34 x 12 | -4.5 | 2 buttons |
| UP | S&H slew pots + local lag | 125.5 .. 141.5 | 263 .. 289 | 16 x 26 | -13 | 2 pots |
| US | A/B selectors | 91 .. 125 | 277 .. 289 | 34 x 12 | -11.5 | 2 toggles |
| K | core | 12 .. 306 | 16 .. 286 | 294 x 270, cutout 18..142 x 25..123 (124 x 98) | -24 | no panel hardware |
| P/B | power pocket reservation | 25 .. 135 | 31 .. 116 | 110 x 85 | -32 | zudo-pd "ENVELOPE ONLY" |

MP L-shape vertices (raw): (91,178) (210,178) (210,290) (142,290) (142,262) (91,262); three.js adds +0.25 mm to every vertex. The notch x 91..142, y 262..290 is where UT, US and UP live.

Control count check: O 5 + OS 10 + OP 25 + MP 50 + ES 18 + ET 6 + EP 24 + UT 2 + UP 2 + US 2 = 144.

Domain assignment rule (`three.js`):

```
block O*  : octave -> O,  switch -> OS, else -> OP
block E*  : switch -> ES, button -> ET, else -> EP
block A*  : EP
block H*  : pot -> UP, else -> UT
block X*  : US
otherwise : MP        (F*, M*, W*)
all ports : J
```

LEDs are not modelled in 3D and are assigned to no board. By position, the 102 magnitude/clip LEDs fall inside the J rectangle and the 12 stage LEDs inside the EP rectangle.

### What core-allocations.json actually allocates

47 rectangles `{id, x, y, w, h, height, kind}` in panel mm, every one with `kind: "package allocation; no netlist"`. They are illustrative IC bodies on the K plane, not a placement.

| Group | Entries | Position pattern (mm) |
| --- | --- | --- |
| OSC1..5 / AS3340D (3.9 x 9.9) | 5 | x = 27 + 24 i, y = 146 |
| OSC1..5 / shaping TL074 | 5 | x = 27 + 24 i, y = 162 |
| ENV1..6 / analogue allocation | 6 | x = 160 + 23 i, y = 47 |
| ENV1..6 / comparator | 6 | x = 160 + 23 i, y = 62 |
| VCF1..3 / LM13700 | 3 | x = 164 + 33 i, y = 94 |
| VCF1..3 / TL074 | 3 | x = 177 + 33 i, y = 105 |
| S&H1..2 / LF398M | 2 | x = 154 + 30 i, y = 145 |
| MULT / OPA4197 0..1 | 2 | x = 154 + 30 i, y = 165 |
| S&H / CD74HC221, S&H / LM393 | 2 | (218,147), (234,147) |
| A/B / buffers | 2 (duplicate id) | (260,151), (278,151) |
| MIX analogue allocation 0..3 | 4 | x = 50 + 30 i, y = 194 |
| AO/output allocation 0..5 | 6 | x = 160 + 23 i, y = 197 |
| SLEW dual-cell / OPA4197IPWR | 1, `board: UP`, `face: rear` | (133.5, 276) |

Not allocated at all: FOLD x2, NOISE, octave reference, 114 LED drivers/detectors, connectors, power interface. `components.json` itself warns: "Do not assign a quantity from empty rectangles."

### Preview stack findings (from evaluating three.js, all PROPOSAL-level)

| Finding | Numbers |
| --- | --- |
| Button body intrudes into the panel | ET/UT top z = -4.5, body 5.0 tall, body top at z = +0.5, panel rear at 0; body is 6 x 6 but the hole is dia 5.0 |
| Jack body does not reach the panel rear | J top z = -10, body 8 tall, body top at z = -2.0: a 2 mm gap to the panel rear although jacks must clamp to the panel |
| Octave body overhangs its board | body x 6.4 .. 90.6 vs O outline 7 .. 90 (0.6 mm each side) |
| Deepest plane | P/B top at -32, slab to -33.6 |
| P/B pocket sits under the jack field | x 25..135, y 31..116 = under jack cols 1..7, rows 0..6 |

`osc-overview.mdx`: "The numeric Z positions in the preview are not build dimensions."

---

## 7. For a KiCad panel PCB only the outline size and hole centres are defined; nine other inputs are missing

| Input | Status | Detail |
| --- | --- | --- |
| Outline size | DEFINED | 318 x 298 mm rectangle |
| Hole / window centres | DEFINED | 324 hardware + 114 LED, formula verified |
| Label text content | DEFINED | 180 jack, 142 control, 71 toggle words, 65 headings |
| Corner radius | MISSING | 3D panel shape has sharp corners; the rx 1.3 belongs to the drawn border line, not the outline |
| Mounting holes | MISSING | none in any file; no enclosure, standoff or screw definition |
| Thickness | MISSING | 1.6 mm appears only as the preview extrusion; G01 lists panel thickness as open |
| NPTH drill diameters | PROPOSAL ONLY | 6.2 / 6.3 / 6.3 / 5.2 / 5.0 mm, section 3 |
| LED apertures / windows | MISSING | no hole, no method (drill, bare FR4 window, light pipe) |
| Silk layer | MISSING as CAD | SVG text in Arial; sizes 0.85 .. 2.6 mm; needs font and minimum-size decisions |
| Exposed copper / ENIG accents | INTENT ONLY | "Black solder mask, exposed gold accents, white silk"; no layer mapping, ENIG not named explicitly |
| Solder mask openings | MISSING | must be derived from whichever elements become exposed copper |
| Back side | MISSING | no copper pour, grounding, or rear marking definition |
| Hardware rotation | MISSING | only the toggle throw axis is implied (horizontal) |
| Footprints | MISSING | no footprint for WQP518MA, PTV09A, 2MS1/2MS3, SRBV160803 or B3F-1020 exists in the sibling repos (180 `.kicad_mod` files checked by name) |
| Tolerances, keepouts, fiducials, tooling | MISSING | - |

Sibling convention observed: `$HOME/repos/circuits/zudo-case/engineering/r6-body/source-data/panels/*.kicad_pcb` are panels authored as KiCad PCBs, file format `20260206`, generator `pcbnew` 10.0, thickness 1.6.

---

## 8. Recommended pipeline: one frozen grid copy, one Python coordinate module, one committed placement lockfile, a pure translation into KiCad

### Frame choice

The handoff frame (origin top-left, +X right, +Y down, mm) has the same axis directions as KiCad board coordinates. Keep it as the single DESIGN FRAME and convert to KiCad with a translation only. No Y flip anywhere in generation code.

```
X_kicad = OX + x_panel
Y_kicad = OY + y_panel
```

Recommended `OX = 100.0`, `OY = 50.0` on an A2 sheet (594 x 420). The panel does not fit A4 or A3 (A3 height is 297 mm, panel is 298 mm). Set both the KiCad drill/place (aux) origin and the grid origin to `(OX, OY)` so exported Gerber, drill and position files are panel-relative.

Every board in the stack uses the SAME frame and the SAME `(OX, OY)`. A jack hole at panel (14.5, 29.0) and its footprint on board J are both at KiCad (114.5, 79.0), so any two board files can be overlaid for checking. Define F.Cu of every board as the side facing the panel; rear-facing parts become B.Cu parts and KiCad handles the mirror.

Sample translation: `J:O1.1V` (14.5, 29.0) to (114.5, 79.0); `C:H1.SLEW` (133.5, 269.0) to (233.5, 319.0); `C:A06.OFFSET` (303.5, 283.0) to (403.5, 333.0).

### Stages

```
1. design/grid/grid.json                  frozen copy of $WB/layout/grid.json
                                          + sha256 pin 65230567...fbca0
2. scripts/geometry/panel_frame.py        THE shared module (constants + functions)
3. scripts/geometry/build_placements.py   grid.json -> design/grid/placements.lock.json
4. design/grid/placements.lock.json       438 records, committed, reviewed by diff
5. generators read ONLY the lockfile:
     scripts/panel/gen_panel.py           Edge.Cuts, NPTH, silk, copper art, mask
     scripts/pcb/gen_placements.py        footprint positions per board domain
     doc tables / SVG overlays
6. scripts/geometry/verify_geometry.py    golden test
```

### Shared module contents

```python
PX, PY = 17.0, 14.0
COLS, JACK_ROWS, CTRL_ROWS = 18, 10, 8
MARGIN_X, JTOP, DIV_GAP, CTRL_GAP, BOTTOM = 6.0, 22.0, 4.0, 12.0, 8.0
DIV    = JTOP + JACK_ROWS * PY + DIV_GAP      # 166
CTOP   = DIV + CTRL_GAP                       # 178
PANEL_W = COLS * PX + 2 * MARGIN_X            # 318
PANEL_H = CTOP + CTRL_ROWS * PY + BOTTOM      # 298

LED_MAGNITUDE = (6.15, 0.0)
LED_CLIP      = (6.15, 2.05)
LED_STAGE     = (5.9, 0.0)

KICAD_OX, KICAD_OY = 100.0, 50.0

def cell_center(field, col, row):
    top = JTOP if field == "jacks" else CTOP
    return (MARGIN_X + (col + 0.5) * PX, top + (row + 0.5) * PY)

def to_kicad(x, y):
    return (KICAD_OX + x, KICAD_OY + y)

def board_domain(record): ...   # the three.js rule in section 6
HOLE_DIAMETER_MM = {...}        # single table, every value tagged PROPOSAL
```

Rules:

- Emit coordinates with fixed decimals (4 places). All hardware values are multiples of 0.5 mm and LED values multiples of 0.05 mm, so output is byte-stable.
- Sort lockfile records by `(field, col, row, family)` for deterministic diffs.
- Generate deterministic UUIDs (hash of uid), as the sibling `schgen_core.py` already does for schematics.
- Port the mapping to Python. The handoff authority is JavaScript (`render.js`); the sibling toolchain (`$HOME/repos/circuits/zudo-led-lamp/scripts/schgen/`, `$HOME/repos/circuits/zudo-pd/scripts/schgen/`) is dependency-free Python with its own `sexp.py`. The mapping is two lines, so a port pinned by a golden test is safer than calling Node from the generators.

### Lockfile record

```json
{
  "uid": "J:O1.1V", "slug": "J_O1_1V", "ref": "J101",
  "kind": "jack", "block": "O1", "family": "OSC", "label": "1V/OCT",
  "field": "jacks", "col": 0, "row": 0,
  "x_mm": 14.5, "y_mm": 29.0, "rot_deg": 0,
  "board": "J", "direction": "in", "accent": true,
  "hole_d_mm": 6.2, "hole_status": "PROPOSAL",
  "component": "qingpu-wqp518ma"
}
```

LED records get their own uid, for example `L:M5A.SUM.mag`, `L:M5A.SUM.clip`, `L:E1.RISE.stage`, with `parent` pointing to the jack or pot.

### Identifier rules the pipeline needs

- Key everything on `uid`. `id` collides 36 times between a jack and a control.
- 46 uids contain `±` (41) or `/` (5). Provide one slug function (suggested: `±` to `PM`, `/` to `-`, `:` and `.` to `_`) and assert slug uniqueness.
- Suggested reference designators, cell-coded so that a reference reveals the position: number = `(col + 1) * 100 + (row + 1)`. Jacks `J101 .. J1810`; pots `RV101 .. RV1808`; toggles, buttons and octave selectors `SW...`; LEDs `D...`. The schematic explorer may override, but the rule must live in the shared module.

### Golden test (already proven feasible in this exploration)

1. Recompute 324 centres and compare with the focus circles in a frozen copy of the handoff `panel.svg`: expect 0 mismatches.
2. Recompute 114 LED centres and compare with `data-led` / `data-stage` circles: expect multiset equality.
3. Assert counts 180 / 144 / 101 / 5 / 19 / 11 / 8 / 92 / 12 / 10.
4. Assert each hardware body lies inside its board outline and no two courtyards overlap, once real footprints exist.

---

## 9. Twenty inconsistencies found; none changes a hardware coordinate

Counts are consistent everywhere: `grid.json`, `changes.json`, `current-spec.json`, `block-contracts.json` and `panel.svg` all give 180 jacks, 144 controls, 101 pots, 5 octave, 19 + 11 toggles, 8 buttons, 92 / 12 / 10 LEDs. The inconsistencies are in side files, ids and preview models.

| # | Inconsistency | Evidence | Impact |
| --- | --- | --- | --- |
| 1 | `placements-review.csv` is stale | 322 rows; `C:H1.SLEW` and `C:H2.SLEW` absent; no script generates it; mtime 16:56 vs grid.json 17:09. The 322 present rows match the formula exactly | do not import the CSV |
| 2 | `reference/panel.json` is R17, not R21 | 289 x 264 mm, 31 blocks, 138 controls, 82 magnitude LEDs, blocks B3/B4, `F*.MAIN` instead of `F*.OUT`, no H/X blocks; `O1.1V` at (15.5, 20.0) vs R21 (14.5, 29.0). `prepare_data.py` loads it but never uses a value from it | never use for coordinates |
| 3 | `id` is not unique | 36 ids shared by a jack and a control, e.g. `O1.SYNC`, `E1.RISE`, `F1.FREQ`, `W1.FOLD`, `A01.OFFSET` | key on `uid` |
| 4 | Ids with special characters | 46 uids contain `±` or `/` | slug function needed |
| 5 | Key and label differ | key `VCO/LFO` label `RANGE`; key `SELECT` label `A / B` (never printed); MIX4 key `LEVEL` label `SUM GAIN`; jack key `1V` label `1V/OCT`; jack key `SYNC` label `SYNC CV` | print `label`, net-name from `key` |
| 6 | Component ids differ between files | grid and components.json: `dailywell-2ms1`, `dailywell-2ms3`, `alps-srbv160803`; switch-functions.json: `dailywell-2ms1-c908280`, `dailywell-2ms3-c19270342`; R17 panel.json: `alps-srbv160803-c470374` | one id scheme needed |
| 7 | 2MS3 supplier code conflict | `null` in components.json and r17-component-decisions.json, implied `c19270342` in switch-functions.json | procurement question |
| 8 | LED aperture values disagree | 1.32 (components.json text, magnitude/clip bezel), 1.34 (stage bezel), 1.2 and 1.44 (R17) | aperture is undefined anyway |
| 9 | `diameter_mm: 6` on all 30 toggles | fall-through default in `prepare_data.py` line 23 | not a dimension |
| 10 | `plug_diameter_mm: 9.6` is unused | renderer plug overlay uses a setting that defaults to 12 | ignore |
| 11 | 2D and 3D body envelopes differ | pot 12 x 12 vs 10 x 10; jack 10 x 10 vs 9.5 x 10 | neither is a footprint |
| 12 | Dangling file references | `mechanical/README.md` points to `../docs/MECHANICAL.md` (absent); R17 panel.json points to `mechanical/board-partition.json` (absent) | board outlines have no data file |
| 13 | Mechanical JSON files are runtime dumps | written by `test_browser.py` from the 3D scene | not an independent authority |
| 14 | `core-allocations.json` id duplicated and coverage partial | `A/B / buffers` appears twice; no FOLD, NOISE, LED driver or connector entries | illustrative only |
| 15 | Stale revision strings and defaults | `three.js` saves `zudo-grid-r20-assembly.png`; `shell.html` slider defaults 1.4 / 1.5 vs `app.js` defaults 1.6 / 1.6 used for exports | cosmetic |
| 16 | Icon data gaps and mislabels | icons.json lacks SH and SWITCH; MIX4 icons are named "Mix3"; MULT-01 draws four outputs while MULT is 1 to 3; block name `Noise` is mixed case while all others are upper case | owner styling review |
| 17 | Project name | `grid.json.title`, panel title text and all doc slugs say `osc-playground`; repo is `zudo-osc-hole-field` | rename decision |
| 18 | "Proposal" wording vs fixed positions | `app.js` status text: "17 mm columns / 14 mm rows are a proposal"; decisions D01/D04 and the owner's request fix the positions | treat positions as fixed |
| 19 | Power board naming | handoff says "zudo-pd Board P + Board B"; local `$HOME/repos/circuits/zudo-pd/boards/` holds `board-a` and `board-b`, schematics only, no board PCB | 110 x 85 envelope is UNVERIFIED |
| 20 | Preview mechanical interferences | section 6: button body +0.5 mm into panel, jack 2 mm short of panel, octave overhang 0.6 mm | z planes and outlines need real datums |

Two taxonomies also coexist: `current-spec.json.module_quantities` uses FILTER_VCA, MIX4_VCA, SH_SLEW, MANUAL_AB, NOISE_4_OUTPUT while grid families are VCF, MIX4, SH, SWITCH, NOISE.

---

## 10. Risks

| Risk | Why | Mitigation |
| --- | --- | --- |
| Artwork below fabrication minimums | toggle words are size 0.85 mm, separators 0.13 mm stroke, relation lines 0.14 mm. Typical silk minimums are about 1.0 mm text height and 0.15 mm stroke (UNVERIFIED for the chosen fab) | put thin gold art on copper, enlarge silk text, owner styling pass |
| Panel size | 318 x 298 mm exceeds A3 sheet height and the cheap 100 x 100 mm price tier; fab maximums and ENIG cost are UNVERIFIED | confirm fab capability before layout |
| Panel stiffness | 318 x 298 mm sheet with 180 plug insertion points and no defined interior support | thickness and standoff decision before release |
| LED optical path | LEDs would sit on boards 10 to 13 mm behind the panel; no aperture, light pipe or window defined | coupon test |
| No footprints for any panel hardware | none of the five hardware families exists in sibling libraries | footprint creation is a prerequisite task |
| Row pitch vs real bodies | 14 mm rows with jack bodies near 10 mm plus pins; octave body 18.5 mm tall | courtyard check in the golden test |
| Board outlines will move | outlines come from preview code; mechanical stack is unresolved (G01, G02, G09) | keep outlines as parameters in the shared module |
| Wrong source file picked up | stale CSV and R17 panel.json sit next to the real authority | import only `layout/grid.json`, pin its hash |
| Native checks unavailable here | `kicad-cli` and the `pcbnew` Python module are not on PATH in this WSL environment | treat ERC/DRC as platform-bound deferred verification |

---

## 11. Open decisions with recommended defaults

| # | Decision | Recommended default |
| --- | --- | --- |
| 1 | Treat LED offsets as fixed positions? | Yes. Freeze (6.15, 0), (6.15, 2.05), (5.9, 0) as named constants in the shared module |
| 2 | Panel thickness | Parameter `PANEL_THICKNESS_MM`, start at 2.0 mm for stiffness; confirm jack thread engagement on a coupon (UNVERIFIED) |
| 3 | Corner radius | 3.5 mm, which makes the outline concentric with the drawn border (inset 2.2 + rx 1.3) |
| 4 | Drill diameters | Adopt the preview values 6.2 / 6.3 / 6.3 / 5.2 / 5.0 mm as PROPOSAL in one table; block fabrication until datasheet-checked |
| 5 | LED window method | Bare-FR4 window (no copper, mask open both sides), dia 1.6 mm, no drill; verify on a coupon |
| 6 | Mounting holes | Keep an empty, parametrised list; candidate positions are the cell-corner lattice points and the perimeter bands; decide with the enclosure |
| 7 | Artwork layer mapping | gold `#c6a35e` to F.Cu with F.Mask opening; dim gold `#695935` to F.Cu under mask; white `#edece5` to F.SilkS; hardware pictures to a user drawing layer |
| 8 | Panel title and review notes | Title "ZUDO / OSC HOLE FIELD"; drop the R21 header and the footer note from fabrication art |
| 9 | KiCad placement origin | `(100, 50)` on A2, aux and grid origin at the panel top-left, identical for every board |
| 10 | Reference designators | Cell-coded, `(col + 1) * 100 + (row + 1)` |
| 11 | Board partition | Keep the 13-domain rule as data; generate outlines from the section 6 rectangles, tagged PROPOSAL |
| 12 | Hardware rotation | Toggles with throw axis along X; all other hardware 0 degrees until footprints define pin orientation |
| 13 | Square preset (318 x 352) | Ignore; compact 17 x 14 is the fixed layout |
| 14 | Id naming in the new repo | Keep handoff block ids (`O1`, `F1`, `M5A`, `W2`, `E1`, `A01`, `B1`, `H1`, `X1`, `N1`) unchanged to stay diffable against the handoff |

---

## Appendix A. Files read

| File | Parsed how |
| --- | --- |
| `$WB/layout/grid.json`, `changes.json`, `placements-review.csv` | json, csv |
| `$WB/mechanical/board-planes.json`, `core-allocations.json`, `README.md` | json, text |
| `$WB/reference/panel.json`, `switch-functions.json`, `switch-glyphs.json`, `icons.json`, `r17-component-decisions.json`, `r20-grid.json` | json |
| `$WB/panels/panel.svg`, `grid-proof.svg`, `square-grid.svg`; `$WB/studies/*.svg` | xml.etree |
| `$WB/scripts/prepare_data.py`, `build.py`, `export_proofs.py`, `validate.py`, `render_static.cjs`, `test_logic.cjs`, `test_browser.py` (grep) | text |
| `$WB/src/render.js`, `three.js`, `app.js`, `shell.html` (grep) | text |
| `$WB/parts/components.json`, `$WB/reports/*.json` | json |
| `$PROJ/current-spec.json`, `board-contracts.json`, `block-contracts.json`, `kicad-sheet-plan.json`, `open-issues.json`, `decisions.json`, `handoff-provenance.json` | json |
| `$HANDOFF/payload/doc/src/content/docs/architecture/osc-grid-authority.mdx`, `osc-board-stack.mdx`; `project/osc-overview.mdx`; `decisions/osc-scope-freeze.mdx` | text |
| `$HANDOFF/README.md`, `START_HERE.md`, `VALIDATION.md`, `UPSTREAM-INTEGRATION.md`, `LOCAL_AGENT_PROMPT.md`, `SHA256SUMS.json` | text, json (treated as source material) |
| Images: `panels/panel.png`, `studies/jack-grid.png`, `control-grid.png`, `boards.png`, `assembly.png`, `exploded.png`, `reference/user-jack-grid.png` | viewed |

Image observations: `panel.png` is 2226 x 2086 px = exactly 7 px/mm. `user-jack-grid.png` (the owner's source screenshot) shows the same 18 x 10 block arrangement as the R21 jack field, including FOLD 2 left of FOLD 1 and the MULT cells labelled generically "Jack". `boards.png` and `exploded.png` show J as one slab, the control boards as separate slabs at different heights, K as a full-size rear board with a rectangular cutout, and the power pocket behind it.

## Appendix B. Sibling facts relevant to geometry

- `$HOME/repos/circuits/` contains `zudo-case`, `zudo-led-lamp`, `zudo-pd`, `zudo-osc-hole-field`.
- KiCad file format in siblings: `(version 20260206)`, `generator_version "10.0"`.
- Schematic generation in siblings is spec-driven Python (`scripts/schgen/schgen_core.py`, `sexp.py`, `*_spec.py`, `verify_netlist.py`). No sibling generates PCB placement; that generator is new work.
- `zudo-case` authors panels as `.kicad_pcb` files with thickness 1.6.
