"""Portable proposal checks; never substitute a toy fixture for native admission."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.pcbgen.foil_collar_geometry import PROPOSAL, compile_proposal, geometry


class FoilCollarGeometryTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(PROPOSAL.read_bytes())

    def rejects(self,fragment):
        with self.assertRaisesRegex(ValueError,fragment):compile_proposal(self.spec)

    def test_real_pair_and_finite_clearances(self):
        result=compile_proposal(self.spec)
        self.assertEqual(result['pair_id'],'JL-K-1:AGND-pin-2')
        for b,clearance in zip(result['boards'],(.270,.265)):
            self.assertAlmostEqual(b['minimum_conservative_copper_separation_mm'],clearance)
            self.assertAlmostEqual(b['minimum_dry_wetting_separation_mm'],.110)
            self.assertGreater(b['proposed_geometry']['minimum_flare_reconnection_overlap_mm'],.06)
            self.assertIn('NOT RUN',b['native_snapshot_binding'])
            self.assertIn('NOT RUN',b['new_native_reconstruction'])
        self.assertEqual(result['electrical_limits']['common_branch_plus_K_ohm'],.0005)
        self.assertEqual(result['boards'][0]['full_trace']['normal'],[0,-1,0])
        self.assertEqual(result['boards'][1]['full_trace']['normal'],[0,1,0])
        for b in result['boards']:
            self.assertAlmostEqual(b['full_trace']['nominal_stack_depth_mm'][1]-b['full_trace']['nominal_stack_depth_mm'][0],.07)

    def test_each_actual_bypass_must_be_retired(self):
        original=copy.deepcopy(self.spec)
        for index in (0,1):
            with self.subTest(index=index):
                self.spec=copy.deepcopy(original)
                del self.spec['boards'][0]['proposed_retirements'][index]
                self.rejects('conflicts|drill/barrel')

    def test_retirement_cannot_remove_fixed_pad(self):
        b=self.spec['boards'][0]
        b['proposed_retirements'].append({'uuid':b['snapshot']['items'][0]['uuid'],'kind':'track'})
        self.rejects('only exact non-pad AGND')

    def test_nominal_clearance_is_insufficient_without_offset(self):
        self.spec['geometry']['neck_x_offset_mm']=0
        # Nominal K right gap is .275 mm; edge+registration bounds consume .06.
        self.assertGreater(120.25-(119.875+.1),.25)
        # Move only the new access origin with the neck, preserving its join.
        self.spec['boards'][0]['board_access']['track_points_native_mm'][0][0]+=.05
        self.rejects('conservative separation')

    def test_larger_registration_breaks_actual_obstacle_gap(self):
        self.spec['geometry']['relative_registration_abs_max_mm']=.05
        self.rejects('conflicts')

    def test_full_possible_wetting_includes_copper_edge(self):
        # Removing the pad-edge allowance would incorrectly pass this case.
        self.spec['geometry']['mask_registration_abs_max_mm']=.065
        self.rejects('full possible solder/mask support')

    def test_nonzero_finite_intervals_and_nominal_membership(self):
        original=copy.deepcopy(self.spec)
        for interval in ([.2,.2],[0,.2],[.2,float('inf')],[.21,.22]):
            with self.subTest(interval=interval):
                self.spec=copy.deepcopy(original)
                self.spec['geometry']['finished_neck_width_interval_mm']=interval
                self.rejects('interval')

    def test_native_minimum_width_is_separate_from_finished_width(self):
        self.spec['geometry']['nominal_neck_width_mm']=.19
        self.rejects('native minimum track rule')

    def test_other_foil_copper_is_conservatively_excluded(self):
        b=self.spec['boards'][1];shape=geometry(b,self.spec['geometry'])
        b['snapshot']['items'].append({'uuid':'mutated-opposite-foil','net':'AGND',
            'copper_bbox_mm':{'B.Cu':shape['worst_dry_collar_bbox_mm']},'primitive_kinds':{'B.Cu':'rectangle'}})
        self.rejects('mutated-opposite-foil')

    def test_any_new_barrel_through_island_is_excluded(self):
        b=self.spec['boards'][1]
        b['snapshot']['holes'].append({'uuid':'new-barrel','xy_mm':b['native_pad_xy_mm'],'size_mm':[.3,.3],'plated':True})
        self.rejects('unretired drill/barrel')

    def test_source_identity_face_and_native_pad_binding(self):
        original=copy.deepcopy(self.spec)
        mutations=[('reference','J999999'),('face','F.Cu'),('pad_uuid','unknown'),('outward_direction_y',1),('native_pad_quarter_turns',0)]
        for key,value in mutations:
            with self.subTest(key=key):
                self.spec=copy.deepcopy(original);self.spec['boards'][0][key]=value
                self.rejects('identity|orientation')

    def test_nominal_reconnection_does_not_prove_interval_reconnection(self):
        self.spec['geometry']['nominal_flare_length_mm']=.35
        self.spec['geometry']['finished_flare_length_interval_mm']=[.33,.37]
        self.rejects('flare cannot reach')

    def test_access_must_join_actual_flare_and_via(self):
        self.spec['boards'][0]['board_access']['track_points_native_mm'][0]=[119.825,84.5]
        self.rejects('dogleg must join')

    def test_rail_is_not_an_ideal_ground_landing(self):
        self.spec['boards'][0]['board_access']['target_plane']='B.Cu'
        self.rejects('no retained AGND target plane')

    def test_all_foreign_rail_clips_and_via_antipads_are_emitted(self):
        b=compile_proposal(self.spec)['boards'][0]
        antipads={c['layer'] for c in b['proposed_zone_clips'] if 'new via' in c['status']}
        self.assertEqual(antipads,{'F.Cu','In2.Cu','B.Cu'})
        self.assertTrue(any(c['net']=='+5V' and 'complete AGND flare' in c['status'] for c in b['proposed_zone_clips']))
        self.assertFalse(any(c['layer']=='In1.Cu' and 'new via' in c['status'] for c in b['proposed_zone_clips']))

    def test_missing_artifact_cannot_report_native_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'artifact unavailable'):
                compile_proposal(self.spec,native_root=Path(tmp))

    def test_projection_window_and_outline_cannot_be_ignored(self):
        original=copy.deepcopy(self.spec)
        self.spec['boards'][0]['snapshot']['scan_window_mm']=[119,84,120,87]
        self.rejects('projection window')
        self.spec=original
        self.spec['boards'][0]['snapshot']['outline_mm']=[[0,0],[1,0],[1,1],[0,1]]
        self.rejects('board outline')

    def test_source_epoch_drift_fails_closed(self):
        self.spec['source_files']['design/partition/partition.json']='0'*64
        self.rejects('source file hash drift')

    def test_same_face_landing_requires_explicit_distinct_priority(self):
        k=self.spec['boards'][1]
        self.assertEqual(k['collar_zone_priority'],1)
        self.assertEqual(k['board_access']['target_zone_priority'],0)
        k['collar_zone_priority']=0
        self.rejects('distinct priorities')

    def test_priority_and_scope_are_source_checked(self):
        original=copy.deepcopy(self.spec)
        for value in (-1,True,.5):
            self.spec=copy.deepcopy(original);self.spec['boards'][1]['collar_zone_priority']=value
            self.rejects('explicit nonnegative')
        self.spec=original;self.spec['boards'][1]['native_realization_scope']='ignore_rules'
        self.rejects('realization scope')


if __name__=='__main__':unittest.main()
