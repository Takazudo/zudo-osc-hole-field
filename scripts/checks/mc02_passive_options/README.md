# MC02 blank-MPN requirement and option inventory

This offline audit maps the 27 empty-MPN latch neighbours at engineering source
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f` to **existing UNADOPTED** rows in
`design/readiness/bom-cost-evidence.json`. It does not construct new options or
write to the inventory, schematic, board, placement or supplier order files.

```sh
python3 scripts/checks/mc02_passive_options/audit.py > /tmp/mc02-passive-options.json
python3 -m unittest discover -s scripts/checks/mc02_passive_options -p 'test_*.py'
```

The exact instance, family and package-unit logical key select the specification
part; its designator, role, symbol and footprint must agree with the retained
package. `Part.value` supplies the required nominal value. The representative
symbol MPN is never promoted to the placed part's identity.

Candidate matching requires equality of the existing classifier's series,
family label and numeric nominal value. The parser and candidate consistency
check reuse `scripts/checks/passive_candidates.py`. Cross-value, cross-series and
cross-family/tolerance-label matches are excluded. The MPN consistency check
validates existing rows only; it never inserts a generated candidate into output.
The present sources yield 26 matched rows and one explicit absence: RB1227 at
620 ohms has no exact family/value row. Near-value or network alternatives from
other candidate studies are not substituted.

All 27 matched specification parts lack an explicit tolerance attribute. The
required tolerance is therefore null and candidate tolerance compliance is
`NOT ESTABLISHED`. A classifier label such as 0.1% thin film or 1% thick film
identifies source policy/family, not independently established circuit error
requirements. The audit refuses newly introduced tolerance attributes until a
reviewed parser and interpretation exist. Value/family matching is not proof of
voltage, power, temperature, stability, parasitic, matching or mounted-height
compliance.

Every `selected_mpn` remains null, every option stays UNADOPTED, and every physical
access verdict stays NOT SHOWN. Dated distributor identity receipts are retained
without presenting old stock or prices as current offers. No network, native CAD,
DRC, fill or hardware adoption occurs.

All specification Python files plus observed specification JSON/symbol inputs
and the package, latch, candidate and classifier inputs are SHA-256 pinned.
Runtime symbol-parser code and package initializers are pinned too; drift is
rejected before importing project executable dependencies. Changed bytes require an explicit source review and
rebind; this program does not refresh hashes itself. The JSON output includes
these pins and the engineering source identity. Native aggregate PASS on the
unchanged engineering source remains a separate prior receipt, not a result of
this option inventory.

## Canonical nut-source rebind

Current source is `6df98d6344f87a64938f919b5a35f151203b618c`. Engineering remains
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f`; the original manual-method amendment
`5620eea27dd2e3232f4ba81a4592660c3f439a26` is preserved separately.
`nut_source_amendment` records the subsequent5620eea2-to-6df98d63 metadata-only
change. Only the consumed threading JSON pin changes here. Nut drawing height
is verified; washer, finish/version, screw/grip tolerances and assembly remain
unresolved. This rebind changes no geometry, parts, counts or access outcomes.
