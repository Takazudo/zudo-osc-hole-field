# MC02 supplemental latch height audit

This offline audit binds the candidate body-height study to engineering source
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f`. It is separate from owner evidence,
canonical geometry and the historical MC02 packet. It does not select parts,
change placement or establish mounted clearance. All 31 access outcomes remain
`NOT SHOWN`; mounted heights remain unknown.

Run from a checkout containing the pinned input bytes:

```sh
python3 scripts/checks/mc02_height/audit.py \
  --murata-source /path/to/retained/product-data.json > /tmp/mc02-height-report.json
python3 -m unittest discover -s scripts/checks/mc02_height -p 'test_*.py'
```

The Murata response is an ignored source cache, never downloaded by the audit.
Its required SHA-256 is recorded in evidence.json and the retained acquisition
receipt. Missing or changed bytes fail closed; they must not be replaced with a
same-family source. The Murata raw max field conflicts with its display value;
the audited output preserves the discrepancy and derives 0.9 mm from the
0.8 ±0.1 mm displayed tolerance. A changed response requires explicit review.

Coverage is 88 references: 59 exact named body-dimension candidates, two family
candidates with unresolved orderable suffixes, and 27 unresolved identities.
`exact` describes matching study identity, not hardware qualification or an
owner fact verdict. The two suffix cases are BAT54S,215 and MMBT3906,215.

Source pins include the candidate procedure, package identities, inspected
manufacturer PDFs, exact OPN mapping and retained dimensional facts. The numeric
PDF extractions were independently reviewed; this program checks retained bytes
and applicability but is not a PDF dimension parser. It does not infer solder,
standoff, latch sweep, finger/tool access or assembled tolerances.

The prior engineering aggregate PASS remains separate. No native/regeneration,
DRC, fill, hardware adoption or manufacturing is performed by this command.
