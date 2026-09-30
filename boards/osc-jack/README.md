# Historical single-J experiment

This directory retains the rejected #38 nine-board-era schematic, PCB and route receipts at base commit `1fc6e5347308fe5e8166d5828ba3ba6fa8e101c7`. It is excluded from the current ten-board manifest. No copper was imported after 180-second fanout and 900-second no-fanout attempts; 5,611 native open edges remained.

Current source projects are `osc-jack-left` and `osc-jack-right`. The historical definition is retained at `design/partition/history/osc-jack-before-66.json`; use the original commit for exact historical lock metadata/reproduction. Do not run current generation over this historical board or treat its reports as half-board evidence.
