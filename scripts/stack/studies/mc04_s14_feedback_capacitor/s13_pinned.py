"""MC04-S14: the pinned S13 modules, imported read-only in a process of their own.

The S14 copies carry the same module names (cells, runner, budget, guard), so the pinned S13 files are loaded here,
in a separate interpreter, with no bytecode written into the S13 directory. Requests arrive as a JSON list on stdin;
answers go to stdout as a JSON list. Nothing here runs a deck or writes into the S13 study or its cache.

    {"op": "texts", "point": p, "deck": "loop"|"closed", "nodeset": [...]}   -> [[name, text], ...]
    {"op": "seed_netlist", "point": p, "kind": "loop"|"closed"}               -> text
    {"op": "closed_metrics", "point": p, "tables": {suffix: path}}            -> S13 closed-loop metrics
    {"op": "loop_metrics", "point": p, "tables": {suffix: path}}              -> S13 loop metrics
    {"op": "plan", "point": p}                                                -> S13 stimulus record of the point
"""
import gzip
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
S13 = Path(__file__).resolve().parents[1] / "mc04_s13_node_cap_budget"
ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(S13), str(ROOT)]

import budget  # noqa: E402  (the pinned S13 file)
import cells  # noqa: E402
import runner  # noqa: E402

assert Path(budget.__file__).resolve().parent == S13 and Path(runner.__file__).resolve().parent == S13

_TOPO = {}


def topo(key):
    if not _TOPO:
        _TOPO.update(budget.topologies()[1])
    return _TOPO[key]


def load(path):
    """The pinned read_table() on a data file; a .gz file is decompressed to a temporary file first."""
    p = Path(path)
    if p.suffix != ".gz":
        return runner.read_table(p)
    with tempfile.TemporaryDirectory() as d:
        q = Path(d) / p.name[:-3]
        q.write_bytes(gzip.decompress(p.read_bytes()))
        return runner.read_table(q)


def answer(req):
    op, p = req["op"], req.get("point")
    t = topo(p["topology"]) if p else None
    if op == "texts":
        ns = req.get("nodeset", [])
        if req["deck"] == "loop":
            return [[n, x] for n, x, _, _ in budget.loop_texts(t, p, ns)]
        return [[n, x] for n, x, _, _ in budget.closed_texts(t, p, ns)]
    if op == "seed_netlist":
        return budget.seed_netlist(t, p, req["kind"])
    if op == "closed_metrics":
        c = t["circuit"]
        _, _, P = cells.closed_text(c, p["corner"], budget.build_lines(t, p, loop=False))
        tables = {k: load(v) for k, v in req["tables"].items()}
        return runner.closed_metrics(c, p["corner"], P, tables)
    if op == "loop_metrics":
        c = t["circuit"]
        _, vv, vi = runner.loop_text(cells.loop_lines(c, p["corner"], budget.build_lines(t, p, loop=True)),
                                     x="xinm", y=budget.loop_y(c))
        tables = {k: load(v) for k, v in req["tables"].items()}
        return runner.loop_metrics(tables["v"], tables["i"], vv, vi)
    if op == "plan":
        c = t["circuit"]
        _, _, P = cells.closed_text(c, p["corner"], budget.build_lines(t, p, loop=False))
        return budget.stimulus_record(c, P)
    raise ValueError(op)


def main():
    reqs = json.loads(sys.stdin.read())
    out = []
    for q in reqs:
        try:
            out.append({"ok": True, "value": answer(q)})
        except Exception as e:  # reported per request; the caller decides
            out.append({"ok": False, "error": f"{type(e).__name__}: {e}"})
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
