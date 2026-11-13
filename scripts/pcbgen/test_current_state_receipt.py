"""latest_receipt() for both stage-receipt shapes; reads JSON only, runs no KiCad."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from scripts.pcbgen import current_state

BOARD = 'a' * 64
OTHER = 'b' * 64


def top_level(candidate=BOARD, adopted=True):
    return {'adopted': adopted, 'candidate_board_sha256': candidate, 'stage': 'rrr-01',
            'open_edges_after': 184, 'open_by_net_after': {'AGND': 3, 'X1': 1}}


def final_gate(candidate=BOARD, adopted=True):
    return {'adopted': adopted, 'schema': 'osc3-k-pilot-1',
            'after': {'open_edges': 3363, 'agnd_open_edges': 22},
            'final_gate': {'adopted': adopted, 'candidate_board_sha256': candidate,
                           'stage': 'osc3-k-pilot', 'open_edges_after': 3363}}


class LatestReceipt(unittest.TestCase):
    def resolve(self, receipts):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'boards' / 'b' / 'reports' / 'grid-routing'
            folder.mkdir(parents=True)
            for name, body in receipts.items():
                (folder / name).write_text(json.dumps(body))
            with mock.patch.object(current_state, 'ROOT', root):
                found = current_state.latest_receipt('b', BOARD)
            if found:
                self.assertEqual(found['sha256'], hashlib.sha256((root / found['path']).read_bytes()).hexdigest())
            return found

    def test_top_level_receipt_is_unchanged(self):
        found = self.resolve({'rrr-01.json': top_level(), 'rrr-02.json': top_level(adopted=False)})
        self.assertEqual((found['path'], found['stage'], found['open_edges_after'], found['agnd_open_edges_after']),
                         ('boards/b/reports/grid-routing/rrr-01.json', 'rrr-01', 184, 3))

    def test_final_gate_receipt_is_recognised(self):
        found = self.resolve({'osc3-k-pilot.json': final_gate(), 'rail-links.json': top_level(candidate=OTHER)})
        self.assertEqual((found['path'], found['stage'], found['open_edges_after'], found['agnd_open_edges_after']),
                         ('boards/b/reports/grid-routing/osc3-k-pilot.json', 'osc3-k-pilot', 3363, 22))

    def test_final_gate_must_be_adopted_and_name_the_board(self):
        self.assertIsNone(self.resolve({'x.json': final_gate(adopted=False)}))
        self.assertIsNone(self.resolve({'x.json': final_gate(candidate=OTHER)}))
        unadopted_gate = final_gate()
        unadopted_gate['final_gate']['adopted'] = False
        self.assertIsNone(self.resolve({'x.json': unadopted_gate}))

    def test_final_gate_receipt_without_after_block_has_unknown_agnd(self):
        receipt = final_gate()
        del receipt['after']
        found = self.resolve({'osc3-wsl.json': receipt})
        self.assertEqual((found['open_edges_after'], found['agnd_open_edges_after']), (3363, None))

    def test_copper_files_and_ambiguity_are_ignored_or_refused(self):
        self.assertIsNone(self.resolve({'rrr-01-copper.json': top_level()}))
        self.assertIsNone(self.resolve({'rrr-01.json': top_level(), 'osc3-k-pilot.json': final_gate()}))

    def test_current_boards_resolve_to_their_accepted_receipts(self):
        expected = {'osc-core': ('osc3-wsl-20261109a.json', 2226, None), 'osc-jack-left': ('rrr-01.json', 184, 3),
                    'osc-jack-right': ('rrr-01.json', 192, 8)}
        for board_id, (name, edges, agnd) in expected.items():
            with self.subTest(board=board_id):
                board = current_state.ROOT / 'boards' / board_id / f'{board_id}.kicad_pcb'
                found = current_state.latest_receipt(board_id, current_state.sha(board))
                self.assertEqual((Path(found['path']).name, found['open_edges_after'], found['agnd_open_edges_after']),
                                 (name, edges, agnd))


if __name__ == '__main__':
    unittest.main()
