#!/usr/bin/env python3
"""Prepare a sealed, executable E16 request descriptor without native admission."""
import argparse
import json
from pathlib import Path
import re
import native_validation as validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialized", type=Path, action="append", default=[],
                        help="materializer output directory; repeat for KA and KB")
    parser.add_argument("--manifest", type=Path, action="append", default=[],
                        help="exact individual materializer manifest; repeat for all targets")
    parser.add_argument("--graph", action="append", required=True, help="TARGET=ABS_SOURCE_GRAPH_JSON")
    parser.add_argument("--stage", type=Path, required=True, help="fresh ignored .circuit-cache directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-attempt", type=int, default=1, help="exact proposed attempt; rerun requires a fresh request")
    parser.add_argument("--local-run-id", help="32-hex local run nonce; no GitHub identity is fabricated")
    args = parser.parse_args()
    try:
        validation.need(not args.output.exists(), "fresh descriptor output required")
        validation.need(bool(args.materialized or args.manifest), "materialized directories or exact manifests required")
        graphs = dict(value.split("=", 1) for value in args.graph)
        validation.need(len(graphs) == len(args.graph), "duplicate graph target")
        request = validation.prepare(args.materialized + args.manifest, graphs, args.stage, run_attempt=args.run_attempt, local_run_id=args.local_run_id)
        pin = (validation.ROOT / "scripts/kicad/pin.env").read_text()
        match = re.search(r"^KICAD_IMAGE='(kicad/kicad@sha256:[0-9a-f]{64})'$", pin, re.M)
        validation.need(match is not None, "pinned image digest unavailable")
        descriptor = dict(request, schema="e16-native-validation-descriptor-v2", oracle_image=match.group(1),
            kicad_version="10.0.6", staged_request_path=str(args.stage.resolve() / "request.json"),
            staged_request_sha256=validation.sha(args.stage / "request.json"),
            execution_commands={target: ["python3", validation.relative(validation.ROOT, validation.HERE / "native_validation.py"),
                "execute", "--stage", validation.relative(validation.ROOT, args.stage), "--target", target]
                for target in validation.TARGETS},
            resources={"board_deadline_seconds": 2580, "per_worker_bytes": 6442450944,
                "aggregate_worker_bytes": 12884901888, "swap": 0, "launch_memavailable_floor_bytes": 8589934592,
                "global_slots": ("Operator reserves one global slot; local targets execute serially." if args.local_run_id else
                                 "Parent separately reserves at most two; execute target requests serially or within that reservation."),
                "cleanup": "Existing reviewed guard owns watchdog, producer-first cleanup and labeled-container absence proof."},
            reports={target: {phase: str(args.stage.resolve() / target / (phase + ".json"))
                for phase in ("fill", "drc", "connectivity", "execution", "guard")} for target in validation.TARGETS},
            review="No native result exists at preparation. Full DRC JSON is unfiltered; connectivity differences remain review evidence. All PCBs are unvalidated drafts.")
        validation.write_json(args.output, descriptor)
        print(json.dumps({"status": descriptor["status"], "targets": list(validation.TARGETS),
                          "descriptor_sha256": validation.sha(args.output), "native_calls": 0}))
    except (ValueError, KeyError, OSError) as error:
        print("E16 DESCRIPTOR REFUSED: " + str(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
