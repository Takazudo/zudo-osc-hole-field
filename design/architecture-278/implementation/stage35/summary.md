# Stage35: shortening alone does not establish a serviceable assembly

Source-only design study. No hardware, wire or canonical geometry is adopted.

| Arch / datum screen | Lower length mm | Upper length mm | Nonempty |
|---|---:|---:|---|
| J-SIG / inherited_height_screen | 126.437261 | 130.576540 | True |
| J-SIG / endpoint_box_downward_bow | 127.155134 | 128.576540 | True |
| J-SIG / endpoint_box_signed_bow | 128.437261 | 127.294413 | False |
| J-PWR / inherited_height_screen | 142.299826 | 153.992250 | True |
| J-PWR / endpoint_box_downward_bow | 143.017698 | 151.992250 | True |
| J-PWR / endpoint_box_signed_bow | 144.299826 | 150.710123 | True |

These are continuous necessary intervals for the specified arch family, not complete feasible hardware intervals. See README for the distinct datum assumptions.

| J-SIG length mm | Historical-shape cover spare mm | Cover K4 | All single-end samples inside |
|---:|---:|---|---|
| 129.000 | 0.938055 | True | True |
| 130.000 | 0.438055 | True | True |
| 130.500 | 0.188055 | True | True |
| 130.580 | 0.148055 | False | True |
| 133.000 | -1.061945 | False | True |

## Complete service feasibility remains unestablished

- Shortening lowers the cap; it does not constrain the extra 15 mm released during withdrawal.
- A tracking former needs 7.5 mm travel and <=0.25 mm contact gap; this is a mechanism requirement, not designed hardware.
- The entire obstacle and vertical-removal ledgers include every modeled obstacle; unknown heights are extended through the sweep.
- The post still fails 50 N. Raw cut lengths, repeated-flex radius and wire selection remain unknown.
- A deeper-cover comparison closes only a stated height inequality, not access, guide removal, registration, flex or strength.

See [mock-up.md](mock-up.md) for required unpowered measurements and stop criteria.
