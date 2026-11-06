# Owner-authorized repository delivery - 2026-10-18

The owner approved adding the already reviewed ZIP and fabrication drawing to
existing draft PR #287 for download on Mac. The complete delivery is
`delivery/GH4-JLC-submission-candidate-537ab6a.zip`, 313203 bytes, SHA256:

`6d6bc6ca293613113df26dec0c7bf5f532cee08436fafa4097cf55eb73c37154`

It is byte-identical to the reviewed local delivery. It does not contain itself
or this publication addendum. The original package manifest describes the original
34-entry bundle; this addendum, Git attributes and delivery copy are publication
wrappers outside that manifest. Do not rerun the historical finalizer in this
published directory: build future revisions in a fresh isolated output directory
without `delivery/` to avoid nesting previous delivery archives.

Download and unzip the outer delivery bundle locally. The inner
`GH4-fabrication-candidate.zip` is the fabrication-upload candidate; upload BOM.csv
and CPL.csv only to their assembly inputs when separately authorized. The outer
bundle also contains evidence/scripts and is not the fabrication upload archive.
The fabrication PDF is separately downloadable for inspection.

The package README/REVIEW statements that no commit/push was made describe the
earlier local preparation checkpoint. This later owner authorization permits
normal fast-forward publication only. It does not authorize supplier upload,
contact, order, payment, merge, or physical validation. Original native exports,
canonical boards, viewers, historical stages and parent PR #286 remain unchanged.

Library delivery was attempted using the supported batch helper. Sandbox network
access failed before preparation; the approved host retry reported
`Library prepare_uploads is not available`. No Library IDs were produced. The
owner then explicitly authorized this repository route; no guessed download URL
or alternative transfer service was used.

Before publication, current remote head and local base both resolved to
537ab6a60272437458f1bfe923ca361c8a2ed09e. Direct existing component validation
passed before/after (manual inventory 68 lines, no schematic/placement binding,
pin-asset check performed). This avoids the earlier pnpm dependency-reconciliation
failure; no toolchain install or whole OSC regeneration is run. Native ERC/DRC
are inherited unchanged; package independent review is PASS_LOCAL_CANDIDATE_ONLY.
CI status is reported separately; no CI or supplier acceptance is inferred.
Initial staged whitespace checks flagged preserved Windows CRLF, the original
generator's final blank line, and ASCII-encoded PDF internals. Local attributes
retain those reviewed bytes, accept CRLF and that single script's final blank
line, and classify PDF as binary; no reviewed artifact bytes were normalized.

Proposed quantities: five fabricated, two assembled, three bare, subject to quote
support. Remaining gates are exact C161692 part/model alignment and pin 1, supplier
interpretation of separate score-only GM2, actual quantities/settings/quote, and
owner approval before release/payment. Physical fit/solder/continuity are untested.
