"""MC04-S13 driver: node capacitance budgets from vendor-model ngspice decks (brief Revision 3, DS-161 to DS-169).

    budget.py --controls          Arm 0 P5, P7, P8 with the study's own runner (P1 to P4 are run outside)
    budget.py --run [--slice-min 25]    start the sweep (refuses if results.jsonl exists)
    budget.py --resume [--slice-min 25] continue from results.jsonl after P1/P3 re-check and docker kill
    budget.py --evaluate          build budget.json from results.jsonl (no simulation)
    budget.py --check             rebuild every deck text and the budget table from results.jsonl; compare

MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

STUDY = Path(__file__).resolve().parent
sys.path[:0] = [str(STUDY), str(STUDY.parents[3])]

import cells  # noqa: E402
import runner  # noqa: E402
from cells import ROOT, Blocked  # noqa: E402
from guard import kill_pinned_containers  # noqa: E402

RESULTS = STUDY / "results.jsonl"
BUDGET = STUDY / "budget.json"
RESULT = STUDY / "result.json"
CENSUS = STUDY / "census.json"
MODELS = STUDY / "models.json"
STATUS = "MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT"

VALUES_PF = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 25, 32, 40, 50, 64, 80, 100]
CANDIDATES_PF = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 32, 40, 50]
C_REDUCED_PF = [0, 25, 50, 100]
CEILING_PF = 50.0
OTHER_PF = (0.0, 50.0)
DECK_CAP = 2400
SWEEP_CEILING_S = 5 * 3600
ORDER = ["B", "C", "A", "D", "H-REF9", "H-output", "E-control", "E-audio", "G"]
PF_PER_MM, ROUTE, VIA_PF, PAD_PF = 0.20, 1.5, 0.5, 0.3
F_DIAG_NETS = {"/W1/F1_SUM", "/W2/F4_SUM"}  # the binding fold-cell nets: R5253 (U5209) and R5162 (U5110)

PINNED = {  # brief "Pinned inputs" (P1) and the model table (P3)
    "scripts/stack/studies/mc04_s12_five_ic_joint/census.json": "92f6fdede21948d10ed49236889f1853b77c1e803445a945a15a92e7dbda095e",
    "scripts/stack/studies/mc04_s12_five_ic_joint/result.json": "32532262d6a98dbdef8e73fee4951487f417c8361cc2f008ea801be099da02ed",
    "design/reports/io-partition.json": "235277959121d8599cbe1b6c6ae65ed4cd3fd3813cf2a8db05d2951ce5b633ce",
    "design/partition/floorplan-candidate.json": "12083ea177cad1492f07fa96ad6dbfea8e5f8d2d347199bb555475c5b9e75a38",
    ".claude/skills/component-spec-audit/references/inventory.json": "dd31420dc068ef2953ada299f3a2a873c5da1ee86f645ce4dc95f12476256eba",
    "design/standard/electrical-standard.json": "0cdef30d4848414c794b7561c07bef6c5cf63a19f7f79a0fd21866412e0e40fe",
    "design/spec/modules/wavefolder.py": "e3a850e841a0f597571d6550e372d337c404fe4155ede3af7372be03ace37a93",
    "design/spec/modules/envelope.py": "015b02c5d84550e19bf92b9ec838a43b255a728e02de1e562e855ba632fc2ee5",
    "design/spec/modules/mix4_vca.py": "46d1efae983c32e763da7d3934d7fa01a7e0473c5b0c0bd586b28c9c85cf80e2",
    "design/spec/cells/sweep_input_buffer_vendor.py": "13c470004de92aeae8dbf31dc54216214b86060758884e9e2ed40e42b9cee23d",
    "design/spec/cells/sweep_precision_vendor.py": "31c77c207c3b3da770cbc3800c3d2c75cd96492a5a3e3c6cd246d27239d87eae",
    "design/spec/modules/spice_trace.py": "3234148d53ec6241468e172e28340a2f0aee1acd299b68c4eea8a6cc7927f964",
    "design/reports/spice/input-buffer-vendor.json": "12a0de40445d5156ccab2d583b45baa14f8b0420935ae57ca7a2f3d391654c9b",
    "design/reports/spice/precision-output-vendor.json": "9a974de1aa3ade8d7c189dd2238e90b96d7f41a8f134210ed3c99fac3d684e9b",
    "scripts/stack/studies/mc04_s7_r4/buffer_runs.py": "df656dc333dff510757b668278ba53ed2a078860d47dcff38c86070a1aaac9b1",
    "scripts/stack/studies/mc04_s10_r2_packet/f2_loop_estimate.py": "667c027b4ce3a861ab2ad86deb50cb702dba60e728b01daf4ba22cbaf812856d",
    "scripts/kicad/run.sh": "bc74f0ade82c29d64c44119ea435bc7bfd164fc06e9afff240a3cb2b44b272a0",
    "scripts/kicad/pin.env": "769e2be0b61e7d92a6930684f13166b7dc098522008de3969cd30d6c4a363246",
    "circuit/orchestration/campaigns/osc-stack-20261114/mc04-s12-disposition-20261127.md": "6c21cb39354f12f091472c1dd33c56ec53b4ea0bf1196489737f7bc1e8516f0b",
    "circuit/orchestration/campaigns/osc-stack-20261114/mc04-s12-report-20261127.md": "d3b9a33026089d24aa4d8e4c591b1cb16545fb617e01800d3993e38a23470a19",
    "circuit/orchestration/campaigns/osc-stack-20261114/reviews/mc04-s12-result-review-20261127.md": "77f8039f95d1afce36e52fe056717dc0c77e0219283bc7f5cca5662dbd58f2d9",
}
MODEL_PINS = {
    ".circuit-cache/sources/opa196-model/SBOMAF9E.ZIP": "9c264813a36536f743c166b6a101904b76ed08f049f2eeb127a438cc6e8ccdf5",
    ".circuit-cache/sources/opa196-model/OPAx196.LIB": "31142f5dbd71b758d887ee8a411692fc4c1309c8f47100af4ba5bed7e173c430",
    ".circuit-cache/sources/opa197-model/SBOMA34D.ZIP": "9e55fcaa23d54cee025dda3fa9872b11c41c531f82e0802c2b93d51e943666e5",
    ".circuit-cache/sources/opa197-model/OPAx197.LIB": "fc5b020e63346e511bd808bf41c856b0150b000bcf8a41fe00eeececb1f422a5",
    "design/spec/modules/spice/filter-model/LM13700.MOD": "666df501773da5e65f7fd3b3c806b2c1ae7770784685dd8191a9df33b382f390",
}
DECK_MODULES = ["design/spec/modules/filter.py", "design/spec/modules/offset.py", "design/spec/modules/mix5.py",
                "design/spec/modules/mixer_common.py", "design/spec/cells/_builder.py", "design/spec/instrument.py",
                "design/spec/modules/io_partition.py", "scripts/schgen/core.py"]


def sha_file(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def check_pins(pins):
    bad = {k: sha_file(k) for k, v in pins.items() if not (ROOT / k).exists() or sha_file(k) != v}
    if bad:
        raise SystemExit(f"STOP 1: input drift {sorted(bad)}")


def check_models():
    """P3 / M1: fail closed before any deck when a cached model byte changes."""
    check_pins(MODEL_PINS)


# ------------------------------------------------------------------------------------------------ points

def topologies():
    cen = cells.census()
    topo, rows, blocked = {}, {}, {}
    for net, info in cen["nets"].items():
        try:
            c = cells.extract(net, info)
        except Blocked as b:
            blocked[net] = str(b)
            rows[net] = {"info": info, "topology": None, "blocked": str(b)}
            continue
        k = cells.topology_key(c)
        t = topo.setdefault(k, {"key": k, "circuit": c, "nets": [], "swept": set()})
        t["nets"].append(net)
        t["swept"].add("inm" if info["pin"] == "IN-" else "inp")
        rows[net] = {"info": info, "topology": k}
    for t in topo.values():
        t["swept"] = sorted(t["swept"])
    return cen, topo, rows


def f_topologies(cen):
    out = {}
    for net, info in cen["nets"].items():
        if info["class"] != "F":
            continue
        c = cells.extract(net, info, diagnostic=True)
        k = "F" + cells.topology_key(c)
        t = out.setdefault(k, {"key": k, "circuit": c, "nets": [], "swept": ["inm"]})
        t["nets"].append(net)
    return out


def point_id(p):
    return hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:24]


def sweep_points(t, *, values=None, whatif=False, phase="sweep", corners=None, out_c=None):
    c = t["circuit"]
    pts = []
    for corner in corners or cells.corners_of(c):
        for swept in t["swept"]:
            others = [None]
            if c["class"] == "B":
                others = [("inp" if swept == "inm" else "inm", o) for o in OTHER_PF]
            for other in others:
                vals = values
                if vals is None:
                    vals = C_REDUCED_PF if c["class"] == "C" else VALUES_PF
                for v in vals:
                    p = {"topology": t["key"], "class": c["subclass"], "corner": corner, "swept": swept,
                         "other": other, "c_pF": v, "whatif": whatif, "phase": phase,
                         "out_pF": cells.OUT_STRAY_PF if out_c is None else out_c}
                    pts.append(p)
    return pts


def build_lines(t, p, *, loop):
    c = t["circuit"]
    other = p["other"]
    lines = cells.header(c, f"MC04-S13 {p['class']} {t['key']} (MODEL EVIDENCE ONLY)") + cells.netlist_lines(
        c, p["corner"], p["c_pF"] * 1e-12, p["swept"], other=other[0] if other else None,
        other_c=(other[1] if other else 0.0) * 1e-12, out_c=p["out_pF"] * 1e-12, whatif=p["whatif"], loop=loop)
    return lines


def loop_texts(t, p):
    c = t["circuit"]
    lines = cells.loop_lines(c, p["corner"], build_lines(t, p, loop=True))
    y = "out" if c["follower"] else "inm"
    opv = ["v(out)", "v(n1)", "v(xinm)"]
    out = []
    for name, tol in runner.LOOP_TOLERANCES:
        text, vv, vi = runner.loop_text(lines, opv, x="xinm", y=y, tol=tol)
        out.append((name, text, vv, vi))
    return out


def closed_texts(t, p):
    c = t["circuit"]
    lines = build_lines(t, p, loop=False)
    text, files, P = cells.closed_text(c, p["corner"], lines)
    gear = text.replace("\n.control\n", "\n.options method=gear\n.control\n", 1)
    return [("ngspice default (trap)", text, files, P), ("gear", gear, files, P)]


def dc_moved(op1, op2):
    for k in op1:
        if abs(op1[k][0] - op2[k][0]) > 1e-4:
            return f"operating point moved on {k}"
    return None


def run_loop(t, p):
    attempts = []
    for name, text, vv, vi in loop_texts(t, p):
        try:
            key, tab, wall = runner.run(text, ["op1", "v", "i", "op2"])
        except (runner.OracleError, RuntimeError) as e:
            msg = str(e)
            if "TIMEOUT" in msg.upper() or "timed out" in msg:
                attempts.append({"tolerance": name, "result": "timeout", "key": runner.deck_key(text)})
                continue
            if "Timestep too small" in msg or "singular" in msg.lower() or "converge" in msg.lower() or \
                    "gmin" in msg.lower() or "source stepping" in msg.lower():
                attempts.append({"tolerance": name, "result": "no convergence", "key": runner.deck_key(text)})
                continue
            raise
        why = dc_moved(tab["op1"], tab["op2"])
        attempts.append({"tolerance": name, "result": why or "usable", "key": key, "wall_s": round(wall, 2)})
        if why is None:
            m = runner.loop_metrics(tab["v"], tab["i"], vv, vi)
            m["op"] = {k: runner.r(v[0]) for k, v in tab["op1"].items() if k.startswith("v(")}
            return {"status": "OK", "key": key, "metrics": m, "attempts": attempts}
    return {"status": "NOT EVALUATED", "key": attempts[0]["key"], "metrics": None, "attempts": attempts}


def run_closed(t, p):
    attempts = []
    for name, text, files, P in closed_texts(t, p):
        try:
            key, tab, wall = runner.run(text, files)
        except (runner.OracleError, RuntimeError) as e:
            msg = str(e)
            if "Timestep too small" in msg or "converge" in msg.lower() or "timed out" in msg or \
                    "singular" in msg.lower() or "gmin" in msg.lower():
                attempts.append({"integration": name, "result": "no convergence", "key": runner.deck_key(text),
                                 "error": msg[-400:]})
                continue
            raise
        attempts.append({"integration": name, "result": "usable", "key": key, "wall_s": round(wall, 2)})
        m = runner.closed_metrics(t["circuit"], p["corner"], P, tab)
        m["stimulus"] = stimulus_record(t["circuit"], P)
        return {"status": "OK", "key": key, "metrics": m, "attempts": attempts}
    return {"status": "NOT EVALUATED", "key": attempts[0]["key"], "metrics": None, "attempts": attempts}


def stimulus_record(c, P):
    out = {"main_source": P["main"], "k4_source_step_V": P.get("k4_source_step_V"),
           "k5_step_V": P.get("k5_step_V"), "sine": {k: v for k, v in (P.get("sine") or {}).items() if k != "roles"},
           "windows": {k: v for k, v in P["windows"].items()}, "tran": P["tran"],
           "measured": ["out"] + (["harness"] if c["class"] == "A" else [])}
    if "tau0_s" in P:
        out["tau0_s"], out["tmax_over_tau0"] = P["tau0_s"], P["resolution_fraction"]
    return out


# ------------------------------------------------------------------------------------------------ results file

def load_results():
    out = {}
    if RESULTS.exists():
        for line in RESULTS.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                out[(d["point_id"], d["deck"])] = d
    return out


def append(rec):
    with open(RESULTS, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


def invocations(results):
    return sum(len(r["attempts"]) for r in results.values())


# ------------------------------------------------------------------------------------------------ criteria

def gating(cls):
    base = ["K1", "K2", "K3", "K4", "K5", "K9"]
    if cls in ("C",):
        return base + ["K6", "K8"]
    if cls in ("E-control", "H-REF9"):
        return base + ["K6"]
    if cls in ("A", "B", "D", "E-audio", "G", "H-output", "F"):
        return base + ["K7"]
    return base


def judge(cls, loop, closed, zero):
    """Pass/fail per criterion of one point; `zero` is the closed metrics at C_stray = 0 of the same corner."""
    res = {}
    if loop is None or closed is None:
        return None
    k1, k2 = runner.k1_k2(loop)
    res["K1"], res["K2"] = k1, k2
    res["K3"] = all(a["peaking_dB"] is not None and a["peaking_dB"] <= runner.PEAK_LIMIT
                    for k, a in closed["ac"].items() if not (cls == "A" and False))
    res["K4"] = all(o["overshoot_percent"] is not None and o["overshoot_percent"] <= runner.OVERSHOOT_LIMIT
                    for v in closed["k4"].values() for o in v)
    res["K5"] = all(x is not None and x <= runner.OSC_LIMIT for x in closed["k5"].values())
    if "K6" in gating(cls):
        if cls == "C":
            if zero is None:
                res["K6"] = None
            else:
                ok = True
                for a, b in zip(closed["k6"], zero["k6"]):
                    if a is None or b is None or not (a - b) < runner.REL_LIMIT * b:
                        ok = False
                res["K6"] = ok
        else:
            res["K6"] = all(x is not None and x <= runner.SETTLE_LIMIT_S for x in closed["k6"])
    if "K8" in gating(cls):
        res["K8"] = None if zero is None else (closed["k8_tau_s"] - zero["k8_tau_s"]) < runner.REL_LIMIT * zero["k8_tau_s"]
    if "K7" in gating(cls):
        if zero is None:
            res["K7"] = None
        else:
            ok = True
            for k, a in closed["ac"].items():
                if cls == "A" and not k.endswith("@harness"):
                    continue
                b = zero["ac"][k]
                if abs(a["gain_20k_dB"] - b["gain_20k_dB"]) > runner.K7_DB or \
                        abs(a["phase_20k_deg"] - b["phase_20k_deg"]) > runner.K7_DEG:
                    ok = False
            res["K7"] = ok
    if zero is None:
        res["K9"] = None
    else:
        res["K9"] = all(20 * math.log10(closed["noise"][n]["integrated_uVrms"] / zero["noise"][n]["integrated_uVrms"])
                        <= runner.K9_DB for n in closed["noise"])
    return res


def corner_id(p):
    return json.dumps({k: p[k] for k in ("topology", "corner", "swept", "other", "whatif", "phase", "out_pF")},
                      sort_keys=True)


def corner_limits(points, results):
    """Group points by corner; per corner the per-value verdicts and C_lim (Ruling 3)."""
    groups = {}
    for p in points:
        groups.setdefault(corner_id(p), []).append(p)
    out = {}
    for cid, pts in groups.items():
        pts.sort(key=lambda p: p["c_pF"])
        recs = {}
        for p in pts:
            pid = point_id(p)
            lo, cl = results.get((pid, "loop")), results.get((pid, "closed"))
            recs[p["c_pF"]] = (p, lo, cl)
        zero = recs.get(0)
        zclosed = zero[2]["metrics"] if zero and zero[2] and zero[2]["status"] == "OK" else None
        verdicts, missing, ne = {}, [], []
        for v, (p, lo, cl) in sorted(recs.items()):
            if lo is None or cl is None:
                missing.append(v)
                continue
            if lo["status"] != "OK" or cl["status"] != "OK":
                ne.append(v)
                verdicts[v] = {"pass": False, "not_evaluated": True, "failed": ["NOT EVALUATED"]}
                continue
            j = judge(p["class"], lo["metrics"], cl["metrics"], zclosed)
            failed = [k for k in gating(p["class"]) if j.get(k) is False or j.get(k) is None and k not in ("K9",)]
            verdicts[v] = {"pass": not failed, "failed": failed, "criteria": j,
                           "pm_deg": lo["metrics"]["phase_margin_deg"], "gm_dB": lo["metrics"]["gain_margin_dB"]}
        tested = sorted(verdicts)
        fails = [v for v in tested if not verdicts[v]["pass"]]
        lowest_fail = fails[0] if fails else None
        nonmono = lowest_fail is not None and any(verdicts[v]["pass"] for v in tested if v > lowest_fail)
        if missing:
            lim, status = None, "INCOMPLETE"
        elif 0 in fails:
            lim, status = None, "FAILS AT ZERO STRAY"
        else:
            lim = 0.0
            for g in CANDIDATES_PF:
                if all(verdicts[v]["pass"] for v in tested if v <= 2 * g) and max(tested) >= 2 * g:
                    lim = float(g)
            lim = min(lim, CEILING_PF)
            status = "OK"
        decided = verdicts[lowest_fail]["failed"] if lowest_fail is not None else None
        out[cid] = {"points": pts, "verdicts": verdicts, "c_lim_pF": lim, "status": status,
                    "lowest_fail_pF": lowest_fail, "deciding": decided, "non_monotonic": nonmono,
                    "not_evaluated": ne, "missing": missing}
    return out


# ------------------------------------------------------------------------------------------------ paper estimate

_PAPER = {}


def paper_estimates(nets):
    missing = [n for n in nets if n not in _PAPER]
    if missing:
        _PAPER.update(_paper_estimates(missing))
    return {n: _PAPER[n] for n in nets}


def _paper_estimates(nets):
    from scripts.stack.studies.mc04_s7_r4.buffer_runs import pin_xy, poses
    nl = cells.netlist()
    io = nl["io"]
    pk = {p["ref"]: p for p in io["physical_packages"]}
    floor = json.loads((ROOT / "design/partition/floorplan-candidate.json").read_text())
    P, lock = poses(floor)
    out = {}
    for net in nets:
        pins = sorted({(nl["parts"][k]["ref"], pin) for k, pin in nl["net_pins"][net]})
        k_amp, _ = cells.owner_unit(net)
        amp = nl["parts"][k_amp]
        aside = P[amp["ref"]]["side"] if amp["ref"] in P else None
        pts, vias, missing = [], 0, []
        for ref, pin in pins:
            q = pin_xy(ref, pin, P, pk, lock)
            if q is None:
                missing.append(ref)
                continue
            pts.append(q)
            th = (pk[ref].get("courtyard") or {}).get("through_hole")
            side = P[ref]["side"] if ref in P else None
            if not th and side is not None and aside is not None and side != aside:
                vias += 1
        hp = (max(x for x, _ in pts) - min(x for x, _ in pts)) + (max(y for _, y in pts) - min(y for _, y in pts))
        c = PF_PER_MM * ROUTE * hp + VIA_PF * vias + PAD_PF * len(pins)
        out[net] = {"hpwl_mm": round(hp, 2), "n_via": vias, "n_pad": len(pins), "c_paper_pF": round(c, 2),
                    "amp_side": aside, "unplaced": missing}
    return out


def hpwl_max(c_lim, n_via, n_pad):
    return round((c_lim - VIA_PF * n_via - PAD_PF * n_pad) / (PF_PER_MM * ROUTE), 1)


# ------------------------------------------------------------------------------------------------ plan

def all_phases(topo, ftopo, results):
    """The ordered list of (phase, topology, points). Later phases depend on earlier results."""
    by_class = {}
    for t in topo.values():
        by_class.setdefault(t["circuit"]["subclass"], []).append(t)
    plan = []
    for cls in ORDER:
        for t in sorted(by_class.get(cls, []), key=lambda t: t["key"]):
            plan.append(("sweep", t, sweep_points(t)))
    return plan


def dependent_phases(topo, ftopo, results):
    plan = []
    # class C full list where a reduced-list corner fails
    for t in sorted(topo.values(), key=lambda t: t["key"]):
        if t["circuit"]["class"] != "C":
            continue
        lim = corner_limits(sweep_points(t), results)
        if any(v["status"] == "INCOMPLETE" for v in lim.values()):
            return plan, False
        for cid, v in lim.items():
            if v["lowest_fail_pF"] is not None:
                corner = v["points"][0]["corner"]
                plan.append(("sweep", t, [p for p in sweep_points(t, values=VALUES_PF, corners=[corner])]))
    # what-if: one 10 pF output-to-IN- variant per topology with a failing or no-headroom result (Ruling 7)
    for cls in ORDER:
        for t in sorted((t for t in topo.values() if t["circuit"]["subclass"] == cls), key=lambda t: t["key"]):
            if t["circuit"]["follower"]:
                continue
            pts = topology_points(t, results)
            lim = corner_limits(pts, results)
            if any(v["status"] == "INCOMPLETE" for v in lim.values()):
                return plan, False
            worst = min(lim.values(), key=lambda v: (-1 if v["c_lim_pF"] is None else v["c_lim_pF"]))
            paper = paper_estimates(t["nets"])
            need = worst["c_lim_pF"] is None or worst["c_lim_pF"] < max(x["c_paper_pF"] for x in paper.values())
            if need:
                p0 = worst["points"][0]
                plan.append(("whatif", t, sweep_points(t, whatif=True, phase="whatif", corners=[p0["corner"]])))
    # Ruling 6 output pair: 0 and 100 pF on OUT at C_lim of the deciding corner
    for t in sorted(topo.values(), key=lambda t: t["key"]):
        pts = topology_points(t, results)
        lim = corner_limits(pts, results)
        worst = min(lim.values(), key=lambda v: (-1 if v["c_lim_pF"] is None else v["c_lim_pF"]))
        if worst["c_lim_pF"]:
            p0 = dict(worst["points"][0])
            for oc in (0.0, 100.0):
                q = {**p0, "c_pF": worst["c_lim_pF"], "out_pF": oc, "phase": "outpair"}
                plan.append(("outpair", t, [q]))
    for t in sorted(ftopo.values(), key=lambda t: t["key"]):
        if set(t["nets"]) & F_DIAG_NETS:
            plan.append(("fdiag", t, sweep_points(t, phase="fdiag")))
    return plan, True


def topology_points(t, results):
    pts = sweep_points(t)
    if t["circuit"]["class"] == "C":
        lim = corner_limits(pts, results)
        extra = []
        for v in lim.values():
            if v["lowest_fail_pF"] is not None:
                extra += sweep_points(t, values=VALUES_PF, corners=[v["points"][0]["corner"]])
        if extra:
            ext_corners = {json.dumps(p["corner"], sort_keys=True) for p in extra}
            pts = [p for p in pts if json.dumps(p["corner"], sort_keys=True) not in ext_corners] + extra
    return pts


# ------------------------------------------------------------------------------------------------ sweep driver

def fingerprint():
    import os
    import platform
    import subprocess
    fp = {"os": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0],
          "interpreter": sys.executable, "nproc": os.cpu_count()}
    try:
        fp["affinity"] = sorted(os.sched_getaffinity(0))
    except Exception:
        pass
    for f in ("/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory.current"):
        fp[f] = Path(f).read_text().strip() if Path(f).exists() else "absent"
    mi = {l.split(":")[0]: l.split(":")[1].strip() for l in Path("/proc/meminfo").read_text().splitlines()}
    fp["MemAvailable"], fp["SwapTotal"] = mi.get("MemAvailable"), mi.get("SwapTotal")
    st = os.statvfs(str(ROOT))
    fp["disk_free_GiB"] = round(st.f_bavail * st.f_frsize / 2 ** 30, 1)
    run = lambda *a: subprocess.run(list(a), capture_output=True, text=True, cwd=ROOT).stdout.strip()  # noqa: E731
    fp["docker"] = run("docker", "version", "--format", "{{.Server.Version}}")
    fp["image"] = run("docker", "image", "inspect", cells_image(), "--format", "{{.Id}}")
    fp["commit"] = run("git", "rev-parse", "HEAD")
    fp["processes_top_rss"] = run("ps", "-eo", "rss,comm", "--sort=-rss").splitlines()[:8]
    return fp


def cells_image():
    from guard import IMAGE
    return IMAGE


def drive(slice_min, *, resume, max_decks=None):
    check_pins(PINNED)
    check_models()
    survivors = kill_pinned_containers()
    if survivors:
        raise SystemExit(f"STOP 3: container survived docker kill: {survivors}")
    if not resume and RESULTS.exists():
        raise SystemExit("results.jsonl exists: use --resume")
    cen, topo, rows = topologies()
    ftopo = f_topologies(cen)
    results = load_results()
    t_start = time.time()
    state = json.loads((STUDY / "checkpoints/sweep-state.json").read_text()) if (STUDY / "checkpoints/sweep-state.json").exists() else {"sweep_s": 0.0, "slices": []}
    done_new = 0
    created = runner.ensure_spiceinit()
    reason = "complete"
    try:
        while True:
            plan = all_phases(topo, ftopo, results)
            dep, ready = dependent_phases(topo, ftopo, results)
            todo = [(ph, t, p) for ph, t, pts in plan + dep for p in pts
                    if (point_id(p), "loop") not in results or (point_id(p), "closed") not in results]
            if not todo:
                break
            # run the first pending point; dependent phases are recomputed after every point
            ph, t, p = todo[0]
            if time.time() - t_start > slice_min * 60:
                reason = "slice end"
                break
            if max_decks is not None and done_new >= max_decks:
                reason = f"pilot end after {done_new} decks"
                break
            if invocations(results) + 4 > DECK_CAP:
                reason = "deck cap reached"
                break
            if state["sweep_s"] + (time.time() - t_start) > SWEEP_CEILING_S:
                reason = "sweep ceiling reached"
                break
            pid = point_id(p)
            for deck in ("loop", "closed"):
                if (pid, deck) in results:
                    continue
                t0 = time.time()
                out = run_loop(t, p) if deck == "loop" else run_closed(t, p)
                rec = {"point_id": pid, "deck": deck, "point": p, "phase": ph, **out,
                       "wall_s": round(time.time() - t0, 2)}
                append(rec)
                results[(pid, deck)] = rec
                done_new += 1
            if not ready and not [x for x in todo[1:] if x[0] == "sweep"]:
                continue
    finally:
        if created:
            runner.remove_spiceinit()
        survivors = kill_pinned_containers()
    state["sweep_s"] += time.time() - t_start
    state["slices"].append({"ended": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "reason": reason,
                            "decks_written": done_new, "invocations_total": invocations(results),
                            "wall_s": round(time.time() - t_start, 1), "containers_after": survivors})
    (STUDY / "checkpoints/sweep-state.json").write_text(json.dumps(state, indent=1) + "\n")
    print(f"{reason}: {done_new} decks this slice, {invocations(results)} invocations in all", flush=True)
    if survivors:
        raise SystemExit("STOP 3: container survived docker kill")


# ------------------------------------------------------------------------------------------------ evaluation

def evaluate(write=True):
    cen, topo, rows = topologies()
    ftopo = f_topologies(cen)
    results = load_results()
    paper = paper_estimates(list(cen["nets"]))
    inv = {l["mpn"]: l["line_id"] for l in json.loads(
        (ROOT / ".claude/skills/component-spec-audit/references/inventory.json").read_text())["lines"]}
    nl = cells.netlist()
    tl = {}
    for k, t in topo.items():
        pts = topology_points(t, results)
        tl[k] = corner_limits(pts, results)
    op = outpair_rows(topo, results)
    out_rows = []
    for net, row in sorted(rows.items()):
        info = row["info"]
        parts = []
        for k, pin in nl["net_pins"][net]:
            p = nl["parts"][k]
            parts.append({"ref": p["ref"], "pin": pin, "role": p["role"], "value": p["value"], "mpn": p["mpn"],
                          "inventory_line": inv.get(p["mpn"]) if p["mpn"] else "IDENTITY OPEN"})
        pe = paper[net]
        r = {"net": net, "class": info["class"], "subclass": info["subclass"],
             "amplifier": {"ref": info["amp_ref"], "unit": info["amp_unit"], "pin": info["pin"], "mpn": info["amp_mpn"],
                           "inventory_line": inv.get(info["amp_mpn"])},
             "parts_on_net": parts, "c_paper": pe}
        if row.get("blocked"):
            r["model"] = None
            r["label"] = f"BLOCKED: MISSING VENDOR MODEL {row['blocked']}"
            r["c_lim_pF"] = None
            out_rows.append(r)
            continue
        t = topo[row["topology"]]
        c = t["circuit"]
        r["model"] = {"subckt": c["model"], "lib": cells.MODEL_LIBS[c["model"]],
                      "sha256": MODEL_PINS[cells.MODEL_LIBS[c["model"]]]}
        r["topology"] = t["key"]
        r["deck_parts"] = c["parts"]
        swept = "inm" if info["pin"] == "IN-" else "inp"
        lims = {cid: v for cid, v in tl[t["key"]].items() if json.loads(cid)["swept"] == swept}
        r["corners"] = [{"corner": json.loads(cid)["corner"], "other": json.loads(cid)["other"],
                         "c_lim_pF": v["c_lim_pF"], "status": v["status"], "lowest_fail_pF": v["lowest_fail_pF"],
                         "deciding": v["deciding"], "non_monotonic": v["non_monotonic"],
                         "values": {str(k): {"pass": x["pass"], "failed": x["failed"], "pm_deg": x.get("pm_deg"),
                                             "gm_dB": x.get("gm_dB")} for k, x in v["verdicts"].items()}}
                        for cid, v in lims.items()]
        r["outpair"] = [x for x in op.get(t["key"], []) if x["swept"] == swept]
        r["label"], r["c_lim_pF"], r["deciding"] = label(r, c, lims, pe, parts)
        if r["c_lim_pF"] is not None and r["label"].startswith(("BUDGET", "PROVISIONAL")):
            r["allowance_pF"] = round(r["c_lim_pF"] - pe["c_paper_pF"], 2)
            r["hpwl_max_mm"] = hpwl_max(r["c_lim_pF"], pe["n_via"], pe["n_pad"])
        out_rows.append(r)
    whatif, fdiag = [], []
    for k, t in topo.items():
        pts = [rec["point"] for (pid, deck), rec in results.items() if deck == "loop" and rec["point"]["topology"] == k
               and rec["point"]["phase"] == "whatif"]
        if pts:
            lim = corner_limits(pts, results)
            for cid, v in lim.items():
                whatif.append({"label": "WHAT-IF, NOT A DESIGN CHANGE", "part": "KEMET C0603C100J5GACTU "
                               "(line-audio-feedback-c), 10 pF from OUT to IN-", "topology": k, "nets": t["nets"],
                               "class": t["circuit"]["subclass"], "corner": json.loads(cid)["corner"],
                               "swept": json.loads(cid)["swept"], "status": v["status"],
                               "c_lim_if_fitted_pF": v["c_lim_pF"], "deciding": v["deciding"],
                               "values": {str(x): {"pass": y["pass"], "failed": y["failed"], "pm_deg": y.get("pm_deg")}
                                          for x, y in v["verdicts"].items()}})
    for k, t in ftopo.items():
        pts = [rec["point"] for (pid, deck), rec in results.items() if deck == "loop" and rec["point"]["topology"] == k]
        if pts:
            lim = corner_limits(pts, results)
            for cid, v in lim.items():
                fdiag.append({"label": "DIAGNOSTIC, NOT A BUDGET", "topology": k, "nets": t["nets"],
                              "corner": json.loads(cid)["corner"], "status": v["status"],
                              "values": {str(x): {"pass": y["pass"], "failed": y["failed"], "pm_deg": y.get("pm_deg"),
                                                  "gm_dB": y.get("gm_dB")} for x, y in v["verdicts"].items()}})
    budget = {"status": STATUS, "method_limits": METHOD_LIMITS, "criteria": CRITERIA, "rows": out_rows,
              "what_if": whatif, "f_diagnostic": fdiag}
    validate_budget(budget)
    if write:
        BUDGET.write_text(json.dumps(budget, indent=1, sort_keys=True) + "\n")
    return budget


def validate_budget(budget):
    """M5 / M8: a blocked class carries no number; an open identity or a K9 NOT RUN is never a plain budget;
    what-if and diagnostic rows are labelled and never budgets."""
    errs = []
    for r in budget["rows"]:
        lab = r["label"]
        if r["class"] in ("F", "I"):
            if not lab.startswith("BLOCKED: MISSING VENDOR MODEL") or r.get("c_lim_pF") is not None \
                    or r.get("allowance_pF") is not None:
                errs.append(f"{r['net']}: class {r['class']} row carries a number or a non-blocked label")
        open_id = [p for p in r.get("parts_on_net", []) if p["inventory_line"] == "IDENTITY OPEN"]
        if lab.startswith("BUDGET") and (open_id or r.get("k9_not_run")):
            errs.append(f"{r['net']}: IDENTITY OPEN or K9 NOT RUN labelled as a plain budget")
        n = sum(lab.startswith(x) for x in ("BUDGET", "PROVISIONAL", "FAILS AT ZERO STRAY", "NO HEADROOM AT PAPER",
                                             "BLOCKED: MISSING VENDOR MODEL", "NOT EVALUATED"))
        if n != 1:
            errs.append(f"{r['net']}: not exactly one label")
    for w in budget.get("what_if", []):
        if w["label"] != "WHAT-IF, NOT A DESIGN CHANGE":
            errs.append("what-if row without its label")
    for f in budget.get("f_diagnostic", []):
        if f["label"] != "DIAGNOSTIC, NOT A BUDGET" or "c_lim_pF" in f:
            errs.append("class F diagnostic row used as a budget")
    if errs:
        raise ValueError("budget table rejected: " + "; ".join(errs[:10]))


def label(r, c, lims, pe, parts):
    if not lims or any(v["status"] == "INCOMPLETE" for v in lims.values()):
        return "NOT EVALUATED: sweep incomplete (cap, ceiling or STOP)", None, None
    ne = [v for v in lims.values() if v["not_evaluated"]]
    if ne:
        return "NOT EVALUATED: non-converging deck at " + ", ".join(f"{x} pF" for v in ne for x in v["not_evaluated"]), None, None
    if any(v["status"] == "FAILS AT ZERO STRAY" for v in lims.values()):
        d = next(v for v in lims.values() if v["status"] == "FAILS AT ZERO STRAY")["deciding"]
        return "FAILS AT ZERO STRAY", None, d
    worst = min(lims.values(), key=lambda v: v["c_lim_pF"])
    lim = worst["c_lim_pF"]
    if lim < pe["c_paper_pF"]:
        return "NO HEADROOM AT PAPER", lim, worst["deciding"]
    reasons = []
    if any(p["inventory_line"] == "IDENTITY OPEN" for p in parts):
        reasons.append("IDENTITY OPEN: " + ", ".join(p["ref"] for p in parts if p["inventory_line"] == "IDENTITY OPEN"))
    if c["subclass"] == "G":
        reasons.append("LM13700 model overstates AC bandwidth and phase margin by more than twofold (its header)")
    if c["tmux"]:
        reasons.append("TMUX6112PWR on-capacitance is not a retained fact (bracketed 0 / 100 pF)")
    if c["brackets"]:
        by = {}
        for cid, v in lims.items():
            corner = json.loads(cid)["corner"]
            key = json.dumps({k: x for k, x in corner.items() if k != "bracket"} | {"o": json.loads(cid)["other"]},
                             sort_keys=True)
            by.setdefault(key, {})[corner["bracket"]] = v
        for pair in by.values():
            if len(pair) == 2:
                a, b = pair["agnd"], pair["open"]
                step = abs(CANDIDATES_PF.index(a["c_lim_pF"]) - CANDIDATES_PF.index(b["c_lim_pF"])) \
                    if a["c_lim_pF"] in CANDIDATES_PF and b["c_lim_pF"] in CANDIDATES_PF else 99
                dpm = max((abs(a["verdicts"][x]["pm_deg"] - b["verdicts"][x]["pm_deg"])
                           for x in a["verdicts"] if x in b["verdicts"] and a["verdicts"][x].get("pm_deg") is not None
                           and b["verdicts"][x].get("pm_deg") is not None), default=0)
                if step >= 1 or dpm > 2:
                    reasons.append(f"Ruling 6 bracket pair differs (dPM {dpm:.2f} deg, {step} candidate step)")
                    break
    bad_pair = [x for x in r.get("outpair") or [] if not x["pass"]]
    if bad_pair:
        reasons.append("Ruling 6 output pair fails at C_lim (" + ", ".join(f"{x['out_pF']:g} pF: {'/'.join(x['failed'])}"
                                                                    for x in bad_pair) + ")")
    if lim < 1:
        return "NO HEADROOM AT PAPER", lim, worst["deciding"]
    if reasons:
        return f"PROVISIONAL {lim:g} pF: " + "; ".join(reasons), lim, worst["deciding"]
    if lim >= CEILING_PF:
        return "BUDGET CAPPED AT 50 pF (MODEL EVIDENCE ONLY)", lim, worst["deciding"]
    return f"BUDGET {lim:g} pF (MODEL EVIDENCE ONLY)", lim, worst["deciding"]


METHOD_LIMITS = [
    "generic single-channel TI family cores (OPAx196 Final 1.5, OPAx197 Final 1.3); no package parasitics, no "
    "coupling between the channels of a quad, no supply impedance",
    "ideal +/-12 V rails", "typical-only models", "27 C", "no temperature or tolerance corner: the factor of two "
    "stands in for them", "capacitance lumped to AGND",
    "0.20 pF/mm, the 1.5 route factor, 0.5 pF per via and 0.3 pF per pad are all ASSUMED (the last two new and "
    "unsourced)", "Ruling 4 is pending its re-review in the placement brief",
    "passives are ideal elements at their specification value; no vendor model exists for them and none is claimed",
    "leakage, hum pickup and neighbour coupling are not covered by a capacitance budget",
]
CRITERIA = {"K1": "phase margin >= 45 deg (Middlebrook double injection at the IN- pin)",
            "K2": "gain margin >= 10 dB, or no phase crossover below 100 MHz",
            "K3": "closed-loop peaking <= 3 dB above the low-frequency gain",
            "K4": "overshoot of a 100 mV small-signal step (100 ns edges) <= 25 %",
            "K5": "late-window residual (quadratic-detrended; sine: harmonic-fit) <= 1 mV",
            "K6": "1 mV settling <= 1 ms (E-control, H-REF9); class C: < +1 % against C_stray = 0",
            "K7": "gain change at 20 kHz <= 0.1 dB and <= 2 deg against C_stray = 0",
            "K8": "class C wiper time constant < +1 % against C_stray = 0",
            "K9": "integrated output noise <= +1 dB against C_stray = 0"}


# ------------------------------------------------------------------------------------------------ outpair

def outpair_rows(topo, results):
    """Ruling 6 output pair: the deciding corner re-run at C_lim with 0 and 100 pF on OUT."""
    out = {}
    for k, t in topo.items():
        main = corner_limits(topology_points(t, results), results)
        for (pid, deck), rec in results.items():
            p = rec["point"]
            if deck != "closed" or p["phase"] != "outpair" or p["topology"] != k:
                continue
            lo = results.get((pid, "loop"))
            zid = corner_id({**p, "phase": "sweep", "out_pF": cells.OUT_STRAY_PF})
            z = main.get(zid)
            zero = None
            if z:
                zp = next(q for q in z["points"] if q["c_pF"] == 0)
                zr = results.get((point_id(zp), "closed"))
                zero = zr["metrics"] if zr and zr["status"] == "OK" else None
            if lo is None or lo["status"] != "OK" or rec["status"] != "OK":
                verdict = {"pass": False, "failed": ["NOT EVALUATED"]}
            else:
                j = judge(p["class"], lo["metrics"], rec["metrics"], zero)
                failed = [c for c in gating(p["class"]) if j.get(c) is False or j.get(c) is None]
                verdict = {"pass": not failed, "failed": failed, "pm_deg": lo["metrics"]["phase_margin_deg"]}
            out.setdefault(k, []).append({"out_pF": p["out_pF"], "c_pF": p["c_pF"], "corner": p["corner"],
                                          "swept": p["swept"], "other": p["other"], **verdict})
    return out


# ------------------------------------------------------------------------------------------------ controls

LOOP_VALIDATION = [(1e3, 9.953), (10.0, 59.67), (1e9, 7.713)]  # retained loop_break_validation (analytic PM)
FOLLOWER = {"OPAx196": (54.82, 2.597e6), "OPAx197": (63.95, 9.986e6)}  # retained case5a_control rows


def loop_run(lines, x, y, opv):
    text, vv, vi = runner.loop_text(lines, opv, x=x, y=y, tol=None, ac="ac dec 100 10 100meg")
    key, tab, wall = runner.run(text, ["op1", "v", "i", "op2"])
    f, T, _ = runner.loop_gain(tab["v"], tab["i"], vv, vi)
    m = runner.margins(f, T)
    u = [q for q in m["unity"] if q["falling"]][0]
    return key, u["pm_deg"], u["f_Hz"]


def controls():
    check_pins(PINNED)
    check_models()
    if kill_pinned_containers():
        raise SystemExit("STOP 3")
    out = {"P5": [], "P8": [], "P7": {}, "M3": []}
    created = runner.ensure_spiceinit()
    try:
        for rl, want in LOOP_VALIDATION:
            base = ["MC04-S13 P5 loop-break validation, linear two-pole loop", "E1 o1 0 0 x 1000", "Rp o1 o2 1k",
                    "Cp o2 0 1.5915n", "E2 o3 0 o2 0 1", "Rq o3 o4 1k", "Cq o4 0 159.15p", "E3 o5 0 o4 0 1",
                    "Ro o5 y 1k", "Rg y 0 2k", f"Rl x 0 {rl:g}"]
            key, pm, f = loop_run(base, "x", "y", ["v(x)"])
            out["P5"].append({"R_load_ohm": rl, "pm_deg": round(pm, 4), "retained_deg": want,
                              "pass": abs(pm - want) <= 0.1, "deck": key})
            key, pm2, f2 = loop_run(base, "y", "x", ["v(x)"])  # M3: probe polarity swapped
            out["M3"].append({"R_load_ohm": rl, "pm_deg": round(pm2, 4), "fails_P5": abs(pm2 - want) > 0.1,
                              "deck": key})
        for sub, lib in (("OPAx196", cells.MODEL_LIBS["OPAx196"]), ("OPAx197", cells.MODEL_LIBS["OPAx197"])):
            lines = [f"MC04-S13 P8 plain follower {sub}", ".param TEMP=27", f".include {lib}", "Vplus vp 0 12",
                     "Vminus vn 0 -12", f"XU 0 xinm vp vn out {sub}"]
            key, pm, f = loop_run(lines, "xinm", "out", ["v(out)"])
            want_pm, want_f = FOLLOWER[sub]
            out["P8"].append({"model": sub, "pm_deg": round(pm, 3), "crossover_Hz": round(f, 1), "retained": FOLLOWER[sub],
                              "pass": abs(pm - want_pm) <= 0.1 and abs(f / want_f - 1) <= 0.005, "deck": key})
        cen, topo, rows = topologies()
        for net, decks in (("/W1/DRIVE_INV_SUM", ("loop", "closed")), ("/E2/REF9_FB", ("loop",))):
            t = topo[rows[net]["topology"]]
            p = sweep_points(t, values=[1000], phase="P7")[0]
            res = {}
            lo = run_loop(t, p)
            res["loop"] = {"status": lo["status"], "pm_deg": lo["metrics"]["phase_margin_deg"] if lo["metrics"] else None}
            res["K1_fails"] = lo["metrics"] is not None and not runner.k1_k2(lo["metrics"])[0]
            if "closed" in decks:
                cl = run_closed(t, p)
                ov = max(o["overshoot_percent"] or 0 for v in cl["metrics"]["k4"].values() for o in v) if cl["metrics"] else None
                res["closed"] = {"status": cl["status"], "max_overshoot_percent": ov}
                res["K4_fails"] = ov is not None and ov > runner.OVERSHOOT_LIMIT
            res["pass"] = res["K1_fails"] and res.get("K4_fails", True)
            res["corner"], res["c_stray"] = p["corner"], "1 nF"
            out["P7"][net] = res
    finally:
        if created:
            runner.remove_spiceinit()
        kill_pinned_containers()
    out["invocations"] = runner.INVOCATIONS["count"]
    out["pass"] = (all(x["pass"] for x in out["P5"]) and all(x["pass"] for x in out["P8"])
                   and all(x["pass"] for x in out["P7"].values()) and all(x["fails_P5"] for x in out["M3"]))
    (STUDY / "checkpoints/controls.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    if not out["pass"]:
        raise SystemExit("STOP 2: an Arm 0 control failed")


# ------------------------------------------------------------------------------------------------ check

def check():
    """Rebuild every deck text from its recorded point and compare its key; rebuild budget.json; no simulation."""
    cen, topo, rows = topologies()
    ftopo = f_topologies(cen)
    allt = {**topo, **ftopo}
    results = load_results()
    bad = []
    for (pid, deck), rec in results.items():
        p = rec["point"]
        if point_id(p) != pid:
            bad.append(f"{pid}: point id")
            continue
        t = allt.get(p["topology"])
        if t is None:
            bad.append(f"{pid}: unknown topology")
            continue
        texts = [x[1] for x in (loop_texts(t, p) if deck == "loop" else closed_texts(t, p))]
        keys = [runner.deck_key(x) for x in texts]
        used = [a["key"] for a in rec["attempts"]]
        if any(k not in keys for k in used) or rec["key"] not in keys:
            bad.append(f"{pid} {deck}: deck key differs from the rebuilt text")
    old = json.loads(BUDGET.read_text()) if BUDGET.exists() else None
    new = evaluate(write=False)
    same = old is not None and json.dumps(old, sort_keys=True) == json.dumps(json.loads(json.dumps(new, sort_keys=True)), sort_keys=True)
    print(f"decks rebuilt: {len(results)}; key mismatches: {len(bad)}; budget.json identical: {same}")
    for b in bad[:20]:
        print(" ", b)
    return 0 if not bad and same else 1


def write_result(b):
    results = load_results()
    ck = STUDY / "checkpoints"
    guards = {p.name: json.loads(p.read_text()) for p in sorted(ck.glob("guard-*.json"))}
    state = json.loads((ck / "sweep-state.json").read_text()) if (ck / "sweep-state.json").exists() else None
    controls = json.loads((ck / "controls.json").read_text()) if (ck / "controls.json").exists() else None
    walls = [r["wall_s"] for r in results.values()]
    labels = {}
    for r in b["rows"]:
        k = r["label"].split(":")[0].split(" ")[0]
        labels[k] = labels.get(k, 0) + 1
    out = {"status": STATUS, "brief_sha256": sha_file(
        "circuit/orchestration/campaigns/osc-stack-20261114/mc04-s13-node-capacitance-budget-brief-20261127.md"),
        "pinned_inputs": PINNED, "models": MODEL_PINS, "deck_source_modules": {m: sha_file(m) for m in DECK_MODULES},
        "study_files": {f: sha_file(f"scripts/stack/studies/mc04_s13_node_cap_budget/{f}")
                        for f in ("cells.py", "runner.py", "budget.py", "guard.py", "test_s13.py")},
        "fingerprint": fingerprint(), "controls": controls, "sweep_state": state, "guards": guards,
        "deck_records": len(results), "invocations": invocations(results), "deck_cap": DECK_CAP,
        "deck_wall_s": {"sum": round(sum(walls), 1), "mean": round(sum(walls) / len(walls), 2) if walls else None,
                        "max": max(walls) if walls else None},
        "not_evaluated_decks": sum(1 for r in results.values() if r["status"] != "OK"),
        "label_counts": labels, "budget_sha256": hashlib.sha256(BUDGET.read_bytes()).hexdigest()}
    RESULT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--run", "--resume", "--evaluate", "--check", "--controls", "--census"):
        g.add_argument(a, action="store_true")
    ap.add_argument("--slice-min", type=float, default=25.0)
    ap.add_argument("--max-decks", type=int, default=None)
    a = ap.parse_args()
    if a.census:
        cen = cells.census()
        errs = cells.check_census(cen)
        CENSUS.write_text(json.dumps({"status": STATUS, **cen, "errors": errs}, indent=1, sort_keys=True) + "\n")
        print("P6", "PASS" if not errs else f"FAIL {errs}")
        check_models()
        MODELS.write_text(json.dumps({"status": STATUS, "models": [
            {"part": "OPA4196IDR (line-op-audio)", "subckt": "OPAx196", "file": ".circuit-cache/sources/opa196-model/OPAx196.LIB",
             "header": "Part: OPAx196; Date: 29AUG2022; Model Type: Generic; Model Version: Final 1.5",
             "zip_sha256": MODEL_PINS[".circuit-cache/sources/opa196-model/SBOMAF9E.ZIP"],
             "lib_sha256": MODEL_PINS[".circuit-cache/sources/opa196-model/OPAx196.LIB"],
             "source": "Takazudo/circuit-dev-resources commit 54c00fc8120e98fb0df02617587818f00609e8f3 (branch "
                       "claude/project-thread-iw3gai) texas-instruments/opa4196/opa4196-pspice-model-sbomaf9e.zip, read-only gh api"},
            {"part": "OPA4197IPWR / OPA4197IDR (line-op-precision, line-op-precision-d)", "subckt": "OPAx197",
             "file": ".circuit-cache/sources/opa197-model/OPAx197.LIB", "header": "Final 1.3 (23JUN2022), SBOMA34D",
             "zip_sha256": MODEL_PINS[".circuit-cache/sources/opa197-model/SBOMA34D.ZIP"],
             "lib_sha256": MODEL_PINS[".circuit-cache/sources/opa197-model/OPAx197.LIB"],
             "source": "retained source rows src-op-precision-vendor-model and src-op-precision-d-vendor-model"},
            {"part": "LM13700M/NOPB (line-ota)", "subckt": "LM13700/NS", "file": "design/spec/modules/spice/filter-model/LM13700.MOD",
             "lib_sha256": MODEL_PINS["design/spec/modules/spice/filter-model/LM13700.MOD"],
             "limit": "header warns AC bandwidth and phase margin are overstated by more than twofold"}],
            "missing": {"BAS16GW-QX": "BLOCKS class F", "BCM847BS,115": "BLOCKS class I",
                        "BAT54S,215": "bracketed behind 10 kOhm on an output (Ruling 6)",
                        "TMUX6112PWR": "output-capacitance pair 0 / 100 pF on REF9 (Ruling 6)",
                        "LM393BIDR": "bracketed behind 100 kOhm on the REF9 output (Ruling 6; interpretation)"}},
            indent=1) + "\n")
        sys.exit(1 if errs else 0)
    if a.controls:
        controls()
    elif a.run or a.resume:
        drive(a.slice_min, resume=a.resume, max_decks=a.max_decks)
    elif a.evaluate:
        b = evaluate()
        write_result(b)
    elif a.check:
        sys.exit(check())


if __name__ == "__main__":
    main()
