"""Native schematic/library checks of the four OPA4196 candidate trees against their predecessors.

Scope: ERC, netlist export, BOM export and one pcbnew footprint load per tree. There is no
board in these trees, so this runs no DRC and no zone fill. Inputs are reconstructed
disposable trees under .circuit-cache/opa4196-native/{before,after}/<variant>/. They are
treated as data; run this file with `python3 -I`, under `flock /tmp/kicad-native.lock`.
"""
import csv, hashlib, json, re, shutil, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
NATIVE = ROOT / ".circuit-cache/opa4196-native"
OUTDIR = NATIVE / "outputs"
RESULT = HERE / "native-check-result.json"
VARIANTS = ("UNI_ROYAL/BA1", "UNI_ROYAL/RevP", "YAGEO/BA1", "YAGEO/RevP")
SIDES = ("before", "after")
TOP = "candidate/rendered/variant/zudo-osc-hole-field.kicad_sch"
FP_LIB = "candidate/footprints/zudo-osc-hole-field.pretty"
FP_NAME = "SOIC-14_3.9x8.7mm_P1.27mm"
FP_SHA = "d686d259c1e4bed4147735ed25de08a498e8626d082058f4f5e00168017b2337"
TARGETS = {"U110", "U210"}
# Same stub the canonical schematic uses; without a project file kicad-cli ignores the tree-local lib tables.
PROJECT_STUB = ROOT / "schematic/zudo-osc-hole-field.kicad_pro"
BOM_FIELDS = "Reference,Value,Footprint,Manufacturer,MPN,LCSC,${DNP},${EXCLUDE_FROM_BOM}"
FP_PROBE = """
import hashlib, json, sys, pcbnew
lib, name = sys.argv[1], sys.argv[2]
fp = pcbnew.FootprintLoad(lib, name)
if fp is None:
    print(json.dumps({"loaded": False})); sys.exit(3)
pads = []
for p in fp.Pads():
    s, c = p.GetSize(), p.GetPosition()
    pads.append([p.GetNumber(), round(pcbnew.ToMM(c.x), 4), round(pcbnew.ToMM(c.y), 4),
                 round(pcbnew.ToMM(s.x), 4), round(pcbnew.ToMM(s.y), 4),
                 sorted(pcbnew.BOARD.GetStandardLayerName(l) for l in p.GetLayerSet().Seq())])
print(json.dumps({"loaded": True, "build": pcbnew.GetBuildVersion(), "pads": pads}))
"""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def run(cmd: list, log: Path) -> dict:
    r = subprocess.run(["bash", "scripts/kicad/run.sh", *cmd], cwd=ROOT, capture_output=True, text=True)
    log.write_text(f"$ {' '.join(cmd)}\nexit {r.returncode}\n--- stdout\n{r.stdout}\n--- stderr\n{r.stderr}")
    return {"cmd": ["bash", "scripts/kicad/run.sh", *cmd], "exit": r.returncode, "log": rel(log),
            "stdout_tail": r.stdout.strip().splitlines()[-3:], "stderr_tail": r.stderr.strip().splitlines()[-5:]}


def sexpr(text: str):
    tokens, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "()":
            tokens.append(ch); i += 1
        elif ch.isspace():
            i += 1
        elif ch == '"':
            j, buf = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    j += 1
                buf.append(text[j]); j += 1
            tokens.append(("s", "".join(buf))); i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            tokens.append(("s", text[i:j])); i = j
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop(); stack[-1].append(done)
        else:
            stack[-1].append(t[1])
    return stack[0][0]


def kids(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def val(node, key, default=None):
    k = kids(node, key)
    return k[0][1] if k and len(k[0]) > 1 else default


def netlist(path: Path):
    root = sexpr(path.read_text())
    comps = {}
    for c in kids(kids(root, "components")[0], "comp"):
        fields = {val(f, "name"): (f[2] if len(f) > 2 and isinstance(f[2], str) else "")
                  for fs in kids(c, "fields") for f in kids(fs, "field")}
        ls = kids(c, "libsource")
        comps[val(c, "ref")] = {"value": val(c, "value"), "footprint": val(c, "footprint"),
                                "lib": (val(ls[0], "lib"), val(ls[0], "part")) if ls else None, "fields": fields}
    nets = {}
    for nt in kids(kids(root, "nets")[0], "net"):
        nets[val(nt, "name")] = sorted((val(nd, "ref"), val(nd, "pin")) for nd in kids(nt, "node"))
    return comps, nets


def erc_key(v):
    return (v.get("severity"), v.get("type"), v.get("description"),
            tuple(sorted(re.sub(r" \[[^\]]*\]$", "", i.get("description", "")) for i in v.get("items", []))))


def erc(path: Path):
    d = json.loads(path.read_text())
    vs = [v for s in d.get("sheets", []) for v in s.get("violations", [])]
    return d, Counter(erc_key(v) for v in vs)


def bom(path: Path):
    rows = list(csv.DictReader(path.open(newline="")))
    out = {}
    for r in rows:
        for ref in r["Reference"].split(","):
            out[ref.strip()] = {k: v for k, v in r.items() if k != "Reference"}
    return rows, out


def pinmap_check(tree: Path, nets: dict):
    pin_net = {p: name for name, ps in nets.items() for p in ps}
    groups, missing, nc_bad = defaultdict(set), [], []
    with (tree / "candidate/source-records/candidate-pin-map.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    virtual = 0
    for r in rows:
        key = (r["ref"], r["pin"])
        if r["ref"].startswith("#"):
            virtual += 1; continue
        if key not in pin_net:
            missing.append(key); continue
        if r["state"] == "NET":
            groups[(r["net_scope"], r["resolved_label"])].add(pin_net[key])
        elif r["state"] == "NC" and len(nets[pin_net[key]]) > 1:
            nc_bad.append(key)
    split = {f"{k[0]}|{k[1]}": sorted(v) for k, v in groups.items() if len(v) > 1}
    owner = defaultdict(set)
    for k, v in groups.items():
        for n in v:
            owner[n].add(k)
    merged = {n: sorted(f"{a}|{b}" for a, b in ks) for n, ks in owner.items() if len(ks) > 1}
    return {"rows": len(rows), "virtual_power_flag_rows_skipped": virtual, "pins_missing_from_netlist": [list(m) for m in missing][:20],
            "pins_missing_count": len(missing), "label_groups": len(groups),
            "label_groups_split_across_nets": dict(list(split.items())[:20]), "split_count": len(split),
            "nets_merging_distinct_labels": dict(list(merged.items())[:20]), "merged_count": len(merged),
            "nc_pins_on_multi_node_nets": [list(k) for k in nc_bad][:20], "nc_bad_count": len(nc_bad)}


def bom_record_check(tree: Path, exported: dict):
    with (tree / "candidate/source-records/candidate-bom.csv").open(newline="") as f:
        recs = {r["ref"]: r for r in csv.DictReader(f) if r["in_bom"] == "yes"}
    mism = []
    for ref, r in recs.items():
        e = exported.get(ref)
        if e is None:
            mism.append([ref, "absent from export"]); continue
        for rk, ek in (("value", "Value"), ("mpn", "MPN"), ("lcsc", "LCSC"), ("footprint", "Footprint"),
                       ("manufacturer", "Manufacturer")):
            if (r[rk] or "") != (e.get(ek) or ""):
                mism.append([ref, rk, r[rk], e.get(ek)])
    extra = sorted(set(exported) - set(recs))
    fields = Counter(m[1] for m in mism)
    targets = {t: [m for m in mism if m[0] == t] for t in sorted(TARGETS)}
    return {"record_rows_in_bom": len(recs), "exported_refs": len(exported), "mismatch_count": len(mism),
            "mismatch_by_field": dict(fields), "target_mismatches": targets, "extra_count": len(extra),
            "_set": {json.dumps(m) for m in mism}}


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    version = subprocess.run(["bash", "scripts/kicad/run.sh", "kicad-cli", "version"], cwd=ROOT,
                             capture_output=True, text=True)
    image = next((l.split("=", 1)[1].strip().strip("'") for l in (ROOT / "scripts/kicad/pin.env").read_text().splitlines()
                  if "sha256:" in l), None)
    result = {"status": "NATIVE SCHEMATIC/LIBRARY CHECKS ONLY; UNADOPTED candidate; no board, no DRC, no fill; "
                        "not validated or qualified",
              "oracle": {"wrapper": "scripts/kicad/run.sh", "pin_env_image": image,
                         "kicad_cli_version": version.stdout.strip(), "version_exit": version.returncode},
              "inputs": {}, "runs": [], "variants": {}}
    receipt = NATIVE / "after/RECONSTRUCTION-RECEIPT.json"
    result["inputs"]["reconstruction_receipt_sha256"] = sha(receipt)
    parsed = {}
    for v in VARIANTS:
        for side in SIDES:
            tree = NATIVE / side / v
            top = tree / TOP
            tag = f"{side}-{v.replace('/', '-')}"
            o = OUTDIR / tag
            o.mkdir(exist_ok=True)
            stub = tree / "candidate/rendered/variant/zudo-osc-hole-field.kicad_pro"
            if not stub.exists():
                shutil.copyfile(PROJECT_STUB, stub)
            if sha(stub) != sha(PROJECT_STUB):
                raise SystemExit(f"unexpected project file in {tree}")
            sheets = sorted((tree / "candidate/rendered/variant").rglob("*.kicad_sch"))
            result["inputs"][tag] = {"top_sha256": sha(top), "project_stub_sha256": sha(stub),
                                     "sheets_sha256": {rel(s).split(f"{side}/{v}/", 1)[1]: sha(s) for s in sheets},
                                     "footprint_sha256": sha(tree / FP_LIB / f"{FP_NAME}.kicad_mod")}
            runs = {
                "erc": run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "--units", "mm",
                            "-o", rel(o / "erc.json"), rel(top)], o / "erc.log"),
                "netlist": run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
                                "-o", rel(o / "netlist.net"), rel(top)], o / "netlist.log"),
                "bom": run(["kicad-cli", "sch", "export", "bom", "--fields", BOM_FIELDS,
                            "--labels", "Reference,Value,Footprint,Manufacturer,MPN,LCSC,DNP,ExcludeFromBOM",
                            "--group-by", "", "--ref-range-delimiter", "", "-o", rel(o / "bom.csv"), rel(top)],
                           o / "bom.log"),
                "footprint": run(["python3", "-c", FP_PROBE, rel(tree / FP_LIB), FP_NAME], o / "footprint.log"),
            }
            for name, r in runs.items():
                r.update({"tree": tag, "check": name})
                for f in {"erc": ["erc.json"], "netlist": ["netlist.net"], "bom": ["bom.csv"]}.get(name, []):
                    r["output_sha256"] = sha(o / f) if (o / f).exists() else None
                result["runs"].append(r)
            fp_out = (o / "footprint.log").read_text().split("--- stdout\n", 1)[1].split("\n--- stderr", 1)[0]
            fp = json.loads(fp_out.strip().splitlines()[-1]) if runs["footprint"]["exit"] == 0 else {"loaded": False}
            erc_doc, erc_c = erc(o / "erc.json") if (o / "erc.json").exists() else (None, None)
            comps, nets = netlist(o / "netlist.net") if (o / "netlist.net").exists() else (None, None)
            rows, bomd = bom(o / "bom.csv") if (o / "bom.csv").exists() else (None, None)
            parsed[tag] = {"erc": erc_c, "comps": comps, "nets": nets, "bom": bomd}
            result["variants"].setdefault(v, {})[side] = {
                "erc_violations": sum(erc_c.values()) if erc_c else None,
                "erc_by_type": dict(Counter(f"{k[0]}:{k[1]}" for k in erc_c.elements())) if erc_c else None,
                "erc_kicad_version": erc_doc.get("kicad_version") if erc_doc else None,
                "components": len(comps) if comps else None, "nets": len(nets) if nets else None,
                "bom_rows": len(rows) if rows else None,
                "footprint": {"sha256_ok": result["inputs"][tag]["footprint_sha256"] == FP_SHA,
                              "loaded": fp.get("loaded"), "pad_count": len(fp.get("pads", [])),
                              "pad_sizes_mm": sorted({(p[3], p[4]) for p in fp.get("pads", [])}),
                              "pad_x_mm": sorted({p[1] for p in fp.get("pads", [])}),
                              "layers": sorted({tuple(p[5]) for p in fp.get("pads", [])})},
                "pin_map_check": pinmap_check(NATIVE / side / v, nets) if nets else None,
                "bom_record_check": bom_record_check(NATIVE / side / v, bomd) if bomd else None,
            }
            brc = result["variants"][v][side]["bom_record_check"]
            parsed[tag]["bom_rec"] = brc.pop("_set") if brc else None
        b, a = parsed[f"before-{v.replace('/', '-')}"], parsed[f"after-{v.replace('/', '-')}"]
        cmp = {}
        if b["erc"] is not None and a["erc"] is not None:
            new = a["erc"] - b["erc"]; gone = b["erc"] - a["erc"]
            cmp["erc_new_violations"] = [list(k) for k in new.elements()][:30]
            cmp["erc_removed_violations"] = [list(k) for k in gone.elements()][:30]
        if b["nets"] is not None and a["nets"] is not None:
            cmp["nets_identical"] = b["nets"] == a["nets"]
            cmp["net_differences"] = sorted(set(b["nets"]) ^ set(a["nets"]) |
                                            {n for n in set(a["nets"]) & set(b["nets"]) if a["nets"][n] != b["nets"][n]})[:30]
            changed = {}
            for ref in sorted(set(a["comps"]) | set(b["comps"])):
                x, y = b["comps"].get(ref), a["comps"].get(ref)
                if x != y:
                    d = {}
                    if x is None or y is None:
                        d = {"presence": [x is not None, y is not None]}
                    else:
                        for k in ("value", "footprint", "lib"):
                            if x[k] != y[k]:
                                d[k] = [x[k], y[k]]
                        for k in sorted(set(x["fields"]) | set(y["fields"])):
                            if x["fields"].get(k) != y["fields"].get(k):
                                d.setdefault("fields", {})[k] = [x["fields"].get(k), y["fields"].get(k)]
                    changed[ref] = d
            cmp["component_changes"] = changed
            cmp["only_targets_changed"] = set(changed) == TARGETS
        if b["bom"] is not None and a["bom"] is not None:
            bd = {r: [b["bom"].get(r), a["bom"].get(r)] for r in set(a["bom"]) | set(b["bom"]) if a["bom"].get(r) != b["bom"].get(r)}
            cmp["bom_changed_refs"] = sorted(bd)
            cmp["bom_changes"] = {r: bd[r] for r in sorted(bd)[:6]}
        if b["bom_rec"] is not None and a["bom_rec"] is not None:
            cmp["bom_record_mismatches_new_in_after"] = sorted(a["bom_rec"] - b["bom_rec"])[:20]
            cmp["bom_record_mismatches_gone_in_after"] = sorted(b["bom_rec"] - a["bom_rec"])[:20]
        result["variants"][v]["after_vs_before"] = cmp
    result["summary"] = {
        "runs": len(result["runs"]), "nonzero_exit": [f"{r['tree']}:{r['check']}={r['exit']}" for r in result["runs"] if r["exit"]],
        "per_variant": {v: {"erc_new": (len(d["after_vs_before"]["erc_new_violations"]) if "erc_new_violations" in d["after_vs_before"] else None),
                            "erc_removed": (len(d["after_vs_before"]["erc_removed_violations"]) if "erc_removed_violations" in d["after_vs_before"] else None),
                            "erc_after": d["after"]["erc_violations"],
                            "bom_record_new_mismatch": len(d["after_vs_before"].get("bom_record_mismatches_new_in_after", [])),
                            "nets_identical": d["after_vs_before"].get("nets_identical"),
                            "only_U110_U210_changed": d["after_vs_before"].get("only_targets_changed"),
                            "bom_changed_refs": d["after_vs_before"].get("bom_changed_refs")}
                        for v, d in result["variants"].items()}}
    RESULT.write_text(json.dumps(result, indent=1, sort_keys=False) + "\n")
    print(json.dumps(result["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
