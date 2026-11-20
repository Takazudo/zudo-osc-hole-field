# Printed spacers for the board stack: four plain sleeves, two long and two short

Status: candidate for an unvalidated draft. These are geometry files for the owner's printer (DS-38). Nothing here is a measured length, a fit or a load rating, and no board is adopted. The sleeve is the one of decision DS-45 (design review A3, section F8). The four places and the way of fitting follow DS-72 to DS-76 (continuation c2 of that review). Gate A-paper can still change the design.

## Print the plate as it is: 2 long and 2 short sleeves are used, the others are spares

| File | Stands between | Gap | Modelled length | Needed | Spares on the plate |
| --- | --- | --- | --- | --- | --- |
| [stack-spacer-for-19mm-gap.stl](generated/stack-spacer-for-19mm-gap.stl) | JL and K, JR and K | 19.0 mm | 18.8 mm | 2 (JL 1, JR 1) | 8 |
| [stack-spacer-for-17mm-gap.stl](generated/stack-spacer-for-17mm-gap.stl) | P and K | 17.0 mm | 16.8 mm | 2 (P 2) | 4 |

[stack-spacer-set-plate.stl](generated/stack-spacer-set-plate.stl) holds the whole set on one plate: 10 sleeves for the 19.0 mm gap in rows of 5, then 6 sleeves for the 17.0 mm gap in rows of 3. The three files are the ones handed over when the count was 8 long and 4 short. Only the number of sleeves in use changed.

Each sleeve has a 7.0 mm outer diameter and a 3.4 mm bore for an M3 screw that passes through. There is no thread in the plastic and no insert. The two lengths look alike, so keep them apart after printing: a long sleeve on the control board is 1.8 mm longer than the gap there and would lift K off its posts.

## Print upright at 100 % scale and check the length

- Stand each sleeve on its end, with no supports. Any rigid filament will do.
- The sleeves are modelled 0.2 mm short of their gap. The brass posts then set the gap, and a printed sleeve only stops K from sagging between them. ASSUMED: a home printer holds ±0.2 mm on the length; no document supports the figure.
- Measure a printed sleeve. A long one must not exceed 19.0 mm and a short one must not exceed 17.0 mm, so that no sleeve stands taller than the brass posts of its board. Sand a longer one down or print it again.
- An M3 screw must pass through the bore freely.

## The four sleeves stand between jacks and controls, none at a board edge

Places are named by the panel hardware next to them, seen from the front of the panel. Seen from behind, left and right are swapped. The coordinates are those of the placement lock: x from the panel's left edge and y from its top edge, in mm.

| Sleeve | Board | Place | Panel coordinates |
| --- | --- | --- | --- |
| Long, 18.8 mm | Left jack board (JL) | In the top row of jacks, midway between the 1V/OCT jacks of O4 and O5, the fourth and fifth jack from the left, 1 mm nearer the top edge than the jack centres | (74, 28) |
| Long, 18.8 mm | Right jack board (JR) | In the top row of jacks, midway between the SIG jacks of E2 and E3, the fifth and fourth jack from the right, 5 mm nearer the top edge than the jack centres, beside the SIG LED of E2 | (244, 24) |
| Short, 16.8 mm | Control board (P) | In the square formed by the PW pot and the PWM ± pot of O5, the SAMPLE button of H1 and the A / B switch of X1, 2 mm right of its middle | (93, 276) |
| Short, 16.8 mm | Control board (P), under the LED board (EL) | Midway between the TRIG buttons of E2 and E3, 3 mm toward the RISE pots | (244, 230) |

Each place is a plain hole for an M3 screw through the front board and through K. Under the LED board the screw head sits on the control board, and the LED board gets a 7.0 mm hole over it. The board drafts do not have these holes yet; they come with the board work of the stack.

## Put the four screws in before the panel, fasten the posts, then turn the four nuts by hand

1. Before the panel goes on, push an M3 × 25 mm screw through each of the four holes from the front of the board and hold its head down with a strip of tape. Behind the panel the head cannot be reached later, and without the tape the screw slides back when the instrument lies on its front.
2. Slip a sleeve over each screw: a long one on the jack boards, a short one on the control board.
3. Lower K onto the 18 brass posts and fasten K's screw at every post first.
4. Put a nut on each of the four sleeve screws and turn it with the fingers until it is snug. No tool and no thread lock. Use a washer under the nut only if the screw end still comes through the nut with it.
5. Close the lock of a flat cable connector with one fingertip or a plastic tool, and never press K with the palm. For a lock near K's lower left corner, beside the PWM ± pot of O1, hold K's edge next to the connector with the other hand.

The screw is a working figure (ASSUMED, DS-76): M3 × 25 mm with a head of at most 5.5 mm across, not countersunk. Its thread stands 2.8 mm behind K at a long sleeve and 4.8 mm at a short one. The tape is ASSUMED to hold. UNSOURCED: the height of an M3 nut and the thickness of a washer.

To buy, which is the owner's step: 4 screws M3 × 25 mm, 4 M3 nuts and 4 M3 washers.

## A printed sleeve never replaces a brass post

- The 18 power and ground joints stay brass posts of 19.00 and 17.00 mm, because they carry the supply current. They stand in the two rows between the jack boards and the control board and are no part of the steps above.
- A printed sleeve is not the only support of a board, not a datum for the octave selector and not used under a clamped screw near a hot part.
- A sleeve nut is turned by hand only. UNSOURCED: creep of the printed material under screw load.

## K is held by 22 fixings where 30 were planned: the 18 posts and these four sleeves

Decisions DS-43 and DS-45 counted 30 fixings with twelve sleeves. Four of those sleeve places stood on locked pots, and a sleeve at a board corner left 0.8 mm of board beside its hole, so DS-73 to DS-75 keep four places away from the board edges. The earlier rule of this page, to stop each sleeve nut at first contact and to sort the sleeves by length, no longer applies (DS-76): each of the four sleeves stands 70 mm or more from the nearest other fixing of K (DS-66). [The fixing study](../fixings/README.md) holds the list and its checks, and [the mechanics study](../mechanics/README.md) the computed movement of K. Both are paper studies on assumed parameters.

## The three files come from one parameter list

[spacer-set.json](spacer-set.json) holds the dimensions and the counts. The script writes the STL files from it, and the tests read the files back:

```sh
python3 scripts/stack/spacers/spacers.py           # write the STL files
python3 scripts/stack/spacers/spacers.py --check   # fail if a retained file differs
python3 scripts/checks/frozen_studies.py discover scripts/stack/spacers
```

The tests check that every sleeve is a closed solid that faces outward, that its dimensions and volume match the parameter list, that no sleeve is longer than its gap, that the count per board and length is that of the ruled sleeves in the fixing list (`design/stack/fixings/fixing-sites.json`), that this page places every ruled sleeve at its coordinates and names the screw of that list, and that a parameter list which cannot give a printable set is refused with the defect named. They do not check a printed part.

NOT RUN: any print, any fit on a board, any load or creep test.
