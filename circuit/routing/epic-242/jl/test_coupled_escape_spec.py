"""Focused source-corridor geometry, immutable binding and refusal regressions."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from shapely.geometry import LineString

from coupled_escape_spec import (ANCHOR_UUID, HERE, SOURCE_UUID, boundary_candidates,
                                 collision, generate, refuse_duplicate_cut_ids)
from prepare_diagnostic import encoded, sha

ARCHIVE=Path(sys.argv.pop(1)) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None


class Geometry(unittest.TestCase):
    def track(self, y=0, net='signal', layer='F.Cu'):
        return {'uuid':'track','net':net,'a':[0,int(y*1e6)],'b':[1000000,int(y*1e6)],
                'width':200000,'layer':layer}

    def test_exact_width_clearance_and_conservative_margin_are_distinct(self):
        line=LineString([(0,0),(1,0)])
        self.assertTrue(collision('track',self.track(.49),line)['unexpanded_envelope_collision'])
        conservative=collision('track',self.track(.52),line)
        self.assertFalse(conservative['unexpanded_envelope_collision'])
        self.assertIsNone(collision('track',self.track(.55),line))
        self.assertIsNone(collision('track',self.track(0,layer='B.Cu'),line))

    def test_rail_growth_remains_extra_clearance(self):
        line=LineString([(0,0),(1,0)])
        self.assertIsNone(collision('track',self.track(.57),line))
        rail=collision('track',self.track(.57,net='-12V'),line)
        self.assertEqual(rail['rail_growth_mm'],.05)
        self.assertFalse(rail['unexpanded_envelope_collision'])

    def test_repeated_uuid_cut_is_refused_without_mutating_source(self):
        dump={'pads':[],'tracks':[self.track(),self.track(.3)],'vias':[]}
        before=copy.deepcopy(dump)
        with self.assertRaisesRegex(ValueError,'repeated UUID'):
            refuse_duplicate_cut_ids(dump,['track'])
        refuse_duplicate_cut_ids(dump,[])
        self.assertEqual(dump,before)

    def test_smd_boundary_never_gains_inner_layer_anchors(self):
        pad={'uuid':'pad','net':'signal','xy':[0,0],'layers':['F.Cu'],'poly':[[0,0],[1,0],[1,1],[0,1]]}
        track=self.track(layer='B.Cu')
        dump={'pads':[pad],'tracks':[track],'vias':[],'layers':['F.Cu','B.Cu']}
        blocker={'source_geometry':pad,'object_type':'pad','source_row_index':0,'source_row_sha256':'test'}
        boundary=boundary_candidates(blocker,dump)['endpoints'][0]
        self.assertEqual(boundary['layers'],['F.Cu'])
        self.assertEqual(boundary['retained_same_net_touching_row_candidates'],[])

    def test_endpoint_candidates_keep_exact_touching_rows(self):
        obj=self.track(); other={**self.track(),'uuid':'other','a':[1000000,0],'b':[2000000,0]}
        dump={'pads':[],'tracks':[obj,other],'vias':[],'layers':['F.Cu','B.Cu']}
        blocker={'source_geometry':obj,'object_type':'track','source_row_index':0,'source_row_sha256':'test'}
        result=boundary_candidates(blocker,dump)
        self.assertEqual(result['endpoints'][0]['retained_same_net_touching_row_candidates'],[])
        self.assertEqual(result['endpoints'][1]['retained_same_net_touching_row_candidates'][0]['uuid'],'other')
        self.assertIn('NOT PROVED',result['restoration_status'])


@unittest.skipUnless(ARCHIVE,'exact accepted JL117 ZIP required')
class AcceptedCorridor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=generate(ARCHIVE)

    def test_deterministic_replay_and_fixed_endpoint_identity(self):
        self.assertEqual((HERE/'coupled-escape-spec.json').read_bytes(),encoded(self.result))
        corridor=self.result['corridor']
        self.assertEqual(corridor['source']['uuid'],SOURCE_UUID)
        self.assertEqual(corridor['existing_anchor']['uuid'],ANCHOR_UUID)
        self.assertEqual(corridor['source']['xy'],[239705000,154257500])
        self.assertEqual(corridor['existing_anchor']['xy'],[233500000,156520000])
        self.assertTrue(corridor['existing_anchor']['locked'])
        self.assertEqual(corridor['goal_component']['all_member_count'],1389)
        self.assertEqual(self.result['removed_uuids'],[])
        self.assertEqual(self.result['added_copper'],[])
        self.assertFalse(self.result['native_executed'])
        self.assertFalse(self.result['search_executed'])

    def test_actual_corridor_retains_all_overlapping_rows_and_full_obligations(self):
        blockers=self.result['screen']['blocker_rows']
        physical=[b for b in blockers if b['unexpanded_envelope_collision']]
        self.assertEqual(len(blockers),9)
        self.assertEqual(len(physical),7)
        self.assertEqual(len({b['source_geometry']['net'] for b in physical}),3)
        self.assertEqual(self.result['screen']['duplicate_uuid_rows_encountered'],[])
        obligations=self.result['full_coupled_restoration_obligations']
        self.assertTrue(all(len(n['all_source_row_identities'])==n['all_source_rows_count'] for n in obligations))
        self.assertEqual(len(self.result['historical_pr233']['six_pad_minus12_original_group_obligation']),6)
        self.assertEqual(len(self.result['historical_pr233']['receipts']['native-cut-membership.json']['content']['boundaries']),2)
        self.assertEqual(self.result['next_diagnosed_case']['case']['open_edges'],2)

    def test_changed_published_board_is_rejected(self):
        original=Path.read_bytes
        def changed(path):
            return b'changed copper' if str(path).endswith('/boards/osc-jack-left/osc-jack-left.kicad_pcb') else original(path)
        with patch.object(Path,'read_bytes',changed), self.assertRaisesRegex(ValueError,'published JL'):
            generate(ARCHIVE)


if __name__=='__main__':unittest.main()
