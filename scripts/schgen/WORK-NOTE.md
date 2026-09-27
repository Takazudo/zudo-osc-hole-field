# Schematic generator work note

Requested result: a deterministic KiCad 10 hierarchical generator with repeated child sheets, complete multi-unit assignment, explicit pin connectivity, attributes, and netlist verification.

Affected authored records: `design/spec/instrument.py` and `design/spec/modules/synthetic.py`. The example is a **synthetic, unvalidated draft**. It uses stock-symbol expressions extracted through the pinned KiCad oracle and has no exact-component evidence, placement lock, or electrical suitability claim.

Actions: generated a master and shared child sheets, added stable designator allocation, no-connect and rail symbols, checked ERC and netlist connectivity against the spec, then changed one specified connection to confirm the verifier rejects it. Remaining work belongs to later issues: replace the fixture with audited project symbols and real module specs; populate the instrument with the actual 11 families and 33 instances; perform physical and electrical design checks.
