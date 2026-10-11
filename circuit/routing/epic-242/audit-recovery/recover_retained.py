"""Reauthenticate retained audit inputs; never execute native tools or dispatch.

Run from the PR241 checkout with downloaded full artifacts in an external cache.
This deliberately calls the original validators without changing their policy.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from scripts.pcbgen import audit_fixture_tasks as a, core_audit_pilot as p
from scripts.pcbgen import core_audit_after as after

SOURCE = "b350905989de9b441aa4ff709a8491d3c753332b"
CONFIG = REPO / "circuit/routing/issue189/core236-task-checkpoints"


def recover(cache, output):
    cache, output = Path(cache).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    if p.revision(REPO) != p.revision(REPO, SOURCE):
        raise ValueError("execution source changed")
    m = json.loads((CONFIG / "manifest.json").read_bytes())
    kernel = a.policy(REPO)
    before_refs = json.loads((CONFIG / "owner-waves-a56f204/all-five-wave-resume-approvals.json").read_bytes())
    recovered = []

    def link(artifact_id, digest, name, local=None):
        metadata = a.github_json("actions/artifacts/" + str(artifact_id))
        a.authenticate_artifact(artifact_id, metadata["workflow_run"]["id"],
                                metadata["workflow_run"]["head_sha"], digest)
        source = cache / (local or (str(artifact_id) + ".zip"))
        with source.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != digest or source.stat().st_size != metadata["size_in_bytes"]:
            raise ValueError("full artifact size/digest mismatch")
        os.link(source, output / name)
        recovered.append(dict(metadata=metadata, verified_full_sha256=actual))
        a.atomic(output / "recovered-artifacts.json", recovered)
        return metadata

    diag = link(11679136451, "b2f5f4d7356eed1b0954e64a6eb7bef7b6195f7ff5a2d1535633eeae42ba2342", "compact.zip")
    native = a.github_json("actions/artifacts/11679236513")
    a.atomic(output / "metadata.json", dict(run=38069793801,
        tested_sha="63f9541aa68ae3e05ee9700ae71dcaea6dfe02f6", diagnostics=diag, native=native))
    old = json.loads((CONFIG / "pilot-38081076014/authenticated-artifact-approval.json").read_bytes())
    for i, ref in enumerate([dict(approval=old, approval_sha256=p.OLD_APPROVAL_SHA)] + before_refs):
        pin = ref["approval"]
        if a.SHA(a.canonical(pin) + b"\n") != ref["approval_sha256"]:
            raise ValueError("historical approval bytes changed")
        link(pin["artifact_id"], pin["artifact_sha256"], f"checkpoint-{i}.zip")
    link(11671779973, "c5971fa98d5235861294e015150242572cb71dd5fc94a862c0587f8f979d881e", "source.zip")
    wanted = {("osc-core-grid-shards-" + stage + "/osc-core" + suffix): (label, suffix)
              for label, stage in [("before", "start"), ("after", "fresh")]
              for suffix in (".kicad_pcb", ".kicad_pro", ".kicad_dru")}
    found = {}

    def visit(z, depth=0):
        if depth > 3:
            raise ValueError("unexpected nested source ZIP")
        for name in z.namelist():
            for suffix, key in wanted.items():
                if name.endswith(suffix):
                    if key in found:
                        raise ValueError("ambiguous source fixture")
                    found[key] = z.read(name)
            if name.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(z.read(name))) as nested:
                    visit(nested, depth + 1)

    with zipfile.ZipFile(output / "source.zip") as z:
        visit(z)
    if set(found) != set(wanted.values()):
        raise ValueError("immutable source artifact missing board/context")
    for (label, suffix), data in found.items():
        folder = output / label
        folder.mkdir(exist_ok=True)
        (folder / ("osc-core" + suffix)).write_bytes(data)
    before, candidate = output / "before/osc-core.kicad_pcb", output / "after/osc-core.kicad_pcb"
    a.validate_manifest(m, before, candidate, kernel)
    leaves, bindings = p.load_approved(m, kernel, output, CONFIG, REPO, before_refs)
    assert len(leaves) == 323
    a.atomic(output / "retained323.json", dict(completed_task_ids=sorted(leaves), count=len(leaves)))
    print("Original validators reauthenticated 323 retained tasks", flush=True)

    # Recover the byte-identical approved bootstrap from a full authenticated wave ZIP.
    after_refs = []
    for wave, artifact_id, local in [(0, 11688551991, None), (1, 11689476370, "after-wave1.zip")]:
        metadata = a.github_json("actions/artifacts/" + str(artifact_id))
        archive = output / f"after-checkpoint-{wave}.zip"
        link(artifact_id, metadata["digest"].removeprefix("sha256:"), archive.name, local)
        execution = a.github_json("actions/runs/" + str(metadata["workflow_run"]["id"]))
        if execution["status"] != "completed" or execution["conclusion"] != "success" or execution["head_sha"] != SOURCE:
            raise ValueError("after run not terminal success at exact execution source")
        with zipfile.ZipFile(archive) as z:
            producer = json.loads(z.read("producer.json"))
            if wave == 0:
                (output / "bootstrap.zip").write_bytes(z.read("geometry/bootstrap.zip"))
                (output / "bootstrap-approval.json").write_bytes(z.read("geometry/approval.json"))
                bindings = after.authenticate_binding(output / "bootstrap.zip", output / "bootstrap-approval.json",
                    m, kernel, REPO, output / "verified-bootstrap", bindings)
        plan = after.load_plan(CONFIG, m, bindings, kernel)
        pin = dict(producer_commit=SOURCE, run=execution["id"], artifact_id=artifact_id,
                   artifact_sha256=metadata["digest"].removeprefix("sha256:"), manifest_sha256=a.identity(m),
                   policy=kernel, orchestration=p.revision(REPO, SOURCE), ledgers=producer["ledgers"])
        approval = output / f"after-approval-{wave}.json"
        a.atomic(approval, pin)
        sha = a.SHA(approval.read_bytes())
        new = p.authenticate_checkpoints(archive, approval, sha, m, kernel, REPO, output / f"after-verified-{wave}")
        leaves = after.reconcile_wave(m, plan, wave, leaves, new, producer, before, candidate, kernel, bindings)
        after_refs.append(dict(approval=pin, approval_sha256=sha))
        a.atomic(output / "after-resume.json", after_refs)
        a.atomic(output / f"wave{wave}-proof.json", dict(status="AUTHENTICATED_PARTIAL; NOT_ELIGIBILITY",
            count=len(leaves), new_task_ids=sorted(new), completed_task_ids=sorted(leaves),
            stage_geometry_sha256=bindings.evidence(m, kernel), approval_sha256=sha, adopted=False))
        print(f"Original validators reauthenticated wave{wave}: {len(leaves)}/426", flush=True)
    packets = after.select_wave(m, leaves, plan, 2, bindings, kernel)
    try:
        a.final_union(m, before, candidate, list(leaves.values()), kernel, bindings)
    except ValueError as error:
        if "incomplete final task coverage" not in str(error):
            raise
    else:
        raise AssertionError("incomplete final union accepted")
    a.atomic(output / "recovery-proof.json", dict(status="AUTHENTICATED_355_OF_426; KEEP_K1402",
        execution_source=SOURCE, policy=kernel, orchestration=p.revision(REPO),
        source_sha256=m["source_sha256"], context_sha256=m["context_sha256"],
        completed_task_ids=sorted(leaves), missing_task_ids=sorted({t["task_id"] for t in m["tasks"]} - set(leaves)),
        completed_count=len(leaves), next_wave=2, next_packets=packets,
        full_coverage_gate="REJECTED_INCOMPLETE", original_final_gates="NOT_RUN",
        legacy_full_native_zip_byte_verification="NOT_RUN; original reviewed producer equivalence retained",
        adopted=False, dispatched=False))


if __name__ == "__main__":
    recover(*sys.argv[1:])
