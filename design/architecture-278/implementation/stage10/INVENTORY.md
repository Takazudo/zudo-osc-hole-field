# A01 source inventory and ownership delta

A01 OFFSET 1 contains 90 complete packages: 29 retained K packages, 59 JR packages and two P packages. The live captured specification matches 118 unit records and 285 physical pin records, including 16 NC pins, against the retained source ledger. All 17 explicit bypass associations are preserved with their complete target packages. Nine fixed panel devices comprise three jacks, four LEDs and two pots; their locked XY and identities remain unchanged.

`inventory-report.json` exposes the complete package/unit/pin inventory, 55 connected nets, every cross-owner endpoint and all NC endpoints. The three proposed owner roles are rear core, front jack and front control. These are candidate ownership assignments, not proof of physical hosting or a prescribed placement. Header hardware and transport conductors are separate additions; connected-net counts are not wire counts.

The complete 5,904-package ownership overlay starts from Stage7. Only the 90 A01 entries change candidate host names. Exactly 29 A01 K references belong to the prior 2,572 non-OSC K population, leaving 2,543 non-OSC K packages and all 13 POWER packages unresolved. The report lists every member of these sets. All other packages retain their prior candidate labels; this does not upgrade those labels to accepted hardware.

Twenty captured package MPN fields remain unselected. RV1308 is captured as PTV09A-4020F-B104 while its fixed-panel component metadata says B103. The B104 captured circuit identity and existing footprint are preserved; the mismatch remains explicit and requires later component/assembly resolution. No silent substitution or new source selection is made.

Focused mutations cover exact live pin/net/NC identity, complete units, bypass ownership, MPN identity and the prior ownership overlay. The generator never executes CAD or simulation. Native/ERC/DRC, physical hosting, electrical performance and hardware acceptance remain NOT RUN or OPEN.
