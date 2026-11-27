"""MC04-S13 Arm 0 P4b as redefined by brief Revision 4, Addendum A (DS-171).

    p4b.py --run       first slice (refuses if checkpoints/p4b.jsonl exists)
    p4b.py --resume    next slice: re-check P1 and P3, stop the oracle, verify the stored batches, continue

Reproduces `design/reports/spice/input-buffer-vendor.json` through the pinned, unedited
`design.spec.cells.sweep_input_buffer_vendor` module, using only its own `models(offline=True)`, `run_all()`,
`validate_loop_break()` and `report()`. Two module attributes are replaced in memory, and nothing else is changed:
`paper_point` by a stub that reads no file, and `all_cases` per batch by the next five cases of the original list.
The original `all_cases()` list is taken once per process, before any substitution; the 136th case forms a last
batch of one. The comparison deletes `metrics.paper_screen` on exactly `results[62]` to `results[77]` on both sides
and then requires string equality of `json.dumps(obj, indent=2) + "\n"`.

MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

STUDY = Path(__file__).resolve().parent
sys.path[:0] = [str(STUDY), str(STUDY.parents[3])]

import budget  # noqa: E402
from cells import ROOT  # noqa: E402
from guard import kill_pinned_containers  # noqa: E402

JOURNAL = STUDY / "checkpoints/p4b.jsonl"
MODULE = "design.spec.cells.sweep_input_buffer_vendor"
SCRIPT = "design/spec/cells/sweep_input_buffer_vendor.py"
RECEIPT = "design/reports/spice/input-buffer-vendor.json"
PAPER = "scripts/stack/studies/mc04_s1b_indicator_loops/result.json"
OWN_PINS = {k: budget.PINNED[k] for k in (SCRIPT, RECEIPT, PAPER)}
BATCH = 5
N_CASES = 136
EXCLUDED = list(range(62, 78))  # the 16 OPA4196 case5a rows that carry metrics.paper_screen (Addendum A2.4)
SLICE_S = 20 * 60
CEILING_S = 120 * 60
MAX_SLICES = 8
STUB = {"paper_pm_deg": None, "basis": "EXCLUDED BY MC04-S13 ADDENDUM A", "run_minus_paper_deg": None}
SUBSTITUTIONS = [
    {"attribute": "paper_point", "replacement": "stub returning " + json.dumps(STUB) + "; reads no file"},
    {"attribute": "all_cases", "replacement": "per batch, the next 5 cases of the original all_cases() list "
                                              "(taken once per process before any substitution), in order"},
]
SPICEINIT = "set ngbehavior=ps\n"


def identity(c):
    return {k: c[k] for k in ("model", "case", "cell", "variant")}


def batches(n=N_CASES, size=BATCH):
    return [(i, min(i + size, n) - 1) for i in range(0, n, size)]


def body(obj):
    return json.dumps(obj, indent=2) + "\n"


def carriers(rep):
    return [i for i, row in enumerate(rep.get("results", [])) if "paper_screen" in row.get("metrics", {})]


def compare(produced, retained):
    """Addendum A2.4 and A2.5. Returns a list of differences; empty means P4b equality holds."""
    errors = []
    for side, rep in (("produced", produced), ("retained", retained)):
        got = carriers(rep)
        if got != EXCLUDED:
            errors.append(f"{side}: metrics.paper_screen on rows {got}, expected exactly {EXCLUDED[0]}..{EXCLUDED[-1]}")
        for i in EXCLUDED:
            row = rep["results"][i] if i < len(rep.get("results", [])) else {}
            if (row.get("model"), row.get("case")) != ("OPA4196", "case5a"):
                errors.append(f"{side}: results[{i}] is not an OPA4196 case5a row")
    if errors:
        return errors
    a, b = copy.deepcopy(produced), copy.deepcopy(retained)
    for rep in (a, b):
        for i in EXCLUDED:
            del rep["results"][i]["metrics"]["paper_screen"]
    if body(a) != body(b):
        errors.append("difference outside the exclusion: " + first_difference(a, b))
    return errors


def first_difference(a, b, path="$"):
    if type(a) is not type(b):
        return f"{path}: {a!r} != {b!r}"
    if isinstance(a, dict):
        if list(a) != list(b):
            return f"{path}: keys {list(a)} != {list(b)}"
        for k in a:
            if body(a[k]) != body(b[k]):
                return first_difference(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            if body(x) != body(y):
                return first_difference(x, y, f"{path}[{i}]")
    return f"{path}: {a!r} != {b!r}"


def named_figures(produced, retained):
    """Addendum A2.6: retained and reproduced PM and crossover of case5a, the controls and the validation rows."""
    def pick(rep):
        rows = [{"index": i, **identity(r), "phase_margin_deg": r["metrics"].get("phase_margin_deg"),
                 "crossover_Hz": r["metrics"].get("crossover_Hz")}
                for i, r in enumerate(rep["results"]) if r["case"] in ("case5a", "case5a_control")]
        val = [{"R_load_ohm": v["R_load_ohm"], "middlebrook_pm_deg": v["middlebrook"]["phase_margin_deg"],
                "middlebrook_crossover_Hz": v["middlebrook"]["crossover_Hz"],
                "analytic_pm_deg": v["analytic"]["phase_margin_deg"]} for v in rep["loop_break_validation"]]
        return rows, val
    pr, pv = pick(produced)
    rr, rv = pick(retained)
    loops = [{**r, "phase_margin_deg": {"retained": r["phase_margin_deg"], "reproduced": p["phase_margin_deg"]},
              "crossover_Hz": {"retained": r["crossover_Hz"], "reproduced": p["crossover_Hz"]}}
             for r, p in zip(rr, pr)]
    val = [{"retained": r, "reproduced": p} for r, p in zip(rv, pv)]
    return {"case5a_and_controls": loops, "loop_break_validation": val}


def append(rec):
    with JOURNAL.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def journal():
    if not JOURNAL.exists():
        return []
    return [json.loads(x) for x in JOURNAL.read_text().splitlines() if x.strip()]


def stop(msg, **extra):
    append({"kind": "stop", "time": now(), "reason": msg, **extra})
    survivors = kill_pinned_containers()
    raise SystemExit(f"{msg}; containers after docker kill: {survivors}")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def clear_spiceinit():
    """Addendum A4: a killed run_all() leaves .spiceinit; delete it only if untracked and exactly the PSpice line."""
    init = ROOT / ".spiceinit"
    if not init.exists():
        return None
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", ".spiceinit"], cwd=ROOT,
                             capture_output=True).returncode == 0
    if tracked or init.read_bytes() != SPICEINIT.encode():
        raise SystemExit("STOP 2: .spiceinit exists and is tracked or not exactly 'set ngbehavior=ps'")
    init.unlink()
    return "deleted a leftover untracked .spiceinit (exactly 'set ngbehavior=ps')"


def preflight():
    budget.check_pins(budget.PINNED)  # P1
    budget.check_models()  # P3
    survivors = kill_pinned_containers()
    if survivors:
        raise SystemExit(f"STOP 3: container survived docker kill: {survivors}")
    return clear_spiceinit()


def slice_run(resume):
    t_start = time.time()
    entries = journal()
    if not resume and entries:
        raise SystemExit("checkpoints/p4b.jsonl exists: use --resume")
    if resume and not entries:
        raise SystemExit("nothing to resume")
    if any(e["kind"] in ("verdict", "stop") for e in entries):
        raise SystemExit("P4b already finished or stopped; see checkpoints/p4b.jsonl")
    cleared = preflight()

    import importlib
    m = importlib.import_module(MODULE)
    m.models(offline=True)
    original_fn = m.all_cases
    original = original_fn()  # once per process, before any substitution
    ids = [identity(c) for c in original]
    if len(original) != N_CASES:
        stop(f"STOP 2: all_cases() has {len(original)} cases, expected {N_CASES}")
    m.paper_point = lambda cap_key, bias_key, pm: dict(STUB)

    slices = [e for e in entries if e["kind"] in ("start", "resume")]
    if len(slices) >= MAX_SLICES:
        stop(f"STOP 3: P4b slice ceiling {MAX_SLICES} reached")
    compute = sum(e["wall_s"] for e in entries if e["kind"] == "batch")
    done = [e for e in entries if e["kind"] == "batch"]
    for j, e in enumerate(done):
        first, last = batches()[j]
        if (e["first"], e["last"]) != (first, last) or e["cases"] != ids[first:last + 1]:
            stop(f"STOP 2: stored batch {j} does not match the original case list at {first}..{last}")
    append({"kind": "resume" if resume else "start", "time": now(), "slice": len(slices) + 1,
            "substitutions": SUBSTITUTIONS, "spiceinit": cleared, "batches_stored": len(done),
            "original_case_count": len(original), "original_cases_sha256": hashlib.sha256(
                json.dumps(ids).encode()).hexdigest(), "pins": {k: budget.sha_file(k) for k in OWN_PINS}})

    for j in range(len(done), len(batches())):
        if time.time() - t_start > SLICE_S:
            kill_pinned_containers()
            append({"kind": "slice_end", "time": now(), "next_batch": j})
            print(f"slice end before batch {j} of {len(batches())}", flush=True)
            return
        if compute > CEILING_S:
            stop(f"STOP 3: P4b compute ceiling {CEILING_S} s reached")
        survivors = kill_pinned_containers()
        if survivors:
            stop(f"STOP 3: container survived docker kill: {survivors}")
        first, last = batches()[j]
        chunk = original[first:last + 1]
        m.all_cases = lambda chunk=chunk: list(chunk)
        t0 = time.time()
        try:
            rows = m.run_all()
        except Exception as error:  # a deck timeout or oracle failure: stop the oracle and stop
            stop(f"STOP 2/3: run_all() raised in batch {j} ({first}..{last}): {type(error).__name__}: {error}")
        wall = round(time.time() - t0, 1)
        compute += wall
        got = [identity(r) for r in rows]
        if got != ids[first:last + 1]:
            stop(f"STOP 2: batch {j} returned rows {got} for cases {ids[first:last + 1]}")
        append({"kind": "batch", "batch": j, "first": first, "last": last, "cases": got, "rows": rows,
                "wall_s": wall, "time": now()})
        print(f"batch {j} ({first}..{last}) done in {wall} s", flush=True)

    m.all_cases = original_fn  # restored; validate_loop_break() and report() do not read it
    finish(m, original, ids, compute)


def finish(m, original, ids, compute):
    done = [e for e in journal() if e["kind"] == "batch"]
    order = [(e["first"], e["last"]) for e in done]
    if order != batches():
        stop(f"STOP 2: batches {order} do not cover 0..{N_CASES - 1} in order")
    results = [row for e in done for row in e["rows"]]
    if [identity(r) for r in results] != ids:
        stop("STOP 2: concatenated rows do not follow the original all_cases() order")
    kill_pinned_containers()
    t0 = time.time()
    validation = m.validate_loop_break()
    produced = m.report(results, validation)
    retained = json.loads((ROOT / RECEIPT).read_text())
    errors = compare(produced, retained)
    after = {k: budget.sha_file(k) for k in OWN_PINS}
    if after != OWN_PINS:
        errors.append(f"pinned file changed during P4b: {after}")
    budget.check_models()
    verdict = {"kind": "verdict", "time": now(), "result": "PASS" if not errors else "FAIL (STOP 2)",
               "rows": len(results), "excluded_rows": EXCLUDED, "excluded_key": "metrics.paper_screen",
               "differences": errors, "compute_s": round(compute + time.time() - t0, 1),
               "pins_after": after, "named_figures": named_figures(produced, retained)}
    append(verdict)
    print(json.dumps({k: verdict[k] for k in ("result", "rows", "differences", "compute_s")}, indent=1))
    if errors:
        raise SystemExit("STOP 2: P4b difference outside the Addendum A exclusion")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true")
    g.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    slice_run(resume=a.resume)


if __name__ == "__main__":
    main()
