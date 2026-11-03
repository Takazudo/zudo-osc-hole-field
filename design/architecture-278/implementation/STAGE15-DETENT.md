# Manual OFFSET: no centre detent, selected part retained

The owner requires a normal continuous rotary manual OFFSET control **without a centre detent/click**. The selected part already satisfies that ordering requirement: **Bourns PTV09A-4020F-B104**,100kΩ, A01 reference **RV1308**. Retain it; no alternative, part substitution, geometry or production-source change is needed.

The exact identity chain is `electrical-standard.json pot_bindings C:A01.OFFSET → pot_104`, `parts-shortlist.json pot_104 → PTV09A-4020F-B104`, and captured candidate BOM `stage10/inventory-report.json packages.RV1308` with matching MPN and PanelUid. The owner evidence bundle names the same exact manufacturer/MPN.

The manufacturer's [PTV09 datasheet](https://www.bourns.com/docs/product-datasheets/PTV09.pdf), rev01/25, physical page0, **How To Order**, separates the code as `PTV09A – 4 | 0 | 20 | F – B | 104`. `4` is horizontal/rear bushingless configuration; the following **option0 means No Detent**. Option2 means centre detent. The remaining fields specify20mm shaft, flat shaft and100kΩ resistance. The diagram's leader lines were visually inspected; this conclusion does not rely on the generic “centre detent option” feature, a family image, or an electrical midpoint.

Manufacturer PDF reacquired2026-10-16, SHA256 `411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558`, matching the retained owner source. [Evidence receipt](stage15-detent/primary-evidence.json) records the locator and exact code interpretation. Raw PDF/visual rendering remain in local cache; no vendor document or oversized artifact is added to Git.

## Addendum to proposed manual-control/factory contract

This addendum supplements the preserved [proposed procedure](STAGE15-PROCEDURE.md). Manual OFFSET has continuous adjustment over ordinary potentiometer travel, no centre click; this does not mean endless rotation or absence of end stops. “Centre” in the proposed checks is a nominal angular/electrical test position, **not a tactile locator or guaranteed zero volts**. Establish a desired baseline by the existing meter-guided procedure; never instruct the operator to find a centre click. Record actual setting and direction of approach for repeatability checks.

The owner's continuous by-ear/meter musical use remains approved, without prescribed-voltage accuracy at knob positions. The2mV post-factory-calibration static-path and1mV same-setting load-change criteria remain unchanged. A later incoming/assembled-part inspection can confirm the supplied ordering option and absence of centre click, but no physical inspection, calibration or performance qualification occurred here. The proposed factory procedure remains unadopted.

Independent review, exact identity/option mutation tests and historical preservation checks accompany the report. All prior evidence and protected files are retained. Native/CAD/simulation/hardware NOT RUN; PR286 remains draft/unmerged and parked PRs unchanged.
