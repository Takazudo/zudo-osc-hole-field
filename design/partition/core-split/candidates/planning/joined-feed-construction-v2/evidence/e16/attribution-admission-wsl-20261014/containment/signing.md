# Current owner-delegated signing policy (2026-10-14)

Takazudo's [explicit owner decision](../owner-decision-20261014.txt) supersedes the
external-signer and no-local-provisioning requirements in the historical procedure
below. The local WSL coordinator is the authorized operator/controller delegate.
Dedicated E16-development-only local signing material and the fixed project trust
file may now be provisioned under existing user permissions. Never use unrelated
keys. All three role principals/namespaces remain distinct, but may use the same
dedicated delegated key; these signatures are not independent external approval.
Private material stays outside Git, evidence, logs and artifacts with restrictive
permissions. Existing keys/trust must be reconciled, never overwritten.

Every new description/request, authorization/reservation grant and signed resource
report carries the exact `authorization_policy` from `attribution_admission.py`.
It binds owner Takazudo, delegate wsl-coordinator, local signature provenance, the
verbatim decision SHA, this selected operation, qualification/production request
kinds, zero additional full baselines, required technical review and no retroactivity.
The source verifies the decision bytes and exact policy. Historical requests do
not acquire this authority. No personally reviewed future digest is claimed.

A resource report additionally binds `technical_review` with `path`, `sha256` and
`reviewer_identity`. Its bounded retained JSON has schema
`e16-technical-resource-review-v1`, the actual separate reviewer identity,
`author_identity: wsl-coordinator`, `verdict: PASS`, exact `operation_sha256` and
exactly the report's `evidence` list. The verifier checks its bytes, identity,
verdict and scope. This records real review; string inequality or a local signature
alone does not prove independence. Do not create a passing report after failed or
incomplete qualification. The review file counts in the compact evidence limit.

The compiler, fixed trust pathname/mode, actual OpenSSH commands, role namespaces,
exact-request/live-reservation gates, resource limits and campaign accounting below
remain applicable. The current authority is this owner delegation, not the old
external-owner instructions or fixture keys. Finish source changes and review,
commit, then compile/sign fresh exact packets. Qualification and production remain
separate; no further owner message is needed for eligible in-scope digests.

## Bounded metadata characterization extension (2026-10-15)

The same retained owner decision explicitly authorizes bounded diagnostics. A
new `resource-characterization` request kind answers only the source-reviewed
raw-construction metadata question. It has distinct payload schemas
`e16-attribution-characterization-authorization-v1` and
`e16-attribution-characterization-reservation-v1`, exact request/run/operation
bindings and an actual separate operation-bound technical review. It never
qualifies the numerical pipeline. Current original qualification/production
limits, namespaces and acceptance gates remain unchanged.

The fixed existing trust permits only the established namespaces. Therefore
characterization signatures use `e16-attribution-qualification-authorization-v1`
and `e16-attribution-qualification-reservation-v1` under their existing respective
principals, while the signed JSON retains the distinct characterization schemas
and request kind. `grant_namespace(kind, role)` and `grant_prefix(kind)` encode
these two roles separately. Exact payload checks prevent either request kind's
grant from authorizing the other; namespace reuse is not payload reuse. No new
key, trust edit or signing owner is introduced.

Use `attribution_request.py describe-characterization --output DESCRIPTION`,
then actual separate review of that operation. The review JSON schema is
`e16-characterization-technical-review-v1`, with PASS, exact operation_sha256,
actual reviewer_identity distinct from author_identity `wsl-coordinator`, purpose
`raw-construction-metadata-v1`, resource_status `NOT_QUALIFIED`.
`seal-characterization --description DESCRIPTION --review REVIEW --output REQUEST`
binds its exact bytes. These commands prepare source-bound records; they do not
approve or execute. Genuine exact grants and live admission still follow. A
characterization COMPLETE receipt means its bounded question finished, never
resource qualification or selected numerical attribution.

---

## Historical external-owner procedure (superseded ownership only)

# Missing independent-owner signing setup

No key, approval, reservation or trust store was created in this task. The
following commands are instructions for their actual independent owners, after
review; no placeholder JSON below is an executable request. Host fixture evidence
is not a signed resource qualification and must not be promoted into authority.

The existing [owner handoff](../owner-handoff.md) retains the exact fixed experiment,
original-input identities, grant schemas, compiler CLI, caps and consumption rules.
Its host-SwapTotal=0-only prerequisite is superseded by the reviewed task-local
[containment contract](README.md); its historical source/operation digest is not
the new request digest. Use a fresh description and final clean immutable HEAD.

## Trust owner: public identities before sealing

The fixed store is `/home/takazudo/.config/zudo-e16/attribution.allowed_signers`.
It must be a regular file owned by execution UID 1000, with no group/other write
bits, at most 65536 bytes. Its exact SHA-256 is bound into the request. It lives
outside the checkout and packet; no packet-supplied alternate trust root works.
The file must really exist before `seal-qualification` can hash it.

Provision genuine existing public keys controlled by the independent operator,
controller and resource reviewer. Allowed-signers records have these principal
and namespace fields, followed by the actual public-key type and base64 key:

| Principal | `namespaces` option |
| --- | --- |
| `e16-operator` | `e16-attribution-qualification-authorization-v1,e16-attribution-authorization-v1` |
| `e16-controller` | `e16-attribution-qualification-reservation-v1,e16-attribution-reservation-v1` |
| `e16-resource-reviewer` | `e16-attribution-resource-v1` |

For example, an owner with the three **real public-key files** assigned to the
variables below can assemble and inspect a candidate file without moving private
keys to this machine:

```sh
awk 'NF>=2 {print "e16-operator namespaces=\"e16-attribution-qualification-authorization-v1,e16-attribution-authorization-v1\" " $1 " " $2}' "$OPERATOR_PUBLIC_KEY" > "$REVIEWED_ALLOWED_SIGNERS"
awk 'NF>=2 {print "e16-controller namespaces=\"e16-attribution-qualification-reservation-v1,e16-attribution-reservation-v1\" " $1 " " $2}' "$CONTROLLER_PUBLIC_KEY" >> "$REVIEWED_ALLOWED_SIGNERS"
awk 'NF>=2 {print "e16-resource-reviewer namespaces=\"e16-attribution-resource-v1\" " $1 " " $2}' "$REVIEWER_PUBLIC_KEY" >> "$REVIEWED_ALLOWED_SIGNERS"
ssh-keygen -lf "$OPERATOR_PUBLIC_KEY"
ssh-keygen -lf "$CONTROLLER_PUBLIC_KEY"
ssh-keygen -lf "$REVIEWER_PUBLIC_KEY"
```

Owners must verify fingerprints and role ownership independently. After review,
the execution-account trust custodian installs that candidate at the fixed path
with mode 0600, preserving any existing store for reconciliation instead of
silently replacing it. No key generation, private-key copying or fixture keys.

For a genuinely absent store, the trust custodian's installation commands are:

```sh
install -d -m 700 /home/takazudo/.config/zudo-e16
test ! -e /home/takazudo/.config/zudo-e16/attribution.allowed_signers && test ! -L /home/takazudo/.config/zudo-e16/attribution.allowed_signers && install -m 600 -- "$REVIEWED_ALLOWED_SIGNERS" /home/takazudo/.config/zudo-e16/attribution.allowed_signers
stat -c '%F uid=%u mode=%a bytes=%s' /home/takazudo/.config/zudo-e16/attribution.allowed_signers
sha256sum /home/takazudo/.config/zudo-e16/attribution.allowed_signers
```

Expected: regular file, UID1000, mode600, no more than65536 bytes, and the exact
reviewed public-key records. Existing-store reconciliation remains the trust
owner's action; this continuation executes none of these commands.


## Request preparer: compile exact qualification scope

On the final clean checkout, set fresh absolute output paths `DESCRIPTION` and
`QUALIFICATION_REQUEST` outside tracked files. Then, from the executable source
directory `design/partition/core-split/candidates/planning/joined-feed-construction-v2`:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python attribution_request.py describe --output "$DESCRIPTION"
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python attribution_request.py seal-qualification --description "$DESCRIPTION" --output "$QUALIFICATION_REQUEST"
```

Review the compiler's actual `qualification_request_sha256`, generated 32-hex run
ID, host UID/boot/machine identity, ledger digest, source/toolchain/original input
bindings and selected `host_limits`. The schema is `e16-attribution-request-v1`,
kind `resource-qualification`, operation `e16-selected-attribution-v1`, attempt 1,
qualification null. Sealing is not approval. Do not use the source operation
SHA, a fixture checksum or an old request digest in a grant.

## Operator and controller: exact messages and signatures

Both JSON messages bind these fields copied from the **actual sealed request**:
`request_kind`, `run_id`, `operation`, `limits`, plus its canonical
`request_sha256`. Their `issued_unix` and `expires_unix` must be finite numbers;
issued no later than verification, expiry covering the complete remaining 180s
and the eventual envelope tail. Queue delay can invalidate them.

The operator message additionally has:

```text
schema = e16-attribution-qualification-authorization-v1
approved = true
```

The independent controller message additionally has:

```text
schema = e16-attribution-qualification-reservation-v1
exclusive = true
host = exact sealed host object (UID, boot_id, machine_id)
ledger_sha256 = exact sealed ledger.sha256
```

These true decisions must be made by their genuine owners. A schema example is
not approval and this task produces no message. Use distinct UTF-8 JSON files
(max 64 KiB, no duplicate fields or nonfinite values), with no edits after signing.
After each owner has reviewed its real message and chosen to authorize it, sign
with that owner's existing private key on the owner's signing system:

```sh
ssh-keygen -Y sign -f "$OPERATOR_EXISTING_PRIVATE_KEY" -n e16-attribution-qualification-authorization-v1 "$AUTHORIZATION_JSON"
ssh-keygen -Y sign -f "$CONTROLLER_EXISTING_PRIVATE_KEY" -n e16-attribution-qualification-reservation-v1 "$RESERVATION_JSON"
```

Retain each exact message and adjacent `<message>.sig` (max 16 KiB). On the
execution host, expected cryptographic verification is exit 0 for both:

```sh
ssh-keygen -Y verify -f /home/takazudo/.config/zudo-e16/attribution.allowed_signers -I e16-operator -n e16-attribution-qualification-authorization-v1 -s "$AUTHORIZATION_JSON.sig" < "$AUTHORIZATION_JSON"
ssh-keygen -Y verify -f /home/takazudo/.config/zudo-e16/attribution.allowed_signers -I e16-controller -n e16-attribution-qualification-reservation-v1 -s "$RESERVATION_JSON.sig" < "$RESERVATION_JSON"
```

Signature success alone is not admission: existing code also checks the exact
request bindings, current host/ledger, times, exclusive grant, real reservation
flock and guard custody, actual containment and one-use identity. The numerical
controller obtains its existing live reservation lock; owners must not invent a
lock observation or reuse a fixture grant. A claimed qualification consumes one
diagnostic even on failure; incomplete accounting needs external reconciliation.

After actual qualification, the resource reviewer must separately review and sign
the `e16-attribution-resource-v1` report under principal `e16-resource-reviewer`
and that namespace. It must bind the new operation digest, exact limits, complete
combined evidence and measured costs, cleanup/all phases, expiry and production
admission allowance, as required by `verify_qualification()`. Only then may a
fresh production `seal --description ... --qualification ... --output ...` be
prepared and separately authorized under the production namespaces above.
Neither operation is authorized by this containment task.
