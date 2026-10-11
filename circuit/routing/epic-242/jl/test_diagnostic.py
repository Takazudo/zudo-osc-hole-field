"""Source authentication, no-search mask semantics and native fail-closed tests."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from prepare_diagnostic import (HERE, ROOT, authenticate, encoded, first_via_mask,
                                prepare, read, target_members, validate_dump)
from native_diagnostic import require_admission

ARCHIVE = Path(sys.argv.pop(1)) if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None


class MaskSemantics(unittest.TestCase):
    def masks(self):
        free = np.zeros((2, 5, 5), bool)
        free[0, 2, 1:4] = True
        src = np.zeros_like(free)
        src[0, 2, 1] = True
        via = np.zeros((5, 5), bool)
        return free, via, src

    def test_legal_via_in_disconnected_component_is_negative(self):
        free, via, src = self.masks()
        free[:, 0, 0] = True
        via[0, 0] = True
        result = first_via_mask(free, via, src, np.zeros_like(src))
        self.assertEqual(result['legal_via_cells'], 1)
        self.assertTrue(result['negative'])

    def test_first_reachable_via_is_not_negative_or_routing_acceptance(self):
        free, via, src = self.masks()
        via[2, 3] = True
        result = first_via_mask(free, via, src, np.zeros_like(src))
        self.assertFalse(result['negative'])
        self.assertFalse(result['search_executed'])
        self.assertFalse(result['native_executed'])

    def test_other_layer_cannot_be_reached_before_first_via(self):
        free, via, src = self.masks()
        free[1, :, :] = True
        via[0, 0] = True
        result = first_via_mask(free, via, src, np.zeros_like(src))
        self.assertTrue(result['negative'])
        self.assertEqual(result['layers'][1]['optimistic_reachable_cells'], 0)

    def test_no_direct_native_execution_even_with_slot_text(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'bounded guard'):
                require_admission('not-an-admission', '250-test')
        with self.assertRaises(ValueError):
            require_admission(None, '250-test')

    def test_guard_environment_cannot_substitute_for_cgroup_membership(self):
        env = {'EPIC242_NATIVE_WORKER': 'jl250-test',
               'EPIC242_NATIVE_SLICE': 'epic242-w' + 'jl250-test'.encode().hex() + '.slice',
               'EPIC242_NATIVE_DEADLINE': '9999999999'}
        with patch.dict('os.environ', env, clear=True), patch.object(
                Path, 'read_text', return_value='0::/unbounded.service\n'):
            with self.assertRaisesRegex(ValueError, 'outside'):
                require_admission('parent-slot', '250-test')

    def test_cgroup_name_cannot_substitute_for_memory_cap(self):
        env = {'EPIC242_NATIVE_WORKER': 'jl250-test',
               'EPIC242_NATIVE_SLICE': 'epic242-w' + 'jl250-test'.encode().hex() + '.slice',
               'EPIC242_NATIVE_DEADLINE': '9999999999'}

        def unbounded(path):
            return '0::/epic242.slice/epic242-w' + 'jl250-test'.encode().hex() + '.slice/checks.service\n' if str(path) == '/proc/self/cgroup' else 'max\n'

        with patch.dict('os.environ', env, clear=True), patch.object(Path, 'read_text', unbounded):
            with self.assertRaisesRegex(ValueError, 'cap'):
                require_admission('parent-slot', '250-test')


class AttributionSemantics(unittest.TestCase):
    def fixture(self, copper=(), growth=None, source_xy=(5, 5)):
        from scipy import ndimage
        from scripts.pcbgen.grid_router import Raster, island_mask
        def pad(uuid, x, y, net='AGND'):
            return {'uuid': uuid, 'ref': uuid, 'pad': '1', 'net': net,
                    'xy': [int(x*1e6), int(y*1e6)], 'layers': ['F.Cu'],
                    'poly': [[int((x+dx)*1e6), int((y+dy)*1e6)] for dx, dy in ((-.1,-.1),(.1,-.1),(.1,.1),(-.1,.1))],
                    'drill': 0, 'npth': False}
        source = pad('source', *source_xy)
        dump = {'pads': [source, pad('other', 8, 8)], 'tracks': list(copper), 'vias': [], 'keepouts': [],
                'edges': [[0,0,10000000,0],[10000000,0,10000000,10000000],
                          [10000000,10000000,0,10000000],[0,10000000,0,0]],
                'islands': {'AGND': [['source'], ['other']]}}
        r = Raster(dump, .1, grow=growth or {}, bounds_mm=[0,0,10,10])
        win = (slice(0,r.h),slice(0,r.w)); N = r.net_id['AGND']; margin=.1/np.sqrt(2)+.01
        foreign=(r.label!=0)&(r.label!=N)
        free=np.array([ndimage.distance_transform_edt(~m)*r.res >= .4+margin for m in foreign])
        source_mask=island_mask(r,dump,['source'])
        via=(ndimage.distance_transform_edt(~foreign.any(0))*r.res >= .55+margin)&(r.d_smd>=.3+margin)
        c={'raster':r,'win':win,'inner':win,'g0':0,'g1':r.h,'h0':0,'h1':r.w,
           'N':N,'clearance':.25,'w':.3,'vr':.3,'margin':margin,'edge_clearance':.5,'hole_clearance':.25}
        return c,free,via,source_mask,dump

    def track(self, uuid='foreign', layer='B.Cu', net='signal'):
        return {'uuid':uuid,'net':net,'a':[5600000,4500000],'b':[5600000,5500000],
                'width':200000,'layer':layer}

    def test_own_smd_pad_prohibits_via_without_foreign_copper(self):
        from attribution import explain
        c,f,v,s,_=self.fixture()
        result=explain(c,f,v,s)
        own=[b for b in result['blockers'] if b.get('uuid')=='source']
        self.assertTrue(any(b['rule']=='smd_pad_via_prohibition' for b in own))
        self.assertFalse(any('foreign_copper' in b['rule'] for b in own))

    def test_other_layer_copper_blocks_via_but_not_frontier(self):
        from attribution import explain
        c,f,v,s,_=self.fixture([self.track()])
        rows=[b for b in explain(c,f,v,s)['blockers'] if b.get('uuid')=='foreign']
        self.assertTrue(any(b['rule']=='all_layer_foreign_copper_via_clearance' for b in rows))
        self.assertFalse(any('reachable_frontier' in b['sites'] for b in rows))

    def test_rail_growth_and_raster_margin_are_applied_and_disclosed(self):
        from attribution import explain
        counts=[]
        for growth in (0,.05):
            c,f,v,s,_=self.fixture([self.track(net='-12V')],{'-12V':growth})
            row=next(b for b in explain(c,f,v,s)['blockers'] if b.get('uuid')=='foreign')
            self.assertEqual(row['rail_growth_mm'],growth)
            self.assertAlmostEqual(row['raster_half_diagonal_mm'],.1/np.sqrt(2))
            self.assertAlmostEqual(row['threshold_mm'],.55+.1/np.sqrt(2)+.01)
            counts.append(row['sites']['reachable_rejected_via']['count'])
        self.assertGreater(counts[1],counts[0])

    def test_duplicate_uuid_rows_are_retained_with_distinct_row_identity(self):
        from attribution import explain
        c,f,v,s,_=self.fixture([self.track(),self.track()])
        rows=[b for b in explain(c,f,v,s)['blockers'] if b.get('uuid')=='foreign']
        self.assertEqual([b['source_row_index'] for b in rows],[0,1])
        self.assertEqual(rows[0]['source_row_sha256'],rows[1]['source_row_sha256'])

    def test_boundary_fence_has_no_fabricated_object_uuid(self):
        from attribution import explain
        c,f,v,s,_=self.fixture(source_xy=(.5,.5))
        v &= c['raster'].d_edge >= .8
        rows=explain(c,f,v,s)['blockers']
        fence=next(b for b in rows if b['object_type']=='computational_boundary_fence' and 'reachable_rejected_via' in b['sites'])
        self.assertIsNone(fence['uuid'])
        self.assertGreater(fence['sites']['reachable_rejected_via']['count'],0)

    def test_duplicate_anchor_uuid_keeps_exact_row_geometry(self):
        from attribution import existing_anchors
        first=self.track(uuid='anchor',layer='F.Cu',net='AGND')
        second={**first,'a':[4000000,4000000],'b':[6000000,4000000]}
        c,f,v,s,dump=self.fixture([first,second])
        dump['islands']['AGND']=[['source'],['anchor']]
        anchors=existing_anchors(c,f,s,dump,['source'])['components'][0]['anchors']
        self.assertEqual([a['source_row_index'] for a in anchors],[0,1])
        self.assertNotEqual(anchors[0]['source_row_sha256'],anchors[1]['source_row_sha256'])
        self.assertNotEqual(anchors[0]['reachable_cells'],anchors[1]['reachable_cells'])

    def test_existing_anchor_excludes_same_component_and_binds_distinct_group(self):
        from attribution import existing_anchors, seal
        c,f,v,s,dump=self.fixture()
        result=existing_anchors(c,f,s,dump,['source'])
        self.assertEqual(len(result['components']),1)
        group=result['components'][0]
        self.assertEqual(group['original_sorted_members'],['other'])
        self.assertGreater(group['reachable_goal_cells'],0)
        self.assertEqual(group['anchors'][0]['uuid'],'other')
        self.assertFalse(result['same_component_is_progress'])
        self.assertFalse(result['search_executed'])


@unittest.skipUnless(ARCHIVE, 'exact retained JL117 ZIP required for artifact tests')
class RetainedInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dump, cls.endpoints, cls.artifact = authenticate(ARCHIVE)

    def test_equal_edge_count_wrong_group_is_rejected(self):
        dump = copy.deepcopy(self.dump)
        groups = dump['islands']['AGND']
        groups[1], groups[2] = [groups[1][0], groups[2][0]], []
        self.assertEqual(sum(len(g)-1 for g in dump['islands'].values()), 117)
        with self.assertRaisesRegex(ValueError, 'membership'):
            validate_dump(dump, self.endpoints)

    def test_pose_drift_rejected(self):
        dump = copy.deepcopy(self.dump)
        uid = target_members(dump)[0]
        next(p for p in dump['pads'] if p['uuid'] == uid)['xy'][0] += 1
        with self.assertRaisesRegex(ValueError, 'pose'):
            validate_dump(dump, self.endpoints)

    def test_target_with_unannounced_copper_source_rejected(self):
        dump = copy.deepcopy(self.dump)
        group = target_members(dump)
        group.append(dump['tracks'][0]['uuid'])
        with self.assertRaisesRegex(ValueError, 'three-pad'):
            target_members(dump)

    def test_corrupt_archive_rejected_before_reading_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / 'bad.zip'
            bad.write_bytes(b'not the retained archive')
            with self.assertRaisesRegex(ValueError, 'size/digest'):
                authenticate(bad)

    def test_stale_published_input_rejected(self):
        original = Path.read_bytes

        def stale(path):
            if str(path).endswith('/boards/osc-jack-left/osc-jack-left.kicad_pcb'):
                return b'stale JL118'
            return original(path)

        with patch.object(Path, 'read_bytes', stale):
            with self.assertRaisesRegex(ValueError, 'published JL'):
                authenticate(ARCHIVE)

    def test_context_drift_rejected(self):
        original = Path.read_bytes

        def stale(path):
            if str(path).endswith('/boards/osc-jack-left/fp-lib-table'):
                return b'wrong relative library context'
            return original(path)

        with patch.object(Path, 'read_bytes', stale):
            with self.assertRaisesRegex(ValueError, 'context'):
                authenticate(ARCHIVE)

    def test_deterministic_source_replay_without_native_or_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                subprocess, 'run', side_effect=AssertionError('no subprocess/native permitted')):
            generated = prepare(ARCHIVE, Path(tmp))
            for name, value in generated.items():
                self.assertEqual((HERE / name).read_bytes(), encoded(value))
            diagnostic = generated['diagnostic-plan.json']['diagnostic']
            self.assertTrue(all(r['negative'] for r in diagnostic['observations']))
            self.assertEqual([r['legal_via_cells'] for r in diagnostic['observations']], [1, 958])
            self.assertEqual([r['layers'][0]['optimistic_reachable_cells'] for r in diagnostic['observations']], [11020, 15807])
            for observation in diagnostic['observations']:
                self.assertTrue(all(s['count'] == 0 for s in observation['attribution']['unattributed_sites'].values()))
            anchor = diagnostic['existing_anchor_hypothesis']
            self.assertEqual(anchor['components'][0]['original_all_member_count'], 1389)
            self.assertEqual(anchor['components'][0]['reachable_goal_cells'], 0)
            self.assertEqual(anchor['computational_window_mm'], 100)
            proposal = generated['no-copper-proposal.json']
            self.assertEqual(proposal['removed_uuids'], [])
            self.assertEqual(proposal['copper'], [])

    def test_all_unresolved_edges_and_endpoints_retained(self):
        cases = read(HERE / 'cases.json')['cases']
        self.assertEqual(sum(c['open_edges'] for c in cases), 117)
        self.assertEqual({c['net']: c['groups'] for c in cases}, self.endpoints['disconnected_nets'])
        self.assertEqual(len(self.endpoints['context_files']), 26)


if __name__ == '__main__':
    unittest.main()
