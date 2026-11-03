"""Reconstruct the four isolated OPA4196 OSC candidates from the handoff base + patches.

Independent re-implementation (the archived apply_isolated.py is not executed).
"""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path

base_after, app_dir, dest = (Path(a).resolve() for a in sys.argv[1:4])
receipt = json.loads((app_dir / "cloud-application-receipt.json").read_text())
if dest.exists():
    sys.exit(f"destination exists: {dest}")


def inventory(root):
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            sys.exit(f"symlink: {p}")
        if p.is_file():
            out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


report = {"scope": "ISOLATED DEVELOPMENT ONLY; NOT CANONICAL OR MANUFACTURING", "variants": []}
originals = {}
for v in receipt["variants"]:
    name = v["variant"]
    src = base_after / name
    inv = inventory(src)
    originals[name] = inv
    if inv != v["predecessor_inventory"]:
        diff = set(inv.items()) ^ set(v["predecessor_inventory"].items())
        sys.exit(f"{name}: predecessor inventory mismatch: {sorted(diff)[:5]}")

for v in receipt["variants"]:
    name = v["variant"]
    out = dest / name
    shutil.copytree(base_after / name, out)
    patch = app_dir / "patches" / (name.replace("/", "-") + ".patch")
    r = subprocess.run(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(patch)], cwd=out,
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{name}: patch failed\n{r.stdout}{r.stderr}")
    succ = inventory(out)
    ok_succ = succ == v["successor_inventory"]
    ok_changed = all(succ[f] == h["proposed_sha256"] for f, h in v["changed_files"].items())
    if not (ok_succ and ok_changed):
        sys.exit(f"{name}: successor mismatch")
    report["variants"].append({"variant": name, "files": len(succ), "changed": sorted(v["changed_files"]),
                               "successor_inventory_match": ok_succ, "patch_sha256":
                               hashlib.sha256(patch.read_bytes()).hexdigest()})

for name, inv in originals.items():
    if inventory(base_after / name) != inv:
        sys.exit(f"{name}: original changed")
report["originals_unchanged"] = True
report["status"] = "PASS (file-level reconstruction only; no native/compile validation)"
(dest / "RECONSTRUCTION-RECEIPT.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
