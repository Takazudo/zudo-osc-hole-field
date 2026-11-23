"""MC04-S10 Revision 1 (DS-148): the four holds, the c6 rebind check, the overlay rules and their acceptance (no KiCad)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c6_rebind  # noqa: E402
import overlay as ov  # noqa: E402

ROOT = ov.ROOT
OV = json.loads(ov.OUT.read_text())
C6 = json.loads(c6_rebind.OUT.read_text())
GATE = json.loads((ROOT / 'design/stack/geometry/links/link-gate.json').read_text())
BASE = json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', '8243acdf:design/stack/geometry/links/link-gate.json'],
                                 capture_output=True, check=True, text=True).stdout)
HELD = {'P-K-P-L13.01.01.01', 'P-K-P-L13.01.01.02', 'P-K-P-L13.01.02.01', 'P-K-P-L15.02.01.01'}


class Links(unittest.TestCase):
    def test_unheld_live_links_are_byte_equal_to_the_base(self):
        a = {x['id']: x for x in BASE['links']}
        for x in GATE['links']:
            if x['id'] in HELD or x.get('gone'):
                continue
            self.assertEqual([x[k] for k in ('centre', 'slot_centre', 'direction')],
                             [a[x['id']][k] for k in ('centre', 'slot_centre', 'direction')], x['id'])
        self.assertEqual({k: GATE['summary'][k] for k in ('links', 'latches', 'signals_on_links')},
                         {'links': 62, 'latches': 124, 'signals_on_links': 531})

    def test_l03_02_02_01_stays_dissolved_with_its_riders_on_l13_01_01_02(self):
        g = {x['id']: x for x in GATE['links']}
        x = g['P-K-P-L03.02.02.01']
        self.assertTrue(x.get('gone'))
        rid = {(r['net'], r['host']): r['distance_mm'] for r in x['riders_out']}
        for net in ('/M4B/1_REMOTE', '/M4B/2_REMOTE'):
            self.assertLessEqual(rid[(net, 'P-K-P-L13.01.01.02')], 45.0)

    def test_l13_01_01_02_turns_with_its_cable_connector_and_order_unchanged(self):
        a = {x['id']: x for x in BASE['links']}['P-K-P-L13.01.01.02']
        b = {x['id']: x for x in GATE['links']}['P-K-P-L13.01.01.02']
        self.assertEqual((a['direction'], b['direction']), ('+y', '-y'))
        for k in ('size', 'connector', 'cable', 'cable_length_mm', 'circuits', 'positions'):
            self.assertEqual(a[k], b[k], k)

    def test_c6_rebind_record_and_verdict(self):
        self.assertTrue(C6['signal_and_positions_unchanged'])
        self.assertTrue(all(all(v.values()) for v in C6['c6_links'].values()))
        self.assertEqual(json.loads((ROOT / 'design/stack/link-electrical/c6-pass.json').read_text())['unsolved_links'], [])


class Overlay(unittest.TestCase):
    def test_positions(self):
        self.assertEqual(OV['without_a_position'], [r for r in OV['without_a_position']])
        self.assertTrue({'U1415', 'U5110', 'U8409'} <= set(OV['without_a_position']))
        self.assertFalse({'U5209', 'U5210'} & set(OV['without_a_position']))
        rows = {(r['board'], r['ref']) for r in GATE['replacement']['footprints']}
        self.assertFalse({('K', 'U5209'), ('K', 'U5210')} & rows)
        self.assertEqual(OV['stop'], [])

    def test_every_new_row_has_a_pose(self):
        for r in OV['row_changes']['rows']:
            if r['change'] == 'new':
                self.assertIsNotNone(r['after']['origin'], r['ref'])

    def test_overlay_blocks_follow_the_block_rule(self):
        need = {r['ic'] for r in OV['block_rule'] if r['pose'].startswith('overlay')}
        self.assertEqual(need, {'U4222', 'U4227', 'U4537'})
        for e in OV['blocks']:
            self.assertIsNotNone(e['pose'])
            self.assertLessEqual(e['pose']['moved_mm'], 24.0)
            before = {d['ref']: d['distance_before_mm'] for d in e['reason']}
            for d in e['decouplers_after']:
                self.assertEqual(d['face'], e['pose']['face'], d['ref'])
                self.assertLessEqual(d['distance_mm'], before[d['ref']] + 1e-6, d['ref'])
        u4537 = next(e for e in OV['blocks'] if e['ic'] == 'U4537')
        self.assertIn('/E5/CLOCK', u4537['timing_nodes'])

    def test_ruled_parts_and_trimmers(self):
        r = OV['ruled_parts']
        self.assertEqual(r['R5257']['face'], 'B')
        self.assertLessEqual(r['R5257']['distance_to_ic_mm'], 7.93)
        self.assertEqual(r['R5259']['face'], 'B')
        for t in ('RV4503', 'RV8407', 'RV2310'):
            self.assertEqual(r[t]['face'], 'B', t)
        self.assertTrue(all(t['rear'] for t in OV['trimmers_in_changed_rows']))

    def test_acceptance_figures_are_unchanged(self):
        for x in OV['acceptance_figures']:
            self.assertEqual(x['parts_in_changed_rows'], [], x['ref'])
            if 'worse' in x:
                self.assertFalse(x['worse'], x['ref'])

    def test_member_faces_clear_for_every_overlay_block(self):
        mf = json.loads((ROOT / 'scripts/stack/studies/mc04_s8_replacement/member-faces.json').read_text())
        kinds = {b['ic']: b for b in mf['blocks']}
        for ic in ('U4222', 'U4227', 'U4537'):
            self.assertEqual(kinds[ic]['kind'], 'S10 block-rule overlay')
        self.assertTrue(all(b['all_clear'] for b in mf['blocks']))

    def test_no_new_row_is_an_input_buffer_stop(self):
        s = ov.OV.__new__(ov.OV)  # the stop rule itself, on a fixed example
        s.buffer_ics, s.owner, s.pins = {'U9'}, {('K', 'R9'): 'U9'}, {'R9': {'1': '/X/A_FB', '2': '/X/B'}, 'U9': {}}
        self.assertEqual(ov.buffer_stop(s, ('K', 'U9')), 'input-buffer IC')
        self.assertIn('_FB', ov.buffer_stop(s, ('K', 'R9')))
        s.pins['R9'] = {'1': '/X/A_DRIVE', '2': '/X/B_REMOTE'}
        self.assertIsNone(ov.buffer_stop(s, ('K', 'R9')))


if __name__ == '__main__':
    unittest.main()
