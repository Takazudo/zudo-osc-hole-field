"""MC04-S7: pin-to-pin warning parity when a master warning's two pins now sit on different boards."""
import json
import unittest

from scripts.schgen.check_board_erc import projected_identities

ident = lambda w: json.dumps({k: w[k] for k in ('type', 'description', 'items')}, sort_keys=True)  # noqa: E731
DESC = 'Pins of type Unspecified and Passive are connected'
LED = 'Symbol D601 Pin 2 [A, Unspecified, Line]'
DIODE = 'Symbol D2125 Pin 1 [K, Passive, Line]'
HEADER = 'Symbol J900001 Pin 7 [7, Passive, Line]'
SAME = {'type': 'pin_to_pin', 'description': DESC, 'items': ['Symbol D701 Pin 1 [K, Unspecified, Line]', 'Symbol D2201 Pin 2 [A, Passive, Line]']}
BOARDS = {'D601': 'JL', 'D2125': 'K', 'D701': 'JL', 'D2201': 'JL'}


def w(*items):
    return {'type': 'pin_to_pin', 'description': DESC, 'items': sorted(items)}


class Projection(unittest.TestCase):
    def check(self, projected, baseline):
        a, e, _ = projected_identities(projected, baseline, BOARDS, ident)
        return a == e

    def test_split_warning_projects_to_a_header_pin(self):
        self.assertTrue(self.check([w(LED, HEADER), SAME], [w(LED, DIODE), SAME]))

    def test_split_warning_with_another_panel_pin_fails(self):
        self.assertFalse(self.check([w('Symbol D602 Pin 2 [A, Unspecified, Line]', HEADER), SAME], [w(LED, DIODE), SAME]))

    def test_same_board_warning_must_match_exactly(self):
        moved = dict(SAME, items=['Symbol D701 Pin 1 [K, Unspecified, Line]', HEADER])
        self.assertFalse(self.check([w(LED, HEADER), moved], [w(LED, DIODE), SAME]))

    def test_a_missing_warning_fails(self):
        self.assertFalse(self.check([SAME], [w(LED, DIODE), SAME]))


if __name__ == '__main__':
    unittest.main()
