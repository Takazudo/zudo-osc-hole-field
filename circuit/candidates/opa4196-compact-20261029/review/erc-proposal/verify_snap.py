"""Native before/after check of the ERC PROPOSALS on scratch copies (run with python3 -I, under flock).

Usage: verify_snap.py <stage>, where <stage> names a scratch set .circuit-cache/opa4196-native/proposal-<stage>/
(copies of the candidate trees with series-rows.snap.patch and/or led_pin_types.py applied). The
reference is the unmodified candidate output of native_checks.py.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import native_checks as nc  # noqa: E402

STAGE = sys.argv[1]
SNAP = nc.NATIVE / f"proposal-{STAGE}"
OUT = nc.NATIVE / f"proposal-{STAGE}-outputs"
RESULT = HERE / f"verification-{STAGE}.json"


def normalized(path: Path) -> str:
    keep = [l for l in path.read_text().splitlines() if not l.strip().startswith(("(date", "(source", "(tool"))]
    return "\n".join(keep).replace('"unspecified"', '"passive"')


def main() -> int:
    OUT.mkdir(exist_ok=True)
    version = nc.subprocess.run(["bash", "scripts/kicad/run.sh", "kicad-cli", "version"], cwd=nc.ROOT,
                                capture_output=True, text=True).stdout.strip()
    result = {"stage": STAGE, "status": "PROPOSAL VERIFICATION ONLY on scratch copies; candidate trees and repository schematics unchanged; "
                        "no board, DRC or fill", "kicad_cli_version": version, "variants": {}}
    for v in nc.VARIANTS:
        tag = v.replace("/", "-")
        tree, o, base = SNAP / v, OUT / tag, nc.OUTDIR / f"after-{tag}"
        o.mkdir(exist_ok=True)
        top = tree / nc.TOP
        runs = {"erc": nc.run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "--units", "mm",
                               "-o", nc.rel(o / "erc.json"), nc.rel(top)], o / "erc.log"),
                "netlist": nc.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
                                   "-o", nc.rel(o / "netlist.net"), nc.rel(top)], o / "netlist.log")}
        _, erc_after = nc.erc(o / "erc.json")
        _, erc_before = nc.erc(base / "erc.json")
        comps_a, nets_a = nc.netlist(o / "netlist.net")
        comps_b, nets_b = nc.netlist(base / "netlist.net")
        result["variants"][v] = {
            "input_sha256": {nc.rel(f).split(f"proposal-{STAGE}/{v}/", 1)[1]: nc.sha(f) for f in sorted((tree / "candidate").rglob("*.kicad_s*")) if f.suffix in (".kicad_sch", ".kicad_sym")},
            "runs": {k: {"cmd": r["cmd"], "exit": r["exit"], "log": r["log"]} for k, r in runs.items()},
            "output_sha256": {"erc.json": nc.sha(o / "erc.json"), "netlist.net": nc.sha(o / "netlist.net")},
            "erc_before": dict(Counter(f"{k[0]}:{k[1]}" for k in erc_before.elements())),
            "erc_after": dict(Counter(f"{k[0]}:{k[1]}" for k in erc_after.elements())),
            "erc_new": [list(k) for k in (erc_after - erc_before).elements()],
            "nets_identical": nets_a == nets_b,
            "components_identical": comps_a == comps_b,
            "netlist_text_equal_except_pin_type_and_header": normalized(o / "netlist.net") == normalized(base / "netlist.net"),
        }
    RESULT.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({v: {k: d[k] for k in ("erc_before", "erc_after", "erc_new", "nets_identical", "components_identical", "netlist_text_equal_except_pin_type_and_header")}
                      for v, d in result["variants"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
