# Untested JR140 single-layer targets

Select the nearest24 eligible native component pairs excluding the six targets already screened. Search each with only F.Cu or only B.Cu as the permitted routing layer,0.025mm lattice, weight1 and300000-expansion cap. Guarded48-case run passed in125s. Three searches returned proposals:45 objects for U5213.3,27 for R8487.1, and51 for D1508.1.

A single permitted routing layer can still require a via at a terminal on another layer. The D1508 proposal contains one via and is explicitly excluded from the no-via replay. The other two contain72 B.Cu segments in total and zero vias. Their minimum new-to-new cross-net copper gap is23.519825200030525mm. Native acceptance is not inferred from this screen. Selected exact-input replay is in ../jr-two-no-via/. All failures are retained in result.json.
