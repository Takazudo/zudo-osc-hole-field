"""Offline consistency check of the committed OPA4196 isolated-candidate record.

Checks only the committed patches and receipts against each other. It does not need
the predecessor source archive and proves nothing about compile, native or hardware state.
With --base PATH (the extracted approved-dev-baseline-07ac1be8-20261026/after), it also
checks every predecessor inventory without writing anything.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
VARIANTS = ("UNI_ROYAL/BA1", "UNI_ROYAL/RevP", "YAGEO/BA1", "YAGEO/RevP")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path)
    a = ap.parse_args()
    errors = []
    members = json.loads((HERE / "receipts/member-hashes.json").read_text())["members"]
    located = {"cloud-application-receipt.json": HERE / "cloud-application-receipt.json",
               "apply_isolated.py": HERE / "tools/apply_isolated.py",
               "HANDOFF.txt": HERE / "receipts/APPLICATION-HANDOFF.txt",
               "safety-check.json": HERE / "receipts/safety-check.json"}
    for name, meta in members.items():
        path = located.get(name, HERE / name)
        if not path.is_file() or sha(path) != meta["sha256"]:
            errors.append(f"packet member mismatch: {name}")
    checks = {c["variant"]: c for c in json.loads((HERE / "patches/checks.json").read_text())}
    app = {v["variant"]: v for v in json.loads((HERE / "cloud-application-receipt.json").read_text())["variants"]}
    overlay = {v["variant"]: v for v in json.loads((HERE / "receipts/opa-overlay-receipt.json").read_text())["variants"]}
    recon = {v["variant"]: v for v in json.loads((HERE / "receipts/cloud-reconstruction-receipt-20261031.json").read_text())["variants"]}
    if set(checks) != set(VARIANTS) or set(app) != set(VARIANTS) or set(overlay) != set(VARIANTS) or set(recon) != set(VARIANTS):
        errors.append("variant set mismatch")
    for v in VARIANTS:
        patch = HERE / "patches" / (v.replace("/", "-") + ".patch")
        if sha(patch) != recon[v]["patch_sha256"]:
            errors.append(f"{v}: patch hash differs from reconstruction receipt")
        if checks[v]["files"] != overlay[v]["files"] or checks[v]["files"] != app[v]["changed_files"]:
            errors.append(f"{v}: changed-file bindings disagree between receipts")
        succ, pred = app[v]["successor_inventory"], app[v]["predecessor_inventory"]
        changed = {k for k in set(succ) | set(pred) if succ.get(k) != pred.get(k)}
        if changed != set(checks[v]["files"]) or sorted(changed) != recon[v]["changed"]:
            errors.append(f"{v}: inventory delta is not exactly the five bound files")
        if any(succ[k] != h["proposed_sha256"] or pred[k] != h["before_sha256"] for k, h in checks[v]["files"].items()):
            errors.append(f"{v}: before/proposed hash mismatch in inventories")
        if a.base:
            root = a.base / v
            inv = {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}
            if inv != pred:
                errors.append(f"{v}: predecessor inventory differs under --base")
    for e in errors:
        print("FAIL:", e)
    if errors:
        return 1
    scope = "with predecessor inventories" if a.base else "receipts and patches only; predecessor base NOT checked"
    print(f"PASS: OPA4196 isolated-candidate record consistent ({scope}); UNADOPTED; no native/hardware claim")
    return 0


if __name__ == "__main__":
    sys.exit(main())
