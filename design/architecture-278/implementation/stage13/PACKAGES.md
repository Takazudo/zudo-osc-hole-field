# A01 reference-capacitor package overlay

This authored scalar package study replaces only C7101/C7102 candidate package geometry. It preserves all90 complete source packages/118 units, their pins/nets, all fixed controls and the exact other88 placement records, including C7107. No earlier geometry, CAD or support structure changes.

C7101 uses T491C475K050AT, C case maximum6.3×3.5×2.8mm, at[251.5,191.5], rear0°. C7102 uses T491D226K035AT, D case maximum7.6×4.6×3.1mm, at[251.5,203], rear180°. Both sit on retained70.8mm pad face. Their maximum rear extents73.6/73.9mm remain inside the preceding5mm package-height planning envelope; this is not whole-enclosure fit.

The exact KEMET T491 family PDF (SHA c3c5bb70009b606c87b40156259670ca9c8452f172b73faa9e2dbf2fcee3522d) printed15/physical14 was visually inspected. Table2 densityB supplies C lands2.37×2.23mm, gap2.57mm, courtyard7.82×4.00mm; D lands2.37×2.43mm, gap3.87mm, courtyard9.12×5.10mm. Positive stripe is assigned candidate pin1 at localnegativeX; rear reflection then quarter-turn yields actual pad coordinates. This is explicit polarized-package registration, not a manufacturer numeric-pin claim. Package input is cross-bound to the selected capacitor input and actual source inventory. Canonical0603 footprints remain historical only and are not claimed suitable for these parts.

The two new envelopes are screened against every retained A01-core package, the other new capacitor, rearGH, all DIN contacts/flange holes/body projection, mounting washer/tool reservations, handle attachments and core board edges. U7101 courtyard gaps are0.45mm and0.64mm. Required additional courtyard gap0.25mm and board edge0.5mm are engineering screening allowances, not universally qualified manufacturing rules. Eight historical other-function XY projections remain reserved with unknown new depth/solid; no unassigned space becomes free. Solder mask, stencil, polarity inspection, copper implementation and installed neighbor/service fit remain unqualified.

Actual local pin separations change as follows (straight-line lower bounds, not routed lengths):

| Path | Prior mm | Candidate mm |
| --- | ---: | ---: |
| C7101+ to U7101 VIN |5.433|4.865|
| C7101− to U7101 GND |4.101|8.904|
| C7102+ to U7101 VOUT |6.468|5.404|
| C7102− to U7101 GND |7.600|4.145|
| C7107+ to U7101 VIN |2.828|2.828|
| C7107− to U7101 GND |4.862|4.862|

The larger input capacitor's ground separation worsens materially; C7107 stays local and unchanged. Neither separation nor nominal capacitance proves bypass impedance, loop area, REF5050 stability or current return quality. No route through an IC body is implied. Four moved pad endpoints and all incident baseline graph edges are listed explicitly in package-report.json. Prior Stage10–12 full-path signal/power/return metrics remain historical and are not current overlay lengths; complete overlay metrics are null pending regeneration.

Package source checks pass only these bounds. Effective capacitance/ESR, tantalum startup/reverse/inrush conditions and manufacturer qualification belong to the capacitor study. Native KiCad/ERC/DRC, simulation and physical validation were NOT RUN. Mechanical support, straps and cassette work remains frozen.

The frozen Stage11 refined frame bounds, unselected strap lane bounds and cassette sweep are also screened read-only in commonXYZ. Neither larger package intersects those modeled envelopes. This does not select the strap option or complete its unknown terminal-block/contact/support solids. The5mm height check is the retained engineering package envelope, not manufacturer or physical qualification.
