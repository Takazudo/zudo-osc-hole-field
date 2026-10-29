PTV09A opening proposal: import records only, no hardware adoption

Recommendation: retain all current CAD while recording the dimensioned rectangular opening as the reference for a later reviewed correction. Do not emit or apply an oval/round replacement from this packet. Current circles cannot reproduce the recommended opening dimensions, but actual tab interference is not proven.

This packet adds only proposal records under circuit/proposals/ptv09a-opening-20261029/. It changes no footprint, symbol, generator, inventory, BOM, pin assignment or panel position. Both electrical pads1–3 and mounting centers4/5 are preserved explicitly in proposal.json. Four nonadditive alternatives stay separate.

Evidence: Bourns PTV09 REV01/25, physical PDF page0 horizontal/rear recommended PCB layout, physical page1 exact -4 view. PDF SHA256411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558. Prior source drawing/pixel review and calculations are retained without another geometry or baseline run. Prior sharp-rectangle containment bounds are conditional, not a manufacturer replacement-hole specification. Nominal drawing intervals do not establish fabrication or installed stack tolerance.

Precise next action: existing WSL repository owner verifies ZIP SHA/CRC/member hashes, reviews proposal.patch, and applies/commits ONLY its added proposal records in the existing legitimate project repository. Stop if target proposal paths already exist or expected footprint identity differs. Do not initialize Git, export history, select an alternative, modify CAD, run KiCad/DRC/fill, publish, push or merge. Report local commit ID, changed paths and receipt verification through the x0x text-file coordinator.

Future design action: obtain the exact mounting-tab/profile or manufacturer-accepted rounded-opening evidence, finished-hole/plating definition, copper requirements and view registration. Panel spacing and physical retention remain separate later gates. No manufacturer contact or manufacturing action is authorized here.
