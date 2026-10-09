# Pinned native zone geometry equivalence profile

Run37983217779 at661f96a584e2944354725852a66935ee1c621ccd uses nativeKiCad10.0.6 and the same immutable core baseline/candidate inputs as the complete-warning audit. Four disposable fixtures retain each source F.Cu/B.Cu zone and one footprint. Exact fixture hashes and project/rule bytes independently match the downloaded artifact. No DRC or routing acceptance is claimed by this profile.

For420,374–441,282native vertices per zone, bidirectional native Boolean subtraction proves source/fixture geometry equal in1.40–1.88s. Native-coordinate serialization and SHA256 equality agree in0.066–0.074s. Every1nm vertex mutation is detected. Results and immutable source/artifact identifiers are committed beside this file.

Exact10.0.6 `SHAPE_POLY_SET::Format` serializes all outline/hole vertices and closure flags through `SHAPE_LINE_CHAIN::Format`, but omits arcs. The production helper therefore rejects any nonzero native ArcCount before using this fingerprint; a regression enforces that boundary. It checks exact ordered native coordinates, not a tolerance or approximate geometric simplification. Pinned source URLs/hashes are in `sources.json`.

Future classification retains source and per-fixture native geometry fingerprints in its receipts. The evidence validator requires the declared method and stage signatures to agree. Existing successful Boolean-based audit receipts remain valid; neither method permits missing native warning classification, incomplete fixture coverage or changed source context.
