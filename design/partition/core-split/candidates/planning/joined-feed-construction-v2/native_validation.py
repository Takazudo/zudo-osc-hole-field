#!/usr/bin/env python3
"""Prepare and execute E16 native requests; preparation never imports pcbnew.

Execution needs parent admission of this immutable checkout. The existing guard
owns worker resources and admission; this module does not create admission tokens.
"""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = next((p for p in HERE.parents if (p / "circuit/WORKFLOW.md").is_file()), HERE)
TARGETS = ("KA-t2", "KB-t2", "KB-p1")
RAILS = frozenset(("+12V", "-12V", "+5V", "AGND"))
SCHEMA = "e16-native-request-v2"
GUARD_KEYS = ("EPIC242_NATIVE_WORKER", "EPIC242_NATIVE_SLICE", "EPIC242_NATIVE_DEADLINE")
AUTHORITY_KEYS = ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "EPIC242_PARENT_ADMISSION_RUN_ID",
                  "EPIC242_PARENT_ADMISSION_SHA", "EPIC242_REVIEWED_HOOK_SHA256", "EPIC242_PARENT_REQUEST_SHA256")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def read_json(path):
    data = Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith(".gz") else data)


def write_json(path, value):
    with Path(path).open("xb") as output:
        output.write(canonical(value))


def sealed_file(base, entry):
    need(isinstance(entry, dict), "manifest requires file path and sha256")
    relative = Path(entry["path"])
    need(not relative.is_absolute() and ".." not in relative.parts, "file must be materializer-relative")
    path = base / relative
    need(not path.is_symlink() and path.resolve().is_relative_to(base.resolve()), "file escapes materialized root")
    need(re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")), "invalid file digest")
    need(path.is_file() and sha(path) == entry["sha256"], "materialized file hash mismatch: " + str(path))
    return path


def validate_mapping(graph, mapping):
    rows = mapping.get("pads", mapping.get("rail_physical_pad_map")) if isinstance(mapping, dict) else mapping
    ports = graph["physical_ports"]
    need(all(p["net"] in RAILS for p in ports), "source graph includes unsupported pad net")
    by_source = {r["source_id"]: r for r in rows}
    need(len(by_source) == len(rows) == len(ports), "mapping must cover every source rail/AGND physical pad exactly once")
    need(set(by_source) == {p["id"] for p in ports}, "mapping/source census differs")
    native_ids = [r["native_pad_uuid"] for r in rows]
    need(len(set(native_ids)) == len(native_ids), "native pad mapping duplicates UUID")
    for port in ports:
        row = by_source[port["id"]]
        need(row["net"] == port["net"], "mapped net differs from source")
        need(re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", row["native_pad_uuid"]), "invalid original native pad UUID")
        if not port["id"].startswith("CS247-"):
            need(row["native_pad_uuid"] == port["id"], "ordinary physical pad must retain original UUID")
            need((row["ref"], row["pad"]) == (port["ref"], port["pad"]), "mapped reference/pad differs")
        need(isinstance(port["all_port_fragments_connected_to_feed"], bool), "source feed verdict missing")
    feeds = Counter(p["net"] for p in ports if p["id"].startswith("CS247-"))
    need(dict(feeds) == {"+12V": 1, "-12V": 1, "+5V": 1, "AGND": 3}, "complete six feed anchors required")
    return rows


def load_materialized(materialized, manifest=None):
    base = Path(materialized).resolve()
    manifest = Path(manifest).resolve() if manifest else base / "manifest.json"
    need(manifest.parent == base, "manifest must live in materialized directory")
    data = read_json(manifest)
    need(data.get("schema") == "e16-materialized-v1", "unsupported materializer manifest")
    targets = data["targets"]
    need(len(targets) == 3 and {t["id"] for t in targets} == set(TARGETS), "all three exact targets required")
    files = {"manifest.json": manifest}
    for target in targets:
        board = sealed_file(base, target["board"])
        need(board.suffix == ".kicad_pcb", "materialized PCB required")
        for kind, suffix in (("project", ".kicad_pro"), ("rules", ".kicad_dru")):
            sidecar = sealed_file(base, target[kind])
            need(sidecar == board.with_suffix(suffix), "matching board project/rule sidecar required")
        graph = read_json(sealed_file(base, target["source_graph"]))
        need(graph["board"] == target["id"].split("-")[0], "source graph board mismatch")
        validate_mapping(graph, read_json(sealed_file(base, target["pad_map"])))
        for section, declared in (("graph_inputs", graph["input_sha256"]),
                                  ("materializer_inputs", read_json(sealed_file(base, target["pad_map"]))["input_sha256"])):
            entries = target[section]
            need(set(entries) == set(declared), "complete " + section + " source seal set required")
            for original, entry in entries.items():
                need(entry["sha256"] == declared[original], section + " original/staged seal mismatch")
                sealed_file(base, entry)
        for kind in ("board", "project", "rules", "source", "source_graph", "pad_map"):
            path = sealed_file(base, target[kind])
            files[target[kind]["path"]] = path
    return data, files


def protected_hashes(root):
    paths = list((root / "boards").rglob("*"))
    paths.extend((root / "design/grid/placements.lock.json", root / "design/partition/core-split/decision.json"))
    return {str(p.relative_to(root)): sha(p) for p in sorted(paths) if p.is_file()}


def check_protected(root, expected):
    need(protected_hashes(root) == expected, "canonical boards, placements or decision changed")


def relative(root, path):
    return str(Path(path).resolve().relative_to(root.resolve()))


def admission_command(root, script, stage, target):
    worker_command = ["python3", script, "worker", "--stage", stage, "--target", target]
    return ["python3", "scripts/kicad/ci_native_admission.py", "--phase", "board",
            "--board", "e16-" + target.lower(), "--seconds", "2580", "--evidence",
            str(Path(stage) / target / "guard.json"), "--", *worker_command]


def phase_commands(script, stage, target, env):
    verify_worker(env)
    prefix = ["bash", "scripts/kicad/run.sh"]
    native_env = ["env"] + [k + "=" + env[k] for k in (*GUARD_KEYS, *AUTHORITY_KEYS)]
    base = ["python3", script]
    filled = str(Path(stage) / target / "filled" / (target + ".kicad_pcb"))
    return [
        ("fill", prefix + native_env + base + ["native-fill", "--stage", stage, "--target", target]),
        ("drc", prefix + ["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "--output",
                          str(Path(stage) / target / "drc.json"), filled]),
        ("connectivity", prefix + native_env + base + ["native-connectivity", "--stage", stage, "--target", target])]


def verify_worker(env, now=None):
    worker = env.get("EPIC242_NATIVE_WORKER", "")
    need(re.fullmatch(r"ci-[0-9]+-[0-9]+-e16-(ka-t2|kb-t2|kb-p1)", worker), "admitted E16 worker required")
    expected_slice = "epic242-w" + worker.encode().hex() + ".slice"
    need(env.get("EPIC242_NATIVE_SLICE") == expected_slice, "worker/slice binding mismatch")
    deadline = env.get("EPIC242_NATIVE_DEADLINE", "")
    need(re.fullmatch(r"[0-9]{10}", deadline), "worker deadline required")
    remaining = int(deadline) - int(time.time() if now is None else now)
    need(0 < remaining <= 2580, "worker deadline expired or exceeds admitted 43-minute budget")
    return worker


def bind_graph_source(materialized_source, graph, graph_input_files):
    """Bind graph's actual normalized-caps input to the exact materializer recipe."""
    models = [read_json(path) for path in graph_input_files if str(path).endswith(".json")]
    models = [model for model in models if isinstance(model, dict) and "objects" in model and "loads" in model]
    need(len(models) == 1, "one exact graph normalized input required")
    spec = importlib.util.spec_from_file_location("e16_staged_caps", HERE / "staged_caps.py")
    caps = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(caps)
    expected = caps.materialize(materialized_source)
    model = models[0]
    for field in ("board", "objects", "loads", "coordinate_offset_mm", "staged_cap_solids"):
        left, right = expected.get(field), model.get(field)
        if field == "staged_cap_solids" and isinstance(right, dict):
            right = {k: v for k, v in right.items() if k != "input_sha256"}
        need(left == right, "graph normalized source differs from materialization recipe: " + field)


def collect_materialized(directories, graphs):
    """Adapt materializer's individual manifests to one staged, sealed index."""
    data = {"schema": "e16-materialized-v1", "targets": []}
    files = {}
    for directory in directories:
        provided = Path(directory).resolve()
        base = provided.parent if provided.is_file() else provided
        manifests = [provided] if provided.is_file() else sorted(base.glob("*-materialization.json"))
        need(manifests, "materializer manifests missing")
        for manifest in manifests:
            manifest_hash = sha(manifest)
            material = read_json(manifest)
            need(material.get("schema") == "e16-source-materialization-v1", "unsupported source materialization")
            target = material["board"] + "-" + material["round"]
            need(target in TARGETS, "unsupported target in materializer directory")
            need(target in graphs, "source graph required for " + target)
            need(not any(t["id"] == target for t in data["targets"]), "duplicate target")
            need(material.get("native_calls") == 0 and material.get("accepted") is False, "materializer must be source-only")
            material_inputs = {}
            for index, (original, digest) in enumerate(sorted(material["input_sha256"].items())):
                path = Path(original)
                need(path.is_file() and sha(path) == digest, "materializer source input changed: " + original)
                staged = target + "/materializer-inputs/" + str(index) + "-" + path.name
                files[staged] = path
                material_inputs[original] = {"path": staged, "sha256": digest}
            outputs = material["output_sha256"]
            for name, digest in outputs.items():
                source = sealed_file(base, {"path": name, "sha256": digest})
                files[target + "/" + name] = source
            files[target + "/" + manifest.name] = manifest
            source = read_json(base / (target + "-source.json"))
            need(hashlib.sha256(json.dumps(source["objects"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                 == material["materialized_source_objects_content_sha256"], "materialized source content seal mismatch")
            graph_path = Path(graphs[target]).resolve()
            graph_hash = sha(graph_path)
            graph = read_json(graph_path)
            need(graph["board"] == material["board"], "source graph board mismatch")
            graph_inputs = {}
            source_inputs = []
            for index, (original, digest) in enumerate(sorted(graph["input_sha256"].items())):
                path = Path(original)
                need(path.is_file() and sha(path) == digest, "graph input changed or unavailable: " + original)
                staged = target + "/graph-inputs/" + str(index) + "-" + path.name
                files[staged] = path
                graph_inputs[original] = {"path": staged, "sha256": digest}
                source_inputs.append(path)
            bind_graph_source(source, graph, source_inputs)
            validate_mapping(graph, material)
            need(sha(graph_path) == graph_hash and sha(manifest) == manifest_hash, "graph or manifest changed during binding")
            graph_name = target + "/source-graph.json" + (".gz" if str(graph_path).endswith(".gz") else "")
            files[graph_name] = graph_path
            def output_entry(name):
                need(name in outputs, "matching board/source/project/rule output required: " + name)
                return {"path": target + "/" + name, "sha256": outputs[name]}
            data["targets"].append({"id": target, "board": output_entry(target + ".kicad_pcb"),
                "project": output_entry(target + ".kicad_pro"), "rules": output_entry(target + ".kicad_dru"),
                "source": output_entry(target + "-source.json"),
                "pad_map": {"path": target + "/" + manifest.name, "sha256": manifest_hash},
                "source_graph": {"path": graph_name, "sha256": graph_hash}, "graph_inputs": graph_inputs,
                "materializer_inputs": material_inputs})
    need({t["id"] for t in data["targets"]} == set(TARGETS), "all three target materializations and graphs required")
    return data, files


def prepare(materialized, graphs, stage, root=None, run_attempt=1):
    root = ROOT if root is None else root
    need(type(run_attempt) is int and run_attempt > 0, "positive exact GitHub run attempt required")
    data, files = collect_materialized(materialized, graphs)
    stage = Path(stage).resolve()
    need((root / ".circuit-cache").resolve().is_relative_to(root.resolve()), "cache must remain within runner repository mount")
    need(stage.is_relative_to((root / ".circuit-cache").resolve()), "stage must be ignored repository .circuit-cache storage")
    need(not stage.exists(), "fresh stage required; previous filled board must never be reset")
    ignored = subprocess.run(["git", "check-ignore", "--", relative(root, stage)], cwd=root, capture_output=True)
    need(ignored.returncode == 0, "stage must be git-ignored")
    protected = protected_hashes(root)
    stage.mkdir(parents=True)
    destination = stage / "materialized"
    destination.mkdir()
    for name, path in files.items():
        out = destination / name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, out)
        need(sha(out) == sha(path), "staging changed exact input bytes")
    write_json(destination / "manifest.json", data)
    load_materialized(destination)
    script = relative(root, HERE / "native_validation.py")
    requests = {}
    for target in data["targets"]:
        identity = target["id"]
        (stage / identity / "filled").mkdir(parents=True)
        for kind, suffix in (("board", ".kicad_pcb"), ("project", ".kicad_pro"), ("rules", ".kicad_dru")):
            source = destination / target[kind]["path"]
            output = stage / identity / "filled" / (identity + suffix)
            shutil.copyfile(source, output)
            need(sha(output) == target[kind]["sha256"], "fresh-copy input hash mismatch")
        requests[identity] = admission_command(root, script, relative(root, stage), identity)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    oracle = {name: sha(root / name) for name in ("scripts/kicad/run.sh", "scripts/kicad/pin.env",
             "scripts/kicad/native_resource_guard.py", "scripts/kicad/ci_native_admission.py")}
    staged_seals = {name: sha(destination / name) for name in files}
    staged_seals["manifest.json"] = sha(destination / "manifest.json")
    packet = {"schema": SCHEMA, "status": "PREPARED; NOT ADMITTED; NOT DISPATCHED", "native_calls": 0,
              "orchestration_commit": head, "github_run_attempt": run_attempt, "manifest_sha256": sha(destination / "manifest.json"),
              "staged_input_sha256": staged_seals, "targets": data["targets"],
              "oracle_sha256": oracle, "worker_source_sha256": sha(HERE / "native_validation.py"),
              "protected_sha256": protected, "requests": requests,
              "process_boundaries": ["guarded host worker", "fill pcbnew process and saved filled board",
                                      "full-severity CLI DRC process without refill", "complete native connectivity process"],
              "admission": "Parent must admit actual run ID, attempt, checkout SHA, reviewed hook and exact request SHA-256; preparation does not grant execution.",
              "required_parent_request_digest_variable": "EPIC242_PARENT_REQUEST_SHA256",
              "preservation": "Fill once; DRC and census inspect identical filled bytes; no phase resets the board.",
              "limits": "Source/native differences retained. Native zone fill need not equal analytic clipped sheets. No finite current/resistance or physical qualification is implied."}
    write_json(stage / "request.json", packet)
    check_protected(root, protected)
    return packet


def load_stage(stage, target, root=None):
    root = ROOT if root is None else root
    stage = Path(stage).resolve()
    need((root / ".circuit-cache").resolve().is_relative_to(root.resolve()), "cache must remain within runner repository mount")
    need(stage.is_relative_to((root / ".circuit-cache").resolve()), "stage escapes ignored repository cache")
    request = read_json(stage / "request.json")
    need(sha(stage / "materialized/manifest.json") == request["manifest_sha256"], "request manifest digest mismatch")
    need(request["schema"] == SCHEMA, "unsupported request")
    need(target in TARGETS, "unknown target")
    need(sha(HERE / "native_validation.py") == request["worker_source_sha256"], "worker source differs from request")
    for name, digest in request["oracle_sha256"].items():
        need(sha(root / name) == digest, "oracle source differs from request")
    for name, digest in request["staged_input_sha256"].items():
        need(sha(stage / "materialized" / name) == digest, "staged input changed")
    data, unused = load_materialized(stage / "materialized")
    check_protected(root, request["protected_sha256"])
    return stage, request, next(t for t in data["targets"] if t["id"] == target)


def append_chain(chain, phase, inputs, outputs, command, returncode):
    record = {"phase": phase, "input_sha256": inputs, "output_sha256": outputs,
              "command": command, "returncode": returncode, "previous_record_sha256": chain[-1]["record_sha256"] if chain else None}
    record["record_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
    return chain + [record]


def verify_chain(chain, complete=False):
    previous = None
    previous_outputs = None
    for record in chain:
        payload = {k: v for k, v in record.items() if k != "record_sha256"}
        need(payload["previous_record_sha256"] == previous and
             hashlib.sha256(canonical(payload)).hexdigest() == record["record_sha256"], "receipt hash chain invalid")
        if previous_outputs is not None:
            for name, digest in payload["input_sha256"].items():
                if name in previous_outputs:
                    need(digest == previous_outputs[name], "phase hash chain input differs from prior output")
        previous_outputs = payload["output_sha256"]
        previous = record["record_sha256"]
    if complete:
        need([r["phase"] for r in chain] == ["fill", "drc", "connectivity"] and
             all(r["returncode"] == 0 for r in chain), "native phase chain incomplete")
    return previous



def verify_authority(request, request_path, env, head):
    need(env.get("GITHUB_RUN_ID", "").isdecimal() and
         env.get("EPIC242_PARENT_ADMISSION_RUN_ID") == env["GITHUB_RUN_ID"], "exact parent admission run ID required")
    need(env.get("GITHUB_RUN_ATTEMPT") == str(request["github_run_attempt"]), "exact requested GitHub run attempt differs")
    need(re.fullmatch(r"[0-9a-f]{40}", head) and head == request["orchestration_commit"] ==
         env.get("GITHUB_SHA") == env.get("EPIC242_PARENT_ADMISSION_SHA"), "exact parent admission SHA required")
    need(env.get("EPIC242_REVIEWED_HOOK_SHA256") == request["oracle_sha256"]["scripts/kicad/run.sh"], "exact reviewed hook digest required")
    need(env.get("EPIC242_PARENT_REQUEST_SHA256") == sha(request_path), "exact parent-approved request digest required; prepare cannot issue approval")
    return ["env"] + [key + "=" + env[key] for key in AUTHORITY_KEYS]



def verify_worker_authority(env, target):
    expected = "ci-" + env["GITHUB_RUN_ID"] + "-" + env["GITHUB_RUN_ATTEMPT"] + "-e16-" + target.lower()
    need(verify_worker(env) == expected, "guard worker differs from exact parent-approved run/attempt/target")

def host_guard_provenance(env, proc=Path("/proc/self/cgroup"), cgroup=Path("/sys/fs/cgroup")):
    worker = verify_worker(env)
    membership = "/epic242.slice/" + env["EPIC242_NATIVE_SLICE"] + "/epic242-" + worker + "-checks.service"
    need(proc.read_text().strip() == "0::" + membership, "host worker is outside actual admitted checks.service cgroup")
    for path, cap in ((cgroup / "epic242.slice" / env["EPIC242_NATIVE_SLICE"], 6442450944),
                      (cgroup / "epic242.slice", 12884901888)):
        need((path / "memory.max").read_text().strip() == str(cap) and
             (path / "memory.swap.max").read_text().strip() == "0", "actual host guard memory/swap cap mismatch")


def native_guard_provenance(env, stage, target, mode, gate=Path("/epic242-gate"), mountinfo=Path("/proc/self/mountinfo"), cgroup=Path("/sys/fs/cgroup")):
    worker = verify_worker(env)
    mounts = {parts[4]: parts[5].split(",") for line in mountinfo.read_text().splitlines() if len(parts := line.split()) > 5}
    need(all("ro" in mounts.get(path, []) for path in ("/epic242-gate", "/epic242-start.sh")), "native gate and startup snapshot require actual read-only mounts")
    request = read_json(gate / "request.json")
    cid = (gate / "container-id").read_text().strip()
    token = request.get("token", "")
    need(re.fullmatch(r"[0-9a-f]{64}", cid) and re.fullmatch(r"gate\.[a-zA-Z0-9]{12}", token), "native gate identity invalid")
    need((gate / "ack").read_text() == token + ":" + cid + "\n", "guard acknowledgement absent or different")
    image = re.search(r"^KICAD_IMAGE='([^']+)'$", (ROOT / "scripts/kicad/pin.env").read_text(), re.M)
    need(image is not None and request.get("image") == image.group(1), "gate pinned image differs")
    need(request.get("container_id") == cid and request.get("worker") == worker and
         request.get("deadline") == int(env["EPIC242_NATIVE_DEADLINE"]), "native gate worker/deadline mismatch")
    expected = ["env"] + [key + "=" + env[key] for key in (*GUARD_KEYS, *AUTHORITY_KEYS)] + ["python3",
        relative(ROOT, HERE / "native_validation.py"), mode, "--stage", relative(ROOT, stage), "--target", target]
    need(request.get("command") == expected, "guard gate did not admit this exact native command")
    # Docker may namespace cgroup root; the read-only guard acknowledgement is
    # issued only after actual host PID/cgroup/cap verification by reviewed guard.
    need((cgroup / "memory.max").read_text().strip() == "6442450944" and
         (cgroup / "memory.swap.max").read_text().strip() == "0", "native container memory/swap caps differ")

def worker(stage, target):
    identity = verify_worker(os.environ)
    need(identity.endswith("-e16-" + target.lower()), "guard worker names different target")
    stage, request, entry = load_stage(stage, target)
    need(identity.split("-")[2] == str(request["github_run_attempt"]), "guard worker attempt differs from exact requested GitHub attempt")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    verify_authority(request, stage / "request.json", os.environ, head)
    verify_worker_authority(os.environ, target)
    host_guard_provenance(os.environ)
    output = stage / target
    need(not (output / "execution.json").exists(), "target already used; filled board cannot be reset")
    board = output / "filled" / (target + ".kicad_pcb")
    sidecars = [board.with_suffix(s) for s in (".kicad_pro", ".kicad_dru")]
    need(sha(board) == entry["board"]["sha256"], "fill must start with exact staged materialization")
    receipts = []
    status = "INCOMPLETE"
    error = None
    try:
        for phase, command in phase_commands(relative(ROOT, HERE / "native_validation.py"), relative(ROOT, stage), target, os.environ):
            verify_worker(os.environ)
            inputs = {relative(ROOT, p): sha(p) for p in [board, *sidecars, stage / "request.json"]}
            log = output / (phase + ".log")
            with log.open("xb") as stream:
                result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False)
            artifacts = [board, *sidecars, log, output / (phase + ".json")]
            outputs = {relative(ROOT, p): sha(p) for p in artifacts if p.is_file()}
            receipts = append_chain(receipts, phase, inputs, outputs, command, result.returncode)
            need(result.returncode == 0, phase + " native process failed; retained log and artifacts")
            need((output / (phase + ".json")).is_file(), phase + " report missing")
            for p in sidecars:
                need(sha(p) == inputs[relative(ROOT, p)], "native phase modified project/rule sidecar")
            if phase != "fill":
                need(sha(board) == inputs[relative(ROOT, board)], "native analysis modified preserved filled board")
            check_protected(ROOT, request["protected_sha256"])
        verify_chain(receipts, complete=True)
        status = "NATIVE PHASES COMPLETED; REVIEW REQUIRED"
    except (ValueError, OSError, subprocess.SubprocessError) as failure:
        error = str(failure)
    finally:
        write_json(output / "execution.json", {"schema": "e16-native-execution-v1", "worker": identity,
            "request_sha256": sha(stage / "request.json"), "status": status, "error": error,
            "chain": receipts, "filled_board_sha256": sha(board), "accepted": False})
    need(error is None, error)


def native_context(stage, target, mode):
    identity = verify_worker(os.environ)
    need(identity.endswith("-e16-" + target.lower()), "native worker target mismatch")
    result = load_stage(stage, target)
    need(identity.split("-")[2] == str(result[1]["github_run_attempt"]), "native worker attempt differs from request")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    verify_authority(result[1], result[0] / "request.json", os.environ, head)
    verify_worker_authority(os.environ, target)
    native_guard_provenance(os.environ, result[0], target, mode)
    return result


def native_fill(stage, target):
    stage, request, entry = native_context(stage, target, "native-fill")
    import pcbnew  # Admission and all input bindings checked before native import.
    need(re.match(r"^10\.0\.6(?:$|[^0-9])", str(pcbnew.GetBuildVersion())), "exact KiCad 10.0.6 required")
    board_path = stage / target / "filled" / (target + ".kicad_pcb")
    before = sha(board_path)
    need(before == entry["board"]["sha256"], "refuse repeat fill of modified board")
    board = pcbnew.LoadBoard(str(board_path))
    need(bool(pcbnew.ZONE_FILLER(board).Fill(board.Zones())), "native zone fill failed")
    pcbnew.SaveBoard(str(board_path), board)
    write_json(stage / target / "fill.json", {"schema": "e16-native-fill-v1", "input_board_sha256": before,
            "filled_board_sha256": sha(board_path), "zone_count": len(list(board.Zones())), "accepted": False})


def reconcile(graph, mapping, native_pads, cluster_by_uuid):
    rows = validate_mapping(graph, mapping)
    native = {p["uuid"]: p for p in native_pads}
    need(len(native) == len(native_pads) and set(native) == {r["native_pad_uuid"] for r in rows},
         "complete native rail/AGND pad census differs from source mapping")
    feeds = {net: set() for net in RAILS}
    for row in rows:
        pad = native[row["native_pad_uuid"]]
        need((pad["ref"], pad["pad"], pad["net"]) == (row["ref"], row["pad"], row["net"]), "native UUID identity/net mismatch")
        need(row["native_pad_uuid"] in cluster_by_uuid, "native connectivity omits pad")
        if row["source_id"].startswith("CS247-"):
            feeds[row["net"]].add(cluster_by_uuid[row["native_pad_uuid"]])
    by_source = {r["source_id"]: r for r in rows}
    source_groups = {}
    native_groups = {}
    for port in graph["physical_ports"]:
        for component in port["component_ids"]:
            source_groups.setdefault(component, set()).add(port["id"])
        cluster = cluster_by_uuid[by_source[port["id"]]["native_pad_uuid"]]
        native_groups.setdefault(cluster, set()).add(port["id"])
    result = []
    for port in sorted(graph["physical_ports"], key=lambda p: p["id"]):
        row = by_source[port["id"]]
        cluster = cluster_by_uuid[row["native_pad_uuid"]]
        connected = cluster in feeds[port["net"]]
        source_peers = set().union(*(source_groups[c] for c in port["component_ids"])) if port["component_ids"] else {port["id"]}
        native_peers = native_groups[cluster]
        result.append({"source_id": port["id"], "native_pad_uuid": row["native_pad_uuid"],
             "ref": row["ref"], "pad": row["pad"], "net": port["net"], "native_cluster": cluster,
             "source_component_ids": port["component_ids"], "source_all_fragments_to_feed": port["all_port_fragments_connected_to_feed"],
             "source_any_fragment_to_feed": port["any_fragment_connected"], "native_pad_to_feed": connected,
             "feed_agreement": connected == port["all_port_fragments_connected_to_feed"],
             "peer_agreement": source_peers == native_peers,
             "source_peer_count": len(source_peers), "native_peer_count": len(native_peers),
             "native_only_peer_count": len(native_peers - source_peers), "source_only_peer_count": len(source_peers - native_peers),
             "agreement": connected == port["all_port_fragments_connected_to_feed"] and source_peers == native_peers})
    return {"pads": result, "pad_count": len(result),
            "source_component_pad_groups": {c: sorted(ids) for c, ids in sorted(source_groups.items())},
            "native_cluster_pad_groups": {c: sorted(ids) for c, ids in sorted(native_groups.items())}, "differences": [r for r in result if not r["agreement"]],
            "native_feed_cluster_count": {net: len(ids) for net, ids in sorted(feeds.items())},
            "source_agnd_feeds_one_component": graph["graph"]["AGND"]["all_three_returns_one_board_component"],
            "native_agnd_feeds_one_component": len(feeds["AGND"]) == 1}


def native_connectivity(stage, target):
    stage, request, entry = native_context(stage, target, "native-connectivity")
    import pcbnew  # No native library load before worker/slice/deadline checks.
    need(re.match(r"^10\.0\.6(?:$|[^0-9])", str(pcbnew.GetBuildVersion())), "exact KiCad 10.0.6 required")
    board_path = stage / target / "filled" / (target + ".kicad_pcb")
    board = pcbnew.LoadBoard(str(board_path))
    conn = board.GetConnectivity()
    conn.RecalculateRatsnest()
    seeds = [p for fp in board.GetFootprints() for p in fp.Pads()] + list(board.GetTracks())
    clusters = Counter()
    cluster_by_uuid = {}
    for item in seeds:
        uuid = item.m_Uuid.AsString()
        if item.GetNetCode() <= 0 or uuid in cluster_by_uuid:
            continue
        members = conn.GetConnectedItems(item)
        ids = {m.m_Uuid.AsString() for m in members if m.Type() != pcbnew.PCB_ZONE_T} | {uuid}
        cluster = min(ids)
        for member in ids:
            need(member not in cluster_by_uuid or cluster_by_uuid[member] == cluster, "inconsistent native cluster census")
            cluster_by_uuid[member] = cluster
        clusters[item.GetNetname()] += 1
    per_net = {net: count - 1 for net, count in sorted(clusters.items()) if count > 1}
    total = conn.GetUnconnectedCount(False)
    need(sum(per_net.values()) == total, "complete native cluster count does not equal full ratsnest")
    pads = [{"uuid": p.m_Uuid.AsString(), "ref": fp.GetReference(), "pad": p.GetNumber(), "net": p.GetNetname()}
            for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() in RAILS]
    graph = read_json(stage / "materialized" / entry["source_graph"]["path"])
    mapping = read_json(stage / "materialized" / entry["pad_map"]["path"])
    result = reconcile(graph, mapping, pads, cluster_by_uuid)
    result.update(schema="e16-native-pad-census-v1", board_sha256=sha(board_path),
            source_graph_sha256=entry["source_graph"]["sha256"], pad_map_sha256=entry["pad_map"]["sha256"],
            native_unconnected_edges=total, native_open_edges_by_net=per_net,
            scope="All rail/AGND pads by original UUID; all-net open-edge count sum-checked. Native pad connectivity cannot prove every source foil fragment, finite resistance/current or physical process.", accepted=False)
    write_json(stage / target / "connectivity.json", result)


def execute(stage, target):
    stage, request, entry = load_stage(stage, target)
    spec = importlib.util.spec_from_file_location("admission", ROOT / "scripts/kicad/ci_native_admission.py")
    admission = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(admission)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    need(head == request["orchestration_commit"], "request SHA differs from checkout")
    forward = verify_authority(request, stage / "request.json", os.environ, head)
    command = request["requests"][target]
    expected = admission_command(ROOT, relative(ROOT, HERE / "native_validation.py"), relative(ROOT, stage), target)
    need(command == expected, "request command changed")
    # This read-only check refuses absent admission before launching any worker.
    args = argparse.Namespace(phase="board", board="e16-" + target.lower(), seconds=2580,
                             evidence=command[command.index("--evidence") + 1], command=command[command.index("--") + 1:])
    admission.admitted_command(os.environ, head, args)
    need(os.environ.get("GITHUB_RUN_ATTEMPT") == str(request["github_run_attempt"]), "exact requested GitHub run attempt differs; refuse rerun receipt reuse")
    boundary = command.index("--") + 1
    command = command[:boundary] + forward + command[boundary:]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--materialized", type=Path, action="append", required=True)
    prep.add_argument("--graph", action="append", required=True, help="TARGET=ABS_SOURCE_GRAPH_JSON; repeated for all three targets")
    prep.add_argument("--stage", type=Path, required=True)
    prep.add_argument("--run-attempt", type=int, default=1)
    for name in ("execute", "worker", "native-fill", "native-connectivity"):
        command = commands.add_parser(name)
        command.add_argument("--stage", type=Path, required=True)
        command.add_argument("--target", choices=TARGETS, required=True)
    args = parser.parse_args()
    try:
        if args.mode == "prepare":
            graphs = dict(value.split("=", 1) for value in args.graph)
            need(len(graphs) == len(args.graph), "duplicate graph target")
            result = prepare(args.materialized, graphs, args.stage, run_attempt=args.run_attempt)
            print(json.dumps({"status": result["status"], "requests": result["requests"]}))
        elif args.mode == "execute":
            return execute(args.stage, args.target)
        else:
            {"worker": worker, "native-fill": native_fill, "native-connectivity": native_connectivity}[args.mode](args.stage, args.target)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print("E16 NATIVE REQUEST REFUSED: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
