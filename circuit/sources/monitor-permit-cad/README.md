# Monitor candidate CAD imports

Three unchanged family footprint imports come from the official KiCad footprint library tag `10.0.0`. The SOT footprints also match the pinned KiCad 10.0.6 image. Unmodified WRL files from tag `8.0.0` live in the project 3D library. No STEP conversion was performed. These are package-family assets, not exact-vendor or installed-fit evidence. The resistor is imported under a candidate-specific footprint name to preserve the existing instrument footprint.

- https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/10.0.0/Package_TO_SOT_SMD.pretty/SOT-23-8.kicad_mod — SHA-256 `275a1c87693f80538dec9617ad6864fd57e5ecdf6663719b8ebf435759d5ac7b`
- https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/10.0.0/Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod — SHA-256 `f341c73aac9dcb553456f68bf3fee3d26eb14acf6d8a1cae82b50418fe1d71ca`
- https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/8.0.0/Package_TO_SOT_SMD.3dshapes/SOT-23-8.wrl — SHA-256 `16984529fce71220d2097396ac625178679078fdcc1a6f1038c9c888d5154ead`
- https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/8.0.0/Package_TO_SOT_SMD.3dshapes/SOT-23-6.wrl — SHA-256 `01fe842f8ca8534456b365e2a38b77b8c61a07e4133d79187d0df9d46037051b`
- https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/10.0.0/Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod — SHA-256 `f050b6a50cc7e6f86291fb7aa8f87b0d02255e21cfbddf291cdccc87e5889794`
- https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/8.0.0/Resistor_SMD.3dshapes/R_0805_2012Metric.wrl — SHA-256 `8ba82403df18104f827f786ef794d9852912dc437e77b62258dc3e6ffe33c5f6`

Per-part CAD receipts retain transformations and open physical checks. Imported license notices remain intact.
