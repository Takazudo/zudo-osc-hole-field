"""MC04-S13 driver: node capacitance budgets from vendor-model ngspice decks (brief Revision 6, DS-161 to DS-173).

    budget.py --pins              Arm 0 P1, P2 and P3 (the P3 read-only fetch is compared by --fetched)
    budget.py --controls          Arm 0 P5, P7, P8 with the study's own runner (P4a and P4b are run outside)
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
    # Addendum A5 and B6: this brief at its current Revision 6, and, for the record only, the regenerated stage 1b paper result
    "circuit/orchestration/campaigns/osc-stack-20261114/mc04-s13-node-capacitance-budget-brief-20261127.md": "b4be52d50212dad993c489b5d2a1df62df1e2ae8a8ddc509acae0d037bbd0c69",
    "scripts/stack/studies/mc04_s1b_indicator_loops/result.json": "4058446308c49e1b044cf933eb788706c43782492fa7968ac12c6ed06574840c",
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


# ------------------------------------------------------------------------------------------------ seeds (Addendum B)

SEED_TOL_V = 50e-6  # B2.5: an evaluation operating point must equal the seed reference within 50 uV
OP_MOVE_V = 1e-4  # the retained "did not move" check between the two operating points of a loop deck
INPUT_TOL_V = 1e-3  # B2.3: amplifier inputs within 1 mV
RAIL_MARGIN_V = 1.0  # B2.3: output at least 1 V inside each rail
DC_TOL_V = 10e-3  # B2.3: a node with a derived DC value within 10 mV of it
RAILS_V = (-12.0, 12.0)
SEED_CAP = 180  # B2.7
SEEDS = {"store": {}, "sink": None}


class SeedCap(RuntimeError):
    pass


def loop_y(c):
    return "out" if c["follower"] else "inm"


def zero_point(p):
    return {**p, "c_pF": 0}


def seed_netlist(t, p, kind):
    """The evaluation deck's netlist at C_stray = 0 with nothing else changed (B2.1)."""
    c = t["circuit"]
    p0 = zero_point(p)
    if kind == "loop":
        lines = cells.loop_lines(c, p0["corner"], build_lines(t, p0, loop=True))
        return runner.loop_netlist(lines, x="xinm", y=loop_y(c))
    text, _, _ = cells.closed_text(c, p0["corner"], build_lines(t, p0, loop=False))
    return text.split("\n.control\n")[0]


def seed_id(netlist_text):
    return hashlib.sha256(netlist_text.encode()).hexdigest()[:24]


def bias_source(netlist_text):
    """B2.2: the cell's DC bias source, the DC voltage source with the largest non-zero value."""
    best = None
    for ln in netlist_text.splitlines():
        f = ln.split()
        if len(f) >= 5 and f[0].startswith(("Vdc_", "Vaux_", "Vac_")) and f[3] == "DC":
            v = float(f[4])
            if v != 0 and (best is None or abs(v) > abs(best[1])):
                best = (f[0].lower(), v)
    return best


def ideal_dc(lines, inm_pin, gref=0.0, inp_node="inp"):
    """Nodal DC solution with an ideal amplifier (V(IN-) = V(IN+), output free), capacitors open and gmin to `gref`."""
    G = {}
    fixed = {"0": 0.0}
    nodes = set()
    for ln in lines:
        f = ln.split()
        if not f or f[0].startswith((".", "*")):
            continue
        k = f[0][0].upper()
        if k == "R":
            a, b, v = f[1], f[2], cells.parse_value(f[3])
            nodes |= {a, b}
            G[(a, b)] = G.get((a, b), 0.0) + 1 / v
        elif k == "V":
            a, b = f[1], f[2]
            val = float(f[4]) if f[3] == "DC" else float(f[3])
            if b == "0":
                fixed[a] = val
            elif a == "0":
                fixed[b] = -val
            else:
                return None
        elif k in ("C", "I", "B"):
            nodes |= {f[1], f[2]}
        elif k == "X":
            nodes |= set(f[1:-1])
    if "XOTA" in " ".join(lines):
        return None
    unknown = sorted(n for n in nodes if n not in fixed)
    idx = {n: i for i, n in enumerate(unknown)}
    n = len(unknown)
    A = [[0.0] * n for _ in range(n)]
    rhs = [0.0] * n
    gmin = 1e-12
    for i, u in enumerate(unknown):
        A[i][i] += gmin
        rhs[i] += gmin * gref
    for (a, b), g in G.items():
        for x, y in ((a, b), (b, a)):
            if x in idx:
                A[idx[x]][idx[x]] += g
                if y in idx:
                    A[idx[x]][idx[y]] -= g
                else:
                    rhs[idx[x]] += g * fixed[y]
    if "out" not in idx:
        return None
    row = [0.0] * n  # the output's KCL row is replaced by the nullor: V(inp) - V(IN-) = 0
    rr = 0.0
    for node, s in ((inp_node, 1.0), (inm_pin, -1.0)):
        if node in idx:
            row[idx[node]] += s
        else:
            rr -= s * fixed[node]
    A[idx["out"]], rhs[idx["out"]] = row, rr
    try:
        x = runner.solve(A, rhs)
    except Exception:
        return None
    return {u: x[i] for i, u in enumerate(unknown)} | {k: v for k, v in fixed.items() if k != "0"}


def expected_dc(t, p):
    """B2.3: DC values derived from the specification netlist with an ideal amplifier, for OUT and the inverting
    input; a node whose value depends on gmin (no resistive DC path) has no derived value."""
    c = t["circuit"]
    if c["class"] == "G":
        return {}, "OTA cell (class G): no derived DC value; only the rail test applies (B2.3)"
    p0 = zero_point(p)
    lines = cells.loop_lines(c, p0["corner"], build_lines(t, p0, loop=False))
    inm_pin = "out" if c["follower"] else "inm"
    a = ideal_dc(lines, inm_pin, 0.0, c["inp_node"])
    b = ideal_dc(lines, inm_pin, 1.0, c["inp_node"])
    if a is None or b is None:
        return {}, "no ideal-amplifier DC solution derivable from the netlist"
    out = {}
    for node in ("out", inm_pin):
        if node in a and abs(a[node] - b[node]) < 1e-6:
            out[node] = round(a[node], 9)
    return out, ("ideal amplifier (IN- = IN+), capacitors open, the cell's resistors and DC sources from the "
                 "specification netlist; nodes without a resistive DC path are left out")


def seed_validity(c, kind, ref, expected):
    """B2.3 on a seed reference. Reasons carry no figure (B2.6)."""
    errs = []
    if c["class"] != "G":
        inm = "xinm" if kind == "loop" else ("out" if c["follower"] else "inm")
        ip = c["inp_node"]
        vin = {**ref, "0": 0.0}
        if ip not in vin or inm not in vin:
            errs.append("amplifier input nodes missing from the seed")
        elif abs(vin[ip] - vin[inm]) > INPUT_TOL_V:
            errs.append("amplifier inputs more than 1 mV apart")
    if "out" not in ref:
        errs.append("output node missing from the seed")
    elif not (RAILS_V[0] + RAIL_MARGIN_V <= ref["out"] <= RAILS_V[1] - RAIL_MARGIN_V):
        errs.append("output not at least 1 V inside each rail")
    for node, v in expected.items():
        if node not in ref or abs(ref[node] - v) > DC_TOL_V:
            errs.append(f"{node} more than 10 mV from its derived DC value")
    return errs


def get_seed(t, p, kind):
    net = seed_netlist(t, p, kind)
    sid = seed_id(net)
    store = SEEDS["store"]
    if sid in store:
        return store[sid]
    if len(store) >= SEED_CAP:
        raise SeedCap(f"seed cap {SEED_CAP} reached")
    expected, derivation = expected_dc(t, p)
    attempts, chosen = [], None
    for method in ("op", "dc ramp"):
        src = val = None
        if method == "dc ramp":
            bs = bias_source(net)
            if bs is None:
                attempts.append({"method": method, "result": "not applicable: no non-zero DC bias source"})
                break
            src, val = bs
        text = net.rstrip("\n") + "\n" + "\n".join(runner.seed_control(method, src, val))
        try:
            key, ref, nodeset, tranop, wall, _ = runner.run_seed(net, method, src, val)
        except (runner.OracleError, RuntimeError) as e:
            attempts.append({"method": method, "source": src, "key": runner.deck_key(text),
                             "result": "failed: " + str(e)[-300:]})
            continue
        errs = seed_validity(t["circuit"], kind, ref, expected)
        attempts.append({"method": method, "source": src, "value": val, "key": key, "transient_op": tranop,
                         "wall_s": round(wall, 2), "result": "valid" if not errs else "invalid", "reasons": errs})
        if not errs:
            chosen = {"method": method, "ref": ref, "nodeset": nodeset}
            break
    rec = {"deck": "seed", "point_id": sid, "kind": kind, "point": {**zero_point(p), "phase": "seed"},
           "expected_dc": expected, "derivation": derivation, "attempts": attempts,
           "wall_s": round(sum(a.get("wall_s", 0) for a in attempts), 2)}
    if chosen:
        ns = "\n".join(chosen["nodeset"])
        rec.update({"status": "OK", "valid": True, "method": chosen["method"], "reference": chosen["ref"],
                    "nodeset": chosen["nodeset"], "nodeset_sha256": hashlib.sha256(ns.encode()).hexdigest()})
    else:
        rec.update({"status": "NOT EVALUATED", "valid": False, "reason": "no valid operating point"})
    store[sid] = rec
    if SEEDS["sink"]:
        SEEDS["sink"](rec)
    return rec


def accept_op(ext, ref):
    if set(ext) != set(ref):
        return "operating-point node set differs from the seed"
    if any(abs(ext[k] - ref[k]) > SEED_TOL_V for k in ref):
        return "operating point differs from the seed reference by more than 50 uV"
    return None


def dc_moved(op1, op2):
    if set(op1) != set(op2) or any(abs(op1[k] - op2[k]) > OP_MOVE_V for k in op1):
        return "operating point moved between the AC runs (more than 0.1 mV)"
    return None


# ------------------------------------------------------------------------------------------------ decks

def loop_texts(t, p, nodeset=()):
    c = t["circuit"]
    lines = cells.loop_lines(c, p["corner"], build_lines(t, p, loop=True))
    out = []
    for name, tol in runner.LOOP_TOLERANCES:
        text, vv, vi = runner.loop_text(lines, x="xinm", y=loop_y(c), tol=tol, nodeset=nodeset)
        out.append((name, text, vv, vi))
    return out


def closed_texts(t, p, nodeset=()):
    c = t["circuit"]
    lines = build_lines(t, p, loop=False)
    text, files, P = cells.closed_text(c, p["corner"], lines)
    ns = "".join(x + "\n" for x in nodeset)
    text = text.replace("\n.control\n", "\n" + ns + ".control\n", 1)
    gear = text.replace("\n.control\n", "\n.options method=gear\n.control\n", 1)
    return [("ngspice default (trap)", text, files, P), ("gear", gear, files, P)]


def not_evaluated(seed, attempts=()):
    return {"status": "NOT EVALUATED", "reason": "no valid operating point" if not seed["valid"] else
            "no tolerance step gave an accepted operating point", "key": attempts[0]["key"] if attempts else None,
            "metrics": None, "attempts": list(attempts), "seed_id": seed["point_id"]}


def oracle_failure(msg):
    low = msg.lower()
    if "timeout" in low or "timed out" in low:
        return "timeout"
    if "timestep too small" in low or "singular" in low or "converge" in low or "gmin" in low or \
            "source stepping" in low:
        return "no convergence"
    return None


def run_loop(t, p):
    seed = get_seed(t, p, "loop")
    if not seed["valid"]:
        return not_evaluated(seed)
    attempts = []
    for name, text, vv, vi in loop_texts(t, p, seed["nodeset"]):
        try:
            key, tab, wall = runner.run(text, ["op1", "v", "i", "op2"])
        except (runner.OracleError, RuntimeError) as e:
            why = oracle_failure(str(e))
            if why is None:
                raise
            attempts.append({"tolerance": name, "result": why, "key": runner.deck_key(text)})
            continue
        e1, e2 = runner.external_nodes(tab["op1"]), runner.external_nodes(tab["op2"])
        why = accept_op(e1, seed["reference"]) or accept_op(e2, seed["reference"]) or dc_moved(e1, e2)
        attempts.append({"tolerance": name, "result": why or "accepted", "key": key, "wall_s": round(wall, 2),
                         "transient_op": "Transient op" in runner.last_log(key)})
        if why is None:
            m = runner.loop_metrics(tab["v"], tab["i"], vv, vi)
            m["op"] = dict(e1)  # accepted, full precision
            return {"status": "OK", "key": key, "metrics": m, "attempts": attempts, "seed_id": seed["point_id"],
                    "seed_sha256": seed["nodeset_sha256"], "accepted_step": name}
    return not_evaluated(seed, attempts)


def run_closed(t, p):
    seed = get_seed(t, p, "closed")
    if not seed["valid"]:
        return not_evaluated(seed)
    attempts = []
    for name, text, files, P in closed_texts(t, p, seed["nodeset"]):
        try:
            key, tab, wall = runner.run(text, files)
        except (runner.OracleError, RuntimeError) as e:
            why = oracle_failure(str(e))
            if why is None:
                raise
            attempts.append({"integration": name, "result": why, "key": runner.deck_key(text)})
            continue
        e0 = runner.external_nodes(tab["op"])
        why = accept_op(e0, seed["reference"])
        attempts.append({"integration": name, "result": why or "accepted", "key": key, "wall_s": round(wall, 2),
                         "transient_op": "Transient op" in runner.last_log(key)})
        if why is None:
            m = runner.closed_metrics(t["circuit"], p["corner"], P, tab)
            m["op"] = dict(e0)  # accepted, full precision
            m["stimulus"] = stimulus_record(t["circuit"], P)
            return {"status": "OK", "key": key, "metrics": m, "attempts": attempts, "seed_id": seed["point_id"],
                    "seed_sha256": seed["nodeset_sha256"], "accepted_step": name}
    return not_evaluated(seed, attempts)


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
    return sum(1 for r in results.values() for a in r["attempts"] if a.get("key"))


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

    def seed_sink(rec):
        append(rec)
        results[(rec["point_id"], "seed")] = rec
    SEEDS["store"] = {pid: rec for (pid, deck), rec in results.items() if deck == "seed"}
    SEEDS["sink"] = seed_sink
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
            if invocations(results) + 6 > DECK_CAP:
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
                try:
                    out = run_loop(t, p) if deck == "loop" else run_closed(t, p)
                except SeedCap:
                    reason = "seed cap reached"
                    break
                rec = {"point_id": pid, "deck": deck, "point": p, "phase": ph, **out,
                       "wall_s": round(time.time() - t0, 2)}
                append(rec)
                results[(pid, deck)] = rec
                done_new += 1
            if reason == "seed cap reached":
                break
            if not ready and not [x for x in todo[1:] if x[0] == "sweep"]:
                continue
    finally:
        if created:
            runner.remove_spiceinit()
        survivors = kill_pinned_containers()
        SEEDS["sink"] = None
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
              "what_if": whatif, "f_diagnostic": fdiag,
              "P9_cross_check": {"note": "not pass or fail; first-order typical-only estimate of the 100k/100k "
                                         "uncompensated summer (f2_loop_estimate.py)", "rows": p9_rows(topo, results)}}
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
        return "NOT EVALUATED: no accepted operating point or no convergence at " + ", ".join(f"{x} pF" for v in ne for x in v["not_evaluated"]), None, None
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
    "(Addendum B) the seed selects the zero-stray operating point, so no other DC state, such as a latched output "
    "or a start-up state, is examined",
]
P9_ESTIMATE = {0: 31.4, 10: 21.3, 20: 17.1}  # f2_loop_estimate.py first-order figures (brief "Expected outcome")


def p9_rows(topo, results):
    """P9, cross-check only: class E loop phase margin at 0, 10 and 20 pF beside the first-order estimate."""
    out = []
    for k, t in sorted(topo.items()):
        if not t["circuit"]["subclass"].startswith("E"):
            continue
        for p in sweep_points(t):
            if p["c_pF"] not in P9_ESTIMATE:
                continue
            lo = results.get((point_id(p), "loop"))
            pm = lo["metrics"]["phase_margin_deg"] if lo and lo["status"] == "OK" else None
            out.append({"topology": k, "nets": t["nets"], "subclass": t["circuit"]["subclass"], "corner": p["corner"],
                        "c_pF": p["c_pF"], "pm_deg": pm, "estimate_deg": P9_ESTIMATE[p["c_pF"]],
                        "difference_deg": None if pm is None else round(pm - P9_ESTIMATE[p["c_pF"]], 2),
                        "status": "NOT RUN" if lo is None else lo["status"]})
    return out
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


def loop_run(lines, x, y, amp_inputs=None):
    """A P5/P8/M3 loop deck through the seeded runner: seed at the same netlist (no stray to remove), then the
    evaluation deck with the seed as .nodeset, accepted only on the 50 uV and 0.1 mV tests (Addendum B2)."""
    net = runner.loop_netlist(lines, x=x, y=y)
    skey, ref, nodeset, tranop, _, _ = runner.run_seed(net)
    seed = {"key": skey, "transient_op": tranop, "nodeset_sha256": hashlib.sha256("\n".join(nodeset).encode()).hexdigest()}
    if amp_inputs:
        vin = {**ref, "0": 0.0}
        errs = []
        if abs(vin[amp_inputs[0]] - vin[amp_inputs[1]]) > INPUT_TOL_V:
            errs.append("amplifier inputs more than 1 mV apart")
        if not (RAILS_V[0] + RAIL_MARGIN_V <= ref["out"] <= RAILS_V[1] - RAIL_MARGIN_V):
            errs.append("output not at least 1 V inside each rail")
        if errs:
            return {"seed": seed, "result": "no valid operating point", "reasons": errs, "pm": None, "f": None}
    text, vv, vi = runner.loop_text(lines, x=x, y=y, tol=None, ac="ac dec 100 10 100meg", nodeset=nodeset)
    key, tab, wall = runner.run(text, ["op1", "v", "i", "op2"])
    e1, e2 = runner.external_nodes(tab["op1"]), runner.external_nodes(tab["op2"])
    why = accept_op(e1, ref) or accept_op(e2, ref) or dc_moved(e1, e2)
    if why:
        return {"seed": seed, "deck": key, "result": why, "pm": None, "f": None}
    f, T, _ = runner.loop_gain(tab["v"], tab["i"], vv, vi)
    m = runner.margins(f, T)
    u = [q for q in m["unity"] if q["falling"]]
    if not u:  # no falling unity crossing: no phase margin to report (a P5 failure, M3's expected outcome)
        return {"seed": seed, "deck": key, "result": "accepted; no falling unity crossing", "pm": None, "f": None}
    return {"seed": seed, "deck": key, "result": "accepted", "pm": u[0]["pm_deg"], "f": u[0]["f_Hz"]}


def p7_pass(res, need_k4):
    """Addendum B4: a positive control passes only as an evaluated failure of its criteria; a missing or
    NOT EVALUATED result is never counted as the required failure."""
    k1 = res.get("loop", {}).get("status") == "OK" and res.get("K1_fails") is True
    if not need_k4:
        return k1
    k4 = res.get("closed", {}).get("status") == "OK" and res.get("K4_fails") is True
    return k1 and k4


def p6b_check(seed, kind):
    """B3 on one H-REF9 seed: OUT 9.000 V +/- 10 mV; IN- within 1 mV of IN+ at 5.000 V."""
    if not seed["valid"]:
        return ["no valid operating point"]
    ref = seed["reference"]
    inm = "xinm" if kind == "loop" else "inm"
    errs = []
    if abs(ref["out"] - 9.0) > DC_TOL_V:
        errs.append("OUT more than 10 mV from 9.000 V")
    if abs(ref["inp"] - 5.0) > INPUT_TOL_V or abs(ref[inm] - ref["inp"]) > INPUT_TOL_V:
        errs.append("IN- not within 1 mV of IN+ at 5.000 V")
    return errs


def controls():
    check_pins(PINNED)
    check_models()
    if kill_pinned_containers():
        raise SystemExit("STOP 3")
    out = {"P5": [], "P8": [], "P6b": [], "P7": {}, "M3": [], "seeds": []}
    SEEDS["store"], SEEDS["sink"] = {}, out["seeds"].append
    created = runner.ensure_spiceinit()
    stop = None
    try:
        for rl, want in LOOP_VALIDATION:
            base = ["MC04-S13 P5 loop-break validation, linear two-pole loop", "E1 o1 0 0 x 1000", "Rp o1 o2 1k",
                    "Cp o2 0 1.5915n", "E2 o3 0 o2 0 1", "Rq o3 o4 1k", "Cq o4 0 159.15p", "E3 o5 0 o4 0 1",
                    "Ro o5 y 1k", "Rg y 0 2k", f"Rl x 0 {rl:g}"]
            r = loop_run(base, "x", "y")
            pm = r["pm"]
            out["P5"].append({"R_load_ohm": rl, "pm_deg": None if pm is None else round(pm, 4), "retained_deg": want,
                              "pass": pm is not None and abs(pm - want) <= 0.1, **{k: r[k] for k in r if k not in ("pm", "f")}})
            r2 = loop_run(base, "y", "x")  # M3: probe polarity swapped
            pm2 = r2["pm"]
            out["M3"].append({"R_load_ohm": rl, "pm_deg": None if pm2 is None else round(pm2, 4),
                              "fails_P5": pm2 is None or abs(pm2 - want) > 0.1,
                              **{k: r2[k] for k in r2 if k not in ("pm", "f")}})
        if not all(x["pass"] for x in out["P5"]):
            stop = "P5"
        cen, topo, rows = topologies()
        if stop is None:  # P6 is the offline census (--census); P6b follows it (Addendum B3)
            t = topo[rows["/E2/REF9_FB"]["topology"]]
            for corner in cells.corners_of(t["circuit"]):
                p = sweep_points(t, values=[0], corners=[corner], phase="P6b")[0]
                row = {"corner": corner, "seeds": {}, "pass": True}
                for kind in ("loop", "closed"):
                    s = get_seed(t, p, kind)
                    errs = p6b_check(s, kind)
                    row["seeds"][kind] = {"seed_id": s["point_id"], "method": s.get("method"), "errors": errs,
                                          "out_V": s["reference"]["out"] if s["valid"] and not errs else None}
                    row["pass"] &= not errs
                lo, cl = run_loop(t, p), run_closed(t, p)
                row["loop"] = {"status": lo["status"], "accepted_step": lo.get("accepted_step"), "attempts": lo["attempts"]}
                row["closed"] = {"status": cl["status"], "accepted_step": cl.get("accepted_step"), "attempts": cl["attempts"]}
                row["pass"] &= lo["status"] == "OK" and cl["status"] == "OK"
                out["P6b"].append(row)
            if not all(x["pass"] for x in out["P6b"]):
                stop = "P6b"
        if stop is None:
            for net, need_k4 in (("/W1/DRIVE_INV_SUM", True), ("/E2/REF9_FB", False)):
                t = topo[rows[net]["topology"]]
                p = sweep_points(t, values=[1000], phase="P7")[0]
                res = {"corner": p["corner"], "c_stray": "1 nF"}
                lo = run_loop(t, p)
                res["loop"] = {"status": lo["status"], "accepted_step": lo.get("accepted_step"),
                               "pm_deg": lo["metrics"]["phase_margin_deg"] if lo["metrics"] else None,
                               "attempts": lo["attempts"], "seed_id": lo.get("seed_id")}
                if lo["metrics"] is not None:
                    res["K1_fails"] = not runner.k1_k2(lo["metrics"])[0]
                if need_k4:
                    cl = run_closed(t, p)
                    res["closed"] = {"status": cl["status"], "accepted_step": cl.get("accepted_step"),
                                     "attempts": cl["attempts"], "seed_id": cl.get("seed_id")}
                    if cl["metrics"] is not None:
                        ov = max(o["overshoot_percent"] or 0 for v in cl["metrics"]["k4"].values() for o in v)
                        res["closed"]["max_overshoot_percent"] = ov
                        res["K4_fails"] = ov > runner.OVERSHOOT_LIMIT
                res["pass"] = p7_pass(res, need_k4)
                out["P7"][net] = res
            if not all(x["pass"] for x in out["P7"].values()):
                stop = "P7"
        if stop is None:
            for sub, lib in (("OPAx196", cells.MODEL_LIBS["OPAx196"]), ("OPAx197", cells.MODEL_LIBS["OPAx197"])):
                lines = [f"MC04-S13 P8 plain follower {sub}", ".param TEMP=27", f".include {lib}", "Vplus vp 0 12",
                         "Vminus vn 0 -12", f"XU 0 xinm vp vn out {sub}"]
                r = loop_run(lines, "xinm", "out", amp_inputs=("0", "xinm"))
                want_pm, want_f = FOLLOWER[sub]
                pm, f = r["pm"], r["f"]
                out["P8"].append({"model": sub, "pm_deg": None if pm is None else round(pm, 3),
                                  "crossover_Hz": None if f is None else round(f, 1), "retained": FOLLOWER[sub],
                                  "pass": pm is not None and abs(pm - want_pm) <= 0.1 and abs(f / want_f - 1) <= 0.005,
                                  **{k: r[k] for k in r if k not in ("pm", "f")}})
            if not all(x["pass"] for x in out["P8"]):
                stop = "P8"
    finally:
        if created:
            runner.remove_spiceinit()
        kill_pinned_containers()
        SEEDS["sink"] = None
    out["invocations"] = runner.INVOCATIONS["count"]
    out["stopped_at"] = stop
    out["pass"] = stop is None and all(x["fails_P5"] for x in out["M3"])
    (STUDY / "checkpoints/controls.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("stopped_at", "pass", "invocations")}))
    if not out["pass"]:
        raise SystemExit(f"STOP 2: Arm 0 control failed ({stop or 'M3'})")


def mutation_m12():
    """M12: the /E2/REF9_FB 1 nF loop deck with its seed removed must be rejected by the operating-point
    acceptance test: the row is NOT EVALUATED and carries no K1 figure. Writes checkpoints/m12.json."""
    check_pins(PINNED)
    check_models()
    if kill_pinned_containers():
        raise SystemExit("STOP 3")
    cen, topo, rows = topologies()
    t = topo[rows["/E2/REF9_FB"]["topology"]]
    p = sweep_points(t, values=[1000], phase="P7")[0]
    SEEDS["store"], SEEDS["sink"] = {}, None
    created = runner.ensure_spiceinit()
    attempts = []
    try:
        seed = get_seed(t, p, "loop")
        if not seed["valid"]:
            raise SystemExit("M12: the REF9 seed is not valid; see P6b")
        for name, text, vv, vi in loop_texts(t, p, nodeset=()):  # the mutation: no .nodeset
            try:
                key, tab, wall = runner.run(text, ["op1", "v", "i", "op2"])
            except (runner.OracleError, RuntimeError) as e:
                why = oracle_failure(str(e))
                if why is None:
                    raise
                attempts.append({"tolerance": name, "result": why, "key": runner.deck_key(text)})
                continue
            e1, e2 = runner.external_nodes(tab["op1"]), runner.external_nodes(tab["op2"])
            why = accept_op(e1, seed["reference"]) or accept_op(e2, seed["reference"]) or dc_moved(e1, e2)
            attempts.append({"tolerance": name, "result": why or "accepted", "key": key, "wall_s": round(wall, 2)})
            if why is None:
                break
    finally:
        if created:
            runner.remove_spiceinit()
        kill_pinned_containers()
    accepted = any(a["result"] == "accepted" for a in attempts)
    rec = {"mutation": "M12", "seed_id": seed["point_id"], "attempts": attempts,
           "status": "OK" if accepted else "NOT EVALUATED", "metrics": None, "rejected": not accepted}
    (STUDY / "checkpoints/m12.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("status", "rejected")}))
    if accepted:
        raise SystemExit("M12 not rejected: an unseeded deck passed the acceptance test")


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
        t = allt.get(p["topology"])
        if t is None:
            bad.append(f"{pid}: unknown topology")
            continue
        if deck == "seed":
            net = seed_netlist(t, p, rec["kind"])
            if seed_id(net) != pid:
                bad.append(f"{pid}: seed netlist differs from the rebuilt one")
            for a in rec["attempts"]:
                if a.get("key"):
                    txt = net.rstrip("\n") + "\n" + "\n".join(runner.seed_control(a["method"], a.get("source"), a.get("value")))
                    if runner.deck_key(txt) != a["key"]:
                        bad.append(f"{pid}: seed deck key differs")
            if rec["valid"]:
                if accept_op(rec["reference"], rec["reference"]) or seed_validity(t["circuit"], rec["kind"], rec["reference"], rec["expected_dc"]):
                    bad.append(f"{pid}: seed marked valid but fails B2.3")
            continue
        if point_id(p) != pid:
            bad.append(f"{pid}: point id")
            continue
        seed = results.get((rec.get("seed_id"), "seed"))
        if seed is None or seed_id(seed_netlist(t, p, deck)) != rec.get("seed_id"):
            bad.append(f"{pid} {deck}: seed missing or not the zero-stray deck of this point")
            continue
        ns = seed.get("nodeset", [])
        texts = [x[1] for x in (loop_texts(t, p, ns) if deck == "loop" else closed_texts(t, p, ns))]
        keys = [runner.deck_key(x) for x in texts]
        used = [a["key"] for a in rec["attempts"] if a.get("key")]
        if any(k not in keys for k in used) or (rec["key"] is not None and rec["key"] not in keys):
            bad.append(f"{pid} {deck}: deck key differs from the rebuilt text")
        if rec["status"] == "OK" and accept_op(rec["metrics"]["op"], seed["reference"]):
            bad.append(f"{pid} {deck}: recorded operating point differs from its seed by more than 50 uV")
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
    arm0 = {"P1_P3": json.loads((ck / "arm0-p1-p3.json").read_text()) if (ck / "arm0-p1-p3.json").exists() else None}
    if (ck / "p4b.jsonl").exists():
        lines = [json.loads(x) for x in (ck / "p4b.jsonl").read_text().splitlines() if x.strip()]
        arm0["P4b"] = {"slices": [{k: v for k, v in e.items() if k != "substitutions"} for e in lines
                                  if e["kind"] in ("start", "resume", "slice_end", "stop")],
                       "batches": len([e for e in lines if e["kind"] == "batch"]),
                       "verdict": next((e for e in lines if e["kind"] == "verdict"), None)}
    walls = [r["wall_s"] for r in results.values()]
    labels = {}
    for r in b["rows"]:
        k = r["label"].split(":")[0].split(" ")[0]
        labels[k] = labels.get(k, 0) + 1
    out = {"status": STATUS, "brief_sha256": sha_file(
        "circuit/orchestration/campaigns/osc-stack-20261114/mc04-s13-node-capacitance-budget-brief-20261127.md"),
        "pinned_inputs": PINNED, "models": MODEL_PINS, "deck_source_modules": {m: sha_file(m) for m in DECK_MODULES},
        "study_files": {f: sha_file(f"scripts/stack/studies/mc04_s13_node_cap_budget/{f}")
                        for f in ("cells.py", "runner.py", "budget.py", "guard.py", "p4b.py", "test_s13.py")},
        "fingerprint": fingerprint(), "arm0": arm0, "controls": controls, "sweep_state": state, "guards": guards,
        "deck_records": len(results), "invocations": invocations(results), "deck_cap": DECK_CAP,
        "deck_wall_s": {"sum": round(sum(walls), 1), "mean": round(sum(walls) / len(walls), 2) if walls else None,
                        "max": max(walls) if walls else None},
        "not_evaluated_decks": sum(1 for r in results.values() if r["status"] != "OK"),
        "label_counts": labels, "budget_sha256": hashlib.sha256(BUDGET.read_bytes()).hexdigest()}
    RESULT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")


def pins(fetched):
    """Arm 0 P1, P2 and P3. `fetched` is the OPAx196 ZIP read read-only from circuit-dev-resources 54c00fc8."""
    import subprocess
    from guard import IMAGE
    check_pins(PINNED)
    out = {"P1": {"result": "PASS", "count": len(PINNED), "pins": PINNED}}
    run = lambda *a: subprocess.run(list(a), capture_output=True, text=True, cwd=ROOT, timeout=300)  # noqa: E731
    image_id = run("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}").stdout.strip()
    ver = run("bash", "scripts/kicad/run.sh", "kicad-cli", "version").stdout.strip()
    banner = run("bash", "scripts/kicad/run.sh", "ngspice", "-v").stdout
    ng = next((x.strip() for x in banner.splitlines() if "ngspice-" in x), banner.strip()[:120])
    p2 = image_id == "sha256:" + IMAGE.split("sha256:")[1] and ver == "10.0.6" and "ngspice-44.2" in ng
    out["P2"] = {"result": "PASS" if p2 else "FAIL", "image": IMAGE, "image_id": image_id,
                 "kicad_cli_version": ver, "ngspice_banner": ng}
    if kill_pinned_containers():
        raise SystemExit("STOP 3: container survived docker kill")
    zip_pin = MODEL_PINS[".circuit-cache/sources/opa196-model/SBOMAF9E.ZIP"]
    f_sha = hashlib.sha256(Path(fetched).read_bytes()).hexdigest()
    cached = ROOT / ".circuit-cache/sources/opa196-model/SBOMAF9E.ZIP"
    same = cached.exists() and cached.read_bytes() == Path(fetched).read_bytes()
    check_models()
    p3 = f_sha == zip_pin and same
    out["P3"] = {"result": "PASS" if p3 else "FAIL", "fetched_sha256": f_sha, "cache_equals_fetch": same,
                 "source": "Takazudo/circuit-dev-resources 54c00fc8 texas-instruments/opa4196/"
                           "opa4196-pspice-model-sbomaf9e.zip (gh api, read-only)", "model_pins": MODEL_PINS}
    (STUDY / "checkpoints/arm0-p1-p3.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v["result"] for k, v in out.items()}))
    if not (p2 and p3):
        raise SystemExit("STOP 2/3: P2 or P3 failed")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ("--run", "--resume", "--evaluate", "--check", "--controls", "--census", "--m12"):
        g.add_argument(a, action="store_true")
    g.add_argument("--pins", metavar="FETCHED_ZIP")
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
    if a.pins:
        pins(a.pins)
    elif a.m12:
        mutation_m12()
    elif a.controls:
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
