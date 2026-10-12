#!/usr/bin/env python3
"""Verify lossless source-keyed copper dispositions without local raw outputs."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "package.json").exists())


def main():
    folder = HERE / "evidence/pad-regions"
    encoding = json.loads((folder / "disposition-encoding.json").read_text())
    source = (ROOT / encoding["source_index_path"]).read_bytes()
    assert hashlib.sha256(source).hexdigest() == encoding["source_index_sha256"]
    index = [json.loads(line) for line in gzip.decompress(source).splitlines()]
    copper = [record for record in index if record["kind"] in ("segment", "via")]
    assert len(index) == 133902 and len(copper) == 133551
    for concept, receipt in encoding["outputs"].items():
        compact = json.loads(gzip.decompress((folder / receipt["compact"]).read_bytes()))
        assert compact["count"] == len(copper) == len(compact["records"])
        assert compact["canonical_disposition"] == "UNCHANGED"
        decoded = []
        for ordinal, row in enumerate(compact["records"]):
            assert row[0] == ordinal and len(row) in (3, 4)
            item = copper[ordinal]
            start, end = item["source_span"]
            decoded.append({
                "object_key": f"{start}:{end}:{item['sha256']}",
                "scope": compact["scope_codes"][row[1]],
                "candidate_disposition": compact["candidate_disposition_codes"][row[2]],
                "canonical_disposition": compact["canonical_disposition"],
                "base_offset_mm": row[3] if len(row) == 4 else compact["default_base_offset_mm"],
            })
        raw = (json.dumps(decoded, sort_keys=True, separators=(",", ":")) + "\n").encode()
        assert hashlib.sha256(raw).hexdigest() == receipt["raw_json_sha256"]
        zones = json.loads((folder / f"{concept}-zones-rule-areas.json").read_text())
        assert len(zones) == len(index) - len(copper) == 351
        print(f"PASS {concept}: 133551 copper records reconstructed exactly; 351 zone/rule records retained")


if __name__ == "__main__":
    main()
