"""Mutation tests for the current OSC PCB checkpoint freshness guard."""
import copy
import json
import unittest
from scripts.checks import osc_pcb_checkpoint as guard


class OscPcbCheckpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint = json.loads(guard.CHECKPOINT.read_text())

    def mutant(self):
        return copy.deepcopy(self.checkpoint)

    def test_live_checkpoint_matches_boards_receipts_and_docs(self):
        guard.check(self.checkpoint)

    def test_board_hash_drift_is_rejected(self):
        changed = self.mutant()
        changed['boards']['osc-core']['board_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'board bytes'):
            guard.check(changed)

    def test_receipt_hash_drift_is_rejected(self):
        changed = self.mutant()
        changed['boards']['osc-jack-left']['receipt']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'receipt bytes'):
            guard.check(changed)

    def test_unadopted_receipt_is_rejected(self):
        changed = self.mutant()
        entry = changed['boards']['osc-jack-right']
        entry['receipt']['path'] = entry['receipt']['path'].replace('rrr-01', 'rrr-02')
        entry['receipt']['sha256'] = guard.sha(guard.ROOT / entry['receipt']['path'])
        with self.assertRaisesRegex(ValueError, 'not an adopted gate'):
            guard.check(changed)

    def test_connectivity_count_drift_is_rejected(self):
        for board_id, key in (('osc-core', 'open_edges'), ('osc-core', 'agnd_open_edges'),
                              ('osc-jack-left', 'agnd_open_edges'), ('osc-jack-right', 'open_nets')):
            with self.subTest(board=board_id, key=key):
                changed = self.mutant()
                changed['boards'][board_id]['connectivity'][key] += 1
                with self.assertRaises(ValueError):
                    guard.check(changed)

    def test_rail_drift_is_rejected(self):
        changed = self.mutant()
        changed['boards']['osc-core']['connectivity']['rail_open_edges']['+5V'] = 0
        with self.assertRaisesRegex(ValueError, 'rail_open_edges'):
            guard.check(changed)

    def test_stale_native_record_cannot_be_called_fresh(self):
        changed = self.mutant()
        changed['boards']['osc-core']['native_state_record']['fresh'] = True
        with self.assertRaisesRegex(ValueError, 'freshness flag'):
            guard.check(changed)

    def test_doc_without_current_hash_is_rejected(self):
        changed = self.mutant()
        changed['referenced_by']['doc/src/content/docs/verification/osc-pcb-core.mdx'].append('osc-jack-left')
        with self.assertRaisesRegex(ValueError, 'osc-pcb-core.mdx'):
            guard.check(changed)

    def test_candidate_is_not_recorded_as_adopted(self):
        self.assertIn('NOT ADOPTED', self.checkpoint['candidate']['status'])


if __name__ == '__main__':
    unittest.main()
