# Paired K/P connector locality proposal

The source assigns 123 K/P harness pairs to existing connector sites using the
explicit bijection in `control-connector-locality.json`. Both ends move together.
The exact JST BM03B-GHS-TBT(LF)(SN), GHR-03V-S and SSHL-002T-P0.2 identities and
all pin maps remain unchanged. The four JL/P utility headers stay fixed.

The initial assignment consumed alphabetically sorted signal chunks in physical
site order. Against baseline commit 141b508e89030e8465bf750147d529426c60b91f,
a nearest-signal-pad distance study selected a paired-site assignment with a
summed estimate of 6,664.254 mm on P and 25,747.667 mm on K, compared with
29,898.178 mm and 29,695.754 mm. P used retained native pad positions; K used
current source footprint-pad transforms. These are placement-distance proxies,
not routed lengths, noise measurements or proof of routability.

`control_connector_locality.reassign` requires the complete bijection, checks
the baseline header digest and exact part identities, preserves every non-geometric
header field, and proves identical multisets of occupied header and service-hole
geometry. Native P comparison covered all 1,740 pads: exactly the five pads of
each of the 123 headers move; all non-header pads and occupied AGND pad geometry
remain unchanged. The generated netlists retain every pin/net assignment and
change only 123 header origin fields on each board. The component floorplan is
byte-identical. All 195 modeled cable-route geometries and 18 load-power routes
remain unchanged as sets.

The JST eGH evidence bundle retains nominal mounting and mating geometry; it
does not qualify installed clearances, retention, crimping or derating. The
existing K depth and enclosure allocation remain proposals. Old header routes
and electrical receipts are not accepted for the new source. Native K and P
routing, actual copper compliance and installed assembly remain open.

The source-only transition is retained in `peripheral-source-epoch-20261002-connector-locality.json`. It proves complete partition equality after the declared permutation, keeps EL/octave geometry unchanged, and preserves historical native/model receipts. The historical K field audit is checked against its original netlist and explicitly rejected for the new source; the current source has a separate field projection.

Native K comparison also covers all 13,406 pads and 207 physical hole sites.
The 123 moved header groups and their service-hole ownership follow the exact
permutation; occupied geometry and non-header component pads are unchanged.
Both bare K projections report 9,650 open edges, zero DRC errors and zero
parity findings. They retain 477 reported annotation warnings, with capped
categories; neither annotation nor routing is complete. This comparison does
not reuse or update historical current/resistance receipts.
