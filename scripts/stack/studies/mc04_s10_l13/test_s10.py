"""MC04-S10 Revision 1 (DS-148): the four holds, the c6 rebind check, the overlay rules and the rejected candidate diagnostic (no KiCad)."""
import copy
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
        self.assertEqual(OV['without_a_position'], ['U1415', 'U5110', 'U8409'])
        rows = {(r['board'], r['ref']) for r in GATE['replacement']['footprints']}
        self.assertFalse({('K', 'U5209'), ('K', 'U5210')} & rows)
        self.assertEqual(OV['disposition'], 'STOP')
        for ref, net in [('R5249', '/W1/FOLDER_SUM'), ('R5256', '/W1/F2_SUM'),
                         ('R8221', '/M5B/Ca92eeb_W_SENSE'), ('R8331', '/M4A/C38051c_W_SENSE'),
                         ('R8356', '/M4A/C24ce01_W_SENSE'), ('R4238', '/E2/REF9_FB')]:
            self.assertIn(f'newly displaced K {ref}: part on {net}', OV['stop'])

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
        resistor = r['R5257']
        self.assertEqual(resistor['distance_to_ic_mm'], resistor['paper_distance_mm'])
        self.assertEqual(round(resistor['distance_to_ic_mm'], 2), resistor['limit_mm'])
        self.assertGreater(resistor['distance_to_ic_mm'], resistor['limit_mm'])
        self.assertFalse(resistor['meets'])
        self.assertEqual(r['R5259']['face'], 'B')
        for t in ('RV4503', 'RV8407', 'RV2310'):
            self.assertEqual(r[t]['face'], 'B', t)
        self.assertTrue(all(t['rear'] for t in OV['trimmers_in_changed_rows']))

    def test_effective_changes(self):
        changed = {x['ref']: x for x in OV['effective_movements']}
        self.assertEqual((changed['R4238']['distance_mm'], changed['R4238']['from'], changed['R4238']['to']),
                         (3.55, 'B', 'B'))
        faces = {x['ref']: (x['from'], x['to']) for x in OV['face_changes']}
        self.assertEqual(faces['C4554'], ('B', 'F'))
        self.assertNotIn('C5212', faces)

    def test_locality_discrepancy_predates_s10(self):
        mismatches = [x for x in OV['acceptance_figures'] if not x['matches_sources']]
        self.assertEqual([x['ref'] for x in mismatches], ['U5113'])
        row = mismatches[0]
        self.assertEqual(row['effective_pose'], row['pre_s10_effective_pose'])
        self.assertEqual((row['distance_mm_recorded'], row['distance_mm_recomputed']), (65.97, 84.77))

    def test_mutated_locality_poses_with_unchanged_distance_are_rejected(self):
        source = {('K', 'U1'): {'x_mm': 1.0, 'y_mm': 2.0, 'side': 'B.Cu'}}
        effective = {('K', 'U1'): ([4.0, 6.0], 'B', 'gate row')}
        record = {'board': 'K', 'ref': 'U1', 'pre_move_pose': [1.0, 2.0, 'B.Cu'],
                  'pose': [4.0, 6.0, 'B.Cu'], 'distance_mm': 5.0}
        self.assertTrue(ov.locality(record, source, effective)['matches_sources'])
        for field in ('pre_move_pose', 'pose'):
            record[field][0] += 1.0
        self.assertFalse(ov.locality(record, source, effective)['matches_sources'])

    def test_nested_metrics_distinguish_inherited_and_candidate_geometry(self):
        rows = {r['ref']: r for r in OV['acceptance_figures']}
        hold = rows['U4526']['ancillary_geometry']['/E5/HOLD_N.capacitance_estimate_pF']
        self.assertEqual((hold['recorded'], hold['pre_s10_effective'], hold['recomputed']), (25.01, 25.01, 30.1))
        w2 = rows['U5112']['ancillary_geometry']['/W2/C8df94f_SENSE.routed_estimate_mm']
        self.assertEqual((w2['recorded'], w2['pre_s10_effective'], w2['recomputed']), (106.2, 118.3, 118.3))
        diode = rows['D4101']['ancillary_geometry']
        self.assertTrue(diode['diode_to_gh_contact_mm.pose (interim board)']['matches'])
        self.assertAlmostEqual(diode['diode_to_protected_pin_mm.pose']['recomputed'], 38.15)

    def test_locality_inventory_and_ancillary_values_are_frozen(self):
        accepted = ov.pinned(ov.BASE, 'design/partition/locality-acceptances.json')
        for mutation in ('deleted', 'duplicate', 'changed distance', 'missing condition'):
            with self.subTest(mutation=mutation):
                doc = copy.deepcopy(accepted)
                records = doc['acceptances']
                if mutation == 'deleted':
                    records.pop()
                elif mutation == 'duplicate':
                    records.append(records[0])
                elif mutation == 'changed distance':
                    row = next(x for x in records if 'led' in x)
                    row['led']['distance_after_mm'] += 0.1
                else:
                    next(x for x in records if 'conditions' in x)['conditions'].pop()
                with self.assertRaisesRegex(ValueError, 'complete accepted record'):
                    ov.verify_locality_inventory(doc, accepted)

    def test_diagnostic_courtyards_use_the_combined_candidate(self):
        self.assertEqual(len(OV['blocks']), 3)
        for block in OV['blocks']:
            self.assertTrue(block['candidate_courtyard_check']['clear'], block)

    def test_protected_nodes_are_independent_of_owner(self):
        s = ov.OV.__new__(ov.OV)  # the stop rule itself, on a fixed example
        s.buffer_ics, s.owner, s.pins = {'U9'}, {('K', 'R9'): 'U9'}, {'R9': {'1': '/X/A_FB', '2': '/X/B'}, 'U9': {}}
        self.assertEqual(ov.buffer_stop(s, ('K', 'U9')), 'input-buffer IC')
        self.assertIn('_FB', ov.buffer_stop(s, ('K', 'R9')))
        for owner in (None, 'U8', 'U9'):
            for suffix in ('_FB', '_SENSE', '_SUM'):
                for ref in ('R9', 'R10'):
                    s.owner['K', ref] = owner
                    s.pins[ref] = {'1': '/X/A' + suffix}
                    self.assertIn('/X/A' + suffix, ov.buffer_stop(s, ('K', ref)))
        s.pins['R9'] = {'1': '/X/A_DRIVE', '2': '/X/B_REMOTE'}
        self.assertIsNone(ov.buffer_stop(s, ('K', 'R9')))


if __name__ == '__main__':
    unittest.main()
