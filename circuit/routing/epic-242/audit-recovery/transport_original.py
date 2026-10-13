"""Bounded supported transport for the complete original artifact, not audit proof.

fetch-split requires a supported runner's existing GH_TOKEN and read-only Actions
access. It never creates credentials, dispatches jobs, or invokes native tools.
join rechecks every chunk and the original full digest before exposing the ZIP.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

REPOSITORY = "Takazudo/zudo-osc-hole-field"
ARTIFACT = 11671963117
RUN = 38044514132
SOURCE = "4768f2f82e8a4d634f8dc2905429616bfcd20c37"
SIZE = 713393322
SHA256 = "d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5"
CHUNK = 128 * 1024 * 1024


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def api(endpoint):
    return json.loads(subprocess.check_output(
        ["gh", "api", f"repos/{REPOSITORY}/{endpoint}"], timeout=60))


def verify(path, size=SIZE, digest=SHA256):
    if Path(path).stat().st_size != size or sha(path) != digest:
        raise ValueError("full original size/digest mismatch")


def split(path, output, size=SIZE, digest=SHA256, chunk_size=CHUNK):
    verify(path, size, digest)
    output = Path(output)
    output.mkdir(exist_ok=False)
    chunks = []
    with Path(path).open("rb") as source:
        offset = 0
        while block := source.read(chunk_size):
            name = f"original.part{len(chunks):03d}"
            (output / name).write_bytes(block)
            chunks.append(dict(name=name, offset=offset, bytes=len(block), sha256=hashlib.sha256(block).hexdigest()))
            offset += len(block)
    manifest = dict(artifact_id=ARTIFACT, run_id=RUN, producer_commit=SOURCE,
                    bytes=size, sha256=digest, chunk_bytes=chunk_size, chunks=chunks)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def join(folder, destination, size=SIZE, digest=SHA256, chunk_size=CHUNK):
    folder, destination = Path(folder), Path(destination)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    if (manifest["artifact_id"], manifest["run_id"], manifest["producer_commit"],
        manifest["bytes"], manifest["sha256"], manifest["chunk_bytes"]) != (
            ARTIFACT, RUN, SOURCE, size, digest, chunk_size):
        raise ValueError("transport manifest original identity changed")
    expected_count = (size + chunk_size - 1) // chunk_size
    if len(manifest["chunks"]) != expected_count:
        raise ValueError("missing/extra chunks")
    # Validate all paths and exact byte ranges before creating any assembled file.
    for index, row in enumerate(manifest["chunks"]):
        if (row["name"], row["offset"], row["bytes"]) != (
                f"original.part{index:03d}", index * chunk_size, min(chunk_size, size - index * chunk_size)):
            raise ValueError("chunk ordering/path/range changed")
        path = folder / row["name"]
        if path.is_symlink() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise ValueError("chunk size/digest mismatch")
    if destination.exists():
        raise ValueError("destination must be new")
    temporary = destination.with_suffix(destination.suffix + ".partial")
    created = False
    try:
        with temporary.open("xb") as stream:
            created = True
            for row in manifest["chunks"]:
                with (folder / row["name"]).open("rb") as source:
                    while block := source.read(1024 * 1024):
                        stream.write(block)
        verify(temporary, size, digest)
        # Exclusive creation also refuses overwriting a file created during verification.
        import os
        os.link(temporary, destination)
    finally:
        if created and temporary.exists():
            temporary.unlink()


def fetch_split(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    available = next(int(row.split()[1]) for row in Path("/proc/meminfo").read_text().splitlines()
                     if row.startswith("MemAvailable:"))
    if available < 2 * 1024 * 1024 or shutil.disk_usage(output).free < 3 * 1024 ** 3:
        raise ValueError("transport requires 2GiB available memory and 3GiB free disk")
    metadata = api(f"actions/artifacts/{ARTIFACT}")
    execution = api(f"actions/runs/{RUN}")
    if (metadata["id"], metadata["size_in_bytes"], metadata["digest"], metadata["expired"],
        metadata["workflow_run"]["id"], metadata["workflow_run"]["head_sha"]) != (
            ARTIFACT, SIZE, "sha256:" + SHA256, False, RUN, SOURCE):
        raise ValueError("original artifact metadata changed")
    if execution["id"] != RUN or execution["head_sha"] != SOURCE or execution["status"] != "completed" or execution["conclusion"] != "success":
        raise ValueError("original producer not terminal successful exact source")
    (output / "original-artifact.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "original-run.json").write_text(json.dumps(execution, indent=2) + "\n")
    archive = output / "original.zip"
    with archive.open("xb") as stream:
        subprocess.run(["gh", "api", f"repos/{REPOSITORY}/actions/artifacts/{ARTIFACT}/zip"],
                       stdout=stream, check=True, timeout=600)
    split(archive, output / "chunks")
    print("FULL_ORIGINAL_BYTES_VERIFIED; six transport chunks; native/final gates NOT RUN")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    fetch = sub.add_parser("fetch-split")
    fetch.add_argument("output")
    assemble = sub.add_parser("join")
    assemble.add_argument("folder")
    assemble.add_argument("destination")
    args = parser.parse_args()
    if args.mode == "fetch-split":
        fetch_split(args.output)
    else:
        join(args.folder, args.destination)
