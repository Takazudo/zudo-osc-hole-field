"""Mutation tests for the current OSC PCB checkpoint freshness guard."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
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

    def test_adoption_record_must_match_and_bind_the_board(self):
        changed = self.mutant()
        changed['boards']['osc-core']['adoption']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'adoption record bytes'):
            guard.check(changed)
        with tempfile.TemporaryDirectory() as temp:
            root = self.forged_root(temp)
            entry = self.checkpoint['boards']['osc-core']
            path = root / entry['adoption']['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            record = json.loads((guard.ROOT / entry['adoption']['path']).read_text())
            record['chain_receipt']['sha256'] = '0' * 64
            path.write_text(json.dumps(record))
            changed = self.mutant()
            changed['boards']['osc-core']['adoption']['sha256'] = guard.sha(path)
            with self.assertRaisesRegex(ValueError, 'does not bind the checkpoint receipt'):
                guard.check(changed, root)

    def test_agnd_islands_drift_is_rejected(self):
        changed = self.mutant()
        changed['boards']['osc-core']['connectivity']['agnd_islands'] = 22
        with self.assertRaisesRegex(ValueError, 'agnd_islands'):
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

    def forged_root(self, temp):
        """Copy every file the guard reads into a scratch root."""
        root = Path(temp)
        paths = set(self.checkpoint['referenced_by'])
        for entry in self.checkpoint['boards'].values():
            paths |= {entry['board'], entry['receipt']['path'], entry['native_state_record']['path']}
            if entry['receipt'].get('mirror'):
                paths.add(entry['receipt']['mirror'])
            if 'adoption' in entry:
                paths.add(entry['adoption']['path'])
        for path in paths:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(guard.ROOT / path, root / path)
        return root

    def refresh(self, root, board_id, checked_at='2026-11-08T00:00:00Z', **overrides):
        """Rewrite one routing.json as a refresh would and mark it fresh; overrides forge single fields."""
        changed = self.mutant()
        entry = changed['boards'][board_id]
        conn = entry['connectivity']
        record_path = root / entry['native_state_record']['path']
        record = json.loads(record_path.read_text())
        record['source']['input_board_sha256'] = entry['board_sha256']
        record['checked_at_utc'] = checked_at
        record['native'].update(open_edges=conn['open_edges'], rail_open_edges=conn['rail_open_edges'],
                                agnd_open_edges=conn['agnd_open_edges'],
                                other_signal_open_edges=conn['signal_open_edges'])
        if 'agnd_islands' in conn:
            record['native']['agnd_islands'] = conn['agnd_islands']
        receipt_path = entry['receipt'].get('mirror') or entry['receipt']['path']
        record['latest_adopted_receipt'] = {'path': receipt_path, 'sha256': entry['receipt']['sha256']}
        for key, value in overrides.items():
            if key in record['native']:
                record['native'][key] = value
            else:
                record['latest_adopted_receipt'][key] = value
        record_path.write_text(json.dumps(record))
        entry['native_state_record'].update(input_board_sha256=entry['board_sha256'],
                                            checked_at_utc=checked_at, fresh=True)
        return changed

    def test_forged_refresh_of_only_the_board_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.forged_root(temp)
            guard.check(self.checkpoint, root)
            changed = self.mutant()
            entry = changed['boards']['osc-core']
            record_path = root / entry['native_state_record']['path']
            record = json.loads(record_path.read_text())
            record['source']['input_board_sha256'] = entry['board_sha256']
            record_path.write_text(json.dumps(record))
            entry['native_state_record'].update(input_board_sha256=entry['board_sha256'], fresh=True)
            with self.assertRaisesRegex(ValueError, 'fresh native record'):
                guard.check(changed, root)

    def test_deeper_multi_field_forgeries_are_rejected(self):
        old = self.checkpoint['boards']['osc-core']['native_state_record']['superseded_checked_at_utc']
        cases = {
            'old timestamp': ({'checked_at': old}, 'not newer'),
            'AGND islands': ({'agnd_islands': 22}, 'agnd_islands'),
            'receipt path': ({'path': 'boards/osc-core/reports/grid-routing/rail-links.json'}, 'accepted receipt'),
            'receipt hash': ({'sha256': '0' * 64}, 'accepted receipt'),
            'signal count': ({'other_signal_open_edges': 3325}, 'other_signal_open_edges'),
        }
        for name, (overrides, message) in cases.items():
            with self.subTest(forgery=name), tempfile.TemporaryDirectory() as temp:
                root = self.forged_root(temp)
                with self.assertRaisesRegex(ValueError, message):
                    guard.check(self.refresh(root, 'osc-core', **overrides), root)

    def test_genuine_fresh_records_are_accepted(self):
        for board_id in self.checkpoint['boards']:
            with self.subTest(board=board_id), tempfile.TemporaryDirectory() as temp:
                root = self.forged_root(temp)
                guard.check(self.refresh(root, board_id), root)

    def test_doc_without_current_hash_is_rejected(self):
        changed = self.mutant()
        changed['referenced_by']['doc/src/content/docs/verification/osc-pcb-core.mdx'].append('osc-jack-left')
        with self.assertRaisesRegex(ValueError, 'osc-pcb-core.mdx'):
            guard.check(changed)

    def test_candidate_status_matches_the_adoption_record(self):
        # An adopted candidate must be the one whose adoption record names the current K board.
        status = self.checkpoint['candidate']['status']
        entry = self.checkpoint['boards']['osc-core']
        record = json.loads((guard.ROOT / entry['adoption']['path']).read_text())
        self.assertIn(f"{record['label']} ADOPTED", status)
        self.assertEqual(record['candidate_board_sha256'], entry['board_sha256'])


if __name__ == '__main__':
    unittest.main()
