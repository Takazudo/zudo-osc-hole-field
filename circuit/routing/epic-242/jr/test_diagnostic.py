"""Reject unsafe JR inputs before any native work or canonical mutation."""
import argparse
import copy
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import prepare_diagnostic as diagnostic


class DiagnosticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ARCHIVE) as z:
            cls.dump = json.loads(z.read(diagnostic.PREFIX + 'dump.json'))
        cls.endpoints = diagnostic.read(diagnostic.BASELINE / 'jr-endpoints.json')

    def test_complete_retained_groups_reproduce_accepted_counts(self):
        pads = diagnostic.validate_dump(self.dump, self.endpoints)
        self.assertEqual(len(pads), 3655)
        self.assertEqual(sum(len(g)-1 for n, g in self.dump['islands'].items() if n != 'AGND'), 107)
        self.assertEqual(len(self.dump['islands']['AGND'])-1, 22)

    def test_stale_stacked_jr130_dump_rejected(self):
        damaged = {**self.dump, 'board_sha256': 'e06b7471ddc8f5c8c498c5eb5bf8655cc6de539e92826a5701cf1de06356e136'}
        with self.assertRaisesRegex(ValueError, 'different board'):
            diagnostic.validate_dump(damaged, self.endpoints)

    def test_same_count_wrong_group_membership_rejected(self):
        damaged = copy.deepcopy(self.dump)
        groups = damaged['islands']['AGND']
        groups[0][0], groups[1][0] = groups[1][0], groups[0][0]
        with self.assertRaisesRegex(ValueError, 'membership differs'):
            diagnostic.validate_dump(damaged, self.endpoints)

    def test_endpoint_pose_drift_rejected(self):
        damaged = copy.deepcopy(self.dump)
        next(p for p in damaged['pads'] if p['uuid'] == diagnostic.SOURCE_PAD)['xy'][0] += 1
        with self.assertRaisesRegex(ValueError, 'pose changed'):
            diagnostic.validate_dump(damaged, self.endpoints)

    def test_all_four_cut_boundaries_include_retained_pad_contact(self):
        cuts, anchors = diagnostic.boundary_contract(self.dump)
        self.assertEqual(len(cuts), 2)
        self.assertEqual(len(anchors), 4)
        self.assertIn('7f250bad-9979-5611-8ea6-fa595712bb10', anchors[2]['retained_touching_uuids'])
        self.assertTrue(all(a['retained_touching_uuids'] for a in anchors))

    def test_missing_or_duplicate_cut_rejected(self):
        for duplicate in (False, True):
            damaged = copy.deepcopy(self.dump)
            cut = next(t for t in damaged['tracks'] if t['uuid'] == diagnostic.CUTS[0])
            if duplicate:
                damaged['tracks'].append(copy.deepcopy(cut))
            else:
                damaged['tracks'].remove(cut)
            with self.assertRaisesRegex(ValueError, 'missing, duplicate'):
                diagnostic.boundary_contract(damaged)

    def test_execution_without_parent_slot_cannot_reach_native(self):
        result = subprocess.run([sys.executable, str(diagnostic.HERE / 'native_diagnostic.py'),
                                 str(ARCHIVE), '--label', '251-test', '--execute'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('requires the parent-issued', result.stderr)

    def test_archive_damage_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'damaged.zip'
            archive.write_bytes(b'not a complete archive')
            with self.assertRaisesRegex(ValueError, 'archive size/digest mismatch'):
                diagnostic.prepare(archive, Path(tmp) / 'output')

    def test_replay_deterministic_and_ineligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            plan = diagnostic.prepare(ARCHIVE, out)
            first = {p.name: p.read_bytes() for p in out.iterdir()}
            diagnostic.prepare(ARCHIVE, out)
            self.assertEqual(first, {p.name: p.read_bytes() for p in out.iterdir()})
            self.assertFalse(plan['adopted'])
            self.assertEqual(plan['native_acceptance'], 'NOT RUN')
            proposal = diagnostic.read(out / 'cut-proposal.json')
            self.assertEqual(proposal['copper'], [])
            self.assertEqual(proposal['board_sha256'], self.dump['board_sha256'])
            self.assertEqual(sum(c['open_edges'] for c in diagnostic.read(out / 'cases.json')['cases']), 129)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    ARCHIVE = args.archive.resolve()
    unittest.main(argv=[sys.argv[0]], verbosity=2)
