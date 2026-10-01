"""Exact graph regression; no physical conductor or supplier admission."""
from fractions import Fraction as F
import unittest

from scripts.pcbgen.cut_current_witness import cut_current_witness, source_current_bound


def edge(identity, first, second, resistance):
    return {"id": identity, "from": first, "to": second,
            "resistance_ohm": resistance}


def solve_exact(edges, source=None, cut=None):
    """Independent small rational nodal solve, used only by this regression."""
    nodes = sorted({e[k] for e in edges for k in ("from", "to")})
    # Set the final node's gauge to zero and retain every other KCL equation.
    unknown = nodes[:-1]
    index = {node: i for i, node in enumerate(unknown)}
    n = len(unknown)
    a = [[F(0) for _ in range(n + 1)] for _ in range(n)]
    for e in edges:
        conductance = 1 / F(e["resistance_ohm"])
        endpoints = [(e["from"], 1), (e["to"], -1)]
        for first, sign1 in endpoints:
            if first in index:
                i = index[first]
                for second, sign2 in endpoints:
                    if second in index:
                        a[i][index[second]] += sign1 * sign2 * conductance
                a[i][-1] += sign1 * conductance * F((cut or {}).get(e["id"], 0))
    for node in unknown:
        a[index[node]][-1] += F((source or {}).get(node, 0))
    for column in range(n):
        pivot = next(i for i in range(column, n) if a[i][column])
        a[column], a[pivot] = a[pivot], a[column]
        divisor = a[column][column]
        a[column] = [value / divisor for value in a[column]]
        for row in range(n):
            if row != column:
                multiplier = a[row][column]
                a[row] = [x - multiplier * y for x, y in zip(a[row], a[column])]
    v = {node: a[index[node]][-1] for node in unknown}
    v[nodes[-1]] = F(0)
    if cut is None:
        currents = {e["id"]: (v[e["from"]] - v[e["to"]]) / F(e["resistance_ohm"])
                    for e in edges}
    else:
        currents = {e["id"]: (F(cut.get(e["id"], 0)) - v[e["from"]] + v[e["to"]])
                    / F(e["resistance_ohm"]) for e in edges}
    return v, currents


class CutCurrentWitnessTest(unittest.TestCase):
    def setUp(self):
        self.edges = [edge("candidate", "J", "K", 2),
                      edge("utility", "J", "P", 3), edge("main", "P", "K", 5)]
        self.cut = {"candidate": 1}
        self.source = {"J": F(2), "P": F(1), "K": F(-3)}
        self.source_trial = {"candidate": F(2), "utility": F(0), "main": F(1)}

    def test_exact_closed_network_reciprocity_with_remote_own_load(self):
        v, k = solve_exact(self.edges, cut=self.cut)
        _, actual = solve_exact(self.edges, source=self.source)
        proof = source_current_bound(self.edges, self.cut, v, k, self.source, self.source_trial)
        self.assertEqual(proof["gap_S"], 0)
        self.assertEqual(proof["center_A"], actual["candidate"])
        self.assertEqual(actual["candidate"], F(21, 10))
        self.assertEqual(proof["auxiliary_energy_upper_S"], F(1, 10))
        self.assertEqual(proof["gap_units"], "S")

    def test_inexact_witness_bounds_actual_current_without_solving_source(self):
        v = {"J": F(3, 4), "K": F(0), "P": F(1, 2)}
        k = {"candidate": F(1, 12), "utility": F(-1, 12), "main": F(-1, 12)}
        proof = source_current_bound(self.edges, self.cut, v, k, self.source, self.source_trial)
        _, actual = solve_exact(self.edges, source=self.source)
        self.assertGreater(proof["gap_S"], 0)
        self.assertLessEqual((actual["candidate"] - proof["center_A"]) ** 2,
                             proof["error_radius_squared_A2"])
        self.assertEqual(proof["auxiliary_energy_upper_S"] - proof["auxiliary_energy_lower_S"],
                         proof["gap_S"])

    def test_bridge_allows_zero_auxiliary_energy(self):
        edges = [edge("wire", "J", "K", "1/100")]
        proof = source_current_bound(edges, {"wire": 1}, {"J": 1, "K": 0},
                                     {"wire": 0}, {"J": "23/5", "K": "-23/5"},
                                     {"wire": "23/5"})
        self.assertEqual(proof["auxiliary_energy_upper_S"], 0)
        self.assertEqual(proof["gap_S"], 0)
        self.assertEqual(proof["center_A"], F(23, 5))

    def test_parallel_strands_are_all_counted_in_complete_cut(self):
        edges = [edge("strand1", "J", "K", 2), edge("strand2", "J", "K", 3),
                 edge("alternative", "J", "K", 5)]
        cut = {"strand1": 1, "strand2": 1}
        v, k = solve_exact(edges, cut=cut)
        source = {"J": 1, "K": -1}
        _, actual = solve_exact(edges, source=source)
        proof = source_current_bound(edges, cut, v, k, source,
                                     {"strand1": 1, "strand2": 0, "alternative": 0})
        self.assertEqual(proof["gap_S"], 0)
        self.assertEqual(proof["center_A"], actual["strand1"] + actual["strand2"])
        self.assertEqual(proof["center_A"], F(25, 31))

    def test_zero_net_local_source_does_not_vanish(self):
        # J and P can be two portions of one external support: their net is
        # zero, but the redistribution still drives current through the cut.
        source = {"J": 1, "P": -1, "K": 0}
        v, k = solve_exact(self.edges, cut=self.cut)
        proof = source_current_bound(self.edges, self.cut, v, k, source,
                                     {"candidate": 0, "utility": 1, "main": 0})
        self.assertEqual(proof["center_A"], F(3, 10))
        self.assertEqual(proof["error_radius_squared_A2"], 0)

    def test_orientation_and_gauge_change_preserve_bound(self):
        v, k = solve_exact(self.edges, cut=self.cut)
        original = source_current_bound(self.edges, self.cut, v, k, self.source, self.source_trial)
        flipped = source_current_bound(self.edges, {"candidate": -1},
                                       {n: 17 - x for n, x in v.items()},
                                       {e: -x for e, x in k.items()}, self.source, self.source_trial)
        self.assertEqual(flipped["center_A"], -original["center_A"])
        self.assertEqual(flipped["gap_S"], original["gap_S"])

    def test_negative_lower_is_valid_and_enclosed(self):
        v = {"J": 0, "K": 0, "P": 0}
        k = {"candidate": -1, "utility": 1, "main": 1}
        proof = cut_current_witness(self.edges, self.cut, v, k)
        self.assertLess(proof["auxiliary_energy_lower_S"], 0)
        self.assertEqual(proof["gap_S"], F(25, 2))

    def test_invalid_trials_fail_closed(self):
        v, k = solve_exact(self.edges, cut=self.cut)
        bad_k = dict(k, candidate=k["candidate"] + 1)
        with self.assertRaisesRegex(ValueError, "divergence"):
            cut_current_witness(self.edges, self.cut, v, bad_k)
        with self.assertRaisesRegex(ValueError, "every graph identity"):
            cut_current_witness(self.edges, self.cut, {"J": 0, "K": 0}, k)
        with self.assertRaisesRegex(ValueError, "exact"):
            cut_current_witness(self.edges, self.cut, dict(v, J=0.5), k)
        with self.assertRaisesRegex(ValueError, "balance globally"):
            source_current_bound(self.edges, self.cut, v, k,
                                 dict(self.source, K=0), self.source_trial)
        with self.assertRaisesRegex(ValueError, "exact source"):
            source_current_bound(self.edges, self.cut, v, k, self.source,
                                 dict(self.source_trial, main=0))
        with self.assertRaisesRegex(ValueError, "positive resistance"):
            cut_current_witness([edge("bad", "J", "K", 0)], {"bad": 1},
                                {"J": 0, "K": 0}, {"bad": 0})

    def test_composed_two_budget_support_encloses_signed_graph_scenarios(self):
        from scripts.pcbgen.observation_support_bound import support_bound

        exact_v, exact_k = solve_exact(self.edges, cut=self.cut)
        trials = [(exact_v, exact_k),
                  ({"J": F(3, 4), "K": F(0), "P": F(1, 2)},
                   {"candidate": F(1, 12), "utility": F(-1, 12), "main": F(-1, 12)})]
        for v, k in trials:
            witness = cut_current_witness(self.edges, self.cut, v, k)
            bound = support_bound(
                observation_kind="wire_current",
                energy_upper=witness["auxiliary_energy_upper_S"],
                energy_lower=witness["auxiliary_energy_lower_S"],
                source_ids=["J_to_K", "P_to_K"],
                sources=[{"id": "J_to_K", "trial_value": v["J"] - v["K"],
                          "source_energy_upper_ohm": 2},
                         {"id": "P_to_K", "trial_value": v["P"] - v["K"],
                          "source_energy_upper_ohm": 5}],
                # A single normalized zero-net redistribution mode on the
                # synthetic J/P support; this does not admit a continuum pad.
                redistribution_ids=["J_P_shape"],
                redistribution=[{"id": "J_P_shape",
                                 "trace_oscillation_upper": abs(v["J"] - v["P"]),
                                 "shape_energy_upper_ohm": 3}],
                source_budget_A=1, redistribution_budget_A=1)
            self.assertGreaterEqual(F(bound["observation_abs_upper"]), F(11, 10))
            for x in range(-2, 3):
                for y in range(-2, 3):
                    if abs(x) + abs(y) > 2:
                        continue
                    for redistribution in range(-2, 3):
                        source = {"J": F(x + redistribution, 2),
                                  "P": F(y - redistribution, 2), "K": F(-x - y, 2)}
                        _, actual = solve_exact(self.edges, source=source)
                        self.assertLessEqual(abs(actual["candidate"]),
                                             F(bound["observation_abs_upper"]))


if __name__ == "__main__":
    unittest.main()
