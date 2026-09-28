"""Injected partition faults must fail before native output is trusted."""
from copy import deepcopy
import unittest
from scripts.schgen.project_boards import load_partition
from scripts.schgen.verify_cross_board import assert_partition, verify


class FaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load_partition()
        cls.assignment = {x['ref']: x for x in cls.base['assignment']['components']}

    def test_swapped_mate_pin(self):
        p = deepcopy(self.base)
        mate = next(c for c in p['connectors'] if c['id'] == p['harnesses'][0]['header_ids'][1])
        mate['pin_map']['1'], mate['pin_map']['3'] = mate['pin_map']['3'], mate['pin_map']['1']
        with self.assertRaisesRegex(ValueError, 'swapped/mismatched'):
            assert_partition(p, self.assignment)

    def test_duplicate_component(self):
        p = deepcopy(self.base)
        p['assignment']['components'].append(deepcopy(p['assignment']['components'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate component assignment'):
            verify(p, {}, '')

    def test_sensitive_connector(self):
        p = deepcopy(self.base)
        
        for c in p['connectors'][:2]: c['pin_map']['1'] = '/H1/SLEW_STORAGE'
        with self.assertRaisesRegex(ValueError, 'Sensitive net'):
            assert_partition(p, self.assignment)

    def test_split_island(self):
        p = deepcopy(self.base)
        assignment = {x['ref']: x for x in p['assignment']['components']}
        assignment['C7101']['board'] = 'J'
        with self.assertRaisesRegex(ValueError, 'split island'):
            assert_partition(p, assignment)


if __name__ == '__main__': unittest.main()
