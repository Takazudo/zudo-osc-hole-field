# Proposed JLC quote settings - not submitted

| Field | Candidate value |
|---|---|
| Material / layers | FR-4 / 2 copper layers |
| Overall fabrication size | 80 x 100 mm, including rails |
| Functional board | 80 x 80 mm, one per unit |
| Board thickness / outer copper | 1.6 mm / 1 oz |
| Solder mask / silk | Green / white |
| Finish | Lead-free HASL |
| Assembly service / side | Standard / top only |
| Paste process | Normal lead-free paste evaluation; no special low-temperature substitution |
| Population | J1 only, exact JST BM04B-GHS-TBT(LF)(SN), C161692 |
| Provisional quantity | 5 fabricated; 2 assembled; 3 bare, subject to current quote support |
| Panel arrangement | One-up supplied design with integral rails; no extra array or auto-added rails |
| Scores | Two full-width V-cuts at drawing y10/y90; retain rails through assembly |
| Impedance / electrical operation | No controlled impedance; isolated unpowered continuity coupon |

The quoted quantity split and process are provisional settings, not a supplier
acceptance statement. Do not increase quantity or substitute parts automatically.
The native coupon is intended to evaluate the ordinary process; its published
JST reflow limits do not establish a qualified profile for a supplier's process.

## Checks when a human is ready to upload

1. Upload only the inner fabrication ZIP to the fabrication flow; BOM/CPL go into
   their assembly inputs. The outer delivery ZIP contains evidence and is not a
   fabrication upload archive.
2. Confirm preview shows 2 layers, 80 x 100 overall, the closed rectangle, three
   NPTH holes, and correct top mask/paste/silk. Empty bottom artwork is intentional.
3. Confirm GM2 is explicitly interpreted as two V-scores, not a second board
   outline, internal slots or copper. Both extend across the full width. If the
   importer ignores GM2, stop for CAM interpretation using the supplied PDF;
   do not silently rename it into the perimeter file or add internal routed cuts.
4. Confirm one-up supplied design, two 10 mm rails, no automatic duplicate rails,
   and Standard Assembly. Check any rail-related pricing/handling restrictions.
5. Verify part-match exact manufacturer and complete MPN, C161692 availability,
   one populated J1 per unit, and the requested quantity split.
6. Inspect top-side placement against ALL six lands and pin 1: leftmost signal
   pad X38.125/Y-51.95; MPs X36.275/43.725,Y-48.6. Native CPL is X40/Y-50/0 degrees.
   Supplier model datum or rotation may differ; resolve by visible pad alignment,
   never by an unexplained Y flip or guessed 90/180-degree correction.
7. Confirm lead-free HASL, stencil/paste interpretation (J1 only), scoring process,
   and supplier order notes. Keep rails attached for initial inspection.
8. Obtain the owner's approval of the actual preview and quote before release or
   payment. This package authorizes no vendor contact, upload, cart or purchase.

Suggested fabrication note:

> One unpowered coupon per 80 x 100 mm unit, including two 10 mm rails. GM1 is the
> closed outer profile. GM2 is V-SCORE ONLY: two straight full-span cuts at Y=-10
> and Y=-90 in the shared absolute metric frame. These are not slots. See attached
> fabrication drawing. Retain rails through top-side assembly. Populate only J1,
> exact JST BM04B-GHS-TBT(LF)(SN), C161692. No substitutions or extra array/rails.
