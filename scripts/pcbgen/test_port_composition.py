"""Finite K copper and both endpoints are retained in joined port energies."""
import unittest
import numpy as np
from scripts.pcbgen.port_composition import joined_energy, open_candidate_current


class PortCompositionTests(unittest.TestCase):
    def setUp(self):
        self.j = np.array([[1., 1.], [1., 3.]])
        self.k = np.array([[3., 3.], [3., 7.]])
        self.sj = np.eye(2)
        # Second functional measures J's candidate against its actual K endpoint.
        self.sk = np.array([[0., 0.], [0., -1.]])

    def direct(self, candidate_present):
        # J-reference, J-load, J-GH, K-main, K-GH; K source is ground (-1).
        laplacian = np.zeros((5, 5))
        edges = [(0, 1, 1.), (1, 2, 2.), (3, -1, 3.), (3, 4, 4.), (0, 3, 5.)]
        if candidate_present: edges.append((2, 4, 6.))
        for first, second, resistance in edges:
            vector = np.zeros(5); vector[first] = 1.
            if second >= 0: vector[second] = -1.
            laplacian += np.outer(vector, vector) / resistance
        sources = np.zeros((5, 2)); sources[1, 0] = 1.
        sources[2, 1] = 1.; sources[4, 1] = -1.
        return sources.T @ np.linalg.solve(laplacian, sources)

    def test_matches_explicit_two_board_resistor_network(self):
        for connected in (False, True):
            result = joined_energy(self.j, self.k, self.sj, self.sk,
                [-1, 1] if connected else [-1], [0, 1] if connected else [0],
                [5., 6.] if connected else [5.])
            np.testing.assert_allclose(result['energy'], self.direct(connected), rtol=1e-13, atol=1e-13)
            if connected: self.assertAlmostEqual(result['wire_current_map'][1, 0], 1/3)

    def test_open_candidate_does_not_credit_its_PCB_or_contact(self):
        result = joined_energy(self.j, self.k, self.sj, self.sk, [-1], [0], [5.])
        bound = open_candidate_current(result['energy'], result['energy'], 1, [0], 1., 6.)
        self.assertAlmostEqual(bound['open_voltage_upper_V'], 6.)
        self.assertAlmostEqual(bound['candidate_current_upper_A'], 1.)
        self.assertEqual(bound['candidate_added_PCB_contact_ohm'], 0.)

    def test_constituent_loewner_envelopes_survive_minimization(self):
        actual = joined_energy(self.j, self.k, self.sj, self.sk, [-1, 1], [0, 1], [5., 6.])['energy']
        upper = joined_energy(self.j + np.eye(2), self.k + 2*np.eye(2), self.sj, self.sk, [-1, 1], [0, 1], [6., 8.])['energy']
        lower = joined_energy(.5*self.j, .7*self.k, self.sj, self.sk, [-1, 1], [0, 1], [4., 5.])['energy']
        self.assertGreaterEqual(np.linalg.eigvalsh(upper-actual).min(), -1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(actual-lower).min(), -1e-12)

    def test_indefinite_internal_stationary_maximum_is_rejected(self):
        actual = joined_energy([[1.]], [[1.]], [[1.]], [[0.]], [-1, 0], [-1, 0], [1., 1.])
        self.assertAlmostEqual(actual['energy'][0, 0], 1.)
        # -10 is a valid scalar lower bound for 1. Its internal block is -7,
        # however: the former stationary value 18/7 exceeded the actual 1.
        with self.assertRaisesRegex(ValueError, 'not positive definite'):
            joined_energy([[-10.]], [[1.]], [[1.]], [[0.]], [-1, 0], [-1, 0], [1., 1.])


if __name__ == '__main__': unittest.main()
