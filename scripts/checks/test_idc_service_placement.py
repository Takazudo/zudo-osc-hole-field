import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'design/architecture-278/implementation/stage36/idc-service-placement'
spec=importlib.util.spec_from_file_location('idc_service',HERE/'generate.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ServicePlacement(unittest.TestCase):
    def setUp(self):
        self.p=m.build()
        self.by={c['ref']:c for c in self.p['connectors']}

    def test_deterministic_outputs_and_bindings(self):
        self.assertEqual(self.p,json.loads((HERE/'candidate.json').read_text()))
        self.assertEqual(m.svg(self.p),(HERE/'placement.svg').read_text())
        for path,digest in self.p['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)

    def test_maps_and_local_coordinates_preserved(self):
        old=json.loads((m.OLD/'candidate.json').read_text())
        self.assertEqual(self.p['pin_maps'],old['pin_maps'])
        for before,after in zip(old['connectors'],self.p['connectors']):
            delta=[after['coordinates']['centre_mm'][i]-before['coordinates']['centre_mm'][i] for i in (0,1)]
            for a,b in zip(before['coordinates']['pins'],after['coordinates']['pins']):
                self.assertEqual(a['net'],b['net'])
                self.assertEqual(a['pin'],b['pin'])
                self.assertEqual(a['header_face_xy'],b['header_face_xy'])
                self.assertEqual(a['socket_face_xy'],b['socket_face_xy'])
                for i in (0,1):self.assertAlmostEqual(a['global_xy'][i]+delta[i],b['global_xy'][i])

    def test_known_screens_and_unchanged_unknown_status(self):
        for c in self.p['connectors']:
            for key in ['same_board_grip_package_hits','same_board_body_terminal_hits','known_tail_hits','mount_tool_body_hits']:
                self.assertEqual(c[key],[],(c['ref'],key))
            self.assertTrue(c['body_with_allowance_within_board'])
            self.assertIsNone(c['mated_max_height_mm'])
            self.assertIsNone(c['cable_cut_length_mm'])
        self.assertFalse(self.p['adopted'])
        self.assertEqual(self.by['J17902']['unknown_neighbor_projection_refs'],['J1610','J1710'])
        self.assertIn('RV1408',{v['ref'] for v in self.p['support_unknown_projection_hits']})

    def test_negative_history_and_new_ceilings(self):
        old=self.p['prior_negative_screens']
        self.assertEqual(old['J17902']['withdrawal15']['necessary_max_height_above_board_mm'],8)
        self.assertEqual(old['J17901']['grip_withdrawal15']['necessary_max_height_above_board_mm'],-9.6)
        self.assertEqual(self.by['J17902']['screens']['grip_withdrawal15']['necessary_max_height_above_board_mm'],39)
        self.assertEqual(self.by['J17901']['screens']['grip_withdrawal15']['necessary_max_height_above_board_mm'],77.4)
        self.assertEqual(len(self.p['prior_J_PWR_grip_package_hits']),5)

    def test_intervals_contain_chosen_points_and_reject_old(self):
        for key,ref,old in [('middle_C_SIG_centre_y_mm_open','J17902',286),
                            ('control_C_SIG_centre_y_mm_open','J17901',297.5),
                            ('jack_J_PWR_centre_y_mm_open','J17903',170)]:
            lo,hi=self.p['feasible_intervals'][key];y=self.by[ref]['coordinates']['centre_mm'][1]
            self.assertLess(lo,y);self.assertLess(y,hi)
            self.assertFalse(lo<old<hi)
        # Restore old neighboring row: the conservative interval is empty.
        half_grip=m.g.mm(.343)/2+3;half_other=m.g.mm(.343)/2+1
        self.assertGreater(154+half_grip+half_other,174-half_grip)

    def test_restoring_old_side_member_reproduces_conflict(self):
        c=self.by['J17901'];box=c['screens']['grip_withdrawal15']['xy_mm']
        self.assertTrue(m.g.overlap(box,[203,287,206,320]))
        self.assertTrue(m.g.overlap(box,[231,287,234,320]))
        for s in self.p['effective_support_solids']:
            if s['id'].startswith('control'):
                self.assertFalse(m.g.overlap(box,s['xy']),s['id'])

    def test_rotation_rejection_and_frame_joint_overlap(self):
        r=self.p['rejected_control_rotation']
        box=m.g.grow(m.g.footprint(r['centre_mm'],m.g.mm(.793),m.g.mm(.343),90),1)
        self.assertTrue(m.g.overlap(box,[211.75,277.75,225.25,291.1]))
        for side in ('left','right'):
            parts={s['id'].split('-')[-1]:s for s in self.p['effective_support_solids'] if s['id'].startswith('control-'+side+'-lower-')}
            for end in ('top','bottom'):
                a,b=parts[end]['xy'],parts['grip']['xy']
                self.assertEqual(min(a[2],b[2])-max(a[0],b[0]),2)
        self.assertEqual([f['xy'] for f in self.p['control_fasteners']],[[213,309],[224,309]])


if __name__=='__main__':unittest.main()
