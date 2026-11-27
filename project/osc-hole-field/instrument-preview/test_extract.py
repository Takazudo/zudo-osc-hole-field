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


class Configuration(unittest.TestCase):
    """The snapshot names one configuration and refuses boards or a package manifest that do not match it.
    Mutation cases use temporary copies; the tracked configuration.json is never rewritten."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location('preview_extract', HERE / 'extract.py')
        cls.ex = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.ex)
        cls.conf_text = (ROOT / cls.ex.CONFIGURATION).read_text()

    def conf(self):
        return json.loads(self.conf_text)

    def inputs(self):
        return {p: {'sha256': sha256(ROOT / p)} for p in self.conf()['board_sha256']}

    def run_with(self, conf):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'configuration.json'
            path.write_text(json.dumps(conf))
            return self.ex.load_configuration(self.inputs(), path)

    def rejects(self, conf, words):
        with self.assertRaises(SystemExit) as cm:
            self.run_with(conf)
        self.assertIn(words, str(cm.exception))

    def with_manifest(self, body, raw=None):
        """A temporary repository-relative manifest (removed afterwards) and a configuration naming it."""
        import tempfile
        fd, name = tempfile.mkstemp(suffix='.json', prefix='.tmp-manifest-', dir=HERE)
        import os
        os.close(fd)
        Path(name).write_text(raw if raw is not None else json.dumps(body))
        self.addCleanup(Path(name).unlink)
        c = self.conf()
        c['package_manifest'] = {'path': str(Path(name).relative_to(ROOT)), 'sha256': sha256(name)}
        return c

    def test_view_carries_the_current_configuration(self):
        self.assertEqual(VIEW['configuration'], self.conf())
        self.assertEqual(VIEW['inputs'][self.ex.CONFIGURATION]['sha256'], sha256(ROOT / self.ex.CONFIGURATION))
        self.assertEqual(VIEW['configuration']['owner_confirmation'], 'PENDING')

    def test_baseline_is_not_selected_and_has_no_package(self):
        c = self.conf()
        self.assertFalse(c['selected_for_order'])
        self.assertIsNone(c['package_manifest'])
        self.assertIn('HOLD', c['package_status'])

    def test_declared_board_hashes_match_the_snapshot(self):
        for p, h in self.conf()['board_sha256'].items():
            self.assertEqual(VIEW['inputs'][p]['sha256'], h, p)

    def test_current_configuration_is_accepted(self):
        self.assertEqual(self.run_with(self.conf())['id'], self.conf()['id'])

    def test_rejects_a_stale_board_hash(self):
        c = self.conf()
        c['board_sha256']['boards/osc-core/osc-core.kicad_pcb'] = '0' * 64
        self.rejects(c, 'does not match the checked-out boards')

    def test_rejects_a_missing_board(self):
        c = self.conf()
        c['board_sha256'].pop('boards/panel/panel.kicad_pcb')
        self.rejects(c, 'differ from the preview board set')

    def test_rejects_an_extra_board(self):
        c = self.conf()
        c['board_sha256']['boards/osc-jack/osc-jack.kicad_pcb'] = '0' * 64
        self.rejects(c, 'differ from the preview board set')

    def test_rejects_selection_without_a_package(self):
        c = self.conf()
        c['selected_for_order'] = True
        c['role'] = 'selected'
        self.rejects(c, 'selected for order without a package manifest')

    def test_rejects_a_missing_package_manifest(self):
        c = self.conf()
        c['package_manifest'] = {'path': 'manufacturing/does-not-exist.json', 'sha256': '0' * 64}
        self.rejects(c, 'is missing')

    def test_rejects_an_absolute_manifest_path(self):
        c = self.conf()
        c['package_manifest'] = {'path': str(HERE / 'configuration.json'), 'sha256': '0' * 64}
        self.rejects(c, 'repository-relative')

    def test_rejects_a_parent_relative_manifest_path(self):
        c = self.conf()
        c['package_manifest'] = {'path': '../outside.json', 'sha256': '0' * 64}
        self.rejects(c, 'repository-relative')

    def test_rejects_a_symlinked_manifest_outside_the_repository(self):
        import tempfile
        outside = Path(tempfile.mkdtemp()) / 'm.json'
        outside.write_text(json.dumps({'board_sha256': self.conf()['board_sha256']}))
        link = HERE / '_test_link_manifest.json'
        link.symlink_to(outside)
        self.addCleanup(link.unlink)
        c = self.conf()
        c['package_manifest'] = {'path': str(link.relative_to(ROOT)), 'sha256': sha256(outside)}
        self.rejects(c, 'repository-relative')

    def test_rejects_a_malformed_manifest(self):
        for bad in ('manufacturing/x.json', {'path': 123, 'sha256': '0' * 64}, {'path': 'x.json'}):
            c = self.conf()
            c['package_manifest'] = bad
            self.rejects(c, 'must be null or')

    def test_rejects_free_text_owner_confirmation(self):
        c = self.conf()
        c['owner_confirmation'] = 'looks fine'
        self.rejects(c, 'must be PENDING or CONFIRMED')

    def test_rejects_confirmation_of_an_unselected_configuration(self):
        c = self.conf()
        c['owner_confirmation'] = 'CONFIRMED'
        self.rejects(c, 'not selected for order')

    def test_rejects_selection_of_a_baseline_role(self):
        c = self.with_manifest({'board_sha256': self.conf()['board_sha256']})
        c['selected_for_order'] = True
        self.rejects(c, 'disagrees with selected_for_order')

    def test_rejects_a_short_source_commit(self):
        c = self.conf()
        c['source_commit'] = 'deadbeef'
        self.rejects(c, 'full commit id')

    def test_rejects_a_missing_hold_label(self):
        c = self.conf()
        c.pop('package_status_short')
        self.rejects(c, 'package_status_short')

    def test_rejects_a_changed_manifest(self):
        c = self.with_manifest({'board_sha256': self.conf()['board_sha256']})
        c['package_manifest']['sha256'] = '0' * 64
        self.rejects(c, 'hash differs from the configuration')

    def test_rejects_a_manifest_bound_to_other_boards(self):
        boards = {**self.conf()['board_sha256'], 'boards/osc-core/osc-core.kicad_pcb': '1' * 64}
        self.rejects(self.with_manifest({'board_sha256': boards}), 'binds other boards')

    def test_rejects_a_manifest_that_is_not_an_object(self):
        self.rejects(self.with_manifest(None, raw='[]'), 'binds other boards')

    def test_accepts_a_matching_manifest(self):
        c = self.with_manifest({'board_sha256': self.conf()['board_sha256']})
        self.assertEqual(self.run_with(c)['package_manifest'], c['package_manifest'])


if __name__ == '__main__':
    unittest.main()
