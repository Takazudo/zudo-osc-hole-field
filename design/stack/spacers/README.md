# Printed spacers for the board stack: twelve plain sleeves in two lengths

Status: candidate for an unvalidated draft. These are geometry files for the owner's printer (DS-38). Nothing here is a measured length, a fit or a load rating, and no board is adopted. The set follows decision DS-45 (design review A3, section F8). ST-08 still has to confirm the sites and state the screw lengths, and Gate A-paper can still change the design.

## Print 8 long and 4 short sleeves, plus spares

| File | Stands between | Gap | Modelled length | Needed | Spares on the plate |
| --- | --- | --- | --- | --- | --- |
| [stack-spacer-for-19mm-gap.stl](generated/stack-spacer-for-19mm-gap.stl) | JL and K, JR and K | 19.0 mm | 18.8 mm | 8 (JL 4, JR 4) | 2 |
| [stack-spacer-for-17mm-gap.stl](generated/stack-spacer-for-17mm-gap.stl) | P and K | 17.0 mm | 16.8 mm | 4 (three beside P, one where EL lies in front of P) | 2 |

[stack-spacer-set-plate.stl](generated/stack-spacer-set-plate.stl) holds the whole set on one plate: 10 sleeves for the 19.0 mm gap in rows of 5, then 6 sleeves for the 17.0 mm gap in rows of 3.

Each sleeve has a 7.0 mm outer diameter and a 3.4 mm bore for an M3 screw that passes through. There is no thread in the plastic and no insert. The two lengths look alike, so keep them apart after printing: a long sleeve at a P site would push K off its 17.00 mm posts.

## Print upright at 100 % scale and check the length

- Stand each sleeve on its end, with no supports. Any rigid filament will do.
- The sleeves are modelled 0.2 mm short of their gap. The brass posts then set the gap, and a printed sleeve only stops K from sagging between them. ASSUMED: a home printer holds ±0.2 mm on the length; no document supports the figure.
- Measure a printed sleeve. A long one must not exceed 19.0 mm and a short one must not exceed 17.0 mm. Sand a longer one down or print it again.
- An M3 screw must pass through the bore freely.

## A printed sleeve never replaces a brass post

- The 18 power and ground joints stay brass posts of 19.00 and 17.00 mm, because they carry the supply current.
- A printed sleeve is not the only support of a board, not a datum for the octave selector and not used under a clamped screw near a hot part.
- Never clamp K onto a printed sleeve; see the next section. UNSOURCED: creep of the printed material under screw load.

Each sleeve takes one M3 screw from the panel side, with a washer and a nut on K's rear face. The screw lengths are not stated yet; ST-08 states them.

## Until the design ruling, stop each sleeve nut at first contact

ST-03 attempt a3 computed that a printed sleeve can bend K past its strain limit of 593 microstrain (`design/stack/mechanics/README.md`; plate model and forces ASSUMED, nothing measured). A sleeve that is longer than its posts lifts K. A short sleeve whose nut is drawn down pulls K: at the four sleeves 22 mm from a post, one eighth of a turn beyond contact already exceeds the limit. How a sleeve is fixed is therefore open and goes to the design authority. Until it rules:

- Tighten the 18 post screws first.
- Use a sleeve only if it is shorter than the posts of its gap. The proposed band is 0.05 to 0.30 mm shorter than the measured posts.
- Turn each sleeve nut until its washer touches K, then stop.

## The three files come from one parameter list

[spacer-set.json](spacer-set.json) holds the dimensions and the counts. The script writes the STL files from it, and the tests read the files back:

```sh
python3 scripts/stack/spacers/spacers.py           # write the STL files
python3 scripts/stack/spacers/spacers.py --check   # fail if a retained file differs
python3 scripts/checks/frozen_studies.py discover scripts/stack/spacers
```

The tests check that every sleeve is a closed solid that faces outward, that its dimensions and volume match the parameter list, that no sleeve is longer than its gap, that each length serves the supports of its own boards in the geometry candidate (`design/stack/geometry/stack-candidate.json`), and that a parameter list which cannot give a printable set is refused with the defect named. They do not check a printed part.

NOT RUN: any print, any fit on a board, any load or creep test.
