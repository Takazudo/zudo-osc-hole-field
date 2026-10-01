# Existing bypass-capacitor identity and lifecycle

Issue #87 first records the existing Murata GRM188R71H104KA93D identity using a
retained manufacturer catalogue response. The exact D suffix is listed, with
180 mm reel / W8P4 paper tape / 4000-piece packaging. The catalogue observation
on 2026-10-01 marks the family plannedDiscontinue and recommendedStatus=false.
No final discontinuation date, remaining stock or factory allocation is inferred.

The new source is distinct from the existing unavailable detailed-datasheet
record, whose zero-hash sentinel remains unchanged. Only exact identity coverage
closes. Pinout, detailed electrical evidence, physical fit and procurement remain
open; no circuit, fitted part, footprint, current requirement or hardware centre
changes. All query/response bytes are retained in the ignored source cache and
project cclogs; a committed acquisition receipt binds the request and response.
The public API used a read-only POST, not an order or supplier contact.

The suggested GRM155R71H104KE14# is 0402 and is not an approved 0603 replacement.
A separate GRM188R72A104KA35D candidate has been researched, but its dedicated
lands, effective capacitance and role-by-role integration remain separate work.
The existing part also appears in filter and noise-coupling roles, so there is
no global substitution. Issue #87 stays open for those obligations.

Component validation, generation and generated-output checks pass after adding
explicit JSON-row locators and updating the inventory's identity summary only.
The detailed source-state summary stays unavailable. Independent source review
confirmed the response hash, exact suffix, packaging and dated lifecycle fields.
Guarded documentation checks, build and strict site checks pass (exit0,50 seconds;
one existing workbench template-link exception remains allowlisted). The parent
reference-diagnostic change was fast-forwarded afterward; component validation and
generation remain clean. Exact combined-source CI is required before merge.

The post-parent aggregate replay exposed two dependent monitor receipts that
bind the updated inventory/passive-owner files. Fresh native ERC/pin-parity and
22 RC runs succeeded; their regenerated reports differ only in input hashes,
with all numerical results and acceptance flags unchanged. Those generated
updates are included rather than treating the first CI failure as a pass.
