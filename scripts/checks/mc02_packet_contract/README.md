# MC02 offline packet contract

This supplemental contract reconciles the retained historical extraction at
`690366aa69450b642f7daee2cb809eb5ded38d63` and candidate engineering inputs at
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f`, against packet
`af027d73c90de3ad9510d952534fea026cd0f752`. It never updates the packet, sources,
geometry or a Gate A verdict.

```sh
python3 scripts/checks/mc02_packet_contract/contract.py > /tmp/mc02-packet-contract.json
python3 -m unittest discover -s scripts/checks/mc02_packet_contract -p 'test_*.py'
```

The checkout must contain the manifest's pinned candidate bytes; its Git object
store must contain the exact historical and packet commits. Missing objects or
changed bytes fail closed. No fetch, download or substitute revision is used.
The manifest retains eleven historical blob IDs, candidate input digests and
the exact unresolved reference sets. The report labels historical and candidate
current scenarios separately, including normal, one-post-open and all-posts-open
conditions. It cannot treat the old single-post result as the candidate all-post
result. All 26 unplaced ICs and 31 NOT SHOWN latch IDs remain unresolved.

The consumed record projection is recomputed by extracting only `projection`
and `projection_sha256` from each revision's own hash-verified kernel AST (historical and c6 projections differ). Its
numerical imports and solver do not run. Stored coupling results are checked
for source binding, 56 numeric records and the exact five intentional nulls
(three STATIC-only and two WIPER-only). Nulls cannot be converted to zero or
accepted when an evaluated pair lacks a reference. This is evidence
reconciliation, not independent recomputation of electromagnetic/current models.

Mutation tests cover wrong historical identity, scenario conflation, missing
members, geometry/projection drift and semantic null misclassification. The
repository's Python test discovery finds this directory without native tools.

No integrated-head verification, physical qualification, formal Gate A ruling,
DRC, fill, routing-hold release, hardware adoption or manufacturing is supplied.
