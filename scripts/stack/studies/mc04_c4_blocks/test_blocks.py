import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('blocks', Path(__file__).with_name('blocks.py'))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

UNRESOLVED = [{'board': 'JL', 'ref': 'U1'}, {'board': 'JL', 'ref': 'U2'}, {'board': 'K', 'ref': 'U3'}]


class Assignment(unittest.TestCase):
    def test_parse_move(self):
        self.assertEqual(b.parse_move('JL:K:U1417,U2218:_PROTECTED,ISO_MID'),
                         ('JL', 'K', ('U1417', 'U2218'), ('_PROTECTED', 'ISO_MID')))
        self.assertEqual(b.parse_move('JR:K:U4347'), ('JR', 'K', ('U4347',), ()))
        for bad in ('JL:K', 'JL::U1', 'a:b:c:d:e'):
            with self.assertRaises(ValueError):
                b.parse_move(bad)

    def test_parse_local(self):
        self.assertEqual(b.parse_local('JL:U1318,U2217'), ('JL', ('U1318', 'U2217')))
        with self.assertRaises(ValueError):
            b.parse_local('JL')

    def test_complete_assignment_passes(self):
        b.check_assignment(UNRESOLVED, [('JL', 'K', ('U1',), ()), ('K', 'K', ('U3',), ())], [('JL', ('U2',))])

    def test_unassigned_ic_is_refused(self):
        with self.assertRaisesRegex(ValueError, "unassigned \\[\\('K', 'U3'\\)\\]"):
            b.check_assignment(UNRESOLVED, [('JL', 'K', ('U1',), ())], [('JL', ('U2',))])

    def test_resolved_or_wrong_board_ic_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'not unresolved'):
            b.check_assignment(UNRESOLVED, [('JL', 'K', ('U1', 'U9'), ()), ('K', 'K', ('U3',), ())], [('JL', ('U2',))])
        with self.assertRaisesRegex(ValueError, 'not unresolved'):
            b.check_assignment(UNRESOLVED, [('JR', 'K', ('U1',), ()), ('K', 'K', ('U3',), ())], [('JL', ('U2',))])

    def test_duplicate_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            b.check_assignment(UNRESOLVED, [('JL', 'K', ('U1', 'U2'), ()), ('K', 'K', ('U3',), ())], [('JL', ('U2',))])


class Turn(unittest.TestCase):
    FP = {'origin': [10.0, 20.0], 'courtyard': [8.0, 19.0, 12.0, 21.0],
          'pads': [{'bbox': [8.5, 19.5, 9.0, 20.5]}]}

    def test_four_turns_are_identity(self):
        self.assertEqual(b.turned(self.FP, 4)['courtyard'], self.FP['courtyard'])
        self.assertEqual(b.turned(self.FP, 4)['pads'][0]['bbox'], self.FP['pads'][0]['bbox'])

    def test_one_turn_swaps_the_box(self):
        t = b.turned(self.FP, 1)
        self.assertEqual(t['courtyard'], [9.0, 18.0, 11.0, 22.0])
        self.assertEqual(self.FP['courtyard'], [8.0, 19.0, 12.0, 21.0])  # the source is not changed


if __name__ == '__main__':
    unittest.main()
