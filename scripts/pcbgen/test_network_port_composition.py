import copy
import json
import unittest
from pathlib import Path
import numpy as np
from scripts.pcbgen.network_port_composition import compose, cycle_coordinates


class NetworkPortCompositionTests(unittest.TestCase):
    def setUp(self):
        self.contacts = {'J0': 'J', 'J1': 'J', 'K0': 'K', 'K1': 'K', 'P0': 'P', 'P1': 'P'}
        self.operators = {
            board: {'reference': board+'0', 'ports': [board+'1'], 'energy': [[value]]}
            for board, value in [('J', 2.), ('K', 3.), ('P', 4.)]}
        self.wires = [
            {'id': 'J-K-main', 'from_contact': 'J0', 'to_contact': 'K0', 'resistance': 5.},
            {'id': 'J-P-utility', 'from_contact': 'J1', 'to_contact': 'P1', 'resistance': 6.},
            {'id': 'P-K-main', 'from_contact': 'P0', 'to_contact': 'K1', 'resistance': 7.}]
        # Real utility measurement is J1 minus P1. K0 explicitly balances
        # the J and P load columns; the numerical gauge injects no current.
        self.sources = {'J0': [0, 0, 0], 'J1': [1, 1, 0], 'K0': [-1, 0, -1],
                        'K1': [0, 0, 0], 'P0': [0, 0, 0], 'P1': [0, -1, 1]}

    def direct(self, wires):
        contacts = list(self.contacts)
        index = {name: i for i, name in enumerate(contacts)}
        laplacian = np.zeros((6, 6))
        edges = [(b+'0', b+'1', self.operators[b]['energy'][0][0]) for b in ('J', 'K', 'P')]
        edges += [(w['from_contact'], w['to_contact'], w['resistance']) for w in wires]
        for a, b, resistance in edges:
            vector = np.zeros(6)
            vector[index[a]], vector[index[b]] = 1, -1
            laplacian += np.outer(vector, vector)/resistance
        rows = [i for i, name in enumerate(contacts) if name != 'K0']
        source = np.asarray([self.sources[name] for name in contacts], dtype=float)[rows]
        return source.T @ np.linalg.solve(laplacian[np.ix_(rows, rows)], source)

    def test_three_board_utility_and_own_loads_match_full_resistor_network(self):
        for wires in (self.wires, [self.wires[0], self.wires[2]]):
            result = compose(self.operators, self.contacts, wires, self.sources)
            np.testing.assert_allclose(result['energy'], self.direct(wires), rtol=2e-14, atol=2e-14)
            self.assertLess(result['floating_board_KCL_residual'], 1e-14)
        # Removing only the physical candidate wire retains both actual PCB
        # endpoints and P's paid copper, rather than replacing P with K.
        opened = compose(self.operators, self.contacts, [self.wires[0], self.wires[2]], self.sources)
        self.assertAlmostEqual(opened['energy'][1, 1], 21.)

    def test_no_missing_board_contact_or_implicit_balancing_boundary(self):
        operators = copy.deepcopy(self.operators)
        del operators['P']
        with self.assertRaisesRegex(ValueError, 'explicit operator'):
            compose(operators, self.contacts, self.wires, self.sources)
        contacts = {**self.contacts, 'P-own-load': 'P'}
        sources = {**self.sources, 'P-own-load': [0, 0, 0]}
        with self.assertRaisesRegex(ValueError, 'every declared contact'):
            compose(self.operators, contacts, self.wires, sources)
        sources = copy.deepcopy(self.sources)
        sources['K0'][0] = 0
        with self.assertRaisesRegex(ValueError, 'balance explicitly'):
            compose(self.operators, self.contacts, self.wires, sources)

    def test_indefinite_internal_energy_and_disconnected_rest_rejected(self):
        operators = copy.deepcopy(self.operators)
        operators['J']['energy'] = [[-100.]]
        with self.assertRaisesRegex(ValueError, 'positive definite'):
            compose(operators, self.contacts, self.wires, self.sources)
        with self.assertRaisesRegex(ValueError, 'disconnected'):
            compose(self.operators, self.contacts, [self.wires[0]], self.sources)

    def test_constituent_energy_order_preserved_by_constrained_minimum(self):
        actual = compose(self.operators, self.contacts, self.wires, self.sources)['energy']
        results = []
        for factor in (.7, 1.3):
            operators = copy.deepcopy(self.operators)
            wires = copy.deepcopy(self.wires)
            for row in operators.values():
                row['energy'] = np.asarray(row['energy'])*factor
            for row in wires:
                row['resistance'] *= factor
            results.append(compose(operators, self.contacts, wires, self.sources)['energy'])
        self.assertGreaterEqual(np.linalg.eigvalsh(actual-results[0]).min(), -1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(results[1]-actual).min(), -1e-12)
        # No conclusion about individual wire-current ordering is drawn.

    def test_full_source_graph_exact_cycle_basis_retains_four_P_utilities(self):
        graph = json.loads(Path('design/partition/ground-network-incidence.json').read_text())
        boards = {row['id']: row['board'] for row in graph['contacts']}
        endpoints = [(boards[row['from_contact']], boards[row['to_contact']]) for row in graph['wire_edges']]
        names = tuple(sorted(set(boards.values())))
        incidence, right, cycles = cycle_coordinates(names, endpoints)
        self.assertEqual(incidence.shape, (10, 389))
        self.assertEqual(cycles.shape, (389, 380))
        self.assertFalse(np.any(incidence @ cycles))
        utility = [i for i, (a, b) in enumerate(endpoints) if {a, b} == {'JL', 'P'}]
        self.assertEqual(len(utility), 4)
        for edge in utility:
            _, _, opened = cycle_coordinates(names, endpoints[:edge]+endpoints[edge+1:])
            self.assertEqual(opened.shape, (388, 379))


if __name__ == '__main__':
    unittest.main()
