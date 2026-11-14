"""Extraction tests for the instrument preview.

    python3 -m unittest project/osc-hole-field/instrument-preview/test_extract.py

The fixed-hardware coincidence test is the proof of the KiCad-to-panel transform: every
footprint carrying a PanelUid must land on its locked centre after the per-board offset,
with no mirroring, and every one of the 438 locked centres must be claimed exactly once.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIEW = json.loads((HERE / 'view-data.json').read_text())
COL = {k: i for i, k in enumerate(VIEW['part_columns'])}
LOCK = json.loads((ROOT / 'design/grid/placements.lock.json').read_text())['placements']
LOCK_BY_UID = {q['uid']: q for q in LOCK}
BOARDS = {b['id']: b for b in VIEW['boards']}
TOL = 0.01  # mm


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


class InputsAndCounts(unittest.TestCase):
    def test_recorded_input_hashes_are_current(self):
        stale = [p for p, v in VIEW['inputs'].items() if sha256(ROOT / p) != v['sha256']]
        self.assertEqual(stale, [], 'view-data.json is stale; run extract.py')

    def test_ten_current_boards_and_exclusions(self):
        self.assertEqual(len(VIEW['boards']), 10)
        self.assertEqual(BOARDS['osc-control']['file'], 'boards/osc-control/osc-control-routed-draft.kicad_pcb')
        files = {b['file'] for b in VIEW['boards']}
        for excluded in VIEW['excluded']:
            self.assertNotIn(excluded, files)
        readiness = json.loads((ROOT / 'design/reports/instrument-readiness.json').read_text())
        self.assertEqual({u['board'] for u in readiness['units']}, files)
        self.assertEqual(set(readiness['excluded_board_files']), set(VIEW['excluded']))

    def test_footprint_counts_equal_source_files(self):
        for b in VIEW['boards']:
            with self.subTest(board=b['id']):
                n = len(re.findall(rb'\n\t\(footprint ', (ROOT / b['file']).read_bytes()))
                self.assertEqual(len(b['parts']), n)
                self.assertEqual(b['counts']['footprint'], n)
        n = len(re.findall(rb'\n\t\(footprint ', (ROOT / VIEW['panel']['file']).read_bytes()))
        self.assertEqual(VIEW['panel']['footprints'], n)
        self.assertEqual(n, 438)

    def test_segment_and_via_counts_equal_source_files(self):
        for b in VIEW['boards']:
            with self.subTest(board=b['id']):
                raw = (ROOT / b['file']).read_bytes()
                self.assertEqual(b['counts']['segment'], len(re.findall(rb'\n\t\(segment\n', raw)))
                self.assertEqual(b['counts']['via'], len(re.findall(rb'\n\t\(via\n', raw)))

    def test_board_hashes_match_status_records(self):
        cp = json.loads((ROOT / 'circuit/routing/osc-pcb-current-checkpoint.json').read_text())
        for bid, rec in cp['boards'].items():
            with self.subTest(board=bid):
                self.assertEqual(BOARDS[bid]['sha256'], rec['metadata_successor']['successor_board_sha256'])
                self.assertEqual(BOARDS[bid]['status']['open_edges'], rec['connectivity']['open_edges'])
                self.assertEqual(BOARDS[bid]['label'], rec['metadata_successor']['label'])
        for b in VIEW['boards']:
            with self.subTest(board=b['id'], record='readiness'):
                self.assertEqual(b['sha256'], b['status']['readiness_board_sha256'])


class PanelFrame(unittest.TestCase):
    def test_438_locked_centres(self):
        self.assertEqual(len(LOCK), 438)
        self.assertEqual(len(VIEW['lock']), 438)
        self.assertEqual(len({q['uid'] for q in VIEW['lock']}), 438)

    def test_panel_board_features_coincide_with_lock(self):
        feats = VIEW['panel']['features']
        self.assertEqual(len(feats), 438)
        self.assertEqual(sorted(f[4] for f in feats), sorted(LOCK_BY_UID))
        for ref, x, y, _, uid in feats:
            q = LOCK_BY_UID[uid]
            self.assertLessEqual(max(abs(x - q['x_mm']), abs(y - q['y_mm'])), TOL, ref)

    def test_fixed_hardware_footprints_coincide_with_locked_centres(self):
        claimed = {}
        for b in VIEW['boards']:
            for p in b['parts']:
                uid = p[COL['panel_uid']]
                if not uid:
                    continue
                self.assertIn(uid, LOCK_BY_UID, f'{b["key"]} {p[COL["ref"]]}')
                self.assertNotIn(uid, claimed, f'{uid} claimed twice')
                claimed[uid] = b['key']
                q = LOCK_BY_UID[uid]
                with self.subTest(board=b['key'], ref=p[COL['ref']]):
                    self.assertLessEqual(abs(p[COL['x']] - q['x_mm']), TOL)
                    self.assertLessEqual(abs(p[COL['y']] - q['y_mm']), TOL)
                    self.assertEqual((p[COL['rot']] - (q['rot_deg'] or 0)) % 360, 0)
        self.assertEqual(set(claimed), set(LOCK_BY_UID))
        by_board = {}
        for uid, key in claimed.items():
            by_board.setdefault(key, []).append(LOCK_BY_UID[uid]['kind'])
        # every jack is on JL/JR and every pot, toggle and button on P
        self.assertEqual(sorted(k for k, v in by_board.items() if 'jack' in v), ['JL', 'JR'])
        self.assertEqual(by_board['JL'].count('jack') + by_board['JR'].count('jack'), 180)
        for kind, n in (('pot', 101), ('switch', 30), ('button', 8)):
            self.assertEqual(by_board['P'].count(kind), n)

    def test_transform_is_a_translation_matching_the_partition(self):
        for b in VIEW['boards']:
            with self.subTest(board=b['id']):
                self.assertEqual(b['kicad_to_panel_offset_mm'], [100.0, 50.0])
                xs = [p[0] for p in b['outline']]; ys = [p[1] for p in b['outline']]
                px = [p[0] for p in b['partition_outline']]; py = [p[1] for p in b['partition_outline']]
                for got, want in zip((min(xs), min(ys), max(xs), max(ys)), (min(px), min(py), max(px), max(py))):
                    self.assertAlmostEqual(got, want, delta=TOL)


class Rasters(unittest.TestCase):
    def test_every_copper_layer_has_a_raster_of_the_board_size(self):
        from PIL import Image
        for b in VIEW['boards']:
            self.assertEqual([c['layer'] for c in b['copper']], b['layers'])
            x0, y0, x1, y1 = b['bbox']
            for c in b['copper']:
                with self.subTest(board=b['id'], layer=c['layer']):
                    path = HERE / c['file']
                    self.assertEqual(path.stat().st_size, c['bytes'])
                    with Image.open(path) as im:
                        self.assertEqual(im.mode, '1')
                        self.assertAlmostEqual(im.size[0], (x1 - x0) * b['ppm'], delta=2)
                        self.assertAlmostEqual(im.size[1], (y1 - y0) * b['ppm'], delta=2)
                    self.assertTrue(0 < c['coverage'] < 1)


if __name__ == '__main__':
    unittest.main()
